# Workflow Export/Import Functionality

This guide explains how to use the new workflow export/import functionality that allows you to export complete workflows (including all related objects) as JSON files and import them to create new workflows.

## Overview

The export/import system allows you to:
- Export a complete workflow with all nodes, connections, triggers, actions, and conditions
- Import the exported data to create a new workflow with new primary keys
- Maintain all relationships between objects during import
- Share workflows between different environments or users

## Features

### What Gets Exported
- **Workflow metadata**: Name, description, settings, UI configuration
- **Nodes**: All node types (When, Condition, Action, Waiting) with their specific configurations
- **Connections**: All connections between nodes with their types and conditions
- **Legacy components**: Triggers, Actions, Conditions (for backward compatibility)
- **Relationships**: All associations between workflow components
- **Metadata**: Export timestamp, original workflow ID, version info

### What Gets Imported
- **New workflow**: Created with a new UUID
- **New nodes**: All nodes recreated with new UUIDs while preserving data
- **New connections**: All connections recreated with references to new node IDs
- **Maintained relationships**: All relationships preserved using ID mapping
- **Status**: Always imported as 'DRAFT' for safety

## API Endpoints

### Export Workflow
```http
GET /workflow/api/workflows/{workflow_id}/export/
```

**Response:**
- Content-Type: `application/json`
- Content-Disposition: `attachment; filename="WorkflowName_YYYYMMDD_HHMMSS.json"`
- Body: Complete workflow JSON with all related objects

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/workflow/api/workflows/123e4567-e89b-12d3-a456-426614174000/export/ \
     -o my_workflow.json
```

### Import Workflow
```http
POST /workflow/api/workflows/import_workflow/
```

**Request Body:**
```json
{
  "workflow_data": {
    // Exported workflow JSON data
  },
  "name": "Optional New Workflow Name"  // Optional: Override workflow name
}
```

**Response:**
```json
{
  "message": "Workflow imported successfully",
  "workflow": {
    "id": "new-workflow-uuid",
    "name": "Imported Workflow Name",
    // ... other workflow details
  }
}
```

**Example:**
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "workflow_data": {...exported_json...},
       "name": "My Imported Workflow"
     }' \
     http://localhost:8000/workflow/api/workflows/import_workflow/
```

## JSON Structure

The exported JSON has the following structure:

```json
{
  "workflow": {
    "name": "Workflow Name",
    "description": "Workflow description",
    "status": "DRAFT",
    "ui_settings": {...},
    "edges": [...],
    "max_executions": 0,
    "delay_between_executions": 0,
    "start_date": null,
    "end_date": null
  },
  "nodes": [
    {
      "id": "node-uuid",
      "node_type": "when|condition|action|waiting",
      "title": "Node Title",
      "position_x": 100,
      "position_y": 100,
      "configuration": {...},
      "is_active": true,
      // Node type specific fields...
    }
  ],
  "connections": [
    {
      "id": "connection-uuid",
      "source_node_id": "source-node-uuid",
      "target_node_id": "target-node-uuid",
      "connection_type": "success|failure|timeout|skip",
      "condition": {...}
    }
  ],
  "triggers": [...],        // Legacy triggers
  "actions": [...],         // Legacy actions
  "conditions": [...],      // Legacy conditions
  "trigger_associations": [...],  // Legacy associations
  "workflow_actions": [...],      // Legacy workflow actions
  "export_metadata": {
    "exported_at": "2024-01-01T12:00:00Z",
    "original_workflow_id": "original-uuid",
    "version": "1.0"
  }
}
```

## Programming API

### Model Methods

#### Export Method
```python
from workflow.models import Workflow

# Get a workflow
workflow = Workflow.objects.get(id=workflow_id)

# Export to dictionary
export_data = workflow.export_to_dict()

# Save to file
import json
with open('workflow_export.json', 'w') as f:
    json.dump(export_data, f, indent=2, default=str)
```

#### Import Method
```python
from workflow.models import Workflow
import json

# Load from file
with open('workflow_export.json', 'r') as f:
    import_data = json.load(f)

# Import workflow
user = request.user  # or get user some other way
imported_workflow = Workflow.import_from_dict(import_data, created_by=user)

print(f"Imported workflow: {imported_workflow.name} (ID: {imported_workflow.id})")
```

### Serializers

#### Export Serializer
```python
from workflow.serializers import WorkflowExportSerializer

workflow = Workflow.objects.get(id=workflow_id)
serializer = WorkflowExportSerializer(workflow)
export_data = serializer.data
```

#### Import Serializer
```python
from workflow.serializers import WorkflowImportSerializer

serializer = WorkflowImportSerializer(
    data={
        'workflow_data': import_data,
        'name': 'Optional New Name'
    },
    context={'request': request}
)

if serializer.is_valid():
    workflow = serializer.save()
```

## Node Type Support

### When Nodes
Exports/imports all when node configurations:
- `when_type`: Message received, tag added, scheduled, etc.
- `keywords`: Trigger keywords
- `tags`: Associated tags
- `channels`: Communication channels
- `schedule_*`: Scheduling configuration

### Condition Nodes
Exports/imports condition logic:
- `combination_operator`: AND/OR logic
- `conditions`: Array of condition rules
- AI conditions and message conditions

### Action Nodes
Exports/imports all action types:
- `action_type`: Send message, webhook, delay, etc.
- `message_content`: Message templates
- `webhook_*`: Webhook configuration
- `ai_*`: AI control settings
- Tag management settings

### Waiting Nodes
Exports/imports user interaction settings:
- `storage_type`: Response data type
- `customer_message`: Prompt message
- `choice_options`: Multiple choice options
- `allowed_errors`: Error tolerance
- `response_timeout_*`: Timeout configuration

## Error Handling

### Common Import Errors
1. **Invalid JSON structure**: Missing required keys
2. **User permissions**: Insufficient permissions to create workflows
3. **Database constraints**: Validation errors on model creation
4. **Relationship errors**: Referenced objects not found

### Error Response Format
```json
{
  "error": "Failed to import workflow",
  "details": "Detailed error message"
}
```

## Best Practices

### Before Export
1. **Test your workflow** to ensure it works correctly
2. **Clean up unused nodes** and connections
3. **Document your workflow** with clear descriptions

### During Import
1. **Review the JSON** before importing to understand the structure
2. **Use meaningful names** when overriding workflow names
3. **Import to draft** and test before activating

### After Import
1. **Verify all nodes** and connections are correct
2. **Test the imported workflow** thoroughly
3. **Update any environment-specific settings** (webhooks, etc.)

## Security Considerations

1. **Authentication required**: Both endpoints require authentication
2. **User isolation**: Users can only export their own workflows
3. **Safe import**: Workflows always imported as DRAFT status
4. **Data validation**: All imported data is validated
5. **No execution data**: Only configuration is exported, not execution history

## Migration and Backup

### Backup Workflows
```bash
# Export all workflows for a user
for workflow_id in $(curl -H "Authorization: Bearer TOKEN" \
                         http://localhost:8000/workflow/api/workflows/ | \
                    jq -r '.results[].id'); do
  curl -H "Authorization: Bearer TOKEN" \
       http://localhost:8000/workflow/api/workflows/$workflow_id/export/ \
       -o "backup_workflow_$workflow_id.json"
done
```

### Environment Migration
1. Export workflows from source environment
2. Import into target environment
3. Update environment-specific configurations
4. Test and activate

## Troubleshooting

### Export Issues
- **Permission denied**: Ensure you own the workflow
- **Large workflows**: May take time to export complex workflows
- **Missing data**: Check if all relationships are properly set

### Import Issues
- **JSON errors**: Validate JSON structure
- **Duplicate names**: Use name override to avoid conflicts
- **Missing permissions**: Ensure user can create workflows
- **Database errors**: Check logs for specific constraint violations

## Testing

A test script is available to verify the functionality:

```bash
cd /path/to/project
python test_workflow_export_import.py
```

This will:
1. Create a sample workflow
2. Test export functionality
3. Test import functionality
4. Verify data integrity
5. Clean up test data

## Version History

- **v1.0**: Initial implementation with full node support
- Supports all current node types and legacy workflow components
- Maintains backward compatibility with existing workflows

## Support

For issues or questions:
1. Check the error messages for specific details
2. Review the exported JSON structure
3. Test with simple workflows first
4. Check server logs for detailed error information
