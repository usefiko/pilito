"""
Hybrid Search Retriever - BM25 + Vector
Combines keyword-based search (BM25) with semantic search (Vector)
Inspired by Intercom, Insider, and industry best practices
"""
import logging
from typing import List, Dict, Optional
from django.db.models import Q, Value, FloatField
from django.db.models.functions import Greatest
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid Search = BM25 (Keyword) + Vector (Semantic)
    
    Benefits:
    - Exact product name match → High score
    - Semantic understanding → Broader matches
    - Combined score → Best results
    
    Industry Standard:
    - Used by Intercom, Insider, Zendesk
    - 30-50% improvement in search accuracy
    - Essential for e-commerce with 10,000+ products
    """
    
    # Weight configuration
    VECTOR_WEIGHT = 0.6  # 60% for semantic search
    KEYWORD_WEIGHT = 0.4  # 40% for keyword search
    
    # Minimum scores
    MIN_VECTOR_SCORE = 0.1
    MIN_KEYWORD_SCORE = 0.05
    
    @classmethod
    def hybrid_search(
        cls,
        query: str,
        user,
        chunk_type: str,
        query_embedding: List[float],
        top_k: int = 5,
        token_budget: int = 800
    ) -> List[Dict]:
        """
        Hybrid search combining vector and keyword search
        
        Args:
            query: Search query text
            user: User object
            chunk_type: Type of chunks to search ('product', 'faq', etc.)
            query_embedding: Vector embedding of query
            top_k: Number of results to return
            token_budget: Maximum tokens for results
            
        Returns:
            List of dicts with title, content, score, etc.
        """
        try:
            from AI_model.models import TenantKnowledge, PGVECTOR_AVAILABLE
            
            if not PGVECTOR_AVAILABLE:
                logger.warning("pgvector not available, falling back to keyword search only")
                return cls._keyword_search_only(query, user, chunk_type, top_k)
            
            from pgvector.django import CosineDistance
            
            # Get base queryset
            base_query = TenantKnowledge.objects.filter(
                user=user,
                chunk_type=chunk_type
            )
            
            # 1. Vector Search (Semantic)
            vector_results = cls._vector_search(
                base_query,
                query_embedding,
                top_k * 3  # Get more candidates for hybrid ranking
            )
            
            # 2. Keyword Search (BM25-like using PostgreSQL Full-Text Search)
            keyword_results = cls._keyword_search(
                base_query,
                query,
                top_k * 3  # Get more candidates
            )
            
            # 3. Combine and re-rank using RRF (Reciprocal Rank Fusion)
            combined_results = cls._reciprocal_rank_fusion(
                vector_results,
                keyword_results,
                top_k
            )
            
            # 4. Apply token budget
            final_results = cls._apply_token_budget(combined_results, token_budget)
            
            logger.info(
                f"🔍 Hybrid search: {len(final_results)} results "
                f"(vector: {len(vector_results)}, keyword: {len(keyword_results)})"
            )
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}, falling back to vector only")
            # Fallback to vector search only
            return cls._vector_search_fallback(user, chunk_type, query_embedding, top_k)
    
    @classmethod
    def _vector_search(cls, base_query, query_embedding, top_k) -> Dict[str, Dict]:
        """
        Pure vector search using pgvector
        Returns: {chunk_id: {score, data}}
        """
        from pgvector.django import CosineDistance
        
        results = {}
        
        chunks = base_query.filter(
            tldr_embedding__isnull=False
        ).annotate(
            distance=CosineDistance('tldr_embedding', query_embedding)
        ).order_by('distance')[:top_k]
        
        for rank, chunk in enumerate(chunks, 1):
            similarity = 1 - chunk.distance
            
            if similarity < cls.MIN_VECTOR_SCORE:
                continue
            
            results[str(chunk.id)] = {
                'chunk': chunk,
                'vector_score': round(similarity, 3),
                'vector_rank': rank,
                'title': chunk.section_title or f"{chunk.chunk_type.upper()} Chunk",
                'content': chunk.full_text,
                'type': chunk.chunk_type,
                'source_id': chunk.source_id,
                'word_count': chunk.word_count
            }
        
        return results
    
    @classmethod
    def _keyword_search(cls, base_query, query, top_k) -> Dict[str, Dict]:
        """
        Keyword search using PostgreSQL Full-Text Search
        Returns: {chunk_id: {score, data}}
        """
        try:
            # Create search vector from section_title and full_text
            # Weight: title = 'A' (highest), content = 'B'
            search_vector = (
                SearchVector('section_title', weight='A') + 
                SearchVector('full_text', weight='B')
            )
            
            # Create search query
            search_query = SearchQuery(query, search_type='websearch')
            
            # Execute search with ranking
            results = {}
            
            chunks = base_query.annotate(
                rank=SearchRank(search_vector, search_query)
            ).filter(
                rank__gt=cls.MIN_KEYWORD_SCORE
            ).order_by('-rank')[:top_k]
            
            for rank_idx, chunk in enumerate(chunks, 1):
                # Normalize rank to 0-1 scale (PostgreSQL rank can be > 1)
                normalized_score = min(chunk.rank / 10.0, 1.0)  # Cap at 1.0
                
                results[str(chunk.id)] = {
                    'chunk': chunk,
                    'keyword_score': round(normalized_score, 3),
                    'keyword_rank': rank_idx,
                    'title': chunk.section_title or f"{chunk.chunk_type.upper()} Chunk",
                    'content': chunk.full_text,
                    'type': chunk.chunk_type,
                    'source_id': chunk.source_id,
                    'word_count': chunk.word_count
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return {}
    
    @classmethod
    def _reciprocal_rank_fusion(
        cls,
        vector_results: Dict,
        keyword_results: Dict,
        top_k: int
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion (RRF) for combining search results
        
        RRF Formula: score = sum(1 / (k + rank_i))
        Where k = 60 (standard constant)
        
        This is industry standard for combining search results
        """
        k = 60  # RRF constant
        combined = {}
        
        # Add vector results
        for chunk_id, data in vector_results.items():
            rrf_score = 1 / (k + data['vector_rank'])
            combined[chunk_id] = {
                **data,
                'rrf_score': rrf_score,
                'keyword_score': 0.0,  # Default if not found in keyword
                'keyword_rank': None
            }
        
        # Add/merge keyword results
        for chunk_id, data in keyword_results.items():
            rrf_score = 1 / (k + data['keyword_rank'])
            
            if chunk_id in combined:
                # Merge scores
                combined[chunk_id]['rrf_score'] += rrf_score
                combined[chunk_id]['keyword_score'] = data['keyword_score']
                combined[chunk_id]['keyword_rank'] = data['keyword_rank']
            else:
                # New result from keyword only
                combined[chunk_id] = {
                    **data,
                    'rrf_score': rrf_score,
                    'vector_score': 0.0,  # Default if not found in vector
                    'vector_rank': None
                }
        
        # Calculate final hybrid score (weighted combination)
        for chunk_id in combined:
            vector_score = combined[chunk_id].get('vector_score', 0)
            keyword_score = combined[chunk_id].get('keyword_score', 0)
            rrf_score = combined[chunk_id]['rrf_score']
            
            # Weighted combination
            hybrid_score = (
                cls.VECTOR_WEIGHT * vector_score +
                cls.KEYWORD_WEIGHT * keyword_score +
                0.2 * rrf_score  # RRF boost for consensus
            )
            
            combined[chunk_id]['score'] = round(hybrid_score, 3)
        
        # Sort by hybrid score and return top_k
        results_list = sorted(
            combined.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:top_k]
        
        return results_list
    
    @classmethod
    def _apply_token_budget(cls, results: List[Dict], token_budget: int) -> List[Dict]:
        """Apply token budget trimming"""
        trimmed = []
        total_tokens = 0
        
        for result in results:
            # Estimate tokens (word_count * 1.3)
            item_tokens = int(result.get('word_count', len(result['content'].split())) * 1.3)
            
            if total_tokens + item_tokens <= token_budget:
                trimmed.append(result)
                total_tokens += item_tokens
            else:
                # Check if we can fit a trimmed version
                remaining = token_budget - total_tokens
                if remaining > 100:  # At least 100 tokens
                    max_words = int(remaining / 1.3)
                    words = result['content'].split()
                    if len(words) > max_words:
                        result['content'] = ' '.join(words[:max_words]) + '...'
                        result['word_count'] = max_words
                        trimmed.append(result)
                        total_tokens += remaining
                
                break  # Budget exhausted
        
        return trimmed
    
    @classmethod
    def _keyword_search_only(cls, query, user, chunk_type, top_k) -> List[Dict]:
        """Fallback to keyword search only when pgvector not available"""
        from AI_model.models import TenantKnowledge
        
        base_query = TenantKnowledge.objects.filter(
            user=user,
            chunk_type=chunk_type
        )
        
        keyword_results = cls._keyword_search(base_query, query, top_k)
        
        # Convert to list format
        results_list = []
        for data in keyword_results.values():
            results_list.append({
                'title': data['title'],
                'content': data['content'],
                'type': data['type'],
                'score': data['keyword_score'],
                'source_id': data['source_id'],
                'word_count': data['word_count']
            })
        
        return sorted(results_list, key=lambda x: x['score'], reverse=True)
    
    @classmethod
    def _vector_search_fallback(cls, user, chunk_type, query_embedding, top_k) -> List[Dict]:
        """Fallback to pure vector search"""
        from AI_model.models import TenantKnowledge
        from pgvector.django import CosineDistance
        
        base_query = TenantKnowledge.objects.filter(
            user=user,
            chunk_type=chunk_type
        )
        
        vector_results = cls._vector_search(base_query, query_embedding, top_k)
        
        # Convert to list format
        results_list = []
        for data in vector_results.values():
            results_list.append({
                'title': data['title'],
                'content': data['content'],
                'type': data['type'],
                'score': data['vector_score'],
                'source_id': data['source_id'],
                'word_count': data['word_count']
            })
        
        return results_list

