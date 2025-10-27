#!/bin/bash
# Test Website Crawling and Chunking

echo "🌐 Testing Website Crawling & Chunking"
echo "======================================"
echo ""
echo "Run this AFTER you've started a website crawl from the UI"
echo ""

# Get website URL from user
read -p "Enter website URL (or press ENTER for faracoach.com): " WEBSITE_URL
WEBSITE_URL=${WEBSITE_URL:-https://faracoach.com}

echo ""
echo "🔍 Checking crawl status for: $WEBSITE_URL"
echo ""

docker-compose exec -T web python manage.py shell <<PYTHON
from web_knowledge.models import WebsiteSource, WebsitePage
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model
import time

User = get_user_model()
user = User.objects.get(username='Faracoach')

website_url = "$WEBSITE_URL"

print("=" * 70)
print("📊 Website Crawl Status")
print("=" * 70)

# Find website source
try:
    website = WebsiteSource.objects.filter(user=user, url__icontains=website_url.replace('https://', '').replace('http://', '')).first()
    
    if not website:
        print(f"\n⚠️  No website source found for: {website_url}")
        print(f"\n   Please create it in the UI first:")
        print(f"   1. Go to Knowledge Base → Websites")
        print(f"   2. Add Website: {website_url}")
        print(f"   3. Start Crawl")
        print(f"   4. Run this script again")
    else:
        print(f"\n✅ Found website: {website.name}")
        print(f"   URL: {website.url}")
        print(f"   Status: {website.status}")
        print(f"   Max pages: {website.max_pages}")
        print(f"   Crawl depth: {website.crawl_depth}")
        
        # Get pages
        pages = WebsitePage.objects.filter(source=website)
        total_pages = pages.count()
        completed_pages = pages.filter(processing_status='completed').count()
        
        print(f"\n📄 Pages Crawled:")
        print(f"   Total: {total_pages}")
        print(f"   Completed: {completed_pages}")
        print(f"   Pending: {total_pages - completed_pages}")
        
        if website.status == 'crawling':
            print(f"\n⏳ Crawl in progress...")
            print(f"   Progress: {website.progress_percentage:.1f}%")
            print(f"   Pages crawled: {website.pages_crawled}/{website.estimated_pages}")
            print(f"\n   Check logs: docker logs -f celery_worker | grep -i crawl")
        
        elif website.status == 'completed':
            print(f"\n✅ Crawl completed!")
            
            # Check chunks
            website_chunks = TenantKnowledge.objects.filter(
                user=user, 
                chunk_type='website'
            )
            
            total_chunks = website_chunks.count()
            
            print(f"\n📦 Chunks Created:")
            print(f"   Total chunks: {total_chunks}")
            
            if total_chunks > 0:
                avg_words = sum(c.word_count for c in website_chunks) / total_chunks
                print(f"   Avg words per chunk: {avg_words:.0f}")
                
                # Show sample chunk
                sample = website_chunks.first()
                print(f"\n📝 Sample Chunk:")
                print(f"   Title: {sample.section_title}")
                print(f"   Words: {sample.word_count}")
                print(f"   TL;DR: {sample.tldr[:100]}...")
                print(f"   Preview: {sample.full_text[:150]}...")
                
                # Check embeddings
                has_emb = sample.full_embedding is not None
                print(f"\n🔢 Embeddings: {'✅ Yes' if has_emb else '❌ No'}")
                if has_emb:
                    import numpy as np
                    emb_array = np.array(sample.full_embedding)
                    print(f"   Dimensions: {len(emb_array)}")
                
                print(f"\n🎉 Website crawl & chunking successful!")
                
                # Check products
                from web_knowledge.models import Product
                products = Product.objects.filter(source=website)
                print(f"\n🛍️  Products Extracted: {products.count()}")
                
                if products.count() > 0:
                    for i, product in enumerate(products[:3], 1):
                        print(f"   {i}. {product.name} - {product.price} {product.currency}")
            
            else:
                print(f"\n⚠️  No chunks created yet!")
                print(f"   Checking if chunking is in progress...")
                print(f"   This might take a few minutes for {completed_pages} pages")
        
        elif website.status == 'failed':
            print(f"\n❌ Crawl failed!")
            print(f"   Error: {website.error_message}")
            print(f"\n   Check logs: docker logs celery_worker --tail 200 | grep -i error")
        
        else:
            print(f"\n⏳ Status: {website.status}")
        
        # Show recent pages
        if total_pages > 0:
            print(f"\n📋 Recent Pages (last 5):")
            for page in pages.order_by('-created_at')[:5]:
                status_icon = '✅' if page.processing_status == 'completed' else '⏳'
                print(f"   {status_icon} {page.title[:50]} ({page.word_count} words)")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

PYTHON

echo ""
echo "======================================"
echo "✅ Check complete!"
echo ""
echo "💡 Next steps:"
echo "   1. If crawl is in progress, wait and run this script again"
echo "   2. If completed, test query answering: ./test_query_answer.sh"
echo "   3. Check celery logs: docker logs -f celery_worker | grep -i crawl"
echo ""

