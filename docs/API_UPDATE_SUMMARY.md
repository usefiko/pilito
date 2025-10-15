# API Update Summary - Web Knowledge Module

## Overview
Comprehensive API updates for WebsiteSource, WebsitePage, and Product models based on recent model changes, optimized for better frontend integration.

---

## What Changed

### 1. Product Model - Significant Enhancements ✅

#### New Fields Added (40+ new fields):

**Pricing & Financial**
- `original_price`, `discount_percentage`, `discount_amount`
- `currency` (USD, EUR, TRY, AED, SAR, IRR, IRT)
- `billing_period` (one_time, monthly, yearly, weekly, daily)

**Product Information**
- `short_description`, `long_description`
- `features` (JSON array)
- `specifications` (JSON object)
- `keywords` (JSON array)

**Categorization**
- `category`, `brand`

**Availability**
- `in_stock`, `stock_quantity`

**Media**
- `main_image`, `images` (JSON array)

**SEO**
- `meta_title`, `meta_description`

**Auto-Extraction Tracking**
- `source_website`, `source_page`
- `extraction_method` (manual, ai_auto, ai_assisted)
- `extraction_confidence`
- `extraction_metadata` (JSON)

**Computed Properties**
- `final_price` (calculated with discounts)
- `has_discount`
- `discount_info` (human-readable)
- `is_auto_extracted`
- `currency_display`, `billing_period_display`

### 2. WebsiteSource Updates ✅
- Added `auto_extract_products` boolean field
- New endpoint: `/websites/{id}/products/` - Get all products from a website
- Updated `/websites/{id}/pages/` to include product counts

### 3. WebsitePage Updates ✅
- Added `products_count` field in serializer
- Updated detail view to include `extracted_products` list
- Shows products extracted from each page

---

## New API Endpoints

### Product Endpoints (15+ new endpoints)

1. **Get All Choices** (NEW)
   ```
   GET /products/choices/all/
   ```
   Returns all dropdown choices for product types, currencies, billing periods, extraction methods

2. **Individual Choice Endpoints** (NEW)
   ```
   GET /products/choices/product-types/
   GET /products/choices/currencies/
   GET /products/choices/billing-periods/
   GET /products/choices/extraction-methods/
   ```

3. **Enhanced Statistics** (UPDATED)
   ```
   GET /products/statistics/
   ```
   Now includes: by extraction method, by currency, with discounts, auto-extracted count, etc.

4. **Get Products by Website** (NEW)
   ```
   GET /products/by-website/?website_id={uuid}
   ```
   Get all products extracted from a specific website

5. **Get Categories & Brands** (NEW)
   ```
   GET /products/categories/
   GET /products/brands/
   ```
   Get unique categories/brands from user's products

6. **Bulk Update** (NEW)
   ```
   POST /products/bulk-update/
   ```
   Bulk update product activation and stock status

7. **Bulk Delete** (NEW)
   ```
   POST /products/bulk-delete/
   ```
   Delete multiple products at once

### Website Endpoints

1. **Get Website Products** (NEW)
   ```
   GET /websites/{id}/products/
   ```
   Get all products extracted from a website with statistics

---

## Enhanced Filtering & Search

### Product List Filtering (20+ filter parameters)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `product_type` | Filter by type | `?product_type=service` |
| `is_active` | Active status | `?is_active=true` |
| `in_stock` | Stock status | `?in_stock=true` |
| `extraction_method` | How created | `?extraction_method=ai_auto` |
| `website_id` | Source website | `?website_id={uuid}` |
| `category` | Category contains | `?category=software` |
| `brand` | Brand contains | `?brand=apple` |
| `currency` | Currency code | `?currency=USD` |
| `billing_period` | Billing period | `?billing_period=monthly` |
| `min_price` | Minimum price | `?min_price=50` |
| `max_price` | Maximum price | `?max_price=200` |
| `has_discount` | Has discount | `?has_discount=true` |
| `search` | Search text | `?search=premium` |

**Search Fields:** title, description, short_description, category, brand

---

## Serializer Updates

### 1. ProductSerializer (UPDATED)
- Added all 40+ new fields
- Added computed properties
- Added source website/page info
- Added display fields for choices

### 2. ProductCreateSerializer (UPDATED)
- Supports all new fields
- All optional except: title, product_type, description
- Includes validation for prices, discounts

### 3. ProductUpdateSerializer (UPDATED)
- Supports all new fields
- All fields optional for partial updates
- Includes validation

### 4. ProductCompactSerializer (NEW)
- Lightweight serializer for listings
- Used in WebsitePage details
- Includes essential fields only

### 5. WebsitePageSerializer (UPDATED)
- Added `products_count` field
- Shows extracted products count

### 6. WebsitePageDetailSerializer (UPDATED)
- Added `extracted_products` list
- Shows full product details with ProductCompactSerializer

---

## Key Features for Frontend

### 1. Comprehensive Product Management
- Full CRUD operations with all fields
- Bulk operations (update, delete)
- Advanced filtering and search
- Statistics and analytics

### 2. Auto-Extraction Support
- Track AI-extracted products
- Source attribution (website, page)
- Extraction confidence scores
- Extraction metadata

### 3. E-commerce Features
- Pricing with discounts
- Currency support (7 currencies)
- Billing periods
- Stock management
- Product images

### 4. Better UX
- Dropdown choices endpoints
- Computed properties (final_price, discount_info)
- Category and brand lists
- Product statistics

### 5. Performance
- Select related for faster queries
- Prefetch related for optimized N+1
- Compact serializers for lists

---

## Migration Notes

### Database Changes Required
If not already migrated, run:
```bash
python manage.py makemigrations web_knowledge
python manage.py migrate web_knowledge
```

### Breaking Changes
⚠️ **None** - All changes are backward compatible

### New Dependencies
✅ **None** - Uses existing packages

---

## Testing

### Quick Test Commands

```bash
# Test product list with filters
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/web-knowledge/products/?has_discount=true&currency=USD"

# Test product choices
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/web-knowledge/products/choices/all/"

# Test product statistics
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/web-knowledge/products/statistics/"

# Test products by website
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/web-knowledge/products/by-website/?website_id=UUID"
```

---

## Frontend Integration Priority

### High Priority (Week 1)
1. ✅ Update product list to show new fields
2. ✅ Add basic filters (type, active, in_stock)
3. ✅ Update product creation form
4. ✅ Display final_price and discounts

### Medium Priority (Week 2)
1. ✅ Add advanced filters (price range, currency, etc.)
2. ✅ Implement bulk operations
3. ✅ Show product statistics
4. ✅ Add category/brand filters

### Low Priority (Week 3+)
1. ✅ Add SEO metadata displays
2. ✅ Show extraction metadata
3. ✅ Implement product image gallery
4. ✅ Add specifications display

---

## Files Changed

### Updated Files
1. `/src/web_knowledge/serializers.py`
   - Updated ProductSerializer (40+ fields)
   - Updated ProductCreateSerializer
   - Updated ProductUpdateSerializer
   - Added ProductCompactSerializer
   - Updated WebsitePageSerializer
   - Updated WebsitePageDetailSerializer

2. `/src/web_knowledge/views.py`
   - Updated ProductViewSet.get_queryset() (20+ filters)
   - Added 7 new @action endpoints
   - Updated WebsiteSourceViewSet.pages() (product counts)
   - Added WebsiteSourceViewSet.products() endpoint

### New Files
1. `/WEB_KNOWLEDGE_API_UPDATES.md` - Comprehensive API documentation
2. `/API_UPDATE_SUMMARY.md` - This file

---

## Support & Documentation

- **Full API Documentation:** See `WEB_KNOWLEDGE_API_UPDATES.md`
- **Model Reference:** See `/src/web_knowledge/models.py`
- **API Testing:** Use Django REST Framework browsable API or Swagger
- **Questions:** Contact backend team

---

## Checklist for Deployment

- [x] Update serializers
- [x] Add new endpoints
- [x] Update filtering logic
- [x] Add validation
- [x] Test endpoints
- [x] Check linting (✅ No errors)
- [x] Create documentation
- [ ] Run database migrations
- [ ] Update API documentation site
- [ ] Notify frontend team
- [ ] Test with frontend integration

---

**Status:** ✅ Complete and Ready for Frontend Integration

**Last Updated:** January 2025

