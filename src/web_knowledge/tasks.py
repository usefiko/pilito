"""
Celery tasks for web_knowledge app
Handles async processing of website crawling, content extraction, and Q&A generation
"""
import logging
from celery import shared_task
from django.utils import timezone
from typing import Optional, Dict, Any

# ✅ Setup proxy BEFORE any AI imports (required for Iran servers)
from core.utils import setup_ai_proxy
setup_ai_proxy()

from .models import WebsiteSource, WebsitePage, QAPair, CrawlJob
from .services.crawler_service import WebsiteCrawler, ContentExtractor
from .services.qa_generator import QAGenerator

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, time_limit=3600, soft_time_limit=3300)
def crawl_website_task(self, website_source_id: str) -> Dict[str, Any]:
    """
    Async task to crawl a website and extract content
    
    Args:
        website_source_id: UUID of the WebsiteSource to crawl
        
    Returns:
        Dict with task results
    """
    try:
        # Get website source
        website_source = WebsiteSource.objects.get(id=website_source_id)
        
        # Create crawl job
        crawl_job = CrawlJob.objects.create(
            website=website_source,
            celery_task_id=self.request.id,
            job_status='running',
            started_at=timezone.now()
        )
        
        # Update website status
        website_source.crawl_status = 'crawling'
        website_source.crawl_started_at = timezone.now()
        website_source.save()
        
        logger.info(f"Starting crawl for website: {website_source.name} ({website_source.url})")
        
        # Initialize crawler
        crawler = WebsiteCrawler(
            base_url=website_source.url,
            max_pages=website_source.max_pages,
            max_depth=website_source.crawl_depth,
            include_external=website_source.include_external_links,
            delay=0.1  # ✅ Fast crawling for domestic servers (0.1s = 600 pages/min theoretical)
        )
        
        # Progress callback function
        def progress_callback(percentage, pages_crawled, current_url, total_pages=None):
            website_source.refresh_from_db()
            
            # Use the percentage provided by the crawler, but ensure it's reasonable
            actual_percentage = max(0, min(percentage, 100))
            website_source.crawl_progress = actual_percentage
            website_source.save(update_fields=['crawl_progress'])
            
            crawl_job.refresh_from_db()
            crawl_job.pages_crawled = pages_crawled
            
            # Update total pages if provided or if we need to adjust the estimate
            if total_pages is not None and total_pages > crawl_job.pages_to_crawl:
                crawl_job.pages_to_crawl = total_pages
                crawl_job.save(update_fields=['pages_crawled', 'pages_to_crawl'])
            elif pages_crawled > crawl_job.pages_to_crawl:
                # If we've crawled more than estimated, increase the estimate
                crawl_job.pages_to_crawl = pages_crawled + 10  # Add buffer
                crawl_job.save(update_fields=['pages_crawled', 'pages_to_crawl'])
            else:
                crawl_job.save(update_fields=['pages_crawled'])
            
            logger.info(f"Crawl progress: {actual_percentage:.1f}% ({pages_crawled}/{crawl_job.pages_to_crawl}) - {current_url}")
        
        # Try to estimate total pages for better progress tracking
        try:
            # Set an initial estimate based on max_pages or a reasonable default
            initial_estimate = min(website_source.max_pages or 50, 50)
            crawl_job.pages_to_crawl = initial_estimate
            crawl_job.save(update_fields=['pages_to_crawl'])
            
            logger.info(f"Initial crawl estimate: {initial_estimate} pages")
        except Exception as e:
            logger.warning(f"Could not set initial estimate: {e}")
        
        # Start crawling
        crawled_pages = crawler.crawl(progress_callback=progress_callback)
        
        # Save crawled pages to database
        saved_pages = 0
        failed_pages = 0
        
        for i, page_data in enumerate(crawled_pages):
            try:
                # Check if page already exists
                existing_page = WebsitePage.objects.filter(url=page_data['url']).first()
                
                if existing_page:
                    # Update existing page
                    page = existing_page
                    page.website = website_source
                else:
                    # Create new page
                    page = WebsitePage(website=website_source, url=page_data['url'])
                
                # Update page data
                page.title = page_data.get('title', '')
                page.raw_content = page_data.get('raw_content', '')
                page.cleaned_content = page_data.get('cleaned_content', '')
                page.meta_description = page_data.get('meta_description', '')
                page.meta_keywords = page_data.get('meta_keywords', '')
                page.h1_tags = page_data.get('h1_tags', [])
                page.h2_tags = page_data.get('h2_tags', [])
                page.links = page_data.get('links', [])
                page.word_count = page_data.get('word_count', 0)
                page.processing_status = 'pending'
                
                page.save()
                saved_pages += 1
                
                # ✅ Stagger processing tasks to prevent thundering herd
                # Formula: (i * 1.5) seconds spreads 200 pages over ~5 minutes
                # Example: page 0=0s, page 100=150s, page 200=300s
                countdown = int(i * 1.5)
                
                process_page_content_task.apply_async(
                    args=[str(page.id)],
                    countdown=countdown
                )
                
                # Log progress every 50 pages
                if (i + 1) % 50 == 0:
                    logger.info(
                        f"⏳ Queued {i + 1}/{len(crawled_pages)} page processing tasks "
                        f"(spread over ~{int(countdown / 60)} minutes)"
                    )
                
            except Exception as e:
                logger.error(f"Error saving page {page_data.get('url', 'unknown')}: {str(e)}")
                failed_pages += 1
        
        # Log completion with timing info
        if saved_pages > 0:
            total_time_minutes = int((saved_pages * 1.5) / 60)
            logger.info(
                f"✅ All {saved_pages} processing tasks queued "
                f"(staggered over ~{total_time_minutes} minutes to prevent overload)"
            )
        
        # Update website source status
        website_source.crawl_status = 'completed'
        website_source.crawl_completed_at = timezone.now()
        website_source.last_crawl_at = timezone.now()
        
        # Debug: Log current state before update
        logger.info(f"Before update_progress: status={website_source.crawl_status}, progress={website_source.crawl_progress}%")
        
        website_source.update_progress()  # Update counts first
        
        # Debug: Log state after update_progress
        logger.info(f"After update_progress: status={website_source.crawl_status}, progress={website_source.crawl_progress}%")
        
        website_source.crawl_progress = 100.0  # Then force 100% completion
        
        # Debug: Log final state
        logger.info(f"Set final progress to 100%: status={website_source.crawl_status}, progress={website_source.crawl_progress}%")
        
        # Update crawl job
        crawl_job.job_status = 'completed'
        crawl_job.completed_at = timezone.now()
        crawl_job.pages_crawled = saved_pages
        
        # Set pages_to_crawl to the actual number crawled if not set earlier
        if crawl_job.pages_to_crawl == 0:
            crawl_job.pages_to_crawl = len(crawled_pages)
        
        crawl_job.error_pages = [{'url': fail['url'], 'error': fail['error']} 
                                for fail in crawler.failed_urls]
        crawl_job.save()
        
        # Ensure final progress is 100% and save all completion fields
        website_source.crawl_progress = 100.0
        website_source.save(update_fields=['crawl_status', 'crawl_completed_at', 'last_crawl_at', 'crawl_progress'])
        
        # Debug: Verify final state is saved
        website_source.refresh_from_db()
        logger.info(f"Final saved state: status={website_source.crawl_status}, progress={website_source.crawl_progress}%")
        
        crawler.close()
        
        result = {
            'success': True,
            'website_id': str(website_source.id),
            'pages_crawled': saved_pages,
            'failed_pages': failed_pages,
            'total_found': len(crawled_pages),
            'crawl_job_id': str(crawl_job.id)
        }
        
        logger.info(f"Crawl completed for {website_source.name}: {saved_pages} pages saved")
        return result
        
    except WebsiteSource.DoesNotExist:
        logger.error(f"WebsiteSource {website_source_id} not found")
        return {'success': False, 'error': 'Website source not found'}
    
    except Exception as e:
        logger.error(f"Error in crawl_website_task: {str(e)}")
        
        # Update website source on error
        try:
            website_source = WebsiteSource.objects.get(id=website_source_id)
            website_source.crawl_status = 'failed'
            website_source.crawl_error_message = str(e)
            website_source.save()
            
            # Update crawl job if exists
            crawl_job = CrawlJob.objects.filter(
                website=website_source,
                celery_task_id=self.request.id
            ).first()
            
            if crawl_job:
                crawl_job.job_status = 'failed'
                crawl_job.error_message = str(e)
                crawl_job.save()
                
        except Exception as update_error:
            logger.error(f"Error updating website status: {str(update_error)}")
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying crawl task in 60 seconds (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=2)
def process_page_content_task(self, page_id: str) -> Dict[str, Any]:
    """
    Async task to process page content and extract structured information
    
    Args:
        page_id: UUID of the WebsitePage to process
        
    Returns:
        Dict with processing results
    """
    try:
        # Get page
        page = WebsitePage.objects.get(id=page_id)
        
        logger.info(f"Processing content for page: {page.url}")
        
        # Update status
        page.processing_status = 'processing'
        page.save(update_fields=['processing_status'])
        
        # Extract main content
        content_data = ContentExtractor.extract_main_content(
            page.raw_content, 
            page.cleaned_content
        )
        
        # Update page with enhanced content
        page.cleaned_content = content_data['main_content']
        page.word_count = content_data['word_count']
        
        # Extract key information
        key_info = ContentExtractor.extract_key_information(page.cleaned_content)
        
        # ❌ REMOVED: Summary generation (no longer needed - was just extractive trimming)
        # Frontend will use cleaned_content directly for display
        # page.summary = ContentExtractor.create_summary(page.cleaned_content, max_length=1200)
        
        # Update processing status
        page.processing_status = 'completed'
        page.processed_at = timezone.now()
        page.save()
        
        # ❌ DISABLED: Auto Q&A generation removed (industry standard: RAG-only approach)
        # Q&A generation is now optional and can be triggered manually if needed
        # Reason: Most companies (Intercom, Zendesk) use pure RAG without pre-generated Q&A
        # if page.word_count >= 100:
        #     generate_qa_pairs_task.delay(str(page.id))
        
        # ============ NEW: Auto Product Extraction (Optional) ============
        # This section is completely isolated and won't affect the main task if it fails
        products_extracted = 0
        try:
            # Only extract if enabled for this website
            if page.website.auto_extract_products:
                from web_knowledge.services.product_extractor import ProductExtractor
                
                logger.info(f"🔍 Starting product auto-extraction for {page.url}")
                
                user = page.website.user
                extractor = ProductExtractor(user)
                
                # Hybrid extraction (rule pre-filter + AI)
                extracted_products = extractor.extract_and_save(page)
                products_extracted = len(extracted_products)
                
                if products_extracted > 0:
                    logger.info(
                        f"✅ Auto-extracted {products_extracted} products from {page.url}"
                    )
        
        except Exception as product_error:
            # Product extraction failure is non-critical
            # Log the error but don't fail the whole task
            logger.error(f"⚠️ Product extraction failed (non-critical): {product_error}")
            import traceback
            logger.debug(traceback.format_exc())
            # Continue processing - Q&A and other features still work
        # ============ END Product Extraction ============
        
        result = {
            'success': True,
            'page_id': str(page.id),
            'word_count': page.word_count,
            'has_summary': bool(page.summary),
            'key_info': key_info,
            'products_extracted': products_extracted  # NEW: Track extracted products
        }
        
        logger.info(f"Content processing completed for page: {page.url}")
        return result
        
    except WebsitePage.DoesNotExist:
        logger.error(f"WebsitePage {page_id} not found")
        return {'success': False, 'error': 'Page not found'}
    
    except Exception as e:
        logger.error(f"Error in process_page_content_task: {str(e)}")
        
        # Update page status on error
        try:
            page = WebsitePage.objects.get(id=page_id)
            page.processing_status = 'failed'
            page.processing_error = str(e)
            page.save()
        except Exception:
            pass
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying content processing in 30 seconds")
            raise self.retry(exc=e, countdown=30)
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=5, default_retry_delay=10)  # ✅ Increased retries 2→5
def generate_qa_pairs_task(self, page_id: str, max_pairs: int = 10) -> Dict[str, Any]:
    """
    🔥 IMPROVED: Async task to generate Q&A pairs using AI ONLY
    
    Changes:
    - ❌ Removed fallback Q&A generation (low quality)
    - ✅ Increased retries: 2 → 5
    - ✅ Auto-retry on failure instead of generating generic Q&A
    
    Args:
        page_id: UUID of the WebsitePage to generate Q&A for
        max_pairs: Maximum number of Q&A pairs to generate
        
    Returns:
        Dict with generation results
    """
    try:
        # Get page
        page = WebsitePage.objects.get(id=page_id)
        
        logger.info(f"Generating Q&A pairs for page: {page.url}")
        
        # Check if content is suitable for Q&A generation
        if not page.cleaned_content or page.word_count < 100:
            logger.warning(f"Page {page.url} has insufficient content for Q&A generation")
            return {'success': False, 'error': 'Insufficient content'}
        
        # ✅ Get user for token consumption
        user = page.website.user if page.website else None
        
        # Initialize Q&A generator with user
        qa_generator = QAGenerator(user=user)
        
        if not qa_generator.is_available():
            # ❌ No fallback - Retry instead
            logger.error("Q&A generator AI not available - will retry")
            raise Exception("AI not available - retrying")
        
        # ✅ Generate Q&A pairs using AI ONLY
        qa_pairs_data = qa_generator.generate_qa_pairs(
            content=page.cleaned_content,
            page_title=page.title,
            max_pairs=max_pairs
        )
        
        if not qa_pairs_data:
            # ❌ No fallback - Retry instead
            logger.error(f"AI failed to generate Q&A for page: {page.url} - will retry")
            raise Exception("AI generation failed - retrying")
        
        # ✅ Accept whatever AI generated (no minimum requirement)
        if not qa_pairs_data:
            logger.error(f"Failed to generate any Q&A pairs for page: {page.url}")
            return {'success': False, 'error': 'No Q&A pairs generated'}
        
        # Save Q&A pairs to database with smart deduplication
        saved_pairs = 0
        skipped_duplicates = 0
        
        for qa_data in qa_pairs_data:
            try:
                question = qa_data['question']
                
                # Check for exact duplicate in database (case-insensitive)
                existing_exact = QAPair.objects.filter(
                    page__website=page.website,
                    question__iexact=question
                ).first()
                
                if existing_exact:
                    logger.debug(f"⏭️  Skipped duplicate in DB: {question[:80]}")
                    skipped_duplicates += 1
                    continue
                
                # Check for similar questions in database (to avoid near-duplicates across pages)
                from django.db.models import Q
                
                # Extract key words from question for similarity check
                question_lower = question.lower()
                key_words = [w for w in question_lower.split() if len(w) > 4][:5]  # Top 5 words longer than 4 chars
                
                if key_words:
                    # Build query to find similar questions
                    similar_query = Q()
                    for word in key_words:
                        similar_query |= Q(question__icontains=word)
                    
                    similar_questions = QAPair.objects.filter(
                        page__website=page.website
                    ).filter(similar_query)[:20]  # Limit to 20 for performance
                    
                    # Check each for actual similarity
                    is_duplicate = False
                    for similar_qa in similar_questions:
                        # Simple word overlap check
                        words1 = set(question_lower.split())
                        words2 = set(similar_qa.question.lower().split())
                        
                        if words1 and words2:
                            overlap = len(words1.intersection(words2))
                            union = len(words1.union(words2))
                            similarity = overlap / union if union > 0 else 0
                            
                            if similarity >= 0.7:  # 70% similar
                                logger.debug(f"⏭️  Skipped similar in DB (similarity: {similarity:.2f}): {question[:80]}")
                                is_duplicate = True
                                skipped_duplicates += 1
                                break
                    
                    if is_duplicate:
                        continue
                
                # Create Q&A pair if passed all checks
                qa_pair = QAPair.objects.create(
                    page=page,
                    question=qa_data['question'],
                    answer=qa_data['answer'],
                    context=qa_data.get('context', ''),
                    confidence_score=qa_data.get('confidence', 0.8),
                    question_type=qa_data.get('question_type', 'factual'),
                    category=qa_data.get('category', 'general'),
                    keywords=qa_data.get('keywords', []),
                    created_by_ai=qa_data.get('created_by_ai', True),
                    generation_status='completed'
                )
                saved_pairs += 1
                logger.debug(f"✅ Saved Q&A: {question[:80]}")
                
            except Exception as e:
                logger.error(f"❌ Error saving Q&A pair: {str(e)}")
        
        # Update website source Q&A count (but don't overwrite completed crawl progress)
        page.website.update_progress()
        
        result = {
            'success': True,
            'page_id': str(page.id),
            'qa_pairs_generated': saved_pairs,
            'total_attempted': len(qa_pairs_data),
            'skipped_duplicates': skipped_duplicates
        }
        
        logger.info(f"✅ Q&A Generation: {saved_pairs} saved, {skipped_duplicates} duplicates skipped for page: {page.url}")
        return result
        
    except WebsitePage.DoesNotExist:
        logger.error(f"WebsitePage {page_id} not found")
        return {'success': False, 'error': 'Page not found'}
    
    except Exception as e:
        logger.error(f"Error in generate_qa_pairs_task: {str(e)}")
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying Q&A generation in 60 seconds")
            raise self.retry(exc=e, countdown=60)
        
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_crawl_jobs():
    """
    Periodic task to cleanup old crawl jobs and update website statuses
    """
    try:
        from datetime import timedelta
        
        # Delete crawl jobs older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        old_jobs = CrawlJob.objects.filter(created_at__lt=cutoff_date)
        deleted_count = old_jobs.count()
        old_jobs.delete()
        
        logger.info(f"Cleaned up {deleted_count} old crawl jobs")
        
        # Reset stuck crawling jobs (running for more than 2 hours)
        stuck_cutoff = timezone.now() - timedelta(hours=2)
        stuck_jobs = CrawlJob.objects.filter(
            job_status='running',
            started_at__lt=stuck_cutoff
        )
        
        for job in stuck_jobs:
            job.job_status = 'failed'
            job.error_message = 'Job timeout - marked as failed'
            job.save()
            
            # Update corresponding website source
            if job.website:
                job.website.crawl_status = 'failed'
                job.website.crawl_error_message = 'Crawl job timed out'
                job.website.save()
        
        stuck_count = stuck_jobs.count()
        if stuck_count > 0:
            logger.info(f"Reset {stuck_count} stuck crawl jobs")
        
        return {
            'success': True,
            'deleted_jobs': deleted_count,
            'reset_stuck_jobs': stuck_count
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_crawl_jobs: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def recrawl_website_task(website_source_id: str) -> Dict[str, Any]:
    """
    Task to recrawl an existing website (update existing pages and find new ones)
    
    Args:
        website_source_id: UUID of the WebsiteSource to recrawl
        
    Returns:
        Dict with recrawl results
    """
    try:
        website_source = WebsiteSource.objects.get(id=website_source_id)
        
        logger.info(f"Starting recrawl for website: {website_source.name}")
        
        # Mark existing pages as needing update
        existing_pages = website_source.pages.all()
        existing_urls = set(existing_pages.values_list('url', flat=True))
        
        # Start fresh crawl
        result = crawl_website_task.delay(website_source_id).get()
        
        if result.get('success'):
            # Find new pages
            new_pages = website_source.pages.exclude(url__in=existing_urls)
            new_count = new_pages.count()
            
            # Update result
            result['new_pages_found'] = new_count
            result['total_existing_pages'] = len(existing_urls)
            
            logger.info(f"Recrawl completed: {new_count} new pages found")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in recrawl_website_task: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=2)
def generate_enhanced_qa_pairs_task(self, page_id: str, max_pairs: int = 8, 
                                   categories: list = None, question_types: list = None) -> Dict[str, Any]:
    """
    Enhanced async task to generate comprehensive Q&A pairs with categories
    
    Args:
        page_id: UUID of the WebsitePage to generate Q&A for
        max_pairs: Maximum number of Q&A pairs to generate
        categories: List of categories to focus on
        question_types: List of question types to generate
        
    Returns:
        Dict with generation results
    """
    try:
        # Get page
        page = WebsitePage.objects.get(id=page_id)
        
        logger.info(f"Generating enhanced Q&A pairs for page: {page.url}")
        
        # Check if content is suitable for Q&A generation
        if not page.cleaned_content or page.word_count < 100:
            logger.warning(f"Page {page.url} has insufficient content for Q&A generation")
            return {'success': False, 'error': 'Insufficient content'}
        
        # ✅ NEW: Get user for token consumption
        user = page.website.user if page.website else None
        
        # Initialize Q&A generator with user
        from .services.qa_generator import QAGenerator
        qa_generator = QAGenerator(user=user)
        
        if not qa_generator.is_available():
            logger.warning("Q&A generator AI not available, using fallback generation for enhanced Q&A")
            # Generate fallback Q&A pairs directly
            all_qa_pairs = _generate_fallback_qa_pairs(page, max_pairs)
        else:
            # Set defaults
            if categories is None:
                categories = ['general', 'contact', 'services']
            if question_types is None:
                question_types = ['factual', 'procedural', 'explanatory']
            
            # Generate multiple rounds of Q&A pairs for different categories
            all_qa_pairs = []
            
            # Generate general Q&A pairs first
            general_pairs = qa_generator.generate_qa_pairs(
                content=page.cleaned_content,
                page_title=page.title,
                max_pairs=max(2, max_pairs // 2)  # At least 2, up to half the total
            )
            all_qa_pairs.extend(general_pairs)
            
            # Generate category-specific Q&A pairs
            remaining_pairs = max_pairs - len(all_qa_pairs)
            if remaining_pairs > 0:
                # Create enhanced prompt for specific categories
                enhanced_content = f"""
                Page Title: {page.title}
                Page Content: {page.cleaned_content}
                
                Focus Categories: {', '.join(categories)}
                Question Types: {', '.join(question_types)}
                
                Generate questions specifically for these categories and types.
                """
                
                category_pairs = qa_generator.generate_qa_pairs(
                    content=enhanced_content,
                    page_title=f"{page.title} - Enhanced Categories",
                    max_pairs=remaining_pairs
                )
                all_qa_pairs.extend(category_pairs)
        
        if not all_qa_pairs:
            logger.warning(f"No Q&A pairs generated for page: {page.url}, trying fallback generation")
            # Fallback: Generate minimum Q&A pairs with simpler approach
            fallback_pairs = _generate_fallback_qa_pairs(page, max_pairs)
            all_qa_pairs.extend(fallback_pairs)
        
        # Ensure minimum 3 Q&A pairs
        if len(all_qa_pairs) < 3:
            logger.info(f"Generating additional Q&A pairs to reach minimum of 3")
            additional_pairs = _generate_fallback_qa_pairs(page, 3 - len(all_qa_pairs))
            all_qa_pairs.extend(additional_pairs)
        
        if not all_qa_pairs:
            logger.error(f"Failed to generate any Q&A pairs for page: {page.url}")
            return {'success': False, 'error': 'No Q&A pairs generated'}
        
        # Save Q&A pairs to database with enhanced categorization
        saved_pairs = 0
        
        for i, qa_data in enumerate(all_qa_pairs[:max_pairs]):
            try:
                # Assign category and question type if not already set
                if 'category' not in qa_data or not qa_data['category']:
                    qa_data['category'] = categories[i % len(categories)]
                
                if 'question_type' not in qa_data or not qa_data['question_type']:
                    qa_data['question_type'] = question_types[i % len(question_types)]
                
                # Ensure keywords exist
                if 'keywords' not in qa_data:
                    # Extract keywords from question and answer
                    import re
                    text = f"{qa_data['question']} {qa_data['answer']}"
                    words = re.findall(r'\b\w{4,}\b', text.lower())  # Words with 4+ chars
                    qa_data['keywords'] = list(set(words))[:5]  # Top 5 unique keywords
                
                qa_pair = QAPair.objects.create(
                    page=page,
                    question=qa_data['question'],
                    answer=qa_data['answer'],
                    context=qa_data.get('context', ''),
                    confidence_score=qa_data.get('confidence', 0.8),
                    question_type=qa_data.get('question_type', 'factual'),
                    category=qa_data.get('category', 'general'),
                    keywords=qa_data.get('keywords', []),
                    created_by_ai=qa_data.get('created_by_ai', True),
                    generation_status='completed'
                )
                saved_pairs += 1
                
            except Exception as e:
                logger.error(f"Error saving enhanced Q&A pair: {str(e)}")
        
        # Update website source Q&A count (but don't overwrite completed crawl progress)
        page.website.update_progress()
        
        result = {
            'success': True,
            'page_id': str(page.id),
            'qa_pairs_generated': saved_pairs,
            'total_attempted': len(all_qa_pairs),
            'categories_used': categories,
            'question_types_used': question_types
        }
        
        logger.info(f"Generated {saved_pairs} enhanced Q&A pairs for page: {page.url}")
        return result
        
    except WebsitePage.DoesNotExist:
        logger.error(f"WebsitePage {page_id} not found")
        return {'success': False, 'error': 'Page not found'}
    
    except Exception as e:
        logger.error(f"Error in generate_enhanced_qa_pairs_task: {str(e)}")
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying enhanced Q&A generation in 60 seconds")
            raise self.retry(exc=e, countdown=60)
        
        return {'success': False, 'error': str(e)}


def _generate_fallback_qa_pairs(page, count: int = 3) -> list:
    """
    Generate fallback Q&A pairs when AI generation fails
    Creates diverse, page-specific Q&A pairs to avoid repetition
    """
    import random
    import hashlib
    import re
    
    fallback_pairs = []
    
    try:
        content = page.cleaned_content or page.raw_content or ""
        title = page.title or "Page"
        url = page.url or ""
        website_name = page.website.name if page.website else "website"
        
        # Extract page-specific information
        page_type = _determine_page_type(url, title, content)
        
        # Create a unique seed based on page URL and content
        content_hash = hashlib.md5((url + title + content[:50]).encode()).hexdigest()
        random.seed(int(content_hash[:8], 16))
        
        # Generate page-specific questions based on page type and content
        question_templates = _get_page_specific_questions(page_type, title, url, content, website_name)
        
        # Shuffle templates and select unique ones
        random.shuffle(question_templates)
        
        # Select the requested number of unique questions
        selected_questions = question_templates[:min(count, len(question_templates))]
        
        # Add created_by_ai flag to all questions
        for question in selected_questions:
            question['created_by_ai'] = False
            
        return selected_questions
        
    except Exception as e:
        logger.error(f"Error generating fallback Q&A pairs: {str(e)}")
        return []


def _determine_page_type(url, title, content):
    """Determine the type of page based on URL and content"""
    url_lower = url.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    if any(word in url_lower for word in ['contact', 'contact-us', 'support']):
        return 'contact'
    elif any(word in url_lower for word in ['pricing', 'price', 'plans', 'subscription']):
        return 'pricing'
    elif any(word in url_lower for word in ['about', 'about-us', 'company']):
        return 'about'
    elif any(word in url_lower for word in ['privacy', 'policy', 'terms', 'legal']):
        return 'legal'
    elif any(word in url_lower for word in ['features', 'product', 'service']):
        return 'features'
    elif url_lower.endswith('/') or 'home' in url_lower or url_lower.count('/') <= 3:
        return 'homepage'
    else:
        return 'general'


def _get_page_specific_questions(page_type, title, url, content, website_name):
    """Generate questions specific to the page type and content"""
    content_snippet = content[:200] + "..." if len(content) > 200 else content
    
    templates = {
        'contact': [
            {
                'question': f"How can I contact {website_name}?",
                'answer': f"You can contact {website_name} through the information provided on this contact page. {content_snippet}",
                'category': 'contact',
                'question_type': 'procedural',
                'keywords': ['contact', website_name.lower()],
                'confidence': 0.85
            },
            {
                'question': f"What contact information is available for {website_name}?",
                'answer': f"This page provides contact information for {website_name}. {content_snippet}",
                'category': 'contact',
                'question_type': 'factual',
                'keywords': ['contact information', website_name.lower()],
                'confidence': 0.80
            },
            {
                'question': f"Where can I find support for {website_name}?",
                'answer': f"Support information for {website_name} can be found on this page. {content_snippet}",
                'category': 'support',
                'question_type': 'procedural',
                'keywords': ['support', website_name.lower()],
                'confidence': 0.82
            }
        ],
        'pricing': [
            {
                'question': f"What are the pricing options for {website_name}?",
                'answer': f"The pricing information for {website_name} is detailed on this page. {content_snippet}",
                'category': 'pricing',
                'question_type': 'factual',
                'keywords': ['pricing', 'options', website_name.lower()],
                'confidence': 0.88
            },
            {
                'question': f"How much does {website_name} cost?",
                'answer': f"The cost and pricing details for {website_name} are available on this page. {content_snippet}",
                'category': 'pricing',
                'question_type': 'factual',
                'keywords': ['cost', 'pricing', website_name.lower()],
                'confidence': 0.85
            },
            {
                'question': f"What subscription plans are available?",
                'answer': f"This page outlines the subscription plans and pricing options available. {content_snippet}",
                'category': 'pricing',
                'question_type': 'factual',
                'keywords': ['subscription', 'plans', 'pricing'],
                'confidence': 0.83
            }
        ],
        'about': [
            {
                'question': f"What is {website_name} about?",
                'answer': f"This page provides information about {website_name} and what we do. {content_snippet}",
                'category': 'general',
                'question_type': 'explanatory',
                'keywords': ['about', website_name.lower()],
                'confidence': 0.87
            },
            {
                'question': f"Who is behind {website_name}?",
                'answer': f"Information about the team and company behind {website_name} can be found here. {content_snippet}",
                'category': 'general',
                'question_type': 'factual',
                'keywords': ['team', 'company', website_name.lower()],
                'confidence': 0.80
            }
        ],
        'legal': [
            {
                'question': f"What are the terms of use for {website_name}?",
                'answer': f"The terms of use and legal information for {website_name} are outlined on this page. {content_snippet}",
                'category': 'policies',
                'question_type': 'factual',
                'keywords': ['terms', 'legal', website_name.lower()],
                'confidence': 0.85
            },
            {
                'question': f"What is the privacy policy?",
                'answer': f"The privacy policy and data handling practices are detailed on this page. {content_snippet}",
                'category': 'policies',
                'question_type': 'factual',
                'keywords': ['privacy', 'policy', 'data'],
                'confidence': 0.83
            }
        ],
        'features': [
            {
                'question': f"What features does {website_name} offer?",
                'answer': f"This page details the features and capabilities offered by {website_name}. {content_snippet}",
                'category': 'services',
                'question_type': 'factual',
                'keywords': ['features', 'capabilities', website_name.lower()],
                'confidence': 0.88
            },
            {
                'question': f"How does {website_name} work?",
                'answer': f"Information about how {website_name} works and its functionality is provided here. {content_snippet}",
                'category': 'services',
                'question_type': 'explanatory',
                'keywords': ['how it works', 'functionality', website_name.lower()],
                'confidence': 0.85
            }
        ],
        'homepage': [
            {
                'question': f"What does {website_name} do?",
                'answer': f"This is the homepage of {website_name}. {content_snippet}",
                'category': 'general',
                'question_type': 'explanatory',
                'keywords': ['homepage', website_name.lower()],
                'confidence': 0.80
            },
            {
                'question': f"How can I get started with {website_name}?",
                'answer': f"You can get started with {website_name} by exploring the information on this homepage. {content_snippet}",
                'category': 'general',
                'question_type': 'procedural',
                'keywords': ['get started', website_name.lower()],
                'confidence': 0.78
            }
        ],
        'general': [
            {
                'question': f"What information is available on this {title} page?",
                'answer': f"This page contains information about {title}. {content_snippet}",
                'category': 'general',
                'question_type': 'factual',
                'keywords': ['information', title.lower()],
                'confidence': 0.75
            },
            {
                'question': f"What can I learn from this page?",
                'answer': f"You can learn about {title} and related topics from this page. {content_snippet}",
                'category': 'general',
                'question_type': 'educational',
                'keywords': ['learn', title.lower()],
                'confidence': 0.72
            }
        ]
    }
    
    return templates.get(page_type, templates['general'])


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_prompt_async_task(self, user_id: int, manual_prompt: str) -> Dict[str, Any]:
    """
    Async task to generate AI-enhanced prompt
    
    Args:
        user_id: ID of the user
        manual_prompt: User's manual prompt to enhance
        
    Returns:
        Dict with generated prompt and metadata
    """
    from django.contrib.auth import get_user_model
    from django.core.cache import cache
    from settings.models import BusinessPrompt
    
    User = get_user_model()
    task_id = self.request.id
    
    # Update status to processing
    cache.set(f'prompt_generation_{task_id}', {
        'status': 'processing',
        'status_fa': 'در حال پردازش',
        'progress': 10,
        'message': 'Initializing AI generation...',
        'message_fa': 'در حال راه‌اندازی تولید هوش مصنوعی...',
        'created_at': timezone.now().isoformat()
    }, timeout=300)  # 5 minutes (reduced from 10)
    
    try:
        user = User.objects.get(id=user_id)
        business_type = user.business_type if hasattr(user, 'business_type') else None
        
        # Find matching BusinessPrompt
        business_prompt_obj = None
        if business_type:
            business_prompt_obj = BusinessPrompt.objects.filter(
                name__iexact=business_type.strip()
            ).first()
        
        # Update status
        cache.set(f'prompt_generation_{task_id}', {
            'status': 'processing',
            'status_fa': 'در حال پردازش',
            'progress': 30,
            'message': 'Checking tokens...',
            'message_fa': 'در حال بررسی توکن‌ها...',
            'created_at': timezone.now().isoformat()
        }, timeout=300)
        
        # ✅ CHECK TOKENS AND SUBSCRIPTION BEFORE AI USAGE
        from billing.utils import check_ai_access_for_user
        
        access_check = check_ai_access_for_user(
            user=user,
            estimated_tokens=700,  # Estimated tokens for prompt enhancement
            feature_name="Async Prompt Enhancement"
        )
        
        if not access_check['has_access']:
            error_message = f"{access_check['message']} (Reason: {access_check['reason']})"
            logger.error(f"Token check failed for async prompt enhancement: {error_message}")
            cache.set(f'prompt_generation_{task_id}', {
                'status': 'failed',
                'status_fa': 'ناموفق',
                'progress': 100,
                'message': error_message,
                'message_fa': f'خطا: {error_message}',
                'error': error_message,
                'error_code': access_check['reason'],
                'tokens_remaining': access_check['tokens_remaining'],
                'days_remaining': access_check['days_remaining'],
                'created_at': timezone.now().isoformat()
            }, timeout=300)
            return {
                'success': False,
                'error': error_message,
                'error_code': access_check['reason']
            }
        
        logger.info(f"Token pre-check passed for async prompt enhancement (user: {user.username})")
        
        # Update status
        cache.set(f'prompt_generation_{task_id}', {
            'status': 'processing',
            'status_fa': 'در حال پردازش',
            'progress': 50,
            'message': 'Generating enhanced prompt with AI...',
            'message_fa': 'در حال تولید پرامپت بهبود یافته با هوش مصنوعی...',
            'created_at': timezone.now().isoformat()
        }, timeout=300)
        
        # Generate with AI
        try:
            # ✅ Setup proxy BEFORE importing Gemini (required for Iran servers)
            from core.utils import setup_ai_proxy
            setup_ai_proxy()
            
            import google.generativeai as genai
            from AI_model.services.gemini_service import get_gemini_api_key
            
            api_key = get_gemini_api_key()
            if not api_key:
                raise ValueError("Gemini API key not configured")
            
            genai.configure(api_key=api_key)
            model_name = 'gemini-2.0-flash-exp'  # ⚡ Faster and cheaper than 2.5-pro
            
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    'temperature': 0.7,
                    'max_output_tokens': 2000,  # Reduced from 3000 for faster generation
                }
            )
            
            # Build instruction
            if business_prompt_obj and business_prompt_obj.prompt:
                instruction = f"""{business_prompt_obj.prompt}

---

## User's Raw Input:
{manual_prompt}

---

## Your Task:
Transform the user's raw input above into a complete, professional, and structured Manual Prompt following the guidelines and format specified in the business prompt template above.

Output ONLY the final structured Manual Prompt.
Do NOT add any explanations or comments outside the prompt structure.
Ensure all information from the user's input is preserved and properly formatted."""
            else:
                instruction = f"""You are an AI assistant helping to create a professional manual prompt for a {business_type or 'business'}.

User's Input:
{manual_prompt}

Task: Rewrite and improve the user's input into a professional, clear, and well-structured manual prompt ready for an AI assistant. Keep all important details (contact info, addresses, services, etc.) but make it professional, organized, and concise.

Output ONLY the improved prompt, nothing else."""
            
            # Update status
            cache.set(f'prompt_generation_{task_id}', {
                'status': 'processing',
                'status_fa': 'در حال پردازش',
                'progress': 70,
                'message': 'Waiting for AI response...',
                'message_fa': 'در انتظار پاسخ هوش مصنوعی...',
                'created_at': timezone.now().isoformat()
            }, timeout=300)
            
            # Configure safety settings
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
            
            # Track timing
            import time
            start_time = time.time()
            
            response = model.generate_content(
                instruction,
                safety_settings=safety_settings
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Update status
            cache.set(f'prompt_generation_{task_id}', {
                'status': 'processing',
                'status_fa': 'در حال پردازش',
                'progress': 90,
                'message': 'Finalizing...',
                'message_fa': 'در حال نهایی‌سازی...',
                'created_at': timezone.now().isoformat()
            }, timeout=300)
            
            # ✅ Extract token usage
            prompt_tokens = 0
            completion_tokens = 0
            if hasattr(response, 'usage_metadata'):
                prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                completion_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
            
            # ✅ Track AI usage in AIUsageLog and AIUsageTracking
            try:
                from AI_model.services.usage_tracker import track_ai_usage_safe
                track_ai_usage_safe(
                    user=user,
                    section='prompt_generation',
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    response_time_ms=response_time_ms,
                    success=True,
                    model_name=model_name,
                    metadata={'business_type': business_type, 'async': True}
                )
                logger.info(f"✅ AI usage tracked for async prompt generation (user: {user.username}, tokens: {prompt_tokens + completion_tokens})")
            except Exception as tracking_error:
                logger.error(f"Failed to track AI usage for async prompt generation: {tracking_error}")
            
            # ✅ Consume tokens for billing
            if response:
                try:
                    actual_tokens = prompt_tokens + completion_tokens
                    if actual_tokens > 0:
                        from billing.services import consume_tokens_for_user
                        consume_tokens_for_user(
                            user,
                            actual_tokens,
                            description='Async prompt enhancement'
                        )
                        logger.info(f"💰 Consumed {actual_tokens} tokens for async prompt enhancement (user: {user.username})")
                except Exception as token_error:
                    logger.error(f"Failed to consume tokens: {token_error}")
            
            if hasattr(response, 'text') and response.text:
                enhanced_prompt = response.text.strip()
            else:
                raise ValueError("No response from AI")
            
            # Success - update cache
            result = {
                'status': 'completed',
                'status_fa': 'تکمیل شد',
                'progress': 100,
                'message': 'Prompt generated successfully',
                'message_fa': 'پرامپت با موفقیت تولید شد',
                'prompt': enhanced_prompt,
                'generated_by_ai': True,
                'created_at': timezone.now().isoformat(),
                'completed_at': timezone.now().isoformat()
            }
            
            cache.set(f'prompt_generation_{task_id}', result, timeout=300)
            
            logger.info(f"Successfully generated prompt asynchronously for user {user.username}")
            
            return {
                'success': True,
                'prompt': enhanced_prompt,
                'generated_by_ai': True
            }
            
        except Exception as ai_error:
            error_msg = str(ai_error)
            logger.error(f"AI generation failed: {error_msg}")
            
            # Track failed AI usage
            try:
                from AI_model.services.usage_tracker import track_ai_usage_safe
                track_ai_usage_safe(
                    user=user,
                    section='prompt_generation',
                    prompt_tokens=0,
                    completion_tokens=0,
                    response_time_ms=0,
                    success=False,
                    model_name='gemini-2.0-flash-exp',
                    error_message=error_msg,
                    metadata={'business_type': business_type, 'async': True, 'error': error_msg}
                )
            except Exception as tracking_error:
                logger.error(f"Failed to track failed AI usage: {tracking_error}")
            
            # Fallback to simple combination
            if business_prompt_obj and business_prompt_obj.prompt:
                enhanced_prompt = f"""{business_prompt_obj.prompt}

{manual_prompt}"""
            else:
                enhanced_prompt = manual_prompt
            
            result = {
                'status': 'completed',
                'status_fa': 'تکمیل شد',
                'progress': 100,
                'message': 'Prompt generated (AI unavailable, using fallback)',
                'message_fa': 'پرامپت تولید شد (هوش مصنوعی در دسترس نبود، از روش جایگزین استفاده شد)',
                'prompt': enhanced_prompt,
                'generated_by_ai': False,
                'warning': 'AI generation failed, using simple combination',
                'warning_fa': 'تولید هوش مصنوعی ناموفق بود، از ترکیب ساده استفاده شد',
                'created_at': timezone.now().isoformat(),
                'completed_at': timezone.now().isoformat()
            }
            
            cache.set(f'prompt_generation_{task_id}', result, timeout=300)
            
            return {
                'success': True,
                'prompt': enhanced_prompt,
                'generated_by_ai': False,
                'warning': 'AI generation failed, using fallback'
            }
    
    except Exception as e:
        logger.error(f"Async prompt generation failed: {str(e)}", exc_info=True)
        
        # Update cache with error
        cache.set(f'prompt_generation_{task_id}', {
            'status': 'failed',
            'status_fa': 'ناموفق',
            'progress': 100,
            'message': f'Failed to generate prompt: {str(e)}',
            'message_fa': f'تولید پرامپت ناموفق بود: {str(e)}',
            'error': str(e),
            'created_at': timezone.now().isoformat()
        }, timeout=300)
        
        return {
            'success': False,
            'error': str(e)
        }
