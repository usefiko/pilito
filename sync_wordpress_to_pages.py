#!/usr/bin/env python
"""
Script to sync existing WordPress content to WebsitePage
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
django.setup()

from integrations.models import WordPressContent
from web_knowledge.models import WebsiteSource, WebsitePage

print("🔄 Syncing WordPress content to WebsitePage...")
print()

# Create WordPress source
wordpress_source, created = WebsiteSource.objects.get_or_create(
    url='https://wordpress-sync',
    defaults={
        'user_id': 1,  # Will be updated per content
        'name': '📝 محتوای WordPress',
        'description': 'صفحات و نوشته‌های همگام‌سازی شده از WordPress',
        'max_pages': 10000,
        'crawl_depth': 1,
        'crawl_status': 'completed'
    }
)

if created:
    print(f"✅ Created WebsiteSource: {wordpress_source.name}")
else:
    print(f"✅ Found existing WebsiteSource: {wordpress_source.name}")

# Sync all WordPress content
synced = 0
skipped = 0

for wp_content in WordPressContent.objects.all():
    try:
        # Update website source user if needed
        if wordpress_source.user_id != wp_content.user_id:
            # Get or create per-user WordPress source
            user_wp_source, _ = WebsiteSource.objects.get_or_create(
                user=wp_content.user,
                url=f'https://wordpress-sync-{wp_content.user.id}',
                defaults={
                    'name': f'📝 محتوای WordPress - {wp_content.user.email}',
                    'description': 'صفحات و نوشته‌های همگام‌سازی شده از WordPress',
                    'max_pages': 10000,
                    'crawl_depth': 1,
                    'crawl_status': 'completed'
                }
            )
        else:
            user_wp_source = wordpress_source
        
        # Create or update WebsitePage
        webpage, webpage_created = WebsitePage.objects.update_or_create(
            url=wp_content.permalink,
            defaults={
                'website': user_wp_source,
                'title': wp_content.title,
                'cleaned_content': wp_content.content,
                'raw_content': wp_content.content,
                'word_count': len(wp_content.content.split()),
                'processing_status': 'completed',
                'processed_at': wp_content.last_synced_at,
                'source_type': 'wordpress',
                'wordpress_post_id': wp_content.wp_post_id,
                'meta_description': wp_content.excerpt[:160] if wp_content.excerpt else '',
            }
        )
        
        action = "Created" if webpage_created else "Updated"
        print(f"  ✅ {action}: {wp_content.title[:60]}")
        synced += 1
        
    except Exception as e:
        print(f"  ❌ Error: {wp_content.title[:60]} - {str(e)}")
        skipped += 1

print()
print(f"📊 Results:")
print(f"  Synced: {synced}")
print(f"  Skipped: {skipped}")
print(f"  Total WebsitePage (WordPress): {WebsitePage.objects.filter(source_type='wordpress').count()}")

