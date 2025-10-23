"""
Knowledge Ingestion Service
Converts existing data (FAQ, Products, Manual, Website) to TenantKnowledge chunks
Generates TL;DR summaries and embeddings
"""
import logging
import uuid
from typing import List, Dict, Optional
from django.db import transaction

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
            
            # Chunk the manual prompt (split by paragraphs or max 500 words)
            chunks = cls._chunk_text(manual_text, max_words=500)
            
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
                # Use summary if available, otherwise cleaned_content
                content = page.summary or page.cleaned_content or ''
                if not content.strip():
                    continue
                
                # Chunk long pages
                chunks = cls._chunk_text(content, max_words=400)
                
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
    def _chunk_text(cls, text: str, max_words: int = 500) -> List[str]:
        """
        Split text into chunks by paragraphs or max words
        """
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_words = 0
        
        for para in paragraphs:
            para_words = len(para.split())
            
            if current_words + para_words <= max_words:
                current_chunk.append(para)
                current_words += para_words
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                
                # Start new chunk
                if para_words > max_words:
                    # Split long paragraph by sentences
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
        
        return chunks if chunks else [text[:max_words * 5]]  # Fallback
    
    @classmethod
    def _generate_tldr(cls, text: str, max_words: int = 100) -> str:
        """
        Generate TL;DR summary using Gemini (extractive fallback)
        Target: 80-120 words
        """
        try:
            # ✅ Setup proxy before importing Gemini
            from core.utils import setup_ai_proxy
            setup_ai_proxy()
            
            import google.generativeai as genai
            from AI_model.models import AIGlobalConfig
            
            # Use lightweight model for summarization
            config = AIGlobalConfig.get_config()
            genai.configure(api_key=config.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-lite')
            
            prompt = f"""Summarize this text in {max_words} words or less. Be concise and capture key points.

Text:
{text[:1000]}

Summary ({max_words} words max):"""
            
            response = model.generate_content(
                prompt,
                generation_config={'temperature': 0.3, 'max_output_tokens': 150}
            )
            
            summary = response.text.strip()
            
            # Verify word count
            if len(summary.split()) > max_words + 20:
                # Trim to max_words
                words = summary.split()
                summary = ' '.join(words[:max_words]) + '...'
            
            return summary
            
        except Exception as e:
            logger.warning(f"TL;DR generation failed: {e}, using extractive fallback")
            # Extractive fallback: first N words
            words = text.split()
            if len(words) <= max_words:
                return text
            return ' '.join(words[:max_words]) + '...'
    
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

