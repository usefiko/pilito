"""
Incremental Chunker Service - Auto-chunking for real-time updates
Processes single items (QAPair, Product, WebPage) incrementally
Used by Celery tasks triggered by Django signals

🔥 IMPROVED: Persian-aware chunking with metadata
"""
import logging
import uuid
from typing import Optional, List
from django.core.cache import cache
from .persian_chunker import PersianChunker, ChunkMetadata

logger = logging.getLogger(__name__)


class IncrementalChunker:
    """
    Incremental chunking service for real-time knowledge updates
    Processes one item at a time (not batch)
    Idempotent: Safe to retry
    """
    
    def __init__(self, user):
        self.user = user
    
    def chunk_qapair(self, qa) -> bool:
        """
        Chunk a single QAPair
        Idempotent: Deletes old chunk first
        
        Args:
            qa: QAPair instance
            
        Returns:
            bool: Success status
        """
        try:
            from AI_model.models import TenantKnowledge
            from AI_model.services.embedding_service import EmbeddingService
            
            # Delete existing chunk for this QAPair (idempotency)
            TenantKnowledge.objects.filter(
                user=self.user,
                source_id=qa.id,
                chunk_type='faq'
            ).delete()
            
            # Build full text
            full_text = f"Q: {qa.question}\n\nA: {qa.answer}"
            
            # Generate TL;DR
            tldr = self._extract_tldr(full_text, max_words=100)
            
            # Generate embeddings
            embedding_service = EmbeddingService()
            tldr_embedding = embedding_service.get_embedding(tldr)
            full_embedding = embedding_service.get_embedding(full_text)
            
            if not tldr_embedding or not full_embedding:
                logger.error(f"Failed to generate embeddings for QAPair {qa.id}")
                return False
            
            # Create chunk
            TenantKnowledge.objects.create(
                user=self.user,
                chunk_type='faq',
                source_id=qa.id,
                section_title=qa.question[:200],  # Truncate if too long
                full_text=full_text,
                tldr=tldr,
                tldr_embedding=tldr_embedding,
                full_embedding=full_embedding,
                word_count=len(full_text.split())
            )
            
            logger.info(f"✅ Chunked QAPair {qa.id} for user {self.user.username}")
            
            # Invalidate cache
            cache.delete(f'knowledge_stats:{self.user.id}')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to chunk QAPair {qa.id}: {e}")
            raise
    
    def chunk_product(self, product) -> bool:
        """
        Chunk a single Product
        Idempotent: Deletes old chunk first
        
        Args:
            product: Product instance
            
        Returns:
            bool: Success status
        """
        try:
            from AI_model.models import TenantKnowledge
            from AI_model.services.embedding_service import EmbeddingService
            
            # Delete existing chunk (idempotency)
            TenantKnowledge.objects.filter(
                user=self.user,
                source_id=product.id,
                chunk_type='product'
            ).delete()
            
            # Build full text
            full_text = f"**{product.title}**\n\n{product.description or ''}"
            if product.price:
                full_text += f"\n\nPrice: {product.price}"
            if product.link:
                full_text += f"\n\nLink: {product.link}"
            
            # Generate TL;DR
            tldr = self._extract_tldr(full_text, max_words=80)
            
            # Generate embeddings
            embedding_service = EmbeddingService()
            tldr_embedding = embedding_service.get_embedding(tldr)
            full_embedding = embedding_service.get_embedding(full_text)
            
            if not tldr_embedding or not full_embedding:
                logger.error(f"Failed to generate embeddings for Product {product.id}")
                return False
            
            # Create chunk
            TenantKnowledge.objects.create(
                user=self.user,
                chunk_type='product',
                source_id=product.id,
                section_title=product.title[:200],
                full_text=full_text,
                tldr=tldr,
                tldr_embedding=tldr_embedding,
                full_embedding=full_embedding,
                word_count=len(full_text.split())
            )
            
            logger.info(f"✅ Chunked Product {product.id} for user {self.user.username}")
            
            # Invalidate cache
            cache.delete(f'knowledge_stats:{self.user.id}')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to chunk Product {product.id}: {e}")
            raise
    
    def chunk_webpage(self, page) -> bool:
        """
        🔥 IMPROVED: Chunk a single WebPage with Persian-aware chunking + metadata
        
        Improvements:
        - Token-based chunking (not word-based) for accurate control
        - Persian language detection and handling
        - Metadata extraction (keywords, h1/h2 tags)
        - Better TL;DR (extractive, Persian-aware)
        
        Args:
            page: WebsitePage instance
            
        Returns:
            bool: Success status
        """
        try:
            from AI_model.models import TenantKnowledge
            from AI_model.services.embedding_service import EmbeddingService
            
            # Delete existing chunks for this page (idempotency)
            TenantKnowledge.objects.filter(
                user=self.user,
                source_id=page.id,
                chunk_type='website'
            ).delete()
            
            # Get content (use cleaned_content or raw_content)
            content = page.cleaned_content or page.raw_content or page.summary or ''
            if not content.strip():
                logger.warning(f"WebPage {page.id} has no content to chunk")
                return True  # Not an error, just nothing to do
            
            # ✅ NEW: Persian-aware chunking with metadata
            chunks_with_metadata = PersianChunker.chunk_text_with_metadata(
                text=content,
                chunk_size=512,  # tokens (industry standard)
                overlap=128,     # 25% overlap
                page_title=page.title or '',
                page_url=page.url or '',
                h1_tags=page.h1_tags or [],
                h2_tags=page.h2_tags or []
            )
            
            if not chunks_with_metadata:
                logger.warning(f"No chunks generated for WebPage {page.id}")
                return True
            
            embedding_service = EmbeddingService()
            document_id = uuid.uuid4()  # Group all chunks under same document
            
            # ✅ Phase 1: Prepare all chunks first (bulk operation)
            chunks_to_create = []
            
            for chunk_text, metadata in chunks_with_metadata:
                # ✅ Persian-aware TL;DR
                tldr = PersianChunker.extract_tldr_persian(chunk_text, max_words=100)
                
                # Generate embeddings
                tldr_embedding = embedding_service.get_embedding(tldr)
                full_embedding = embedding_service.get_embedding(chunk_text)
                
                if not tldr_embedding or not full_embedding:
                    logger.warning(
                        f"Failed to generate embeddings for WebPage {page.id} "
                        f"chunk {metadata.chunk_index + 1}"
                    )
                    continue
                
                # Create chunk with metadata
                section_title = (
                    page.title if metadata.chunk_index == 0 
                    else f"{page.title} - Part {metadata.chunk_index + 1}"
                )
                
                # ✅ Store metadata as JSON for RAG retrieval
                chunk_metadata = {
                    'page_url': metadata.page_url,
                    'keywords': metadata.keywords,
                    'h1_tags': metadata.h1_tags,
                    'h2_tags': metadata.h2_tags,
                    'chunk_index': metadata.chunk_index,
                    'total_chunks': metadata.total_chunks,
                    'language': metadata.language
                }
                
                # Append to list (not saved yet)
                chunks_to_create.append(
                    TenantKnowledge(
                        user=self.user,
                        chunk_type='website',
                        source_id=page.id,
                        document_id=document_id,
                        section_title=section_title[:200],
                        full_text=chunk_text,
                        tldr=tldr,
                        tldr_embedding=tldr_embedding,
                        full_embedding=full_embedding,
                        word_count=len(chunk_text.split()),
                        metadata=chunk_metadata
                    )
                )
            
            # ✅ Phase 2: Bulk insert (single DB transaction, 6x faster!)
            if chunks_to_create:
                from django.db import IntegrityError
                try:
                    # Try bulk create with ignore_conflicts (handles duplicates gracefully)
                    TenantKnowledge.objects.bulk_create(
                        chunks_to_create,
                        batch_size=100,
                        ignore_conflicts=True  # Skip duplicates from race conditions
                    )
                    logger.info(
                        f"✅ Created {len(chunks_to_create)} chunks for WebPage {page.id} "
                        f"(language: {chunks_with_metadata[0][1].language})"
                    )
                except IntegrityError as e:
                    # Fallback: Try individual inserts for partial success
                    logger.warning(f"⚠️ Bulk create had conflicts, trying individual inserts: {e}")
                    success_count = 0
                    for chunk in chunks_to_create:
                        try:
                            chunk.save()
                            success_count += 1
                        except IntegrityError:
                            pass  # Skip duplicate
                    logger.info(f"✅ Created {success_count}/{len(chunks_to_create)} new chunks")
            else:
                logger.warning(f"⚠️ No chunks created for WebPage {page.id} (embedding failures)")
            
            # Invalidate cache
            cache.delete(f'knowledge_stats:{self.user.id}')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to chunk WebPage {page.id}: {e}")
            raise
    
    def chunk_manual_prompt(self) -> bool:
        """
        🔥 IMPROVED: Chunk user's manual prompt with Persian-aware chunking
        
        Args:
            None
            
        Returns:
            bool: Success status
        """
        try:
            from AI_model.models import TenantKnowledge
            from AI_model.services.embedding_service import EmbeddingService
            from settings.models import AIPrompts
            
            # Get manual prompt
            try:
                ai_prompts = AIPrompts.objects.get(user=self.user)
            except AIPrompts.DoesNotExist:
                logger.info(f"No AIPrompts found for user {self.user.username}")
                return True  # Not an error
            
            if not ai_prompts.manual_prompt or not ai_prompts.manual_prompt.strip():
                logger.info(f"Manual prompt is empty for user {self.user.username}")
                return True  # Not an error
            
            # Delete existing manual chunks (idempotency)
            TenantKnowledge.objects.filter(
                user=self.user,
                chunk_type='manual'
            ).delete()
            
            manual_text = ai_prompts.manual_prompt.strip()
            
            # ✅ NEW: Persian-aware chunking
            chunks_with_metadata = PersianChunker.chunk_text_with_metadata(
                text=manual_text,
                chunk_size=512,
                overlap=128,
                page_title="Manual Prompt",
                page_url="",
                h1_tags=[],
                h2_tags=[]
            )
            
            embedding_service = EmbeddingService()
            document_id = uuid.uuid4()  # Group all chunks under same document
            
            for chunk_text, metadata in chunks_with_metadata:
                # ✅ NEW: Persian-aware TL;DR
                tldr = PersianChunker.extract_tldr_persian(chunk_text, max_words=100)
                
                # Generate embeddings
                tldr_embedding = embedding_service.get_embedding(tldr)
                full_embedding = embedding_service.get_embedding(chunk_text)
                
                if not tldr_embedding or not full_embedding:
                    logger.warning(f"Failed to generate embeddings for Manual Prompt chunk {metadata.chunk_index + 1}")
                    continue
                
                # Create chunk
                TenantKnowledge.objects.create(
                    user=self.user,
                    chunk_type='manual',
                    document_id=document_id,
                    section_title=f"Manual Prompt - Part {metadata.chunk_index + 1}",
                    full_text=chunk_text,
                    tldr=tldr,
                    tldr_embedding=tldr_embedding,
                    full_embedding=full_embedding,
                    word_count=len(chunk_text.split())
                )
            
            logger.info(
                f"✅ Chunked Manual Prompt into {len(chunks_with_metadata)} chunks "
                f"for user {self.user.username} (language: {chunks_with_metadata[0][1].language})"
            )
            
            # Invalidate cache
            cache.delete(f'knowledge_stats:{self.user.id}')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to chunk Manual Prompt for user {self.user.username}: {e}")
            raise
    
    def delete_chunks_for_source(self, source_id: uuid.UUID, chunk_type: str) -> int:
        """
        Delete chunks for a deleted source
        Called from post_delete signals
        
        Args:
            source_id: UUID of deleted source
            chunk_type: Type of chunk (faq, product, website)
            
        Returns:
            int: Number of chunks deleted
        """
        try:
            from AI_model.models import TenantKnowledge
            
            deleted_count = TenantKnowledge.objects.filter(
                user=self.user,
                source_id=source_id,
                chunk_type=chunk_type
            ).delete()[0]
            
            if deleted_count > 0:
                logger.info(f"✅ Deleted {deleted_count} chunks for {chunk_type} source {source_id}")
                # Invalidate cache
                cache.delete(f'knowledge_stats:{self.user.id}')
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete chunks for {chunk_type} {source_id}: {e}")
            return 0
    
    # Helper methods
    
    @staticmethod
    def _chunk_text(text: str, max_words: int = 500) -> List[str]:
        """
        ⚠️ DEPRECATED: Use PersianChunker.chunk_text_with_metadata instead
        
        Split text into chunks of approximately max_words
        Kept for backward compatibility
        """
        # Delegate to PersianChunker
        chunks_with_metadata = PersianChunker.chunk_text_with_metadata(
            text=text,
            chunk_size=int(max_words * 1.25),  # words to tokens approximation
            overlap=int(max_words * 0.25),
            page_title="",
            page_url="",
            h1_tags=[],
            h2_tags=[]
        )
        
        # Return just the text (without metadata)
        return [chunk_text for chunk_text, _ in chunks_with_metadata]
    
    @staticmethod
    def _extract_tldr(text: str, max_words: int = 100) -> str:
        """
        ⚠️ DEPRECATED: Use PersianChunker.extract_tldr_persian instead
        
        Extract TL;DR summary (extractive approach)
        Kept for backward compatibility
        """
        return PersianChunker.extract_tldr_persian(text, max_words=max_words)
