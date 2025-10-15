"""
Django management command to force Q&A generation for testing
This bypasses AI and creates Q&A pairs using fallback generation
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from web_knowledge.models import WebsiteSource, WebsitePage, QAPair
from web_knowledge.tasks import _generate_fallback_qa_pairs

User = get_user_model()


class Command(BaseCommand):
    help = 'Force Q&A generation for testing (bypasses AI)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--website-id',
            type=str,
            help='Website ID to generate Q&A for'
        )
        parser.add_argument(
            '--page-id',
            type=str,
            help='Specific page ID to generate Q&A for'
        )
        parser.add_argument(
            '--create-test-website',
            action='store_true',
            help='Create a test website and generate Q&A'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Force Q&A Generation (Fallback Mode)')
        )
        
        if options['create_test_website']:
            website_id = self.create_test_website()
            self.generate_qa_for_website(website_id)
        elif options['website_id']:
            self.generate_qa_for_website(options['website_id'])
        elif options['page_id']:
            self.generate_qa_for_page(options['page_id'])
        else:
            self.stdout.write(
                self.style.ERROR('Please provide --website-id, --page-id, or --create-test-website')
            )
        
        self.stdout.write(self.style.SUCCESS('✅ Force Q&A generation completed!'))
    
    def create_test_website(self):
        """Create a test website with sample content"""
        self.stdout.write('📝 Creating test website with sample content...')
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='qa_force_test_user',
            defaults={'email': 'force-test@example.com'}
        )
        if created:
            self.stdout.write('   ✅ Created test user')
        
        # Create test website
        website = WebsiteSource.objects.create(
            name='Force Test Website for Q&A',
            url='https://force-test-example.com',
            user=user,
            description='Test website for forced Q&A generation',
            max_pages=5,
            crawl_status='completed'
        )
        self.stdout.write(f'   ✅ Created test website: {website.id}')
        
        # Create test pages with rich content
        test_pages = [
            {
                'url': 'https://force-test-example.com/',
                'title': 'Home - Business Services Company',
                'content': '''
                Welcome to our comprehensive business services company. We have been serving clients 
                for over 15 years with professional web development, digital marketing, and business 
                consulting services.
                
                Our Services:
                - Custom Web Development: We create responsive, modern websites
                - Digital Marketing: SEO, social media management, and online advertising
                - Business Consulting: Strategy development and process optimization
                - Technical Support: 24/7 customer support for all our clients
                
                Contact Information:
                Email: info@force-test-example.com
                Phone: (555) 123-4567
                Address: 123 Business Ave, Suite 100, Business City, BC 12345
                
                Business Hours:
                Monday - Friday: 9:00 AM - 6:00 PM
                Saturday: 10:00 AM - 2:00 PM
                Sunday: Closed
                
                We offer free consultations and competitive pricing for all our services.
                '''
            },
            {
                'url': 'https://force-test-example.com/services',
                'title': 'Our Services - Web Development & Marketing',
                'content': '''
                Our Professional Services:
                
                1. Web Development Services
                - Custom Website Design
                - E-commerce Solutions
                - Mobile App Development
                - Website Maintenance
                
                2. Digital Marketing Services
                - Search Engine Optimization (SEO)
                - Pay-Per-Click Advertising (PPC)
                - Social Media Marketing
                - Email Marketing Campaigns
                
                3. Business Consulting
                - Strategic Planning
                - Process Improvement
                - Market Analysis
                - Technology Integration
                
                Pricing starts at $1,500 for basic websites and $500 for marketing packages.
                Contact us for a custom quote based on your specific needs.
                '''
            },
            {
                'url': 'https://force-test-example.com/contact',
                'title': 'Contact Us - Get In Touch',
                'content': '''
                Get in touch with our team today!
                
                Office Location:
                123 Business Avenue, Suite 100
                Business City, BC 12345
                
                Contact Methods:
                Phone: (555) 123-4567
                Email: info@force-test-example.com
                Contact Form: Available on our website
                
                Office Hours:
                Monday - Friday: 9:00 AM - 6:00 PM EST
                Saturday: 10:00 AM - 2:00 PM EST
                Sunday: Closed
                
                Emergency Support:
                For urgent technical issues, call our 24/7 support line at (555) 999-8888
                
                We typically respond to emails within 2 business hours and phone calls immediately.
                '''
            }
        ]
        
        for page_data in test_pages:
            page = WebsitePage.objects.create(
                website=website,
                url=page_data['url'],
                title=page_data['title'],
                cleaned_content=page_data['content'],
                raw_content=page_data['content'],
                word_count=len(page_data['content'].split()),
                processing_status='completed'
            )
            self.stdout.write(f'   ✅ Created test page: {page.title}')
        
        return str(website.id)
    
    def generate_qa_for_website(self, website_id):
        """Generate Q&A pairs for all pages in a website"""
        try:
            website = WebsiteSource.objects.get(id=website_id)
            pages = website.pages.filter(processing_status='completed')
            
            self.stdout.write(f'🔄 Generating Q&A for website: {website.name}')
            self.stdout.write(f'   Found {pages.count()} pages to process')
            
            total_created = 0
            
            for page in pages:
                created_count = self.generate_qa_for_page(str(page.id), show_output=False)
                total_created += created_count
                self.stdout.write(f'   ✅ {page.title}: {created_count} Q&A pairs created')
            
            self.stdout.write(f'🎉 Total Q&A pairs created: {total_created}')
            
            # Show some examples
            self.show_qa_examples(website)
            
        except WebsiteSource.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Website {website_id} not found')
            )
    
    def generate_qa_for_page(self, page_id, show_output=True):
        """Generate Q&A pairs for a specific page"""
        try:
            page = WebsitePage.objects.get(id=page_id)
            
            if show_output:
                self.stdout.write(f'🔄 Generating Q&A for page: {page.title}')
            
            # Remove existing Q&A pairs for this page (for testing)
            existing_count = QAPair.objects.filter(page=page).count()
            if existing_count > 0:
                QAPair.objects.filter(page=page).delete()
                if show_output:
                    self.stdout.write(f'   🗑️  Removed {existing_count} existing Q&A pairs')
            
            # Generate fallback Q&A pairs (guaranteed to work)
            qa_pairs_data = _generate_fallback_qa_pairs(page, 5)
            
            # Save Q&A pairs to database
            created_count = 0
            for qa_data in qa_pairs_data:
                qa_pair = QAPair.objects.create(
                    page=page,
                    question=qa_data['question'],
                    answer=qa_data['answer'],
                    context=qa_data.get('context', ''),
                    confidence_score=qa_data.get('confidence', 0.8),
                    question_type=qa_data.get('question_type', 'factual'),
                    category=qa_data.get('category', 'general'),
                    keywords=qa_data.get('keywords', []),
                    created_by_ai=qa_data.get('created_by_ai', False),
                    generation_status='completed'
                )
                created_count += 1
            
            if show_output:
                self.stdout.write(f'   ✅ Created {created_count} Q&A pairs')
                
                # Show the Q&A pairs
                for i, qa in enumerate(QAPair.objects.filter(page=page), 1):
                    self.stdout.write(f'   {i}. Q: {qa.question}')
                    self.stdout.write(f'      A: {qa.answer[:100]}...')
                    self.stdout.write('')
            
            return created_count
            
        except WebsitePage.DoesNotExist:
            if show_output:
                self.stdout.write(
                    self.style.ERROR(f'❌ Page {page_id} not found')
                )
            return 0
    
    def show_qa_examples(self, website):
        """Show some Q&A examples from the website"""
        qa_pairs = QAPair.objects.filter(
            page__website=website
        ).order_by('-created_at')[:10]
        
        if qa_pairs.exists():
            self.stdout.write('\n📋 Sample Q&A Pairs Created:')
            for i, qa in enumerate(qa_pairs, 1):
                self.stdout.write(f'\n{i}. Category: {qa.category} | Type: {qa.question_type}')
                self.stdout.write(f'   Q: {qa.question}')
                self.stdout.write(f'   A: {qa.answer[:120]}...')
                self.stdout.write(f'   Page: {qa.page.title}')
        
        # Show statistics
        total_qa = QAPair.objects.filter(page__website=website).count()
        by_category = QAPair.objects.filter(page__website=website).values(
            'category'
        ).distinct()
        
        self.stdout.write(f'\n📊 Q&A Statistics for {website.name}:')
        self.stdout.write(f'   Total Q&A Pairs: {total_qa}')
        self.stdout.write(f'   Categories: {", ".join([c["category"] for c in by_category])}')
