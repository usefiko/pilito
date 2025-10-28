#!/bin/bash

# 🔍 Real-time Crawl & Chunking Monitor
# Usage: ./monitor_crawl.sh

echo "🔍 Pilito Crawl & Chunking Monitor"
echo "=================================="
echo ""

while true; do
    clear
    echo "🕐 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=================================="
    echo ""
    
    # Queue status
    echo "📊 Celery Queue Status:"
    echo "----------------------"
    docker-compose exec -T redis redis-cli LLEN celery | awk '{print "  General:      " $1 " tasks"}'
    docker-compose exec -T redis redis-cli LLEN high_priority | awk '{print "  High Priority:" $1 " tasks"}'
    docker-compose exec -T redis redis-cli LLEN default | awk '{print "  Default:      " $1 " tasks"}'
    docker-compose exec -T redis redis-cli LLEN low_priority | awk '{print "  Low Priority: " $1 " tasks (processing/crawling)"}'
    echo ""
    
    # Database status
    echo "📦 Database Status (User ID: 12):"
    echo "--------------------------------"
    docker-compose exec -T web python manage.py shell -c "
from web_knowledge.models import WebsitePage, WebsiteSource
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model
import sys

User = get_user_model()
user = User.objects.get(id=12)
website = WebsiteSource.objects.filter(user=user).order_by('-created_at').first()

if website:
    total = WebsitePage.objects.filter(website=website).count()
    pending = WebsitePage.objects.filter(website=website, processing_status='pending').count()
    processing = WebsitePage.objects.filter(website=website, processing_status='processing').count()
    completed = WebsitePage.objects.filter(website=website, processing_status='completed').count()
    chunked = TenantKnowledge.objects.filter(user=user, chunk_type='website').values('source_id').distinct().count()
    gap = completed - chunked
    
    print(f'  Website:    {website.name}')
    print(f'  Total:      {total} pages')
    print(f'  Pending:    {pending} pages')
    print(f'  Processing: {processing} pages')
    print(f'  Completed:  {completed} pages')
    print(f'  Chunked:    {chunked} pages')
    
    if gap > 0:
        print(f'  ⚠️  Gap:      {gap} pages (completed but not chunked)')
    else:
        print(f'  ✅ Gap:      0 pages (all synced!)')
    
    # Progress bar
    progress = int((chunked / total) * 100) if total > 0 else 0
    bar_length = 30
    filled = int(bar_length * progress / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f'  Progress:   [{bar}] {progress}%')
else:
    print('  No website found for this user')
" 2>/dev/null
    
    echo ""
    
    # Recent activity (last 10 seconds)
    echo "🔄 Recent Activity (last 10 tasks):"
    echo "-----------------------------------"
    docker-compose logs --tail 50 celery_worker 2>/dev/null | \
        grep -E "succeeded in|Processing content|Task.*received" | \
        tail -10 | \
        sed 's/celery_worker  | /  /' | \
        sed 's/\[2025-/[/' | \
        cut -c1-100
    
    echo ""
    echo "Press Ctrl+C to stop monitoring..."
    echo ""
    
    sleep 5
done

