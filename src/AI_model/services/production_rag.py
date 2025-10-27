"""
Production-Ready RAG System
Drop-in replacement for ContextRetriever with advanced retrieval and reranking

Performance targets:
- Latency: < 2s
- Accuracy: 90%+
- Cost-effective
- Persian-optimized
"""
import logging
import time
from typing import List, Dict, Optional
from django.conf import settings
from AI_model.services.rag_metrics import RAGMetrics, RAGTimer

logger = logging.getLogger(__name__)


class ProductionRAG:
    """
    Advanced RAG system with:
    - Hybrid retrieval (BM25 + Vector)
    - Cross-encoder reranking
    - Context optimization
    - Persian support
    
    Drop-in replacement for ContextRetriever with same interface
    """
    
    # Configuration
    DENSE_TOP_K = 20  # Dense retrieval candidates
    SPARSE_TOP_K = 15  # BM25 candidates
    FUSION_TOP_K = 20  # After RRF fusion
    RERANK_TOP_K = 8   # Final chunks after reranking
    
    # Feature flags
    ENABLE_RERANKING = True  # Can be disabled for rollback
    RERANK_MODEL = 'base'    # 'base' (fast) or 'large' (better)
    
    @classmethod
    def retrieve_context(
        cls,
        query: str,
        user,
        primary_source: str,
        secondary_sources: List[str],
        primary_budget: int,
        secondary_budget: int,
        routing_info: Optional[Dict] = None
    ) -> Dict:
        """
        Retrieve context with advanced RAG pipeline
        
        ✅ Same interface as ContextRetriever!
        
        Args:
            query: User question
            user: User instance
            primary_source: Main source ('products', 'faq', etc.)
            secondary_sources: Additional sources
            primary_budget: Token budget for primary
            secondary_budget: Token budget for secondary
            routing_info: Optional routing metadata
        
        Returns:
            {
                'primary_context': List[Dict],
                'secondary_context': List[Dict],
                'sources_used': List[str],
                'total_chunks': int,
                'retrieval_method': str
            }
        """
        start_time = time.time()
        
        try:
            logger.info(
                f"🎯 ProductionRAG: query='{query[:50]}...', "
                f"primary={primary_source}, secondary={secondary_sources}"
            )
            
            # === STAGE 1: Query Analysis ===
            complexity = cls._analyze_query_complexity(query)
            language = cls._detect_language(query)
            
            logger.debug(f"Query complexity: {complexity:.2f}, language: {language}")
            
            # === STAGE 2: Hybrid Retrieval ===
            primary_chunks = cls._retrieve_from_source(
                query=query,
                user=user,
                source=primary_source,
                top_k=cls.DENSE_TOP_K,
                token_budget=primary_budget
            )
            
            secondary_chunks = []
            if secondary_sources and secondary_budget > 0:
                for source in secondary_sources[:3]:  # Limit to 3 sources
                    chunks = cls._retrieve_from_source(
                        query=query,
                        user=user,
                        source=source,
                        top_k=cls.SPARSE_TOP_K,
                        token_budget=secondary_budget // len(secondary_sources)
                    )
                    secondary_chunks.extend(chunks)
            
            logger.info(
                f"📚 Retrieved: primary={len(primary_chunks)}, "
                f"secondary={len(secondary_chunks)}"
            )
            
            # === STAGE 3: Fusion ===
            all_chunks = primary_chunks + secondary_chunks
            
            if not all_chunks:
                logger.warning("⚠️  No chunks retrieved!")
                return cls._empty_result()
            
            # Deduplicate
            unique_chunks = cls._deduplicate_chunks(all_chunks)
            
            logger.info(f"🔗 After deduplication: {len(unique_chunks)} chunks")
            
            # === STAGE 4: Reranking ===
            if cls.ENABLE_RERANKING and len(unique_chunks) > 5:
                try:
                    reranked_chunks = cls._rerank_chunks(
                        query=query,
                        chunks=unique_chunks,
                        top_k=cls.RERANK_TOP_K,
                        complexity=complexity
                    )
                    
                    logger.info(
                        f"✅ Reranked: {len(unique_chunks)} → {len(reranked_chunks)} chunks"
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Reranking failed: {e}, using original order")
                    reranked_chunks = unique_chunks[:cls.RERANK_TOP_K]
            else:
                logger.debug("Reranking skipped (disabled or too few chunks)")
                reranked_chunks = unique_chunks[:cls.RERANK_TOP_K]
            
            # === STAGE 5: Context Optimization ===
            optimized_chunks = cls._optimize_context(
                chunks=reranked_chunks,
                query=query,
                primary_budget=primary_budget,
                secondary_budget=secondary_budget
            )
            
            # === STAGE 6: Format Output ===
            # Split back to primary/secondary for compatibility
            result_primary = []
            result_secondary = []
            
            for chunk_data in optimized_chunks:
                chunk = chunk_data.get('chunk')
                if not chunk:
                    continue
                
                # Format for compatibility with existing code
                formatted = {
                    'chunk': chunk,
                    'score': chunk_data.get('score', 0.0),
                    'source': getattr(chunk, 'chunk_type', 'unknown'),
                    'title': getattr(chunk, 'section_title', ''),
                    'content': getattr(chunk, 'full_text', ''),
                    'tokens': chunk_data.get('tokens', 0)
                }
                
                # Assign to primary or secondary based on original source
                chunk_source = getattr(chunk, 'chunk_type', '')
                if cls._map_source_to_type(primary_source) == chunk_source:
                    result_primary.append(formatted)
                else:
                    result_secondary.append(formatted)
            
            total_time = (time.time() - start_time) * 1000
            
            # Track metrics
            RAGMetrics.track_retrieval(
                method='production_rag',
                primary_source=primary_source,
                latency_ms=total_time,
                chunks_retrieved=len(optimized_chunks),
                query_complexity=complexity,
                success=True
            )
            
            logger.info(
                f"🎉 ProductionRAG complete: {len(optimized_chunks)} chunks "
                f"in {total_time:.0f}ms"
            )
            
            return {
                'primary_context': result_primary,
                'secondary_context': result_secondary,
                'sources_used': [primary_source] + secondary_sources,
                'total_chunks': len(optimized_chunks),
                'retrieval_method': 'production_rag',
                'performance': {
                    'latency_ms': total_time,
                    'reranking_used': cls.ENABLE_RERANKING,
                    'query_complexity': complexity
                }
            }
            
        except Exception as e:
            logger.error(f"❌ ProductionRAG failed: {e}")
            logger.error("Falling back to simple retrieval")
            import traceback
            traceback.print_exc()
            
            # Fallback to simple retrieval
            return cls._fallback_retrieval(
                query=query,
                user=user,
                primary_source=primary_source,
                secondary_sources=secondary_sources,
                primary_budget=primary_budget,
                secondary_budget=secondary_budget
            )
    
    @classmethod
    def _retrieve_from_source(
        cls,
        query: str,
        user,
        source: str,
        top_k: int,
        token_budget: int
    ) -> List:
        """
        Retrieve from a single source using HybridRetriever
        """
        try:
            from AI_model.services.hybrid_retriever import HybridRetriever
            from AI_model.services.embedding_service import EmbeddingService
            
            # Map source name to chunk_type
            chunk_type = cls._map_source_to_type(source)
            
            # Generate embedding
            embedding_service = EmbeddingService()
            query_embedding = embedding_service.get_embedding(query)
            
            if not query_embedding:
                logger.warning(f"Failed to generate embedding for query: {query[:50]}")
                return []
            
            # Hybrid search
            results = HybridRetriever.hybrid_search(
                query=query,
                user=user,
                chunk_type=chunk_type,
                query_embedding=query_embedding,
                top_k=top_k,
                token_budget=token_budget
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve from {source}: {e}")
            return []
    
    @classmethod
    def _rerank_chunks(
        cls,
        query: str,
        chunks: List,
        top_k: int,
        complexity: float
    ) -> List[Dict]:
        """
        Rerank chunks using cross-encoder
        """
        try:
            from AI_model.services.cross_encoder_reranker import get_reranker
            
            # Choose model based on query complexity
            if complexity > 0.8:
                model = 'large'  # Better for complex queries
            else:
                model = 'base'   # Fast for simple queries
            
            reranker = get_reranker(model_name=model)
            
            reranked = reranker.rerank(
                query=query,
                chunks=chunks,
                top_k=top_k
            )
            
            return reranked
            
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            raise
    
    @classmethod
    def _optimize_context(
        cls,
        chunks: List[Dict],
        query: str,
        primary_budget: int,
        secondary_budget: int
    ) -> List[Dict]:
        """
        Optimize context (remove duplicates, cap tokens)
        """
        if not chunks:
            return []
        
        # Simple optimization: cap total tokens
        max_tokens = primary_budget + secondary_budget
        
        optimized = []
        total_tokens = 0
        
        for chunk_data in chunks:
            chunk_tokens = chunk_data.get('tokens', 100)
            
            if total_tokens + chunk_tokens <= max_tokens:
                optimized.append(chunk_data)
                total_tokens += chunk_tokens
            else:
                # Budget exceeded
                break
        
        return optimized
    
    @classmethod
    def _deduplicate_chunks(cls, chunks: List) -> List:
        """Remove duplicate chunks"""
        seen_ids = set()
        unique = []
        
        for chunk_data in chunks:
            # Handle both dict and object
            if isinstance(chunk_data, dict):
                chunk = chunk_data.get('chunk')
            else:
                chunk = chunk_data
            
            if not chunk:
                continue
            
            chunk_id = getattr(chunk, 'id', id(chunk))
            
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique.append(chunk_data)
        
        return unique
    
    @classmethod
    def _analyze_query_complexity(cls, query: str) -> float:
        """
        Analyze query complexity (0-1)
        Simple heuristic based on length and structure
        """
        if not query:
            return 0.0
        
        words = query.split()
        word_count = len(words)
        
        # Complexity factors
        score = 0.0
        
        # Length
        if word_count > 15:
            score += 0.4
        elif word_count > 8:
            score += 0.2
        
        # Question marks (complex if multiple questions)
        question_marks = query.count('؟') + query.count('?')
        if question_marks > 1:
            score += 0.3
        
        # Conjunctions (and, or)
        conjunctions = ['و', 'یا', 'and', 'or']
        if any(conj in query.lower() for conj in conjunctions):
            score += 0.2
        
        return min(score, 1.0)
    
    @classmethod
    def _detect_language(cls, text: str) -> str:
        """Detect language (fa or en)"""
        if not text:
            return 'en'
        
        # Count Persian characters
        persian_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        total_chars = len(text)
        
        if total_chars == 0:
            return 'en'
        
        persian_ratio = persian_chars / total_chars
        
        return 'fa' if persian_ratio > 0.3 else 'en'
    
    @classmethod
    def _map_source_to_type(cls, source: str) -> str:
        """Map source name to chunk_type"""
        mapping = {
            'products': 'product',
            'website': 'website',
            'faq': 'faq',
            'manual': 'manual'
        }
        return mapping.get(source, source)
    
    @classmethod
    def _empty_result(cls) -> Dict:
        """Return empty result"""
        return {
            'primary_context': [],
            'secondary_context': [],
            'sources_used': [],
            'total_chunks': 0,
            'retrieval_method': 'production_rag'
        }
    
    @classmethod
    def _fallback_retrieval(
        cls,
        query: str,
        user,
        primary_source: str,
        secondary_sources: List[str],
        primary_budget: int,
        secondary_budget: int
    ) -> Dict:
        """
        Fallback to ContextRetriever if ProductionRAG fails
        """
        try:
            from AI_model.services.context_retriever import ContextRetriever
            
            logger.warning("Using ContextRetriever fallback")
            
            return ContextRetriever.retrieve_context(
                query=query,
                user=user,
                primary_source=primary_source,
                secondary_sources=secondary_sources,
                primary_budget=primary_budget,
                secondary_budget=secondary_budget
            )
            
        except Exception as e:
            logger.error(f"Fallback also failed: {e}")
            return cls._empty_result()

