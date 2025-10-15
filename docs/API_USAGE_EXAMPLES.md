# WebKnowledge API Usage Examples

## ✅ Fixed: Website ID Now Returned

The issue where the website ID wasn't returned after creation has been fixed. Here are the updated API responses:

## 1. **Create Website (Standard Method)**

### Request:
```bash
POST /api/v1/web-knowledge/websites/
Content-Type: application/json
Authorization: Bearer YOUR_JWT_TOKEN

{
    "name": "My Company Website",
    "url": "https://example.com",
    "description": "Main company website",
    "max_pages": 50,
    "crawl_depth": 3,
    "include_external_links": false
}
```

### Response (NOW INCLUDES ID):
```json
{
    "success": true,
    "message": "Website source created successfully",
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "website": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "My Company Website",
        "url": "https://example.com",
        "description": "Main company website",
        "max_pages": 50,
        "crawl_depth": 3,
        "include_external_links": false,
        "crawl_status": "pending",
        "pages_crawled": 0,
        "total_qa_pairs": 0,
        "crawl_progress": 0.0,
        "created_at": "2024-01-15T10:30:00Z"
    },
    "next_steps": {
        "start_crawl_url": "/api/v1/web-knowledge/websites/123e4567-e89b-12d3-a456-426614174000/start_crawl/",
        "status_url": "/api/v1/web-knowledge/websites/123e4567-e89b-12d3-a456-426614174000/crawl_status/",
        "analytics_url": "/api/v1/web-knowledge/websites/123e4567-e89b-12d3-a456-426614174000/analytics/"
    }
}
```

## 2. **Create Website + Start Crawling (New One-Step Method)**

### Request:
```bash
POST /api/v1/web-knowledge/websites/create-and-crawl/
Content-Type: application/json
Authorization: Bearer YOUR_JWT_TOKEN

{
    "name": "My Company Website",
    "url": "https://example.com",
    "max_pages": 25,
    "crawl_depth": 2
}
```

### Response:
```json
{
    "success": true,
    "message": "Website created and crawl started successfully",
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "task_id": "celery-task-id-12345",
    "website": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "My Company Website",
        "url": "https://example.com",
        "crawl_status": "pending",
        "pages_crawled": 0,
        "total_qa_pairs": 0,
        "crawl_progress": 0.0,
        "created_at": "2024-01-15T10:30:00Z"
    },
    "urls": {
        "status": "/api/v1/web-knowledge/websites/123e4567-e89b-12d3-a456-426614174000/crawl_status/",
        "analytics": "/api/v1/web-knowledge/websites/123e4567-e89b-12d3-a456-426614174000/analytics/",
        "pages": "/api/v1/web-knowledge/pages/?website=123e4567-e89b-12d3-a456-426614174000",
        "qa_pairs": "/api/v1/web-knowledge/qa-pairs/?page__website=123e4567-e89b-12d3-a456-426614174000"
    }
}
```

## 3. **Check Crawl Status**

### Request:
```bash
GET /api/v1/web-knowledge/websites/123e4567-e89b-12d3-a456-426614174000/crawl_status/
Authorization: Bearer YOUR_JWT_TOKEN
```

### Response:
```json
{
    "website_id": "123e4567-e89b-12d3-a456-426614174000",
    "crawl_status": "crawling",
    "crawl_progress": 45.5,
    "pages_crawled": 23,
    "total_qa_pairs": 67,
    "last_crawl_at": "2024-01-15T10:35:00Z",
    "crawl_error_message": null,
    "latest_job": {
        "id": "job-uuid-123",
        "job_status": "running",
        "pages_crawled": 23,
        "qa_pairs_generated": 67,
        "progress_percentage": 45.5,
        "started_at": "2024-01-15T10:30:00Z"
    }
}
```

## 4. **JavaScript Frontend Example**

```javascript
// Create website and get ID for further operations
async function createWebsite(websiteData) {
    try {
        const response = await fetch('/api/v1/web-knowledge/websites/create-and-crawl/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwt_token}`
            },
            body: JSON.stringify(websiteData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Website created with ID:', result.id);
            
            // Start monitoring progress
            monitorCrawlProgress(result.id);
            
            return result.id; // Now you have the ID to use!
        } else {
            console.error('Error:', result.errors);
        }
    } catch (error) {
        console.error('Request failed:', error);
    }
}

// Monitor crawl progress
async function monitorCrawlProgress(websiteId) {
    const checkStatus = async () => {
        try {
            const response = await fetch(`/api/v1/web-knowledge/websites/${websiteId}/crawl_status/`, {
                headers: {
                    'Authorization': `Bearer ${jwt_token}`
                }
            });
            
            const status = await response.json();
            
            console.log(`Progress: ${status.crawl_progress}%`);
            console.log(`Pages crawled: ${status.pages_crawled}`);
            console.log(`Q&A pairs: ${status.total_qa_pairs}`);
            
            if (status.crawl_status === 'completed') {
                console.log('Crawl completed!');
                loadQAPairs(websiteId);
            } else if (status.crawl_status === 'crawling') {
                // Check again in 5 seconds
                setTimeout(checkStatus, 5000);
            }
        } catch (error) {
            console.error('Status check failed:', error);
        }
    };
    
    checkStatus();
}

// Load Q&A pairs for the website
async function loadQAPairs(websiteId) {
    try {
        const response = await fetch(`/api/v1/web-knowledge/qa-pairs/?page__website=${websiteId}`, {
            headers: {
                'Authorization': `Bearer ${jwt_token}`
            }
        });
        
        const qaPairs = await response.json();
        console.log('Q&A pairs:', qaPairs.results);
        
        // Display in UI...
    } catch (error) {
        console.error('Failed to load Q&A pairs:', error);
    }
}

// Usage
createWebsite({
    name: "My Website",
    url: "https://example.com",
    max_pages: 50,
    crawl_depth: 3
});
```

## 🎯 **Key Improvements**

1. **✅ ID Always Returned** - Both creation methods now return the website ID
2. **✅ Helpful URLs** - Response includes direct links to status, analytics, etc.
3. **✅ One-Step Creation** - New endpoint to create and start crawling immediately
4. **✅ Better Error Handling** - Clear success/failure indicators
5. **✅ Complete Data** - Full website object returned for immediate use

## 🚀 **Quick Commands**

```bash
# Create and immediately start crawling
curl -X POST /api/v1/web-knowledge/websites/create-and-crawl/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Site", "url": "https://example.com", "max_pages": 10}'

# Check status using returned ID
curl -X GET /api/v1/web-knowledge/websites/{WEBSITE_ID}/crawl_status/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search Q&A pairs
curl -X POST /api/v1/web-knowledge/search/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "business hours", "website_id": "{WEBSITE_ID}"}'
```

Now when you create a website, you'll immediately get the ID and all the information you need to use it!
