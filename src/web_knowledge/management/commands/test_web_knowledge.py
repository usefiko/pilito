"""
Management command to test the web_knowledge functionality
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from web_knowledge.models import WebsiteSource
from web_knowledge.services.crawler_service import WebsiteCrawler, ContentExtractor
from web_knowledge.services.qa_generator import QAGenerator

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test web knowledge functionality with a sample website'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://example.com',
            help='URL to test crawling (default: https://example.com)'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username to create website source for (creates test user if not provided)'
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=3,
            help='Maximum pages to crawl (default: 3)'
        )
        parser.add_argument(
            '--skip-qa',
            action='store_true',
            help='Skip Q&A generation'
        )
    
    def handle(self, *args, **options):
        url = options['url']
        username = options['username']
        max_pages = options['max_pages']
        skip_qa = options['skip_qa']
        
        self.stdout.write(f"Testing Web Knowledge with URL: {url}")
        
        # Get or create user
        if username:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f"Using existing user: {username}")
            except User.DoesNotExist:
                self.stdout.write(f"User {username} not found!")
                return
        else:
            user, created = User.objects.get_or_create(
                username='test_web_knowledge',
                defaults={
                    'email': 'test@webknowledge.com',
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            if created:
                user.set_password('testpassword123')
                user.save()
                self.stdout.write("Created test user: test_web_knowledge")
            else:
                self.stdout.write("Using existing test user: test_web_knowledge")
        
        # Test crawler
        self.stdout.write("\n=== Testing Website Crawler ===")
        try:
            with WebsiteCrawler(
                base_url=url,
                max_pages=max_pages,
                max_depth=2,
                include_external=False,
                delay=0.5
            ) as crawler:
                
                def progress_callback(percentage, pages_crawled, current_url):
                    self.stdout.write(f"Progress: {percentage:.1f}% - {current_url}")
                
                crawled_pages = crawler.crawl(progress_callback=progress_callback)
                
                self.stdout.write(f"✅ Crawled {len(crawled_pages)} pages successfully")
                self.stdout.write(f"❌ Failed to crawl {len(crawler.failed_urls)} pages")
                
                if crawled_pages:
                    # Test content extraction
                    self.stdout.write("\n=== Testing Content Extraction ===")
                    page_data = crawled_pages[0]
                    
                    content_data = ContentExtractor.extract_main_content(
                        page_data['raw_content'],
                        page_data['cleaned_content']
                    )
                    
                    summary = ContentExtractor.create_summary(
                        content_data['main_content'],
                        max_length=200
                    )
                    
                    self.stdout.write(f"✅ Extracted {content_data['word_count']} words")
                    self.stdout.write(f"✅ Generated summary: {summary[:100]}...")
                    
                    # Test Q&A generation if not skipped
                    if not skip_qa:
                        self.stdout.write("\n=== Testing Q&A Generation ===")
                        qa_generator = QAGenerator()
                        
                        if qa_generator.is_available():
                            qa_pairs = qa_generator.generate_qa_pairs(
                                content=content_data['main_content'],
                                page_title=page_data.get('title', ''),
                                max_pairs=3
                            )
                            
                            if qa_pairs:
                                self.stdout.write(f"✅ Generated {len(qa_pairs)} Q&A pairs")
                                for i, qa in enumerate(qa_pairs, 1):
                                    self.stdout.write(f"\n--- Q&A Pair {i} ---")
                                    self.stdout.write(f"Q: {qa['question']}")
                                    self.stdout.write(f"A: {qa['answer'][:100]}...")
                                    self.stdout.write(f"Confidence: {qa['confidence']:.2f}")
                            else:
                                self.stdout.write("❌ No Q&A pairs generated")
                        else:
                            self.stdout.write("❌ Q&A generator not available (check Gemini API key)")
                    
                    # Create website source for database testing
                    self.stdout.write("\n=== Testing Database Models ===")
                    website_source, created = WebsiteSource.objects.get_or_create(
                        user=user,
                        url=url,
                        defaults={
                            'name': f'Test Site - {url}',
                            'description': 'Test website for web knowledge functionality',
                            'max_pages': max_pages,
                            'crawl_depth': 2,
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"✅ Created WebsiteSource: {website_source.name}")
                    else:
                        self.stdout.write(f"✅ Using existing WebsiteSource: {website_source.name}")
                    
                    self.stdout.write(f"Website ID: {website_source.id}")
                    self.stdout.write(f"User: {website_source.user.username}")
                
        except Exception as e:
            self.stdout.write(f"❌ Error during testing: {str(e)}")
            logger.error(f"Test error: {str(e)}", exc_info=True)
        
        self.stdout.write("\n=== Test Summary ===")
        self.stdout.write("✅ Web Knowledge system is ready!")
        self.stdout.write(f"🌐 Test URL: {url}")
        self.stdout.write(f"👤 Test User: {user.username}")
        self.stdout.write("\nTo start using the system:")
        self.stdout.write("1. Run migrations: python manage.py migrate")
        self.stdout.write("2. Start Celery worker: celery -A core worker --loglevel=info")
        self.stdout.write("3. Use the API endpoints to create and crawl websites")
        self.stdout.write("4. Check the admin interface for detailed management")
        
        if not skip_qa:
            self.stdout.write("\nNote: Make sure to configure Gemini API key in AIGlobalConfig for Q&A generation")
