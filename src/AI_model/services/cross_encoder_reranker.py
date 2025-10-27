"""
Cross-Encoder Reranker for Advanced RAG
Uses sentence-transformers cross-encoder models for precise relevance scoring
"""
import logging
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# ✅ Setup proxy BEFORE importing sentence-transformers (required for Iran servers)
# sentence-transformers downloads models from Hugging Face
from core.utils import setup_ai_proxy
setup_ai_proxy()

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """Result from reranking"""
    chunk: any  # TenantKnowledge object
    score: float
    original_rank: int


class CrossEncoderReranker:
    """
    Cross-Encoder based reranking for RAG
    
    Models:
    - BAAI/bge-reranker-base: Fast (200ms for 20 chunks)
    - BAAI/bge-reranker-large: Better (400ms for 20 chunks)
    
    Usage:
        reranker = CrossEncoderReranker()
        reranked = reranker.rerank(
            query="بورسیه دارین؟",
            chunks=candidate_chunks,
            top_k=8
        )
    """
    
    # Model cache (class-level for sharing across instances)
    _model_cache = {}
    _model_lock = None
    
    # Available models
    MODELS = {
        'base': 'BAAI/bge-reranker-base',
        'large': 'BAAI/bge-reranker-large',
    }
    
    def __init__(self, model_name: str = 'base', device: str = 'cpu'):
        """
        Initialize reranker
        
        Args:
            model_name: 'base' (fast) or 'large' (better)
            device: 'cpu' or 'cuda' (if GPU available)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load model with caching and error handling"""
        try:
            # Check if model is already loaded
            cache_key = f"{self.model_name}_{self.device}"
            
            if cache_key in self._model_cache:
                self.model = self._model_cache[cache_key]
                logger.debug(f"✅ Using cached cross-encoder: {self.model_name}")
                return
            
            # Load model
            model_path = self.MODELS.get(self.model_name)
            if not model_path:
                logger.warning(f"Unknown model: {self.model_name}, using 'base'")
                model_path = self.MODELS['base']
            
            logger.info(f"📥 Loading cross-encoder model: {model_path}")
            start_time = time.time()
            
            try:
                from sentence_transformers import CrossEncoder
                
                self.model = CrossEncoder(
                    model_path,
                    max_length=512,
                    device=self.device
                )
                
                # Cache model
                self._model_cache[cache_key] = self.model
                
                load_time = (time.time() - start_time) * 1000
                logger.info(f"✅ Cross-encoder loaded in {load_time:.0f}ms")
                
            except ImportError:
                logger.error("❌ sentence-transformers not installed!")
                logger.error("Install: pip install sentence-transformers")
                raise ImportError(
                    "sentence-transformers is required for cross-encoder reranking. "
                    "Install it with: pip install sentence-transformers"
                )
            
        except Exception as e:
            logger.error(f"❌ Failed to load cross-encoder: {e}")
            raise
    
    def rerank(
        self,
        query: str,
        chunks: List,
        top_k: int = 8,
        return_scores: bool = True
    ) -> List[Dict]:
        """
        Rerank chunks using cross-encoder
        
        Args:
            query: User query
            chunks: List of chunks (TenantKnowledge objects or dicts)
            top_k: Number of top chunks to return
            return_scores: Include scores in output
        
        Returns:
            List of dicts with format:
            [
                {
                    'chunk': TenantKnowledge object,
                    'score': 0.95,
                    'original_rank': 2
                },
                ...
            ]
        """
        if not chunks:
            logger.warning("No chunks to rerank")
            return []
        
        if not self.model:
            logger.error("Model not loaded, returning original chunks")
            return self._format_output(chunks[:top_k], scores=[0.0] * len(chunks[:top_k]))
        
        try:
            start_time = time.time()
            
            # Prepare pairs for cross-encoder
            pairs = []
            for chunk in chunks:
                chunk_text = self._extract_text(chunk)
                pairs.append([query, chunk_text])
            
            # Score with cross-encoder
            logger.debug(f"🔍 Reranking {len(pairs)} chunks with {self.model_name}")
            scores = self.model.predict(pairs)
            
            # Sort by score (descending)
            ranked_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )
            
            # Get top-k
            top_indices = ranked_indices[:top_k]
            
            # Format output
            results = []
            for rank, idx in enumerate(top_indices):
                results.append({
                    'chunk': chunks[idx],
                    'score': float(scores[idx]),
                    'original_rank': idx,
                    'rerank': rank
                })
            
            rerank_time = (time.time() - start_time) * 1000
            logger.info(
                f"✅ Reranked {len(chunks)} → {len(results)} chunks in {rerank_time:.0f}ms "
                f"(model: {self.model_name})"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Reranking failed: {e}")
            logger.error(f"Returning original chunks without reranking")
            # Fallback: return original order
            return self._format_output(chunks[:top_k], scores=[0.0] * len(chunks[:top_k]))
    
    def _extract_text(self, chunk) -> str:
        """Extract text from chunk (handle both dict and object)"""
        try:
            # If it's a dict
            if isinstance(chunk, dict):
                return chunk.get('content', chunk.get('full_text', ''))
            
            # If it's a TenantKnowledge object
            return getattr(chunk, 'full_text', str(chunk))
            
        except Exception as e:
            logger.warning(f"Failed to extract text from chunk: {e}")
            return ""
    
    def _format_output(self, chunks: List, scores: List[float]) -> List[Dict]:
        """Format output with consistent structure"""
        results = []
        for i, (chunk, score) in enumerate(zip(chunks, scores)):
            results.append({
                'chunk': chunk,
                'score': score,
                'original_rank': i,
                'rerank': i
            })
        return results
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if cross-encoder reranking is available"""
        try:
            from sentence_transformers import CrossEncoder
            return True
        except ImportError:
            return False


# Global singleton for reusability
_reranker_instance = None


def get_reranker(model_name: str = 'base', device: str = 'cpu') -> CrossEncoderReranker:
    """
    Get singleton reranker instance
    
    Args:
        model_name: 'base' or 'large'
        device: 'cpu' or 'cuda'
    
    Returns:
        CrossEncoderReranker instance
    """
    global _reranker_instance
    
    if _reranker_instance is None:
        _reranker_instance = CrossEncoderReranker(
            model_name=model_name,
            device=device
        )
    
    return _reranker_instance

