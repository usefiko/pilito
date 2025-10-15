# Web Knowledge API Updates - Frontend Integration Guide

## Overview
This document outlines the comprehensive API updates for WebsiteSource, WebsitePage, and Product models, optimized for better frontend usage.

## Table of Contents
1. [Model Changes](#model-changes)
2. [Product API Endpoints](#product-api-endpoints)
3. [WebsiteSource API Updates](#websitesource-api-updates)
4. [WebsitePage API Updates](#websitepage-api-updates)
5. [Filtering & Search](#filtering--search)
6. [Examples](#examples)

---

## Model Changes

### WebsiteSource
**New Field:**
- `auto_extract_products` (boolean, default: `true`) - Automatically extract products/services from crawled pages using AI

### Product Model - Major Enhancements

#### Basic Information
- `title` - Product/service title
- `product_type` - Type (service, product, software, consultation, course, tool, other)
- `description` - Detailed description
- `short_description` - Brief description for listings (NEW)
- `long_description` - Extended description with full details (NEW)
- `link` - Product page URL

#### Pricing Information (NEW)
- `price` - Current price
- `original_price` - Original price before discount
- `discount_percentage` - Discount percentage (0-100)
- `discount_amount` - Discount amount in currency
- `currency` - Currency code (USD, EUR, TRY, AED, SAR, IRR, IRT)
- `billing_period` - Billing period (one_time, monthly, yearly, weekly, daily)

#### Product Details (NEW)
- `features` - JSON array of key features
- `specifications` - JSON object of technical specifications
- `category` - Product category
- `brand` - Product brand
- `tags` - JSON array of tags
- `keywords` - JSON array of SEO keywords

#### Availability (NEW)
- `is_active` - Product is currently active
- `in_stock` - Product is in stock
- `stock_quantity` - Stock quantity (optional)

#### Media (NEW)
- `main_image` - URL of main product image
- `images` - JSON array of image URLs

#### SEO (NEW)
- `meta_title` - Meta title for SEO
- `meta_description` - Meta description for SEO

#### Auto-Extraction Tracking (NEW)
- `source_website` - Source website (if auto-extracted)
- `source_page` - Source page (if auto-extracted)
- `extraction_method` - How created (manual, ai_auto, ai_assisted)
- `extraction_confidence` - AI extraction confidence (0-1)
- `extraction_metadata` - Extraction metadata (JSON)

#### Computed Properties
- `has_link` - Whether product has a valid link
- `final_price` - Price after discount
- `has_discount` - Whether product has a discount
- `discount_info` - Human-readable discount information
- `is_auto_extracted` - Whether product was auto-extracted

---

## Product API Endpoints

### Base Endpoint: `/api/v1/web-knowledge/products/`

### 1. List Products (GET)
```http
GET /api/v1/web-knowledge/products/
```

**Query Parameters:**
```
product_type: Filter by type (service, product, software, etc.)
is_active: true/false - Filter by active status
in_stock: true/false - Filter by stock status
extraction_method: manual, ai_auto, ai_assisted
website_id: Filter by source website UUID
category: Filter by category (contains search)
brand: Filter by brand (contains search)
currency: Filter by currency code (USD, EUR, etc.)
billing_period: one_time, monthly, yearly, etc.
min_price: Minimum price
max_price: Maximum price
has_discount: true - Filter products with discounts
search: Search in title, description, category, brand
```

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "Product Name",
    "product_type": "service",
    "product_type_display": "Service",
    "description": "Detailed description",
    "short_description": "Brief description",
    "long_description": "Extended description",
    "link": "https://example.com/product",
    "has_link": true,
    "price": "99.99",
    "original_price": "149.99",
    "currency": "USD",
    "currency_display": "US Dollar",
    "final_price": "99.99",
    "discount_percentage": "33.33",
    "discount_amount": null,
    "has_discount": true,
    "discount_info": "33.33% OFF",
    "billing_period": "monthly",
    "billing_period_display": "Monthly",
    "features": ["Feature 1", "Feature 2"],
    "specifications": {"spec1": "value1"},
    "category": "Software",
    "brand": "Brand Name",
    "tags": ["tag1", "tag2"],
    "tags_display": "tag1, tag2",
    "keywords": ["keyword1", "keyword2"],
    "is_active": true,
    "in_stock": true,
    "stock_quantity": 100,
    "main_image": "https://example.com/image.jpg",
    "images": ["https://example.com/img1.jpg"],
    "meta_title": "SEO Title",
    "meta_description": "SEO Description",
    "extraction_method": "ai_auto",
    "extraction_confidence": 0.95,
    "extraction_metadata": {"model": "gemini"},
    "is_auto_extracted": true,
    "source_website": "uuid",
    "source_website_name": "Website Name",
    "source_page": "uuid",
    "source_page_url": "https://example.com/page",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

### 2. Create Product (POST)
```http
POST /api/v1/web-knowledge/products/
```

**Request Body (Required fields: `title`, `product_type`, `description`):**
```json
{
  "title": "Product Name",
  "product_type": "service",
  "description": "Description",
  "short_description": "Brief",
  "price": "99.99",
  "original_price": "149.99",
  "currency": "USD",
  "discount_percentage": "33.33",
  "billing_period": "monthly",
  "features": ["Feature 1", "Feature 2"],
  "category": "Software",
  "brand": "Brand Name",
  "tags": ["tag1", "tag2"],
  "is_active": true,
  "in_stock": true,
  "stock_quantity": 100,
  "main_image": "https://example.com/image.jpg",
  "images": ["https://example.com/img1.jpg"]
}
```

### 3. Update Product (PUT/PATCH)
```http
PATCH /api/v1/web-knowledge/products/{id}/
```

**Request Body (All fields optional for PATCH):**
```json
{
  "title": "Updated Title",
  "price": "79.99",
  "in_stock": false
}
```

### 4. Delete Product (DELETE)
```http
DELETE /api/v1/web-knowledge/products/{id}/
```

### 5. Get Product Choices (NEW)

#### Get All Choices
```http
GET /api/v1/web-knowledge/products/choices/all/
```
**Response:**
```json
{
  "product_types": [
    {"value": "service", "label": "Service"},
    {"value": "product", "label": "Product"}
  ],
  "currencies": [
    {"value": "USD", "label": "US Dollar"},
    {"value": "EUR", "label": "Euro"}
  ],
  "billing_periods": [
    {"value": "one_time", "label": "One-time Purchase"},
    {"value": "monthly", "label": "Monthly"}
  ],
  "extraction_methods": [
    {"value": "manual", "label": "Manual Entry"},
    {"value": "ai_auto", "label": "AI Auto-extracted"}
  ]
}
```

#### Individual Choice Endpoints
```http
GET /api/v1/web-knowledge/products/choices/product-types/
GET /api/v1/web-knowledge/products/choices/currencies/
GET /api/v1/web-knowledge/products/choices/billing-periods/
GET /api/v1/web-knowledge/products/choices/extraction-methods/
```

### 6. Get Product Statistics (NEW)
```http
GET /api/v1/web-knowledge/products/statistics/
```

**Response:**
```json
{
  "total_products": 150,
  "active_products": 145,
  "in_stock_products": 130,
  "by_type": [
    {"product_type": "service", "count": 80},
    {"product_type": "product", "count": 70}
  ],
  "by_extraction_method": [
    {"extraction_method": "ai_auto", "count": 100},
    {"extraction_method": "manual", "count": 50}
  ],
  "by_currency": [
    {"currency": "USD", "count": 120},
    {"currency": "EUR", "count": 30}
  ],
  "with_links": 140,
  "with_prices": 145,
  "with_discounts": 50,
  "auto_extracted": 100,
  "manual": 50,
  "recent_products": [...]
}
```

### 7. Get Products by Website (NEW)
```http
GET /api/v1/web-knowledge/products/by-website/?website_id={uuid}
```

**Response:**
```json
{
  "website_id": "uuid",
  "website_name": "Website Name",
  "website_url": "https://example.com",
  "total_products": 50,
  "products": [...]
}
```

### 8. Get Categories & Brands (NEW)
```http
GET /api/v1/web-knowledge/products/categories/
GET /api/v1/web-knowledge/products/brands/
```

**Response:**
```json
{
  "categories": ["Software", "Hardware", "Services"]
}
```

### 9. Bulk Operations (NEW)

#### Bulk Update
```http
POST /api/v1/web-knowledge/products/bulk-update/
```

**Request Body:**
```json
{
  "product_ids": ["uuid1", "uuid2"],
  "is_active": false,
  "in_stock": false
}
```

#### Bulk Delete
```http
POST /api/v1/web-knowledge/products/bulk-delete/
```

**Request Body:**
```json
{
  "product_ids": ["uuid1", "uuid2"]
}
```

---

## WebsiteSource API Updates

### Base Endpoint: `/api/v1/web-knowledge/websites/`

### Get Products from Website (NEW)
```http
GET /api/v1/web-knowledge/websites/{id}/products/
```

**Response:**
```json
{
  "website_id": "uuid",
  "website_name": "Website Name",
  "website_url": "https://example.com",
  "total_products": 50,
  "active_products": 45,
  "in_stock_products": 40,
  "products": [...]
}
```

### Get Pages with Product Info (UPDATED)
```http
GET /api/v1/web-knowledge/websites/{id}/pages/
```

**Response (now includes product counts):**
```json
{
  "website_id": "uuid",
  "pages": [
    {
      "id": "uuid",
      "title": "Page Title",
      "qa_pairs": {
        "total": 10,
        "average_confidence": 0.85
      },
      "products": {
        "total": 5,
        "in_stock": 4
      }
    }
  ],
  "summary": {
    "total_pages": 20,
    "total_qa_pairs": 100,
    "total_products": 50,
    "pages_with_products": 10
  }
}
```

---

## WebsitePage API Updates

### Base Endpoint: `/api/v1/web-knowledge/pages/`

### Get Page Details (UPDATED)
```http
GET /api/v1/web-knowledge/pages/{id}/
```

**Response (now includes extracted products):**
```json
{
  "id": "uuid",
  "title": "Page Title",
  "url": "https://example.com/page",
  "qa_pairs_count": 10,
  "products_count": 5,
  "qa_pairs": [...],
  "extracted_products": [
    {
      "id": "uuid",
      "title": "Product Name",
      "product_type": "service",
      "description": "Description",
      "price": "99.99",
      "final_price": "99.99",
      "currency": "USD",
      "main_image": "https://example.com/image.jpg",
      "is_active": true,
      "in_stock": true,
      "extraction_method": "ai_auto"
    }
  ]
}
```

---

## Filtering & Search

### Advanced Product Filtering Examples

#### Filter by Price Range
```http
GET /api/v1/web-knowledge/products/?min_price=50&max_price=200
```

#### Filter by Multiple Criteria
```http
GET /api/v1/web-knowledge/products/?product_type=service&currency=USD&is_active=true&in_stock=true
```

#### Search Products
```http
GET /api/v1/web-knowledge/products/?search=software
```
Searches in: title, description, short_description, category, brand

#### Filter by Discounts
```http
GET /api/v1/web-knowledge/products/?has_discount=true
```

#### Filter by Auto-Extraction
```http
GET /api/v1/web-knowledge/products/?extraction_method=ai_auto
```

#### Filter by Website Source
```http
GET /api/v1/web-knowledge/products/?website_id={uuid}
```

---

## Examples

### Example 1: Get All AI-Extracted Products with Discounts
```javascript
fetch('/api/v1/web-knowledge/products/?extraction_method=ai_auto&has_discount=true', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
  .then(res => res.json())
  .then(products => {
    products.forEach(product => {
      console.log(`${product.title}: ${product.discount_info} - Final Price: ${product.final_price} ${product.currency}`);
    });
  });
```

### Example 2: Create a New Product
```javascript
fetch('/api/v1/web-knowledge/products/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: "Premium Service",
    product_type: "service",
    description: "Comprehensive service offering",
    price: "99.99",
    original_price: "149.99",
    currency: "USD",
    discount_percentage: "33.33",
    billing_period: "monthly",
    features: ["24/7 Support", "Premium Features"],
    category: "Software",
    is_active: true,
    in_stock: true
  })
})
  .then(res => res.json())
  .then(data => {
    console.log('Product created:', data.product);
  });
```

### Example 3: Get All Products from a Website
```javascript
const websiteId = 'your-website-uuid';

fetch(`/api/v1/web-knowledge/websites/${websiteId}/products/`, {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
  .then(res => res.json())
  .then(data => {
    console.log(`Found ${data.total_products} products from ${data.website_name}`);
    data.products.forEach(product => {
      console.log(`- ${product.title} (${product.product_type})`);
    });
  });
```

### Example 4: Get All Choices for Dropdowns
```javascript
fetch('/api/v1/web-knowledge/products/choices/all/', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
  .then(res => res.json())
  .then(choices => {
    // Populate dropdowns
    populateDropdown('product-type-select', choices.product_types);
    populateDropdown('currency-select', choices.currencies);
    populateDropdown('billing-period-select', choices.billing_periods);
  });
```

### Example 5: Bulk Update Products
```javascript
fetch('/api/v1/web-knowledge/products/bulk-update/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    product_ids: ['uuid1', 'uuid2', 'uuid3'],
    is_active: false,
    in_stock: false
  })
})
  .then(res => res.json())
  .then(data => {
    console.log(`Updated ${data.updated_count} products`);
  });
```

### Example 6: Get Product Statistics
```javascript
fetch('/api/v1/web-knowledge/products/statistics/', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
  .then(res => res.json())
  .then(stats => {
    console.log(`Total: ${stats.total_products}`);
    console.log(`Active: ${stats.active_products}`);
    console.log(`With Discounts: ${stats.with_discounts}`);
    console.log(`Auto-extracted: ${stats.auto_extracted}`);
  });
```

---

## Response Formats

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "product": {...},
  "id": "uuid"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "errors": {
    "field_name": ["Error detail"]
  }
}
```

---

## Notes for Frontend Developers

1. **All product endpoints require authentication** - Include `Authorization: Bearer YOUR_TOKEN` in headers

2. **UUIDs are used for all IDs** - Always use string format for IDs

3. **Date fields are in ISO 8601 format** - Use Date parsing libraries

4. **JSON fields** (`features`, `specifications`, `tags`, `keywords`, `images`) should be arrays/objects

5. **Computed properties are read-only** - `final_price`, `has_discount`, `discount_info`, `is_auto_extracted`

6. **Price validation** - Prices must be non-negative decimal values

7. **Discount validation** - Discount percentage must be between 0-100

8. **Filtering is case-insensitive** - Search and filter queries use `icontains`

9. **Pagination** - Use standard DRF pagination parameters (`page`, `page_size`)

10. **Auto-extraction fields** - These are automatically populated by the AI system when products are extracted from websites

---

## Frontend Integration Checklist

- [ ] Update product list component to display new fields
- [ ] Add filters for: type, currency, price range, discount, stock status
- [ ] Implement product creation form with all new fields
- [ ] Add product editing with comprehensive field support
- [ ] Display computed properties: `final_price`, `discount_info`
- [ ] Show auto-extraction metadata when available
- [ ] Add bulk operations UI (update, delete)
- [ ] Display product statistics dashboard
- [ ] Show products grouped by website source
- [ ] Implement category and brand filters
- [ ] Add product image gallery support
- [ ] Display SEO metadata in appropriate sections

---

## Support

For issues or questions about the API, contact the backend team or refer to the Django REST Framework documentation.

**Last Updated:** January 2025
**API Version:** 1.0

