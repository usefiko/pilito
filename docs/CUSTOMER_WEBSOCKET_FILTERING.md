# Customer WebSocket Enhanced Filtering Documentation

## Overview

The `CustomerListConsumer` WebSocket has been enhanced with comprehensive filtering capabilities to provide better customer segmentation and management. This document covers all available filters and how to use them.

## WebSocket Endpoint

Connect to: `ws/customers/`

## Supported Message Types

### 1. Get Customers with Filters
```javascript
{
  "type": "get_customers",
  "filters": {
    // Filter options here
  }
}
```

### 2. Refresh Customer List
```javascript
{
  "type": "refresh_customers", 
  "filters": {
    // Filter options here
  }
}
```

### 3. Filter Customers (Advanced)
```javascript
{
  "type": "filter_customers",
  "filters": {
    // Filter options here
  }
}
```

### 4. Search Customers (Legacy Support)
```javascript
{
  "type": "search_customers",
  "search_term": "john doe"
}
```

### 5. Get Available Filter Options
```javascript
{
  "type": "get_filter_options"
}
```

## Available Filters

### 🔍 Text Search
Search across multiple fields:
```javascript
{
  "type": "filter_customers",
  "filters": {
    "search": "john doe"
  }
}
```
**Searches in:** first_name, last_name, username, email, phone_number

### 📧 Email Presence Filter
Filter customers by email availability:
```javascript
{
  "type": "filter_customers",
  "filters": {
    "has_email": "true"    // Has email
    // "has_email": "false" // No email
    // "has_email": "all"   // All customers
  }
}
```

### 📱 Phone Number Presence Filter
Filter customers by phone number availability:
```javascript
{
  "type": "filter_customers",
  "filters": {
    "has_phone": "true"    // Has phone
    // "has_phone": "false" // No phone
    // "has_phone": "all"   // All customers
  }
}
```

### 🏷️ Tag Filters
Filter by customer tags (supports both names and IDs):
```javascript
{
  "type": "filter_customers",
  "filters": {
    "tags": ["VIP", "Premium"],        // Filter by tag names
    "tag_ids": [1, 2, 3]              // Filter by tag IDs
  }
}
```

### 📱 Source Filter
Filter by customer source platform:
```javascript
{
  "type": "filter_customers",
  "filters": {
    "source": "telegram"
    // Options: "telegram", "instagram", "unknown", "all"
  }
}
```

### 💬 Conversation Status Filter
Filter by conversation status:
```javascript
{
  "type": "filter_customers",
  "filters": {
    "conversation_status": "active"
    // Options: "active", "support_active", "marketing_active", "closed"
  }
}
```

### 📩 Unread Messages Filter
Filter customers with/without unread messages:
```javascript
{
  "type": "filter_customers",
  "filters": {
    "has_unread": "true"    // Has unread messages
    // "has_unread": "false" // No unread messages
    // "has_unread": "all"   // All customers
  }
}
```

### 📅 Date Range Filters

#### Customer Creation Date
```javascript
{
  "type": "filter_customers",
  "filters": {
    "date_from": "2023-01-01",
    "date_to": "2023-12-31"
  }
}
```

#### Last Activity Date
```javascript
{
  "type": "filter_customers",
  "filters": {
    "last_activity_from": "2023-01-01",
    "last_activity_to": "2023-12-31"
  }
}
```

### 📊 Sorting Options
```javascript
{
  "type": "filter_customers",
  "filters": {
    "order_by": "-created_at"
    // Options: "created_at", "-created_at", "updated_at", 
    //          "-updated_at", "first_name", "-first_name"
  }
}
```

## Complex Filter Examples

### Example 1: VIP Customers with Email
```javascript
{
  "type": "filter_customers",
  "filters": {
    "tags": ["VIP"],
    "has_email": "true",
    "order_by": "-updated_at"
  }
}
```

### Example 2: Telegram Customers with Unread Messages
```javascript
{
  "type": "filter_customers",
  "filters": {
    "source": "telegram",
    "has_unread": "true",
    "conversation_status": "active"
  }
}
```

### Example 3: Customers Without Contact Info
```javascript
{
  "type": "filter_customers",
  "filters": {
    "has_email": "false",
    "has_phone": "false"
  }
}
```

### Example 4: Recent Active Instagram Customers
```javascript
{
  "type": "filter_customers",
  "filters": {
    "source": "instagram",
    "last_activity_from": "2023-11-01",
    "conversation_status": "active",
    "order_by": "-updated_at"
  }
}
```

## Response Structure

### Customer List Response
```javascript
{
  "type": "customers_list",
  "customers": [
    {
      "id": "customer_id",
      "first_name": "John",
      "last_name": "Doe", 
      "username": "johndoe",
      "email": "john@example.com",
      "phone_number": "+1234567890",
      "source": "telegram",
      "source_id": "telegram_user_123",
      "profile_picture": "/media/customer_img/profile.jpg",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z",
      "tags": [
        {"id": 1, "name": "VIP"},
        {"id": 2, "name": "Premium"}
      ],
      "conversations": [
        {
          "id": "conversation_id",
          "title": "Support Chat",
          "status": "active",
          "source": "telegram",
          "last_message": {
            "id": "message_id",
            "content": "Hello, I need help!",
            "type": "customer",
            "is_ai_response": false,
            "created_at": "2023-01-01T12:00:00Z"
          },
          "unread_count": 2,
          "created_at": "2023-01-01T10:00:00Z",
          "updated_at": "2023-01-01T12:00:00Z"
        }
      ]
    }
  ],
  "pagination": {
    "count": 150,
    "page_count": 10,
    "page_size": 10,
    "page": 1,
    "total_pages": 15,
    "has_next": true,
    "has_previous": false,
    "offset": 0,
    "limit": 10
  },
  "filters": {
    "has_email": "true",
    "source": "telegram"
  },
  "count": 150,
  "timestamp": "2023-01-01T12:00:00Z"
}
```

### Filter Options Response
```javascript
{
  "type": "filter_options",
  "options": {
    "sources": ["telegram", "instagram", "unknown"],
    "tags": ["VIP", "Premium", "New Customer", "Support"],
    "conversation_statuses": ["active", "support_active", "marketing_active", "closed"],
    "has_email_options": [
      {"value": "true", "label": "Has Email"},
      {"value": "false", "label": "No Email"},
      {"value": "all", "label": "All"}
    ],
    "has_phone_options": [
      {"value": "true", "label": "Has Phone"},
      {"value": "false", "label": "No Phone"},
      {"value": "all", "label": "All"}
    ],
    "has_unread_options": [
      {"value": "true", "label": "Has Unread Messages"},
      {"value": "false", "label": "No Unread Messages"},
      {"value": "all", "label": "All"}
    ],
    "order_options": [
      {"value": "-updated_at", "label": "Recently Updated"},
      {"value": "-created_at", "label": "Recently Created"},
      {"value": "created_at", "label": "Oldest First"},
      {"value": "first_name", "label": "Name A-Z"},
      {"value": "-first_name", "label": "Name Z-A"}
    ]
  },
  "timestamp": "2023-01-01T12:00:00Z"
}
```

## Pagination

The WebSocket supports pagination with these parameters in filters:
```javascript
{
  "type": "get_customers",
  "filters": {
    "page": 1,
    "page_size": 20,
    // other filters...
  }
}
```

## Error Handling

### Common Error Response
```javascript
{
  "type": "error",
  "message": "Error description",
  "timestamp": "2023-01-01T12:00:00Z"
}
```

### Timeout Errors
```javascript
{
  "type": "error", 
  "message": "Request timeout - please try again",
  "timestamp": "2023-01-01T12:00:00Z"
}
```

## Frontend Integration Examples

### React/JavaScript Example
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/customers/');

// Send filter request
const filterCustomers = (filters) => {
  ws.send(JSON.stringify({
    type: 'filter_customers',
    filters: filters
  }));
};

// Usage examples
filterCustomers({
  has_email: 'true',
  source: 'telegram',
  tags: ['VIP']
});

// Get filter options
ws.send(JSON.stringify({
  type: 'get_filter_options'
}));

// Handle responses
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'customers_list') {
    console.log('Customers:', data.customers);
    console.log('Total count:', data.count);
  } else if (data.type === 'filter_options') {
    console.log('Available filters:', data.options);
  } else if (data.type === 'error') {
    console.error('Error:', data.message);
  }
};
```

### jQuery Example
```javascript
// Initialize WebSocket
var socket = new WebSocket('ws://localhost:8000/ws/customers/');

// Filter customers with email and phone
function filterContactableCustomers() {
  socket.send(JSON.stringify({
    type: 'filter_customers',
    filters: {
      has_email: 'true',
      has_phone: 'true',
      order_by: '-updated_at'
    }
  }));
}

// Filter customers by tag
function filterByTag(tagName) {
  socket.send(JSON.stringify({
    type: 'filter_customers',
    filters: {
      tags: [tagName]
    }
  }));
}
```

## Performance Considerations

1. **Query Optimization**: All filters use optimized database queries with proper indexing
2. **Timeout Protection**: 10-second timeout for customer queries, 5-second for filter options
3. **Result Limiting**: Filter options are limited to prevent excessive memory usage
4. **Pagination**: Use pagination for large datasets to improve performance

## Best Practices

1. **Combine Filters**: Use multiple filters together for precise customer segmentation
2. **Use Pagination**: Always implement pagination for better user experience
3. **Handle Errors**: Implement proper error handling for timeout and connection issues
4. **Cache Filter Options**: Cache filter options on the frontend to reduce WebSocket calls
5. **Debounce Search**: Implement debouncing for search input to reduce server load

## Migration Notes

- All existing filter functionality remains unchanged
- New filters are additive and don't break existing implementations
- Legacy `search_customers` message type is still supported
- Filter options are dynamically generated based on user's actual data

## Troubleshooting

### Common Issues

1. **No Results**: Check if filters are too restrictive
2. **Timeout Errors**: Reduce filter complexity or check database performance
3. **Invalid Filters**: Ensure filter values match expected formats
4. **Connection Issues**: Verify WebSocket authentication and connection

### Debug Tips

1. Use `get_filter_options` to see available values
2. Start with simple filters and add complexity gradually
3. Check browser console for WebSocket connection errors
4. Verify user authentication for WebSocket connection
