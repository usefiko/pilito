# Smart PATCH API Documentation
## Intelligent Node Update System

### 📋 Overview
The Smart PATCH API provides an intelligent and flexible way to update workflow nodes. It accepts any field and applies changes intelligently, supporting merge operations, position management, and content updates in a single request.

---

## 🚀 Key Features

### ✅ **Smart Intelligence**
- **Accepts any field** and applies changes appropriately
- **Automatic merging** for arrays (keywords, tags, channels, conditions)
- **Smart JSON handling** for objects (webhook headers/payload)
- **Position management** with advanced features
- **Type-specific validation** based on node type
- **Flexible replacement** options with special flags

### ✅ **Supported Node Types**
- **When Nodes** - Trigger conditions
- **Condition Nodes** - Logic conditions
- **Action Nodes** - Operations to perform
- **Waiting Nodes** - User response handlers

---

## 🌐 API Endpoint

```http
PATCH /api/v1/workflow/api/nodes/{node_id}/
```

### Authentication
```http
Authorization: Bearer {your-jwt-token}
Content-Type: application/json
```

---

## 📍 Position Management

### Direct Position Updates
```json
{
  "position_x": 450,
  "position_y": 350
}
```

### Position Object Format
```json
{
  "position": {
    "x": 500,
    "y": 300
  }
}
```

### Relative Movement
```json
{
  "move_by": {
    "x": 50,
    "y": -30
  }
}
```
**Result:** Moves node 50px right, 30px up from current position

### Position Alignment
```json
{
  "align_to": {
    "x": 600
  }
}
```
**Result:** Aligns node to x=600, keeps Y coordinate unchanged

### Grid Snapping
```json
{
  "position_x": 347,
  "position_y": 183,
  "snap_to_grid": true,
  "grid_size": 25
}
```
**Result:** Position snapped to grid: (350, 175) with 25px grid

### Bounds Enforcement
```json
{
  "position_x": 2500,
  "position_y": -50,
  "enforce_bounds": {
    "min_x": 0,
    "max_x": 2000,
    "min_y": 0,
    "max_y": 1500
  }
}
```
**Result:** Position constrained to bounds: (2000, 0)

### Complex Position Updates
```json
{
  "move_by": {"x": 100, "y": 75},
  "snap_to_grid": true,
  "grid_size": 20,
  "enforce_bounds": {
    "min_x": 0,
    "max_x": 1800,
    "min_y": 0,
    "max_y": 1200
  }
}
```
**Processing Order:** Move → Snap to Grid → Constrain to Bounds

---

## 🔥 When Node Examples

### Add Keywords (Merge)
```json
{
  "keywords": ["help", "support", "assistance"]
}
```
**Result:** New keywords merged with existing ones (no duplicates)

### Add Channels
```json
{
  "channels": ["whatsapp", "email"]
}
```
**Result:** Channels merged: telegram, instagram, whatsapp, email

### Multiple Updates
```json
{
  "title": "Updated Trigger",
  "position_x": 350,
  "keywords": ["updated"],
  "channels": ["telegram"],
  "customer_tags": ["vip", "premium"]
}
```

### Replace Keywords (Force Replace)
```json
{
  "keywords": ["completely", "new", "keywords"],
  "replace_keywords": true
}
```
**Result:** All old keywords replaced with new ones

### Schedule Updates
```json
{
  "when_type": "scheduled",
  "schedule_frequency": "weekly",
  "schedule_time": "10:00:00",
  "schedule_date": "2024-01-15"
}
```

---

## ❓ Condition Node Examples

### Add Condition (Merge)
```json
{
  "conditions": [
    {
      "type": "message",
      "operator": "contains",
      "value": "urgent"
    }
  ]
}
```
**Result:** New condition added to existing conditions

### Change Operator + Add Condition
```json
{
  "combination_operator": "or",
  "conditions": [
    {
      "type": "ai",
      "prompt": "Is this an emergency?"
    }
  ]
}
```

### Replace All Conditions
```json
{
  "conditions": [
    {
      "type": "message",
      "operator": "equals",
      "value": "help"
    }
  ],
  "replace_conditions": true
}
```
**Result:** All previous conditions replaced with new one

---

## ⚡ Action Node Examples

### Update Message Content
```json
{
  "message_content": "Updated welcome message! 🎉"
}
```

### Add Webhook Headers (Merge)
```json
{
  "webhook_headers": {
    "X-Custom-Header": "value",
    "Authorization": "Bearer new-token"
  }
}
```
**Result:** New headers merged with existing ones

### Update Webhook + Payload
```json
{
  "webhook_url": "https://new-webhook.com/endpoint",
  "webhook_payload": {
    "new_field": "new_value",
    "timestamp": "{{now}}"
  }
}
```
**Result:** URL updated, payload merged with existing

### Replace Webhook Headers
```json
{
  "webhook_headers": {
    "Content-Type": "application/json"
  },
  "replace_webhook_headers": true
}
```
**Result:** All old headers replaced with new ones

### Change Action Type
```json
{
  "action_type": "send_email",
  "email_to": "admin@company.com",
  "email_subject": "New Alert",
  "email_body": "Alert message body"
}
```

---

## ⏳ Waiting Node Examples

### Add Choice Options (Merge)
```json
{
  "choice_options": ["New Option", "Another Choice"]
}
```
**Result:** New options added to existing choice list

### Update Message + Add Skip Keywords
```json
{
  "customer_message": "Updated: Please choose an option:",
  "skip_keywords": ["skip", "cancel", "later"]
}
```

### Enable Time Limit
```json
{
  "response_time_limit_enabled": true,
  "response_timeout_amount": 10,
  "response_timeout_unit": "minutes"
}
```

### Replace All Choice Options
```json
{
  "choice_options": ["Yes", "No", "Maybe"],
  "replace_choice_options": true
}
```

### Storage Settings
```json
{
  "storage_type": "database",
  "storage_field": "user_preference",
  "allowed_errors": 2
}
```

---

## 🏷️ Special Replacement Flags

### When Node Flags
```json
{
  "keywords": ["new", "keywords"],
  "replace_keywords": true,     // Replace all keywords
  "replace_channels": true,     // Replace all channels
  "replace_customer_tags": true // Replace all customer tags
}
```

### Condition Node Flags
```json
{
  "conditions": [...],
  "replace_conditions": true    // Replace all conditions
}
```

### Action Node Flags
```json
{
  "webhook_headers": {...},
  "replace_webhook_headers": true,  // Replace all headers
  "replace_webhook_payload": true   // Replace payload
}
```

### Waiting Node Flags
```json
{
  "choice_options": [...],
  "replace_choice_options": true,   // Replace all options
  "replace_skip_keywords": true     // Replace skip keywords
}
```

---

## 💻 JavaScript Implementation

### Basic Usage
```javascript
class SmartNodeUpdater {
  constructor(token, baseUrl = '/api/v1/workflow/api') {
    this.token = token;
    this.baseUrl = baseUrl;
  }

  async smartPatch(nodeId, updates) {
    const response = await fetch(`${this.baseUrl}/nodes/${nodeId}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates)
    });

    if (response.ok) {
      return await response.json();
    } else {
      throw new Error(await response.text());
    }
  }

  // Convenience methods
  async addKeywords(nodeId, keywords) {
    return this.smartPatch(nodeId, { keywords });
  }

  async replaceKeywords(nodeId, keywords) {
    return this.smartPatch(nodeId, { 
      keywords, 
      replace_keywords: true 
    });
  }

  async updatePosition(nodeId, x, y) {
    return this.smartPatch(nodeId, { position_x: x, position_y: y });
  }

  async moveBy(nodeId, deltaX, deltaY) {
    return this.smartPatch(nodeId, { 
      move_by: { x: deltaX, y: deltaY } 
    });
  }

  async snapToGrid(nodeId, gridSize = 20) {
    return this.smartPatch(nodeId, { 
      snap_to_grid: true, 
      grid_size: gridSize 
    });
  }
}

// Usage Examples
const updater = new SmartNodeUpdater('your-jwt-token');

// Position updates
await updater.updatePosition('node-id', 400, 300);
await updater.moveBy('node-id', 50, -30);
await updater.snapToGrid('node-id', 25);

// Content updates
await updater.addKeywords('node-id', ['help', 'support']);
await updater.replaceKeywords('node-id', ['new', 'keywords']);

// Complex update
await updater.smartPatch('node-id', {
  title: 'Updated Node',
  position: { x: 500, y: 300 },
  keywords: ['updated'],
  snap_to_grid: true,
  grid_size: 25
});
```

### Position Management Class
```javascript
class NodePositionManager {
  constructor(token, baseUrl = '/api/v1/workflow/api') {
    this.token = token;
    this.baseUrl = baseUrl;
  }

  async setPosition(nodeId, x, y) {
    return this.updatePosition(nodeId, { position_x: x, position_y: y });
  }

  async setPositionObject(nodeId, position) {
    return this.updatePosition(nodeId, { position });
  }

  async moveBy(nodeId, deltaX, deltaY) {
    return this.updatePosition(nodeId, { 
      move_by: { x: deltaX, y: deltaY } 
    });
  }

  async alignTo(nodeId, x = null, y = null) {
    const align_to = {};
    if (x !== null) align_to.x = x;
    if (y !== null) align_to.y = y;
    return this.updatePosition(nodeId, { align_to });
  }

  async snapToGrid(nodeId, gridSize = 20, newPosition = null) {
    const updates = { snap_to_grid: true, grid_size: gridSize };
    if (newPosition) updates.position = newPosition;
    return this.updatePosition(nodeId, updates);
  }

  async constrainToBounds(nodeId, bounds, newPosition = null) {
    const updates = { enforce_bounds: bounds };
    if (newPosition) updates.position = newPosition;
    return this.updatePosition(nodeId, updates);
  }

  // Layout helpers
  async arrangeHorizontally(nodes, startX = 100, y = 200, spacing = 200) {
    const promises = nodes.map((nodeId, index) => 
      this.setPosition(nodeId, startX + (index * spacing), y)
    );
    return Promise.all(promises);
  }

  async arrangeVertically(nodes, x = 300, startY = 100, spacing = 150) {
    const promises = nodes.map((nodeId, index) => 
      this.setPosition(nodeId, x, startY + (index * spacing))
    );
    return Promise.all(promises);
  }

  async createGridLayout(nodes, cols = 3, startX = 100, startY = 100, 
                         spacingX = 250, spacingY = 200) {
    const promises = nodes.map((nodeId, index) => {
      const row = Math.floor(index / cols);
      const col = index % cols;
      const x = startX + (col * spacingX);
      const y = startY + (row * spacingY);
      return this.setPosition(nodeId, x, y);
    });
    return Promise.all(promises);
  }

  async updatePosition(nodeId, updates) {
    const response = await fetch(`${this.baseUrl}/nodes/${nodeId}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates)
    });
    return response.json();
  }
}
```

---

## 🌐 cURL Examples

### Basic Position Update
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "position_x": 450,
    "position_y": 350
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

### Complex Update with Position + Content
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Node",
    "position": {"x": 500, "y": 300},
    "keywords": ["updated", "repositioned"],
    "snap_to_grid": true,
    "grid_size": 25,
    "enforce_bounds": {
      "min_x": 0, "max_x": 2000,
      "min_y": 0, "max_y": 1500
    }
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

### When Node Update
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["help", "support"],
    "channels": ["whatsapp"],
    "customer_tags": ["vip"]
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

### Condition Node Update
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "combination_operator": "or",
    "conditions": [{
      "type": "message",
      "operator": "contains",
      "value": "urgent"
    }]
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

### Action Node Update
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message_content": "Updated message!",
    "webhook_headers": {
      "X-Custom": "value"
    }
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

### Waiting Node Update
```bash
curl -X PATCH \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_message": "Please choose:",
    "choice_options": ["Option A", "Option B"],
    "response_time_limit_enabled": true,
    "response_timeout_amount": 10,
    "response_timeout_unit": "minutes"
  }' \
  "https://api.pilito.com/api/v1/workflow/api/nodes/{node-id}/"
```

---

## ✅ Response Format

### Success Response
```json
{
  "id": "uuid",
  "node_type": "when",
  "title": "Updated Node",
  "position_x": 450,
  "position_y": 350,
  "keywords": ["help", "support", "existing"],
  "channels": ["telegram", "whatsapp"],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "error": "Validation failed",
  "details": {
    "keywords": ["This field is required for when nodes"],
    "position_x": ["Position must be a positive number"]
  }
}
```

---

## 🎯 Best Practices

### 1. **Incremental Updates**
```json
// Good: Only send fields you want to change
{
  "title": "New Title",
  "position_x": 400
}

// Avoid: Sending entire object unnecessarily
```

### 2. **Use Merge by Default**
```json
// Merge new keywords with existing
{
  "keywords": ["new", "keyword"]
}

// Only use replace when needed
{
  "keywords": ["completely", "new"],
  "replace_keywords": true
}
```

### 3. **Combine Related Updates**
```json
// Good: Update position and content together
{
  "title": "Repositioned Node",
  "position": {"x": 500, "y": 300},
  "snap_to_grid": true
}
```

### 4. **Position Management**
```json
// Use appropriate position method
{
  "position": {"x": 400, "y": 300}        // Direct positioning
}
{
  "move_by": {"x": 50, "y": -30}          // Relative movement
}
{
  "align_to": {"x": 500}                  // Alignment
}
```

### 5. **Grid and Bounds**
```json
// Always specify grid_size with snap_to_grid
{
  "position": {"x": 347, "y": 183},
  "snap_to_grid": true,
  "grid_size": 25
}

// Use bounds for canvas constraints
{
  "enforce_bounds": {
    "min_x": 0, "max_x": 2000,
    "min_y": 0, "max_y": 1500
  }
}
```

---

## 🔍 Validation Rules

### Position Validation
- `position_x`, `position_y`: Must be numbers
- `grid_size`: Must be positive integer (default: 20)
- `enforce_bounds`: All values must be numbers
- `move_by`: Values can be positive or negative

### Content Validation
- Arrays are automatically merged (unless replace flag is used)
- JSON objects are merged by key
- Required fields are validated based on node type

### Node-Specific Validation
- **When Nodes**: Require at least one trigger condition
- **Condition Nodes**: Require valid operator and conditions
- **Action Nodes**: Require valid action_type
- **Waiting Nodes**: Conditional validation based on settings

---

## 🚀 Performance Tips

### 1. **Batch Updates**
```javascript
// Good: Single request with multiple changes
await updater.smartPatch('node-id', {
  title: 'Updated',
  position: {x: 400, y: 300},
  keywords: ['new'],
  snap_to_grid: true
});

// Avoid: Multiple separate requests
await updater.updateTitle('node-id', 'Updated');
await updater.updatePosition('node-id', 400, 300);
await updater.addKeywords('node-id', ['new']);
```

### 2. **Efficient Position Updates**
```javascript
// Good: Use relative movement for small changes
await updater.moveBy('node-id', 25, 0);

// Avoid: Calculating absolute positions unnecessarily
const current = await getNodePosition('node-id');
await updater.setPosition('node-id', current.x + 25, current.y);
```

### 3. **Smart Array Updates**
```javascript
// Good: Let API merge arrays
await updater.smartPatch('node-id', {
  keywords: ['new', 'keyword']
});

// Avoid: Fetching and merging manually
const node = await getNode('node-id');
const mergedKeywords = [...node.keywords, 'new', 'keyword'];
await updater.replaceKeywords('node-id', mergedKeywords);
```

---

## 📚 Common Use Cases

### 1. **Workflow Designer Integration**
```javascript
// Drag and drop position update
async function onNodeDrag(nodeId, newPosition) {
  await updater.smartPatch(nodeId, {
    position: newPosition,
    snap_to_grid: true,
    grid_size: 25,
    enforce_bounds: CANVAS_BOUNDS
  });
}

// Property panel updates
async function onPropertyChange(nodeId, property, value) {
  await updater.smartPatch(nodeId, {
    [property]: value
  });
}
```

### 2. **Bulk Layout Updates**
```javascript
// Arrange workflow in horizontal layout
async function arrangeWorkflow(nodeIds) {
  const positionManager = new NodePositionManager(token);
  await positionManager.arrangeHorizontally(nodeIds, 100, 200, 250);
}

// Auto-organize overlapping nodes
async function autoOrganize(nodes) {
  for (let i = 0; i < nodes.length; i++) {
    await updater.smartPatch(nodes[i].id, {
      position: { x: 100 + (i % 4) * 300, y: 100 + Math.floor(i / 4) * 200 },
      snap_to_grid: true,
      grid_size: 50
    });
  }
}
```

### 3. **Content Management**
```javascript
// Add keywords from user input
async function addKeywords(nodeId, newKeywords) {
  await updater.addKeywords(nodeId, newKeywords);
}

// Update condition with validation
async function addCondition(nodeId, condition) {
  await updater.smartPatch(nodeId, {
    conditions: [condition]
  });
}
```

---

## 🎉 Summary

The Smart PATCH API provides:

✅ **Intelligent field handling** - Accepts any field and applies appropriately  
✅ **Array merging** - Automatically merges keywords, tags, channels, conditions  
✅ **Position management** - Advanced positioning with grid snap and bounds  
✅ **Replacement options** - Special flags for complete replacement  
✅ **Type-specific validation** - Smart validation based on node type  
✅ **Performance optimization** - Single request for multiple updates  
✅ **Developer-friendly** - Intuitive API design with helpful JavaScript libraries  

**Your workflow nodes can now be updated with maximum flexibility and intelligence!** 🚀
