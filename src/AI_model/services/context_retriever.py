"""
Context Retriever - RAG with Hybrid Search
Retrieves relevant knowledge using hybrid search (BM25 + Vector)
Supports multi-source retrieval (FAQ, Manual, Products, Website)
"""
import logging
from typing import List, Dict, Optional
from django.core.cache import cache
from django.db.models import Q

logger = logging.getLogger(__name__)


class ContextRetriever:
    """
    Retrieval Augmented Generation (RAG) using Hybrid Search
    
    Features:
    - Hybrid search (BM25 keyword + Vector semantic)
    - Multi-source retrieval (FAQ, Manual, Products, Website)
    - Industry standard (Intercom, Insider approach)
    - Token budget awareness
    - 30-50% better accuracy than pure vector search
    """
    
    # Default retrieval limits
    DEFAULT_TOP_K = 5
    MIN_SIMILARITY_SCORE = 0.1  # Minimum cosine similarity (0-1) - lowered for multilingual
    
    # Source type mapping
    SOURCE_TO_CHUNK_TYPE = {
        'faq': 'faq',
        'manual': 'manual',
        'products': 'product',
        'website': 'website'
    }
    
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
        Retrieve relevant context from knowledge base
        
        Args:
            query: User's question
            user: User instance
            primary_source: Main source to search (e.g., 'faq')
            secondary_sources: Additional sources (e.g., ['products', 'manual'])
            primary_budget: Token budget for primary source
            secondary_budget: Token budget for secondary sources
            routing_info: Optional routing metadata
        
        Returns:
            {
                'primary_context': List[Dict],  # Main chunks
                'secondary_context': List[Dict],  # Supplementary chunks
                'sources_used': List[str],
                'total_chunks': int,
                'retrieval_method': 'semantic_search'
            }
        """
        try:
            from AI_model.services.embedding_service import EmbeddingService
            
            # 🔥 WORLD-CLASS: Normalize query before embedding (matches chunk normalization)
            from AI_model.services.persian_normalizer import get_normalizer
            normalizer = get_normalizer()
            
            # Normalize query if Persian (same normalization as chunks = better matching)
            if normalizer.is_persian(query):
                query_normalized = normalizer.normalize(query)
            else:
                query_normalized = query
            
            # Generate query embedding (with normalized query = better quality)
            embedding_service = EmbeddingService()
            query_embedding = embedding_service.get_embedding(query_normalized, task_type="retrieval_query")
            
            if not query_embedding:
                logger.warning("Query embedding failed, using fallback")
                return cls._fallback_retrieval(user, primary_source, secondary_sources)
            
            # Retrieve from primary source (use normalized query)
            # ⭐ STANDARD RAG: No token budget at search level - returns all top_k results
            primary_chunks = cls._search_source(
                user=user,
                source=primary_source,
                query_embedding=query_embedding,
                top_k=cls.DEFAULT_TOP_K,
                query_text=query_normalized  # ✅ Use normalized query for hybrid search
            )
            
            # Retrieve from ALL secondary sources (standard RAG approach)
            secondary_chunks = []
            if secondary_budget > 50 and secondary_sources:
                for source in secondary_sources:  # ✅ Use ALL secondary sources
                    chunks = cls._search_source(
                        user=user,
                        source=source,
                        query_embedding=query_embedding,
                        top_k=5,  # ✅ More chunks per secondary source
                        query_text=query_normalized  # ✅ Use normalized query for hybrid search
                    )
                    secondary_chunks.extend(chunks)
            
            logger.info(
                f"📚 Retrieved {len(primary_chunks)} primary + {len(secondary_chunks)} secondary chunks "
                f"from {primary_source} + {secondary_sources}"
            )
            
            return {
                'primary_context': primary_chunks,
                'secondary_context': secondary_chunks,
                'sources_used': [primary_source] + secondary_sources,
                'total_chunks': len(primary_chunks) + len(secondary_chunks),
                'retrieval_method': 'semantic_search'
            }
            
        except Exception as e:
            logger.error(f"❌ Context retrieval failed: {e}")
            return cls._fallback_retrieval(user, primary_source, secondary_sources)
    
    @classmethod
    def _search_source(
        cls,
        user,
        source: str,
        query_embedding: List[float],
        top_k: int,
        query_text: str = ""  # ✅ Added for keyword search
    ) -> List[Dict]:
        """
        Search a specific knowledge source using Hybrid Search (BM25 + Vector)
        
        Returns:
            List of dicts: [
                {
                    'title': str,
                    'content': str,
                    'type': str,
                    'score': float,  # Hybrid score (keyword + semantic)
                    'source_id': uuid
                },
                ...
            ]
        """
        try:
            from AI_model.models import TenantKnowledge, PGVECTOR_AVAILABLE
            from AI_model.services.hybrid_retriever import HybridRetriever
            
            chunk_type = cls.SOURCE_TO_CHUNK_TYPE.get(source, source)
            
            # ✅ Use Hybrid Search (BM25 + Vector)
            # ⭐ STANDARD RAG: No token budget at search level - returns all top_k results
            if PGVECTOR_AVAILABLE and query_text:
                results = HybridRetriever.hybrid_search(
                    query=query_text,
                    user=user,
                    chunk_type=chunk_type,
                    query_embedding=query_embedding,
                    top_k=top_k
                )
                
                logger.debug(
                    f"🔍 Hybrid search: {len(results)} chunks from {source} "
                    f"(scores: {[r['score'] for r in results[:3]]})"
                )
                
                return results
            
            # Fallback: Pure vector search (if no query_text)
            elif PGVECTOR_AVAILABLE:
                from pgvector.django import CosineDistance
                
                base_query = TenantKnowledge.objects.filter(
                    user=user,
                    chunk_type=chunk_type
                )
                
                results = []
                
                chunks = base_query.filter(
                    tldr_embedding__isnull=False
                ).annotate(
                    distance=CosineDistance('tldr_embedding', query_embedding)
                ).order_by('distance')[:top_k * 2]
                
                for chunk in chunks:
                    similarity = 1 - chunk.distance
                    
                    if similarity < cls.MIN_SIMILARITY_SCORE:
                        continue
                    
                    results.append({
                        'id': chunk.id,  # ✅ Add ID for debugging
                        'title': chunk.section_title or f"{chunk.chunk_type.upper()} Chunk",
                        'content': chunk.full_text,
                        'type': chunk.chunk_type,
                        'score': round(similarity, 3),
                        'source_id': chunk.source_id,
                        'word_count': chunk.word_count
                    })
                    
                    if len(results) >= top_k:
                        break
                
                # ⭐ STANDARD RAG: No token budget at search level - returns all top_k results
                logger.debug(
                    f"Found {len(results)} chunks from {source} (vector only)"
                )
                
                return results
            
            # Final fallback: no pgvector
            else:
                logger.warning(f"pgvector not available, using recent chunks for {source}")
                base_query = TenantKnowledge.objects.filter(
                    user=user,
                    chunk_type=chunk_type
                )
                
                chunks = base_query.order_by('-created_at')[:top_k]
                
                results = []
                for chunk in chunks:
                    results.append({
                        'id': chunk.id,  # ✅ Add ID for debugging
                        'title': chunk.section_title or f"{chunk.chunk_type.upper()} Chunk",
                        'content': chunk.full_text,
                        'type': chunk.chunk_type,
                        'score': 0.7,
                        'source_id': chunk.source_id,
                        'word_count': chunk.word_count
                    })
                
                return results
            
        except Exception as e:
            logger.error(f"❌ Source search failed for {source}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    @classmethod
    def _trim_to_budget(cls, chunks: List[Dict], token_budget: int) -> List[Dict]:
        """
        Trim chunks to fit within token budget
        Uses word count estimation (1 word ≈ 1.3 tokens)
        """
        if not chunks:
            return []
        
        trimmed = []
        total_tokens = 0
        
        for chunk in chunks:
            # Estimate tokens (word_count * 1.3)
            chunk_tokens = int(chunk.get('word_count', len(chunk['content'].split())) * 1.3)
            
            if total_tokens + chunk_tokens <= token_budget:
                trimmed.append(chunk)
                total_tokens += chunk_tokens
            else:
                # Check if we can fit a trimmed version
                remaining = token_budget - total_tokens
                if remaining > 100:  # At least 100 tokens
                    # Trim content to fit
                    max_words = int(remaining / 1.3)
                    words = chunk['content'].split()
                    if len(words) > max_words:
                        chunk['content'] = ' '.join(words[:max_words]) + '...'
                        chunk['word_count'] = max_words
                        trimmed.append(chunk)
                        total_tokens += remaining
                
                break  # Budget exhausted
        
        return trimmed
    
    @classmethod
    def _fallback_retrieval(cls, user, primary_source: str, secondary_sources: List[str]) -> Dict:
        """
        Fallback when semantic search fails
        Returns most recent chunks from each source
        """
        try:
            from AI_model.models import TenantKnowledge
            
            primary_chunks = []
            secondary_chunks = []
            
            # Get recent chunks from primary source
            chunk_type = cls.SOURCE_TO_CHUNK_TYPE.get(primary_source, primary_source)
            recent_primary = TenantKnowledge.objects.filter(
                user=user,
                chunk_type=chunk_type
            ).order_by('-created_at')[:3]
            
            for chunk in recent_primary:
                primary_chunks.append({
                    'id': chunk.id,  # ✅ Add ID for debugging
                    'title': chunk.section_title or f"{chunk.chunk_type.upper()} Info",
                    'content': chunk.full_text[:500],  # Limit to 500 chars
                    'type': chunk.chunk_type,
                    'score': 0.5,
                    'source_id': chunk.source_id
                })
            
            # Get from ALL secondary sources
            for source in secondary_sources:  # ✅ Use ALL secondary sources
                chunk_type = cls.SOURCE_TO_CHUNK_TYPE.get(source, source)
                recent_secondary = TenantKnowledge.objects.filter(
                    user=user,
                    chunk_type=chunk_type
                ).order_by('-created_at')[:2]
                
                for chunk in recent_secondary:
                    secondary_chunks.append({
                        'id': chunk.id,  # ✅ Add ID for debugging
                        'title': chunk.section_title or f"{chunk.chunk_type.upper()} Info",
                        'content': chunk.full_text[:300],
                        'type': chunk.chunk_type,
                        'score': 0.5,
                        'source_id': chunk.source_id
                    })
            
            logger.warning(
                f"⚠️ Using fallback retrieval: {len(primary_chunks)} primary, "
                f"{len(secondary_chunks)} secondary"
            )
            
            return {
                'primary_context': primary_chunks,
                'secondary_context': secondary_chunks,
                'sources_used': [primary_source] + secondary_sources,
                'total_chunks': len(primary_chunks) + len(secondary_chunks),
                'retrieval_method': 'fallback_recent'
            }
            
        except Exception as e:
            logger.error(f"❌ Fallback retrieval failed: {e}")
            return {
                'primary_context': [],
                'secondary_context': [],
                'sources_used': [],
                'total_chunks': 0,
                'retrieval_method': 'failed'
            }
    
    @classmethod
    def preload_user_knowledge(cls, user) -> Dict[str, int]:
        """
        Preload and cache user's knowledge base statistics
        Useful for monitoring and diagnostics
        
        Returns:
            {
                'faq': 15,
                'manual': 8,
                'product': 50,
                'website': 120,
                'total': 193
            }
        """
        try:
            from AI_model.models import TenantKnowledge
            
            stats = {}
            total = 0
            
            for chunk_type in ['faq', 'manual', 'product', 'website']:
                count = TenantKnowledge.objects.filter(
                    user=user,
                    chunk_type=chunk_type
                ).count()
                stats[chunk_type] = count
                total += count
            
            stats['total'] = total
            
            # Cache for 1 hour
            cache_key = f"knowledge_stats:{user.id}"
            cache.set(cache_key, stats, 3600)
            
            logger.info(f"📊 Knowledge base stats for {user.username}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to load knowledge stats: {e}")
            return {'total': 0}

