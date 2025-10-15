"""
Django management command to debug Q&A generation issues
This helps identify why Q&A pairs are not being created
"""
from django.core.management.base import BaseCommand
from web_knowledge.models import WebsiteSource, WebsitePage, QAPair
from web_knowledge.services.qa_generator import QAGenerator
from web_knowledge.tasks import _generate_fallback_qa_pairs
from AI_model.models import AIGlobalConfig


class Command(BaseCommand):
    help = 'Debug Q&A generation issues'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Debugging Q&A Generation Issues')
        )
        
        # Check 1: Database connectivity and existing data
        self.check_database_data()
        
        # Check 2: AI Configuration
        self.check_ai_configuration()
        
        # Check 3: Q&A Generator Service
        self.check_qa_generator()
        
        # Check 4: Fallback Generation (without AI)
        self.test_fallback_generation()
        
        # Check 5: Recent Q&A pairs
        self.check_recent_qa_pairs()
        
        self.stdout.write(self.style.SUCCESS('✅ Debug analysis completed!'))
    
    def check_database_data(self):
        """Check existing data in database"""
        self.stdout.write('\n📊 Database Data Check:')
        
        try:
            # Count websites
            website_count = WebsiteSource.objects.count()
            self.stdout.write(f'   📁 Total Websites: {website_count}')
            
            # Count pages
            page_count = WebsitePage.objects.count()
            completed_pages = WebsitePage.objects.filter(processing_status='completed').count()
            self.stdout.write(f'   📄 Total Pages: {page_count}')
            self.stdout.write(f'   ✅ Completed Pages: {completed_pages}')
            
            # Count Q&A pairs
            qa_count = QAPair.objects.count()
            self.stdout.write(f'   ❓ Total Q&A Pairs: {qa_count}')
            
            # Show recent websites
            recent_websites = WebsiteSource.objects.order_by('-created_at')[:3]
            if recent_websites:
                self.stdout.write('   📋 Recent Websites:')
                for website in recent_websites:
                    pages_count = website.pages.count()
                    qa_count = QAPair.objects.filter(page__website=website).count()
                    self.stdout.write(f'     - {website.name}: {pages_count} pages, {qa_count} Q&A pairs')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Database error: {str(e)}')
            )
    
    def check_ai_configuration(self):
        """Check AI configuration"""
        self.stdout.write('\n🤖 AI Configuration Check:')
        
        try:
            config = AIGlobalConfig.get_config()
            if config:
                has_gemini_key = bool(config.gemini_api_key)
                self.stdout.write(f'   🔑 Gemini API Key Present: {has_gemini_key}')
                if has_gemini_key:
                    # Show partial key for verification
                    key_preview = config.gemini_api_key[:10] + "..." if len(config.gemini_api_key) > 10 else "Short Key"
                    self.stdout.write(f'   🔑 Key Preview: {key_preview}')
                else:
                    self.stdout.write(
                        self.style.WARNING('   ⚠️  No Gemini API key found - Q&A will use fallback generation')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING('   ⚠️  No AI configuration found - Q&A will use fallback generation')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ AI config error: {str(e)}')
            )
    
    def check_qa_generator(self):
        """Test Q&A generator service"""
        self.stdout.write('\n🧠 Q&A Generator Service Check:')
        
        try:
            qa_generator = QAGenerator()
            is_available = qa_generator.is_available()
            self.stdout.write(f'   🔧 QA Generator Available: {is_available}')
            
            if is_available:
                self.stdout.write('   ✅ AI-powered Q&A generation should work')
            else:
                self.stdout.write('   ⚠️  AI unavailable - will use fallback generation')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ QA Generator error: {str(e)}')
            )
    
    def test_fallback_generation(self):
        """Test fallback Q&A generation"""
        self.stdout.write('\n🔄 Fallback Generation Test:')
        
        try:
            # Create a mock page object
            class MockPage:
                def __init__(self):
                    self.title = "Test Page for Debugging"
                    self.url = "https://example.com/debug-test"
                    self.cleaned_content = """
                    Welcome to our business website. We offer professional services including:
                    - Web development and design
                    - Digital marketing and SEO
                    - Business consulting and strategy
                    
                    Contact us at info@example.com or call (555) 123-4567.
                    Our office hours are Monday-Friday 9AM-5PM.
                    """
                    self.raw_content = self.cleaned_content
            
            mock_page = MockPage()
            
            # Test fallback generation
            fallback_qa = _generate_fallback_qa_pairs(mock_page, 3)
            
            self.stdout.write(f'   📝 Fallback Q&A Generated: {len(fallback_qa)} pairs')
            
            if fallback_qa:
                self.stdout.write('   ✅ Fallback generation working correctly')
                for i, qa in enumerate(fallback_qa, 1):
                    self.stdout.write(f'   {i}. Q: {qa["question"][:60]}...')
                    self.stdout.write(f'      A: {qa["answer"][:60]}...')
            else:
                self.stdout.write(
                    self.style.ERROR('   ❌ Fallback generation failed')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Fallback test error: {str(e)}')
            )
    
    def check_recent_qa_pairs(self):
        """Check recent Q&A pairs"""
        self.stdout.write('\n🕒 Recent Q&A Pairs Check:')
        
        try:
            recent_qa = QAPair.objects.order_by('-created_at')[:5]
            
            if recent_qa:
                self.stdout.write(f'   📋 Found {len(recent_qa)} recent Q&A pairs:')
                for qa in recent_qa:
                    page_title = qa.page.title if qa.page else "Unknown Page"
                    self.stdout.write(f'   - {qa.question[:50]}... (Page: {page_title})')
                    self.stdout.write(f'     Created: {qa.created_at}, AI: {qa.created_by_ai}')
            else:
                self.stdout.write(
                    self.style.WARNING('   ⚠️  No Q&A pairs found in database')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Recent Q&A check error: {str(e)}')
            )
    
    def show_debug_recommendations(self):
        """Show debugging recommendations"""
        self.stdout.write('\n💡 Debug Recommendations:')
        
        # Check if there are pages but no Q&A
        try:
            completed_pages = WebsitePage.objects.filter(processing_status='completed').count()
            qa_count = QAPair.objects.count()
            
            if completed_pages > 0 and qa_count == 0:
                self.stdout.write(
                    self.style.WARNING('   🎯 Issue Found: Pages exist but no Q&A pairs created')
                )
                self.stdout.write('   📋 Possible Solutions:')
                self.stdout.write('     1. Check if Q&A generation tasks are running')
                self.stdout.write('     2. Verify Celery workers are active')
                self.stdout.write('     3. Check task logs for errors')
                self.stdout.write('     4. Use force_qa_generation command to bypass AI')
            elif completed_pages == 0:
                self.stdout.write(
                    self.style.WARNING('   🎯 Issue Found: No completed pages for Q&A generation')
                )
                self.stdout.write('   📋 Solution: Complete website crawling first')
            else:
                self.stdout.write('   ✅ No obvious issues detected')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Recommendation error: {str(e)}')
