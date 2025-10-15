"""
Management command to fix crawl progress for completed websites
"""
from django.core.management.base import BaseCommand
from web_knowledge.models import WebsiteSource


class Command(BaseCommand):
    help = 'Fix crawl progress for completed websites that are stuck at low percentages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--website-id',
            type=str,
            help='Specific website ID to fix',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually changing',
        )

    def handle(self, *args, **options):
        website_id = options.get('website_id')
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Find completed websites with progress < 100%
        if website_id:
            try:
                websites = WebsiteSource.objects.filter(
                    id=website_id,
                    crawl_status='completed'
                )
            except Exception:
                self.stdout.write(
                    self.style.ERROR(f'Website with ID {website_id} not found')
                )
                return
        else:
            websites = WebsiteSource.objects.filter(
                crawl_status='completed',
                crawl_progress__lt=100.0
            )
        
        if not websites.exists():
            self.stdout.write(
                self.style.SUCCESS('✅ No completed websites found with progress < 100%')
            )
            return
        
        self.stdout.write(f'\n🔍 Found {websites.count()} completed websites with incorrect progress:')
        
        fixed_count = 0
        
        for website in websites:
            pages_count = website.pages.count()
            current_progress = website.crawl_progress
            
            self.stdout.write(
                f'\n🌐 Website: {website.name}'
            )
            self.stdout.write(
                f'   📊 Current progress: {current_progress}%'
            )
            self.stdout.write(
                f'   📄 Pages crawled: {pages_count}'
            )
            self.stdout.write(
                f'   📅 Completed at: {website.crawl_completed_at}'
            )
            
            if not dry_run:
                # Fix the progress to 100%
                website.crawl_progress = 100.0
                website.save(update_fields=['crawl_progress'])
                
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Fixed progress to 100%')
                )
                fixed_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'   🔧 Would fix progress to 100%')
                )
        
        # Summary
        self.stdout.write('\n=== Summary ===')
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would fix {websites.count()} completed websites'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Fixed progress for {fixed_count} completed websites'
                )
            )
            
            if fixed_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        '🎉 All completed crawls now show 100% progress!'
                    )
                )
