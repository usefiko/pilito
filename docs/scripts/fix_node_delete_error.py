#!/usr/bin/env python3
"""
Fix Node Delete Error - prefetch_related issue resolution
"""

import json

def explain_node_delete_error():
    """Explain the node delete error and its fix"""
    
    print("🔧 Fix Node Delete Error")
    print("=" * 50)
    
    NODE_ID = "4a1ee0e6-dde7-4429-8dd5-e2978f11c1f6"
    
    print("❌ Original Error:")
    error_message = {
        "error": "Failed to delete node: Cannot find 'source_connections' on WorkflowNode object, 'source_connections' is an invalid parameter to prefetch_related()"
    }
    print(json.dumps(error_message, indent=2))
    
    print("\n🔍 Root Cause:")
    print("The backend code was using incorrect related_name references:")
    print("❌ Wrong: 'source_connections', 'target_connections'")
    print("✅ Correct: 'outgoing_connections', 'incoming_connections'")
    
    print("\n📋 Model Definition (NodeConnection):")
    model_definition = '''
class NodeConnection(models.Model):
    source_node = models.ForeignKey(
        WorkflowNode, 
        on_delete=models.CASCADE, 
        related_name='outgoing_connections'  # ✅ Correct
    )
    target_node = models.ForeignKey(
        WorkflowNode, 
        on_delete=models.CASCADE, 
        related_name='incoming_connections'  # ✅ Correct
    )
'''
    print(model_definition)
    
    print("🔧 Backend Fix Applied:")
    print("Changed in src/workflow/api/unified_views.py:")
    print("❌ Before: queryset.prefetch_related('source_connections', 'target_connections')")
    print("✅ After:  queryset.prefetch_related('outgoing_connections', 'incoming_connections')")
    
    print(f"\n✅ Fix Status: APPLIED - Node delete should work now")
    print(f"🗑️ Test URL: DELETE /api/v1/workflow/api/nodes/{NODE_ID}/")

def test_node_delete_after_fix():
    """Show how to test node delete after the fix"""
    
    print("\n🧪 Test Node Delete After Fix")
    print("=" * 50)
    
    NODE_ID = "4a1ee0e6-dde7-4429-8dd5-e2978f11c1f6"
    
    # Method 1: Direct node delete
    print("🎯 Method 1: Direct Node Delete")
    delete_command = f'''curl -X DELETE \\
  -H "Authorization: Bearer your-jwt-token" \\
  "https://api.pilito.com/api/v1/workflow/api/nodes/{NODE_ID}/"'''
    
    print("Command:")
    print(delete_command)
    
    print("\nExpected Success Response:")
    success_response = {
        "message": f"Node deleted successfully",
        "deleted_node": {
            "id": NODE_ID,
            "title": "Node Title",
            "node_type": "when"
        },
        "deleted_connections": 3,
        "status": "success"
    }
    print(json.dumps(success_response, indent=2))
    
    # Method 2: Check if node exists first
    print("\n🔍 Method 2: Safe Delete (Check First)")
    check_command = f'''# Step 1: Check if node exists
curl -H "Authorization: Bearer your-jwt-token" \\
  "https://api.pilito.com/api/v1/workflow/api/nodes/{NODE_ID}/"

# Step 2: Delete if exists
curl -X DELETE \\
  -H "Authorization: Bearer your-jwt-token" \\
  "https://api.pilito.com/api/v1/workflow/api/nodes/{NODE_ID}/"'''
    
    print("Commands:")
    print(check_command)

def javascript_safe_delete():
    """JavaScript example for safe node deletion"""
    
    js_code = '''
// JavaScript Safe Node Delete
class NodeDeleter {
  constructor(token) {
    this.token = token;
    this.baseUrl = '/api/v1/workflow/api';
  }

  async safeDeleteNode(nodeId) {
    console.log(`🗑️ Attempting to delete node: ${nodeId}`);
    
    try {
      // Step 1: Check if node exists
      const checkResponse = await fetch(`${this.baseUrl}/nodes/${nodeId}/`, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });

      if (!checkResponse.ok) {
        if (checkResponse.status === 404) {
          console.log('ℹ️ Node not found - already deleted');
          return { success: true, message: 'Node already deleted' };
        }
        throw new Error(`Failed to check node: ${checkResponse.status}`);
      }

      const nodeData = await checkResponse.json();
      console.log('✅ Node found:', nodeData.title);

      // Step 2: Delete the node
      const deleteResponse = await fetch(`${this.baseUrl}/nodes/${nodeId}/`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${this.token}` }
      });

      if (deleteResponse.ok) {
        const result = await deleteResponse.json();
        console.log('✅ Node deleted successfully:', result);
        return { success: true, result };
      } else {
        const error = await deleteResponse.json();
        console.error('❌ Delete failed:', error);
        return { success: false, error };
      }

    } catch (error) {
      console.error('❌ Network error:', error);
      return { success: false, error: error.message };
    }
  }

  async deleteWithConnections(nodeId) {
    console.log(`🔗 Deleting node with all connections: ${nodeId}`);
    
    try {
      // Use the enhanced delete endpoint that handles connections
      const response = await fetch(`${this.baseUrl}/nodes/${nodeId}/delete_connections/`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${this.token}` }
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Node and connections deleted:', result);
        
        // Now delete the node itself
        return await this.safeDeleteNode(nodeId);
      } else {
        console.log('ℹ️ Connection delete endpoint not available, using direct delete');
        return await this.safeDeleteNode(nodeId);
      }

    } catch (error) {
      console.log('ℹ️ Using fallback delete method');
      return await this.safeDeleteNode(nodeId);
    }
  }
}

// Usage Examples
const deleter = new NodeDeleter('your-jwt-token');

// Delete the problematic node
deleter.safeDeleteNode('4a1ee0e6-dde7-4429-8dd5-e2978f11c1f6')
  .then(result => {
    if (result.success) {
      console.log('🎉 Node deleted successfully!');
      // Update UI - remove node from workflow diagram
    } else {
      console.error('💥 Delete failed:', result.error);
    }
  });

// Delete with connections cleanup
deleter.deleteWithConnections('4a1ee0e6-dde7-4429-8dd5-e2978f11c1f6')
  .then(result => {
    console.log('🎉 Complete cleanup done!');
  });
'''
    
    print("\n💻 JavaScript Safe Delete Implementation")
    print("=" * 50)
    print(js_code)

def alternative_delete_methods():
    """Show alternative methods if direct delete still fails"""
    
    print("\n🔄 Alternative Delete Methods")
    print("=" * 50)
    
    NODE_ID = "4a1ee0e6-dde7-4429-8dd5-e2978f11c1f6"
    
    methods = [
        {
            "method": "1. Delete Node Connections First",
            "commands": [
                f"# Get all connections for the node",
                f"curl -H \"Authorization: Bearer token\" \\",
                f"  \"/api/v1/workflow/api/nodes/{NODE_ID}/connections/\"",
                f"",
                f"# Delete connections first",
                f"curl -X DELETE -H \"Authorization: Bearer token\" \\",
                f"  \"/api/v1/workflow/api/nodes/{NODE_ID}/delete_connections/\"",
                f"",
                f"# Then delete the node",
                f"curl -X DELETE -H \"Authorization: Bearer token\" \\",
                f"  \"/api/v1/workflow/api/nodes/{NODE_ID}/\""
            ]
        },
        {
            "method": "2. Use Legacy Node-Specific Endpoints",
            "commands": [
                f"# First, check node type",
                f"curl -H \"Authorization: Bearer token\" \\",
                f"  \"/api/v1/workflow/api/nodes/{NODE_ID}/\"",
                f"",
                f"# Then use type-specific endpoint (example for when node)",
                f"curl -X DELETE -H \"Authorization: Bearer token\" \\",
                f"  \"/api/v1/workflow/api/when-nodes/{NODE_ID}/\""
            ]
        },
        {
            "method": "3. Workflow-Level Cleanup",
            "commands": [
                f"# If all else fails, clean up at workflow level",
                f"curl -X DELETE -H \"Authorization: Bearer token\" \\",
                f"  \"/api/v1/workflow/api/node-connections/delete_by_workflow/?workflow_id=workflow-uuid\"",
                f"",
                f"# Then try node delete again",
                f"curl -X DELETE -H \"Authorization: Bearer token\" \\",
                f"  \"/api/v1/workflow/api/nodes/{NODE_ID}/\""
            ]
        }
    ]
    
    for method in methods:
        print(f"\n{method['method']}:")
        for command in method['commands']:
            print(f"  {command}")

def verification_steps():
    """Steps to verify the fix worked"""
    
    print("\n✅ Verification Steps")
    print("=" * 50)
    
    steps = [
        "1. 🔧 Backend fix has been applied to unified_views.py",
        "2. 🔄 Server restart may be required for changes to take effect",
        "3. 🧪 Test with the same DELETE request that failed before",
        "4. 📊 Check server logs for any remaining errors",
        "5. 🎯 Verify node is actually removed from database",
        "6. 🔗 Confirm associated connections are also cleaned up"
    ]
    
    for step in steps:
        print(f"  {step}")
    
    print("\n🎯 Test Commands:")
    NODE_ID = "4a1ee0e6-dde7-4429-8dd5-e2978f11c1f6"
    
    test_commands = [
        f"# Test the fixed delete endpoint",
        f"curl -X DELETE -H \"Authorization: Bearer your-token\" \\",
        f"  \"https://api.pilito.com/api/v1/workflow/api/nodes/{NODE_ID}/\"",
        f"",
        f"# Verify node is gone",
        f"curl -H \"Authorization: Bearer your-token\" \\",
        f"  \"https://api.pilito.com/api/v1/workflow/api/nodes/{NODE_ID}/\"",
        f"# Should return 404 Not Found"
    ]
    
    for cmd in test_commands:
        print(f"  {cmd}")

if __name__ == "__main__":
    explain_node_delete_error()
    test_node_delete_after_fix()
    javascript_safe_delete()
    alternative_delete_methods()
    verification_steps()
    
    print("\n🎉 Summary:")
    print("✅ Backend error fixed: prefetch_related() now uses correct field names")
    print("✅ Node delete should work properly now")
    print("🔄 Server restart may be needed for changes to take effect")
    print("🧪 Test the same DELETE request that failed before")
