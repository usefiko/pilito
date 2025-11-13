# API مستندات: Bulk Delete

## 📋 خلاصه

این API برای حذف چندتایی (bulk delete) آیتم‌های مختلف استفاده می‌شود:
- **Pages** (صفحات وب‌سایت)
- **Products** (محصولات)
- **Q&A Pairs** (سوال و جواب‌ها)

**⚠️ نکته مهم:** وقتی آیتم‌ها پاک می‌شن، chunks مربوطه هم به صورت خودکار از TenantKnowledge پاک می‌شن (via `pre_delete` signal).

---

## 🔌 API Endpoints

### 1. Bulk Delete Pages (Website Knowledge)

**Endpoint:** `POST /api/v1/web-knowledge/pages/bulk-delete/`

**Authentication:** Required (Bearer Token)

**Request Body:**
```json
{
  "page_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174001",
    "789e0123-e89b-12d3-a456-426614174002"
  ]
}
```

**دستور curl:**
```bash
curl -X POST "https://api.pilito.com/api/v1/web-knowledge/pages/bulk-delete/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page_ids": [
      "123e4567-e89b-12d3-a456-426614174000",
      "456e7890-e89b-12d3-a456-426614174001"
    ]
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "3 page(s) and 15 Q&A pair(s) deleted successfully",
  "deleted_count": 3,
  "qa_pairs_deleted": 15,
  "deleted_pages": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Page Title 1",
      "url": "https://example.com/page1",
      "qa_pairs_count": 5
    },
    {
      "id": "456e7890-e89b-12d3-a456-426614174001",
      "title": "Page Title 2",
      "url": "https://example.com/page2",
      "qa_pairs_count": 10
    }
  ]
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "success": false,
  "error": "page_ids is required"
}
```

**404 Not Found:**
```json
{
  "success": false,
  "error": "No pages found or access denied"
}
```

---

### 2. Bulk Delete Products

**Endpoint:** `POST /api/v1/web-knowledge/products/bulk-delete/`

**Authentication:** Required (Bearer Token)

**Request Body:**
```json
{
  "product_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174001",
    "789e0123-e89b-12d3-a456-426614174002"
  ]
}
```

**دستور curl:**
```bash
curl -X POST "https://api.pilito.com/api/v1/web-knowledge/products/bulk-delete/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_ids": [
      "123e4567-e89b-12d3-a456-426614174000",
      "456e7890-e89b-12d3-a456-426614174001"
    ]
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "3 products deleted successfully",
  "deleted_count": 3,
  "deleted_products": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Product 1",
      "product_type": "product"
    },
    {
      "id": "456e7890-e89b-12d3-a456-426614174001",
      "title": "Product 2",
      "product_type": "service"
    }
  ]
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "success": false,
  "error": "product_ids is required"
}
```

**404 Not Found:**
```json
{
  "success": false,
  "error": "No products found or access denied"
}
```

---

### 3. Bulk Delete Q&A Pairs (FAQ)

**Endpoint:** `POST /api/v1/web-knowledge/qa-pairs/bulk_delete/`

**Authentication:** Required (Bearer Token)

**Request Body:**
```json
{
  "qa_pair_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "456e7890-e89b-12d3-a456-426614174001",
    "789e0123-e89b-12d3-a456-426614174002"
  ]
}
```

**دستور curl:**
```bash
curl -X POST "https://api.pilito.com/api/v1/web-knowledge/qa-pairs/bulk_delete/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "qa_pair_ids": [
      "123e4567-e89b-12d3-a456-426614174000",
      "456e7890-e89b-12d3-a456-426614174001"
    ]
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "3 Q&A pairs deleted successfully",
  "deleted_count": 3,
  "deleted_qa_pairs": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "question": "What are your business hours?",
      "page_title": "Contact Us",
      "website_name": "My Business Website"
    },
    {
      "id": "456e7890-e89b-12d3-a456-426614174001",
      "question": "How can I contact support?",
      "page_title": "Support",
      "website_name": "My Business Website"
    }
  ]
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "error": "qa_pair_ids is required"
}
```

**404 Not Found:**
```json
{
  "error": "No Q&A pairs found or access denied"
}
```

---

## 🎨 مثال React/TypeScript

### Component عمومی برای Bulk Delete

```tsx
import React, { useState } from 'react';

interface BulkDeleteProps {
  type: 'pages' | 'products' | 'qa-pairs';
  selectedIds: string[];
  onSuccess?: () => void;
}

export const BulkDeleteButton: React.FC<BulkDeleteProps> = ({ 
  type, 
  selectedIds, 
  onSuccess 
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) {
      setError('Please select at least one item');
      return;
    }

    if (!confirm(`Are you sure you want to delete ${selectedIds.length} item(s)?`)) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // تعیین endpoint بر اساس type
      const endpoint = {
        'pages': '/api/v1/web-knowledge/pages/bulk-delete/',
        'products': '/api/v1/web-knowledge/products/bulk-delete/',
        'qa-pairs': '/api/v1/web-knowledge/qa-pairs/bulk_delete/'
      }[type];

      const fieldName = {
        'pages': 'page_ids',
        'products': 'product_ids',
        'qa-pairs': 'qa_pair_ids'
      }[type];

      const token = localStorage.getItem('access_token');

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          [fieldName]: selectedIds
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.message || 'Failed to delete');
      }

      // Success
      alert(`✅ ${data.message}`);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {error && <div className="error-message">{error}</div>}
      <button
        onClick={handleBulkDelete}
        disabled={loading || selectedIds.length === 0}
        className="btn-delete"
      >
        {loading ? 'Deleting...' : `Delete ${selectedIds.length} Selected`}
      </button>
    </div>
  );
};
```

### مثال کامل: Products Component با Bulk Selection

```tsx
import React, { useState, useEffect } from 'react';
import { BulkDeleteButton } from './BulkDeleteButton';

interface Product {
  id: string;
  title: string;
  product_type: string;
  sale_price: string;
  image: string | null;
}

const ProductsList: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load products
  useEffect(() => {
    const loadProducts = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/v1/web-knowledge/products/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) throw new Error('Failed to load products');
        
        const data = await response.json();
        setProducts(data.results || data);
      } catch (err) {
        console.error('Error loading products:', err);
      } finally {
        setLoading(false);
      }
    };
    
    loadProducts();
  }, []);

  // Handle individual selection
  const handleSelect = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
    setSelectAll(newSelected.size === products.length);
  };

  // Handle select all
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedIds(new Set());
      setSelectAll(false);
    } else {
      setSelectedIds(new Set(products.map(p => p.id)));
      setSelectAll(true);
    }
  };

  // Handle bulk delete success
  const handleBulkDeleteSuccess = () => {
    // Remove deleted products from list
    setProducts(products.filter(p => !selectedIds.has(p.id)));
    setSelectedIds(new Set());
    setSelectAll(false);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      {/* Bulk Actions Bar */}
      {selectedIds.size > 0 && (
        <div style={{ 
          padding: '12px', 
          background: '#f3f4f6', 
          borderRadius: '4px',
          marginBottom: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>{selectedIds.size} item(s) selected</span>
          <BulkDeleteButton
            type="products"
            selectedIds={Array.from(selectedIds)}
            onSuccess={handleBulkDeleteSuccess}
          />
        </div>
      )}

      {/* Select All Checkbox */}
      <div style={{ marginBottom: '8px' }}>
        <label>
          <input
            type="checkbox"
            checked={selectAll}
            onChange={handleSelectAll}
          />
          Select All
        </label>
      </div>

      {/* Products List */}
      <div className="products-list">
        {products.map(product => (
          <div 
            key={product.id} 
            style={{
              padding: '12px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              marginBottom: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}
          >
            <input
              type="checkbox"
              checked={selectedIds.has(product.id)}
              onChange={() => handleSelect(product.id)}
            />
            {product.image && (
              <img 
                src={product.image} 
                alt={product.title}
                style={{ width: '50px', height: '50px', objectFit: 'cover' }}
              />
            )}
            <div style={{ flex: 1 }}>
              <h3>{product.title}</h3>
              <p>Type: {product.product_type}</p>
              <p>Price: {product.sale_price}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProductsList;
```

### مثال: Q&A Pairs Component

```tsx
import React, { useState, useEffect } from 'react';
import { BulkDeleteButton } from './BulkDeleteButton';

interface QAPair {
  id: string;
  question: string;
  answer: string;
  page_title?: string;
}

const QAPairsList: React.FC = () => {
  const [qaPairs, setQAPairs] = useState<QAPair[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Load Q&A pairs
  useEffect(() => {
    const loadQAPairs = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/v1/web-knowledge/qa-pairs/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) throw new Error('Failed to load Q&A pairs');
        
        const data = await response.json();
        setQAPairs(data.results || data);
      } catch (err) {
        console.error('Error loading Q&A pairs:', err);
      }
    };
    
    loadQAPairs();
  }, []);

  const handleSelect = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleBulkDeleteSuccess = () => {
    setQAPairs(qaPairs.filter(qa => !selectedIds.has(qa.id)));
    setSelectedIds(new Set());
  };

  return (
    <div>
      {selectedIds.size > 0 && (
        <div style={{ padding: '12px', background: '#f3f4f6', marginBottom: '16px' }}>
          <BulkDeleteButton
            type="qa-pairs"
            selectedIds={Array.from(selectedIds)}
            onSuccess={handleBulkDeleteSuccess}
          />
        </div>
      )}

      {qaPairs.map(qa => (
        <div key={qa.id} style={{ padding: '12px', border: '1px solid #ddd', marginBottom: '8px' }}>
          <input
            type="checkbox"
            checked={selectedIds.has(qa.id)}
            onChange={() => handleSelect(qa.id)}
          />
          <h4>{qa.question}</h4>
          <p>{qa.answer}</p>
          {qa.page_title && <small>Page: {qa.page_title}</small>}
        </div>
      ))}
    </div>
  );
};

export default QAPairsList;
```

---

## ⚠️ نکات مهم

### 1. Security
- فقط آیتم‌هایی که متعلق به کاربر هستند پاک می‌شن
- اگر ID آیتمی که متعلق به کاربر نیست ارسال شود، نادیده گرفته می‌شود

### 2. Automatic Cleanup
- وقتی Pages پاک می‌شن، Q&A pairs مربوطه هم پاک می‌شن
- وقتی Pages یا Products پاک می‌شن، chunks مربوطه از TenantKnowledge هم پاک می‌شن (via signals)

### 3. Response
- Response شامل لیست آیتم‌های پاک شده است
- برای Pages، تعداد Q&A pairs پاک شده هم نمایش داده می‌شود

### 4. Error Handling
- اگر هیچ آیتمی پیدا نشود یا دسترسی نداشته باشید، 404 برمی‌گردونه
- اگر `ids` ارسال نشود، 400 برمی‌گردونه

---

## 🔗 لینک‌های مرتبط

- [Manual Product API](./MANUAL_PRODUCT_API.md) - برای مدیریت محصولات
- [Manual Page Crawl API](./MANUAL_PAGE_CRAWL_API.md) - برای کرال صفحات
- [Q&A Delete API](./QA_DELETE_AND_PARTIAL_CREATE_API.md) - برای حذف Q&A

---

**نسخه:** 1.0  
**تاریخ:** 2025-11-11  
**مخاطب:** Frontend Developers

