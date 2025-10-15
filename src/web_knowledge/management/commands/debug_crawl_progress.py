"""
Management command to debug crawl progress issues
"""
from django.core.management.base import BaseCommand
from web_knowledge.models import WebsiteSource, CrawlJob


class Command(BaseCommand):
    help = 'Debug crawl progress for websites'

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
                website = WebsiteSource.objects.get(id=website_id)
                websites = [website]
            except WebsiteSource.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Website with ID {website_id} not found')
                )
                return
        else:
            websites = WebsiteSource.objects.all()[:5]  # Limit to 5 for debugging
        
        self.stdout.write('=== Crawl Progress Debug Report ===\n')
        
        for website in websites:
            self.stdout.write(f'🌐 Website: {website.name}')
            self.stdout.write(f'   URL: {website.url}')
            self.stdout.write(f'   Status: {website.crawl_status}')
            self.stdout.write(f'   Progress: {website.crawl_progress}%')
            self.stdout.write(f'   Pages crawled: {website.pages_crawled}')
            self.stdout.write(f'   Total Q&A: {website.total_qa_pairs}')
            
            # Check crawl jobs
            recent_jobs = website.crawl_jobs.order_by('-created_at')[:3]
            
            if recent_jobs:
                self.stdout.write(f'   📊 Recent Crawl Jobs:')
                for i, job in enumerate(recent_jobs, 1):
                    progress_pct = job.progress_percentage
                    self.stdout.write(f'      Job {i}: {job.job_status}')
                    self.stdout.write(f'         Progress: {progress_pct:.1f}%')
                    self.stdout.write(f'         Pages: {job.pages_crawled}/{job.pages_to_crawl}')
                    self.stdout.write(f'         Started: {job.started_at}')
                    self.stdout.write(f'         Completed: {job.completed_at}')
                    
                    # Diagnose progress issues
                    if job.pages_to_crawl == 0:
                        self.stdout.write(
                            self.style.WARNING(f'         ⚠️ Issue: pages_to_crawl is 0')
                        )
                    elif progress_pct < 100 and job.job_status == 'completed':
                        self.stdout.write(
                            self.style.WARNING(f'         ⚠️ Issue: Job completed but progress < 100%')
                        )
                    elif progress_pct == 12 or (progress_pct > 10 and progress_pct < 15):
                        self.stdout.write(
                            self.style.ERROR(f'         🐛 Found the bug: Progress stuck around 12%')
                        )
                        self.stdout.write(f'         Debug: crawled={job.pages_crawled}, total={job.pages_to_crawl}')
                        if job.pages_to_crawl > 0:
                            calc_progress = (job.pages_crawled / job.pages_to_crawl) * 100
                            self.stdout.write(f'         Calculated: {calc_progress:.1f}%')
            else:
                self.stdout.write(f'   No crawl jobs found')
            
            self.stdout.write('')  # Empty line
        
        # Global statistics
        total_websites = WebsiteSource.objects.count()
        stuck_progress = WebsiteSource.objects.filter(
            crawl_progress__gt=10, 
            crawl_progress__lt=15
        ).count()
        
        self.stdout.write('=== Summary ===')
        self.stdout.write(f'Total websites: {total_websites}')
        self.stdout.write(f'Websites with progress 10-15%: {stuck_progress}')
        
        if stuck_progress > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'Found {stuck_progress} websites with potentially stuck progress!'
                )
            )
