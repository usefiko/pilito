# Tag Search & Filter Guide

Complete guide for using search and filter functionality in Tag APIs.

---

## 📋 Overview

All tag-related endpoints now support powerful search, filter, and ordering capabilities to help you find and organize tags efficiently.

---

## 🔍 Search Capabilities

### 1. Main Tags API (`/api/v1/msg/tags`)

**Endpoint:** `GET /api/v1/msg/tags`

**Supported Features:**
- ✅ **Search** - Search by tag name
- ✅ **Filter** - Filter by creation date
- ✅ **Ordering** - Sort by name or creation date

#### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Search by tag name (case-insensitive partial match) | `?search=vip` |
| `ordering` | string | Order by field (use `-` for descending) | `?ordering=-created_at` |
| `created_at` | date | Filter by exact creation date | `?created_at=2024-01-15` |

#### Examples

**Search for tags containing "premium":**
```bash
GET /api/v1/msg/tags?search=premium
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "Premium",
        "created_by": 5,
        "created_at": "2024-01-15T10:30:00Z"
    },
    {
        "id": 2,
        "name": "Premium Plus",
        "created_by": 5,
        "created_at": "2024-01-16T14:20:00Z"
    }
]
```

**Get tags ordered by name (A-Z):**
```bash
GET /api/v1/msg/tags?ordering=name
```

**Get tags ordered by creation date (newest first):**
```bash
GET /api/v1/msg/tags?ordering=-created_at
```

**Get tags created on a specific date:**
```bash
GET /api/v1/msg/tags?created_at=2024-01-15
```

**Combine search and ordering:**
```bash
GET /api/v1/msg/tags?search=vip&ordering=name
```

---

### 2. Customer Tags API (`/api/v1/msg/customer/{id}/tags/`)

**Endpoint:** `GET /api/v1/msg/customer/{customer_id}/tags/`

**Supported Features:**
- ✅ **Search** - Search customer's tags by name
- ✅ **Ordering** - Sort by name or creation date
- ✅ **Count** - Returns total number of matching tags

#### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Search by tag name (case-insensitive partial match) | `?search=active` |
| `ordering` | string | Order by field: `name`, `-name`, `created_at`, `-created_at` | `?ordering=-name` |

#### Examples

**Search customer's tags:**
```bash
GET /api/v1/msg/customer/123/tags?search=vip
```

**Response:**
```json
{
    "customer_id": 123,
    "tags": [
        {
            "id": 1,
            "name": "VIP",
            "created_by": 5,
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "id": 5,
            "name": "VIP Gold",
            "created_by": 5,
            "created_at": "2024-01-20T09:15:00Z"
        }
    ],
    "count": 2
}
```

**Get customer's tags ordered alphabetically:**
```bash
GET /api/v1/msg/customer/123/tags?ordering=name
```

**Get customer's tags in reverse alphabetical order:**
```bash
GET /api/v1/msg/customer/123/tags?ordering=-name
```

**Get customer's tags ordered by creation date (newest first):**
```bash
GET /api/v1/msg/customer/123/tags?ordering=-created_at
```

**Combine search and ordering:**
```bash
GET /api/v1/msg/customer/123/tags?search=premium&ordering=name
```

---

## 🎯 Use Cases

### Use Case 1: Find All VIP Customers' Tags
```bash
# Search for "VIP" tags
GET /api/v1/msg/tags?search=vip
```

### Use Case 2: Get Recently Created Tags
```bash
# Get newest tags first
GET /api/v1/msg/tags?ordering=-created_at
```

### Use Case 3: Find Customer's Active Status Tags
```bash
# Search customer's tags for "active"
GET /api/v1/msg/customer/123/tags?search=active
```

### Use Case 4: List All Tags Alphabetically
```bash
# Order tags A-Z
GET /api/v1/msg/tags?ordering=name
```

### Use Case 5: Find Tags Created on Specific Date
```bash
# Get tags created on January 15, 2024
GET /api/v1/msg/tags?created_at=2024-01-15
```

### Use Case 6: Search and Sort Customer Tags
```bash
# Find customer's "premium" tags sorted by name
GET /api/v1/msg/customer/123/tags?search=premium&ordering=name
```

---

## 💡 Tips & Best Practices

### Search Tips

1. **Case-Insensitive:** Search is case-insensitive, so `vip`, `VIP`, and `Vip` all work the same.

2. **Partial Match:** Search matches any part of the tag name:
   - Searching `prem` will match `Premium`, `Supreme`, `Premium Plus`

3. **Multiple Words:** For multi-word searches, use URL encoding:
   ```bash
   # Search for "Premium Plus"
   GET /api/v1/msg/tags?search=Premium%20Plus
   ```

### Ordering Tips

1. **Default Order:** If no ordering is specified, tags are ordered by creation date (newest first) for main tags API, and by name for customer tags.

2. **Valid Ordering Fields:**
   - `name` - Alphabetical A-Z
   - `-name` - Alphabetical Z-A (reverse)
   - `created_at` - Oldest first
   - `-created_at` - Newest first (default)

3. **Invalid Ordering:** If you provide an invalid ordering field, the API will use the default ordering.

### Performance Tips

1. **Be Specific:** Use specific search terms to reduce result size.

2. **Combine Parameters:** Combine search and ordering for precise results:
   ```bash
   GET /api/v1/msg/tags?search=premium&ordering=name
   ```

---

## 🧪 Testing Examples

### cURL Examples

```bash
# Search for tags
curl -X GET \
  'http://localhost:8000/api/v1/msg/tags?search=vip' \
  -H 'Authorization: Bearer YOUR_TOKEN'

# Order tags by name
curl -X GET \
  'http://localhost:8000/api/v1/msg/tags?ordering=name' \
  -H 'Authorization: Bearer YOUR_TOKEN'

# Filter by date
curl -X GET \
  'http://localhost:8000/api/v1/msg/tags?created_at=2024-01-15' \
  -H 'Authorization: Bearer YOUR_TOKEN'

# Search customer's tags
curl -X GET \
  'http://localhost:8000/api/v1/msg/customer/123/tags?search=active' \
  -H 'Authorization: Bearer YOUR_TOKEN'

# Combined parameters
curl -X GET \
  'http://localhost:8000/api/v1/msg/tags?search=premium&ordering=name' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/msg"
TOKEN = "your_auth_token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Search for tags
response = requests.get(
    f"{BASE_URL}/tags",
    headers=headers,
    params={"search": "vip"}
)
print(response.json())

# Order by name
response = requests.get(
    f"{BASE_URL}/tags",
    headers=headers,
    params={"ordering": "name"}
)
print(response.json())

# Filter by date
response = requests.get(
    f"{BASE_URL}/tags",
    headers=headers,
    params={"created_at": "2024-01-15"}
)
print(response.json())

# Search customer's tags
response = requests.get(
    f"{BASE_URL}/customer/123/tags/",
    headers=headers,
    params={"search": "active", "ordering": "name"}
)
print(response.json())
```

### JavaScript/Axios Examples

```javascript
import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/v1/msg';
const TOKEN = 'your_auth_token';

const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Authorization': `Bearer ${TOKEN}`
    }
});

// Search for tags
const searchTags = async (searchTerm) => {
    const { data } = await api.get('/tags', {
        params: { search: searchTerm }
    });
    return data;
};

// Order tags by name
const getOrderedTags = async () => {
    const { data } = await api.get('/tags', {
        params: { ordering: 'name' }
    });
    return data;
};

// Filter by date
const getTagsByDate = async (date) => {
    const { data } = await api.get('/tags', {
        params: { created_at: date }
    });
    return data;
};

// Search customer's tags
const searchCustomerTags = async (customerId, searchTerm) => {
    const { data } = await api.get(`/customer/${customerId}/tags/`, {
        params: { search: searchTerm, ordering: 'name' }
    });
    return data;
};

// Example usage
(async () => {
    const vipTags = await searchTags('vip');
    console.log('VIP Tags:', vipTags);
    
    const orderedTags = await getOrderedTags();
    console.log('Ordered Tags:', orderedTags);
    
    const customerTags = await searchCustomerTags(123, 'active');
    console.log('Customer Tags:', customerTags);
})();
```

---

## 🔧 Advanced Examples

### Pagination + Search (if pagination is added later)

```bash
# Search with pagination
GET /api/v1/msg/tags?search=premium&page=1&page_size=10
```

### Multiple Filters

```bash
# Search + Filter + Order
GET /api/v1/msg/tags?search=vip&created_at=2024-01-15&ordering=name
```

### URL Encoding for Special Characters

```python
import urllib.parse

# Search for tag with special characters
search_term = "VIP & Premium"
encoded_term = urllib.parse.quote(search_term)
url = f"/api/v1/msg/tags?search={encoded_term}"
```

---

## 📊 Response Format

### Main Tags API Response
```json
[
    {
        "id": 1,
        "name": "VIP",
        "created_by": 5,
        "created_at": "2024-01-15T10:30:00Z"
    },
    {
        "id": 2,
        "name": "Premium",
        "created_by": 5,
        "created_at": "2024-01-16T14:20:00Z"
    }
]
```

### Customer Tags API Response
```json
{
    "customer_id": 123,
    "tags": [
        {
            "id": 1,
            "name": "VIP",
            "created_by": 5,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "count": 1
}
```

---

## ⚠️ Important Notes

1. **System Tags:** Search and filters exclude system tags (Telegram, Whatsapp, Instagram)

2. **User Scope:** Search only returns tags created by the authenticated user

3. **Customer Permission:** For customer tags, you must have permission to view that customer

4. **Empty Results:** If no tags match the search criteria, an empty array/list is returned

5. **Invalid Parameters:** Invalid filter/ordering parameters are ignored and defaults are used

---

## 🎓 Quick Reference

| Feature | Main Tags API | Customer Tags API |
|---------|---------------|-------------------|
| Search by name | ✅ `?search=term` | ✅ `?search=term` |
| Order by name | ✅ `?ordering=name` | ✅ `?ordering=name` |
| Order by date | ✅ `?ordering=-created_at` | ✅ `?ordering=-created_at` |
| Filter by date | ✅ `?created_at=2024-01-15` | ❌ |
| Result count | ❌ | ✅ (included in response) |

---

**Created:** 2025-10-29  
**Version:** 1.0  
**Status:** ✅ Complete

