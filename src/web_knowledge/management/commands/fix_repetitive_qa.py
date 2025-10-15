"""
Management command to fix repetitive Q&A pairs
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from web_knowledge.models import QAPair, WebsiteSource
from web_knowledge.tasks import _generate_fallback_qa_pairs


class Command(BaseCommand):
    help = 'Fix repetitive Q&A pairs by removing duplicates and generating better ones'

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
        
        if website_id:
            try:
                websites = [WebsiteSource.objects.get(id=website_id)]
            except WebsiteSource.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Website with ID {website_id} not found')
                )
                return
        else:
            websites = WebsiteSource.objects.all()
        
        total_removed = 0
        total_created = 0
        
        for website in websites:
            self.stdout.write(f'\n🌐 Processing website: {website.name}')
            
            # Find repetitive questions across all pages of this website
            repetitive_questions = QAPair.objects.filter(
                page__website=website
            ).values('question').annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            for rep_q in repetitive_questions:
                question = rep_q['question']
                count = rep_q['count']
                
                self.stdout.write(f'  📋 Found {count} copies of: "{question[:60]}..."')
                
                # Get all Q&A pairs with this question
                duplicate_qa_pairs = QAPair.objects.filter(
                    page__website=website,
                    question=question
                ).order_by('created_at')
                
                if not dry_run:
                    # Delete all duplicates
                    deleted_count = duplicate_qa_pairs.delete()[0]
                    total_removed += deleted_count
                    self.stdout.write(f'    ❌ Deleted {deleted_count} duplicate Q&A pairs')
                else:
                    self.stdout.write(f'    ❌ Would delete {count} duplicate Q&A pairs')
            
            # Now regenerate better Q&A for each page
            pages = website.pages.filter(processing_status='completed')
            
            for page in pages:
                existing_qa_count = page.qa_pairs.count()
                
                if existing_qa_count < 2:  # Only generate if page has few Q&As
                    self.stdout.write(f'  📄 Generating new Q&A for page: {page.title[:50]}...')
                    
                    try:
                        # Generate new, diverse Q&A pairs
                        new_qa_data = _generate_fallback_qa_pairs(page, 3)
                        
                        if not dry_run:
                            created_count = 0
                            for qa_data in new_qa_data:
                                # Check if question already exists
                                if not QAPair.objects.filter(
                                    page=page,
                                    question=qa_data['question']
                                ).exists():
                                    QAPair.objects.create(
                                        page=page,
                                        question=qa_data['question'],
                                        answer=qa_data['answer'],
                                        context='',
                                        confidence_score=qa_data.get('confidence', 0.8),
                                        question_type=qa_data.get('question_type', 'factual'),
                                        category=qa_data.get('category', 'general'),
                                        keywords=qa_data.get('keywords', []),
                                        created_by_ai=False,
                                        generation_status='completed'
                                    )
                                    created_count += 1
                            
                            total_created += created_count
                            self.stdout.write(f'    ✅ Created {created_count} new Q&A pairs')
                        else:
                            self.stdout.write(f'    ✅ Would create {len(new_qa_data)} new Q&A pairs')
                            
                    except Exception as e:
                        self.stdout.write(f'    ❌ Error generating Q&A: {e}')
        
        # Summary
        self.stdout.write('\n=== Summary ===')
        if dry_run:
            remaining_qa = QAPair.objects.count()
            self.stdout.write(f'Current total Q&A pairs: {remaining_qa}')
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would remove duplicates and create new diverse Q&A'
                )
            )
        else:
            remaining_qa = QAPair.objects.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Removed {total_removed} repetitive Q&A pairs'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Created {total_created} new diverse Q&A pairs'
                )
            )
            self.stdout.write(f'Total Q&A pairs now: {remaining_qa}')
