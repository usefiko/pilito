"""
Knowledge Ingestion Service
Converts existing data (FAQ, Products, Manual, Website) to TenantKnowledge chunks
Generates TL;DR summaries and embeddings
"""
import logging
import uuid
from typing import List, Dict, Optional
from django.db import transaction
from AI_model.services.persian_normalizer import get_normalizer

logger = logging.getLogger(__name__)


class KnowledgeIngestionService:
    """
    Ingests knowledge from various sources into TenantKnowledge model
    
    Sources:
    - FAQ: web_knowledge.QAPair
    - Products: web_knowledge.Product
    - Manual Prompt: settings.AIPrompts
    - Website: web_knowledge.WebsitePage
    """
    
    @classmethod
    def ingest_user_knowledge(cls, user, sources: List[str] = None, force_recreate: bool = False) -> Dict:
        """
        Ingest all knowledge sources for a user
        
        Args:
            user: User instance
            sources: List of sources to ingest (default: all)
                    ['faq', 'products', 'manual', 'website']
            force_recreate: If True, delete existing chunks and recreate
        
        Returns:
            {
                'faq': {'chunks': 10, 'success': True},
                'products': {'chunks': 50, 'success': True},
                'manual': {'chunks': 5, 'success': True},
                'website': {'chunks': 120, 'success': True},
                'total_chunks': 185,
                'errors': []
            }
        """
        if sources is None:
            sources = ['faq', 'products', 'manual', 'website']
        
        results = {
            'faq': {'chunks': 0, 'success': False},
            'products': {'chunks': 0, 'success': False},
            'manual': {'chunks': 0, 'success': False},
            'website': {'chunks': 0, 'success': False},
            'total_chunks': 0,
            'errors': []
        }
        
        # Delete existing chunks if force_recreate
        if force_recreate:
            try:
                from AI_model.models import TenantKnowledge
                deleted_count = TenantKnowledge.objects.filter(user=user).delete()[0]
                logger.info(f"🗑️ Deleted {deleted_count} existing knowledge chunks for {user.username}")
            except Exception as e:
                logger.error(f"Failed to delete existing chunks: {e}")
        
        # Ingest each source
        for source in sources:
            try:
                if source == 'faq':
                    count = cls._ingest_faq(user)
                    results['faq'] = {'chunks': count, 'success': True}
                
                elif source == 'products':
                    count = cls._ingest_products(user)
                    results['products'] = {'chunks': count, 'success': True}
                
                elif source == 'manual':
                    count = cls._ingest_manual_prompt(user)
                    results['manual'] = {'chunks': count, 'success': True}
                
                elif source == 'website':
                    count = cls._ingest_website(user)
                    results['website'] = {'chunks': count, 'success': True}
                
                results['total_chunks'] += count
                logger.info(f"✅ Ingested {count} chunks from {source} for {user.username}")
                
            except Exception as e:
                error_msg = f"Failed to ingest {source}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results['errors'].append(error_msg)
                results[source] = {'chunks': 0, 'success': False, 'error': str(e)}
        
        logger.info(
            f"🎉 Knowledge ingestion complete for {user.username}: "
            f"{results['total_chunks']} total chunks, {len(results['errors'])} errors"
        )
        
        return results
    
    @classmethod
    def _ingest_faq(cls, user) -> int:
        """
        Ingest FAQ (QAPair) into TenantKnowledge
        Each Q&A pair becomes one chunk
        """
        try:
            from web_knowledge.models import QAPair
            from AI_model.models import TenantKnowledge
            from AI_model.services.embedding_service import EmbeddingService
            
            # Get completed Q&A pairs
            qa_pairs = QAPair.objects.filter(
                page__website__user=user,
                generation_status='completed'
            ).select_related('page', 'page__website')
            
            chunks_created = 0
            embedding_service = EmbeddingService()
            
            for qa in qa_pairs:
                # Build full text
                full_text = f"Q: {qa.question}\n\nA: {qa.answer}"
                
                # Generate TL;DR (shorter version)
                tldr = cls._generate_tldr(full_text, max_words=100)
                
                # Generate embeddings
                tldr_embedding = embedding_service.get_embedding(tldr)
                full_embedding = embedding_service.get_embedding(full_text)
                
                if not tldr_embedding or not full_embedding:
                    logger.warning(f"Failed to generate embeddings for QAPair {qa.id}")
                    continue
                
                # Create chunk
                TenantKnowledge.objects.create(
                    user=user,
                    chunk_type='faq',
                    source_id=qa.id,
                    document_id=qa.page.id if qa.page else None,
                    section_title=qa.question[:200],  # Use question as title
                    full_text=full_text,
                    tldr=tldr,
                    tldr_embedding=tldr_embedding,
                    full_embedding=full_embedding,
                    language=cls._detect_language(qa.question),
                    word_count=len(full_text.split()),
                    metadata={
                        'source': qa.page.title if qa.page else 'Unknown',
                        'website': qa.page.website.name if qa.page and qa.page.website else 'Unknown',
                        'confidence_score': float(qa.confidence_score) if qa.confidence_score else 0.0
                    }
                )
                chunks_created += 1
            
            return chunks_created
            
        except Exception as e:
            logger.error(f"FAQ ingestion failed: {e}")
            raise
    
    @classmethod
    def _ingest_products(cls, user) -> int:
        """
        Ingest Products into TenantKnowledge
        Each product becomes one chunk
        """
        try:
            from web_knowledge.models import Product
            from AI_model.models import TenantKnowledge
            from AI_model.services.embedding_service import EmbeddingService
            
            products = Product.objects.filter(user=user, is_active=True)
            
            chunks_created = 0
            embedding_service = EmbeddingService()
            
            for product in products:
                # Build full text
                full_text = f"Product: {product.title}\n"
                full_text += f"Type: {product.get_product_type_display()}\n"
                if product.description:
                    full_text += f"Description: {product.description}\n"
                if product.price:
                    full_text += f"Price: {product.price}\n"
                if product.link:
                    full_text += f"Link: {product.link}\n"
                if product.tags:
                    full_text += f"Tags: {', '.join(product.tags)}\n"
                
                # Generate TL;DR
                tldr = cls._generate_tldr(full_text, max_words=80)
                
                # Generate embeddings
                tldr_embedding = embedding_service.get_embedding(tldr)
                full_embedding = embedding_service.get_embedding(full_text)
                
                if not tldr_embedding or not full_embedding:
                    logger.warning(f"Failed to generate embeddings for Product {product.id}")
                    continue
                
                # Create chunk
                TenantKnowledge.objects.create(
                    user=user,
                    chunk_type='product',
                    source_id=product.id,
                    section_title=product.title,
                    full_text=full_text,
                    tldr=tldr,
                    tldr_embedding=tldr_embedding,
                    full_embedding=full_embedding,
                    language=cls._detect_language(product.title),
                    word_count=len(full_text.split()),
                    metadata={
                        'product_type': product.product_type,
                        'price': float(product.price) if product.price else None,
                        'link': product.link or '',
                        'tags': product.tags or []
                    }
                )
                chunks_created += 1
            
            return chunks_created
            
        except Exception as e:
            logger.error(f"Products ingestion failed: {e}")
            raise
    
    @classmethod
    def _ingest_manual_prompt(cls, user) -> int:
        """
        Ingest Manual Prompt into TenantKnowledge
        Chunks long prompts into sections
        """
        try:
            from settings.models import AIPrompts
            from AI_model.models import TenantKnowledge
            from AI_model.services.embedding_service import EmbeddingService
            
            # Get user's manual prompt
            try:
                ai_prompts = user.ai_prompts
            except AIPrompts.DoesNotExist:
                logger.info(f"No AIPrompts found for {user.username}")
                return 0
            
            if not ai_prompts.manual_prompt or not ai_prompts.manual_prompt.strip():
                logger.info(f"Manual prompt is empty for {user.username}")
                return 0
            
            manual_text = ai_prompts.manual_prompt.strip()
            
            # ✅ Chunk the manual prompt with overlap (700 words, 150 overlap)
            chunks = cls._chunk_text(manual_text, chunk_size=700, overlap=150)
            
            chunks_created = 0
            document_id = uuid.uuid4()  # Group all chunks under same document
            embedding_service = EmbeddingService()
            
            for i, chunk_text in enumerate(chunks):
                # Generate TL;DR
                tldr = cls._generate_tldr(chunk_text, max_words=100)
                
                # Generate embeddings
                tldr_embedding = embedding_service.get_embedding(tldr)
                full_embedding = embedding_service.get_embedding(chunk_text)
                
                if not tldr_embedding or not full_embedding:
                    logger.warning(f"Failed to generate embeddings for Manual chunk {i}")
                    continue
                
                # Create chunk
                TenantKnowledge.objects.create(
                    user=user,
                    chunk_type='manual',
                    document_id=document_id,
                    section_title=f"Manual Prompt - Part {i+1}",
                    full_text=chunk_text,
                    tldr=tldr,
                    tldr_embedding=tldr_embedding,
                    full_embedding=full_embedding,
                    language=cls._detect_language(chunk_text),
                    word_count=len(chunk_text.split()),
                    metadata={'part': i+1, 'total_parts': len(chunks)}
                )
                chunks_created += 1
            
            return chunks_created
            
        except Exception as e:
            logger.error(f"Manual prompt ingestion failed: {e}")
            raise
    
    @classmethod
    def _ingest_website(cls, user) -> int:
        """
        Ingest Website pages into TenantKnowledge
        Each page becomes multiple chunks (if long)
        """
        try:
            from web_knowledge.models import WebsitePage
            from AI_model.models import TenantKnowledge
            from AI_model.services.embedding_service import EmbeddingService
            
            pages = WebsitePage.objects.filter(
                website__user=user,
                processing_status='completed'
            ).select_related('website')
            
            chunks_created = 0
            embedding_service = EmbeddingService()
            
            for page in pages:
                # ✅ Use cleaned_content instead of summary for better quality
                content = page.cleaned_content or page.summary or ''
                if not content.strip():
                    continue
                
                # ✅ Chunk long pages with overlap (600 words, 120 overlap)
                chunks = cls._chunk_text(content, chunk_size=600, overlap=120)
                
                for i, chunk_text in enumerate(chunks):
                    # Build full text with context
                    full_text = f"Page: {page.title or page.url}\n\n{chunk_text}"
                    
                    # Generate TL;DR
                    tldr = cls._generate_tldr(chunk_text, max_words=80)
                    
                    # Generate embeddings
                    tldr_embedding = embedding_service.get_embedding(tldr)
                    full_embedding = embedding_service.get_embedding(full_text)
                    
                    if not tldr_embedding or not full_embedding:
                        logger.warning(f"Failed to generate embeddings for WebsitePage {page.id} chunk {i}")
                        continue
                    
                    # Create chunk
                    TenantKnowledge.objects.create(
                        user=user,
                        chunk_type='website',
                        source_id=page.id,
                        document_id=page.id,  # Group chunks from same page
                        section_title=f"{page.title or 'Page'} - Part {i+1}" if len(chunks) > 1 else page.title,
                        full_text=full_text,
                        tldr=tldr,
                        tldr_embedding=tldr_embedding,
                        full_embedding=full_embedding,
                        language=cls._detect_language(chunk_text),
                        word_count=len(chunk_text.split()),
                        metadata={
                            'url': page.url,
                            'website': page.website.name if page.website else 'Unknown',
                            'part': i+1,
                            'total_parts': len(chunks)
                        }
                    )
                    chunks_created += 1
            
            return chunks_created
            
        except Exception as e:
            logger.error(f"Website ingestion failed: {e}")
            raise
    
    @classmethod
    def _chunk_text(cls, text: str, chunk_size: int = 700, overlap: int = 150) -> List[str]:
        """
        🔥 IMPROVED: Smart text chunking with overlap + Persian normalization
        
        Changes:
        - ✅ Chunk size: 500 → 700 words (+40%)
        - ✅ Added overlap: 150 words (prevents context loss)
        - ✅ Persian normalization (Hazm) before chunking
        - ✅ Better handling of boundaries
        
        Example:
        Text: "A B C D E F G H I J"
        chunk_size=5, overlap=2
        
        Chunk 1: A B C D E
        Chunk 2:       D E F G H
        Chunk 3:             F G H I J
        
        Args:
            text: Text to chunk
            chunk_size: Target words per chunk (default: 700)
            overlap: Words to overlap between chunks (default: 150)
        
        Returns:
            List of text chunks with overlap
        """
        if not text or not text.strip():
            return []
        
        # ✅ Normalize Persian text before chunking
        normalizer = get_normalizer()
        if normalizer.is_persian(text):
            text = normalizer.normalize(text)
            logger.debug("✅ Applied Persian normalization before chunking")
        
        # Split into words for precise control
        words = text.split()
        
        if len(words) <= chunk_size:
            # Text is small enough, return as-is
            return [text]
        
        chunks = []
        i = 0
        
        while i < len(words):
            # Get chunk
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)
            
            # Move forward (with overlap)
            i += (chunk_size - overlap)
            
            # Stop if we've covered the text
            if i + overlap >= len(words):
                # Add final chunk if there's remaining text
                if i < len(words):
                    final_chunk = ' '.join(words[i:])
                    if len(final_chunk.split()) > overlap:  # Only if substantial
                        chunks.append(final_chunk)
                break
        
        logger.debug(f"✅ Chunked {len(words)} words into {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
        return chunks
    
    @classmethod
    def _generate_tldr(cls, text: str, max_words: int = 120) -> str:
        """
        🔥 IMPROVED: Fast extractive TL;DR (NO AI calls)
        
        Changes:
        - ✅ No AI calls → 100x faster, zero cost
        - ✅ Increased from 100 to 120 words
        - ✅ Smart sentence selection (first + middle + last)
        
        Strategy:
        1. First sentence (introduction)
        2. Middle sentences (main content)
        3. Last sentence (conclusion)
        
        Target: 100-120 words
        """
        if not text or not text.strip():
            return ''
        
        # Split into sentences
        import re
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        if not sentences:
            # No sentences found, just trim words
            words = text.split()
            return ' '.join(words[:max_words]) + ('...' if len(words) > max_words else '')
        
        # Simple case: text is already short enough
        word_count = len(text.split())
        if word_count <= max_words:
            return text
        
        # Strategy: First + Middle + Last sentences
        summary_sentences = []
        current_words = 0
        
        # 1. Always include first sentence (introduction)
        if sentences:
            first = sentences[0]
            summary_sentences.append(first)
            current_words += len(first.split())
        
        # 2. Include last sentence if space allows (conclusion)
        if len(sentences) > 1:
            last = sentences[-1]
            last_words = len(last.split())
            if current_words + last_words < max_words * 0.7:  # Leave room for middle
                summary_sentences.append(last)
                current_words += last_words
        
        # 3. Fill with middle sentences
        middle_start = 1
        middle_end = len(sentences) - 1 if len(sentences) > 2 else len(sentences)
        
        for i in range(middle_start, middle_end):
            sent = sentences[i]
            sent_words = len(sent.split())
            
            if current_words + sent_words <= max_words:
                summary_sentences.insert(-1 if len(summary_sentences) > 1 else len(summary_sentences), sent)
                current_words += sent_words
            else:
                break
        
        # Join and clean
        summary = '. '.join(summary_sentences)
        if not summary.endswith('.'):
            summary += '.'
        
        # Final trim if still too long
        words = summary.split()
        if len(words) > max_words:
            summary = ' '.join(words[:max_words]) + '...'
        
        logger.debug(f"✅ Fast TL;DR: {len(text.split())} → {len(summary.split())} words (no AI)")
        return summary
    
    @classmethod
    def _detect_language(cls, text: str) -> str:
        """
        Simple language detection (fa, en, ar, tr)
        """
        if not text:
            return 'en'
        
        # Sample first 100 chars
        sample = text[:100]
        
        # Farsi detection (Persian Unicode range)
        farsi_chars = sum(1 for c in sample if '\u0600' <= c <= '\u06FF')
        if farsi_chars > len(sample) * 0.3:
            return 'fa'
        
        # Arabic detection
        arabic_chars = sum(1 for c in sample if '\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F')
        if arabic_chars > len(sample) * 0.3:
            return 'ar'
        
        # Turkish detection (basic)
        turkish_chars = sum(1 for c in sample if c in 'ğĞıİöÖüÜşŞçÇ')
        if turkish_chars > 2:
            return 'tr'
        
        # Default to English
        return 'en'

