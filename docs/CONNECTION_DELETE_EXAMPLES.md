# Connection Delete Operations - Complete Examples

This document provides comprehensive examples for deleting connections between workflow nodes using the enhanced connection management APIs.

## 📋 Available Delete Operations

### 1. Single Connection Delete
### 2. Bulk Connection Delete
### 3. Delete by Node Pairs
### 4. Delete by Workflow
### 5. Delete Orphaned Connections
### 6. Node-Level Connection Management

---

## 🔧 Single Connection Delete

**Delete a specific connection by ID:**

```bash
#!/bin/bash

TOKEN="your-jwt-token"
CONNECTION_ID="connection-uuid"

curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/node-connections/$CONNECTION_ID/"
```

**Response:**
```json
{
  "message": "Connection deleted successfully",
  "deleted_connection": {
    "id": "connection-uuid",
    "source_node": {
      "id": "source-uuid",
      "title": "When: New Message"
    },
    "target_node": {
      "id": "target-uuid",
      "title": "Action: Send Response"
    },
    "connection_type": "success",
    "workflow": {
      "id": "workflow-uuid",
      "name": "Customer Support Flow"
    }
  },
  "status": "success"
}
```

---

## 📦 Bulk Connection Delete

**Delete multiple connections at once:**

```bash
#!/bin/bash

TOKEN="your-jwt-token"

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_ids": [
      "conn-uuid-1",
      "conn-uuid-2",
      "conn-uuid-3"
    ]
  }' \
  "http://localhost:8000/api/v1/workflow/api/node-connections/bulk_delete/"
```

**JavaScript Example:**
```javascript
const deleteMultipleConnections = async (connectionIds, token) => {
  const response = await fetch('/api/v1/workflow/api/node-connections/bulk_delete/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      connection_ids: connectionIds
    })
  });
  
  return response.json();
};

// Usage
const result = await deleteMultipleConnections([
  'conn-uuid-1',
  'conn-uuid-2',
  'conn-uuid-3'
], 'your-token');

console.log(result);
```

---

## 🎯 Delete Connections Between Specific Nodes

**Delete all connections between two specific nodes:**

```bash
#!/bin/bash

TOKEN="your-jwt-token"
SOURCE_NODE="source-node-uuid"
TARGET_NODE="target-node-uuid"

curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/node-connections/delete_by_nodes/?source_node=$SOURCE_NODE&target_node=$TARGET_NODE"
```

**Delete specific connection type between nodes:**

```bash
#!/bin/bash

TOKEN="your-jwt-token"
SOURCE_NODE="source-node-uuid"
TARGET_NODE="target-node-uuid"
CONNECTION_TYPE="success"

curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/node-connections/delete_by_nodes/?source_node=$SOURCE_NODE&target_node=$TARGET_NODE&connection_type=$CONNECTION_TYPE"
```

**Python Example:**
```python
import requests

def delete_connections_between_nodes(source_node_id, target_node_id, token, connection_type=None):
    """Delete connections between specific nodes"""
    
    url = "http://localhost:8000/api/v1/workflow/api/node-connections/delete_by_nodes/"
    headers = {"Authorization": f"Bearer {token}"}
    
    params = {
        "source_node": source_node_id,
        "target_node": target_node_id
    }
    
    if connection_type:
        params["connection_type"] = connection_type
    
    response = requests.delete(url, headers=headers, params=params)
    return response.json()

# Usage
result = delete_connections_between_nodes(
    source_node_id="source-uuid",
    target_node_id="target-uuid", 
    token="your-token",
    connection_type="success"
)
```

---

## 🗂️ Delete All Connections for Workflow

**Delete all connections within a specific workflow:**

```bash
#!/bin/bash

TOKEN="your-jwt-token"
WORKFLOW_ID="workflow-uuid"

curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/node-connections/delete_by_workflow/?workflow_id=$WORKFLOW_ID"
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

---

## 🧹 Delete Orphaned Connections

**Clean up connections that reference non-existent or inactive nodes:**

```bash
#!/bin/bash

TOKEN="your-jwt-token"

curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/node-connections/delete_orphaned/"
```

**Automated cleanup script:**
```bash
#!/bin/bash

# Cleanup script to run periodically
TOKEN="your-jwt-token"
BASE_URL="http://localhost:8000/api/v1/workflow/api"

echo "🧹 Starting workflow cleanup..."

# Delete orphaned connections
echo "Deleting orphaned connections..."
ORPHANED_RESULT=$(curl -s -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/node-connections/delete_orphaned/")

echo "Orphaned cleanup result: $ORPHANED_RESULT"

# Get statistics after cleanup
echo "Getting updated statistics..."
STATS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/node-connections/statistics/")

echo "Updated statistics: $STATS"

echo "✅ Cleanup completed!"
```

---

## 🎯 Node-Level Connection Management

### Delete All Connections for a Node

```bash
#!/bin/bash

TOKEN="your-jwt-token"
NODE_ID="node-uuid"

curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/nodes/$NODE_ID/delete_connections/"
```

### Disconnect from Specific Target Nodes

```bash
#!/bin/bash

TOKEN="your-jwt-token"
NODE_ID="source-node-uuid"

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_node_ids": [
      "target-uuid-1",
      "target-uuid-2"
    ],
    "connection_type": "success"
  }' \
  "http://localhost:8000/api/v1/workflow/api/nodes/$NODE_ID/disconnect_from/"
```

### Delete Only Incoming Connections

```bash
#!/bin/bash

TOKEN="your-jwt-token"
NODE_ID="target-node-uuid"

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/nodes/$NODE_ID/disconnect_incoming/"
```

### Delete Only Outgoing Connections

```bash
#!/bin/bash

TOKEN="your-jwt-token"
NODE_ID="source-node-uuid"

curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/nodes/$NODE_ID/disconnect_outgoing/"
```

---

## 🔄 React/Frontend Examples

### React Hook for Connection Management

```jsx
import { useState, useCallback } from 'react';

const useConnectionManager = (token) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const deleteConnection = useCallback(async (connectionId) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/v1/workflow/api/node-connections/${connectionId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to delete connection');
      }
      
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [token]);

  const bulkDeleteConnections = useCallback(async (connectionIds) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/workflow/api/node-connections/bulk_delete/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          connection_ids: connectionIds
        }),
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to delete connections');
      }
      
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [token]);

  const deleteNodeConnections = useCallback(async (nodeId) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/v1/workflow/api/nodes/${nodeId}/delete_connections/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || 'Failed to delete node connections');
      }
      
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [token]);

  return {
    deleteConnection,
    bulkDeleteConnections,
    deleteNodeConnections,
    loading,
    error
  };
};

// Usage in component
const WorkflowEditor = () => {
  const { deleteConnection, bulkDeleteConnections, loading, error } = useConnectionManager(token);
  
  const handleDeleteConnection = async (connectionId) => {
    try {
      const result = await deleteConnection(connectionId);
      console.log('Connection deleted:', result);
      // Refresh workflow data
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const handleBulkDelete = async (selectedConnectionIds) => {
    try {
      const result = await bulkDeleteConnections(selectedConnectionIds);
      console.log('Connections deleted:', result);
      // Refresh workflow data
    } catch (err) {
      console.error('Bulk delete failed:', err);
    }
  };

  return (
    <div>
      {/* Your workflow editor UI */}
      {loading && <div>Deleting connections...</div>}
      {error && <div>Error: {error}</div>}
    </div>
  );
};
```

---

## 🔄 Advanced Use Cases

### Workflow Reset (Delete All Connections)

```bash
#!/bin/bash

# Script to reset a workflow by deleting all connections
TOKEN="your-jwt-token"
WORKFLOW_ID="workflow-uuid"

echo "🔄 Resetting workflow $WORKFLOW_ID..."

# Delete all connections for the workflow
RESULT=$(curl -s -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/node-connections/delete_by_workflow/?workflow_id=$WORKFLOW_ID")

echo "Reset result: $RESULT"

# Verify no connections remain
STATS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/workflow/api/node-connections/statistics/")

echo "Updated statistics: $STATS"
```

### Conditional Connection Cleanup

```python
import requests

def cleanup_connections_by_criteria(token, workflow_id=None, connection_type=None, max_age_days=None):
    """Advanced connection cleanup with multiple criteria"""
    
    base_url = "http://localhost:8000/api/v1/workflow/api"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all connections
    params = {}
    if workflow_id:
        params['workflow'] = workflow_id
    if connection_type:
        params['connection_type'] = connection_type
    
    response = requests.get(f"{base_url}/node-connections/", headers=headers, params=params)
    connections = response.json()['results']
    
    # Filter by age if specified
    if max_age_days:
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        connections = [
            conn for conn in connections 
            if datetime.fromisoformat(conn['created_at'].replace('Z', '+00:00')) < cutoff_date
        ]
    
    # Bulk delete filtered connections
    if connections:
        connection_ids = [conn['id'] for conn in connections]
        
        delete_response = requests.post(
            f"{base_url}/node-connections/bulk_delete/",
            headers={**headers, "Content-Type": "application/json"},
            json={"connection_ids": connection_ids}
        )
        
        return delete_response.json()
    
    return {"message": "No connections found matching criteria", "deleted_count": 0}

# Usage examples
result1 = cleanup_connections_by_criteria(token, workflow_id="old-workflow-uuid")
result2 = cleanup_connections_by_criteria(token, connection_type="timeout", max_age_days=30)
```

---

## 📊 Monitoring and Validation

### Connection Health Check

```bash
#!/bin/bash

TOKEN="your-jwt-token"
BASE_URL="http://localhost:8000/api/v1/workflow/api"

echo "🔍 Connection Health Check"
echo "========================="

# Get overall statistics
echo "📊 Overall Statistics:"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/node-connections/statistics/" | jq '.'

echo ""
echo "🧹 Checking for orphaned connections:"
curl -s -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/node-connections/delete_orphaned/" | jq '.'

echo ""
echo "✅ Health check complete!"
```

---

This comprehensive guide covers all aspects of connection deletion in the workflow system. Use these examples to implement robust connection management in your applications!
