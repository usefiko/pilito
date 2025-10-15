"""
Django management command to test enhanced Q&A generation
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count
from web_knowledge.models import WebsiteSource, WebsitePage, QAPair
from web_knowledge.tasks import generate_enhanced_qa_pairs_task, _generate_fallback_qa_pairs

User = get_user_model()


class Command(BaseCommand):
    help = 'Test enhanced Q&A generation functionality'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--website-id',
            type=str,
            help='Website ID to test Q&A generation for'
        )
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test website and page data'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Testing Enhanced Q&A Generation System'))
        
        if options['create_test_data']:
            self.create_test_data()
        
        website_id = options.get('website_id')
        if website_id:
            self.test_enhanced_qa_generation(website_id)
        else:
            self.test_fallback_generation()
        
        self.stdout.write(self.style.SUCCESS('✅ Enhanced Q&A testing completed!'))
    
    def create_test_data(self):
        """Create test website and page for Q&A generation"""
        self.stdout.write('📝 Creating test data...')
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='qa_test_user',
            defaults={'email': 'test@example.com'}
        )
        
        # Create test website
        website, created = WebsiteSource.objects.get_or_create(
            name='Test Website for Q&A',
            url='https://example.com',
            user=user,
            defaults={
                'description': 'Test website for Q&A generation',
                'max_pages': 10
            }
        )
        
        # Create test page
        page, created = WebsitePage.objects.get_or_create(
            website=website,
            url='https://example.com/test-page',
            defaults={
                'title': 'Test Page for Q&A Generation',
                'cleaned_content': '''
                Welcome to our comprehensive business services platform. We provide web development, 
                consulting, and digital marketing solutions for businesses of all sizes.
                
                Our Business Hours:
                Monday - Friday: 9:00 AM - 6:00 PM EST
                Saturday: 10:00 AM - 4:00 PM EST
                Sunday: Closed
                
                Services We Offer:
                1. Web Development - Custom websites and web applications
                2. Digital Marketing - SEO, social media, and online advertising
                3. Business Consulting - Strategy and process optimization
                4. Technical Support - 24/7 support for all our clients
                
                Contact Information:
                Email: support@example.com
                Phone: (555) 123-4567
                Address: 123 Business Street, City, State 12345
                
                Pricing Information:
                We offer competitive pricing with flexible payment plans. Contact us for a free quote.
                Our basic web development package starts at $1,500, while comprehensive business 
                consulting packages range from $500 to $5,000 depending on scope and duration.
                
                Why Choose Us:
                - Over 10 years of experience
                - Dedicated project managers
                - 100% satisfaction guarantee
                - Free consultations
                - Ongoing support and maintenance
                ''',
                'word_count': 200,
                'processing_status': 'completed'
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Test data created:')
        )
        self.stdout.write(f'   Website ID: {website.id}')
        self.stdout.write(f'   Page ID: {page.id}')
    
    def test_enhanced_qa_generation(self, website_id):
        """Test enhanced Q&A generation for a specific website"""
        self.stdout.write(f'🧪 Testing enhanced Q&A generation for website: {website_id}')
        
        try:
            website = WebsiteSource.objects.get(id=website_id)
            pages = website.pages.filter(processing_status='completed')
            
            if not pages.exists():
                self.stdout.write(
                    self.style.WARNING('⚠️  No completed pages found for this website')
                )
                return
            
            self.stdout.write(f'📄 Found {pages.count()} pages to test')
            
            for page in pages[:2]:  # Test first 2 pages
                self.stdout.write(f'\n🔄 Testing page: {page.title} ({page.url})')
                
                # Test enhanced Q&A generation
                result = generate_enhanced_qa_pairs_task(
                    str(page.id),
                    max_pairs=5,
                    categories=['general', 'contact', 'services'],
                    question_types=['factual', 'procedural', 'explanatory']
                )
                
                if result.get('success'):
                    qa_count = result.get('qa_pairs_generated', 0)
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Generated {qa_count} Q&A pairs')
                    )
                    
                    # Show the generated Q&A pairs
                    qa_pairs = QAPair.objects.filter(page=page).order_by('-created_at')[:5]
                    for i, qa in enumerate(qa_pairs, 1):
                        self.stdout.write(f'   {i}. Q: {qa.question[:60]}...')
                        self.stdout.write(f'      A: {qa.answer[:80]}...')
                        self.stdout.write(f'      Category: {qa.category}, Type: {qa.question_type}')
                        self.stdout.write(f'      Confidence: {qa.confidence_score:.2f}')
                        self.stdout.write('')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Failed: {result.get("error", "Unknown error")}')
                    )
        
        except WebsiteSource.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Website with ID {website_id} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during testing: {str(e)}')
            )
    
    def test_fallback_generation(self):
        """Test fallback Q&A generation"""
        self.stdout.write('🧪 Testing fallback Q&A generation...')
        
        # Create a minimal test page object
        class MockPage:
            def __init__(self):
                self.title = "Test Fallback Page"
                self.url = "https://example.com/fallback"
                self.cleaned_content = "This is a test page for fallback Q&A generation. It contains basic information about our services."
                self.raw_content = self.cleaned_content
        
        mock_page = MockPage()
        
        # Test fallback generation
        fallback_pairs = _generate_fallback_qa_pairs(mock_page, 3)
        
        self.stdout.write(f'✅ Generated {len(fallback_pairs)} fallback Q&A pairs:')
        
        for i, qa in enumerate(fallback_pairs, 1):
            self.stdout.write(f'   {i}. Q: {qa["question"]}')
            self.stdout.write(f'      A: {qa["answer"][:80]}...')
            self.stdout.write(f'      Category: {qa["category"]}, Type: {qa["question_type"]}')
            self.stdout.write('')
    
    def show_qa_statistics(self):
        """Show Q&A statistics"""
        total_qa = QAPair.objects.count()
        by_category = QAPair.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        self.stdout.write(f'📊 Q&A Statistics:')
        self.stdout.write(f'   Total Q&A Pairs: {total_qa}')
        self.stdout.write(f'   By Category:')
        
        for cat in by_category:
            self.stdout.write(f'     - {cat["category"]}: {cat["count"]}')
