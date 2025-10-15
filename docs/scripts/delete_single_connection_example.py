#!/usr/bin/env python3
"""
Examples for deleting a single connection between workflow nodes
"""

import json

def delete_single_connection_examples():
    """Show different ways to delete a single connection"""
    
    print("🔗 How to Delete a Single Connection")
    print("=" * 50)
    
    TOKEN = "your-jwt-token"
    BASE_URL = "http://localhost:8000/api/v1/workflow/api"
    
    # Method 1: Delete by Connection ID (Recommended)
    print("\n🎯 Method 1: Delete by Connection ID")
    print("-" * 40)
    
    connection_id = "550e8400-e29b-41d4-a716-446655440000"
    
    curl_example_1 = f"""
curl -X DELETE \\
  -H "Authorization: Bearer {TOKEN}" \\
  "{BASE_URL}/node-connections/{connection_id}/"
"""
    
    print("cURL Example:")
    print(curl_example_1)
    
    js_example_1 = f"""
// JavaScript Example
const deleteConnection = async (connectionId) => {{
  const response = await fetch(`{BASE_URL}/node-connections/${{connectionId}}/`, {{
    method: 'DELETE',
    headers: {{
      'Authorization': 'Bearer {TOKEN}',
    }},
  }});
  
  if (response.ok) {{
    const result = await response.json();
    console.log('✅ Connection deleted:', result.message);
    return result;
  }} else {{
    console.error('❌ Delete failed:', response.status);
  }}
}};

// Usage
deleteConnection('{connection_id}');
"""
    
    print("JavaScript Example:")
    print(js_example_1)
    
    # Method 2: Delete by Source/Target Nodes
    print("\n🎯 Method 2: Delete by Source/Target Nodes")
    print("-" * 40)
    
    source_node = "source-node-uuid"
    target_node = "target-node-uuid" 
    connection_type = "success"
    
    curl_example_2 = f"""
curl -X DELETE \\
  -H "Authorization: Bearer {TOKEN}" \\
  "{BASE_URL}/node-connections/delete_by_nodes/?source_node={source_node}&target_node={target_node}&connection_type={connection_type}"
"""
    
    print("cURL Example:")
    print(curl_example_2)
    
    js_example_2 = f"""
// JavaScript Example
const deleteConnectionByNodes = async (sourceId, targetId, connType) => {{
  const params = new URLSearchParams({{
    source_node: sourceId,
    target_node: targetId,
    connection_type: connType
  }});
  
  const response = await fetch(`{BASE_URL}/node-connections/delete_by_nodes/?${{params}}`, {{
    method: 'DELETE',
    headers: {{
      'Authorization': 'Bearer {TOKEN}',
    }},
  }});
  
  return response.json();
}};

// Usage
deleteConnectionByNodes('{source_node}', '{target_node}', '{connection_type}');
"""
    
    print("JavaScript Example:")
    print(js_example_2)
    
    # Method 3: Via Node Disconnect
    print("\n🎯 Method 3: Via Node Disconnect")
    print("-" * 40)
    
    curl_example_3 = f"""
curl -X POST \\
  -H "Authorization: Bearer {TOKEN}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "target_node_ids": ["{target_node}"],
    "connection_type": "{connection_type}"
  }}' \\
  "{BASE_URL}/nodes/{source_node}/disconnect_from/"
"""
    
    print("cURL Example:")
    print(curl_example_3)
    
    js_example_3 = f"""
// JavaScript Example
const disconnectFromNode = async (sourceNodeId, targetNodeId, connType) => {{
  const response = await fetch(`{BASE_URL}/nodes/${{sourceNodeId}}/disconnect_from/`, {{
    method: 'POST',
    headers: {{
      'Authorization': 'Bearer {TOKEN}',
      'Content-Type': 'application/json',
    }},
    body: JSON.stringify({{
      target_node_ids: [targetNodeId],
      connection_type: connType
    }})
  }});
  
  return response.json();
}};

// Usage
disconnectFromNode('{source_node}', '{target_node}', '{connection_type}');
"""
    
    print("JavaScript Example:")
    print(js_example_3)

def response_examples():
    """Show expected response formats"""
    
    print("\n📊 Expected Response Examples")
    print("=" * 50)
    
    # Success Response
    print("\n✅ Success Response:")
    success_response = {
        "message": "Connection deleted successfully",
        "deleted_connection": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
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
    print(json.dumps(success_response, indent=2))
    
    # Error Response
    print("\n❌ Error Response (Connection not found):")
    error_response = {
        "detail": "Not found.",
        "status": "error"
    }
    print(json.dumps(error_response, indent=2))
    
    # Error Response (No permission)
    print("\n❌ Error Response (No permission):")
    permission_error = {
        "error": "Failed to delete connection: Permission denied",
        "status": "error"
    }
    print(json.dumps(permission_error, indent=2))

def react_component_example():
    """React component example for deleting connections"""
    
    react_code = '''
// React Component Example
import React, { useState } from 'react';

const ConnectionManager = ({ token, onConnectionDeleted }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const deleteConnection = async (connectionId) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/v1/workflow/api/node-connections/${connectionId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Connection deleted:', result.message);
        
        // Notify parent component
        if (onConnectionDeleted) {
          onConnectionDeleted(connectionId, result);
        }
        
        return result;
      } else {
        throw new Error(`Delete failed: ${response.status}`);
      }
    } catch (err) {
      setError(err.message);
      console.error('❌ Delete error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {loading && <div>Deleting connection...</div>}
      {error && <div style={{color: 'red'}}>Error: {error}</div>}
      
      <button 
        onClick={() => deleteConnection('connection-uuid')}
        disabled={loading}
      >
        {loading ? 'Deleting...' : 'Delete Connection'}
      </button>
    </div>
  );
};

// Usage in Workflow Editor
const WorkflowEditor = () => {
  const handleConnectionDeleted = (connectionId, result) => {
    console.log(`Connection ${connectionId} deleted:`, result);
    // Refresh workflow diagram
    // Remove connection from UI
    // Update connections state
  };

  return (
    <div>
      <ConnectionManager 
        token="your-jwt-token"
        onConnectionDeleted={handleConnectionDeleted}
      />
    </div>
  );
};
'''
    
    print("\n⚛️ React Component Example")
    print("=" * 50)
    print(react_code)

def best_practices():
    """Best practices for deleting connections"""
    
    print("\n💡 Best Practices")
    print("=" * 50)
    
    practices = [
        "✅ Use Method 1 (Connection ID) when you have the exact connection ID",
        "✅ Use Method 2 (Source/Target) when you know the nodes but not the connection ID", 
        "✅ Use Method 3 (Node Disconnect) for node-level operations",
        "✅ Always check response status before assuming success",
        "✅ Handle errors gracefully in your UI",
        "✅ Update your UI state after successful deletion",
        "✅ Show loading states during delete operations",
        "✅ Confirm with user before deleting (especially for important connections)",
        "❌ Don't delete connections without user confirmation",
        "❌ Don't forget to refresh your workflow diagram after deletion"
    ]
    
    for practice in practices:
        print(f"  {practice}")

def common_scenarios():
    """Common scenarios for single connection deletion"""
    
    print("\n🎬 Common Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            "title": "🎯 Workflow Editor - User clicks delete on connection line",
            "method": "Connection ID",
            "reason": "UI knows the exact connection ID from the diagram"
        },
        {
            "title": "🔧 Node Configuration - Remove specific connection type",
            "method": "Source/Target with type filter",
            "reason": "Want to remove only 'failure' connections but keep 'success'"
        },
        {
            "title": "🧹 Node Cleanup - Disconnect from one specific target",
            "method": "Node disconnect with single target",
            "reason": "Node-level operation, focusing on one relationship"
        },
        {
            "title": "🔄 Connection Replacement - Remove old before adding new",
            "method": "Connection ID or Source/Target",
            "reason": "Replacing existing connection with new one"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['title']}")
        print(f"   Method: {scenario['method']}")
        print(f"   Why: {scenario['reason']}")

if __name__ == "__main__":
    delete_single_connection_examples()
    response_examples()
    react_component_example()
    best_practices()
    common_scenarios()
    
    print("\n🎉 Single Connection Delete Guide Complete!")
    print("\nQuick Summary:")
    print("1. 🎯 Best: DELETE /node-connections/{id}/ (if you have ID)")
    print("2. 🔧 Alternative: DELETE /node-connections/delete_by_nodes/ (if you know nodes)")
    print("3. 📱 Node-level: POST /nodes/{id}/disconnect_from/ (node-focused operations)")
