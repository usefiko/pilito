# 🎨 Frontend API Documentation - محصولات WooCommerce

این داکیومنت شامل تمام API های مورد نیاز فرانت برای نمایش محصولات است.

---

## 📋 فهرست

1. [لیست محصولات](#لیست-محصولات)
2. [جزئیات محصول](#جزئیات-محصول)
3. [فیلترها](#فیلترها)
4. [جستجو](#جستجو)
5. [آمار محصولات](#آمار-محصولات)

---

## 🔐 Authentication

همه endpoint ها نیاز به authentication دارند:

```http
Authorization: Bearer {access_token}
```

---

## 📦 لیست محصولات

### Endpoint
```http
GET /api/v1/web-knowledge/products/
```

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `page` | integer | شماره صفحه | `1` |
| `page_size` | integer | تعداد در هر صفحه (max: 100) | `20` |
| `search` | string | جستجو در عنوان، توضیحات، دسته، برند | `کفش` |
| `external_source` | string | فیلتر بر اساس منبع | `woocommerce`, `shopify`, `manual` |
| `product_type` | string | نوع محصول | `product`, `service`, `software` |
| `category` | string | دسته‌بندی | `کفش` |
| `brand` | string | برند | `Nike` |
| `is_active` | boolean | فقط محصولات فعال | `true` |
| `in_stock` | boolean | فقط محصولات موجود | `true` |
| `has_discount` | boolean | فقط محصولات با تخفیف | `true` |
| `min_price` | number | حداقل قیمت | `100000` |
| `max_price` | number | حداکثر قیمت | `500000` |
| `currency` | string | واحد پول | `IRT`, `USD` |
| `ordering` | string | مرتب‌سازی | `-created_at`, `price`, `-price` |

### Response Example

```json
{
    "count": 150,
    "next": "https://api.fiko.ai/api/v1/web-knowledge/products/?page=2",
    "previous": null,
    "results": [
        {
            "id": "uuid-here",
            "title": "کفش اسپرت مردانه نایک",
            "product_type": "product",
            "product_type_display": "Product",
            "short_description": "کفش ورزشی سبک و راحت",
            "description": "این کفش با زیره نرم و طراحی مدرن...",
            "link": "https://myshop.com/products/nike-shoe",
            "has_link": true,
            
            // قیمت‌گذاری
            "price": "950000.00",
            "original_price": "950000.00",
            "sale_price": "850000.00",
            "final_price": "850000.00",
            "currency": "IRT",
            "currency_display": "Iranian Toman",
            "has_discount": true,
            "discount_percentage": null,
            "discount_amount": "100000.00",
            "discount_info": "-100000.0 IRT",
            
            // جزئیات
            "category": "کفش، مردانه",
            "brand": "Nike",
            "tags": ["ورزشی", "تابستانی", "سبک"],
            "tags_display": "ورزشی, تابستانی, سبک",
            "features": [
                "زیره نرم و انعطاف‌پذیر",
                "طراحی ergonomic",
                "قابل شستشو"
            ],
            "specifications": {
                "وزن": "350 گرم",
                "جنس رویه": "Mesh",
                "جنس زیره": "EVA"
            },
            
            // موجودی
            "is_active": true,
            "in_stock": true,
            "stock_quantity": 12,
            
            // تصاویر
            "main_image": "https://cdn.myshop.com/products/nike-1.jpg",
            "images": [
                "https://cdn.myshop.com/products/nike-1.jpg",
                "https://cdn.myshop.com/products/nike-2.jpg",
                "https://cdn.myshop.com/products/nike-3.jpg"
            ],
            
            // منبع (WooCommerce)
            "external_id": "woo_414",
            "external_source": "woocommerce",
            "extraction_method": "manual",
            "is_auto_extracted": false,
            
            // تاریخ
            "created_at": "2025-11-10T10:30:00Z",
            "updated_at": "2025-11-10T15:45:00Z"
        }
    ]
}
```

---

## 🔍 جزئیات محصول

### Endpoint
```http
GET /api/v1/web-knowledge/products/{id}/
```

### Response Example

```json
{
    "id": "uuid-here",
    "title": "کفش اسپرت مردانه نایک",
    "product_type": "product",
    "product_type_display": "Product",
    
    // توضیحات کامل
    "short_description": "کفش ورزشی سبک و راحت",
    "description": "این کفش با زیره نرم و طراحی مدرن مناسب برای ورزش روزانه است...",
    "long_description": "توضیحات تکمیلی...",
    
    "link": "https://myshop.com/products/nike-shoe",
    "has_link": true,
    
    // قیمت‌گذاری کامل
    "price": "950000.00",
    "original_price": "950000.00",
    "final_price": "850000.00",
    "currency": "IRT",
    "currency_display": "Iranian Toman",
    "has_discount": true,
    "discount_percentage": null,
    "discount_amount": "100000.00",
    "discount_info": "-100000.0 IRT",
    "billing_period": null,
    "billing_period_display": null,
    
    // دسته‌بندی
    "category": "کفش، مردانه",
    "brand": "Nike",
    "tags": ["ورزشی", "تابستانی", "سبک"],
    "keywords": ["کفش", "nike", "ورزشی", "مردانه"],
    
    // ویژگی‌ها
    "features": [
        "زیره نرم و انعطاف‌پذیر",
        "طراحی ergonomic",
        "قابل شستشو",
        "مقاوم در برابر آب"
    ],
    
    // مشخصات فنی
    "specifications": {
        "وزن": "350 گرم",
        "جنس رویه": "Mesh",
        "جنس زیره": "EVA",
        "رنگ": "مشکی",
        "سایزها": "39-44"
    },
    
    // موجودی
    "is_active": true,
    "in_stock": true,
    "stock_quantity": 12,
    
    // رسانه
    "image": null,  // آپلود مستقیم
    "main_image": "https://cdn.myshop.com/products/nike-1.jpg",
    "images": [
        "https://cdn.myshop.com/products/nike-1.jpg",
        "https://cdn.myshop.com/products/nike-2.jpg",
        "https://cdn.myshop.com/products/nike-3.jpg",
        "https://cdn.myshop.com/products/nike-4.jpg"
    ],
    
    // SEO
    "meta_title": "کفش اسپرت مردانه نایک - خرید آنلاین",
    "meta_description": "کفش ورزشی سبک و راحت نایک با تخفیف ویژه...",
    
    // منبع WooCommerce
    "external_id": "woo_414",
    "external_source": "woocommerce",
    "extraction_method": "manual",
    "extraction_confidence": 1.0,
    "extraction_metadata": {
        "woo_product_id": 414,
        "sku": "NIKE-SPORT-001",
        "content_hash": "abc123...",
        "last_sync_at": "2025-11-10T15:45:00Z"
    },
    "is_auto_extracted": false,
    
    // تاریخ‌ها
    "created_at": "2025-11-10T10:30:00Z",
    "updated_at": "2025-11-10T15:45:00Z"
}
```

---

## 🎯 مثال‌های استفاده

### 1. فقط محصولات WooCommerce

```http
GET /api/v1/web-knowledge/products/?external_source=woocommerce
```

### 2. محصولات با تخفیف

```http
GET /api/v1/web-knowledge/products/?has_discount=true&external_source=woocommerce
```

### 3. جستجو در محصولات

```http
GET /api/v1/web-knowledge/products/?search=کفش&external_source=woocommerce
```

### 4. فیلتر بر اساس دسته و برند

```http
GET /api/v1/web-knowledge/products/?category=کفش&brand=Nike&external_source=woocommerce
```

### 5. فیلتر قیمت

```http
GET /api/v1/web-knowledge/products/?min_price=500000&max_price=1000000&currency=IRT
```

### 6. فقط محصولات موجود

```http
GET /api/v1/web-knowledge/products/?is_active=true&in_stock=true&external_source=woocommerce
```

### 7. مرتب‌سازی بر اساس قیمت (ارزان‌ترین)

```http
GET /api/v1/web-knowledge/products/?ordering=price&external_source=woocommerce
```

### 8. مرتب‌سازی بر اساس جدیدترین

```http
GET /api/v1/web-knowledge/products/?ordering=-created_at
```

---

## 📊 آمار محصولات

### Endpoint (پیشنهادی - باید پیاده شود)

```http
GET /api/v1/web-knowledge/products/stats/
```

### Response Example

```json
{
    "total_products": 150,
    "active_products": 142,
    "inactive_products": 8,
    "in_stock_products": 135,
    "out_of_stock_products": 15,
    "products_with_discount": 23,
    "by_source": {
        "woocommerce": 120,
        "shopify": 15,
        "manual": 15
    },
    "by_category": {
        "کفش": 45,
        "لباس": 38,
        "لوازم الکترونیکی": 30,
        "سایر": 37
    },
    "price_range": {
        "min": "50000.00",
        "max": "5000000.00",
        "average": "850000.00"
    },
    "total_value": "127500000.00",  // مجموع قیمت همه محصولات
    "currency": "IRT"
}
```

---

## 🛒 Catalog عمومی (اختیاری)

برای نمایش catalog عمومی بدون authentication:

### Endpoint
```http
GET /api/v1/catalog/products/
```

این endpoint نیاز به authentication ندارد و فقط محصولات فعال (`is_active=true`) را نمایش می‌دهد.

**نکته:** باید در تنظیمات کاربر، گزینه "نمایش عمومی کاتالوگ" فعال شده باشد.

---

## 🎨 Component های پیشنهادی React

### ProductCard

```jsx
<ProductCard
  title="کفش اسپرت مردانه نایک"
  image="https://..."
  price="950000"
  salePrice="850000"
  currency="IRT"
  hasDiscount={true}
  discountInfo="-100000 IRT"
  inStock={true}
  stockQuantity={12}
  brand="Nike"
  category="کفش"
  link="https://..."
/>
```

### ProductList

```jsx
<ProductList
  filters={{
    external_source: 'woocommerce',
    category: 'کفش',
    min_price: 500000,
    max_price: 1000000,
    has_discount: true
  }}
  sorting="price"
  pageSize={20}
/>
```

### ProductFilter

```jsx
<ProductFilter
  categories={['کفش', 'لباس', 'الکترونیک']}
  brands={['Nike', 'Adidas', 'Puma']}
  priceRange={{ min: 0, max: 5000000 }}
  onFilterChange={handleFilterChange}
/>
```

---

## 🔄 Real-time Updates

برای نمایش محصولات به‌روز، می‌توانید:

1. **Polling** - هر 30 ثانیه refresh
2. **WebSocket** - اتصال real-time (پیچیده‌تر)
3. **Cache Strategy** - استفاده از SWR یا React Query

```javascript
// با SWR
import useSWR from 'swr'

function Products() {
  const { data, error } = useSWR(
    '/api/v1/web-knowledge/products/?external_source=woocommerce',
    fetcher,
    { refreshInterval: 30000 } // refresh every 30s
  )
  
  // ...
}
```

---

## 📝 نکات مهم

### 1. Pagination
همیشه از pagination استفاده کنید. حداکثر `page_size=100`

### 2. Caching
محصولات را cache کنید (حداقل 5 دقیقه)

### 3. Image Optimization
تصاویر را lazy load کنید

### 4. Error Handling
```javascript
if (error) return <ErrorMessage />
if (!data) return <LoadingSkeleton />
```

### 5. Currency Formatting
از کتابخانه‌های formatting استفاده کنید:

```javascript
new Intl.NumberFormat('fa-IR', {
  style: 'currency',
  currency: 'IRR'
}).format(850000)
// "۸۵۰٬۰۰۰ ریال"
```

---

## 🚀 تغییرات مورد نیاز در Backend

برای پشتیبانی کامل از WooCommerce، این تغییرات لازمه:

### 1. اضافه کردن فیلدها به Product Model
```python
external_id = models.CharField(max_length=100, blank=True, null=True)
external_source = models.CharField(
    max_length=20,
    choices=[('woocommerce', 'WooCommerce'), ('shopify', 'Shopify'), ('manual', 'Manual')],
    default='manual'
)
```

### 2. اضافه کردن فیلتر external_source به ProductViewSet
```python
# در get_queryset()
external_source = self.request.query_params.get('external_source', None)
if external_source:
    queryset = queryset.filter(external_source=external_source)
```

### 3. اضافه کردن Stats Endpoint
```python
@action(detail=False, methods=['get'])
def stats(self, request):
    # محاسبه آمار
    return Response({...})
```

### 4. اضافه کردن فیلدها به Serializer
```python
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [..., 'external_id', 'external_source']
```

---

**نسخه:** 1.0  
**تاریخ:** 2025-11-10  
**مخاطب:** Frontend Developers

