# Unified Node API - Complete Examples

This document provides comprehensive examples for using the new Unified Node Management API.

## 📋 Table of Contents

- [Basic Operations](#basic-operations)
- [Node Type Examples](#node-type-examples)
- [Advanced Operations](#advanced-operations)
- [Real-world Scenarios](#real-world-scenarios)
- [Error Handling](#error-handling)
- [Testing Examples](#testing-examples)

## 🌐 Base Information

**Base URL:** `/api/v1/workflow/api/nodes/`  
**Authentication:** Required (Bearer Token)  
**Content-Type:** `application/json`

## 🔧 Basic Operations

### 1. List All Nodes

```bash
GET /api/v1/workflow/api/nodes/

# With filters
GET /api/v1/workflow/api/nodes/?node_type=action
GET /api/v1/workflow/api/nodes/?workflow=workflow-uuid
GET /api/v1/workflow/api/nodes/?search=welcome
GET /api/v1/workflow/api/nodes/?is_active=true&node_type=when
```

**Response:**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/workflow/api/nodes/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "node_type": "when",
      "title": "New Customer Registration",
      "workflow": "workflow-uuid",
      "workflow_name": "Customer Onboarding",
      "when_type": "new_customer",
      "position_x": 100,
      "position_y": 200,
      "is_active": true,
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

### 2. Get Node Details

```bash
GET /api/v1/workflow/api/nodes/{node-id}/
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "node_type": "action",
  "title": "Send Welcome Message",
  "workflow": "workflow-uuid",
  "workflow_name": "Customer Onboarding",
  "action_type": "send_message",
  "action_type_display": "Send Message",
  "message_content": "Welcome to our platform! 🎉",
  "position_x": 300,
  "position_y": 200,
  "is_active": true,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "connections_as_source": [
    {
      "id": "conn-uuid-1",
      "target_node": "target-uuid",
      "target_node_title": "Wait for Response",
      "connection_type": "success",
      "condition": {}
    }
  ],
  "connections_as_target": [
    {
      "id": "conn-uuid-2",
      "source_node": "source-uuid",
      "source_node_title": "New Customer",
      "connection_type": "success",
      "condition": {}
    }
  ]
}
```

## 🎯 Node Type Examples

### 1. Create When Node

**Receive Message Trigger:**
```bash
POST /api/v1/workflow/api/nodes/
```
```json
{
  "node_type": "when",
  "workflow": "workflow-uuid",
  "title": "New Support Message",
  "when_type": "receive_message",
  "keywords": ["help", "support", "problem"],
  "channels": ["telegram", "instagram"],
  "position_x": 100,
  "position_y": 200
}
```

**Scheduled Trigger:**
```json
{
  "node_type": "when",
  "workflow": "workflow-uuid",
  "title": "Daily Check-in",
  "when_type": "scheduled",
  "schedule_frequency": "daily",
  "schedule_time": "09:00:00",
  "position_x": 100,
  "position_y": 300
}
```

**New Customer Trigger:**
```json
{
  "node_type": "when",
  "workflow": "workflow-uuid",
  "title": "Welcome New Customers",
  "when_type": "new_customer",
  "customer_tags": ["new", "trial"],
  "position_x": 100,
  "position_y": 400
}
```

### 2. Create Condition Node

**AI-based Condition:**
```bash
POST /api/v1/workflow/api/nodes/
```
```json
{
  "node_type": "condition",
  "workflow": "workflow-uuid",
  "title": "Check Intent",
  "combination_operator": "and",
  "conditions": [
    {
      "type": "ai",
      "prompt": "Is this customer asking about pricing or billing?"
    },
    {
      "type": "message",
      "operator": "contains",
      "value": "price"
    }
  ],
  "position_x": 300,
  "position_y": 200
}
```

**Message-based Conditions:**
```json
{
  "node_type": "condition",
  "workflow": "workflow-uuid",
  "title": "Check Priority",
  "combination_operator": "or",
  "conditions": [
    {
      "type": "message",
      "operator": "contains",
      "value": "urgent"
    },
    {
      "type": "message",
      "operator": "start_with",
      "value": "URGENT:"
    },
    {
      "type": "message",
      "operator": "equals",
      "value": "emergency"
    }
  ],
  "position_x": 300,
  "position_y": 300
}
```

### 3. Create Action Node

**Send Message:**
```bash
POST /api/v1/workflow/api/nodes/
```
```json
{
  "node_type": "action",
  "workflow": "workflow-uuid",
  "title": "Send Welcome",
  "action_type": "send_message",
  "message_content": "Welcome to our service! How can we help you today?",
  "position_x": 500,
  "position_y": 200
}
```

**Delay Action:**
```json
{
  "node_type": "action",
  "workflow": "workflow-uuid",
  "title": "Wait 5 Minutes",
  "action_type": "delay",
  "delay_amount": 5,
  "delay_unit": "minutes",
  "position_x": 500,
  "position_y": 300
}
```

**Send Email:**
```json
{
  "node_type": "action",
  "workflow": "workflow-uuid",
  "title": "Send Notification Email",
  "action_type": "send_email",
  "email_to": "admin@company.com",
  "email_subject": "New Customer Alert",
  "email_body": "A new customer has joined the platform.",
  "position_x": 500,
  "position_y": 400
}
```

**Webhook:**
```json
{
  "node_type": "action",
  "workflow": "workflow-uuid",
  "title": "Notify CRM",
  "action_type": "webhook",
  "webhook_url": "https://api.crm.com/webhook",
  "webhook_method": "POST",
  "webhook_headers": {
    "Authorization": "Bearer token",
    "Content-Type": "application/json"
  },
  "webhook_payload": {
    "event": "new_customer",
    "timestamp": "{{now}}"
  },
  "position_x": 500,
  "position_y": 500
}
```

### 4. Create Waiting Node

**Email Collection:**
```bash
POST /api/v1/workflow/api/nodes/
```
```json
{
  "node_type": "waiting",
  "workflow": "workflow-uuid",
  "title": "Collect Email",
  "answer_type": "email",
  "storage_type": "user_profile",
  "storage_field": "email",
  "customer_message": "Please provide your email address for updates:",
  "response_time_limit_enabled": true,
  "response_timeout_amount": 10,
  "response_timeout_unit": "minutes",
  "allowed_errors": 3,
  "position_x": 700,
  "position_y": 200
}
```

**Rating Collection:**
```json
{
  "node_type": "waiting",
  "workflow": "workflow-uuid",
  "title": "Service Rating",
  "answer_type": "number",
  "storage_type": "database",
  "storage_field": "service_rating",
  "customer_message": "Please rate our service from 1 to 10:",
  "response_time_limit_enabled": true,
  "response_timeout_amount": 30,
  "response_timeout_unit": "minutes",
  "allowed_errors": 2,
  "skip_keywords": ["skip", "later"],
  "position_x": 700,
  "position_y": 300
}
```

**Choice Selection:**
```json
{
  "node_type": "waiting",
  "workflow": "workflow-uuid",
  "title": "Choose Department",
  "answer_type": "choice",
  "storage_type": "session",
  "storage_field": "selected_department",
  "customer_message": "Which department do you need help with?",
  "choice_options": [
    "Technical Support",
    "Billing",
    "Sales",
    "General Inquiry"
  ],
  "response_time_limit_enabled": false,
  "allowed_errors": 3,
  "position_x": 700,
  "position_y": 400
}
```

## 🚀 Advanced Operations

### 1. Update Node

**Complete Update (PUT):**
```bash
PUT /api/v1/workflow/api/nodes/{node-id}/
```
```json
{
  "node_type": "action",
  "workflow": "workflow-uuid",
  "title": "Updated Welcome Message",
  "action_type": "send_message",
  "message_content": "Welcome! We're excited to have you here! 🎉",
  "position_x": 350,
  "position_y": 250,
  "is_active": true
}
```

**Partial Update (PATCH):**
```bash
PATCH /api/v1/workflow/api/nodes/{node-id}/
```
```json
{
  "title": "New Title",
  "position_x": 400,
  "is_active": false
}
```

### 2. Delete Node

```bash
DELETE /api/v1/workflow/api/nodes/{node-id}/
```

**Response:**
```json
{
  "message": "Node 'Welcome Message' and its connections have been deleted successfully",
  "deleted_connections": "All connections involving this node were removed"
}
```

### 3. Get Node Connections

```bash
GET /api/v1/workflow/api/nodes/{node-id}/connections/
```

**Response:**
```json
{
  "node_id": "node-uuid",
  "node_title": "Send Welcome",
  "outgoing_connections": [
    {
      "id": "conn-1",
      "type": "outgoing",
      "target_node": {
        "id": "target-uuid",
        "title": "Wait for Response",
        "node_type": "waiting"
      },
      "connection_type": "success",
      "condition": {}
    }
  ],
  "incoming_connections": [
    {
      "id": "conn-2",
      "type": "incoming",
      "source_node": {
        "id": "source-uuid",
        "title": "New Customer",
        "node_type": "when"
      },
      "connection_type": "success",
      "condition": {}
    }
  ],
  "total_connections": 2
}
```

### 4. Duplicate Node

```bash
POST /api/v1/workflow/api/nodes/{node-id}/duplicate/
```

**Response:**
```json
{
  "message": "Node 'Send Welcome' duplicated successfully",
  "original_node_id": "original-uuid",
  "duplicated_node": {
    "id": "new-uuid",
    "title": "Send Welcome (Copy)",
    "node_type": "action",
    "position_x": 550,
    "position_y": 250,
    "action_type": "send_message",
    "message_content": "Welcome! We're excited to have you here! 🎉"
  }
}
```

### 5. Activate/Deactivate Node

```bash
POST /api/v1/workflow/api/nodes/{node-id}/activate/
POST /api/v1/workflow/api/nodes/{node-id}/deactivate/
```

**Response:**
```json
{
  "message": "Node 'Send Welcome' activated successfully",
  "node_id": "node-uuid",
  "is_active": true
}
```

### 6. Test Node Execution

```bash
POST /api/v1/workflow/api/nodes/{node-id}/test_execution/
```

**Request Body:**
```json
{
  "context": {
    "event": {
      "type": "MESSAGE_RECEIVED",
      "data": {
        "content": "I need help with billing",
        "user_id": "customer-123",
        "channel": "telegram"
      }
    },
    "user": {
      "id": "customer-123",
      "first_name": "John",
      "email": "john@example.com"
    }
  }
}
```

**Response:**
```json
{
  "node_type": "condition",
  "condition_met": true,
  "message": "Condition node 'Check Intent' evaluation result",
  "node_id": "node-uuid",
  "node_title": "Check Intent",
  "test_context": {
    "event": {...},
    "user": {...}
  },
  "timestamp": "2024-01-01T10:30:00Z"
}
```

## 🎪 Real-world Scenarios

### Scenario 1: Customer Support Flow

**Step 1: Create When Node**
```json
{
  "node_type": "when",
  "workflow": "support-workflow-uuid",
  "title": "Support Request",
  "when_type": "receive_message",
  "keywords": ["help", "support", "problem", "issue"],
  "position_x": 100,
  "position_y": 200
}
```

**Step 2: Create Condition Node**
```json
{
  "node_type": "condition",
  "workflow": "support-workflow-uuid",
  "title": "Check Urgency",
  "combination_operator": "or",
  "conditions": [
    {
      "type": "message",
      "operator": "contains",
      "value": "urgent"
    },
    {
      "type": "ai",
      "prompt": "Is this an urgent support request?"
    }
  ],
  "position_x": 300,
  "position_y": 200
}
```

**Step 3: Create Action Nodes**
```json
// For urgent cases
{
  "node_type": "action",
  "workflow": "support-workflow-uuid",
  "title": "Urgent Response",
  "action_type": "send_message",
  "message_content": "We've received your urgent request. A specialist will contact you within 15 minutes.",
  "position_x": 500,
  "position_y": 150
}

// For normal cases
{
  "node_type": "action",
  "workflow": "support-workflow-uuid",
  "title": "Standard Response",
  "action_type": "send_message",
  "message_content": "Thank you for contacting support. We'll get back to you within 24 hours.",
  "position_x": 500,
  "position_y": 250
}
```

### Scenario 2: Lead Generation Flow

**Step 1: New Customer Welcome**
```json
{
  "node_type": "when",
  "workflow": "lead-gen-uuid",
  "title": "New Lead",
  "when_type": "new_customer",
  "position_x": 100,
  "position_y": 200
}
```

**Step 2: Welcome Message**
```json
{
  "node_type": "action",
  "workflow": "lead-gen-uuid",
  "title": "Welcome New Lead",
  "action_type": "send_message",
  "message_content": "Welcome! 🎉 We're excited to help you. What brings you here today?",
  "position_x": 300,
  "position_y": 200
}
```

**Step 3: Collect Information**
```json
{
  "node_type": "waiting",
  "workflow": "lead-gen-uuid",
  "title": "Get Email",
  "answer_type": "email",
  "storage_type": "user_profile",
  "storage_field": "email",
  "customer_message": "To get started, please share your email address:",
  "response_time_limit_enabled": true,
  "response_timeout_amount": 5,
  "response_timeout_unit": "minutes",
  "position_x": 500,
  "position_y": 200
}
```

**Step 4: Follow-up Action**
```json
{
  "node_type": "action",
  "workflow": "lead-gen-uuid",
  "title": "Send Follow-up Email",
  "action_type": "send_email",
  "email_to": "{{user.email}}",
  "email_subject": "Welcome to Our Platform!",
  "email_body": "Thanks for joining! Here's what you can do next...",
  "position_x": 700,
  "position_y": 200
}
```

## ⚠️ Error Handling

### Validation Errors

**Missing Required Fields:**
```json
{
  "node_type": ["This field is required."],
  "workflow": ["This field is required."],
  "title": ["This field is required."]
}
```

**Invalid Node Type:**
```json
{
  "node_type": ["Invalid node type: invalid_type"]
}
```

**When Node Validation:**
```json
{
  "when_type": ["When type is required for When nodes"],
  "schedule_frequency": ["Schedule frequency is required for scheduled when nodes"]
}
```

**Condition Node Validation:**
```json
{
  "conditions": ["At least one condition is required for Condition nodes"],
  "combination_operator": ["Combination operator must be \"and\" or \"or\""]
}
```

**Action Node Validation:**
```json
{
  "action_type": ["Action type is required for Action nodes"],
  "message_content": ["Message content is required for send_message actions"],
  "webhook_url": ["Webhook URL is required for webhook actions"]
}
```

**Waiting Node Validation:**
```json
{
  "answer_type": ["Answer type is required for Waiting nodes"],
  "customer_message": ["Customer message is required for Waiting nodes"],
  "choice_options": ["Choice options are required for choice answer type"]
}
```

## 🧪 Testing Examples

### Test 1: Create Complete Workflow

```bash
#!/bin/bash

TOKEN="your-jwt-token"
BASE_URL="http://localhost:8000/api/v1/workflow/api"
WORKFLOW_ID="your-workflow-uuid"

# 1. Create When Node
WHEN_NODE=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "when",
    "workflow": "'$WORKFLOW_ID'",
    "title": "New Message",
    "when_type": "receive_message",
    "keywords": ["hello", "hi"],
    "position_x": 100,
    "position_y": 200
  }' \
  "$BASE_URL/nodes/" | jq -r '.id')

# 2. Create Action Node
ACTION_NODE=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "action",
    "workflow": "'$WORKFLOW_ID'",
    "title": "Send Response",
    "action_type": "send_message",
    "message_content": "Hello! How can I help you?",
    "position_x": 300,
    "position_y": 200
  }' \
  "$BASE_URL/nodes/" | jq -r '.id')

echo "Created nodes: $WHEN_NODE -> $ACTION_NODE"

# 3. Test node execution
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "event": {
        "type": "MESSAGE_RECEIVED",
        "data": {
          "content": "hello there!",
          "user_id": "test-user"
        }
      }
    }
  }' \
  "$BASE_URL/nodes/$WHEN_NODE/test_execution/"
```

### Test 2: Node Management Operations

```bash
#!/bin/bash

TOKEN="your-jwt-token"
BASE_URL="http://localhost:8000/api/v1/workflow/api/nodes"

# List all nodes
echo "📋 Listing all nodes:"
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/"

# Filter by type
echo "🎯 Action nodes only:"
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/?node_type=action"

# Search nodes
echo "🔍 Search for 'welcome':"
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/?search=welcome"

# Get node types
echo "📝 Available node types:"
curl -H "Authorization: Bearer $TOKEN" "$BASE_URL/types/"
```

---

This comprehensive guide covers all aspects of the Unified Node Management API. Use these examples as templates for building your own workflow automation systems!
