# Workflow Template Module

## Overview
Complete workflow template management system with comprehensive API support for languages, types, tags, and templates with full search, pagination, and filtering capabilities.

## Features ✨

- ✅ **Full Pagination** - All list endpoints support pagination
- ✅ **Advanced Search** - Search across multiple fields
- ✅ **Comprehensive Filtering** - Filter by any field with multiple options
- ✅ **Flexible Sorting** - Order by any field in ascending/descending order
- ✅ **Date Range Filters** - Filter by creation and update dates
- ✅ **RESTful API** - Full CRUD operations
- ✅ **Well Documented** - Complete API documentation included

## Quick Start

### Basic API Calls

```bash
# Get all templates with pagination
GET /api/workflow-template/templates/?page=1&page_size=20

# Search templates
GET /api/workflow-template/templates/?search=automation

# Filter by language and status
GET /api/workflow-template/templates/?language_name=english&status=popular

# Get recent templates
GET /api/workflow-template/templates/recent/?limit=10

# Advanced search with multiple filters
GET /api/workflow-template/templates/search/?q=workflow&language=english&status=popular
```

## API Endpoints

### Languages
- `GET /api/workflow-template/languages/` - List all languages

### Types
- `GET /api/workflow-template/types/` - List all types

### Tags
- `GET /api/workflow-template/tags/` - List all tags

### Templates
- `GET /api/workflow-template/templates/` - List templates
- `POST /api/workflow-template/templates/` - Create template
- `GET /api/workflow-template/templates/{id}/` - Get template details
- `PUT /api/workflow-template/templates/{id}/` - Update template (full)
- `PATCH /api/workflow-template/templates/{id}/` - Update template (partial)
- `DELETE /api/workflow-template/templates/{id}/` - Delete template

### Utility Endpoints
- `GET /api/workflow-template/templates/recent/` - Recent templates
- `GET /api/workflow-template/templates/search/` - Advanced search
- `GET /api/workflow-template/templates/statistics/` - Template statistics

## Common Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `page` | integer | Page number | `?page=1` |
| `page_size` | integer | Items per page (max: 500) | `?page_size=20` |
| `search` | string | Search query | `?search=automation` |
| `ordering` | string | Sort field | `?ordering=-created_at` |
| `status` | string | Template status | `?status=popular` |
| `is_active` | boolean | Active filter | `?is_active=true` |

## Filter Options

### Templates
- `search` - Multi-field search
- `name__icontains` - Name filter
- `description__icontains` - Description filter
- `language` - Language UUID
- `language_name` - Language name
- `type` - Type UUID
- `type_name` - Type name
- `tag` - Tag UUID
- `tag_name` - Tag name
- `status` - Status (new/popular/none)
- `is_active` - Active status
- `created_at__gte` - Created after date
- `created_at__lte` - Created before date
- `updated_at__gte` - Updated after date
- `updated_at__lte` - Updated before date

## Documentation Files

| File | Description |
|------|-------------|
| `API_DOCUMENTATION.md` | Complete API reference with examples |
| `QUICK_API_REFERENCE.md` | Quick reference cheat sheet |
| `IMPLEMENTATION_SUMMARY.md` | Technical implementation details |
| `README.md` | This file - Quick overview |

## Module Structure

```
workflow_template/
├── __init__.py
├── admin.py                    # Django admin configuration
├── apps.py                     # App configuration
├── filters.py                  # Advanced filter classes (NEW)
├── models.py                   # Data models
├── serializers.py              # API serializers
├── urls.py                     # URL routing
├── views.py                    # API views (ENHANCED)
├── migrations/                 # Database migrations
├── API_DOCUMENTATION.md        # Complete API docs (NEW)
├── QUICK_API_REFERENCE.md      # Quick reference (NEW)
├── IMPLEMENTATION_SUMMARY.md   # Implementation details (NEW)
└── README.md                   # This file (NEW)
```

## Models

### Language
- `id` (UUID)
- `name` (String)
- `is_active` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Type
- `id` (UUID)
- `name` (String)
- `description` (Text)
- `is_active` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Tag
- `id` (UUID)
- `name` (String)
- `description` (Text)
- `is_active` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Template
- `id` (UUID)
- `name` (String)
- `description` (Text)
- `jsonfield` (JSON)
- `language` (ForeignKey)
- `type` (ForeignKey)
- `tag` (ForeignKey, nullable)
- `status` (Choice: new/popular/none)
- `cover_image` (ImageField, nullable)
- `is_active` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)

## Response Format

### Paginated List Response
```json
{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

### Template List Item
```json
{
  "id": "uuid",
  "name": "Template Name",
  "description": "Description",
  "language_name": "English",
  "type_name": "Automation",
  "tag_name": "Marketing",
  "status": "popular",
  "cover_image": "url",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Template Detail
```json
{
  "id": "uuid",
  "name": "Template Name",
  "description": "Description",
  "jsonfield": {},
  "language": {...},
  "type": {...},
  "tag": {...},
  "status": "popular",
  "cover_image": "url",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Frontend Integration

### Example Usage (JavaScript/React)

```javascript
// Fetch templates with filters
const fetchTemplates = async (filters) => {
  const params = new URLSearchParams({
    page: filters.page || 1,
    page_size: filters.pageSize || 10,
    ...(filters.search && { search: filters.search }),
    ...(filters.language && { language_name: filters.language }),
    ...(filters.status && { status: filters.status }),
    ordering: filters.ordering || '-created_at'
  });

  const response = await fetch(
    `${API_URL}/api/workflow-template/templates/?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );

  return await response.json();
};

// Usage
const result = await fetchTemplates({
  page: 1,
  pageSize: 20,
  search: 'automation',
  language: 'english',
  status: 'popular',
  ordering: '-created_at'
});

console.log(result.count); // Total count
console.log(result.results); // Array of templates
```

## Authentication

All endpoints require authentication. Include JWT token in headers:

```
Authorization: Bearer <your_jwt_token>
```

## Status Codes

- `200 OK` - Successful GET, PUT, PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing/invalid authentication
- `403 Forbidden` - No permission
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Best Practices

1. **Use Pagination** - Always paginate large lists
2. **Implement Debouncing** - Debounce search inputs (300-500ms)
3. **Cache Static Data** - Cache languages, types, tags lists
4. **Handle Errors** - Implement proper error handling
5. **Use Specific Filters** - Use specific filters instead of broad searches
6. **Store Filter State** - Save filter state in URL params for shareability

## Performance Tips

- Use `page_size` appropriately (10-50 items recommended)
- Cache language/type/tag lists as they rarely change
- Use specific filters to reduce result sets
- Implement frontend caching where appropriate

## Testing

### Test the API

```bash
# Test basic listing
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/workflow-template/templates/

# Test with filters
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/workflow-template/templates/?search=test&page=1&page_size=10"

# Test recent templates
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/workflow-template/templates/recent/?limit=5

# Test statistics
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/workflow-template/templates/statistics/
```

## Troubleshooting

### Common Issues

**Issue:** No results returned
- Check if `is_active=true` filter is appropriate
- Verify authentication token is valid
- Check if data exists in database

**Issue:** Pagination not working
- Ensure `page` and `page_size` parameters are integers
- Check if `page_size` exceeds maximum (500)

**Issue:** Filters not working
- Verify filter parameter names are correct
- Check if values match expected format (UUID, boolean, etc.)
- Use `name__icontains` for case-insensitive string matching

## Support & Questions

For detailed API documentation, see `API_DOCUMENTATION.md`

For quick reference, see `QUICK_API_REFERENCE.md`

For implementation details, see `IMPLEMENTATION_SUMMARY.md`

## Version History

### v2.0.0 (October 1, 2025)
- ✅ Added comprehensive pagination
- ✅ Added advanced filtering
- ✅ Enhanced search capabilities
- ✅ Added sorting/ordering
- ✅ Added date range filters
- ✅ Created comprehensive documentation
- ✅ Fixed URL routing order

### v1.0.0 (Initial Release)
- Basic CRUD operations
- Simple filtering
- Basic serializers

