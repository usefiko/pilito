"""
Management command to remove duplicate Q&A pairs
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from web_knowledge.models import QAPair


class Command(BaseCommand):
    help = 'Remove duplicate Q&A pairs (same question on same page)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Find duplicates (same question on same page)
        duplicates = QAPair.objects.values('page', 'question').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        total_duplicates = 0
        total_removed = 0
        
        for duplicate in duplicates:
            page_id = duplicate['page']
            question = duplicate['question']
            count = duplicate['count']
            
            # Get all Q&A pairs with this question on this page
            qa_pairs = QAPair.objects.filter(
                page_id=page_id,
                question=question
            ).order_by('created_at')  # Keep the oldest one
            
            self.stdout.write(
                f"Found {count} duplicates for question: '{question[:50]}...'"
            )
            
            # Keep the first one, delete the rest
            pairs_to_delete = qa_pairs[1:]  # Skip the first (oldest) one
            
            for qa_pair in pairs_to_delete:
                total_duplicates += 1
                if not dry_run:
                    qa_pair.delete()
                    total_removed += 1
                    self.stdout.write(f"  - Deleted duplicate Q&A: {qa_pair.id}")
                else:
                    self.stdout.write(f"  - Would delete: {qa_pair.id}")
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Found {total_duplicates} duplicate Q&A pairs that would be removed'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully removed {total_removed} duplicate Q&A pairs'
                )
            )
        
        # Show summary of remaining Q&A pairs
        remaining_qa = QAPair.objects.count()
        self.stdout.write(f'Total Q&A pairs remaining: {remaining_qa}')
