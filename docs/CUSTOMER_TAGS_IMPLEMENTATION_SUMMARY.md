# Customer Tags Management - Implementation Summary

## 📋 Overview

Comprehensive API endpoints have been created for managing tags on the Customer model in the message app. These APIs provide full CRUD operations for customer tags with permission checking and real-time WebSocket notifications.

---

## ✅ What Was Created

### 1. **New API File: `customer_tags.py`**
Location: `/src/message/api/customer_tags.py`

**Contains two main API classes:**

#### `CustomerTagsAPIView`
Manages bulk tag operations on customers:
- **GET** - Get all tags for a customer
- **POST** - Add tags to customer (keeps existing tags)
- **PUT** - Replace all customer tags
- **DELETE** - Remove specific tags from customer

#### `CustomerSingleTagAPIView`
Manages single tag operations:
- **POST** - Add a single tag to customer
- **DELETE** - Remove a single tag from customer

---

### 2. **Updated URLs**
Location: `/src/message/urls.py`

**Added new endpoints:**
```python
# Customer Tags Management
path("customer/<int:customer_id>/tags/", CustomerTagsAPIView.as_view(), name="customer-tags"),
path("customer/<int:customer_id>/tags/<int:tag_id>/", CustomerSingleTagAPIView.as_view(), name="customer-single-tag"),
```

---

### 3. **Documentation Files**

#### `CUSTOMER_TAGS_API_DOCS.md`
Complete API documentation including:
- Detailed endpoint descriptions
- Request/response examples
- Error handling
- Best practices
- WebSocket integration details

#### `CUSTOMER_TAGS_QUICK_REFERENCE.md`
Quick reference guide with:
- Endpoint summary table
- Quick examples
- Common use cases
- Testing code (Python & JavaScript)
- Error examples

---

## 🎯 API Endpoints

### Base URL
```
/api/v1/msg/
```

### All Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/customer/{id}/tags/` | Get all tags for a customer |
| `POST` | `/customer/{id}/tags/` | Add tags to customer (keeps existing) |
| `PUT` | `/customer/{id}/tags/` | Replace all customer tags |
| `DELETE` | `/customer/{id}/tags/` | Remove specific tags from customer |
| `POST` | `/customer/{id}/tags/{tag_id}/` | Add a single tag to customer |
| `DELETE` | `/customer/{id}/tags/{tag_id}/` | Remove a single tag from customer |

---

## 🔐 Security Features

### Permission Checking
- ✅ All endpoints require authentication (`IsAuthenticated`)
- ✅ Users can only manage tags for customers they have conversations with
- ✅ Returns `403 Forbidden` if user doesn't have permission

### System Tag Protection
- ✅ System tags (`Telegram`, `Whatsapp`, `Instagram`) cannot be removed
- ✅ System tags are automatically managed based on customer source
- ✅ Returns error if attempting to remove system tags

### Input Validation
- ✅ Tag IDs must be valid integers
- ✅ Tag IDs must exist in database
- ✅ Duplicate tag IDs are rejected
- ✅ Empty tag lists are handled appropriately

---

## 💡 Key Features

### 1. Bulk Operations
```python
# Add multiple tags at once
POST /customer/123/tags/
{"tag_ids": [1, 2, 3, 4, 5]}

# Replace all tags at once
PUT /customer/123/tags/
{"tag_ids": [6, 7, 8]}

# Remove multiple tags at once
DELETE /customer/123/tags/
{"tag_ids": [1, 2, 3]}
```

### 2. Single Tag Operations
```python
# Add single tag
POST /customer/123/tags/1/

# Remove single tag
DELETE /customer/123/tags/1/
```

### 3. Clear All Tags
```python
# Remove all tags (keeps system tags)
PUT /customer/123/tags/
{"tag_ids": []}
```

### 4. WebSocket Integration
All tag operations trigger real-time updates:
```python
from message.websocket_utils import notify_customer_updated
notify_customer_updated(customer)
```

### 5. Swagger Documentation
All endpoints include Swagger/OpenAPI documentation with:
- Request/response schemas
- Parameter descriptions
- Error response codes
- Example values

---

## 📊 Usage Examples

### Example 1: Get Customer Tags
```bash
curl -X GET \
  'http://localhost:8000/api/v1/msg/customer/123/tags/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
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

### Example 2: Add Tags
```bash
curl -X POST \
  'http://localhost:8000/api/v1/msg/customer/123/tags/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"tag_ids": [1, 2, 3]}'
```

**Response:**
```json
{
    "message": "Successfully added 3 tag(s) to customer",
    "customer_id": 123,
    "tags": [...]
}
```

### Example 3: Replace Tags
```bash
curl -X PUT \
  'http://localhost:8000/api/v1/msg/customer/123/tags/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"tag_ids": [4, 5]}'
```

### Example 4: Remove Tags
```bash
curl -X DELETE \
  'http://localhost:8000/api/v1/msg/customer/123/tags/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"tag_ids": [1, 2]}'
```

---

## 🔄 Integration with Existing Code

### Works with Existing Models
```python
# Customer model (message/models.py)
class Customer(models.Model):
    tag = models.ManyToManyField(Tag, related_name='customers', blank=True)
    # ... other fields

# Tag model (message/models.py)
class Tag(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    # ... other fields
```

### Uses Existing Serializers
```python
from message.serializers import TagSerializer
```

### Triggers WebSocket Notifications
```python
from message.websocket_utils import notify_customer_updated
```

---

## 🎨 Frontend Integration

### React/Vue Example
```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1/msg',
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

// Get customer tags
const getCustomerTags = async (customerId) => {
    const { data } = await api.get(`/customer/${customerId}/tags/`);
    return data.tags;
};

// Add tags to customer
const addTags = async (customerId, tagIds) => {
    const { data } = await api.post(`/customer/${customerId}/tags/`, {
        tag_ids: tagIds
    });
    return data;
};

// Remove tags from customer
const removeTags = async (customerId, tagIds) => {
    const { data } = await api.delete(`/customer/${customerId}/tags/`, {
        data: { tag_ids: tagIds }
    });
    return data;
};
```

---

## 🧪 Testing

### Manual Testing
1. Start the Django server
2. Access Swagger UI at: `http://localhost:8000/swagger/`
3. Find the customer tags endpoints
4. Test with different scenarios

### Python Testing
```python
import requests

BASE_URL = "http://localhost:8000/api/v1/msg"
TOKEN = "your_auth_token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Test getting tags
response = requests.get(f"{BASE_URL}/customer/123/tags/", headers=headers)
assert response.status_code == 200

# Test adding tags
response = requests.post(
    f"{BASE_URL}/customer/123/tags/",
    headers=headers,
    json={"tag_ids": [1, 2, 3]}
)
assert response.status_code == 200
```

---

## 📝 Error Handling

### Common Errors

#### 400 Bad Request
- Invalid tag IDs
- Empty tag list when not allowed
- Attempting to remove system tags
- Tag already exists (for single tag add)

#### 403 Forbidden
- User doesn't have permission to access customer

#### 404 Not Found
- Customer not found
- Tag not found

---

## 🚀 Next Steps

### For Development
1. Deploy the changes to staging
2. Test all endpoints
3. Update frontend to use new APIs
4. Add integration tests

### For Production
1. Run migrations (if any)
2. Deploy to production
3. Monitor for errors
4. Update API documentation

---

## 📚 Files Created/Modified

### Created Files
1. `/src/message/api/customer_tags.py` - Main API implementation
2. `/src/message/CUSTOMER_TAGS_API_DOCS.md` - Complete documentation
3. `/src/message/CUSTOMER_TAGS_QUICK_REFERENCE.md` - Quick reference guide
4. `/CUSTOMER_TAGS_IMPLEMENTATION_SUMMARY.md` - This file

### Modified Files
1. `/src/message/urls.py` - Added new URL patterns

---

## ✨ Benefits

### For Developers
- ✅ Clean, well-documented API
- ✅ Comprehensive error handling
- ✅ Swagger documentation
- ✅ Type hints and validation
- ✅ Follows DRF best practices

### For Users
- ✅ Flexible tag management
- ✅ Real-time updates via WebSocket
- ✅ Bulk and single operations
- ✅ Protected system tags
- ✅ Clear error messages

### For Business
- ✅ Better customer organization
- ✅ Improved segmentation
- ✅ Enhanced filtering capabilities
- ✅ Scalable architecture

---

## 🎯 Conclusion

The Customer Tags Management API is now complete and ready for use. It provides a comprehensive solution for managing tags on customers with:

- ✅ 6 endpoints covering all use cases
- ✅ Full CRUD operations
- ✅ Robust security and validation
- ✅ Real-time WebSocket updates
- ✅ Complete documentation
- ✅ Ready for frontend integration

**Status:** ✅ Ready for testing and deployment

**Created:** 2025-10-29  
**Version:** 1.0

