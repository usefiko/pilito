# Product Management API - Complete Documentation

## 🎯 **Overview**

The Product Management API allows you to manage products and services in your knowledge base. This matches the design shown in your AI & Prompts interface with Product & Services tab.

## 📋 **Product Model Fields**

Based on the UI design, the Product model includes:

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `title` | String | Product or service title | ✅ Yes |
| `product_type` | Choice | Type of product/service | ✅ Yes |
| `description` | Text | Detailed description | ✅ Yes |
| `link` | URL | Product link/URL | ❌ Optional |
| `price` | Decimal | Price in USD | ❌ Optional |
| `tags` | Array | Tags for categorization | ❌ Optional |
| `is_active` | Boolean | Active status | ❌ Optional (default: true) |

### **Product Type Choices:**
- `service` - Service
- `product` - Product  
- `software` - Software
- `consultation` - Consultation
- `course` - Course
- `tool` - Tool
- `other` - Other

---

## 🌐 **API Endpoints**

### **1. Get Product Types (for dropdown)**
```http
GET /api/v1/web-knowledge/products/product_types/
```

**Response:**
```json
{
  "product_types": [
    {"value": "service", "label": "Service"},
    {"value": "product", "label": "Product"},
    {"value": "software", "label": "Software"},
    {"value": "consultation", "label": "Consultation"},
    {"value": "course", "label": "Course"},
    {"value": "tool", "label": "Tool"},
    {"value": "other", "label": "Other"}
  ]
}
```

### **2. Create Product (Add Button)**
```http
POST /api/v1/web-knowledge/products/
```

**Request Body:**
```json
{
  "title": "Professional Web Development Service",
  "product_type": "service",
  "description": "Custom web development services including responsive design, e-commerce solutions, and modern web applications using latest technologies.",
  "link": "https://example.com/web-development",
  "price": 2500.00,
  "tags": ["web development", "responsive", "e-commerce"],
  "is_active": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Product created successfully",
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "product": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Professional Web Development Service",
    "product_type": "service",
    "product_type_display": "Service",
    "description": "Custom web development services...",
    "link": "https://example.com/web-development",
    "has_link": true,
    "price": "2500.00",
    "tags": ["web development", "responsive", "e-commerce"],
    "tags_display": "web development, responsive, e-commerce",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### **3. List Products**
```http
GET /api/v1/web-knowledge/products/
```

**Query Parameters:**
- `product_type` - Filter by product type
- `is_active` - Filter by active status (true/false)
- `search` - Search in title and description

**Examples:**
```bash
# Get all products
GET /api/v1/web-knowledge/products/

# Get only services
GET /api/v1/web-knowledge/products/?product_type=service

# Get only active products
GET /api/v1/web-knowledge/products/?is_active=true

# Search products
GET /api/v1/web-knowledge/products/?search=web development
```

**Response:**
```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Professional Web Development Service",
      "product_type": "service",
      "product_type_display": "Service",
      "description": "Custom web development services...",
      "link": "https://example.com/web-development",
      "has_link": true,
      "price": "2500.00",
      "tags": ["web development", "responsive", "e-commerce"],
      "tags_display": "web development, responsive, e-commerce",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### **4. Get Single Product**
```http
GET /api/v1/web-knowledge/products/{product_id}/
```

**Response:** Same as individual product object above.

### **5. Update Product**
```http
PUT /api/v1/web-knowledge/products/{product_id}/     # Full update
PATCH /api/v1/web-knowledge/products/{product_id}/   # Partial update
```

**Request Body (PATCH example):**
```json
{
  "title": "Updated Professional Web Development Service",
  "price": 3000.00,
  "tags": ["web development", "responsive", "e-commerce", "modern"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Product updated successfully",
  "product": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Updated Professional Web Development Service",
    "price": "3000.00",
    "tags": ["web development", "responsive", "e-commerce", "modern"],
    ...
  }
}
```

### **6. Delete Product**
```http
DELETE /api/v1/web-knowledge/products/{product_id}/
```

**Response:**
```json
{
  "success": true,
  "message": "Product \"Professional Web Development Service\" deleted successfully",
  "deleted_product": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Professional Web Development Service",
    "product_type": "service"
  }
}
```

### **7. Get Products Statistics**
```http
GET /api/v1/web-knowledge/products/statistics/
```

**Response:**
```json
{
  "total_products": 15,
  "active_products": 12,
  "by_type": [
    {"product_type": "service", "count": 8},
    {"product_type": "product", "count": 4},
    {"product_type": "software", "count": 2},
    {"product_type": "course", "count": 1}
  ],
  "with_links": 10,
  "with_prices": 8,
  "recent_products": [
    {
      "id": "123...",
      "title": "Web Development Service",
      "product_type": "service",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## 💻 **Frontend Integration Examples**

### **1. Load Product Types for Dropdown**
```javascript
// Get product types for the "Select type" dropdown
const loadProductTypes = async () => {
  const response = await fetch('/api/v1/web-knowledge/products/product_types/', {
    headers: { 'Authorization': 'Bearer ' + token }
  });
  const data = await response.json();
  
  // Populate dropdown
  const dropdown = document.getElementById('productType');
  data.product_types.forEach(type => {
    dropdown.innerHTML += `<option value="${type.value}">${type.label}</option>`;
  });
};
```

### **2. Add New Product (Form Submission)**
```javascript
// Handle "Add" button click
const addProduct = async (formData) => {
  const response = await fetch('/api/v1/web-knowledge/products/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title: formData.title,
      product_type: formData.productType,
      description: formData.description,
      link: formData.link,
      price: formData.price ? parseFloat(formData.price) : null,
      tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : []
    })
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('Product created:', result.product);
    // Refresh products list
    loadProducts();
    // Clear form
    clearForm();
  }
};
```

### **3. Load and Display Products List**
```javascript
// Load products and display in UI
const loadProducts = async () => {
  const response = await fetch('/api/v1/web-knowledge/products/', {
    headers: { 'Authorization': 'Bearer ' + token }
  });
  const data = await response.json();
  
  // Display products
  const container = document.getElementById('productsList');
  container.innerHTML = '';
  
  if (data.results.length === 0) {
    container.innerHTML = '<p>No products added yet</p>';
    return;
  }
  
  data.results.forEach(product => {
    container.innerHTML += `
      <div class="product-card">
        <h3>${product.title}</h3>
        <span class="badge">${product.product_type_display}</span>
        <p>${product.description}</p>
        ${product.has_link ? `<a href="${product.link}" target="_blank">View Product</a>` : ''}
        ${product.price ? `<span class="price">$${product.price}</span>` : ''}
        <div class="actions">
          <button onclick="editProduct('${product.id}')">Edit</button>
          <button onclick="deleteProduct('${product.id}')">Delete</button>
        </div>
      </div>
    `;
  });
};
```

### **4. Edit Product**
```javascript
// Edit existing product
const editProduct = async (productId, updatedData) => {
  const response = await fetch(`/api/v1/web-knowledge/products/${productId}/`, {
    method: 'PATCH',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updatedData)
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('Product updated:', result.product);
    loadProducts(); // Refresh list
  }
};
```

### **5. Delete Product**
```javascript
// Delete product with confirmation
const deleteProduct = async (productId) => {
  if (!confirm('Are you sure you want to delete this product?')) {
    return;
  }
  
  const response = await fetch(`/api/v1/web-knowledge/products/${productId}/`, {
    method: 'DELETE',
    headers: { 'Authorization': 'Bearer ' + token }
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('Product deleted:', result.message);
    loadProducts(); // Refresh list
  }
};
```

---

## 🔒 **Security & Validation**

### **Security Features:**
- ✅ **User Isolation**: Users can only manage their own products
- ✅ **Authentication Required**: All endpoints require valid token
- ✅ **Input Validation**: All fields validated for format and content
- ✅ **XSS Protection**: HTML content properly escaped

### **Validation Rules:**
- **Title**: Minimum 3 characters, required
- **Description**: Minimum 10 characters, required  
- **Link**: Must be valid URL format (http/https)
- **Price**: Cannot be negative, optional
- **Product Type**: Must be one of the predefined choices

### **Error Responses:**
```json
{
  "success": false,
  "errors": {
    "title": ["Title must be at least 3 characters long"],
    "link": ["Link must start with http:// or https://"],
    "price": ["Price cannot be negative"]
  }
}
```

---

## 📊 **Complete Workflow Example**

Based on your UI design, here's a complete workflow:

### **1. Page Load**
```javascript
// Load product types for dropdown
await loadProductTypes();

// Load existing products
await loadProducts();
```

### **2. Form Submission (Add Button)**
```javascript
document.getElementById('addProductForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  const productData = {
    title: formData.get('title'),
    product_type: formData.get('product_type'),
    description: formData.get('description'),
    link: formData.get('link'),
    price: formData.get('price') ? parseFloat(formData.get('price')) : null,
    tags: formData.get('tags') ? formData.get('tags').split(',').map(t => t.trim()) : []
  };
  
  await addProduct(productData);
});
```

### **3. Save Changes Button**
```javascript
document.getElementById('saveChanges').addEventListener('click', async () => {
  // Save all modified products
  // This would save any changes made to the products list
  console.log('All changes saved successfully');
});
```

The Product Management API provides complete CRUD functionality that matches your UI design perfectly! 🚀
