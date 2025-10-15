# Web Knowledge Page Delete API Documentation

## 📋 Overview

The Web Knowledge Pages API already includes **DELETE functionality** for individual pages. This endpoint allows users to delete specific website pages along with all their associated Q&A pairs.

## 🚀 API Endpoint

**URL:** `DELETE {{base_url}}/api/v1/web-knowledge/pages/{page_id}/`  
**Method:** `DELETE`  
**Authentication:** Required (Bearer Token)  
**Content-Type:** `application/json`

## 📡 Request Details

### URL Parameters
- `page_id` (UUID): The unique identifier of the page to delete
  - Example: `f952823c-22c9-46a7-b661-75ef37d015e9`

### Headers
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

## 📨 Request Examples

### Using cURL
```bash
curl -X DELETE "{{base_url}}/api/v1/web-knowledge/pages/f952823c-22c9-46a7-b661-75ef37d015e9/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Using JavaScript (Fetch)
```javascript
const response = await fetch('{{base_url}}/api/v1/web-knowledge/pages/f952823c-22c9-46a7-b661-75ef37d015e9/', {
  method: 'DELETE',
  headers: {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  }
});

const result = await response.json();
console.log(result);
```

### Using Python (requests)
```python
import requests

url = "{{base_url}}/api/v1/web-knowledge/pages/f952823c-22c9-46a7-b661-75ef37d015e9/"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}

response = requests.delete(url, headers=headers)
result = response.json()
print(result)
```

## 📦 Response Structure

### ✅ Success Response (200 OK)
```json
{
  "success": true,
  "message": "Page \"Example Page Title\" and 5 Q&A pairs deleted successfully",
  "deleted_data": {
    "page": {
      "id": "f952823c-22c9-46a7-b661-75ef37d015e9",
      "title": "Example Page Title",
      "url": "https://example.com/page",
      "qa_pairs_count": 5
    },
    "qa_pairs_deleted": 5
  }
}
```

### ❌ Error Responses

#### 404 Not Found
```json
{
  "detail": "Not found."
}
```

#### 403 Permission Denied
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## 🔒 Security & Permissions

### Authentication
- **Required**: Valid Bearer token in Authorization header
- **User Verification**: Users can only delete pages from their own websites

### Permission Checks
1. User must be authenticated
2. Page must exist
3. Page must belong to a website owned by the requesting user

## 🗑️ What Gets Deleted

When you delete a page, the following data is **permanently removed**:

### ✅ Cascading Deletions
1. **The Page Record**: Complete page information
2. **All Q&A Pairs**: Every question-answer pair associated with the page
3. **Related Metadata**: Processing status, crawl data, etc.

### ⚠️ Data Loss Warning
- **This action is irreversible**
- All Q&A pairs generated for this page will be lost
- Page content and metadata will be permanently deleted

## 📊 Response Data Explanation

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indicates successful deletion |
| `message` | string | Human-readable confirmation message |
| `deleted_data.page.id` | string | UUID of the deleted page |
| `deleted_data.page.title` | string | Title of the deleted page |
| `deleted_data.page.url` | string | URL of the deleted page |
| `deleted_data.page.qa_pairs_count` | number | Number of Q&A pairs that were on the page |
| `deleted_data.qa_pairs_deleted` | number | Actual count of Q&A pairs deleted |

## 🔧 Implementation Details

### ViewSet Information
- **Class**: `WebsitePageViewSet`
- **Method**: `destroy()`
- **Location**: `src/web_knowledge/views.py`
- **Router**: Handled by Django REST Framework router

### Database Operations
- Uses Django ORM cascade deletion
- Atomic transaction ensures data integrity
- Statistics collected before deletion for response

## 🧪 Testing Examples

### Test Scenario 1: Successful Deletion
```bash
# Delete an existing page
curl -X DELETE "http://localhost:8000/api/v1/web-knowledge/pages/f952823c-22c9-46a7-b661-75ef37d015e9/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected: 200 OK with deletion confirmation
```

### Test Scenario 2: Page Not Found
```bash
# Try to delete non-existent page
curl -X DELETE "http://localhost:8000/api/v1/web-knowledge/pages/00000000-0000-0000-0000-000000000000/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected: 404 Not Found
```

### Test Scenario 3: Permission Denied
```bash
# Try to delete another user's page
curl -X DELETE "http://localhost:8000/api/v1/web-knowledge/pages/OTHER_USER_PAGE_ID/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected: 404 Not Found (filtered by ownership)
```

## 🌐 Frontend Integration

### React Example
```javascript
const deletePage = async (pageId) => {
  try {
    const response = await fetch(`/api/v1/web-knowledge/pages/${pageId}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const result = await response.json();
      console.log('Page deleted:', result.message);
      // Update UI - remove page from list
      setPages(pages.filter(page => page.id !== pageId));
      
      // Show success notification
      showNotification(`${result.deleted_data.qa_pairs_deleted} Q&A pairs deleted with page`);
    } else {
      const error = await response.json();
      console.error('Delete failed:', error.detail);
    }
  } catch (error) {
    console.error('Delete error:', error);
  }
};
```

### Vue.js Example
```javascript
async deletePage(pageId) {
  try {
    const response = await this.$http.delete(`/api/v1/web-knowledge/pages/${pageId}/`);
    
    // Success
    this.$message.success(response.data.message);
    
    // Remove from local state
    this.pages = this.pages.filter(page => page.id !== pageId);
    
    // Update statistics
    this.totalQaPairs -= response.data.deleted_data.qa_pairs_deleted;
    
  } catch (error) {
    this.$message.error('Failed to delete page');
  }
}
```

## 🔗 Related Endpoints

### Get All Pages
- `GET /api/v1/web-knowledge/pages/`
- List all pages for the user

### Get Single Page  
- `GET /api/v1/web-knowledge/pages/{page_id}/`
- Get detailed information about a specific page

### Update Page
- `PUT/PATCH /api/v1/web-knowledge/pages/{page_id}/`
- Update page information

### Get Page Q&A Pairs
- `GET /api/v1/web-knowledge/qa-pairs/?page={page_id}`
- Get all Q&A pairs for a specific page

## 📈 Monitoring & Analytics

### Metrics to Track
- Pages deleted per user
- Q&A pairs lost due to page deletion  
- Most frequently deleted page types
- User deletion patterns

### Logging
The system logs page deletions for audit purposes:
```
INFO: Page "Example Page" (f952823c-22c9-46a7-b661-75ef37d015e9) deleted by user 123 with 5 Q&A pairs
```

## 🛡️ Best Practices

### For API Consumers
1. **Confirm Before Delete**: Always show confirmation dialog
2. **Backup Important Data**: Export Q&A pairs if needed
3. **Update UI Immediately**: Remove deleted pages from lists
4. **Handle Errors Gracefully**: Show appropriate error messages

### For Developers
1. **Check Ownership**: Verify user owns the page
2. **Atomic Operations**: Use transactions for data integrity
3. **Audit Logging**: Log deletion activities
4. **Soft Delete Option**: Consider implementing soft deletes for recovery

---

## ✅ Status Summary

- **Endpoint Status**: ✅ **FULLY IMPLEMENTED AND WORKING**
- **Authentication**: ✅ Required and enforced
- **Permissions**: ✅ User ownership verification
- **Documentation**: ✅ Complete with Swagger annotations
- **Error Handling**: ✅ Comprehensive error responses
- **Testing**: ✅ Ready for testing

The delete functionality for web-knowledge pages is **already available and fully functional** at the endpoint you specified! 🎉
