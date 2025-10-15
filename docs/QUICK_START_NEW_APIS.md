# Quick Start Guide - New Web Knowledge APIs

## 🚀 Getting Started

This guide will help you quickly integrate the new and improved Product APIs into your frontend.

---

## 📋 Prerequisites

1. Backend server running
2. Valid authentication token
3. Python 3.8+ (for migration script)

---

## ⚙️ Setup Steps

### Step 1: Apply Database Migrations

```bash
cd /Users/nima/Projects/Fiko-Backend

# Create migrations (if not already created)
python manage.py makemigrations web_knowledge

# Apply migrations
python manage.py migrate web_knowledge
```

### Step 2: Analyze Existing Data (Optional)

```bash
# Check what needs migration
python migrate_product_data.py --analyze
```

### Step 3: Migrate Existing Products (Optional)

```bash
# Dry run first to see what would change
python migrate_product_data.py --dry-run

# Apply changes
python migrate_product_data.py
```

---

## 🎯 Quick Examples

### Example 1: Fetch All Products with Discounts

```javascript
// Fetch products with discounts
const response = await fetch(
  '/api/v1/web-knowledge/products/?has_discount=true',
  {
    headers: {
      'Authorization': `Bearer ${YOUR_TOKEN}`
    }
  }
);

const products = await response.json();

// Display products
products.forEach(product => {
  console.log(`
    ${product.title}
    Price: ${product.final_price} ${product.currency}
    Discount: ${product.discount_info}
    In Stock: ${product.in_stock ? 'Yes' : 'No'}
  `);
});
```

### Example 2: Create a New Product

```javascript
// Create a new product
const newProduct = {
  title: "Premium SaaS Subscription",
  product_type: "software",
  description: "Advanced cloud software solution",
  short_description: "Cloud software for businesses",
  price: "99.99",
  original_price: "149.99",
  discount_percentage: "33.33",
  currency: "USD",
  billing_period: "monthly",
  features: [
    "24/7 Support",
    "Unlimited Users",
    "Advanced Analytics"
  ],
  category: "Software",
  brand: "Your Company",
  is_active: true,
  in_stock: true
};

const response = await fetch(
  '/api/v1/web-knowledge/products/',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${YOUR_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(newProduct)
  }
);

const result = await response.json();
console.log('Created:', result.product);
```

### Example 3: Get All Dropdown Choices

```javascript
// Fetch all choices for dropdowns
const response = await fetch(
  '/api/v1/web-knowledge/products/choices/all/',
  {
    headers: {
      'Authorization': `Bearer ${YOUR_TOKEN}`
    }
  }
);

const choices = await response.json();

// Use in your UI
const productTypes = choices.product_types;
const currencies = choices.currencies;
const billingPeriods = choices.billing_periods;

// Example: Populate a select dropdown
productTypes.forEach(type => {
  const option = document.createElement('option');
  option.value = type.value;
  option.text = type.label;
  document.getElementById('product-type-select').appendChild(option);
});
```

### Example 4: Get Products from a Website

```javascript
// Get all products extracted from a specific website
const websiteId = 'your-website-uuid';

const response = await fetch(
  `/api/v1/web-knowledge/websites/${websiteId}/products/`,
  {
    headers: {
      'Authorization': `Bearer ${YOUR_TOKEN}`
    }
  }
);

const data = await response.json();

console.log(`
  Website: ${data.website_name}
  Total Products: ${data.total_products}
  Active: ${data.active_products}
  In Stock: ${data.in_stock_products}
`);

// Display products
data.products.forEach(product => {
  console.log(`- ${product.title} (${product.product_type})`);
});
```

### Example 5: Advanced Filtering

```javascript
// Complex filter query
const filters = new URLSearchParams({
  product_type: 'service',
  currency: 'USD',
  min_price: '50',
  max_price: '200',
  is_active: 'true',
  in_stock: 'true',
  has_discount: 'true',
  search: 'premium'
});

const response = await fetch(
  `/api/v1/web-knowledge/products/?${filters}`,
  {
    headers: {
      'Authorization': `Bearer ${YOUR_TOKEN}`
    }
  }
);

const products = await response.json();
console.log(`Found ${products.length} matching products`);
```

### Example 6: Get Product Statistics

```javascript
// Get comprehensive statistics
const response = await fetch(
  '/api/v1/web-knowledge/products/statistics/',
  {
    headers: {
      'Authorization': `Bearer ${YOUR_TOKEN}`
    }
  }
);

const stats = await response.json();

console.log(`
  Total Products: ${stats.total_products}
  Active: ${stats.active_products}
  In Stock: ${stats.in_stock_products}
  With Discounts: ${stats.with_discounts}
  Auto-Extracted: ${stats.auto_extracted}
  Manual: ${stats.manual}
`);

// Display by type
stats.by_type.forEach(item => {
  console.log(`${item.product_type}: ${item.count}`);
});
```

### Example 7: Bulk Operations

```javascript
// Bulk deactivate products
const productIds = ['uuid1', 'uuid2', 'uuid3'];

const response = await fetch(
  '/api/v1/web-knowledge/products/bulk-update/',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${YOUR_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      product_ids: productIds,
      is_active: false,
      in_stock: false
    })
  }
);

const result = await response.json();
console.log(`Updated ${result.updated_count} products`);
```

---

## 🎨 React Component Examples

### Product List Component

```jsx
import React, { useState, useEffect } from 'react';

function ProductList() {
  const [products, setProducts] = useState([]);
  const [filters, setFilters] = useState({
    product_type: '',
    currency: 'USD',
    has_discount: false,
    search: ''
  });

  useEffect(() => {
    fetchProducts();
  }, [filters]);

  const fetchProducts = async () => {
    const params = new URLSearchParams(
      Object.entries(filters).filter(([_, v]) => v)
    );
    
    const response = await fetch(
      `/api/v1/web-knowledge/products/?${params}`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    );
    
    const data = await response.json();
    setProducts(data);
  };

  return (
    <div>
      <h2>Products</h2>
      
      {/* Filters */}
      <div className="filters">
        <input
          type="text"
          placeholder="Search..."
          value={filters.search}
          onChange={(e) => setFilters({...filters, search: e.target.value})}
        />
        
        <label>
          <input
            type="checkbox"
            checked={filters.has_discount}
            onChange={(e) => setFilters({...filters, has_discount: e.target.checked})}
          />
          Show only discounted
        </label>
      </div>

      {/* Product List */}
      <div className="product-grid">
        {products.map(product => (
          <div key={product.id} className="product-card">
            {product.main_image && (
              <img src={product.main_image} alt={product.title} />
            )}
            <h3>{product.title}</h3>
            <p>{product.short_description}</p>
            
            <div className="price">
              {product.has_discount && (
                <span className="original-price">
                  {product.original_price} {product.currency}
                </span>
              )}
              <span className="final-price">
                {product.final_price} {product.currency}
              </span>
              {product.discount_info && (
                <span className="discount-badge">{product.discount_info}</span>
              )}
            </div>
            
            <div className="meta">
              <span className={product.in_stock ? 'in-stock' : 'out-of-stock'}>
                {product.in_stock ? 'In Stock' : 'Out of Stock'}
              </span>
              {product.is_auto_extracted && (
                <span className="badge">AI Extracted</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ProductList;
```

### Product Form Component

```jsx
import React, { useState, useEffect } from 'react';

function ProductForm({ productId = null, onSave }) {
  const [product, setProduct] = useState({
    title: '',
    product_type: 'service',
    description: '',
    price: '',
    currency: 'USD',
    is_active: true,
    in_stock: true
  });
  
  const [choices, setChoices] = useState(null);

  useEffect(() => {
    // Fetch choices
    fetchChoices();
    
    // If editing, fetch product
    if (productId) {
      fetchProduct();
    }
  }, [productId]);

  const fetchChoices = async () => {
    const response = await fetch(
      '/api/v1/web-knowledge/products/choices/all/',
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    );
    const data = await response.json();
    setChoices(data);
  };

  const fetchProduct = async () => {
    const response = await fetch(
      `/api/v1/web-knowledge/products/${productId}/`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    );
    const data = await response.json();
    setProduct(data);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const method = productId ? 'PATCH' : 'POST';
    const url = productId
      ? `/api/v1/web-knowledge/products/${productId}/`
      : '/api/v1/web-knowledge/products/';
    
    const response = await fetch(url, {
      method,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(product)
    });
    
    const result = await response.json();
    
    if (result.success) {
      onSave(result.product);
    }
  };

  if (!choices) return <div>Loading...</div>;

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Product Title"
        value={product.title}
        onChange={(e) => setProduct({...product, title: e.target.value})}
        required
      />

      <select
        value={product.product_type}
        onChange={(e) => setProduct({...product, product_type: e.target.value})}
      >
        {choices.product_types.map(type => (
          <option key={type.value} value={type.value}>
            {type.label}
          </option>
        ))}
      </select>

      <textarea
        placeholder="Description"
        value={product.description}
        onChange={(e) => setProduct({...product, description: e.target.value})}
        required
      />

      <input
        type="number"
        step="0.01"
        placeholder="Price"
        value={product.price}
        onChange={(e) => setProduct({...product, price: e.target.value})}
      />

      <select
        value={product.currency}
        onChange={(e) => setProduct({...product, currency: e.target.value})}
      >
        {choices.currencies.map(curr => (
          <option key={curr.value} value={curr.value}>
            {curr.label}
          </option>
        ))}
      </select>

      <label>
        <input
          type="checkbox"
          checked={product.is_active}
          onChange={(e) => setProduct({...product, is_active: e.target.checked})}
        />
        Active
      </label>

      <label>
        <input
          type="checkbox"
          checked={product.in_stock}
          onChange={(e) => setProduct({...product, in_stock: e.target.checked})}
        />
        In Stock
      </label>

      <button type="submit">
        {productId ? 'Update' : 'Create'} Product
      </button>
    </form>
  );
}

export default ProductForm;
```

---

## 📚 Additional Resources

- **Full API Documentation:** [WEB_KNOWLEDGE_API_UPDATES.md](./WEB_KNOWLEDGE_API_UPDATES.md)
- **Summary of Changes:** [API_UPDATE_SUMMARY.md](./API_UPDATE_SUMMARY.md)
- **Migration Script:** [migrate_product_data.py](./migrate_product_data.py)
- **Django Models:** [src/web_knowledge/models.py](./src/web_knowledge/models.py)

---

## 🧪 Testing Endpoints

### Using cURL

```bash
# Get all products
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/web-knowledge/products/

# Get products with filters
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/web-knowledge/products/?has_discount=true&currency=USD"

# Get choices
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/web-knowledge/products/choices/all/

# Get statistics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/web-knowledge/products/statistics/
```

### Using Python Requests

```python
import requests

TOKEN = "your-auth-token"
BASE_URL = "http://localhost:8000/api/v1/web-knowledge"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get products
response = requests.get(f"{BASE_URL}/products/", headers=headers)
products = response.json()

# Create product
new_product = {
    "title": "Test Product",
    "product_type": "service",
    "description": "Test description",
    "price": "99.99",
    "currency": "USD"
}
response = requests.post(f"{BASE_URL}/products/", json=new_product, headers=headers)
result = response.json()
```

---

## ❓ FAQ

### Q: Do I need to migrate existing products?
**A:** Only if you want to set default values for new fields. The API will work with existing products as-is.

### Q: What happens if I don't provide optional fields when creating a product?
**A:** They will be set to their default values (empty strings, empty arrays, null, etc.)

### Q: Can I filter by multiple criteria at once?
**A:** Yes! All filter parameters can be combined in the query string.

### Q: How do I know if a product was auto-extracted?
**A:** Check the `is_auto_extracted` computed property or `extraction_method` field.

### Q: What's the difference between `price` and `final_price`?
**A:** `final_price` is computed and includes any discounts applied to `price`.

---

## 🆘 Troubleshooting

### Products not showing up
- Check authentication token
- Verify user has products
- Check filters aren't too restrictive

### Validation errors when creating products
- Ensure title is at least 3 characters
- Ensure description is at least 10 characters
- Ensure price is non-negative
- Ensure discount percentage is 0-100

### Migration script errors
- Ensure Django is properly configured
- Run from project root directory
- Check database connections

---

## 📞 Support

For questions or issues:
1. Check the full API documentation
2. Review this quick start guide
3. Check the migration summary
4. Contact the backend team

---

**Happy Coding! 🚀**

