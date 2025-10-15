"""
Management command to debug crawl status and progress issues
"""
from django.core.management.base import BaseCommand
from web_knowledge.models import WebsiteSource, CrawlJob


class Command(BaseCommand):
    help = 'Debug crawl status and progress calculation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--website-id',
            type=str,
            help='Specific website ID to debug',
        )

    def handle(self, *args, **options):
        website_id = options.get('website_id')
        
        if website_id:
            try:
                websites = [WebsiteSource.objects.get(id=website_id)]
            except WebsiteSource.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Website with ID {website_id} not found')
                )
                return
        else:
            # Find recent websites with issues
            websites = WebsiteSource.objects.filter(
                crawl_progress__lt=100.0
            ).order_by('-created_at')[:5]
        
        if not websites:
            self.stdout.write(
                self.style.SUCCESS('✅ No websites found with progress < 100%')
            )
            return
        
        self.stdout.write('\n🔍 Debugging crawl status and progress:\n')
        
        for website in websites:
            self.stdout.write(f'🌐 Website: {website.name}')
            self.stdout.write(f'   URL: {website.url}')
            self.stdout.write(f'   Status: {website.crawl_status}')
            self.stdout.write(f'   Progress: {website.crawl_progress}%')
            self.stdout.write(f'   Max Pages: {website.max_pages}')
            self.stdout.write(f'   Pages Crawled: {website.pages_crawled}')
            self.stdout.write(f'   Actual Pages Count: {website.pages.count()}')
            
            # Calculate what progress SHOULD be
            if website.max_pages > 0:
                calculated_progress = min((website.pages.count() / website.max_pages) * 100, 100.0)
                self.stdout.write(f'   Calculated Progress: {calculated_progress}%')
            else:
                self.stdout.write(f'   Calculated Progress: N/A (max_pages = 0)')
            
            # Check crawl jobs
            crawl_jobs = CrawlJob.objects.filter(website=website).order_by('-created_at')
            if crawl_jobs.exists():
                latest_job = crawl_jobs.first()
                self.stdout.write(f'   Latest Job Status: {latest_job.job_status}')
                self.stdout.write(f'   Job Pages Crawled: {latest_job.pages_crawled}')
                self.stdout.write(f'   Job Pages To Crawl: {latest_job.pages_to_crawl}')
                self.stdout.write(f'   Job Progress: {latest_job.progress_percentage}%')
            
            self.stdout.write(f'   Created: {website.created_at}')
            self.stdout.write(f'   Crawl Started: {website.crawl_started_at}')
            self.stdout.write(f'   Crawl Completed: {website.crawl_completed_at}')
            
            # Test what happens if we call update_progress()
            self.stdout.write('   --- Testing update_progress() ---')
            old_progress = website.crawl_progress
            old_status = website.crawl_status
            
            self.stdout.write(f'   Before: status={old_status}, progress={old_progress}%')
            
            # Call update_progress without saving
            website.pages_crawled = website.pages.count()
            if website.crawl_status != 'completed':
                if website.max_pages > 0:
                    test_progress = min((website.pages_crawled / website.max_pages) * 100, 100.0)
                else:
                    test_progress = 0.0
                self.stdout.write(f'   Would set progress to: {test_progress}%')
            else:
                self.stdout.write(f'   Would NOT change progress (status = completed)')
            
            self.stdout.write('   ' + '='*50 + '\n')
        
        # Summary
        self.stdout.write('\n=== Analysis ===')
        
        completed_low_progress = WebsiteSource.objects.filter(
            crawl_status='completed',
            crawl_progress__lt=100.0
        ).count()
        
        if completed_low_progress > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Found {completed_low_progress} completed websites with progress < 100%'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Run: python manage.py fix_completed_crawl_progress'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '✅ All completed websites have 100% progress'
                )
            )
