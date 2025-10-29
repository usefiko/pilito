# Customer Tags Management API Documentation

Complete API documentation for managing tags on customers in the message app.

## Table of Contents
- [Overview](#overview)
- [Endpoints](#endpoints)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)

---

## Overview

The Customer Tags Management API provides endpoints to manage tags associated with customers. All endpoints require authentication and ensure that users can only manage tags for customers they have conversations with.

### Base URL
```
/api/v1/msg/
```

### Authentication
All endpoints require authentication using Bearer token:
```
Authorization: Bearer <your_token>
```

### System Tags
The following tags are considered system tags and cannot be removed:
- `Telegram`
- `Whatsapp`
- `Instagram`

These tags are automatically managed by the system based on the customer's source.

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/customer/<customer_id>/tags/` | Get all tags for a customer |
| POST | `/customer/<customer_id>/tags/` | Add tags to a customer (keeps existing) |
| PUT | `/customer/<customer_id>/tags/` | Replace all customer tags |
| DELETE | `/customer/<customer_id>/tags/` | Remove specific tags from customer |
| POST | `/customer/<customer_id>/tags/<tag_id>/` | Add a single tag to customer |
| DELETE | `/customer/<customer_id>/tags/<tag_id>/` | Remove a single tag from customer |

---

## API Reference

### 1. Get Customer Tags

Get all tags associated with a specific customer.

**Endpoint:** `GET /customer/<customer_id>/tags/`

**Parameters:**
- `customer_id` (path, required): Customer ID

**Response (200 OK):**
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
            "id": 2,
            "name": "Premium",
            "created_by": 5,
            "created_at": "2024-01-16T14:20:00Z"
        }
    ]
}
```

**Error Responses:**
- `403 Forbidden`: User doesn't have permission to access this customer
- `404 Not Found`: Customer not found

---

### 2. Add Tags to Customer

Add one or more tags to a customer without removing existing tags.

**Endpoint:** `POST /customer/<customer_id>/tags/`

**Parameters:**
- `customer_id` (path, required): Customer ID

**Request Body:**
```json
{
    "tag_ids": [1, 2, 3]
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully added 3 tag(s) to customer",
    "customer_id": 123,
    "tags": [
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
        },
        {
            "id": 3,
            "name": "Enterprise",
            "created_by": 5,
            "created_at": "2024-01-17T09:15:00Z"
        }
    ]
}
```

**Error Responses:**
- `400 Bad Request`: Invalid tag IDs or empty list
- `403 Forbidden`: User doesn't have permission to access this customer
- `404 Not Found`: Customer not found

---

### 3. Replace Customer Tags

Replace all customer tags with a new set of tags. This removes all existing tags (except system tags) and adds the new ones.

**Endpoint:** `PUT /customer/<customer_id>/tags/`

**Parameters:**
- `customer_id` (path, required): Customer ID

**Request Body:**
```json
{
    "tag_ids": [4, 5]
}
```

**To remove all tags, send an empty array:**
```json
{
    "tag_ids": []
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully replaced customer tags with 2 tag(s)",
    "customer_id": 123,
    "tags": [
        {
            "id": 4,
            "name": "Gold Member",
            "created_by": 5,
            "created_at": "2024-01-18T11:00:00Z"
        },
        {
            "id": 5,
            "name": "Loyal Customer",
            "created_by": 5,
            "created_at": "2024-01-19T15:30:00Z"
        }
    ]
}
```

**Error Responses:**
- `400 Bad Request`: Invalid tag IDs or missing tag_ids field
- `403 Forbidden`: User doesn't have permission to access this customer
- `404 Not Found`: Customer not found

---

### 4. Remove Tags from Customer

Remove specific tags from a customer.

**Endpoint:** `DELETE /customer/<customer_id>/tags/`

**Parameters:**
- `customer_id` (path, required): Customer ID

**Request Body:**
```json
{
    "tag_ids": [1, 2]
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully removed 2 tag(s) from customer",
    "customer_id": 123,
    "tags": [
        {
            "id": 3,
            "name": "Enterprise",
            "created_by": 5,
            "created_at": "2024-01-17T09:15:00Z"
        }
    ]
}
```

**Error Responses:**
- `400 Bad Request`: Invalid tag IDs, empty list, or attempting to remove system tags
- `403 Forbidden`: User doesn't have permission to access this customer
- `404 Not Found`: Customer not found

---

### 5. Add Single Tag to Customer

Add a single tag to a customer.

**Endpoint:** `POST /customer/<customer_id>/tags/<tag_id>/`

**Parameters:**
- `customer_id` (path, required): Customer ID
- `tag_id` (path, required): Tag ID to add

**Response (200 OK):**
```json
{
    "message": "Successfully added tag \"VIP\" to customer",
    "customer_id": 123,
    "tag": {
        "id": 1,
        "name": "VIP",
        "created_by": 5,
        "created_at": "2024-01-15T10:30:00Z"
    }
}
```

**Error Responses:**
- `400 Bad Request`: Tag already exists on customer
- `403 Forbidden`: User doesn't have permission to access this customer
- `404 Not Found`: Customer or tag not found

---

### 6. Remove Single Tag from Customer

Remove a single tag from a customer.

**Endpoint:** `DELETE /customer/<customer_id>/tags/<tag_id>/`

**Parameters:**
- `customer_id` (path, required): Customer ID
- `tag_id` (path, required): Tag ID to remove

**Response (200 OK):**
```json
{
    "message": "Successfully removed tag \"VIP\" from customer",
    "customer_id": 123
}
```

**Error Responses:**
- `400 Bad Request`: Cannot remove system tag or tag doesn't exist on customer
- `403 Forbidden`: User doesn't have permission to access this customer
- `404 Not Found`: Customer or tag not found

---

## Usage Examples

### Example 1: Get Customer Tags

```bash
curl -X GET \
  'http://localhost:8000/api/v1/msg/customer/123/tags/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Example 2: Add Multiple Tags to Customer

```bash
curl -X POST \
  'http://localhost:8000/api/v1/msg/customer/123/tags/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "tag_ids": [1, 2, 3]
  }'
```

### Example 3: Replace All Customer Tags

```bash
curl -X PUT \
  'http://localhost:8000/api/v1/msg/customer/123/tags/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "tag_ids": [4, 5]
  }'
```

### Example 4: Remove All Tags from Customer

```bash
curl -X PUT \
  'http://localhost:8000/api/v1/msg/customer/123/tags/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "tag_ids": []
  }'
```

### Example 5: Remove Specific Tags from Customer

```bash
curl -X DELETE \
  'http://localhost:8000/api/v1/msg/customer/123/tags/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "tag_ids": [1, 2]
  }'
```

### Example 6: Add Single Tag to Customer

```bash
curl -X POST \
  'http://localhost:8000/api/v1/msg/customer/123/tags/1/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Example 7: Remove Single Tag from Customer

```bash
curl -X DELETE \
  'http://localhost:8000/api/v1/msg/customer/123/tags/1/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
    "error": "tag_ids must be a list of integers"
}
```

```json
{
    "error": "Invalid tag IDs: [10, 15]"
}
```

```json
{
    "error": "Cannot remove system tags (Telegram, Whatsapp, Instagram)"
}
```

#### 403 Forbidden
```json
{
    "error": "You don't have permission to access this customer"
}
```

#### 404 Not Found
```json
{
    "error": "Customer not found"
}
```

```json
{
    "error": "Tag with ID 99 not found"
}
```

---

## WebSocket Notifications

All tag management operations trigger WebSocket notifications to update the frontend in real-time. When tags are modified, a `customer_updated` event is sent to all connected clients with access to that customer.

---

## Best Practices

1. **Use Batch Operations**: When adding/removing multiple tags, use the batch endpoints (`POST/DELETE /customer/<id>/tags/`) instead of multiple single-tag operations.

2. **Validate Tag IDs**: Always validate that tag IDs exist before making requests to avoid errors.

3. **Handle System Tags**: Never attempt to remove system tags (Telegram, Whatsapp, Instagram) - they are managed automatically.

4. **Check Permissions**: Ensure users have conversations with the customer before attempting to modify tags.

5. **Use PUT for Complete Replacement**: When you need to completely change a customer's tags, use `PUT` instead of multiple `POST/DELETE` operations.

---

## Related APIs

### Create Tags
Before assigning tags to customers, you need to create them:

**Endpoint:** `POST /api/v1/msg/tags`

**Request:**
```json
{
    "names": ["VIP", "Premium", "Enterprise"]
}
```

### List All Tags
Get all available tags:

**Endpoint:** `GET /api/v1/msg/tags`

---

## Changelog

### Version 1.0 (2025-10-29)
- Initial release
- Added customer tag management endpoints
- Support for bulk and single tag operations
- WebSocket integration for real-time updates
- System tag protection

---

## Support

For issues or questions, please contact the development team or create an issue in the project repository.

