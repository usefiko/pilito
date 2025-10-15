# WebSocket Frontend Updates

## 🚫 **BREAKING CHANGES**

### Removed Features
```javascript
// ❌ REMOVE - Typing events no longer work
{ type: 'typing', is_typing: true }
// ❌ REMOVE - No typing_indicator events received
```

### New Features
- ✅ Customer `username` field now included in all responses
- ✅ Advanced search and filtering for customers and conversations
- ✅ Filter options API to build dynamic UI

---

## 📡 **WebSocket Connections**

```javascript
// Same as before
const customerWS = new WebSocket('ws://localhost:8000/ws/customers/?token=JWT_TOKEN');
const conversationWS = new WebSocket('ws://localhost:8000/ws/conversations/?token=JWT_TOKEN'); 
const chatWS = new WebSocket('ws://localhost:8000/ws/chat/CONVERSATION_ID/?token=JWT_TOKEN');
```

---

## 🔍 **Customer List WebSocket**

### Basic Usage
```javascript
// Get all customers
customerWS.send(JSON.stringify({ type: 'get_customers' }));

// Search (backward compatible)
customerWS.send(JSON.stringify({ 
  type: 'search_customers', 
  search_term: 'john' 
}));
```

### **NEW: Advanced Filtering**
```javascript
customerWS.send(JSON.stringify({
  type: 'filter_customers',
  filters: {
    search: 'john doe',              // Searches: name, username, email, phone
    source: 'telegram',              // 'telegram', 'instagram', 'unknown'
    tags: ['vip', 'support'],        // Customer tags
    date_from: '2024-01-01',         // Date range
    order_by: '-updated_at',         // Sorting
    limit: 50, offset: 0             // Pagination
  }
}));
```

### **NEW: Get Filter Options**
```javascript
// Get available sources, tags, and order options
customerWS.send(JSON.stringify({ type: 'get_filter_options' }));
```

### Response Format
```javascript
{
  type: 'customers_list',
  customers: [
    {
      id: 1,
      first_name: 'John',
      last_name: 'Doe',
      username: 'johndoe',           // ← NEW FIELD
      email: 'john@example.com',
      source: 'telegram',
      profile_picture: '/media/...',
      // ... other fields
    }
  ],
  count: 25,                         // ← NEW FIELD
  filters: {...}                     // ← NEW FIELD
}
```

---

## 💬 **Conversation List WebSocket**

### Basic Usage
```javascript
// Get all conversations
conversationWS.send(JSON.stringify({ type: 'get_conversations' }));
```

### **NEW: Advanced Filtering**
```javascript
conversationWS.send(JSON.stringify({
  type: 'filter_conversations',
  filters: {
    search: 'support',               // Searches: title, customer info, messages
    status: 'open',                  // 'open', 'closed', 'pending'
    source: 'telegram',              // Platform filter
    priority: 'high',                // Priority filter
    unread_only: true,               // Show only unread
    tags: ['urgent']                 // Customer tags
  }
}));
```

### **NEW: Get Filter Options**
```javascript
conversationWS.send(JSON.stringify({ type: 'get_conversation_filter_options' }));
```

### Response Format
```javascript
{
  type: 'conversations_list',
  conversations: [
    {
      id: 'conv_123',
      title: 'Support Issue',
      status: 'open',
      customer: {
        id: 1,
        first_name: 'John',
        username: 'johndoe',         // ← NEW FIELD
        // ...
      },
      unread_count: 3,               // ← Unread messages
      last_message: { /* ... */ }
    }
  ]
}
```

---

## 💭 **Chat WebSocket (Updated)**

### Send Message
```javascript
chatWS.send(JSON.stringify({
  type: 'chat_message',
  content: 'Hello!',
  type: 'support'                    // or 'marketing'
}));
```

### Mark as Read
```javascript
chatWS.send(JSON.stringify({ type: 'mark_read' }));
```

### **REMOVED: Typing Events**
```javascript
// ❌ Don't use these anymore
// chatWS.send(JSON.stringify({ type: 'typing', is_typing: true }));
```

---

## 🛠 **Frontend Implementation**

### Customer List with Search
```javascript
class CustomerList {
  setupWebSocket() {
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'customers_list') {
        this.renderCustomers(data.customers);
        this.updatePagination(data.count);
      }
    };
  }
  
  search(term) {
    this.ws.send(JSON.stringify({
      type: 'filter_customers',
      filters: { search: term }
    }));
  }
  
  filterBySource(source) {
    this.ws.send(JSON.stringify({
      type: 'filter_customers', 
      filters: { source: source }
    }));
  }
  
  renderCustomer(customer) {
    // NEW: Include username in display
    const name = customer.username 
      ? `${customer.first_name} (@${customer.username})`
      : `${customer.first_name} ${customer.last_name}`;
    
    return `<div class="customer">${name}</div>`;
  }
}
```

### Chat Component (Remove Typing)
```javascript
class ChatWindow {
  setupWebSocket() {
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch(data.type) {
        case 'chat_message':
          this.addMessage(data.message);
          break;
          
        // ❌ Remove typing_indicator case
        
        case 'messages_read':
          this.markAsRead(data.user_id);
          break;
      }
    };
  }
  
  // ❌ Remove all typing methods
  // startTyping() { ... }
  // stopTyping() { ... }
}
```

---

## 🎯 **Quick Migration Checklist**

### Remove Typing Features
- [ ] Remove typing indicator UI
- [ ] Remove typing event handlers  
- [ ] Remove typing WebSocket messages
- [ ] Remove typing state management

### Add Username Support
- [ ] Update customer display to show username
- [ ] Handle cases where username is null/empty

### Implement New Filtering
- [ ] Add search input with new filter API
- [ ] Add filter dropdowns (source, status, etc.)
- [ ] Add pagination controls
- [ ] Load filter options on connect

### Update Message Handlers
- [ ] Handle new response fields (count, filters)
- [ ] Update error handling
- [ ] Test all WebSocket connections

---

## ⚡ **Quick Examples**

### Search Box
```javascript
searchInput.addEventListener('input', (e) => {
  ws.send(JSON.stringify({
    type: 'filter_customers',
    filters: { search: e.target.value }
  }));
});
```

### Filter Dropdown
```javascript
sourceSelect.addEventListener('change', (e) => {
  ws.send(JSON.stringify({
    type: 'filter_customers',
    filters: { source: e.target.value }
  }));
});
```

### Show Unread Only
```javascript
unreadCheckbox.addEventListener('change', (e) => {
  ws.send(JSON.stringify({
    type: 'filter_conversations',
    filters: { unread_only: e.target.checked }
  }));
});
```

---

## 🧪 **Testing**

### Test WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/customers/?token=YOUR_TOKEN');

ws.onopen = () => {
  // Test basic functionality
  ws.send(JSON.stringify({ type: 'get_customers' }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data.type);
  
  // Check username field exists
  if (data.type === 'customers_list') {
    console.log('Username field:', data.customers[0]?.username);
  }
};
```

### Test Filters
```javascript
// Test each filter type
const testFilters = [
  { search: 'john' },
  { source: 'telegram' },
  { search: 'support', source: 'instagram' }
];

testFilters.forEach(filters => {
  ws.send(JSON.stringify({ type: 'filter_customers', filters }));
});
```

---

## ⚠️ **Important Notes**

1. **Backward Compatibility**: Old search methods still work but use new filters for advanced features
2. **Username Field**: Always check if username exists before displaying
3. **Error Handling**: All WebSocket errors now return `{ type: 'error', message: '...' }`
4. **Performance**: Use pagination for large datasets with `limit` and `offset`
5. **Real-time**: Filters update instantly via WebSocket