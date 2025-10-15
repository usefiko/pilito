"""
Multilingual Embedding Service for semantic search
✅ Primary: OpenAI text-embedding-3-large (best for multilingual)
✅ Fallback: Gemini text-embedding-004
✅ Final fallback: Returns None (caller uses BM25)
✅ Safe: No database changes, uses Redis cache
"""
import logging
import hashlib
from typing import List, Dict, Optional, Tuple
import math

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Multilingual embedding service with intelligent fallback
    - Primary: OpenAI text-embedding-3-large (industry standard, 100+ languages)
    - Fallback: Gemini text-embedding-004 (free tier)
    - Caches all embeddings in Redis (30 days)
    - Returns None if all methods fail (caller uses BM25)
    """
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize embedding service
        
        Args:
            use_cache: Whether to use Redis cache (default: True)
        """
        self.use_cache = use_cache
        self.openai_configured = False
        self.gemini_configured = False
        self.openai_client = None
        self.genai = None
        
        # Initialize both services
        self._initialize_openai()
        self._initialize_gemini()
        
        # Log configuration status
        if self.openai_configured:
            logger.info("✅ OpenAI embedding (primary) initialized successfully")
        if self.gemini_configured:
            logger.info("✅ Gemini embedding (fallback) initialized successfully")
        
        if not self.openai_configured and not self.gemini_configured:
            logger.warning("⚠️ No embedding service configured! Will fall back to BM25")
    
    def _initialize_openai(self):
        """Initialize OpenAI embedding API"""
        try:
            from openai import OpenAI
            from settings.models import GeneralSettings
            
            # Get API key from settings
            settings = GeneralSettings.get_settings()
            api_key = settings.openai_api_key
            
            if not api_key or len(api_key) < 20:
                logger.debug("OpenAI API key not configured")
                return
            
            # Initialize OpenAI client
            self.openai_client = OpenAI(api_key=api_key)
            self.openai_configured = True
            
        except ImportError:
            logger.debug("openai library not installed")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {str(e)}")
    
    def _initialize_gemini(self):
        """Initialize Gemini embedding model (fallback)"""
        try:
            import google.generativeai as genai
            from settings.models import GeneralSettings
            
            # Get API key from settings
            settings = GeneralSettings.get_settings()
            api_key = settings.gemini_api_key
            
            if not api_key or len(api_key) < 20:
                logger.debug("Gemini API key not configured")
                return
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            self.genai = genai
            self.gemini_configured = True
            
        except ImportError:
            logger.debug("google.generativeai not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
    
    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
        """
        Get embedding vector for text using OpenAI (primary) or Gemini (fallback)
        
        Args:
            text: Text to embed
            task_type: Task type hint
                - "retrieval_document": For documents/content to search
                - "retrieval_query": For user queries
        
        Returns:
            List of floats (embedding vector) or None if all methods failed
        """
        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided for embedding")
            return None
        
        # Check cache first (works for both OpenAI and Gemini)
        if self.use_cache:
            cached = self._get_from_cache(text, task_type)
            if cached:
                logger.debug(f"✅ Cache hit for embedding (length: {len(text)})")
                return cached
        
        # Try OpenAI first (best for multilingual)
        if self.openai_configured:
            embedding = self._get_openai_embedding(text)
            if embedding:
                # Cache it
                if self.use_cache:
                    self._save_to_cache(text, task_type, embedding)
                return embedding
            else:
                logger.info("🔄 OpenAI embedding failed, trying Gemini fallback...")
        
        # Fallback to Gemini
        if self.gemini_configured:
            embedding = self._get_gemini_embedding(text, task_type)
            if embedding:
                # Cache it
                if self.use_cache:
                    self._save_to_cache(text, task_type, embedding)
                return embedding
        
        # All methods failed
        logger.warning("⚠️ All embedding methods failed, will fall back to BM25")
        return None
    
    def _get_openai_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding from OpenAI text-embedding-3-large
        Industry standard for multilingual semantic search
        """
        if not self.openai_configured:
            return None
        
        try:
            # Limit text length to reasonable size (8000 tokens ~ 6000 chars)
            text_truncated = text[:6000]
            
            # Call OpenAI API
            # Using text-embedding-3-small (1536 dims) instead of 3-large (3072 dims)
            # because PostgreSQL 15 ivfflat index max is 2000 dimensions
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",  # 1536 dimensions
                input=text_truncated,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(f"✅ OpenAI embedding: dim={len(embedding)}, text_len={len(text)}")
            return embedding
            
        except Exception as e:
            logger.warning(f"⚠️ OpenAI embedding failed: {str(e)}")
            return None
    
    def _get_gemini_embedding(self, text: str, task_type: str) -> Optional[List[float]]:
        """
        Get embedding from Gemini text-embedding-004 (fallback)
        Free tier: 1500 requests/day
        """
        if not self.gemini_configured:
            return None
        
        try:
            # Limit text length
            text_truncated = text[:1000]
            
            # Call Gemini API
            result = self.genai.embed_content(
                model="models/text-embedding-004",
                content=text_truncated,
                task_type=task_type
            )
            
            embedding = result['embedding']
            
            logger.debug(f"✅ Gemini embedding: dim={len(embedding)}, text_len={len(text)}")
            return embedding
            
        except Exception as e:
            logger.warning(f"⚠️ Gemini embedding failed: {str(e)}")
            return None
    
    def _get_cache_key(self, text: str, task_type: str) -> str:
        """
        Generate cache key from text and task type
        
        Args:
            text: Text to embed
            task_type: Task type
        
        Returns:
            Cache key string
        """
        # Hash text + task_type for unique key
        # v2 to differentiate from old Gemini-only cache
        content = f"v2:{task_type}:{text}"
        hash_obj = hashlib.md5(content.encode('utf-8'))
        return f"emb:v2:{hash_obj.hexdigest()[:20]}"
    
    def _get_from_cache(self, text: str, task_type: str) -> Optional[List[float]]:
        """
        Get embedding from Redis cache
        
        Args:
            text: Text to embed
            task_type: Task type
        
        Returns:
            Cached embedding or None
        """
        try:
            from django.core.cache import cache
            key = self._get_cache_key(text, task_type)
            return cache.get(key)
        except Exception as e:
            logger.debug(f"Cache read failed: {str(e)}")
            return None
    
    def _save_to_cache(self, text: str, task_type: str, embedding: List[float]):
        """
        Save embedding to Redis cache (30 days TTL)
        
        Args:
            text: Text that was embedded
            task_type: Task type
            embedding: Embedding vector to cache
        """
        try:
            from django.core.cache import cache
            key = self._get_cache_key(text, task_type)
            # Cache for 30 days (30 * 24 * 60 * 60 seconds)
            cache.set(key, embedding, timeout=30*24*60*60)
            logger.debug(f"✅ Embedding cached with key: {key}")
        except Exception as e:
            logger.debug(f"Cache write failed: {str(e)}")
    
    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec_a: First vector
            vec_b: Second vector
        
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        
        try:
            dot_product = sum(x * y for x, y in zip(vec_a, vec_b))
            magnitude_a = math.sqrt(sum(x * x for x in vec_a))
            magnitude_b = math.sqrt(sum(y * y for y in vec_b))
            
            if magnitude_a == 0 or magnitude_b == 0:
                return 0.0
            
            similarity = dot_product / (magnitude_a * magnitude_b)
            
            # Clamp to [0, 1] range (should already be, but just in case)
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Cosine similarity calculation failed: {str(e)}")
            return 0.0
    
    def rank_documents(
        self,
        query: str,
        documents: List[str],
        top_n: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Rank documents by relevance to query using embeddings
        
        Args:
            query: User query text
            documents: List of document texts to rank
            top_n: Number of top results to return
        
        Returns:
            List of (document_index, similarity_score) tuples, sorted by score desc
            Returns empty list if embedding fails
        """
        if not query or not documents:
            return []
        
        try:
            # Get query embedding
            query_emb = self.get_embedding(query, task_type="retrieval_query")
            if not query_emb:
                return []
            
            # Get document embeddings and calculate similarities
            scores = []
            for idx, doc in enumerate(documents):
                doc_emb = self.get_embedding(doc, task_type="retrieval_document")
                if doc_emb:
                    similarity = self.cosine_similarity(query_emb, doc_emb)
                    scores.append((idx, similarity))
                else:
                    # If individual embedding fails, give low score
                    scores.append((idx, 0.0))
            
            # Sort by similarity (descending)
            scores.sort(key=lambda x: x[1], reverse=True)
            
            return scores[:top_n]
            
        except Exception as e:
            logger.error(f"Document ranking failed: {str(e)}")
            return []
