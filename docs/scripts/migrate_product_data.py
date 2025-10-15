#!/usr/bin/env python
"""
Migration script for updating existing Product data with new fields
Run this after applying database migrations

Usage:
    python migrate_product_data.py [--dry-run]
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings.settings')
django.setup()

from web_knowledge.models import Product


def migrate_products(dry_run=False):
    """
    Migrate existing products to populate new fields with defaults
    """
    print("=" * 80)
    print("Product Data Migration Script")
    print("=" * 80)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")
    else:
        print("\n⚠️  LIVE MODE - Changes will be applied\n")
    
    # Get all products
    products = Product.objects.all()
    total_products = products.count()
    
    print(f"Found {total_products} products to process\n")
    
    if total_products == 0:
        print("✅ No products to migrate")
        return
    
    updated_count = 0
    skipped_count = 0
    
    for product in products:
        needs_update = False
        updates = []
        
        # Set default extraction_method if not set
        if not product.extraction_method:
            product.extraction_method = 'manual'
            needs_update = True
            updates.append("extraction_method: 'manual'")
        
        # Set default currency if not set
        if not product.currency:
            product.currency = 'USD'
            needs_update = True
            updates.append("currency: 'USD'")
        
        # Set default is_active if needed (should be True by default in model)
        if product.is_active is None:
            product.is_active = True
            needs_update = True
            updates.append("is_active: True")
        
        # Set default in_stock if needed
        if product.in_stock is None:
            product.in_stock = True
            needs_update = True
            updates.append("in_stock: True")
        
        # Ensure JSON fields have proper defaults
        if product.features is None:
            product.features = []
            needs_update = True
            updates.append("features: []")
        
        if product.specifications is None:
            product.specifications = {}
            needs_update = True
            updates.append("specifications: {}")
        
        if product.tags is None:
            product.tags = []
            needs_update = True
            updates.append("tags: []")
        
        if product.keywords is None:
            product.keywords = []
            needs_update = True
            updates.append("keywords: []")
        
        if product.images is None:
            product.images = []
            needs_update = True
            updates.append("images: []")
        
        if product.extraction_metadata is None:
            product.extraction_metadata = {}
            needs_update = True
            updates.append("extraction_metadata: {}")
        
        # Set extraction_confidence default
        if product.extraction_confidence is None:
            product.extraction_confidence = 1.0
            needs_update = True
            updates.append("extraction_confidence: 1.0")
        
        # Calculate discount if needed
        if product.original_price and product.price:
            if product.original_price > product.price and not product.discount_percentage:
                discount_pct = ((product.original_price - product.price) / product.original_price) * 100
                product.discount_percentage = Decimal(str(round(discount_pct, 2)))
                needs_update = True
                updates.append(f"discount_percentage: {product.discount_percentage}%")
        
        if needs_update:
            print(f"Updating product: {product.title}")
            for update in updates:
                print(f"  - {update}")
            
            if not dry_run:
                try:
                    product.save()
                    updated_count += 1
                    print("  ✅ Updated\n")
                except Exception as e:
                    print(f"  ❌ Error: {str(e)}\n")
                    skipped_count += 1
            else:
                updated_count += 1
                print("  🔍 Would update (dry run)\n")
        else:
            skipped_count += 1
    
    # Summary
    print("=" * 80)
    print("Migration Summary")
    print("=" * 80)
    print(f"Total products: {total_products}")
    print(f"Updated: {updated_count}")
    print(f"Skipped (no changes needed): {skipped_count}")
    
    if dry_run:
        print("\n🔍 This was a dry run. Run without --dry-run to apply changes.")
    else:
        print("\n✅ Migration complete!")


def analyze_products():
    """
    Analyze current product data to show what needs migration
    """
    print("=" * 80)
    print("Product Data Analysis")
    print("=" * 80)
    
    products = Product.objects.all()
    total = products.count()
    
    print(f"\nTotal products: {total}\n")
    
    if total == 0:
        print("No products found.")
        return
    
    # Analyze extraction methods
    print("Extraction Methods:")
    manual = products.filter(extraction_method='manual').count()
    ai_auto = products.filter(extraction_method='ai_auto').count()
    ai_assisted = products.filter(extraction_method='ai_assisted').count()
    null_method = products.filter(extraction_method__isnull=True).count() + \
                  products.filter(extraction_method='').count()
    
    print(f"  - Manual: {manual}")
    print(f"  - AI Auto: {ai_auto}")
    print(f"  - AI Assisted: {ai_assisted}")
    print(f"  - Not Set: {null_method}")
    
    # Analyze currencies
    print("\nCurrencies:")
    for currency in Product.CURRENCY_CHOICES:
        count = products.filter(currency=currency[0]).count()
        if count > 0:
            print(f"  - {currency[1]}: {count}")
    null_currency = products.filter(currency__isnull=True).count() + \
                    products.filter(currency='').count()
    if null_currency > 0:
        print(f"  - Not Set: {null_currency}")
    
    # Analyze pricing
    print("\nPricing:")
    with_price = products.exclude(price__isnull=True).count()
    with_original_price = products.exclude(original_price__isnull=True).count()
    with_discount_pct = products.exclude(discount_percentage__isnull=True).count()
    with_discount_amt = products.exclude(discount_amount__isnull=True).count()
    
    print(f"  - With Price: {with_price}")
    print(f"  - With Original Price: {with_original_price}")
    print(f"  - With Discount Percentage: {with_discount_pct}")
    print(f"  - With Discount Amount: {with_discount_amt}")
    
    # Analyze availability
    print("\nAvailability:")
    active = products.filter(is_active=True).count()
    inactive = products.filter(is_active=False).count()
    in_stock = products.filter(in_stock=True).count()
    out_of_stock = products.filter(in_stock=False).count()
    
    print(f"  - Active: {active}")
    print(f"  - Inactive: {inactive}")
    print(f"  - In Stock: {in_stock}")
    print(f"  - Out of Stock: {out_of_stock}")
    
    # Analyze new fields
    print("\nNew Fields Usage:")
    with_short_desc = products.exclude(short_description='').count()
    with_long_desc = products.exclude(long_description='').count()
    with_features = products.exclude(features=[]).count()
    with_specs = products.exclude(specifications={}).count()
    with_category = products.exclude(category='').count()
    with_brand = products.exclude(brand='').count()
    with_main_image = products.exclude(main_image='').count()
    
    print(f"  - With Short Description: {with_short_desc}")
    print(f"  - With Long Description: {with_long_desc}")
    print(f"  - With Features: {with_features}")
    print(f"  - With Specifications: {with_specs}")
    print(f"  - With Category: {with_category}")
    print(f"  - With Brand: {with_brand}")
    print(f"  - With Main Image: {with_main_image}")
    
    # Analyze auto-extraction
    print("\nAuto-Extraction:")
    with_source_website = products.exclude(source_website__isnull=True).count()
    with_source_page = products.exclude(source_page__isnull=True).count()
    auto_extracted = products.filter(extraction_method__in=['ai_auto', 'ai_assisted']).count()
    
    print(f"  - With Source Website: {with_source_website}")
    print(f"  - With Source Page: {with_source_page}")
    print(f"  - Auto-Extracted: {auto_extracted}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate Product data to new schema')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run without making changes')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze current product data')
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_products()
    else:
        migrate_products(dry_run=args.dry_run)

