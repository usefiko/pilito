# Customer Tags API - Quick Reference

## 🎯 Overview
Manage tags on customers with full CRUD operations. All endpoints require authentication and validate user permissions.

---

## 📍 Endpoints Summary

| Operation | Method | Endpoint | Description |
|-----------|--------|----------|-------------|
| **List Tags** | `GET` | `/customer/{id}/tags/` | Get all customer tags |
| **Add Tags** | `POST` | `/customer/{id}/tags/` | Add tags (keeps existing) |
| **Replace Tags** | `PUT` | `/customer/{id}/tags/` | Replace all tags |
| **Remove Tags** | `DELETE` | `/customer/{id}/tags/` | Remove specific tags |
| **Add One Tag** | `POST` | `/customer/{id}/tags/{tag_id}/` | Add single tag |
| **Remove One Tag** | `DELETE` | `/customer/{id}/tags/{tag_id}/` | Remove single tag |

---

## 🚀 Quick Examples

### Get Customer Tags
```http
GET /api/v1/msg/customer/123/tags/
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
    "customer_id": 123,
    "tags": [
        {"id": 1, "name": "VIP", "created_at": "2024-01-15T10:30:00Z"},
        {"id": 2, "name": "Premium", "created_at": "2024-01-16T14:20:00Z"}
    ]
}
```

---

### Add Tags to Customer
```http
POST /api/v1/msg/customer/123/tags/
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
    "tag_ids": [1, 2, 3]
}
```

**Response:**
```json
{
    "message": "Successfully added 3 tag(s) to customer",
    "customer_id": 123,
    "tags": [...]
}
```

---

### Replace All Tags
```http
PUT /api/v1/msg/customer/123/tags/
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
    "tag_ids": [4, 5]
}
```

**Response:**
```json
{
    "message": "Successfully replaced customer tags with 2 tag(s)",
    "customer_id": 123,
    "tags": [...]
}
```

---

### Remove Tags
```http
DELETE /api/v1/msg/customer/123/tags/
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
    "tag_ids": [1, 2]
}
```

**Response:**
```json
{
    "message": "Successfully removed 2 tag(s) from customer",
    "customer_id": 123,
    "tags": [...]
}
```

---

### Add Single Tag
```http
POST /api/v1/msg/customer/123/tags/5/
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
    "message": "Successfully added tag \"VIP\" to customer",
    "customer_id": 123,
    "tag": {"id": 5, "name": "VIP", ...}
}
```

---

### Remove Single Tag
```http
DELETE /api/v1/msg/customer/123/tags/5/
Authorization: Bearer YOUR_TOKEN
```

**Response:**
```json
{
    "message": "Successfully removed tag \"VIP\" from customer",
    "customer_id": 123
}
```

---

## ⚠️ Important Notes

### System Tags (Protected)
These tags **cannot be removed**:
- `Telegram`
- `Whatsapp`
- `Instagram`

They are automatically managed by the system based on customer source.

### Permissions
- Users can only manage tags for customers they have conversations with
- Tag IDs must exist and be valid integers
- Attempting to remove non-existent tags returns an error

### WebSocket Updates
All tag operations trigger real-time WebSocket notifications (`customer_updated` event).

---

## 🔧 Common Use Cases

### 1. Tag a Customer as VIP
```bash
# First, create the VIP tag (if not exists)
curl -X POST http://localhost:8000/api/v1/msg/tags \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "VIP"}'

# Then add it to customer (assuming tag_id=1)
curl -X POST http://localhost:8000/api/v1/msg/customer/123/tags/1/ \
  -H "Authorization: Bearer TOKEN"
```

### 2. Bulk Tag Multiple Customers
```bash
# Add "Premium" and "Active" tags (IDs: 2, 3) to customer
curl -X POST http://localhost:8000/api/v1/msg/customer/123/tags/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag_ids": [2, 3]}'
```

### 3. Replace Customer Segment
```bash
# Change customer from "Free" to "Premium" tier
curl -X PUT http://localhost:8000/api/v1/msg/customer/123/tags/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag_ids": [5]}'  # Only "Premium" tag
```

### 4. Remove Old Tags
```bash
# Remove "Trial" and "Inactive" tags (IDs: 7, 8)
curl -X DELETE http://localhost:8000/api/v1/msg/customer/123/tags/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag_ids": [7, 8]}'
```

### 5. Clear All Tags
```bash
# Remove all tags (except system tags)
curl -X PUT http://localhost:8000/api/v1/msg/customer/123/tags/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tag_ids": []}'
```

---

## 🐛 Error Examples

### Invalid Tag IDs
```json
{
    "error": "Invalid tag IDs: [99, 100]"
}
```

### Permission Denied
```json
{
    "error": "You don't have permission to access this customer"
}
```

### Cannot Remove System Tags
```json
{
    "error": "Cannot remove system tags (Telegram, Whatsapp, Instagram)"
}
```

### Tag Already Exists
```json
{
    "error": "Tag 'VIP' already exists on this customer"
}
```

---

## 📚 Full Documentation
See [CUSTOMER_TAGS_API_DOCS.md](./CUSTOMER_TAGS_API_DOCS.md) for complete API documentation.

---

## 🧪 Testing with Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/msg"
TOKEN = "your_auth_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get customer tags
response = requests.get(
    f"{BASE_URL}/customer/123/tags/",
    headers=headers
)
print(response.json())

# Add tags
response = requests.post(
    f"{BASE_URL}/customer/123/tags/",
    headers=headers,
    json={"tag_ids": [1, 2, 3]}
)
print(response.json())

# Replace tags
response = requests.put(
    f"{BASE_URL}/customer/123/tags/",
    headers=headers,
    json={"tag_ids": [4, 5]}
)
print(response.json())

# Remove tags
response = requests.delete(
    f"{BASE_URL}/customer/123/tags/",
    headers=headers,
    json={"tag_ids": [1, 2]}
)
print(response.json())

# Add single tag
response = requests.post(
    f"{BASE_URL}/customer/123/tags/1/",
    headers=headers
)
print(response.json())

# Remove single tag
response = requests.delete(
    f"{BASE_URL}/customer/123/tags/1/",
    headers=headers
)
print(response.json())
```

---

## 🧪 Testing with JavaScript/Axios

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000/api/v1/msg';
const TOKEN = 'your_auth_token';

const headers = {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json'
};

// Get customer tags
const getTags = async (customerId) => {
    const response = await axios.get(
        `${BASE_URL}/customer/${customerId}/tags/`,
        { headers }
    );
    return response.data;
};

// Add tags
const addTags = async (customerId, tagIds) => {
    const response = await axios.post(
        `${BASE_URL}/customer/${customerId}/tags/`,
        { tag_ids: tagIds },
        { headers }
    );
    return response.data;
};

// Replace tags
const replaceTags = async (customerId, tagIds) => {
    const response = await axios.put(
        `${BASE_URL}/customer/${customerId}/tags/`,
        { tag_ids: tagIds },
        { headers }
    );
    return response.data;
};

// Remove tags
const removeTags = async (customerId, tagIds) => {
    const response = await axios.delete(
        `${BASE_URL}/customer/${customerId}/tags/`,
        { headers, data: { tag_ids: tagIds } }
    );
    return response.data;
};

// Add single tag
const addSingleTag = async (customerId, tagId) => {
    const response = await axios.post(
        `${BASE_URL}/customer/${customerId}/tags/${tagId}/`,
        {},
        { headers }
    );
    return response.data;
};

// Remove single tag
const removeSingleTag = async (customerId, tagId) => {
    const response = await axios.delete(
        `${BASE_URL}/customer/${customerId}/tags/${tagId}/`,
        { headers }
    );
    return response.data;
};

// Example usage
(async () => {
    try {
        const tags = await getTags(123);
        console.log('Customer tags:', tags);
        
        const added = await addTags(123, [1, 2, 3]);
        console.log('Tags added:', added);
        
        const replaced = await replaceTags(123, [4, 5]);
        console.log('Tags replaced:', replaced);
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
})();
```

---

**Created:** 2025-10-29  
**Version:** 1.0  
**Status:** Ready to use

