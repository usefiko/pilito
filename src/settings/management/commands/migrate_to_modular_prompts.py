"""
Management command to migrate old auto_prompt to new modular prompt system

Usage:
    python manage.py migrate_to_modular_prompts

This command is OPTIONAL and only needed if you have customized the old auto_prompt field.
The new system has better default values already configured.
"""

from django.core.management.base import BaseCommand
from settings.models import GeneralSettings


class Command(BaseCommand):
    help = (
        'Migrate old auto_prompt to new modular prompt system. '
        'This is OPTIONAL - new defaults are already configured.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔄 Migrating to Modular Prompt System"))
        self.stdout.write("=" * 80)
        
        try:
            settings = GeneralSettings.get_settings()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: Could not load GeneralSettings: {e}"))
            return
        
        # Check if new fields are already configured
        has_modular = any([
            settings.ai_role and settings.ai_role.strip() and settings.ai_role != "You are an AI customer service assistant.",
            settings.language_rules and settings.language_rules.strip(),
            settings.tone_and_style and settings.tone_and_style.strip(),
        ])
        
        if has_modular:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  New modular fields are already configured!\n"
                    "   No migration needed. Your settings are already using the new system."
                )
            )
            return
        
        # Check if old auto_prompt exists and is customized
        has_custom_auto_prompt = (
            settings.auto_prompt and 
            settings.auto_prompt.strip() and 
            "You are an AI customer service representative" not in settings.auto_prompt
        )
        
        if not has_custom_auto_prompt:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n✅ No custom auto_prompt found.\n"
                    "   Using default modular prompt configuration.\n"
                    "   You can customize it in Admin Panel → General AI Settings"
                )
            )
            return
        
        # Show what we're migrating
        self.stdout.write("\n📝 Found custom auto_prompt:")
        self.stdout.write("─" * 80)
        preview = settings.auto_prompt[:300] + "..." if len(settings.auto_prompt) > 300 else settings.auto_prompt
        self.stdout.write(preview)
        self.stdout.write("─" * 80)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n🔍 DRY RUN MODE\n"
                    "   Your custom auto_prompt is preserved in the deprecated field.\n"
                    "   Please manually review and configure the new modular fields in Admin Panel.\n"
                    "\n💡 Recommended Steps:\n"
                    "   1. Go to Admin Panel → General AI Settings\n"
                    "   2. Review your old auto_prompt in the '[DEPRECATED] Old Auto Prompt' section\n"
                    "   3. Split it into the new modular sections:\n"
                    "      - AI Role & Identity\n"
                    "      - Language & Localization\n"
                    "      - Tone & Style\n"
                    "      - Response Guidelines\n"
                    "      - Greeting Rules\n"
                    "      - Anti-Hallucination Rules\n"
                    "      - Link Handling Rules\n"
                    "   4. Save your changes\n"
                    "\n⚠️  The old auto_prompt field will continue to work as fallback,\n"
                    "   but we recommend migrating to the new modular system for better control."
                )
            )
            return
        
        # In non-dry-run mode, we don't auto-migrate because it's too complex
        # Just inform the user
        self.stdout.write(
            self.style.WARNING(
                "\n⚠️  MANUAL MIGRATION REQUIRED\n"
                "\n   Your custom auto_prompt is too complex to auto-migrate.\n"
                "   Please manually configure the new modular fields.\n"
                "\n💡 Steps:\n"
                "   1. Go to Admin Panel → General AI Settings\n"
                "   2. Review your old auto_prompt in '[DEPRECATED] Old Auto Prompt'\n"
                "   3. Copy relevant parts to the new modular sections\n"
                "   4. Save your changes\n"
                "\n✅ Your old auto_prompt is preserved and will work as fallback\n"
                "   until you configure the new fields."
            )
        )
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(
            self.style.SUCCESS(
                "✅ Migration check complete!\n"
                "   Visit Admin Panel to configure your modular prompts."
            )
        )
        self.stdout.write("=" * 80)

