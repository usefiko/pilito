# Customer WebSocket Filtering - Quick Reference

## 🚀 Quick Start

### Connect
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/customers/');
```

### Basic Filter
```javascript
ws.send(JSON.stringify({
  type: 'filter_customers',
  filters: {
    has_email: 'true',
    source: 'telegram'
  }
}));
```

## 📋 Filter Cheat Sheet

| Filter | Type | Values | Description |
|--------|------|--------|-------------|
| `search` | String | Any text | Search in name, username, email, phone |
| `has_email` | String | `true`, `false`, `all` | Filter by email presence |
| `has_phone` | String | `true`, `false`, `all` | Filter by phone presence |
| `source` | String | `telegram`, `instagram`, `unknown`, `all` | Filter by platform |
| `tags` | Array | `["VIP", "Premium"]` | Filter by tag names |
| `tag_ids` | Array | `[1, 2, 3]` | Filter by tag IDs |
| `conversation_status` | String | `active`, `closed`, etc. | Filter by conversation status |
| `has_unread` | String | `true`, `false`, `all` | Filter by unread messages |
| `date_from` | String | `2023-01-01` | Filter from creation date |
| `date_to` | String | `2023-12-31` | Filter to creation date |
| `last_activity_from` | String | `2023-01-01` | Filter from last activity |
| `last_activity_to` | String | `2023-12-31` | Filter to last activity |
| `order_by` | String | `-created_at`, `first_name` | Sort order |

## 🎯 Common Use Cases

### VIP Customers with Email
```javascript
{
  type: 'filter_customers',
  filters: {
    tags: ['VIP'],
    has_email: 'true'
  }
}
```

### Telegram Users Needing Response
```javascript
{
  type: 'filter_customers', 
  filters: {
    source: 'telegram',
    has_unread: 'true'
  }
}
```

### Customers Without Contact Info
```javascript
{
  type: 'filter_customers',
  filters: {
    has_email: 'false',
    has_phone: 'false'
  }
}
```

### Recent Active Customers
```javascript
{
  type: 'filter_customers',
  filters: {
    last_activity_from: '2023-11-01',
    conversation_status: 'active',
    order_by: '-updated_at'
  }
}
```

## 📨 Message Types

| Type | Purpose |
|------|---------|
| `get_customers` | Get customers with filters |
| `filter_customers` | Advanced filtering |
| `refresh_customers` | Refresh current list |
| `search_customers` | Legacy search (use `search` filter instead) |
| `get_filter_options` | Get available filter values |

## 📊 Response Types

| Type | Description |
|------|-------------|
| `customers_list` | Customer data with pagination |
| `filter_options` | Available filter values |
| `error` | Error message |

## ⚡ Performance Tips

1. **Use Pagination**: Set `page_size` for large datasets
2. **Combine Filters**: Multiple filters = better performance than separate queries
3. **Cache Filter Options**: Don't call `get_filter_options` repeatedly
4. **Debounce Search**: Wait 300ms before sending search requests

## 🐛 Quick Debug

```javascript
// Check available filters
ws.send(JSON.stringify({type: 'get_filter_options'}));

// Test basic connection
ws.send(JSON.stringify({type: 'get_customers', filters: {}}));

// Check specific filter
ws.send(JSON.stringify({
  type: 'filter_customers',
  filters: {has_email: 'true'}
}));
```

## 🔧 Frontend Integration Snippet

```javascript
class CustomerWebSocket {
  constructor() {
    this.ws = new WebSocket('ws://localhost:8000/ws/customers/');
    this.ws.onmessage = this.handleMessage.bind(this);
  }
  
  filter(filters) {
    this.ws.send(JSON.stringify({
      type: 'filter_customers',
      filters
    }));
  }
  
  handleMessage(event) {
    const data = JSON.parse(event.data);
    switch(data.type) {
      case 'customers_list':
        this.onCustomers(data.customers, data.pagination);
        break;
      case 'filter_options':
        this.onFilterOptions(data.options);
        break;
      case 'error':
        this.onError(data.message);
        break;
    }
  }
  
  onCustomers(customers, pagination) {
    console.log('Customers:', customers);
  }
  
  onFilterOptions(options) {
    console.log('Filter options:', options);
  }
  
  onError(message) {
    console.error('WebSocket error:', message);
  }
}

// Usage
const customerWS = new CustomerWebSocket();
customerWS.filter({has_email: 'true', source: 'telegram'});
```
