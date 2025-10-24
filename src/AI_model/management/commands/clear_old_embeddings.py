"""
Management command to clear old embeddings and regenerate with new dimensions
"""
from django.core.management.base import BaseCommand
from AI_model.models import TenantKnowledge


class Command(BaseCommand):
    help = 'Clear old 768-dim embeddings and prepare for 1536-dim OpenAI embeddings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleared without actually clearing',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Clear embeddings for specific user only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_filter = options.get('user')

        self.stdout.write('=' * 80)
        self.stdout.write('🧹 Clear Old Embeddings (768-dim → 1536-dim)')
        self.stdout.write('=' * 80)

        # Build queryset
        queryset = TenantKnowledge.objects.exclude(embedding__isnull=True)
        
        if user_filter:
            from accounts.models import User
            try:
                user = User.objects.get(username=user_filter)
                queryset = queryset.filter(user=user)
                self.stdout.write(f'\n📌 Filtering for user: {user.username}')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ User "{user_filter}" not found'))
                return

        total_count = queryset.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('\n✅ No embeddings found to clear'))
            return

        # Show statistics
        self.stdout.write(f'\n📊 Statistics:')
        self.stdout.write(f'   Total chunks with embeddings: {total_count}')
        
        # Group by chunk_type
        for chunk_type in queryset.values_list('chunk_type', flat=True).distinct():
            count = queryset.filter(chunk_type=chunk_type).count()
            self.stdout.write(f'   - {chunk_type}: {count} chunks')

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n🔍 DRY RUN: Would clear {total_count} embeddings'))
            self.stdout.write('\n💡 Run without --dry-run to actually clear embeddings')
            return

        # Confirm action
        self.stdout.write(self.style.WARNING(f'\n⚠️  About to clear {total_count} embeddings!'))
        self.stdout.write('   After clearing, run: python manage.py reconcile_knowledge_base')
        
        confirm = input('\n❓ Continue? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.ERROR('\n❌ Cancelled'))
            return

        # Clear embeddings
        self.stdout.write('\n🧹 Clearing embeddings...')
        updated = queryset.update(embedding=None)
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Cleared {updated} embeddings'))
        self.stdout.write('\n📝 Next steps:')
        self.stdout.write('   1. Run: python manage.py reconcile_knowledge_base')
        self.stdout.write('   2. Wait for embeddings to regenerate with OpenAI (1536-dim)')
        self.stdout.write('   3. Test hybrid search functionality')

