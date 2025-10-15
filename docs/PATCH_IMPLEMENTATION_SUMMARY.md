# PATCH API Implementation Summary

## Overview
The PATCH endpoints for workflows and nodes have been enhanced to support true partial updates, where only the fields sent in the request are updated, without requiring or validating other fields.

## API Endpoints Updated

### 1. Workflow PATCH Endpoint
- **URL**: `PATCH /api/v1/workflow/api/workflows/{id}/`
- **Implementation**: Enhanced `WorkflowViewSet.update()` method

### 2. Node PATCH Endpoint  
- **URL**: `PATCH /api/v1/workflow/api/nodes/{id}/`
- **Implementation**: Enhanced `UnifiedNodeViewSet.update()` method

## Key Features Implemented

### ✅ Partial Updates Only
- Only fields included in the PATCH request are updated
- Unmodified fields remain exactly as they were
- No need to send the complete object

### ✅ Complete Response Data
- PATCH responses return the complete updated object
- All fields are included in the response
- Only the requested fields are actually modified

### ✅ No Unnecessary Validation
- Fields not being updated are not validated
- **EXCLUDED FROM VALIDATION**: `key_word`, `key_value`, `tags`, `position_x`, `position_y`, `keywords`, `channels`, `customer_tags`
- These fields can be updated without any validation checks
- Validation only applies to fields actually being changed

### ✅ Smart Field Handling
- Position updates support multiple formats (direct, relative, alignment)
- Array fields can be merged or replaced based on options
- JSON fields (webhooks, headers, etc.) can be merged intelligently

## Implementation Details

### 1. Enhanced ViewSets

#### WorkflowViewSet Changes
```python
def update(self, request, *args, **kwargs):
    """Override update to implement partial updates"""
    # Always use partial=True for PATCH requests
    if request.method == 'PATCH':
        partial = True
    
    # Only update provided fields
    for field_name, field_value in validated_data.items():
        if hasattr(instance, field_name):
            setattr(instance, field_name, field_value)
```

#### UnifiedNodeViewSet Changes
```python
def update(self, request, *args, **kwargs):
    """Override update to implement partial updates"""
    # Uses UnifiedNodeSerializer's intelligent update logic
    # Handles all node types (When, Condition, Action, Waiting)
```

### 2. Enhanced Serializer Validation

#### Partial Update Validation
```python
def validate(self, data):
    """Skip validation during partial updates unless node_type is changing"""
    if hasattr(self, 'partial') and self.partial and 'node_type' not in data:
        return data  # Skip validation entirely for partial updates
```

#### Field-Specific Validation
- `_validate_when_node_partial()`: Only validates When node fields being updated
- `_validate_condition_node_partial()`: Only validates Condition node fields being updated  
- `_validate_action_node_partial()`: Only validates Action node fields being updated
- `_validate_waiting_node_partial()`: Only validates Waiting node fields being updated

## Usage Examples

### Example 1: Update Only Workflow Name
```http
PATCH /api/v1/workflow/api/workflows/123/
Content-Type: application/json

{
  "name": "New Workflow Name"
}
```
**Result**: Only the name is updated, all other fields remain unchanged.

### Example 2: Update Only Node Position
```http
PATCH /api/v1/workflow/api/nodes/456/
Content-Type: application/json

{
  "position_x": 300,
  "position_y": 150
}
```
**Request**: Only position coordinates are sent.
**Response**: Complete object with all fields, but only `position_x` and `position_y` are actually modified.
```json
{
  "id": "456",
  "node_type": "when",
  "workflow_name": "Test Workflow",
  "title": "Existing Title",
  "position_x": 300,
  "position_y": 150,
  "is_active": true,
  "when_type": "scheduled",
  "keywords": ["existing", "keywords"],
  "tags": [],
  "channels": ["all"],
  "schedule_frequency": "daily",
  "updated_at": "2025-08-22T21:05:39.578506Z",
  ...
}
```
**Result**: Only position coordinates are updated, no validation errors for position fields, and complete object is returned.

### Example 3: Update Node Message Content
```http
PATCH /api/v1/workflow/api/nodes/789/
Content-Type: application/json

{
  "message_content": "Updated message"
}
```
**Result**: Only message content is updated, no validation for action_type or other required fields.

### Example 4: Minimal Update
```http
PATCH /api/v1/workflow/api/nodes/789/
Content-Type: application/json

{
  "is_active": false
}
```
**Result**: Only the active status is changed, everything else stays the same.

## Key Benefits

1. **Simplified Client Code**: Clients can send only the fields they want to change
2. **No Validation Overhead**: No need to fetch current state to satisfy validation
3. **Efficient Updates**: Minimal data transfer and processing
4. **Backward Compatible**: Existing full updates still work
5. **Smart Merging**: Arrays and objects can be merged intelligently when needed

## Fields That Are Never Required

The following fields are never validated as required during PATCH operations:
- `key_word`
- `key_value` 
- `tags`
- Any field not explicitly being updated

## Testing

Use the included `test_patch_api.py` script to see example usage patterns and test the implementation.

## Files Modified

1. `/src/workflow/api/views.py` - Enhanced WorkflowViewSet
2. `/src/workflow/api/unified_views.py` - Enhanced UnifiedNodeViewSet  
3. `/src/workflow/serializers.py` - Enhanced UnifiedNodeSerializer with partial validation

All changes maintain backward compatibility while adding the new partial update functionality.
