# Customer Bulk Operations API Documentation

This document describes the Customer Bulk Delete and Export APIs that allow selective operations on customers with filtering support.

## Overview

The Customer Bulk APIs provide two main functionalities:
1. **Bulk Delete**: Delete multiple customers based on ID list with filtering support
2. **Bulk Export**: Export customers to CSV format for download with filtering support

Both APIs respect user permissions and support the same filtering system as the customer list view.

## Authentication

All APIs require authentication. Include the authorization header:
```
Authorization: Bearer <your-token>
```

## Base URL
```
/message/customers/
```

---

## 1. Bulk Delete API

### Endpoint
```
POST /message/customers/bulk-delete/
```

### Description
Delete multiple customers based on their IDs. When filters are applied in the frontend, they will be respected in the deletion process.

### Request Body
```json
{
  "customer_ids": [1, 2, 3, 4]  // Optional: Array of customer IDs to delete
}
```

**Note**: If `customer_ids` is empty or not provided, ALL customers matching the applied filters will be deleted.

### Query Parameters (Filters)
You can apply the same filters as the customer list:

- **Search**: `?search=john` (searches in first_name, last_name, phone_number, description)
- **Source Filter**: `?source=telegram`
- **Email Filter**: `?email=test@example.com`
- **Tag Filter**: `?tag__name=vip`
- **Date Filters**: 
  - `?created_at=2024-01-01`
  - `?updated_at=2024-01-01`
- **Ordering**: `?ordering=-created_at` (newest first)

### Example Requests

#### Delete Specific Customers
```bash
curl -X POST "http://localhost:8000/message/customers/bulk-delete/" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"customer_ids": [1, 2, 3]}'
```

#### Delete All Telegram Customers
```bash
curl -X POST "http://localhost:8000/message/customers/bulk-delete/?source=telegram" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Delete Customers with Search Filter
```bash
curl -X POST "http://localhost:8000/message/customers/bulk-delete/?search=john" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"customer_ids": []}'
```

### Response

#### Success (200 OK)
```json
{
  "message": "Successfully deleted 3 customer(s)",
  "deleted_count": 3
}
```

#### No Customers Found (200 OK)
```json
{
  "message": "No customers found matching the criteria",
  "deleted_count": 0
}
```

#### Error (400 Bad Request)
```json
{
  "error": "customer_ids must be a list of integers"
}
```

---

## 2. Bulk Export API

### Endpoint
```
POST /message/customers/bulk-export/
```

### Description
Export customers to CSV format. When filters are applied in the frontend, they will be respected in the export process.

### Request Body
```json
{
  "customer_ids": [1, 2, 3, 4]  // Optional: Array of customer IDs to export
}
```

**Note**: If `customer_ids` is empty or not provided, ALL customers matching the applied filters will be exported.

### Query Parameters (Filters)
Same filtering options as the delete API (see above).

### Example Requests

#### Export Specific Customers
```bash
curl -X POST "http://localhost:8000/message/customers/bulk-export/" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"customer_ids": [1, 2, 3]}' \
  --output customers_export.csv
```

#### Export All VIP Tagged Customers
```bash
curl -X POST "http://localhost:8000/message/customers/bulk-export/?tag__name=vip" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{}' \
  --output vip_customers.csv
```

#### Export Recent Customers (Last 30 days)
```bash
curl -X POST "http://localhost:8000/message/customers/bulk-export/?created_at__gte=2024-01-01&ordering=-created_at" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{}' \
  --output recent_customers.csv
```

### Response

#### Success (200 OK)
- **Content-Type**: `text/csv`
- **Content-Disposition**: `attachment; filename="customers_export_YYYYMMDD_HHMMSS.csv"`
- **Body**: CSV file content

#### Error (400 Bad Request)
```json
{
  "error": "No customers found matching the criteria"
}
```

### CSV Format

The exported CSV includes the following columns:

| Column | Description |
|--------|-------------|
| ID | Customer ID |
| First Name | Customer's first name |
| Last Name | Customer's last name |
| Username | Customer's username |
| Email | Customer's email address |
| Phone Number | Customer's phone number |
| Description | Customer description |
| Source | Customer source (telegram, instagram, unknown) |
| Source ID | External source ID |
| Tags | Comma-separated list of tags |
| Created At | Creation timestamp (YYYY-MM-DD HH:MM:SS) |
| Updated At | Last update timestamp (YYYY-MM-DD HH:MM:SS) |

### Example CSV Output
```csv
ID,First Name,Last Name,Username,Email,Phone Number,Description,Source,Source ID,Tags,Created At,Updated At
1,John,Doe,johndoe,john@example.com,+1234567890,VIP Customer,telegram,123456789,vip,premium,2024-01-15 10:30:00,2024-01-20 14:45:00
2,Jane,Smith,janesmith,jane@example.com,+0987654321,Regular Customer,instagram,987654321,regular,2024-01-16 11:00:00,2024-01-21 09:15:00
```

---

## Frontend Integration

### React/JavaScript Example

```javascript
// Bulk Delete
const deleteCustomers = async (customerIds = [], filters = {}) => {
  const queryParams = new URLSearchParams(filters).toString();
  const url = `/message/customers/bulk-delete/?${queryParams}`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ customer_ids: customerIds })
  });
  
  return await response.json();
};

// Bulk Export
const exportCustomers = async (customerIds = [], filters = {}) => {
  const queryParams = new URLSearchParams(filters).toString();
  const url = `/message/customers/bulk-export/?${queryParams}`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ customer_ids: customerIds })
  });
  
  // Handle file download
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = `customers_export_${Date.now()}.csv`;
  a.click();
  window.URL.revokeObjectURL(downloadUrl);
};

// Usage Examples
// Delete selected customers
await deleteCustomers([1, 2, 3]);

// Delete all telegram customers
await deleteCustomers([], { source: 'telegram' });

// Export VIP customers
await exportCustomers([], { tag__name: 'vip' });

// Export customers matching search
await exportCustomers([], { search: 'john' });
```

---

## Security Considerations

1. **User Isolation**: Users can only delete/export customers they have conversations with
2. **Authentication Required**: All endpoints require valid authentication
3. **Input Validation**: Customer IDs are validated to ensure they are integers
4. **Permission Checks**: Each customer is checked for user permission before operation

---

## Error Handling

### Common Error Codes

| Code | Description | Response |
|------|-------------|----------|
| 400 | Invalid customer_ids format | `{"error": "customer_ids must be a list of integers"}` |
| 400 | Invalid ID values | `{"error": "All customer IDs must be valid integers"}` |
| 400 | No customers found | `{"error": "No customers found matching the criteria"}` |
| 401 | Unauthorized | `{"detail": "Authentication credentials were not provided."}` |
| 403 | Forbidden | `{"error": "You don't have permission to access this customer"}` |

---

## Performance Notes

1. **Filtering**: Filters are applied at the database level for optimal performance
2. **Bulk Operations**: Both APIs use efficient bulk operations to minimize database queries
3. **Memory Usage**: CSV export streams data to avoid memory issues with large datasets
4. **WebSocket Notifications**: Delete operations trigger real-time notifications for UI updates

---

## Rate Limiting

Consider implementing rate limiting for bulk operations to prevent abuse:
- Recommended: 10 requests per minute for bulk operations
- Large exports (>1000 customers) should be queued for background processing

---

## Testing

### Test Cases to Verify

1. **Delete with specific IDs**
2. **Delete with filters only**
3. **Delete with both IDs and filters**
4. **Export with specific IDs**
5. **Export with filters only**
6. **Export with both IDs and filters**
7. **Error handling for invalid IDs**
8. **Permission checks for unauthorized customers**
9. **Empty result handling**
10. **Large dataset handling (1000+ customers)**

### Sample Test Data
```bash
# Create test customers
POST /message/customers/
# Apply various filters
# Test bulk operations
# Verify results
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-XX | Initial implementation of bulk delete and export APIs |
