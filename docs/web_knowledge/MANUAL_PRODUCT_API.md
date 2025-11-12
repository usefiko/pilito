# API مستندات: اضافه کردن دستی Product

## 📋 خلاصه

این API برای اضافه کردن دستی محصولات استفاده می‌شود (غیر از WordPress plugin که خودکار sync می‌شه).

**⚠️ مهم:** 
- برای **اضافه کردن دستی**: از `sale_price` و `original_price` استفاده کنید، `price` را خالی بگذارید
- برای **AI extraction**: سیستم خودش `price` را پر می‌کند
- برای **image upload**: باید از `multipart/form-data` استفاده کنید

---

## 🔌 API Endpoints

### 1. اضافه کردن Product جدید (Manual Entry)

**Endpoint:** `POST /api/v1/web-knowledge/products/`

**Content-Type:** `multipart/form-data` (برای image upload) یا `application/json`

**Authentication:** Required (Bearer Token)

**دستور curl (با image):**
```bash
curl -X POST "https://api.pilito.com/api/v1/web-knowledge/products/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "title=کفش اسپرت مردانه نایک" \
  -F "product_type=product" \
  -F "description=کفش ورزشی سبک و راحت با زیره نرم" \
  -F "original_price=950000" \
  -F "sale_price=850000" \
  -F "currency=IRT" \
  -F "link=https://myshop.com/products/nike-shoe" \
  -F "image=@/path/to/image.jpg"
```

**دستور curl (بدون image):**
```bash
curl -X POST "https://api.pilito.com/api/v1/web-knowledge/products/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "کفش اسپرت مردانه نایک",
    "product_type": "product",
    "description": "کفش ورزشی سبک و راحت با زیره نرم",
    "original_price": "950000.00",
    "sale_price": "850000.00",
    "currency": "IRT",
    "link": "https://myshop.com/products/nike-shoe"
  }'
```

**Request Body (JSON):**
```json
{
  "title": "کفش اسپرت مردانه نایک",
  "product_type": "product",
  "description": "کفش ورزشی سبک و راحت با زیره نرم و طراحی مدرن",
  "original_price": "950000.00",
  "sale_price": "850000.00",
  "currency": "IRT",
  "link": "https://myshop.com/products/nike-shoe",
  "image": null  // برای file upload از multipart/form-data استفاده کنید
}
```

**Request Body (Form Data - برای image upload):**
```
title: کفش اسپرت مردانه نایک
product_type: product
description: کفش ورزشی سبک و راحت با زیره نرم
original_price: 950000.00
sale_price: 850000.00
currency: IRT
link: https://myshop.com/products/nike-shoe
image: [FILE]
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Product created successfully",
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "product": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "کفش اسپرت مردانه نایک",
    "product_type": "product",
    "product_type_display": "Product",
    "description": "کفش ورزشی سبک و راحت با زیره نرم و طراحی مدرن",
    "link": "https://myshop.com/products/nike-shoe",
    "has_link": true,
    
    // قیمت‌گذاری
    "price": null,  // ✅ برای manual entry خالی است
    "sale_price": "850000.00",  // ✅ Sale price
    "original_price": "950000.00",  // ✅ Original price
    "final_price": "850000.00",  // ✅ محاسبه شده از sale_price
    "currency": "IRT",
    "currency_display": "Iranian Toman",
    "has_discount": true,
    "discount_info": "-100000.0 IRT",
    
    // تصاویر
    "image": "https://api.pilito.com/media/products/images/nike-shoe.jpg",  // ✅ اگر آپلود شده باشد
    "main_image": null,
    "images": [],
    
    // سایر فیلدها
    "is_active": true,
    "in_stock": true,
    "extraction_method": "manual",
    "is_auto_extracted": false,
    "created_at": "2025-11-11T10:30:00Z",
    "updated_at": "2025-11-11T10:30:00Z"
  }
}
```

---

## 📊 فیلدهای Request

### فیلدهای اجباری

| فیلد | نوع | توضیح |
|------|-----|-------|
| `title` | String | عنوان محصول (حداقل 3 کاراکتر) |
| `product_type` | String | نوع محصول: `product`, `service`, `software`, `consultation`, `course`, `tool`, `other` |
| `description` | String | توضیحات کامل (حداقل 10 کاراکتر) |

### فیلدهای قیمت‌گذاری (برای Manual Entry)

| فیلد | نوع | توضیح | مثال |
|------|-----|-------|------|
| `sale_price` | Decimal | **قیمت فروش (نهایی)** - برای manual entry | `850000.00` |
| `original_price` | Decimal | قیمت اصلی (قبل از تخفیف) | `950000.00` |
| `price` | Decimal | **خالی بگذارید** - فقط برای AI extraction استفاده می‌شود | `null` |
| `currency` | String | واحد پول: `USD`, `EUR`, `TRY`, `AED`, `SAR`, `IRR`, `IRT` | `IRT` |

**⚠️ مهم:** 
- برای **manual entry**: `sale_price` و `original_price` را پر کنید، `price` را خالی بگذارید
- برای **AI extraction**: سیستم خودش `price` را پر می‌کند

### فیلدهای اختیاری

| فیلد | نوع | توضیح |
|------|-----|-------|
| `link` | URL | لینک محصول در سایت |
| `image` | File | تصویر محصول (فقط با `multipart/form-data`) |
| `short_description` | String | توضیحات کوتاه |
| `long_description` | Text | توضیحات کامل |
| `category` | String | دسته‌بندی |
| `brand` | String | برند |
| `tags` | Array | تگ‌ها |
| `features` | Array | ویژگی‌ها |
| `is_active` | Boolean | فعال/غیرفعال (پیش‌فرض: `true`) |
| `in_stock` | Boolean | موجود/ناموجود (پیش‌فرض: `true`) |
| `stock_quantity` | Integer | تعداد موجودی |

---

## 🖼️ Image Upload

### روش 1: با multipart/form-data (توصیه می‌شود)

```javascript
const formData = new FormData();
formData.append('title', 'کفش اسپرت');
formData.append('product_type', 'product');
formData.append('description', 'توضیحات محصول');
formData.append('sale_price', '850000');
formData.append('original_price', '950000');
formData.append('currency', 'IRT');
formData.append('image', fileInput.files[0]);  // File object

const response = await fetch('/api/v1/web-knowledge/products/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
    // ❌ Content-Type را تنظیم نکنید! مرورگر خودش تنظیم می‌کند
  },
  body: formData
});
```

### روش 2: بدون image (JSON)

```javascript
const response = await fetch('/api/v1/web-knowledge/products/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'کفش اسپرت',
    product_type: 'product',
    description: 'توضیحات محصول',
    sale_price: '850000',
    original_price: '950000',
    currency: 'IRT'
  })
});
```

---

## 🎨 مثال React/TypeScript

### Component کامل برای Add Product

```tsx
import React, { useState } from 'react';

interface ProductFormData {
  title: string;
  product_type: string;
  description: string;
  original_price: string;
  sale_price: string;
  currency: string;
  link?: string;
  image?: File;
}

const AddProductForm: React.FC = () => {
  const [formData, setFormData] = useState<ProductFormData>({
    title: '',
    product_type: 'product',
    description: '',
    original_price: '',
    sale_price: '',
    currency: 'IRT',
    link: ''
  });
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const formDataToSend = new FormData();

      // اضافه کردن فیلدهای متنی
      formDataToSend.append('title', formData.title);
      formDataToSend.append('product_type', formData.product_type);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('original_price', formData.original_price);
      formDataToSend.append('sale_price', formData.sale_price);
      formDataToSend.append('currency', formData.currency);
      
      if (formData.link) {
        formDataToSend.append('link', formData.link);
      }

      // اضافه کردن تصویر (اگر انتخاب شده باشد)
      if (imageFile) {
        formDataToSend.append('image', imageFile);
      }

      const response = await fetch('/api/v1/web-knowledge/products/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
          // ❌ Content-Type را تنظیم نکنید!
        },
        body: formDataToSend
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.errors || result.message || 'خطا در ایجاد محصول');
      }

      if (result.success) {
        alert('محصول با موفقیت ایجاد شد!');
        // Reset form
        setFormData({
          title: '',
          product_type: 'product',
          description: '',
          original_price: '',
          sale_price: '',
          currency: 'IRT',
          link: ''
        });
        setImageFile(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در ایجاد محصول');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="product-form">
      {error && <div className="error-message">{error}</div>}

      {/* Title */}
      <div className="form-group">
        <label>Title *</label>
        <input
          type="text"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          required
          minLength={3}
        />
      </div>

      {/* Type */}
      <div className="form-group">
        <label>Type *</label>
        <select
          value={formData.product_type}
          onChange={(e) => setFormData({ ...formData, product_type: e.target.value })}
          required
        >
          <option value="product">Product</option>
          <option value="service">Service</option>
          <option value="software">Software</option>
          <option value="consultation">Consultation</option>
          <option value="course">Course</option>
          <option value="tool">Tool</option>
          <option value="other">Other</option>
        </select>
      </div>

      {/* Original Price */}
      <div className="form-group">
        <label>Original Price *</label>
        <input
          type="number"
          step="0.01"
          value={formData.original_price}
          onChange={(e) => setFormData({ ...formData, original_price: e.target.value })}
          required
          min="0"
        />
      </div>

      {/* Sale Price */}
      <div className="form-group">
        <label>Sale Price *</label>
        <input
          type="number"
          step="0.01"
          value={formData.sale_price}
          onChange={(e) => setFormData({ ...formData, sale_price: e.target.value })}
          required
          min="0"
        />
      </div>

      {/* Currency */}
      <div className="form-group">
        <label>Currency *</label>
        <select
          value={formData.currency}
          onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
          required
        >
          <option value="USD">USD</option>
          <option value="EUR">EUR</option>
          <option value="TRY">TRY</option>
          <option value="AED">AED</option>
          <option value="SAR">SAR</option>
          <option value="IRR">IRR</option>
          <option value="IRT">IRT</option>
        </select>
      </div>

      {/* Description */}
      <div className="form-group">
        <label>Description *</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          required
          minLength={10}
          rows={5}
        />
      </div>

      {/* Product Link */}
      <div className="form-group">
        <label>Product Link on the Site</label>
        <input
          type="url"
          value={formData.link}
          onChange={(e) => setFormData({ ...formData, link: e.target.value })}
          placeholder="https://..."
        />
      </div>

      {/* Image Upload */}
      <div className="form-group">
        <label>Image Product</label>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              setImageFile(file);
            }
          }}
        />
        {imageFile && (
          <div className="image-preview">
            <img src={URL.createObjectURL(imageFile)} alt="Preview" />
            <button type="button" onClick={() => setImageFile(null)}>Remove</button>
          </div>
        )}
      </div>

      {/* Buttons */}
      <div className="form-actions">
        <button type="button" className="btn-discard">Discard</button>
        <button type="submit" className="btn-save" disabled={loading}>
          {loading ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
};

export default AddProductForm;
```

---

## 🔄 Update Product

**Endpoint:** `PUT /api/v1/web-knowledge/products/{id}/` یا `PATCH /api/v1/web-knowledge/products/{id}/`

**مثال:**
```bash
curl -X PATCH "https://api.pilito.com/api/v1/web-knowledge/products/{id}/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sale_price": "800000.00",
    "original_price": "950000.00"
  }'
```

---

## ⚠️ نکات مهم

### 1. Price Fields

- **برای Manual Entry:**
  - ✅ `sale_price`: قیمت فروش نهایی
  - ✅ `original_price`: قیمت اصلی
  - ❌ `price`: خالی بگذارید (برای AI extraction استفاده می‌شود)

- **برای AI Extraction:**
  - ✅ `price`: سیستم خودش پر می‌کند
  - ❌ `sale_price`: استفاده نمی‌شود

### 2. Image Upload

- برای آپلود تصویر، **حتماً** از `multipart/form-data` استفاده کنید
- `Content-Type` را تنظیم نکنید (مرورگر خودش تنظیم می‌کند)
- فرمت‌های مجاز: `jpg`, `jpeg`, `png`, `gif`, `webp`
- حداکثر اندازه: طبق تنظیمات Django (معمولاً 10MB)

### 3. Validation

- `title`: حداقل 3 کاراکتر
- `description`: حداقل 10 کاراکتر
- `sale_price` و `original_price`: باید عدد مثبت باشند
- `link`: باید با `http://` یا `https://` شروع شود

---

## 📝 Response Fields

### فیلدهای قیمت در Response

```json
{
  "price": null,  // برای manual entry همیشه null است
  "sale_price": "850000.00",  // قیمت فروش
  "original_price": "950000.00",  // قیمت اصلی
  "final_price": "850000.00",  // محاسبه شده (از sale_price یا price)
  "has_discount": true,  // آیا تخفیف دارد؟
  "discount_info": "-100000.0 IRT"  // اطلاعات تخفیف
}
```

### فیلدهای Image در Response

```json
{
  "image": "https://api.pilito.com/media/products/images/abc123.jpg",  // اگر آپلود شده باشد
  "main_image": null,  // URL تصویر اصلی (از external source)
  "images": []  // لیست تصاویر اضافی
}
```

---

## 🔗 لینک‌های مرتبط

- [WooCommerce Frontend API](./../wordpress/WOOCOMMERCE_FRONTEND_API.md) - برای محصولات sync شده از WordPress
- [Manual Page Crawl API](./MANUAL_PAGE_CRAWL_API.md) - برای کرال دستی صفحات

---

**نسخه:** 1.0  
**تاریخ:** 2025-11-11  
**مخاطب:** Frontend Developers

