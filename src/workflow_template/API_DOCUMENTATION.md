# Workflow Template API Documentation

This document provides comprehensive documentation for the Workflow Template APIs with full search, pagination, and filtering capabilities.

## Table of Contents
- [Authentication](#authentication)
- [Pagination](#pagination)
- [Languages API](#languages-api)
- [Types API](#types-api)
- [Tags API](#tags-api)
- [Templates API](#templates-api)
- [Response Formats](#response-formats)
- [Error Handling](#error-handling)

## Authentication

All endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Pagination

All list endpoints support pagination with the following parameters:

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | integer | 1 | - | Page number |
| `page_size` | integer | 10 | 500 | Number of items per page |

### Paginated Response Format

```json
{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=3",
  "previous": "http://api.example.com/endpoint/?page=1",
  "results": [...]
}
```

---

## Languages API

### List Languages

**Endpoint:** `GET /api/workflow-template/languages/`

**Description:** Get a paginated list of active languages with filtering and search capabilities.

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Search in language names | `?search=eng` |
| `name__icontains` | string | Filter by name (case-insensitive) | `?name__icontains=english` |
| `is_active` | boolean | Filter by active status | `?is_active=true` |
| `ordering` | string | Sort results | `?ordering=-created_at` |
| `page` | integer | Page number | `?page=1` |
| `page_size` | integer | Items per page | `?page_size=20` |

#### Ordering Options
- `name` / `-name`
- `created_at` / `-created_at`

#### Example Request

```bash
curl -X GET "http://api.example.com/api/workflow-template/languages/?search=eng&ordering=name&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Example Response

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "English",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

## Types API

### List Types

**Endpoint:** `GET /api/workflow-template/types/`

**Description:** Get a paginated list of active workflow types with filtering and search.

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Search in type names and descriptions | `?search=automation` |
| `name__icontains` | string | Filter by name (case-insensitive) | `?name__icontains=automation` |
| `description__icontains` | string | Filter by description | `?description__icontains=sales` |
| `is_active` | boolean | Filter by active status | `?is_active=true` |
| `ordering` | string | Sort results | `?ordering=-created_at` |
| `page` | integer | Page number | `?page=1` |
| `page_size` | integer | Items per page | `?page_size=20` |

#### Ordering Options
- `name` / `-name`
- `created_at` / `-created_at`

#### Example Request

```bash
curl -X GET "http://api.example.com/api/workflow-template/types/?search=automation&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Example Response

```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Sales Automation",
      "description": "Automated sales workflows",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

## Tags API

### List Tags

**Endpoint:** `GET /api/workflow-template/tags/`

**Description:** Get a paginated list of active tags with filtering and search.

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Search in tag names and descriptions | `?search=marketing` |
| `name__icontains` | string | Filter by name (case-insensitive) | `?name__icontains=marketing` |
| `description__icontains` | string | Filter by description | `?description__icontains=email` |
| `is_active` | boolean | Filter by active status | `?is_active=true` |
| `ordering` | string | Sort results | `?ordering=-created_at` |
| `page` | integer | Page number | `?page=1` |
| `page_size` | integer | Items per page | `?page_size=20` |

#### Ordering Options
- `name` / `-name`
- `created_at` / `-created_at`

#### Example Request

```bash
curl -X GET "http://api.example.com/api/workflow-template/tags/?search=marketing&ordering=name" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Templates API

### List Templates

**Endpoint:** `GET /api/workflow-template/templates/`

**Description:** Get a paginated list of workflow templates with comprehensive filtering, search, and sorting.

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Multi-field search in names and descriptions | `?search=automation` |
| `name__icontains` | string | Filter by template name | `?name__icontains=email` |
| `description__icontains` | string | Filter by description | `?description__icontains=workflow` |
| `language` | UUID | Filter by language UUID | `?language=550e8400-e29b-41d4-a716-446655440000` |
| `language_name` | string | Filter by language name | `?language_name=english` |
| `type` | UUID | Filter by type UUID | `?type=550e8400-e29b-41d4-a716-446655440001` |
| `type_name` | string | Filter by type name | `?type_name=automation` |
| `tag` | UUID | Filter by tag UUID | `?tag=550e8400-e29b-41d4-a716-446655440002` |
| `tag_name` | string | Filter by tag name | `?tag_name=marketing` |
| `status` | string | Filter by status (new, popular, none) | `?status=popular` |
| `is_active` | boolean | Filter by active status | `?is_active=true` |
| `created_at__gte` | datetime | Created on or after date | `?created_at__gte=2024-01-01` |
| `created_at__lte` | datetime | Created on or before date | `?created_at__lte=2024-12-31` |
| `updated_at__gte` | datetime | Updated on or after date | `?updated_at__gte=2024-01-01` |
| `updated_at__lte` | datetime | Updated on or before date | `?updated_at__lte=2024-12-31` |
| `ordering` | string | Sort results | `?ordering=-created_at` |
| `page` | integer | Page number | `?page=1` |
| `page_size` | integer | Items per page | `?page_size=20` |

#### Ordering Options
- `name` / `-name`
- `created_at` / `-created_at`
- `updated_at` / `-updated_at`

#### Example Requests

**1. Basic search with pagination:**
```bash
curl -X GET "http://api.example.com/api/workflow-template/templates/?search=workflow&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**2. Filter by language and status:**
```bash
curl -X GET "http://api.example.com/api/workflow-template/templates/?language_name=english&status=popular&ordering=-created_at" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**3. Date range filter:**
```bash
curl -X GET "http://api.example.com/api/workflow-template/templates/?created_at__gte=2024-01-01&created_at__lte=2024-12-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**4. Multiple filters combined:**
```bash
curl -X GET "http://api.example.com/api/workflow-template/templates/?language_name=english&type_name=automation&status=popular&is_active=true&ordering=-created_at&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Example Response

```json
{
  "count": 50,
  "next": "http://api.example.com/api/workflow-template/templates/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "Email Marketing Workflow",
      "description": "Automated email marketing campaign",
      "language_name": "English",
      "type_name": "Marketing Automation",
      "tag_name": "Email",
      "status": "popular",
      "cover_image": "http://example.com/media/templates/cover1.jpg",
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

---

### Create Template

**Endpoint:** `POST /api/workflow-template/templates/`

**Description:** Create a new workflow template.

#### Request Body

```json
{
  "name": "Email Marketing Workflow",
  "description": "Automated email marketing campaign",
  "jsonfield": {
    "nodes": [],
    "edges": []
  },
  "language_id": "550e8400-e29b-41d4-a716-446655440000",
  "type_id": "550e8400-e29b-41d4-a716-446655440001",
  "tag_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "new",
  "is_active": true
}
```

#### Example Request

```bash
curl -X POST "http://api.example.com/api/workflow-template/templates/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Email Marketing Workflow",
    "description": "Automated email marketing campaign",
    "jsonfield": {},
    "language_id": "550e8400-e29b-41d4-a716-446655440000",
    "type_id": "550e8400-e29b-41d4-a716-446655440001",
    "status": "new"
  }'
```

---

### Get Template Details

**Endpoint:** `GET /api/workflow-template/templates/{id}/`

**Description:** Get detailed information about a specific template.

#### Example Request

```bash
curl -X GET "http://api.example.com/api/workflow-template/templates/550e8400-e29b-41d4-a716-446655440003/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Example Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "name": "Email Marketing Workflow",
  "description": "Automated email marketing campaign",
  "jsonfield": {
    "nodes": [],
    "edges": []
  },
  "language": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "English",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "type": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Marketing Automation",
    "description": "Marketing workflows",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "tag": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Email",
    "description": "Email related workflows",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "status": "popular",
  "cover_image": "http://example.com/media/templates/cover1.jpg",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

---

### Update Template

**Endpoint:** `PUT /api/workflow-template/templates/{id}/` or `PATCH /api/workflow-template/templates/{id}/`

**Description:** Update an existing template (PUT for full update, PATCH for partial update).

#### Example Request (PATCH)

```bash
curl -X PATCH "http://api.example.com/api/workflow-template/templates/550e8400-e29b-41d4-a716-446655440003/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "popular",
    "is_active": true
  }'
```

---

### Delete Template

**Endpoint:** `DELETE /api/workflow-template/templates/{id}/`

**Description:** Delete a template.

#### Example Request

```bash
curl -X DELETE "http://api.example.com/api/workflow-template/templates/550e8400-e29b-41d4-a716-446655440003/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Recent Templates

**Endpoint:** `GET /api/workflow-template/templates/recent/`

**Description:** Get recently created templates with optional pagination.

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `page` | integer | Page number | `?page=1` |
| `page_size` | integer | Items per page | `?page_size=20` |
| `limit` | integer | Max results (overrides pagination) | `?limit=10` |

#### Example Request

```bash
curl -X GET "http://api.example.com/api/workflow-template/templates/recent/?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Search Templates

**Endpoint:** `GET /api/workflow-template/templates/search/`

**Description:** Advanced template search with multiple filters and pagination.

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Search query | `?q=automation` |
| `language` | string | Filter by language name | `?language=english` |
| `type` | string | Filter by type name | `?type=automation` |
| `tag` | string | Filter by tag name | `?tag=marketing` |
| `status` | string | Filter by status | `?status=popular` |
| `is_active` | boolean | Filter by active status | `?is_active=true` |
| `ordering` | string | Sort results | `?ordering=-created_at` |
| `page` | integer | Page number | `?page=1` |
| `page_size` | integer | Items per page | `?page_size=20` |

#### Example Request

```bash
curl -X GET "http://api.example.com/api/workflow-template/templates/search/?q=automation&language=english&status=popular&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Template Statistics

**Endpoint:** `GET /api/workflow-template/templates/statistics/`

**Description:** Get overall template statistics.

#### Example Request

```bash
curl -X GET "http://api.example.com/api/workflow-template/templates/statistics/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Example Response

```json
{
  "total_templates": 150,
  "active_templates": 120,
  "language_distribution": [
    {
      "language__name": "English",
      "count": 60
    },
    {
      "language__name": "Persian",
      "count": 40
    }
  ],
  "type_distribution": [
    {
      "type__name": "Marketing Automation",
      "count": 50
    },
    {
      "type__name": "Sales Automation",
      "count": 30
    }
  ]
}
```

---

## Response Formats

### Success Response (List)
```json
{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

### Success Response (Single Object)
```json
{
  "id": "...",
  "field1": "value1",
  ...
}
```

### Success Response (Create/Update)
```json
{
  "id": "...",
  "field1": "value1",
  ...
}
```

### Success Response (Delete)
```
HTTP 204 No Content
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message",
  "field_name": ["Field-specific error message"]
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Successful GET, PUT, PATCH request |
| 201 | Created | Successful POST request |
| 204 | No Content | Successful DELETE request |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | User doesn't have permission |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

---

## Frontend Integration Examples

### React/JavaScript Example

```javascript
// Fetch templates with filters
const fetchTemplates = async (filters = {}) => {
  const params = new URLSearchParams({
    page: filters.page || 1,
    page_size: filters.pageSize || 10,
    ...(filters.search && { search: filters.search }),
    ...(filters.language && { language_name: filters.language }),
    ...(filters.status && { status: filters.status }),
    ...(filters.ordering && { ordering: filters.ordering || '-created_at' })
  });

  const response = await fetch(
    `${API_BASE_URL}/api/workflow-template/templates/?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch templates');
  }

  return await response.json();
};

// Usage
const templates = await fetchTemplates({
  page: 1,
  pageSize: 20,
  search: 'automation',
  language: 'english',
  status: 'popular',
  ordering: '-created_at'
});
```

### Axios Example

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Authorization': `Bearer ${authToken}`
  }
});

// Fetch templates
const getTemplates = async (params) => {
  const response = await api.get('/api/workflow-template/templates/', { params });
  return response.data;
};

// Usage
const result = await getTemplates({
  page: 1,
  page_size: 20,
  search: 'workflow',
  language_name: 'english',
  status: 'popular',
  ordering: '-created_at'
});
```

---

## Best Practices

1. **Always use pagination** for list endpoints to improve performance
2. **Use specific filters** instead of broad searches when possible
3. **Cache frequently accessed data** (languages, types, tags)
4. **Handle errors gracefully** with proper error messages to users
5. **Use ordering** to present data in a meaningful way
6. **Implement debouncing** for search inputs to reduce API calls
7. **Store and reuse** filter states for better UX

---

## Support

For any issues or questions regarding the API, please contact the backend team or create an issue in the project repository.

