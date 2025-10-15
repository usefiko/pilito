# WebKnowledge Pages API Documentation

## 🆕 New API Endpoints for Website Pages

I've added new functionality to get detailed information about website pages after crawling is completed.

## 1. **Get All Pages for a Website (Detailed)**

### Endpoint:
```
GET /api/v1/web-knowledge/websites/{website_id}/pages/
```

### Description:
Get all pages for a specific website with complete details including Q&A statistics.

### Response Example:
```json
{
    "website_id": "123e4567-e89b-12d3-a456-426614174000",
    "website_name": "My Company Website",
    "website_url": "https://example.com",
    "total_pages": 25,
    "pages": [
        {
            "id": "page-uuid-123",
            "url": "https://example.com/about",
            "title": "About Us - Company Information",
            "summary": "Our company has been serving customers since 1995...",
            "word_count": 1250,
            "processing_status": "completed",
            "processing_error": null,
            "meta_description": "Learn about our company history and mission",
            "meta_keywords": "company, history, mission, values",
            "h1_tags": ["About Our Company"],
            "h2_tags": ["Our History", "Our Mission", "Our Team"],
            "links_count": 15,
            "crawled_at": "2024-01-15T10:30:00Z",
            "processed_at": "2024-01-15T10:32:00Z",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:32:00Z",
            "qa_pairs": {
                "total": 8,
                "average_confidence": 0.92,
                "featured_count": 2
            }
        },
        {
            "id": "page-uuid-456",
            "url": "https://example.com/services",
            "title": "Our Services - What We Offer",
            "summary": "We provide comprehensive solutions including...",
            "word_count": 980,
            "processing_status": "completed",
            "processing_error": null,
            "meta_description": "Explore our comprehensive service offerings",
            "meta_keywords": "services, solutions, consulting",
            "h1_tags": ["Our Services"],
            "h2_tags": ["Consulting", "Development", "Support"],
            "links_count": 12,
            "crawled_at": "2024-01-15T10:31:00Z",
            "processed_at": "2024-01-15T10:33:00Z",
            "created_at": "2024-01-15T10:31:00Z",
            "updated_at": "2024-01-15T10:33:00Z",
            "qa_pairs": {
                "total": 6,
                "average_confidence": 0.88,
                "featured_count": 1
            }
        }
    ],
    "summary": {
        "total_words": 24750,
        "completed_pages": 23,
        "failed_pages": 2,
        "total_qa_pairs": 152,
        "pages_with_qa": 20
    }
}
```

## 2. **Enhanced Websites List (Now Includes Page Titles)**

### Endpoint:
```
GET /api/v1/web-knowledge/websites/
```

### Description:
The websites list API now includes page titles and basic page information.

### Response Example:
```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "My Company Website",
            "url": "https://example.com",
            "description": "Main company website",
            "crawl_status": "completed",
            "pages_crawled": 25,
            "total_qa_pairs": 152,
            "crawl_progress": 100.0,
            "page_titles": [
                {
                    "id": "page-uuid-123",
                    "title": "About Us - Company Information",
                    "url": "https://example.com/about",
                    "word_count": 1250,
                    "qa_pairs_count": 8,
                    "crawled_at": "2024-01-15T10:30:00Z"
                },
                {
                    "id": "page-uuid-456",
                    "title": "Our Services - What We Offer",
                    "url": "https://example.com/services",
                    "word_count": 980,
                    "qa_pairs_count": 6,
                    "crawled_at": "2024-01-15T10:31:00Z"
                }
            ],
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:35:00Z"
        }
    ]
}
```

## 3. **Filter Pages by Website**

### Endpoint:
```
GET /api/v1/web-knowledge/pages/?website={website_id}
```

### Description:
Get all pages filtered by a specific website.

### Query Parameters:
- `website` - Filter by website ID
- `status` - Filter by processing status (`pending`, `processing`, `completed`, `failed`)

### Examples:
```bash
# Get all pages for a specific website
GET /api/v1/web-knowledge/pages/?website=123e4567-e89b-12d3-a456-426614174000

# Get only completed pages for a website
GET /api/v1/web-knowledge/pages/?website=123e4567-e89b-12d3-a456-426614174000&status=completed

# Get all failed pages across all websites
GET /api/v1/web-knowledge/pages/?status=failed
```

## 4. **Usage Examples**

### JavaScript Example:
```javascript
// Get all pages for a website with full details
async function getWebsitePages(websiteId) {
    try {
        const response = await fetch(`/api/v1/web-knowledge/websites/${websiteId}/pages/`, {
            headers: {
                'Authorization': `Bearer ${jwt_token}`
            }
        });
        
        const data = await response.json();
        
        console.log(`Website: ${data.website_name}`);
        console.log(`Total pages: ${data.total_pages}`);
        console.log(`Total words: ${data.summary.total_words}`);
        console.log(`Total Q&A pairs: ${data.summary.total_qa_pairs}`);
        
        // Display pages
        data.pages.forEach(page => {
            console.log(`- ${page.title} (${page.qa_pairs.total} Q&A pairs)`);
        });
        
        return data;
    } catch (error) {
        console.error('Error fetching pages:', error);
    }
}

// Get websites with page titles
async function getWebsitesWithPages() {
    try {
        const response = await fetch('/api/v1/web-knowledge/websites/', {
            headers: {
                'Authorization': `Bearer ${jwt_token}`
            }
        });
        
        const data = await response.json();
        
        data.results.forEach(website => {
            console.log(`\nWebsite: ${website.name}`);
            console.log(`Status: ${website.crawl_status}`);
            console.log(`Pages crawled: ${website.pages_crawled}`);
            
            console.log('Recent pages:');
            website.page_titles.forEach(page => {
                console.log(`  - ${page.title} (${page.qa_pairs_count} Q&A)`);
            });
        });
        
        return data;
    } catch (error) {
        console.error('Error fetching websites:', error);
    }
}
```

### cURL Examples:
```bash
# Get detailed pages for a website
curl -X GET /api/v1/web-knowledge/websites/123e4567-e89b-12d3-a456-426614174000/pages/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get websites with page titles
curl -X GET /api/v1/web-knowledge/websites/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter pages by website and status
curl -X GET "/api/v1/web-knowledge/pages/?website=123e4567-e89b-12d3-a456-426614174000&status=completed" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🎯 **Key Features**

✅ **Complete Page Details** - Get all page information including content, metadata, and Q&A statistics
✅ **Page Titles in Website List** - See recent page titles directly in the websites API
✅ **Advanced Filtering** - Filter pages by website and processing status
✅ **Summary Statistics** - Get aggregate data about words, Q&A pairs, and completion status
✅ **Optimized Queries** - Efficient database queries with proper prefetching

## 📊 **Data Structure**

Each page includes:
- **Basic Info**: ID, URL, title, summary
- **Content Stats**: Word count, processing status
- **SEO Data**: Meta description, keywords, headings
- **Structure**: Links count, H1/H2 tags
- **Q&A Analytics**: Total pairs, confidence scores, featured count
- **Timestamps**: Crawled, processed, created, updated

This gives you complete visibility into what was crawled and processed for each website!
