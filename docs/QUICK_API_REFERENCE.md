# Workflow Template API - Quick Reference

## Base URL
```
/api/workflow-template/
```

## All Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/languages/` | GET | List all languages |
| `/types/` | GET | List all types |
| `/tags/` | GET | List all tags |
| `/templates/` | GET, POST | List/Create templates |
| `/templates/{id}/` | GET, PUT, PATCH, DELETE | Template details |
| `/templates/recent/` | GET | Recent templates |
| `/templates/search/` | GET | Advanced search |
| `/templates/statistics/` | GET | Template statistics |

## Common Query Parameters

### Pagination (All List Endpoints)
```
?page=1&page_size=20
```

### Search (Languages, Types, Tags, Templates)
```
?search=keyword
```

### Ordering (All List Endpoints)
```
?ordering=-created_at    # Descending
?ordering=name          # Ascending
```

### Status Filter (Templates)
```
?status=popular         # new, popular, none
```

### Active Filter (All)
```
?is_active=true        # true or false
```

## Quick Examples

### Get all templates with filters
```bash
GET /api/workflow-template/templates/?search=workflow&language_name=english&status=popular&page=1&page_size=20
```

### Get recent templates (limit 10)
```bash
GET /api/workflow-template/templates/recent/?limit=10
```

### Search templates with multiple filters
```bash
GET /api/workflow-template/templates/search/?q=automation&language=english&type=marketing&ordering=-created_at
```

### Get templates by date range
```bash
GET /api/workflow-template/templates/?created_at__gte=2024-01-01&created_at__lte=2024-12-31
```

### Create new template
```bash
POST /api/workflow-template/templates/
Content-Type: application/json

{
  "name": "My Template",
  "description": "Description here",
  "jsonfield": {},
  "language_id": "uuid-here",
  "type_id": "uuid-here",
  "status": "new"
}
```

## Filter Cheat Sheet

### Templates
- `search` - Search in name and description
- `name__icontains` - Filter by name
- `language` - Filter by language UUID
- `language_name` - Filter by language name
- `type` - Filter by type UUID
- `type_name` - Filter by type name
- `tag` - Filter by tag UUID
- `tag_name` - Filter by tag name
- `status` - Filter by status (new/popular/none)
- `is_active` - Filter by active status
- `created_at__gte` - Created after date
- `created_at__lte` - Created before date
- `ordering` - Sort results

### Languages, Types, Tags
- `search` - Full text search
- `name__icontains` - Filter by name
- `description__icontains` - Filter by description (types/tags)
- `is_active` - Filter by active status
- `ordering` - Sort results

## Response Format

### Paginated List
```json
{
  "count": 100,
  "next": "url-to-next-page",
  "previous": "url-to-previous-page",
  "results": [...]
}
```

### Single Object
```json
{
  "id": "uuid",
  "name": "Name",
  ...
}
```

## Status Codes
- `200` - Success (GET, PUT, PATCH)
- `201` - Created (POST)
- `204` - Deleted (DELETE)
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found

## Authentication
All endpoints require JWT token:
```
Authorization: Bearer <token>
```

