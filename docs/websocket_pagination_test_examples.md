# WebSocket Pagination Testing Examples

## 🔧 Fixed Issues:
1. **Query String Parameters**: Now supports pagination parameters in WebSocket URL
2. **Message Body Parameters**: Also supports pagination parameters in JSON message
3. **Debugging**: Added logging to track parameter processing
4. **Priority**: Message body parameters override query string parameters

## 📋 Testing Methods:

### Method 1: Query String Parameters (Your Current Method) ✅
```
URL: ws://api.pilito.com/ws/customers/?token=your-token&page_size=2&page=2

Message Body:
{
  "type": "get_customers"
}
```

### Method 2: Message Body Parameters ✅
```
URL: ws://api.pilito.com/ws/customers/?token=your-token

Message Body:
{
  "type": "get_customers",
  "filters": {
    "page_size": 2,
    "page": 2
  }
}
```

### Method 3: Combined (Message Body Takes Priority) ✅
```
URL: ws://api.pilito.com/ws/customers/?token=your-token&page_size=10&page=1

Message Body:
{
  "type": "get_customers",
  "filters": {
    "page_size": 2,
    "page": 2
  }
}
```
Result: Will use page_size=2, page=2 (from message body)

## 🎯 Expected Response Format:
```json
{
  "type": "customers_list",
  "customers": [...],
  "pagination": {
    "count": 3,           // Total customers
    "page_count": 2,      // Customers in current page
    "page_size": 2,       // Items per page
    "page": 2,            // Current page number
    "total_pages": 2,     // Total pages available
    "has_next": false,    // More pages available
    "has_previous": true, // Previous pages available
    "offset": 2,          // Current offset (calculated)
    "limit": 2            // Page size (backward compatibility)
  },
  "filters": {
    "page_size": 2,
    "page": 2
  },
  "count": 3,
  "page_count": 2,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🔍 Debugging:
Check logs for:
- `WebSocketPagination initialized with filters: {...}`
- `WebSocketPagination calculated: page_size=X, page=Y, offset=Z`
- `Merged filters: query_params={...}, filters={...}, result={...}`

## 🚀 Supported WebSocket APIs:
- **Customers**: `/ws/customers/`
- **Conversations**: `/ws/conversations/`
- **Messages**: `/ws/chat/{conversation_id}/`

## 📊 Parameters:
- `page_size`: Items per page (1-500, default: 10)
- `page`: Page number (1-based, default: 1)
- `limit`: Alternative to page_size (backward compatibility)
- `offset`: Alternative to page-based (backward compatibility)
