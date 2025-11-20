"""
Management command to create AIBehaviorSettings for existing users

Usage:
    python manage.py create_ai_behavior_for_existing_users
    
This is a one-time command to add AIBehaviorSettings to all existing users
who don't have one yet. Future users will get it automatically via signals.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from settings.models import AIBehaviorSettings

User = get_user_model()


class Command(BaseCommand):
    help = 'Create AIBehaviorSettings for existing users who don\'t have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        # Get all users
        users = User.objects.all()
        total_users = users.count()
        
        self.stdout.write(f'\n📊 Found {total_users} total users')
        
        # Check how many already have AIBehaviorSettings
        users_with_settings = User.objects.filter(ai_behavior__isnull=False).count()
        users_without_settings = total_users - users_with_settings
        
        self.stdout.write(f'✅ {users_with_settings} users already have AI Behavior Settings')
        self.stdout.write(f'❌ {users_without_settings} users need AI Behavior Settings\n')
        
        if users_without_settings == 0:
            self.stdout.write(self.style.SUCCESS('✨ All users already have AI Behavior Settings! Nothing to do.'))
            return
        
        created_count = 0
        error_count = 0
        
        for user in users:
            # Check if user already has settings
            if hasattr(user, 'ai_behavior') and user.ai_behavior:
                continue
            
            if dry_run:
                self.stdout.write(f'  [DRY RUN] Would create AI Behavior Settings for: {user.username}')
                created_count += 1
            else:
                try:
                    behavior, created = AIBehaviorSettings.objects.get_or_create(
                        user=user,
                        defaults={
                            'tone': 'friendly',
                            'emoji_usage': 'moderate',
                            'response_length': 'balanced',
                            'use_customer_name': True,
                            'use_bio_context': True,
                            'persuasive_selling_enabled': False,
                            'persuasive_cta_text': 'آیا می‌خواهید این محصول را سفارش دهید؟ 🛒',
                            'unknown_fallback_text': 'من در حال حاضر پاسخ دقیق این سوال را ندارم، اما همکارانم به زودی پاسخ شما را خواهند داد.',
                        }
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✅ Created AI Behavior Settings for: {user.username} ({user.email})')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠️ AI Behavior Settings already existed for: {user.username}')
                        )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Error creating for {user.username}: {str(e)}')
                    )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'🔍 DRY RUN: Would create {created_count} AI Behavior Settings'))
            self.stdout.write('\nRun without --dry-run to actually create them:')
            self.stdout.write('  python manage.py create_ai_behavior_for_existing_users')
        else:
            self.stdout.write(self.style.SUCCESS(f'🎉 Successfully created {created_count} AI Behavior Settings'))
            if error_count > 0:
                self.stdout.write(self.style.ERROR(f'❌ {error_count} errors occurred'))
        self.stdout.write('='*60 + '\n')

