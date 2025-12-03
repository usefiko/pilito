"""
Management command to update existing invite codes from 10 characters to 4 characters
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
import random
import string


class Command(BaseCommand):
    help = 'Update all existing invite codes from 10-character to 4-character format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
        
        # Get all users with invite codes
        users = User.objects.exclude(invite_code__isnull=True).exclude(invite_code='')
        total_users = users.count()
        
        self.stdout.write(f'Found {total_users} users with invite codes')
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        with transaction.atomic():
            for user in users:
                old_code = user.invite_code
                
                # Skip if already 4 characters
                if len(old_code) == 4 and old_code.isdigit():
                    skipped_count += 1
                    continue
                
                try:
                    # Generate new 4-digit code
                    new_code = self._generate_unique_code(user)
                    
                    if not dry_run:
                        user.invite_code = new_code
                        user.save(update_fields=['invite_code', 'updated_at'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Updated user {user.email}: {old_code} → {new_code}'
                        )
                    )
                    updated_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Error updating user {user.email}: {str(e)}'
                        )
                    )
                    error_count += 1
            
            if dry_run:
                # Rollback transaction in dry-run mode
                transaction.set_rollback(True)
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Total users processed: {total_users}')
        self.stdout.write(self.style.SUCCESS(f'✓ Updated: {updated_count}'))
        self.stdout.write(self.style.WARNING(f'⊘ Skipped (already 4-digit): {skipped_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ Errors: {error_count}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes were saved'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ All changes saved successfully!'))
    
    def _generate_unique_code(self, exclude_user=None):
        """Generate a unique 4-digit invite code"""
        max_attempts = 100
        for _ in range(max_attempts):
            code = ''.join(random.choices(string.digits, k=4))
            
            # Check if code exists for other users
            query = User.objects.filter(invite_code=code)
            if exclude_user:
                query = query.exclude(pk=exclude_user.pk)
            
            if not query.exists():
                return code
        
        raise Exception('Could not generate unique code after maximum attempts')

