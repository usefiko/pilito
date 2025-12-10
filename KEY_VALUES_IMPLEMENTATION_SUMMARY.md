# Key-Values Field Implementation Summary

## Overview
This document summarizes the implementation of the `key_values` field for ActionNode and WaitingNode models in the workflow system. This feature allows the frontend to send CTA button configurations (like `[[CTA:Title|https://link.com]]`) that can be stored, updated, and used in workflow executions.

## Changes Made

### 1. Database Models (`src/workflow/models.py`)

#### ActionNode Model
- **Added Field**: `key_values` (JSONField)
  - Type: `JSONField` with `default=list`
  - Description: Stores key-value pairs for CTA buttons in send_message and instagram_comment operations
  - Format: `[["CTA:Title|https://url.com"], ["CTA:Another|https://url2.com"]]`
  - Location: Added after `message_content` field (line ~1122)

#### WaitingNode Model
- **Added Field**: `key_values` (JSONField)
  - Type: `JSONField` with `default=list`
  - Description: Stores key-value pairs for CTA buttons in customer messages
  - Format: Same as ActionNode
  - Location: Added after `customer_message` field (line ~1227)

### 2. Database Migration
- **File**: `src/workflow/migrations/0013_add_key_values_to_action_waiting_nodes.py`
- **Operations**:
  - Added `key_values` field to `ActionNode` model
  - Added `key_values` field to `WaitingNode` model
- **Migration Status**: Created and ready to be applied

### 3. Serializers (`src/workflow/serializers.py`)

#### ActionNodeSerializer
- Added automatic handling of `key_values` field
- Updated `to_representation()` method to ensure `key_values` is always a list (never null)
- Ensures backward compatibility

#### WaitingNodeSerializer
- Added automatic handling of `key_values` field
- Updated `to_representation()` method to ensure `key_values` is always a list
- Maintains compatibility with existing `skip_keywords` alias

#### UnifiedNodeSerializer
- Added `key_values` field declaration with proper serialization (line ~568)
- Updated `_update_action_node_fields()` to include `key_values` in action fields list (line ~1126)
- Updated `_update_waiting_node_fields()` to include `key_values` in waiting fields list (line ~1174)
- Added logging for key_values updates

#### CreateNodeSerializer
- Added `key_values` field with ListField type
- Added validation to ensure `key_values` is always a list (line ~514)
- Supports both action and waiting node creation

### 4. API Views (`src/workflow/api/views.py`)

#### NodeBasedWorkflowViewSet.create_node()
- **Action Node Creation**: Added `key_values=data.get('key_values', [])` parameter (line ~1643)
- **Waiting Node Creation**: Added `key_values=data.get('key_values', [])` parameter (line ~1674)
- Ensures default empty list if not provided

### 5. Import/Export Support (`src/workflow/models.py`)

#### Workflow.export_to_dict()
- **ActionNode Export**: Added `'key_values': action_node.key_values` to node_data (line ~385)
- **WaitingNode Export**: Added `'key_values': waiting_node.key_values` to node_data (line ~401)

#### Workflow.import_from_dict()
- **ActionNode Import**: Added `key_values=node_data.get('key_values', [])` parameter (line ~611)
- **WaitingNode Import**: Added `key_values=node_data.get('key_values', [])` parameter (line ~628)

## API Usage Examples

### 1. Create Action Node with Key-Values (Send Message)

```bash
POST /api/v1/workflow/api/nodes/
```

```json
{
  "node_type": "action",
  "workflow": "workflow-uuid",
  "title": "Send Welcome Message",
  "action_type": "send_message",
  "message_content": "Welcome! Check out our products.",
  "key_values": [
    ["CTA:View Products|https://example.com/products"],
    ["CTA:Contact Us|https://example.com/contact"]
  ],
  "position_x": 500,
  "position_y": 200
}
```

### 2. Create Waiting Node with Key-Values

```bash
POST /api/v1/workflow/api/nodes/
```

```json
{
  "node_type": "waiting",
  "workflow": "workflow-uuid",
  "title": "Ask for Feedback",
  "storage_type": "text",
  "customer_message": "Please rate our service",
  "key_values": [
    ["CTA:Rate Now|https://example.com/rate"]
  ],
  "response_time_limit_enabled": true,
  "response_timeout_amount": 30,
  "response_timeout_unit": "minutes",
  "position_x": 700,
  "position_y": 300
}
```

### 3. Update Node with Key-Values (PATCH)

```bash
PATCH /api/v1/workflow/api/nodes/{node_id}/
```

```json
{
  "key_values": [
    ["CTA:New Link|https://example.com/new"]
  ]
}
```

### 4. Create via Workflow-Specific Endpoint

```bash
POST /api/v1/workflow/api/node-workflows/{workflow_id}/create_node/
```

```json
{
  "node_type": "action",
  "title": "Instagram Comment Reply",
  "action_type": "instagram_comment_dm_reply",
  "instagram_dm_text_template": "Thank you for your comment!",
  "key_values": [
    ["CTA:Shop Now|https://example.com/shop"]
  ],
  "position_x": 300,
  "position_y": 400
}
```

## Integration with Existing CTA System

The `key_values` field is designed to work seamlessly with the existing CTA extraction system:

1. **Frontend sends key_values**: The frontend can send CTA button configurations in the `key_values` field
2. **Backend stores them**: The system stores these values in the database
3. **Runtime processing**: During workflow execution, the system can:
   - Retrieve `key_values` from the node
   - Convert them to the CTA format `[[CTA:Title|URL]]`
   - Append them to the message content
   - Use the existing `extract_cta_from_text()` function (from `message/utils/cta_utils.py`) to parse and create buttons

### Example Runtime Flow

```python
# In workflow execution service:
action_node = ActionNode.objects.get(id=node_id)
message_content = action_node.message_content

# If key_values exist, append them to message
if action_node.key_values:
    for kv in action_node.key_values:
        # kv format: ["CTA:Title|https://url.com"]
        message_content += f" {kv[0]}"

# Existing CTA extraction will handle the rest
from message.utils.cta_utils import extract_cta_from_text
clean_message, buttons = extract_cta_from_text(message_content)

# Send message with buttons
instagram_service.send_message(recipient_id, clean_message, buttons)
```

## Testing Recommendations

1. **Unit Tests**:
   - Test ActionNode creation with key_values
   - Test WaitingNode creation with key_values
   - Test serializer validation
   - Test empty/null key_values handling

2. **Integration Tests**:
   - Test workflow export with key_values
   - Test workflow import with key_values
   - Test node updates via API
   - Test key_values retrieval via API

3. **End-to-End Tests**:
   - Create workflow with nodes containing key_values
   - Execute workflow and verify CTA buttons are sent correctly
   - Test Instagram comment DM reply with key_values
   - Test waiting node messages with CTA buttons

## Migration Instructions

To apply the database changes:

```bash
# Run migration
python src/manage.py migrate workflow

# Or if using python3
python3 src/manage.py migrate workflow
```

## Backward Compatibility

- All existing nodes without `key_values` will default to empty list `[]`
- The system gracefully handles null values by converting them to empty lists
- No breaking changes to existing APIs
- All existing serializers and views continue to work

## Frontend Integration Points

The frontend can now:

1. **Send key_values during node creation** (POST /nodes/)
2. **Update key_values** (PATCH /nodes/{id}/)
3. **Retrieve key_values** in node details (GET /nodes/{id}/)
4. **Export/Import workflows** with key_values preserved

## Notes

- The format `[["CTA:Title|URL"]]` is used to maintain consistency with the existing CTA system
- The field is always returned as a list in API responses, never null
- Both action nodes (send_message, instagram_comment_dm_reply) and waiting nodes support key_values
- The implementation is fully integrated with the import/export functionality

## Files Modified

1. `src/workflow/models.py` - Added key_values field to ActionNode and WaitingNode
2. `src/workflow/serializers.py` - Updated all relevant serializers
3. `src/workflow/api/views.py` - Updated create_node action
4. `src/workflow/migrations/0013_add_key_values_to_action_waiting_nodes.py` - New migration file

## Status: ✅ Complete

All implementation tasks have been completed:
- ✅ Database models updated
- ✅ Migration created
- ✅ Serializers updated
- ✅ API views updated
- ✅ Import/Export support added
- ✅ Backward compatibility maintained
- ✅ No linter errors

