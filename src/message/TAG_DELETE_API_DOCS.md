# Tag Deletion API Documentation

Complete documentation for deleting tags in the message app.

---

## 📋 Overview

New endpoints have been added to delete Tag objects with proper permission checking and system tag protection.

### Base URL
```
/api/v1/msg/
```

### Authentication
All endpoints require authentication:
```
Authorization: Bearer <your_token>
```

### System Tags Protection
The following system tags **cannot be deleted**:
- `Telegram`
- `Whatsapp`
- `Instagram`

---

## 🎯 Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tags/<tag_id>/` | Get a specific tag |
| `PUT` | `/tags/<tag_id>/` | Update a tag |
| `DELETE` | `/tags/<tag_id>/` | Delete a single tag |
| `POST` | `/tags/bulk-delete/` | Delete multiple tags |

---

## 📚 API Reference

### 1. Get Single Tag

Get details of a specific tag by ID.

**Endpoint:** `GET /api/v1/msg/tags/<tag_id>/`

**Parameters:**
- `tag_id` (path, required): Tag ID

**Response (200 OK):**
```json
{
    "id": 1,
    "name": "VIP",
    "created_by": 5,
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `403 Forbidden`: User doesn't own this tag
- `404 Not Found`: Tag not found

---

### 2. Update Tag

Update a tag's name.

**Endpoint:** `PUT /api/v1/msg/tags/<tag_id>/`

**Parameters:**
- `tag_id` (path, required): Tag ID

**Request Body:**
```json
{
    "name": "VIP Plus"
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "name": "VIP Plus",
    "created_by": 5,
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid data
- `403 Forbidden`: User doesn't own this tag or it's a system tag
- `404 Not Found`: Tag not found

---

### 3. Delete Single Tag

Delete a specific tag by ID.

**Endpoint:** `DELETE /api/v1/msg/tags/<tag_id>/`

**Parameters:**
- `tag_id` (path, required): Tag ID

**Response (200 OK):**
```json
{
    "message": "Tag 'VIP' deleted successfully",
    "tag_name": "VIP"
}
```

**Error Responses:**
- `403 Forbidden`: User doesn't own this tag or it's a system tag
- `404 Not Found`: Tag not found

**Example:**
```bash
curl -X DELETE \
  'http://localhost:8000/api/v1/msg/tags/1/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

---

### 4. Bulk Delete Tags

Delete multiple tags at once.

**Endpoint:** `POST /api/v1/msg/tags/bulk-delete/`

**Request Body:**
```json
{
    "tag_ids": [1, 2, 3]
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully deleted 3 tag(s)",
    "deleted_count": 3,
    "deleted_tags": ["VIP", "Premium", "Active"],
    "skipped_tags": []
}
```

**Response with Skipped Tags:**
```json
{
    "message": "Successfully deleted 2 tag(s)",
    "deleted_count": 2,
    "deleted_tags": ["VIP", "Premium"],
    "skipped_tags": [
        "Telegram",
        "Tag IDs not found or not owned: [99, 100]"
    ]
}
```

**Error Responses:**
- `400 Bad Request`: Invalid tag_ids format

**Example:**
```bash
curl -X POST \
  'http://localhost:8000/api/v1/msg/tags/bulk-delete/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "tag_ids": [1, 2, 3]
  }'
```

---

## 🔒 Permission Rules

### Ownership
- ✅ Users can only delete tags they created
- ❌ Users cannot delete tags created by others

### System Tags
- ❌ System tags (`Telegram`, `Whatsapp`, `Instagram`) cannot be deleted
- ❌ System tags cannot be updated
- ✅ System tags are automatically excluded in bulk delete

---

## 🧪 Usage Examples

### Example 1: Delete a Single Tag

```bash
# Get tag ID first
curl -X GET \
  'http://localhost:8000/api/v1/msg/tags?search=vip' \
  -H 'Authorization: Bearer YOUR_TOKEN'

# Delete the tag
curl -X DELETE \
  'http://localhost:8000/api/v1/msg/tags/1/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Example 2: Bulk Delete Tags

```bash
curl -X POST \
  'http://localhost:8000/api/v1/msg/tags/bulk-delete/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "tag_ids": [1, 2, 3, 4, 5]
  }'
```

### Example 3: Update Tag Name

```bash
curl -X PUT \
  'http://localhost:8000/api/v1/msg/tags/1/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "VIP Plus"
  }'
```

---

## 💻 Python Examples

### Delete Single Tag

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/msg"
TOKEN = "your_auth_token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Delete tag
tag_id = 1
response = requests.delete(
    f"{BASE_URL}/tags/{tag_id}/",
    headers=headers
)

if response.status_code == 200:
    print(f"Success: {response.json()['message']}")
else:
    print(f"Error: {response.json()}")
```

### Bulk Delete Tags

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/msg"
TOKEN = "your_auth_token"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Bulk delete
tag_ids = [1, 2, 3]
response = requests.post(
    f"{BASE_URL}/tags/bulk-delete/",
    headers=headers,
    json={"tag_ids": tag_ids}
)

result = response.json()
print(f"Deleted: {result['deleted_count']} tags")
print(f"Deleted tags: {result['deleted_tags']}")
if 'skipped_tags' in result:
    print(f"Skipped: {result['skipped_tags']}")
```

### Update Tag

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/msg"
TOKEN = "your_auth_token"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Update tag name
tag_id = 1
response = requests.put(
    f"{BASE_URL}/tags/{tag_id}/",
    headers=headers,
    json={"name": "VIP Plus"}
)

if response.status_code == 200:
    print(f"Updated: {response.json()}")
```

---

## 🌐 JavaScript/Axios Examples

### Delete Single Tag

```javascript
import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/v1/msg';
const TOKEN = 'your_auth_token';

const deleteTag = async (tagId) => {
    try {
        const response = await axios.delete(
            `${BASE_URL}/tags/${tagId}/`,
            {
                headers: {
                    'Authorization': `Bearer ${TOKEN}`
                }
            }
        );
        console.log('Success:', response.data.message);
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
};

// Usage
deleteTag(1);
```

### Bulk Delete Tags

```javascript
const bulkDeleteTags = async (tagIds) => {
    try {
        const response = await axios.post(
            `${BASE_URL}/tags/bulk-delete/`,
            { tag_ids: tagIds },
            {
                headers: {
                    'Authorization': `Bearer ${TOKEN}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        console.log('Deleted:', response.data.deleted_count, 'tags');
        console.log('Deleted tags:', response.data.deleted_tags);
        
        if (response.data.skipped_tags) {
            console.log('Skipped:', response.data.skipped_tags);
        }
        
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
};

// Usage
bulkDeleteTags([1, 2, 3, 4, 5]);
```

---

## ⚠️ Important Notes

### 1. Cascading Deletes

When a tag is deleted:
- ✅ Tag is removed from all customers
- ✅ Tag is removed from ManyToMany relationships
- ✅ No data loss - only the tag association is removed

### 2. Cannot Delete System Tags

System tags are protected:
```bash
# This will fail
DELETE /api/v1/msg/tags/telegram_tag_id/

# Response
{
    "error": "System tags cannot be modified or deleted"
}
```

### 3. Ownership Validation

Users can only delete their own tags:
```bash
# Trying to delete another user's tag
DELETE /api/v1/msg/tags/someone_elses_tag_id/

# Response
{
    "error": "You don't have permission to modify this tag"
}
```

### 4. Bulk Delete Behavior

Bulk delete is smart:
- ✅ Skips system tags automatically
- ✅ Skips tags user doesn't own
- ✅ Deletes only valid, owned tags
- ✅ Returns detailed report of what was deleted/skipped

---

## 🔍 Error Handling

### Common Errors

#### 400 Bad Request
```json
{
    "error": "tag_ids must be a list of integers"
}
```

```json
{
    "error": "tag_ids cannot be empty"
}
```

#### 403 Forbidden
```json
{
    "error": "You don't have permission to modify this tag"
}
```

```json
{
    "error": "System tags cannot be modified or deleted"
}
```

#### 404 Not Found
```json
{
    "error": "Tag not found"
}
```

---

## 🎯 Use Cases

### Use Case 1: Clean Up Old Tags

```python
# Get all tags
tags = get_all_tags()

# Find tags with no customers
unused_tags = [tag['id'] for tag in tags if tag['customer_count'] == 0]

# Bulk delete
bulk_delete_tags(unused_tags)
```

### Use Case 2: Rename a Tag

```python
# Update tag name instead of delete + create
update_tag(tag_id=1, new_name="VIP Premium")
```

### Use Case 3: Delete Multiple Tags by Name

```python
# Search tags by name
tags_to_delete = []
for name in ['Old Tag', 'Unused Tag', 'Test Tag']:
    tags = search_tags(name)
    tags_to_delete.extend([t['id'] for t in tags])

# Bulk delete
bulk_delete_tags(tags_to_delete)
```

---

## 📊 Complete Tag Management Workflow

### 1. List Tags
```bash
GET /api/v1/msg/tags
```

### 2. Search Tags
```bash
GET /api/v1/msg/tags?search=vip
```

### 3. Create Tags
```bash
POST /api/v1/msg/tags
{"names": ["VIP", "Premium"]}
```

### 4. Get Single Tag
```bash
GET /api/v1/msg/tags/1/
```

### 5. Update Tag
```bash
PUT /api/v1/msg/tags/1/
{"name": "VIP Plus"}
```

### 6. Delete Single Tag
```bash
DELETE /api/v1/msg/tags/1/
```

### 7. Bulk Delete Tags
```bash
POST /api/v1/msg/tags/bulk-delete/
{"tag_ids": [1, 2, 3]}
```

---

## 🔄 Migration from Old System

If you have old code that needs updating:

### Before (No Delete Endpoint)
```python
# Had to use Django admin or database directly
```

### After (With Delete Endpoint)
```python
import requests

# Single delete
requests.delete(f"{BASE_URL}/tags/{tag_id}/", headers=headers)

# Bulk delete
requests.post(
    f"{BASE_URL}/tags/bulk-delete/",
    json={"tag_ids": [1, 2, 3]},
    headers=headers
)
```

---

## ✅ Testing

### Manual Testing

1. **Create test tags:**
   ```bash
   curl -X POST 'http://localhost:8000/api/v1/msg/tags' \
     -H 'Authorization: Bearer TOKEN' \
     -H 'Content-Type: application/json' \
     -d '{"names": ["Test1", "Test2", "Test3"]}'
   ```

2. **List tags to get IDs:**
   ```bash
   curl -X GET 'http://localhost:8000/api/v1/msg/tags' \
     -H 'Authorization: Bearer TOKEN'
   ```

3. **Delete single tag:**
   ```bash
   curl -X DELETE 'http://localhost:8000/api/v1/msg/tags/1/' \
     -H 'Authorization: Bearer TOKEN'
   ```

4. **Bulk delete:**
   ```bash
   curl -X POST 'http://localhost:8000/api/v1/msg/tags/bulk-delete/' \
     -H 'Authorization: Bearer TOKEN' \
     -H 'Content-Type: application/json' \
     -d '{"tag_ids": [2, 3]}'
   ```

---

## 📚 Related Documentation

- **Tag APIs:** `TAG_SEARCH_GUIDE.md` - Tag search and filtering
- **Customer Tags:** `CUSTOMER_TAGS_API_DOCS.md` - Customer tag management
- **Workflow Tags:** `WORKFLOW_TAG_FIX_SUMMARY.md` - Workflow tag usage

---

**Created:** 2025-10-29  
**Version:** 1.0  
**Status:** ✅ Ready to use

