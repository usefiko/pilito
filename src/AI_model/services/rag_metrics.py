"""
Metrics and Monitoring for Production RAG System
"""
import logging
import time
from typing import Dict, Optional
from datetime import datetime, timezone
from django.core.cache import cache
from django.db import models
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)


# ==========================================
#  Prometheus Metrics
# ==========================================

# Retrieval metrics
rag_retrieval_total = Counter(
    'rag_retrieval_total',
    'Total RAG retrievals',
    ['method', 'primary_source']
)

rag_retrieval_latency = Histogram(
    'rag_retrieval_latency_seconds',
    'RAG retrieval latency',
    ['method'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

rag_chunks_retrieved = Histogram(
    'rag_chunks_retrieved',
    'Number of chunks retrieved',
    ['method', 'source'],
    buckets=[0, 1, 2, 5, 8, 10, 15, 20]
)

# Reranking metrics
rag_reranking_total = Counter(
    'rag_reranking_total',
    'Total reranking operations',
    ['model']
)

rag_reranking_latency = Histogram(
    'rag_reranking_latency_seconds',
    'Reranking latency',
    ['model'],
    buckets=[0.1, 0.2, 0.5, 1.0, 2.0]
)

# Error metrics
rag_errors_total = Counter(
    'rag_errors_total',
    'Total RAG errors',
    ['method', 'error_type']
)

# Quality metrics
rag_query_complexity = Histogram(
    'rag_query_complexity',
    'Query complexity score',
    buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
)

rag_chunk_scores = Histogram(
    'rag_chunk_scores',
    'Chunk relevance scores',
    ['source'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0]
)

# Active models
rag_active_model = Gauge(
    'rag_active_model',
    'Currently active RAG configuration',
    ['component', 'value']
)


# ==========================================
#  Metrics Tracking
# ==========================================

class RAGMetrics:
    """Track and report RAG metrics"""
    
    @classmethod
    def track_retrieval(
        cls,
        method: str,
        primary_source: str,
        latency_ms: float,
        chunks_retrieved: int,
        query_complexity: float = 0.0,
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """
        Track a retrieval operation
        
        Args:
            method: 'production_rag' or 'context_retriever'
            primary_source: 'products', 'manual', etc.
            latency_ms: Latency in milliseconds
            chunks_retrieved: Number of chunks retrieved
            query_complexity: Complexity score (0-1)
            success: Whether retrieval succeeded
            error_type: Type of error if failed
        """
        # Prometheus metrics
        rag_retrieval_total.labels(
            method=method,
            primary_source=primary_source
        ).inc()
        
        rag_retrieval_latency.labels(
            method=method
        ).observe(latency_ms / 1000.0)
        
        rag_chunks_retrieved.labels(
            method=method,
            source=primary_source
        ).observe(chunks_retrieved)
        
        if query_complexity > 0:
            rag_query_complexity.observe(query_complexity)
        
        if not success and error_type:
            rag_errors_total.labels(
                method=method,
                error_type=error_type
            ).inc()
        
        # Cache recent metrics
        cls._cache_metric('last_retrieval', {
            'method': method,
            'source': primary_source,
            'latency_ms': latency_ms,
            'chunks': chunks_retrieved,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # Log
        logger.info(
            f"📊 RAG Retrieval: method={method}, source={primary_source}, "
            f"latency={latency_ms:.0f}ms, chunks={chunks_retrieved}"
        )
    
    @classmethod
    def track_reranking(
        cls,
        model: str,
        latency_ms: float,
        input_chunks: int,
        output_chunks: int,
        avg_score: float = 0.0,
        success: bool = True
    ):
        """
        Track a reranking operation
        
        Args:
            model: 'base' or 'large'
            latency_ms: Latency in milliseconds
            input_chunks: Number of input chunks
            output_chunks: Number of output chunks
            avg_score: Average relevance score
            success: Whether reranking succeeded
        """
        rag_reranking_total.labels(model=model).inc()
        
        rag_reranking_latency.labels(model=model).observe(latency_ms / 1000.0)
        
        if avg_score > 0:
            rag_chunk_scores.labels(source='reranked').observe(avg_score)
        
        cls._cache_metric('last_reranking', {
            'model': model,
            'latency_ms': latency_ms,
            'input_chunks': input_chunks,
            'output_chunks': output_chunks,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(
            f"📊 Reranking: model={model}, latency={latency_ms:.0f}ms, "
            f"{input_chunks}→{output_chunks} chunks"
        )
    
    @classmethod
    def _cache_metric(cls, key: str, value: Dict, ttl: int = 300):
        """Cache metric for dashboard"""
        cache_key = f'rag_metric:{key}'
        cache.set(cache_key, value, ttl)
    
    @classmethod
    def get_cached_metrics(cls) -> Dict:
        """Get recent metrics from cache"""
        return {
            'last_retrieval': cache.get('rag_metric:last_retrieval'),
            'last_reranking': cache.get('rag_metric:last_reranking'),
        }
    
    @classmethod
    def set_active_config(cls, component: str, value: str):
        """Set active configuration"""
        rag_active_model.labels(component=component, value=value).set(1)


# ==========================================
#  Performance Timer
# ==========================================

class RAGTimer:
    """Context manager for timing RAG operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        elapsed_ms = (self.end_time - self.start_time) * 1000
        
        logger.debug(f"⏱️  {self.operation_name}: {elapsed_ms:.0f}ms")
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

