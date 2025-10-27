#!/bin/bash
# Clean all chunks for Faracoach user - Fresh Start Test

echo "🧹 Cleaning all chunks for user: Faracoach"
echo "=========================================="
echo ""

# Step 1: Check current stats
echo "📊 Current Stats:"
docker-compose exec -T web python manage.py shell <<'PYTHON'
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    user = User.objects.get(username='Faracoach')
    
    stats = {
        'website': TenantKnowledge.objects.filter(user=user, chunk_type='website').count(),
        'product': TenantKnowledge.objects.filter(user=user, chunk_type='product').count(),
        'faq': TenantKnowledge.objects.filter(user=user, chunk_type='faq').count(),
        'manual': TenantKnowledge.objects.filter(user=user, chunk_type='manual').count(),
    }
    
    total = sum(stats.values())
    
    print(f"   User: {user.username}")
    print(f"   Total chunks: {total}")
    for chunk_type, count in stats.items():
        if count > 0:
            print(f"   - {chunk_type}: {count} chunks")
    
    if total == 0:
        print("\n✅ No chunks found - already clean!")
    
except User.DoesNotExist:
    print("❌ User 'Faracoach' not found!")
PYTHON

echo ""
echo "🗑️  Deleting all chunks..."

# Step 2: Delete all chunks
docker-compose exec -T web python manage.py shell <<'PYTHON'
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    user = User.objects.get(username='Faracoach')
    
    # Delete all chunks for this user
    deleted_count = TenantKnowledge.objects.filter(user=user).delete()[0]
    
    print(f"✅ Deleted {deleted_count} chunks for user: {user.username}")
    
except User.DoesNotExist:
    print("❌ User 'Faracoach' not found!")
except Exception as e:
    print(f"❌ Error: {e}")
PYTHON

echo ""
echo "✅ Verification - Stats after deletion:"

# Step 3: Verify deletion
docker-compose exec -T web python manage.py shell <<'PYTHON'
from AI_model.models import TenantKnowledge
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    user = User.objects.get(username='Faracoach')
    
    stats = {
        'website': TenantKnowledge.objects.filter(user=user, chunk_type='website').count(),
        'product': TenantKnowledge.objects.filter(user=user, chunk_type='product').count(),
        'faq': TenantKnowledge.objects.filter(user=user, chunk_type='faq').count(),
        'manual': TenantKnowledge.objects.filter(user=user, chunk_type='manual').count(),
    }
    
    total = sum(stats.values())
    
    print(f"   User: {user.username}")
    print(f"   Total chunks: {total}")
    
    if total == 0:
        print("\n🎉 All chunks deleted successfully! Fresh start ready!")
    else:
        print("\n⚠️  Some chunks still exist:")
        for chunk_type, count in stats.items():
            if count > 0:
                print(f"   - {chunk_type}: {count} chunks")
    
except User.DoesNotExist:
    print("❌ User 'Faracoach' not found!")
PYTHON

echo ""
echo "=========================================="
echo "✅ Cleanup complete!"
echo ""

