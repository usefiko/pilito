"""
Management command برای seed کردن default keywords به database
Usage: python manage.py seed_default_keywords
"""

from django.core.management.base import BaseCommand
from AI_model.models import IntentKeyword
from AI_model.services.query_router import QueryRouter


class Command(BaseCommand):
    help = 'Seed default keywords from code to database (one-time setup)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if keywords already exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        
        self.stdout.write("="*80)
        self.stdout.write(self.style.SUCCESS("🌱 Seed Default Keywords to Database"))
        self.stdout.write("="*80)
        
        default_keywords = QueryRouter.DEFAULT_KEYWORDS
        total_keywords = 0
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for intent, lang_keywords in default_keywords.items():
            for lang, keywords in lang_keywords.items():
                for keyword in keywords:
                    total_keywords += 1
                    
                    # Check if already exists (global only)
                    existing = IntentKeyword.objects.filter(
                        intent=intent,
                        language=lang,
                        keyword=keyword,
                        user__isnull=True  # Only global
                    ).first()
                    
                    if existing:
                        if force:
                            # Update weight if forcing
                            if not dry_run:
                                existing.weight = 1.0
                                existing.is_active = True
                                existing.save()
                            updated_count += 1
                            self.stdout.write(
                                f"  🔄 Updated: [{lang}] {intent} → '{keyword}'"
                            )
                        else:
                            skipped_count += 1
                            self.stdout.write(
                                self.style.WARNING(f"  ⏭️  Skipped (exists): [{lang}] {intent} → '{keyword}'")
                            )
                    else:
                        if not dry_run:
                            IntentKeyword.objects.create(
                                intent=intent,
                                language=lang,
                                keyword=keyword,
                                weight=1.0,
                                is_active=True,
                                user=None  # Global
                            )
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✅ Created: [{lang}] {intent} → '{keyword}'")
                        )
        
        # Summary
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write("📊 خلاصه:")
        self.stdout.write(f"{'='*80}")
        self.stdout.write(f"  Total keywords in code: {total_keywords}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  DRY RUN - No changes made"))
            self.stdout.write(f"  Would create: {created_count}")
            if force:
                self.stdout.write(f"  Would update: {updated_count}")
            self.stdout.write(f"  Would skip: {skipped_count}")
        else:
            self.stdout.write(f"  ✅ Created: {created_count}")
            if force:
                self.stdout.write(f"  🔄 Updated: {updated_count}")
            self.stdout.write(f"  ⏭️  Skipped: {skipped_count}")
        
        # Verify
        db_count = IntentKeyword.objects.filter(user__isnull=True, is_active=True).count()
        self.stdout.write(f"\n📊 Total global keywords in DB: {db_count}")
        
        if db_count == 0 and not dry_run:
            self.stdout.write(
                self.style.ERROR("\n❌ Warning: No keywords in database!")
            )
            self.stdout.write("   Run this command again or check for errors.")
        elif db_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Success! {db_count} global keywords now in database.")
            )
            self.stdout.write("   You can now manage all keywords from admin panel.")
            self.stdout.write("   Default keywords in code are now just for reference.")
        
        # Clear cache
        if not dry_run:
            from django.core.cache import cache
            # Try to clear all intent_keywords cache entries
            try:
                # If using Redis or similar cache backend with pattern support
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern("intent_keywords:*")
                else:
                    # Fallback: clear all cache (or specific keys if known)
                    cache.clear()
                self.stdout.write("\n✅ Cache cleared")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"\n⚠️  Cache clear failed: {e}"))

