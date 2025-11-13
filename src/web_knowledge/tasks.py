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
                page.images = page_data.get('images', [])
                page.processing_status = 'pending'
                page.save()
                
                saved_pages += 1
                
                # Process page content asynchronously
                process_page_content_task.delay(str(page.id))
                
            except Exception as e:
                logger.error(f"Failed to save page {page_data.get('url', 'unknown')}: {str(e)}")
                failed_pages += 1
                continue
        
        # Update crawl job
        crawl_job.job_status = 'completed'
        crawl_job.pages_crawled = saved_pages
        crawl_job.pages_to_crawl = saved_pages
        crawl_job.completed_at = timezone.now()
        crawl_job.save()
        
        # Update website status
        website_source.crawl_status = 'completed'
        website_source.crawl_progress = 100.0
        website_source.crawl_completed_at = timezone.now()
        website_source.save()
        
        logger.info(f"Crawl completed for {website_source.name}: {saved_pages} pages saved, {failed_pages} failed")
        
        return {
            'success': True,
            'website_id': str(website_source.id),
            'pages_crawled': saved_pages,
            'pages_failed': failed_pages,
            'crawl_job_id': str(crawl_job.id)
        }
        
    except WebsiteSource.DoesNotExist:
        logger.error(f"WebsiteSource {website_source_id} not found")
        return {'success': False, 'error': 'Website source not found'}
    
    except Exception as e:
        logger.error(f"Error in crawl_website_task: {str(e)}")
        
        # Update website status on error
        try:
            website_source = WebsiteSource.objects.get(id=website_source_id)
            website_source.crawl_status = 'failed'
            website_source.save()
            
            # Update crawl job if exists
            crawl_job = CrawlJob.objects.filter(celery_task_id=self.request.id).first()
            if crawl_job:
                crawl_job.job_status = 'failed'
                crawl_job.completed_at = timezone.now()
                crawl_job.save()
        except:
            pass
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=2)
def crawl_manual_urls_task(self, website_source_id: str, urls: list) -> Dict[str, Any]:
    """
    Async task to crawl specific URLs manually (no internal page discovery)
    
    Args:
        website_source_id: UUID of the WebsiteSource
        urls: List of URLs to crawl (only these URLs, no internal links)
        
    Returns:
        Dict with task results
    """
    try:
        # Get website source
        website_source = WebsiteSource.objects.get(id=website_source_id)
        
        # Create crawl job for progress tracking (ensure it exists before starting)
        # Filter out empty URLs first
        valid_urls = [url.strip() for url in urls if url.strip()]
        total_urls = len(valid_urls)
        
        if total_urls == 0:
            logger.warning("No valid URLs provided for manual crawl")
            return {'success': False, 'error': 'No valid URLs provided'}
        
        crawl_job, created = CrawlJob.objects.get_or_create(
            celery_task_id=self.request.id,
            defaults={
                'website': website_source,
                'job_status': 'running',
                'started_at': timezone.now(),
                'pages_to_crawl': total_urls,
                'pages_crawled': 0
            }
        )
        
        # Update if already exists (shouldn't happen, but just in case)
        if not created:
            crawl_job.website = website_source
            crawl_job.job_status = 'running'
            crawl_job.started_at = timezone.now()
            crawl_job.pages_to_crawl = total_urls
            crawl_job.pages_crawled = 0
            crawl_job.completed_at = None
            crawl_job.save()
        
        logger.info(f"Created/updated crawl_job {crawl_job.id} for {total_urls} URLs (task_id: {self.request.id})")
        
        logger.info(f"Starting manual crawl for {total_urls} URLs")
        
        # Initialize crawler (we'll use it only for _crawl_page method)
        crawler = WebsiteCrawler(
            base_url=website_source.url,
            max_pages=total_urls,
            max_depth=0,  # Don't crawl internal links
            include_external=False,
            delay=0.1
        )
        
        saved_pages = 0
        failed_pages = 0
        
        # Crawl each URL individually (no internal link discovery)
        for i, url in enumerate(valid_urls):
            try:
                # URL is already cleaned (we filtered earlier)
                # Ensure URL has scheme
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                # Crawl only this specific URL (no internal links)
                page_data = crawler._crawl_page(url, depth=0)
                
                if not page_data:
                    logger.warning(f"Failed to crawl URL: {url}")
                    failed_pages += 1
                    continue
                
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
                page.images = page_data.get('images', [])
                page.processing_status = 'pending'
                page.save()
                
                saved_pages += 1
                
                # Process page content asynchronously
                process_page_content_task.delay(str(page.id))
                
                # Update progress (refresh from DB first to avoid race conditions)
                crawl_job.refresh_from_db()
                progress = round(((i + 1) / total_urls) * 100, 1)
                crawl_job.pages_crawled = i + 1
                crawl_job.save(update_fields=['pages_crawled'])
                
                logger.info(f"Manual crawl progress: {progress}% ({i + 1}/{total_urls}) - {url}")
                
            except Exception as e:
                logger.error(f"Failed to crawl URL {url}: {str(e)}")
                failed_pages += 1
                continue
        
        # Update crawl job
        crawl_job.job_status = 'completed'
        crawl_job.pages_crawled = saved_pages
        crawl_job.completed_at = timezone.now()
        crawl_job.save()
        
        logger.info(f"Manual crawl completed: {saved_pages} pages saved, {failed_pages} failed")
        
        return {
            'success': True,
            'website_id': str(website_source.id),
            'pages_crawled': saved_pages,
            'pages_failed': failed_pages,
            'total_urls': total_urls,
            'crawl_job_id': str(crawl_job.id)
        }
        
    except WebsiteSource.DoesNotExist:
        logger.error(f"WebsiteSource {website_source_id} not found")
        return {'success': False, 'error': 'Website source not found'}
    
    except Exception as e:
        logger.error(f"Error in crawl_manual_urls_task: {str(e)}")
        
        # Update crawl job on error
        try:
            crawl_job = CrawlJob.objects.filter(celery_task_id=self.request.id).first()
            if crawl_job:
                crawl_job.job_status = 'failed'
                crawl_job.completed_at = timezone.now()
                crawl_job.save()
        except:
            pass
        
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
        
        # ============ DISABLED: Auto Product Extraction ============
        # Temporarily disabled - product extraction is not needed for now
        # Site crawling and page processing will continue normally
        products_extracted = 0
        # try:
        #     # Only extract if enabled for this website
        #     if page.website.auto_extract_products:
        #         from web_knowledge.services.product_extractor import ProductExtractor
        #         
        #         logger.info(f"🔍 Starting product auto-extraction for {page.url}")
        #         
        #         user = page.website.user
        #         extractor = ProductExtractor(user)
        #         
        #         # Hybrid extraction (rule pre-filter + AI)
        #         extracted_products = extractor.extract_and_save(page)
        #         products_extracted = len(extracted_products)
        #         
        #         if products_extracted > 0:
        #             logger.info(
        #                 f"✅ Auto-extracted {products_extracted} products from {page.url}"
        #             )
        # 
        # except Exception as product_error:
        #     # Product extraction failure is non-critical
        #     # Log the error but don't fail the whole task
        #     logger.error(f"⚠️ Product extraction failed (non-critical): {product_error}")
        #     import traceback
        #     logger.debug(traceback.format_exc())
        #     # Continue processing - Q&A and other features still work
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
            page.save(update_fields=['processing_status'])
        except:
            pass
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=2, default_retry_delay=30, time_limit=300, soft_time_limit=270)
def generate_prompt_async_task(self, user_id: int, manual_prompt: str) -> Dict[str, Any]:
    """
    Async task to generate AI-enhanced prompt from manual_prompt
    
    Args:
        user_id: ID of the user requesting prompt generation
        manual_prompt: Raw manual prompt to enhance
        
    Returns:
        Dict with generation results
    """
    from django.contrib.auth import get_user_model
    from django.core.cache import cache
    from settings.models import BusinessPrompt
    
    User = get_user_model()
    
    try:
        # Get user
        user = User.objects.get(id=user_id)
        
        # Update status in cache
        cache.set(f'prompt_generation_{self.request.id}', {
        'status': 'در حال پردازش',
            'progress': 20,
            'message': 'در حال آماده‌سازی...',
        'created_at': timezone.now().isoformat()
        }, timeout=300)
    
        logger.info(f"Starting prompt generation for user {user.username}")
        
        business_type = user.business_type if hasattr(user, 'business_type') else None
        
        # Find matching BusinessPrompt based on business_type
        business_prompt_obj = None
        if business_type:
            business_prompt_obj = BusinessPrompt.objects.filter(
                name__iexact=business_type.strip()
            ).first()
        
        # ✅ CHECK TOKENS AND SUBSCRIPTION BEFORE AI USAGE
        from billing.utils import check_ai_access_for_user
        
        access_check = check_ai_access_for_user(
            user=user,
            estimated_tokens=700,  # Estimated tokens for prompt enhancement
            feature_name="Prompt Enhancement"
        )
        
        if not access_check['has_access']:
            logger.warning(
                f"User {user.username} denied access to Prompt Enhancement. "
                f"Reason: {access_check['reason']}"
            )
            cache.set(f'prompt_generation_{self.request.id}', {
                'status': 'خطا',
                'progress': 0,
                'message': access_check['message'],
                'error': access_check['message'],
                'error_code': access_check['reason'],
                'created_at': timezone.now().isoformat()
            }, timeout=300)
            return {
                'success': False,
                'error': access_check['message'],
                'error_code': access_check['reason']
            }
        
        # Update progress
        cache.set(f'prompt_generation_{self.request.id}', {
            'status': 'در حال پردازش',
            'progress': 40,
            'message': 'در حال تولید پرامپت با هوش مصنوعی...',
            'created_at': timezone.now().isoformat()
        }, timeout=300)
        
        # Use AI to rewrite and improve the manual_prompt
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
            
            # Use Flash model for prompt generation (more reliable than Pro)
            # Try gemini-2.5-flash first, fallback to gemini-2.0-flash-exp
            model_name = 'gemini-2.5-flash'
            fallback_model = 'gemini-2.0-flash-exp'
            
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={
                        'temperature': 0.7,
                        'max_output_tokens': 3000,
                    }
                )
            except Exception as model_error:
                logger.warning(f"Failed to use {model_name}, trying fallback {fallback_model}: {model_error}")
                model_name = fallback_model
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={
                        'temperature': 0.7,
                        'max_output_tokens': 3000,
                    }
                )
            
            # Build instruction for AI based on BusinessPrompt.prompt
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
            
            # Configure safety settings
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
            
            # Update progress
            cache.set(f'prompt_generation_{self.request.id}', {
                'status': 'در حال پردازش',
                'progress': 60,
                'message': 'در حال ارتباط با هوش مصنوعی...',
                'created_at': timezone.now().isoformat()
            }, timeout=300)
            
            # Track timing
            import time
            start_time = time.time()
            
            # Generate improved prompt
            response = model.generate_content(
                instruction,
                safety_settings=safety_settings
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract token usage
            prompt_tokens = 0
            completion_tokens = 0
            if hasattr(response, 'usage_metadata'):
                prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                completion_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
            
            # Track AI usage
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
                    metadata={'business_type': business_type}
                )
            except Exception as tracking_error:
                logger.error(f"Failed to track AI usage: {tracking_error}")
            
            # Consume tokens for billing
            if response:
                try:
                    actual_tokens = prompt_tokens + completion_tokens
                    if actual_tokens > 0:
                        from billing.services import consume_tokens_for_user
                        consume_tokens_for_user(
                            user,
                            actual_tokens,
                            description='Prompt enhancement (AI)'
                        )
                except Exception as token_error:
                    logger.error(f"Failed to consume tokens: {token_error}")
            
            if hasattr(response, 'text') and response.text:
                enhanced_prompt = response.text.strip()
            else:
                raise ValueError("No response from AI")
            
            # Update progress - completed
            cache.set(f'prompt_generation_{self.request.id}', {
                'status': 'تکمیل شد',
                'progress': 100,
                'message': 'پرامپت با موفقیت تولید شد',
                'prompt': enhanced_prompt,
                'generated_by_ai': True,
                'created_at': timezone.now().isoformat()
            }, timeout=300)
            
            logger.info(f"✅ Prompt generation completed for user {user.username}")
            
            return {
                'success': True,
                'prompt': enhanced_prompt,
                'generated_by_ai': True
            }
            
        except Exception as ai_error:
            error_msg = str(ai_error)
            logger.error(f"AI generation failed: {error_msg}", exc_info=True)
            
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
                    model_name='gemini-2.5-pro',
                    error_message=error_msg,
                    metadata={'business_type': business_type, 'error': error_msg}
                )
            except Exception as tracking_error:
                logger.error(f"Failed to track failed AI usage: {tracking_error}")
            
            # Fallback to simple combination
            if business_prompt_obj and business_prompt_obj.prompt:
                enhanced_prompt = f"""{business_prompt_obj.prompt}

{manual_prompt}"""
            else:
                enhanced_prompt = manual_prompt
            
            # Update progress - completed with fallback
            cache.set(f'prompt_generation_{self.request.id}', {
                'status': 'تکمیل شد',
                'progress': 100,
                'message': 'پرامپت تولید شد (هوش مصنوعی در دسترس نبود)',
                'prompt': enhanced_prompt,
                'generated_by_ai': False,
                'warning': 'AI generation failed, using simple combination',
                'created_at': timezone.now().isoformat()
            }, timeout=300)
            
            return {
                'success': True,
                'prompt': enhanced_prompt,
                'generated_by_ai': False,
                'warning': 'AI generation failed, using simple combination'
            }
            
    except User.DoesNotExist:
        error_msg = f"User {user_id} not found"
        logger.error(error_msg)
        cache.set(f'prompt_generation_{self.request.id}', {
            'status': 'خطا',
            'progress': 0,
            'message': error_msg,
            'error': error_msg,
            'created_at': timezone.now().isoformat()
        }, timeout=300)
        return {'success': False, 'error': error_msg}
    
    except Exception as e:
        error_msg = f"Error in prompt generation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        cache.set(f'prompt_generation_{self.request.id}', {
            'status': 'خطا',
            'progress': 0,
            'message': error_msg,
            'error': error_msg,
            'created_at': timezone.now().isoformat()
        }, timeout=300)
        return {'success': False, 'error': error_msg}
