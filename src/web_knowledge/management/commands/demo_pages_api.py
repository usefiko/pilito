"""
Management command to demonstrate the new pages API functionality
"""
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from web_knowledge.models import WebsiteSource, WebsitePage, QAPair

User = get_user_model()


class Command(BaseCommand):
    help = 'Demonstrate the new pages API functionality with sample data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to create sample data for'
        )
        parser.add_argument(
            '--create-sample',
            action='store_true',
            help='Create sample data if none exists'
        )
    
    def handle(self, *args, **options):
        username = options.get('username')
        create_sample = options.get('create_sample', False)
        
        self.stdout.write("=== WebKnowledge Pages API Demo ===")
        
        # Get or create user
        if username:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f"Using user: {username}")
            except User.DoesNotExist:
                self.stdout.write(f"User {username} not found!")
                return
        else:
            user, created = User.objects.get_or_create(
                username='demo_user',
                defaults={
                    'email': 'demo@example.com',
                    'first_name': 'Demo',
                    'last_name': 'User'
                }
            )
            if created:
                user.set_password('demopassword123')
                user.save()
                self.stdout.write("Created demo user: demo_user")
            else:
                self.stdout.write("Using existing demo user: demo_user")
        
        # Get or create sample website
        website = WebsiteSource.objects.filter(user=user).first()
        
        if not website and create_sample:
            self.stdout.write("\n--- Creating Sample Data ---")
            
            website = WebsiteSource.objects.create(
                user=user,
                name="Demo Company Website",
                url="https://demo-company.example.com",
                description="Sample website for demonstrating pages API",
                max_pages=10,
                crawl_depth=2,
                crawl_status='completed',
                pages_crawled=5,
                total_qa_pairs=15
            )
            
            # Create sample pages
            sample_pages = [
                {
                    'url': 'https://demo-company.example.com/',
                    'title': 'Home - Demo Company',
                    'summary': 'Welcome to Demo Company, your trusted partner in business solutions.',
                    'word_count': 850,
                    'meta_description': 'Demo Company homepage with company overview',
                    'h1_tags': ['Welcome to Demo Company'],
                    'h2_tags': ['Our Services', 'Why Choose Us', 'Contact Information']
                },
                {
                    'url': 'https://demo-company.example.com/about',
                    'title': 'About Us - Our Story',
                    'summary': 'Learn about our company history, mission, and the team behind our success.',
                    'word_count': 1200,
                    'meta_description': 'Learn about Demo Company history and mission',
                    'h1_tags': ['About Demo Company'],
                    'h2_tags': ['Our History', 'Our Mission', 'Meet the Team']
                },
                {
                    'url': 'https://demo-company.example.com/services',
                    'title': 'Services - What We Offer',
                    'summary': 'Comprehensive business solutions including consulting, development, and support.',
                    'word_count': 950,
                    'meta_description': 'Explore our comprehensive service offerings',
                    'h1_tags': ['Our Services'],
                    'h2_tags': ['Consulting Services', 'Development Solutions', 'Ongoing Support']
                },
                {
                    'url': 'https://demo-company.example.com/contact',
                    'title': 'Contact Us - Get in Touch',
                    'summary': 'Contact information and office locations for Demo Company.',
                    'word_count': 450,
                    'meta_description': 'Contact Demo Company for inquiries and support',
                    'h1_tags': ['Contact Information'],
                    'h2_tags': ['Office Locations', 'Business Hours', 'Support Channels']
                },
                {
                    'url': 'https://demo-company.example.com/faq',
                    'title': 'FAQ - Frequently Asked Questions',
                    'summary': 'Common questions and answers about our services and policies.',
                    'word_count': 1100,
                    'meta_description': 'Frequently asked questions about Demo Company services',
                    'h1_tags': ['Frequently Asked Questions'],
                    'h2_tags': ['General Questions', 'Service Questions', 'Billing Questions']
                }
            ]
            
            for page_data in sample_pages:
                page = WebsitePage.objects.create(
                    website=website,
                    url=page_data['url'],
                    title=page_data['title'],
                    summary=page_data['summary'],
                    word_count=page_data['word_count'],
                    meta_description=page_data['meta_description'],
                    h1_tags=page_data['h1_tags'],
                    h2_tags=page_data['h2_tags'],
                    processing_status='completed',
                    cleaned_content=f"Sample content for {page_data['title']}. " * 50,
                    raw_content=f"<html><body><h1>{page_data['title']}</h1><p>Content...</p></body></html>",
                    links=[]
                )
                
                # Create sample Q&A pairs
                qa_count = min(page_data['word_count'] // 300, 5)  # 1 Q&A per 300 words, max 5
                for i in range(qa_count):
                    QAPair.objects.create(
                        page=page,
                        question=f"What can you tell me about {page_data['title'].split(' - ')[0].lower()}?",
                        answer=f"Based on the {page_data['title'].split(' - ')[0].lower()} page, {page_data['summary']}",
                        context=page_data['summary'][:200],
                        confidence_score=0.85 + (i * 0.02),
                        generation_status='completed'
                    )
            
            website.update_progress()
            self.stdout.write(f"✅ Created sample website: {website.name}")
            self.stdout.write(f"✅ Created {len(sample_pages)} sample pages")
            self.stdout.write(f"✅ Created {website.total_qa_pairs} Q&A pairs")
        
        elif not website:
            self.stdout.write("❌ No websites found. Use --create-sample to create demo data.")
            return
        else:
            self.stdout.write(f"Using existing website: {website.name}")
        
        # Demonstrate API data structure
        self.stdout.write(f"\n--- API Response Preview ---")
        
        # Simulate the /websites/{id}/pages/ endpoint response
        pages = website.pages.filter(processing_status='completed').order_by('-crawled_at')
        
        pages_data = []
        for page in pages:
            page_data = {
                'id': str(page.id),
                'url': page.url,
                'title': page.title,
                'summary': page.summary,
                'word_count': page.word_count,
                'processing_status': page.processing_status,
                'qa_pairs': {
                    'total': page.qa_pairs.filter(generation_status='completed').count(),
                    'average_confidence': 0.87,  # Simplified for demo
                    'featured_count': 0
                }
            }
            pages_data.append(page_data)
        
        response_data = {
            'website_id': str(website.id),
            'website_name': website.name,
            'website_url': website.url,
            'total_pages': len(pages_data),
            'pages': pages_data[:3],  # Show first 3 for brevity
            'summary': {
                'total_words': sum(page['word_count'] for page in pages_data),
                'completed_pages': len(pages_data),
                'failed_pages': 0,
                'total_qa_pairs': sum(page['qa_pairs']['total'] for page in pages_data),
                'pages_with_qa': len([p for p in pages_data if p['qa_pairs']['total'] > 0])
            }
        }
        
        self.stdout.write("\n🌐 GET /api/v1/web-knowledge/websites/{id}/pages/")
        self.stdout.write(json.dumps(response_data, indent=2, default=str))
        
        # Show page titles in website list
        self.stdout.write(f"\n--- Website List with Page Titles ---")
        page_titles = pages[:3]  # First 3 pages
        titles_data = [
            {
                'id': str(page.id),
                'title': page.title,
                'url': page.url,
                'word_count': page.word_count,
                'qa_pairs_count': page.qa_pairs.filter(generation_status='completed').count()
            }
            for page in page_titles
        ]
        
        self.stdout.write("\n📋 GET /api/v1/web-knowledge/websites/ (page_titles field)")
        self.stdout.write(json.dumps(titles_data, indent=2, default=str))
        
        # Show API endpoints
        self.stdout.write(f"\n--- Available API Endpoints ---")
        endpoints = [
            f"GET /api/v1/web-knowledge/websites/{website.id}/pages/",
            f"GET /api/v1/web-knowledge/websites/",
            f"GET /api/v1/web-knowledge/pages/?website={website.id}",
            f"GET /api/v1/web-knowledge/pages/?website={website.id}&status=completed"
        ]
        
        for endpoint in endpoints:
            self.stdout.write(f"  📡 {endpoint}")
        
        self.stdout.write(f"\n✅ Demo completed! Website ID: {website.id}")
        self.stdout.write(f"   User: {user.username}")
        self.stdout.write(f"   Total pages: {website.pages_crawled}")
        self.stdout.write(f"   Total Q&A pairs: {website.total_qa_pairs}")
        
        self.stdout.write("\n🚀 Next steps:")
        self.stdout.write("1. Test the API endpoints with your JWT token")
        self.stdout.write("2. Use the website ID in your frontend application")
        self.stdout.write("3. Check the pages API for detailed page information")
