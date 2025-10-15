#!/usr/bin/env python
"""
Sync all existing products to TenantKnowledge
Run this once after deploying the signal to ensure all products are searchable
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/Users/omidataei/Documents/GitHub/Fiko-Backend/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
django.setup()

from web_knowledge.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

print("="*80)
print("🔄 Syncing Products to TenantKnowledge")
print("="*80)

# Get all active products
products = Product.objects.filter(is_active=True).select_related('user')
total = products.count()

print(f"\nFound {total} active products")
print("\nTriggering signals for each product (this will add them to TenantKnowledge)...")
print("-"*80)

success_count = 0
error_count = 0

for i, product in enumerate(products, 1):
    try:
        # Re-save to trigger post_save signal
        product.save()
        success_count += 1
        print(f"✅ [{i}/{total}] {product.title} (User: {product.user.email})")
    except Exception as e:
        error_count += 1
        print(f"❌ [{i}/{total}] Failed: {product.title} - {str(e)}")

print("\n" + "="*80)
print(f"✅ Sync complete!")
print(f"  - Success: {success_count}")
print(f"  - Errors: {error_count}")
print("="*80)

