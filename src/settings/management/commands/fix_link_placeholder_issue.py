"""
Management command to fix Gemini link placeholder issue
Adds explicit instruction to include full URLs in responses
"""
from django.core.management.base import BaseCommand
from settings.models import GeneralSettings


class Command(BaseCommand):
    help = 'Fix Gemini link placeholder issue by updating Auto Prompt'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Fixing Gemini link placeholder issue...")
        
        settings = GeneralSettings.get_settings()
        
        # Check if already fixed
        if '🔗 CRITICAL - Links & URLs:' in settings.auto_prompt:
            self.stdout.write(self.style.SUCCESS('✅ Auto Prompt already has link instructions'))
            return
        
        # Add link instructions to existing auto_prompt
        link_instruction = '''

🔗 CRITICAL - Links & URLs:
- Always include FULL URLs (e.g., https://fiko.net/pricing)
- NEVER use placeholders like [link] or [URL]
- Write complete clickable links in your responses'''
        
        settings.auto_prompt = settings.auto_prompt.strip() + link_instruction
        settings.save()
        
        self.stdout.write(self.style.SUCCESS('✅ Auto Prompt updated successfully!'))
        self.stdout.write(f'\n📝 New Auto Prompt:\n{settings.auto_prompt}\n')

