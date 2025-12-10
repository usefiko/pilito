# Key-Values API Quick Reference

## Overview
Quick reference for using the key_values field in workflow nodes.

## Format
```
key_values: ["CTA:Button Text|https://url.com"]
```

## API Endpoints

### 1. Create Action Node with key_values

**Endpoint:** `POST /api/v1/workflow/api/nodes/`

**Request:**
```json
{
  "node_type": "action",
  "workflow": "workflow-uuid",
  "title": "Send Message",
  "action_type": "send_message",
  "message_content": "Hello! Check this out.",
  "key_values": [
    "CTA:View Products|https://example.com/products",
    "CTA:Contact Us|https://example.com/contact"
  ],
  "position_x": 100,
  "position_y": 200
}
```

**Response:**
```json
{
  "id": "node-uuid",
  "node_type": "action",
  "title": "Send Message",
  "action_type": "send_message",
  "message_content": "Hello! Check this out.",
  "key_values": [
    "CTA:View Products|https://example.com/products",
    "CTA:Contact Us|https://example.com/contact"
  ],
  "workflow": "workflow-uuid",
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### 2. Create Waiting Node with key_values

**Endpoint:** `POST /api/v1/workflow/api/nodes/`

**Request:**
```json
{
  "node_type": "waiting",
  "workflow": "workflow-uuid",
  "title": "Get Feedback",
  "storage_type": "text",
  "customer_message": "Please rate our service",
  "key_values": [
    "CTA:Rate Now|https://example.com/rate"
  ],
  "response_time_limit_enabled": true,
  "response_timeout_amount": 30,
  "response_timeout_unit": "minutes",
  "position_x": 300,
  "position_y": 200
}
```

---

### 3. Update key_values (PATCH)

**Endpoint:** `PATCH /api/v1/workflow/api/nodes/{node_id}/`

**Request:**
```json
{
  "key_values": [
    "CTA:Updated Link|https://example.com/new"
  ]
}
```

**Response:**
```json
{
  "id": "node-uuid",
  "key_values": [
    "CTA:Updated Link|https://example.com/new"
  ],
  "message_content": "Hello! Check this out.",
  "...": "other fields"
}
```

---

### 4. Add key_values (PATCH - merge)

**Endpoint:** `PATCH /api/v1/workflow/api/nodes/{node_id}/`

**Request:**
```json
{
  "key_values": [
    "CTA:Third Button|https://example.com/third"
  ]
}
```

**Note:** By default, PATCH replaces the entire key_values array. The system handles this at the model level.

---

### 5. Get Node with key_values

**Endpoint:** `GET /api/v1/workflow/api/nodes/{node_id}/`

**Response:**
```json
{
  "id": "node-uuid",
  "node_type": "action",
  "title": "Send Message",
  "action_type": "send_message",
  "message_content": "Hello!",
  "key_values": [
    "CTA:View Products|https://example.com/products",
    "CTA:Contact Us|https://example.com/contact"
  ],
  "workflow": "workflow-uuid",
  "position_x": 100,
  "position_y": 200,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z"
}
```

---

### 6. Create via Workflow Endpoint

**Endpoint:** `POST /api/v1/workflow/api/node-workflows/{workflow_id}/create_node/`

**Request:**
```json
{
  "node_type": "action",
  "title": "Welcome Message",
  "action_type": "send_message",
  "message_content": "Welcome to our service!",
  "key_values": [
    "CTA:Get Started|https://example.com/start"
  ],
  "position_x": 500,
  "position_y": 400
}
```

---

### 7. Instagram Comment DM Reply with key_values

**Endpoint:** `POST /api/v1/workflow/api/nodes/`

**Request:**
```json
{
  "node_type": "action",
  "workflow": "workflow-uuid",
  "title": "Instagram Reply",
  "action_type": "instagram_comment_dm_reply",
  "instagram_dm_mode": "STATIC",
  "instagram_dm_text_template": "Thanks for your comment {{username}}!",
  "instagram_public_reply_enabled": true,
  "instagram_public_reply_text": "We'll DM you! 💌",
  "key_values": [
    "CTA:Shop Now|https://example.com/shop",
    "CTA:Learn More|https://example.com/about"
  ],
  "position_x": 200,
  "position_y": 300
}
```

---

## Export/Import

### Export Workflow with key_values

**Endpoint:** `GET /api/v1/workflow/api/workflows/{workflow_id}/export/`

**Response:** (workflow JSON includes key_values)
```json
{
  "workflow": {...},
  "nodes": [
    {
      "id": "node-uuid",
      "node_type": "action",
      "action_type": "send_message",
      "message_content": "Hello!",
      "key_values": [
        "CTA:View Products|https://example.com/products"
      ],
      "...": "other fields"
    }
  ],
  "...": "other export data"
}
```

### Import Workflow with key_values

**Endpoint:** `POST /api/v1/workflow/api/workflows/import/`

**Request:**
```json
{
  "name": "Imported Workflow",
  "workflow_data": {
    "workflow": {...},
    "nodes": [
      {
        "node_type": "action",
        "key_values": [
          "CTA:Button|https://example.com"
        ],
        "...": "other node data"
      }
    ]
  }
}
```

---

## Field Details

### key_values Field

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| key_values | Array | No | [] | List of CTA button configurations |

### Format Rules

1. **Array of Strings**: Each element is a string
2. **CTA Format**: `"CTA:Title|URL"`
3. **Maximum**: Up to 3 buttons (Instagram limit)
4. **Title Length**: Max 20 characters (Instagram limit)
5. **URL**: Must be valid HTTP/HTTPS URL

### Valid Examples

✅ **Single Button:**
```json
"key_values": ["CTA:Click Here|https://example.com"]
```

✅ **Multiple Buttons:**
```json
"key_values": [
  "CTA:Option 1|https://example.com/1",
  "CTA:Option 2|https://example.com/2",
  "CTA:Option 3|https://example.com/3"
]
```

✅ **Empty (no buttons):**
```json
"key_values": []
```

### Invalid Examples

❌ **Wrong Format:**
```json
"key_values": [
  "Button|https://example.com"  // Missing "CTA:" prefix
]
```

❌ **Objects instead of Strings:**
```json
"key_values": [
  {"title": "Button", "url": "https://example.com"}  // Should be string
]
```

---

## Common Use Cases

### Use Case 1: Product Marketing Message
```json
{
  "node_type": "action",
  "action_type": "send_message",
  "message_content": "🎉 New arrivals are here!",
  "key_values": [
    "CTA:Shop Now|https://shop.com/new",
    "CTA:View Catalog|https://shop.com/catalog"
  ]
}
```

### Use Case 2: Customer Feedback Request
```json
{
  "node_type": "waiting",
  "customer_message": "How was your experience?",
  "key_values": [
    "CTA:Give Feedback|https://feedback.com/rate"
  ],
  "storage_type": "text"
}
```

### Use Case 3: Instagram Comment Auto-Reply
```json
{
  "node_type": "action",
  "action_type": "instagram_comment_dm_reply",
  "instagram_dm_text_template": "Hi {{username}}! Check this out:",
  "key_values": [
    "CTA:View Product|https://shop.com/product/123",
    "CTA:More Info|https://shop.com/info"
  ]
}
```

---

## Error Handling

### Empty key_values
- ✅ Accepted: System treats as no buttons
- Returns: `[]` in response

### Invalid format in key_values
- ⚠️ Warning: Logged but doesn't fail node creation
- Runtime: Invalid entries are skipped during button generation

### Too many buttons (>3)
- ⚠️ Warning: Logged
- Runtime: Only first 3 buttons are used (Instagram limit)

---

## Notes

1. **Backward Compatible**: All existing nodes work without key_values
2. **Always Returns Array**: API always returns `[]` instead of `null`
3. **Persists in Export**: key_values are preserved in workflow export/import
4. **Runtime Processing**: Actual button creation happens during workflow execution
5. **Multi-Channel**: Works with Instagram, can be extended to Telegram/WhatsApp

---

## Migration Required

Before using this feature, run:
```bash
python src/manage.py migrate workflow
```

This applies migration `0013_add_key_values_to_action_waiting_nodes`.

---

## Quick Test

```bash
# Create a test node
curl -X POST "http://localhost:8000/api/v1/workflow/api/nodes/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "action",
    "workflow": "your-workflow-uuid",
    "title": "Test CTA Buttons",
    "action_type": "send_message",
    "message_content": "Test message",
    "key_values": ["CTA:Test Button|https://example.com"],
    "position_x": 100,
    "position_y": 100
  }'

# Verify
curl -X GET "http://localhost:8000/api/v1/workflow/api/nodes/{node-uuid}/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Support

For issues or questions:
- Check implementation details in: `KEY_VALUES_IMPLEMENTATION_SUMMARY.md`
- Runtime integration guide: `RUNTIME_INTEGRATION_GUIDE.md`
- Existing CTA system: `src/message/utils/cta_utils.py`

