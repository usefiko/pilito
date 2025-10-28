"""
Management command to chunk all completed WebsitePages that haven't been chunked yet
This fixes the issue where pages were completed but signals didn't fire

Usage:
    python manage.py chunk_completed_pages
    python manage.py chunk_completed_pages --user-id 123
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from web_knowledge.models import WebsitePage
from AI_model.models import TenantKnowledge
from AI_model.tasks import chunk_webpage_async
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Chunk all completed WebsitePages that are missing chunks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Only chunk pages for this specific user ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be chunked without actually doing it',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        dry_run = options.get('dry_run', False)
        
        # Get completed pages
        pages_qs = WebsitePage.objects.filter(
            processing_status='completed'
        ).select_related('website__user')
        
        if user_id:
            pages_qs = pages_qs.filter(website__user_id=user_id)
        
        total_pages = pages_qs.count()
        self.stdout.write(f"Found {total_pages} completed pages")
        
        if total_pages == 0:
            self.stdout.write(self.style.WARNING("No completed pages found"))
            return
        
        # Find pages that are NOT chunked
        chunked_page_ids = set(
            TenantKnowledge.objects.filter(
                chunk_type='website'
            ).values_list('source_id', flat=True).distinct()
        )
        
        unchunked_pages = [
            page for page in pages_qs 
            if page.id not in chunked_page_ids
        ]
        
        unchunked_count = len(unchunked_pages)
        
        if unchunked_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ All pages are already chunked!"))
            return
        
        self.stdout.write(
            self.style.WARNING(
                f"Found {unchunked_count} pages that need chunking "
                f"({total_pages - unchunked_count} already chunked)"
            )
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN - Would chunk these pages:"))
            for page in unchunked_pages[:10]:  # Show first 10
                self.stdout.write(f"  - {page.title or page.url} (ID: {page.id})")
            if unchunked_count > 10:
                self.stdout.write(f"  ... and {unchunked_count - 10} more")
            return
        
        # Queue chunking tasks
        self.stdout.write("\n⏳ Queueing chunking tasks...")
        queued = 0
        failed = 0
        
        for page in unchunked_pages:
            try:
                chunk_webpage_async.apply_async(
                    args=[str(page.id)],
                    countdown=queued * 2  # Stagger tasks (2 seconds apart)
                )
                queued += 1
                
                if queued % 10 == 0:
                    self.stdout.write(f"  Queued {queued}/{unchunked_count} tasks...")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Failed to queue {page.id}: {e}")
                )
                failed += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Done! Queued {queued} chunking tasks"
            )
        )
        
        if failed > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠️  {failed} tasks failed to queue")
            )
        
        self.stdout.write(
            self.style.WARNING(
                f"\n⏳ Tasks will process over ~{(queued * 2) // 60} minutes "
                f"(staggered to avoid overload)"
            )
        )

