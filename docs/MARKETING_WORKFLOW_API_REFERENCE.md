# Marketing Workflow API Reference

Complete reference for all Marketing Workflow APIs with usage examples and routes.

## 📋 Table of Contents

- [Base URL & Authentication](#base-url--authentication)
- [Workflow Management](#workflow-management)
- [Node-Based Workflow Management](#node-based-workflow-management)
- [Unified Node Management API](#unified-node-management-api)
- [Connection Management API](#connection-management-api)
- [Trigger Management](#trigger-management)
- [Action Management](#action-management)
- [Condition Management](#condition-management)
- [Event Processing](#event-processing)
- [Monitoring & Analytics](#monitoring--analytics)
- [Common Response Formats](#common-response-formats)
- [Error Handling](#error-handling)

## 🌐 Base URL & Authentication

### Base URL
```
http://localhost:8000/api/v1/workflow/api/
```

### Authentication
All endpoints require authentication using JWT Bearer tokens:

```bash
# Include in all requests
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

### Get Authentication Token
```bash
# Login to get token (adjust endpoint as per your auth system)
curl -X POST http://localhost:8000/api/v1/usr/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

## 🔄 Workflow Management

### List Workflows
```bash
GET /workflows/
```

**Parameters:**
- `page` (int): Page number for pagination
- `page_size` (int): Number of items per page (max 100)
- `status` (string): Filter by status (DRAFT, ACTIVE, PAUSED, ARCHIVED)
- `search` (string): Search in name and description

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/workflows/?status=ACTIVE&page=1&page_size=10"
```

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "workflow-uuid",
      "name": "Welcome New Users",
      "description": "Send welcome message to new registrations",
      "status": "ACTIVE",
      "actions_count": 2,
      "triggers_count": 1,
      "executions_count": 15,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-02T10:00:00Z"
    }
  ]
}
```

### Get Workflow Details
```bash
GET /workflows/{id}/
```

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/workflows/workflow-uuid/"
```

**Response:**
```json
{
  "id": "workflow-uuid",
  "name": "Welcome New Users",
  "description": "Send welcome message to new registrations",
  "status": "ACTIVE",
  "max_executions": 1,
  "delay_between_executions": 0,
  "start_date": null,
  "end_date": null,
  "created_by": "admin",
  "ui_settings": {},
  "edges": [],
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-02T10:00:00Z",
  "actions": [
    {
      "id": "action-uuid",
      "action_name": "Send Welcome Message",
      "action_type": "send_message",
      "order": 1,
      "is_required": true
    }
  ],
  "triggers": [
    {
      "id": "trigger-uuid",
      "trigger_name": "New User Registration",
      "priority": 100,
      "is_active": true
    }
  ],
  "recent_executions": [],
  
  "nodes": [
    {
      "id": "when-node-uuid",
      "node_type": "when",
      "title": "New User Registration",
      "when_type": "new_customer",
      "keywords": [],
      "channels": ["telegram", "instagram"],
      "customer_tags": ["new_user"],
      "position_x": 100,
      "position_y": 200,
      "is_active": true,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    },
    {
      "id": "action-node-uuid",
      "node_type": "action", 
      "title": "Send Welcome Message",
      "action_type": "send_message",
      "action_type_display": "Send Message",
      "message_content": "Welcome to our platform! 🎉",
      "position_x": 300,
      "position_y": 200,
      "is_active": true,
      "created_at": "2024-01-01T10:05:00Z",
      "updated_at": "2024-01-01T10:05:00Z"
    }
  ],
  
  "connections": [
    {
      "id": "connection-uuid",
      "source_node": "when-node-uuid",
      "target_node": "action-node-uuid",
      "source_node_title": "New User Registration",
      "target_node_title": "Send Welcome Message",
      "connection_type": "success",
      "connection_type_display": "Success",
      "condition": {},
      "created_at": "2024-01-01T10:10:00Z"
    }
  ],
  
  "node_summary": {
    "total_nodes": 2,
    "when_nodes": 1,
    "condition_nodes": 0,
    "action_nodes": 1,
    "waiting_nodes": 0,
    "total_connections": 1
  }
}
```

### Create Workflow
```bash
POST /workflows/
```

**Request Body:**
```json
{
  "name": "Discount Code Campaign",
  "description": "Send discount codes when customers ask",
  "status": "DRAFT",
  "max_executions": 1,
  "delay_between_executions": 3600
}
```

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Discount Code Campaign",
    "description": "Send discount codes when customers ask",
    "status": "DRAFT"
  }' \
  "http://localhost:8000/api/v1/workflow/api/workflows/"
```

### Update Workflow
```bash
PUT /workflows/{id}/
PATCH /workflows/{id}/  # Partial update
```

**Example:**
```bash
curl -X PATCH \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "ACTIVE"}' \
  "http://localhost:8000/api/v1/workflow/api/workflows/workflow-uuid/"
```

### Delete Workflow
```bash
DELETE /workflows/{id}/
```

**Example:**
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/workflows/workflow-uuid/"
```

### Workflow Actions

#### Activate Workflow
```bash
POST /workflows/{id}/activate/
```

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/workflows/workflow-uuid/activate/"
```

#### Pause Workflow
```bash
POST /workflows/{id}/pause/
```

#### Archive Workflow
```bash
POST /workflows/{id}/archive/
```

#### Reset Workflow to Draft
```bash
POST /workflows/{id}/reset/
```

#### Execute Workflow Manually
```bash
POST /workflows/{id}/execute/
```

**Request Body:**
```json
{
  "context": {
    "user": {
      "id": "customer-123",
      "email": "test@example.com",
      "first_name": "John"
    },
    "event": {
      "type": "MANUAL_TRIGGER",
      "data": {
        "reason": "Testing workflow"
      }
    }
  }
}
```

### Workflow Associations

#### Add Trigger to Workflow
```bash
POST /workflows/{id}/add_trigger/
```

**Request Body:**
```json
{
  "trigger_id": "trigger-uuid",
  "priority": 100,
  "specific_conditions": {
    "operator": "and",
    "conditions": [
      {
        "field": "user.tags",
        "operator": "contains",
        "value": "premium"
      }
    ]
  }
}
```

#### Remove Trigger from Workflow
```bash
POST /workflows/{id}/remove_trigger/
```

**Request Body:**
```json
{
  "trigger_id": "trigger-uuid"
}
```

#### Get Workflow Triggers
```bash
GET /workflows/{id}/triggers/
```

#### Get Workflow Actions
```bash
GET /workflows/{id}/actions/
```

#### Get Workflow Executions
```bash
GET /workflows/{id}/executions/
```

**Parameters:**
- `page`, `page_size`: Pagination
- `status`: Filter by execution status

#### Get Workflow Events
```bash
GET /workflows/{id}/events/
```

### Workflow Statistics
```bash
GET /workflows/statistics/
```

**Response:**
```json
{
  "total_workflows": 5,
  "active_workflows": 3,
  "draft_workflows": 1,
  "paused_workflows": 1,
  "total_executions": 150,
  "recent_executions": 25,
  "successful_executions": 140,
  "failed_executions": 10
}
```

## 🎯 Trigger Management

### List Triggers
```bash
GET /triggers/
```

**Parameters:**
- `trigger_type`: Filter by trigger type
- `is_active`: Filter by active status
- `search`: Search in name and description

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/triggers/?trigger_type=MESSAGE_RECEIVED&is_active=true"
```

### Create Trigger
```bash
POST /triggers/
```

**Request Body:**
```json
{
  "name": "Coupon Request Trigger",
  "description": "Triggers when users ask for discounts",
  "trigger_type": "MESSAGE_RECEIVED",
  "filters": {
    "operator": "or",
    "conditions": [
      {
        "field": "event.data.content",
        "operator": "icontains",
        "value": "کد تخفیف"
      },
      {
        "field": "event.data.content",
        "operator": "icontains",
        "value": "coupon"
      }
    ]
  },
  "is_active": true
}
```

### Process Event (Main Event Processing Endpoint)
```bash
POST /triggers/process_event/
```

**Request Body:**
```json
{
  "event_type": "MESSAGE_RECEIVED",
  "data": {
    "message_id": "msg-123",
    "content": "سلام، کد تخفیف دارید؟",
    "timestamp": "2024-01-01T10:00:00Z"
  },
  "user_id": "customer-123",
  "conversation_id": "conv-456"
}
```

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "MESSAGE_RECEIVED",
    "data": {
      "message_id": "msg-123",
      "content": "Hello, do you have any discount codes?",
      "timestamp": "2024-01-01T10:00:00Z"
    },
    "user_id": "customer-123",
    "conversation_id": "conv-456"
  }' \
  "http://localhost:8000/api/v1/workflow/api/triggers/process_event/"
```

**Response:**
```json
{
  "success": true,
  "event_log_id": "event-log-uuid",
  "message": "Event queued for processing"
}
```

### Test Trigger
```bash
POST /triggers/{id}/test/
```

**Request Body:**
```json
{
  "context": {
    "event": {
      "data": {
        "content": "I need a coupon code"
      }
    },
    "user": {
      "tags": ["interested", "premium"]
    }
  }
}
```

### Get Trigger Workflows
```bash
GET /triggers/{id}/workflows/
```

### Activate/Deactivate Trigger
```bash
POST /triggers/{id}/activate/
POST /triggers/{id}/deactivate/
```

## ⚡ Action Management

### List Actions
```bash
GET /actions/
```

**Parameters:**
- `action_type`: Filter by action type
- `is_active`: Filter by active status

### Create Action
```bash
POST /actions/
```

**Send Message Action:**
```json
{
  "name": "Send Welcome Message",
  "description": "Send personalized welcome message",
  "action_type": "send_message",
  "configuration": {
    "message": "خوش آمدید {{user.first_name}}! چطور می‌تونم کمکتون کنم؟"
  },
  "order": 1,
  "delay": 0,
  "is_active": true
}
```

**Send Email Action:**
```json
{
  "name": "Send Welcome Email",
  "action_type": "send_email",
  "configuration": {
    "subject": "Welcome {{user.first_name}}!",
    "body": "Thank you for joining us!",
    "recipient": "{{user.email}}",
    "is_html": false
  }
}
```

**Add Tag Action:**
```json
{
  "name": "Add Interested Tag",
  "action_type": "add_tag",
  "configuration": {
    "tag_name": "interested"
  }
}
```

**Webhook Action:**
```json
{
  "name": "Notify External System",
  "action_type": "webhook",
  "configuration": {
    "url": "https://your-system.com/webhook",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer your-token"
    },
    "payload": {
      "user_id": "{{user.id}}",
      "event_type": "{{event.type}}",
      "timestamp": "{{event.timestamp}}"
    }
  }
}
```

**Wait Action:**
```json
{
  "name": "Wait 10 Minutes",
  "action_type": "wait",
  "configuration": {
    "duration": 10,
    "unit": "minutes"
  }
}
```

### Node-Based Action System

#### List Action Nodes
```bash
GET /action-nodes/
```

#### Create Action Node via Workflow
```bash
POST /node-workflows/{workflow_id}/create_node/
```

#### Get Action Types
```bash
GET /action-nodes/action_types/
```

**Response:**
```json
[
  {"value": "send_message", "label": "Send Message"},
  {"value": "delay", "label": "Delay"},
  {"value": "redirect_conversation", "label": "Redirect Conversation"},
  {"value": "add_tag", "label": "Add Tag"},
  {"value": "remove_tag", "label": "Remove Tag"},
  {"value": "transfer_to_human", "label": "Transfer to Human"},
  {"value": "send_email", "label": "Send Email"},
  {"value": "webhook", "label": "Webhook"},
  {"value": "custom_code", "label": "Custom Code"}
]
```

#### Get Redirect Destinations
```bash
GET /action-nodes/redirect_destinations/
```

**Response:**
```json
[
  {"value": "support", "label": "Support"},
  {"value": "sales", "label": "Sales"},
  {"value": "technical", "label": "Technical"},
  {"value": "billing", "label": "Billing"},
  {"value": "general", "label": "General"}
]
```

#### Get Delay Units
```bash
GET /action-nodes/delay_units/
```

**Response:**
```json
[
  {"value": "seconds", "label": "Seconds"},
  {"value": "minutes", "label": "Minutes"},
  {"value": "hours", "label": "Hours"},
  {"value": "days", "label": "Days"}
]
```

### Complete Action Node Examples

#### Send Message Action
```json
{
  "node_type": "action",
  "title": "Send Welcome Message",
  "action_type": "send_message",
  "message_content": "سلام {{user.first_name}}! خوش آمدید."
}
```

#### Delay Action
```json
{
  "node_type": "action", 
  "title": "Wait 30 Minutes",
  "action_type": "delay",
  "delay_amount": 30,
  "delay_unit": "minutes"
}
```

#### Redirect Conversation Action
```json
{
  "node_type": "action",
  "title": "Transfer to Support",
  "action_type": "redirect_conversation", 
  "redirect_destination": "support"
}
```

#### Add/Remove Tag Actions
```json
{
  "node_type": "action",
  "title": "Add VIP Tag",
  "action_type": "add_tag",
  "tag_name": "VIP"
}
```

```json
{
  "node_type": "action",
  "title": "Remove Trial Tag", 
  "action_type": "remove_tag",
  "tag_name": "trial"
}
```

#### Transfer to Human Action
```json
{
  "node_type": "action",
  "title": "Transfer to Agent",
  "action_type": "transfer_to_human"
}
```

#### Send Email Action
```json
{
  "node_type": "action",
  "title": "Send Follow-up Email",
  "action_type": "send_email"
}
```

#### Webhook Action
```json
{
  "node_type": "action",
  "title": "Call External API", 
  "action_type": "webhook",
  "webhook_url": "https://api.example.com/notify",
  "webhook_method": "POST",
  "webhook_headers": {"Authorization": "Bearer token"},
  "webhook_payload": {"user_id": "{{user.id}}", "event": "action_triggered"}
}
```

#### Custom Code Action
```json
{
  "node_type": "action",
  "title": "Calculate Discount",
  "action_type": "custom_code", 
  "custom_code": "# Custom business logic\nuser_orders = context.get('user', {}).get('total_orders', 0)\nif user_orders > 10:\n    context['discount'] = 20\nelse:\n    context['discount'] = 10"
}
```
  {"value": "remove_tag", "label": "Remove Tag"},
  {"value": "update_user", "label": "Update User"},
  {"value": "add_note", "label": "Add Note"},
  {"value": "webhook", "label": "Webhook"},
  {"value": "wait", "label": "Wait"},
  {"value": "set_conversation_status", "label": "Set Conversation Status"},
  {"value": "custom_code", "label": "Custom Code"}
]
```

### Get Action Parameter Templates
```bash
GET /actions/parameter_templates/?action_type=send_message
```

### Test Action
```bash
POST /actions/{id}/test/
```

**Request Body:**
```json
{
  "context": {
    "user": {
      "id": "customer-123",
      "first_name": "John",
      "email": "john@example.com"
    },
    "event": {
      "type": "MESSAGE_RECEIVED"
    }
  }
}
```

## 🔍 Condition Management

### Node-Based Condition System

#### List Condition Nodes
```bash
GET /condition-nodes/
```

**Parameters:**
- `workflow` (UUID): Filter by workflow ID
- `combination_operator` (string): Filter by combination operator (`and`, `or`)
- `is_active` (boolean): Filter by active status

#### Create Condition Node via Workflow
```bash
POST /node-workflows/{workflow_id}/create_node/
```

**Request Body:**
```json
{
  "node_type": "condition",
  "title": "Message Type Check",
  "combination_operator": "or",
  "conditions": [
    {
      "type": "ai",
      "prompt": "Is this message asking for support?"
    },
    {
      "type": "message",
      "operator": "contains",
      "value": "help"
    },
    {
      "type": "message",
      "operator": "start_with", 
      "value": "hello"
    }
  ],
  "position_x": 300.0,
  "position_y": 200.0
}
```

#### Get Condition Configuration Options

**Get Available Condition Types:**
```bash
GET /condition-nodes/condition_types/
```
**Response:**
```json
[
  {"value": "ai", "label": "AI Condition"},
  {"value": "message", "label": "Message Condition"}
]
```

**Get Message Operators:**
```bash
GET /condition-nodes/message_operators/
```
**Response:**
```json
[
  {"value": "equals_to", "label": "Equals to (=)"},
  {"value": "not_equal", "label": "Not equal (≠)"},
  {"value": "start_with", "label": "Start with"},
  {"value": "end_with", "label": "End with"},
  {"value": "contains", "label": "Contains"}
]
```

**Get Combination Operators:**
```bash
GET /condition-nodes/combination_operators/
```
**Response:**
```json
[
  {"value": "and", "label": "AND"},
  {"value": "or", "label": "OR"}
]
```

#### Test Condition Node
```bash
POST /condition-nodes/{node_id}/test/
```

**Request Body:**
```json
{
  "context": {
    "event": {
      "data": {
        "content": "Hello, I need help with my account"
      }
    },
    "user": {
      "first_name": "John",
      "tags": ["premium"]
    }
  }
}
```

**Response:**
```json
{
  "condition_node_id": "uuid-here",
  "condition_node_title": "Message Type Check",
  "conditions_match": true,
  "test_context": {...}
}
```

### Condition Structure Examples

**AI Condition:**
```json
{
  "type": "ai",
  "prompt": "Does the customer seem frustrated or angry?"
}
```

**Message Conditions:**
```json
{
  "type": "message",
  "operator": "equals_to",
  "value": "yes"
}
```

```json
{
  "type": "message", 
  "operator": "contains",
  "value": "refund"
}
```

```json
{
  "type": "message",
  "operator": "start_with",
  "value": "Good morning"
}
```

## 📊 Event Processing

### Event Types
```bash
GET /event-types/
```

**Response:**
```json
{
  "results": [
    {
      "id": "event-type-uuid",
      "name": "Message Received",
      "code": "MESSAGE_RECEIVED",
      "category": "message",
      "description": "Triggered when a customer message is received",
      "available_fields": {
        "message_id": "string",
        "conversation_id": "string",
        "user_id": "string",
        "content": "string",
        "source": "string",
        "timestamp": "datetime"
      }
    }
  ]
}
```

### Common Event Types:
- `MESSAGE_RECEIVED` - Customer sends a message
- `MESSAGE_SENT` - Message sent to customer
- `USER_CREATED` - New customer registration
- `CONVERSATION_CREATED` - New conversation started
- `CONVERSATION_CLOSED` - Conversation ended
- `TAG_ADDED` - Tag added to customer
- `TAG_REMOVED` - Tag removed from customer
- `SCHEDULED` - Scheduled trigger execution

## 📈 Monitoring & Analytics

### Workflow Executions
```bash
GET /workflow-executions/
```

**Parameters:**
- `status`: Filter by execution status
- `workflow`: Filter by workflow ID
- `user`: Filter by user ID
- `created_at__gte`: Filter by date (greater than or equal)

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/workflow-executions/?status=COMPLETED&workflow=workflow-uuid"
```

### Action Executions
```bash
GET /workflow-action-executions/
```

### Event Logs
```bash
GET /trigger-event-logs/
```

**Parameters:**
- `event_type`: Filter by event type
- `user_id`: Filter by user
- `conversation_id`: Filter by conversation

### Action Logs
```bash
GET /action-logs/
```

**Parameters:**
- `success`: Filter by success status
- `action`: Filter by action ID

### Cancel Execution
```bash
POST /workflow-executions/{id}/cancel/
```

## 📝 Common Response Formats

### Success Response
```json
{
  "id": "uuid",
  "field1": "value1",
  "field2": "value2",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### Paginated Response
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/workflow/api/workflows/?page=3",
  "previous": "http://localhost:8000/api/v1/workflow/api/workflows/?page=1",
  "results": [...]
}
```

### Error Response
```json
{
  "error": "Workflow not found",
  "detail": "No Workflow matches the given query."
}
```

### Validation Error Response
```json
{
  "name": ["This field is required."],
  "trigger_type": ["Select a valid choice."]
}
```

## ⚠️ Error Handling

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

### Common Error Scenarios

**Authentication Error:**
```bash
# Missing or invalid token
HTTP 401 Unauthorized
{
  "detail": "Authentication credentials were not provided."
}
```

**Validation Error:**
```bash
# Invalid data in request
HTTP 400 Bad Request
{
  "name": ["This field is required."],
  "action_type": ["Select a valid choice."]
}
```

**Not Found Error:**
```bash
HTTP 404 Not Found
{
  "detail": "Not found."
}
```

## 🚀 Usage Examples

### Complete Workflow Setup Example

```bash
# 1. Create a trigger
TRIGGER_ID=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Discount Request",
    "trigger_type": "MESSAGE_RECEIVED",
    "filters": {
      "operator": "or",
      "conditions": [
        {"field": "event.data.content", "operator": "icontains", "value": "discount"},
        {"field": "event.data.content", "operator": "icontains", "value": "coupon"}
      ]
    }
  }' \
  "http://localhost:8000/api/v1/workflow/api/triggers/" | jq -r '.id')

# 2. Create actions
ACTION1_ID=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Send Discount Code",
    "action_type": "send_message",
    "configuration": {
      "message": "Here is your discount code: SAVE20"
    },
    "order": 1
  }' \
  "http://localhost:8000/api/v1/workflow/api/actions/" | jq -r '.id')

# 3. Create workflow
WORKFLOW_ID=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Discount Code Campaign",
    "description": "Send discount codes when requested",
    "status": "DRAFT"
  }' \
  "http://localhost:8000/api/v1/workflow/api/workflows/" | jq -r '.id')

# 4. Associate trigger with workflow
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"trigger_id\": \"$TRIGGER_ID\", \"priority\": 100}" \
  "http://localhost:8000/api/v1/workflow/api/workflows/$WORKFLOW_ID/add_trigger/"

# 5. Activate workflow
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/workflows/$WORKFLOW_ID/activate/"

# 6. Test with an event
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "MESSAGE_RECEIVED",
    "data": {
      "message_id": "test-123",
      "content": "Do you have any discount codes?",
      "timestamp": "2024-01-01T10:00:00Z"
    },
    "user_id": "customer-123",
    "conversation_id": "conv-456"
  }' \
  "http://localhost:8000/api/v1/workflow/api/triggers/process_event/"
```

### Monitoring Workflow Performance

```bash
# Get workflow statistics
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/workflows/statistics/"

# Monitor recent executions
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/workflow-executions/?page_size=10"

# Check failed executions
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/workflow-executions/?status=FAILED"
```

## 🔗 Node-Based Workflow Management

The enhanced workflow system supports visual, node-based workflow creation with drag-and-drop interface.

### Node-Based Workflow Operations

#### Get All Nodes for Workflow
```bash
GET /node-workflows/{workflow_id}/nodes/
```

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/node-workflows/workflow-uuid/nodes/"
```

#### Create Node for Workflow
```bash
POST /node-workflows/{workflow_id}/create_node/
```

**Request Body Examples:**

**When Node:**
```json
{
  "node_type": "when",
  "title": "New Message Received",
  "when_type": "receive_message",
  "keywords": ["help", "support"],
  "channels": ["telegram", "instagram"],
  "position_x": 100,
  "position_y": 200
}
```

**Condition Node:**
```json
{
  "node_type": "condition",
  "title": "Check Support Request",
  "combination_operator": "or",
  "conditions": [
    {
      "type": "ai",
      "prompt": "Is this a technical support request?"
    },
    {
      "type": "message",
      "operator": "contains",
      "value": "technical"
    }
  ],
  "position_x": 300,
  "position_y": 200
}
```

**Action Node:**
```json
{
  "node_type": "action",
  "title": "Send Response",
  "action_type": "send_message",
  "message_content": "Thank you for contacting support!",
  "position_x": 500,
  "position_y": 200
}
```

**Waiting Node:**
```json
{
  "node_type": "waiting",
  "title": "Collect Email",
  "answer_type": "email",
  "storage_type": "user_profile",
  "storage_field": "email",
  "customer_message": "Please provide your email:",
  "response_time_limit_enabled": true,
  "response_timeout_amount": 10,
  "response_timeout_unit": "minutes",
  "position_x": 700,
  "position_y": 200
}
```

#### Create Connection Between Nodes
```bash
POST /node-workflows/{workflow_id}/create_connection/
```

**Request Body:**
```json
{
  "source_node": "source-node-uuid",
  "target_node": "target-node-uuid",
  "connection_type": "success"
}
```

### Individual Node Management

#### When Nodes
```bash
GET /when-nodes/                    # List all
POST /when-nodes/                   # Create
GET /when-nodes/{id}/              # Get details
PUT /when-nodes/{id}/              # Update
DELETE /when-nodes/{id}/           # Delete
GET /when-nodes/when_types/        # Get available when types
```

#### Condition Nodes
```bash
GET /condition-nodes/                         # List all
POST /condition-nodes/                        # Create
GET /condition-nodes/{id}/                   # Get details
PUT /condition-nodes/{id}/                   # Update
DELETE /condition-nodes/{id}/                # Delete
GET /condition-nodes/condition_types/        # Get condition types
GET /condition-nodes/message_operators/      # Get message operators
GET /condition-nodes/combination_operators/  # Get combination operators
POST /condition-nodes/{id}/test/             # Test condition
```

#### Action Nodes
```bash
GET /action-nodes/                    # List all
POST /action-nodes/                   # Create
GET /action-nodes/{id}/              # Get details
PUT /action-nodes/{id}/              # Update
DELETE /action-nodes/{id}/           # Delete
GET /action-nodes/action_types/      # Get action types
GET /action-nodes/redirect_destinations/  # Get redirect options
GET /action-nodes/delay_units/       # Get delay time units
GET /action-nodes/webhook_methods/   # Get webhook HTTP methods
```

#### Waiting Nodes
```bash
GET /waiting-nodes/                  # List all
POST /waiting-nodes/                 # Create
GET /waiting-nodes/{id}/            # Get details
PUT /waiting-nodes/{id}/            # Update
DELETE /waiting-nodes/{id}/         # Delete
GET /waiting-nodes/answer_types/     # Get answer types
GET /waiting-nodes/storage_types/    # Get storage types
GET /waiting-nodes/time_units/       # Get time units
GET /waiting-nodes/{id}/responses/   # Get user responses
```

#### Node Connections
```bash
GET /node-connections/                    # List all
POST /node-connections/                   # Create
GET /node-connections/{id}/              # Get details
PUT /node-connections/{id}/              # Update
DELETE /node-connections/{id}/           # Delete single connection
GET /node-connections/connection_types/   # Get connection types
GET /node-connections/statistics/         # Get connection statistics

# Bulk and Advanced Delete Operations
POST /node-connections/bulk_delete/       # Delete multiple connections
DELETE /node-connections/delete_by_nodes/ # Delete connections between specific nodes
DELETE /node-connections/delete_by_workflow/ # Delete all connections for workflow
DELETE /node-connections/delete_orphaned/ # Delete orphaned connections
```

### Node Configuration Options

#### Get When Types
```bash
GET /when-nodes/when_types/
```

**Response:**
```json
[
  {"value": "receive_message", "label": "Receive Message"},
  {"value": "new_customer", "label": "New Customer"},
  {"value": "add_tag", "label": "Add Tag"},
  {"value": "scheduled", "label": "Scheduled"}
]
```

#### Get Condition Types and Operators
```bash
GET /condition-nodes/condition_types/
GET /condition-nodes/message_operators/
GET /condition-nodes/combination_operators/
```

#### Get Action Types
```bash
GET /action-nodes/action_types/
```

**Response:**
```json
[
  {"value": "send_message", "label": "Send Message"},
  {"value": "delay", "label": "Delay"},
  {"value": "redirect_conversation", "label": "Redirect Conversation"},
  {"value": "add_tag", "label": "Add Tag"},
  {"value": "remove_tag", "label": "Remove Tag"},
  {"value": "transfer_to_human", "label": "Transfer to Human"},
  {"value": "send_email", "label": "Send Email"},
  {"value": "webhook", "label": "Webhook"},
  {"value": "custom_code", "label": "Custom Code"}
]
```

#### Get Storage Types for Waiting Nodes
```bash
GET /waiting-nodes/storage_types/
```

**Response:**
```json
[
  {"value": "user_profile", "label": "User Profile"},
  {"value": "custom_field", "label": "Custom Field"},
  {"value": "database", "label": "Database"},
  {"value": "session", "label": "Session Storage"},
  {"value": "temporary", "label": "Temporary Storage"}
]
```

### Execute Node-Based Workflow
```bash
POST /node-workflows/{workflow_id}/execute_with_nodes/
```

**Request Body:**
```json
{
  "context": {
    "event": {
      "type": "MESSAGE_RECEIVED",
      "data": {
        "content": "I need technical support",
        "user_id": "customer-123"
      }
    },
    "user": {
      "id": "customer-123",
      "first_name": "John"
    }
  }
}
```

## 🎯 Unified Node Management API

The new unified API provides a single endpoint for complete node management across all node types, featuring intelligent PATCH updates and advanced position management.

### 🧠 Smart PATCH API Features

The enhanced PATCH endpoint now provides intelligent updating capabilities:
- **✅ Accepts any field** and applies changes appropriately
- **✅ Automatic merging** for arrays (keywords, tags, channels, conditions)
- **✅ Advanced position management** with grid snapping and bounds checking
- **✅ Smart JSON handling** for webhook headers/payload
- **✅ Replacement options** with special flags
- **✅ Combine position + content updates** in single request

📚 **Complete Documentation:** See [Smart PATCH API Documentation](./SMART_PATCH_API_DOCUMENTATION.md) for detailed examples and usage.

### 🚀 Smart PATCH Quick Examples

**Position Updates:**
```json
PATCH /nodes/{id}/
{
  "position_x": 450,
  "position_y": 350,
  "snap_to_grid": true,
  "grid_size": 25
}
```

**Content + Position Combined:**
```json
PATCH /nodes/{id}/
{
  "title": "Updated Node",
  "keywords": ["new", "keywords"],
  "position": {"x": 500, "y": 300},
  "snap_to_grid": true
}
```

**Relative Movement:**
```json
PATCH /nodes/{id}/
{
  "move_by": {"x": 50, "y": -30},
  "enforce_bounds": {
    "min_x": 0, "max_x": 2000,
    "min_y": 0, "max_y": 1500
  }
}
```

**Array Merging (default) vs Replacement:**
```json
// Merge new keywords with existing
{
  "keywords": ["help", "support"]
}

// Replace all keywords
{
  "keywords": ["new", "keywords"],
  "replace_keywords": true
}
```

### Unified Node Endpoints
```bash
GET /nodes/                    # List all nodes with filters
POST /nodes/                   # Create any type of node
GET /nodes/{id}/              # Get node details with connections
PUT /nodes/{id}/              # Update complete node
PATCH /nodes/{id}/            # Partial update node
DELETE /nodes/{id}/           # Delete node and all connections
```

### Unified Node Creation

**Create When Node:**
```bash
POST /nodes/
```
```json
{
  "node_type": "when",
  "workflow": "workflow-uuid",
  "title": "New Customer Registration",
  "when_type": "new_customer",
  "keywords": ["signup", "register"],
  "channels": ["telegram", "instagram"],
  "position_x": 100,
  "position_y": 200
}
```

**Create Condition Node:**
```bash
POST /nodes/
```
```json
{
  "node_type": "condition",
  "workflow": "workflow-uuid",
  "title": "Check Support Type",
  "combination_operator": "or",
  "conditions": [
    {
      "type": "ai",
      "prompt": "Is this a technical support request?"
    },
    {
      "type": "message",
      "operator": "contains",
      "value": "technical"
    }
  ],
  "position_x": 300,
  "position_y": 200
}
```

**Create Action Node:**
```bash
POST /nodes/
```
```json
{
  "node_type": "action",
  "workflow": "workflow-uuid",
  "title": "Send Welcome Message",
  "action_type": "send_message",
  "message_content": "Welcome to our service! How can we help you?",
  "position_x": 500,
  "position_y": 200
}
```

**Create Waiting Node:**
```bash
POST /nodes/
```
```json
{
  "node_type": "waiting",
  "workflow": "workflow-uuid",
  "title": "Collect User Email",
  "answer_type": "email",
  "storage_type": "user_profile",
  "storage_field": "email",
  "customer_message": "Please provide your email address:",
  "response_time_limit_enabled": true,
  "response_timeout_amount": 10,
  "response_timeout_unit": "minutes",
  "position_x": 700,
  "position_y": 200
}
```

### Unified Node Actions

#### Get Node Connections
```bash
GET /nodes/{node_id}/connections/
```

**Response:**
```json
{
  "node_id": "node-uuid",
  "node_title": "Node Title",
  "outgoing_connections": [
    {
      "id": "conn-uuid",
      "type": "outgoing",
      "target_node": {
        "id": "target-uuid",
        "title": "Target Node",
        "node_type": "action"
      },
      "connection_type": "success"
    }
  ],
  "incoming_connections": [
    {
      "id": "conn-uuid",
      "type": "incoming",
      "source_node": {
        "id": "source-uuid",
        "title": "Source Node",
        "node_type": "when"
      },
      "connection_type": "success"
    }
  ],
  "total_connections": 2
}
```

#### Duplicate Node
```bash
POST /nodes/{node_id}/duplicate/
```

**Response:**
```json
{
  "message": "Node 'Original Title' duplicated successfully",
  "original_node_id": "original-uuid",
  "duplicated_node": {
    "id": "new-uuid",
    "title": "Original Title (Copy)",
    "position_x": 150,
    "position_y": 250
  }
}
```

#### Get Available Node Types
```bash
GET /nodes/types/
```

**Response:**
```json
[
  {
    "value": "when",
    "label": "When Node",
    "description": "Triggers that start the workflow",
    "icon": "▶️",
    "color": "#4CAF50"
  },
  {
    "value": "condition",
    "label": "Condition Node",
    "description": "Logic conditions to control flow",
    "icon": "❓",
    "color": "#FF9800"
  },
  {
    "value": "action",
    "label": "Action Node",
    "description": "Actions to perform",
    "icon": "⚡",
    "color": "#2196F3"
  },
  {
    "value": "waiting",
    "label": "Waiting Node",
    "description": "Wait for user input",
    "icon": "⏳",
    "color": "#9C27B0"
  }
]
```

#### Get Nodes by Workflow
```bash
GET /nodes/by_workflow/?workflow_id=workflow-uuid
```

**Response:**
```json
{
  "workflow_id": "workflow-uuid",
  "workflow_name": "Customer Support Flow",
  "nodes": {
    "when": [
      {
        "id": "when-uuid",
        "title": "New Message",
        "when_type": "receive_message"
      }
    ],
    "condition": [
      {
        "id": "condition-uuid", 
        "title": "Check Priority",
        "combination_operator": "and"
      }
    ],
    "action": [
      {
        "id": "action-uuid",
        "title": "Send Response",
        "action_type": "send_message"
      }
    ],
    "waiting": [
      {
        "id": "waiting-uuid",
        "title": "Get Rating",
        "answer_type": "number"
      }
    ]
  },
  "total_nodes": 4
}
```

#### Test Node Execution
```bash
POST /nodes/{node_id}/test_execution/
```

**Request Body:**
```json
{
  "context": {
    "event": {
      "type": "MESSAGE_RECEIVED",
      "data": {
        "content": "I need help with my order",
        "user_id": "customer-123"
      }
    }
  }
}
```

**Response:**
```json
{
  "node_type": "condition",
  "condition_met": true,
  "message": "Condition node 'Check Support Type' evaluation result",
  "node_id": "node-uuid",
  "node_title": "Check Support Type",
  "test_context": {...},
  "timestamp": "2024-01-01T10:00:00Z"
}
```

#### Activate/Deactivate Node
```bash
POST /nodes/{node_id}/activate/
POST /nodes/{node_id}/deactivate/
```

**Response:**
```json
{
  "message": "Node 'Node Title' activated successfully",
  "node_id": "node-uuid",
  "is_active": true
}
```

### Advanced Filtering

**Filter by node type:**
```bash
GET /nodes/?node_type=action
```

**Filter by workflow:**
```bash
GET /nodes/?workflow=workflow-uuid
```

**Search by title:**
```bash
GET /nodes/?search=welcome
```

**Combine filters:**
```bash
GET /nodes/?node_type=action&workflow=workflow-uuid&is_active=true
```

## 🔗 Connection Management API

Enhanced connection management with advanced delete operations.

### Single Connection Delete

```bash
DELETE /node-connections/{connection-id}/
```

**Response:**
```json
{
  "message": "Connection deleted successfully",
  "deleted_connection": {
    "id": "connection-uuid",
    "source_node": {
      "id": "source-uuid",
      "title": "Source Node"
    },
    "target_node": {
      "id": "target-uuid", 
      "title": "Target Node"
    },
    "connection_type": "success",
    "workflow": {
      "id": "workflow-uuid",
      "name": "Workflow Name"
    }
  },
  "status": "success"
}
```

### Bulk Connection Delete

```bash
POST /node-connections/bulk_delete/
```

**Request Body:**
```json
{
  "connection_ids": [
    "conn-uuid-1",
    "conn-uuid-2", 
    "conn-uuid-3"
  ]
}
```

**Response:**
```json
{
  "message": "Successfully deleted 3 connections",
  "deleted_count": 3,
  "deleted_connections": [
    {
      "id": "conn-uuid-1",
      "source_node_title": "When Node",
      "target_node_title": "Action Node",
      "connection_type": "success"
    }
  ],
  "status": "success"
}
```

### Delete Connections Between Specific Nodes

```bash
DELETE /node-connections/delete_by_nodes/?source_node=source-uuid&target_node=target-uuid&connection_type=success
```

**Response:**
```json
{
  "message": "Successfully deleted 2 connections between nodes",
  "deleted_count": 2,
  "source_node_id": "source-uuid",
  "target_node_id": "target-uuid",
  "deleted_connections": [
    {
      "id": "conn-uuid-1",
      "connection_type": "success",
      "condition": {}
    }
  ],
  "status": "success"
}
```

### Delete All Connections for Workflow

```bash
DELETE /node-connections/delete_by_workflow/?workflow_id=workflow-uuid
```

**Response:**
```json
{
  "message": "Successfully deleted all 15 connections for workflow \"Customer Support Flow\"",
  "deleted_count": 15,
  "workflow_id": "workflow-uuid",
  "workflow_name": "Customer Support Flow",
  "status": "success"
}
```

### Delete Orphaned Connections

```bash
DELETE /node-connections/delete_orphaned/
```

**Response:**
```json
{
  "message": "Successfully deleted 3 orphaned connections",
  "deleted_count": 3,
  "status": "success"
}
```

### Node-Level Connection Management

**Delete all connections for a specific node:**
```bash
DELETE /nodes/{node-id}/delete_connections/
```

**Disconnect from specific target nodes:**
```bash
POST /nodes/{node-id}/disconnect_from/
```
```json
{
  "target_node_ids": ["target-uuid-1", "target-uuid-2"],
  "connection_type": "success"
}
```

**Delete only incoming connections:**
```bash
POST /nodes/{node-id}/disconnect_incoming/
```

**Delete only outgoing connections:**
```bash
POST /nodes/{node-id}/disconnect_outgoing/
```

### Connection Statistics

```bash
GET /node-connections/statistics/
```

**Response:**
```json
{
  "total_connections": 156,
  "by_type": {
    "success": {
      "count": 120,
      "label": "Success"
    },
    "failure": {
      "count": 25,
      "label": "Failure"
    },
    "timeout": {
      "count": 8,
      "label": "Timeout"
    },
    "skip": {
      "count": 3,
      "label": "Skip"
    }
  },
  "by_workflow": {
    "workflow-uuid-1": {
      "name": "Customer Support Flow",
      "count": 45
    },
    "workflow-uuid-2": {
      "name": "Lead Generation", 
      "count": 32
    }
  },
  "recent_connections": [
    {
      "id": "conn-uuid",
      "source_node__title": "New Message",
      "target_node__title": "Send Response",
      "connection_type": "success",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

---

This comprehensive API reference provides everything needed to integrate and use the Marketing Workflow system programmatically. All endpoints support standard REST operations and follow consistent patterns for easy integration.
