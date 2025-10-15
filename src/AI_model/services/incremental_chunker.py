"""
Incremental Chunker Service - Auto-chunking for real-time updates
Processes single items (QAPair, Product, WebPage) incrementally
Used by Celery tasks triggered by Django signals
"""
import logging
import uuid
from typing import Optional, List
from django.core.cache import cache

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
        Chunk a single WebPage
        May create multiple chunks if content is large
        Idempotent: Deletes old chunks first
        
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
            
            # Split into chunks if content is large
            chunks = self._chunk_text(content, max_words=500)
            
            embedding_service = EmbeddingService()
            document_id = uuid.uuid4()  # Group all chunks under same document
            
            for i, chunk_text in enumerate(chunks):
                # Generate TL;DR for each chunk
                tldr = self._extract_tldr(chunk_text, max_words=100)
                
                # Generate embeddings
                tldr_embedding = embedding_service.get_embedding(tldr)
                full_embedding = embedding_service.get_embedding(chunk_text)
                
                if not tldr_embedding or not full_embedding:
                    logger.warning(f"Failed to generate embeddings for WebPage {page.id} chunk {i+1}")
                    continue
                
                # Create chunk
                section_title = page.title if i == 0 else f"{page.title} - Part {i+1}"
                
                TenantKnowledge.objects.create(
                    user=self.user,
                    chunk_type='website',
                    source_id=page.id,
                    document_id=document_id,
                    section_title=section_title[:200],
                    full_text=chunk_text,
                    tldr=tldr,
                    tldr_embedding=tldr_embedding,
                    full_embedding=full_embedding,
                    word_count=len(chunk_text.split())
                )
            
            logger.info(f"✅ Chunked WebPage {page.id} into {len(chunks)} chunks for user {self.user.username}")
            
            # Invalidate cache
            cache.delete(f'knowledge_stats:{self.user.id}')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to chunk WebPage {page.id}: {e}")
            raise
    
    def chunk_manual_prompt(self) -> bool:
        """
        Chunk user's manual prompt
        Expensive operation (large text)
        Idempotent: Deletes old chunks first
        
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
            
            # Split into chunks
            chunks = self._chunk_text(manual_text, max_words=500)
            
            embedding_service = EmbeddingService()
            document_id = uuid.uuid4()  # Group all chunks under same document
            
            for i, chunk_text in enumerate(chunks):
                # Generate TL;DR
                tldr = self._extract_tldr(chunk_text, max_words=100)
                
                # Generate embeddings
                tldr_embedding = embedding_service.get_embedding(tldr)
                full_embedding = embedding_service.get_embedding(chunk_text)
                
                if not tldr_embedding or not full_embedding:
                    logger.warning(f"Failed to generate embeddings for Manual Prompt chunk {i+1}")
                    continue
                
                # Create chunk
                TenantKnowledge.objects.create(
                    user=self.user,
                    chunk_type='manual',
                    document_id=document_id,
                    section_title=f"Manual Prompt - Part {i+1}",
                    full_text=chunk_text,
                    tldr=tldr,
                    tldr_embedding=tldr_embedding,
                    full_embedding=full_embedding,
                    word_count=len(chunk_text.split())
                )
            
            logger.info(f"✅ Chunked Manual Prompt into {len(chunks)} chunks for user {self.user.username}")
            
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
        Split text into chunks of approximately max_words
        Preserves paragraph boundaries
        """
        if not text:
            return []
        
        words = text.split()
        if len(words) <= max_words:
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = []
        current_words = 0
        
        for para in paragraphs:
            para_words = len(para.split())
            
            if current_words + para_words <= max_words:
                current_chunk.append(para)
                current_words += para_words
            else:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                
                if para_words > max_words:
                    # Split large paragraph by sentences
                    sentences = para.split('. ')
                    temp_chunk = []
                    temp_words = 0
                    
                    for sent in sentences:
                        sent_words = len(sent.split())
                        if temp_words + sent_words <= max_words:
                            temp_chunk.append(sent)
                            temp_words += sent_words
                        else:
                            if temp_chunk:
                                chunks.append('. '.join(temp_chunk) + '.')
                            temp_chunk = [sent]
                            temp_words = sent_words
                    
                    if temp_chunk:
                        chunks.append('. '.join(temp_chunk) + '.')
                    
                    current_chunk = []
                    current_words = 0
                else:
                    current_chunk = [para]
                    current_words = para_words
        
        # Add remaining
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks if chunks else [text[:max_words * 5]]
    
    @staticmethod
    def _extract_tldr(text: str, max_words: int = 100) -> str:
        """
        Extract TL;DR summary (extractive approach)
        Falls back to truncation if text is very short
        """
        words = text.split()
        
        # If text is already short enough
        if len(words) <= max_words:
            return text
        
        # Simple extractive summary: first max_words words
        return ' '.join(words[:max_words]) + '...'
