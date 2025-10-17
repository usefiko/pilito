#!/usr/bin/env python3
"""
Debug script for connection delete issues
"""

import json

def debug_connection_delete():
    """Debug steps for connection delete problems"""
    
    print("🔍 Debug Connection Delete Issue")
    print("=" * 50)
    
    TOKEN = "your-jwt-token"
    BASE_URL = "https://api.pilito.com/api/v1/workflow/api"
    CONNECTION_ID = "0c172da6-6946-44d2-bea5-797aa72b6c94"
    
    print(f"❌ Failed Connection ID: {CONNECTION_ID}")
    print(f"🔗 Failed URL: {BASE_URL}/node-connections/{CONNECTION_ID}/")
    print()
    
    # Step 1: Check if connection exists
    print("🔍 Step 1: Check if connection exists")
    print("-" * 40)
    
    check_connection_cmd = f'''
curl -H "Authorization: Bearer {TOKEN}" \\
  "{BASE_URL}/node-connections/{CONNECTION_ID}/"
'''
    
    print("Check Connection Command:")
    print(check_connection_cmd)
    
    print("Expected responses:")
    print("✅ If exists: Connection data with source/target nodes")
    print("❌ If not exists: 404 Not Found")
    print()
    
    # Step 2: List all connections to find the right one
    print("🔍 Step 2: List all connections for your workflows")
    print("-" * 40)
    
    list_connections_cmd = f'''
curl -H "Authorization: Bearer {TOKEN}" \\
  "{BASE_URL}/node-connections/"
'''
    
    print("List All Connections:")
    print(list_connections_cmd)
    print()
    
    # Step 3: Search by workflow
    print("🔍 Step 3: Search connections by workflow")
    print("-" * 40)
    
    search_by_workflow_cmd = f'''
curl -H "Authorization: Bearer {TOKEN}" \\
  "{BASE_URL}/node-connections/?workflow=your-workflow-uuid"
'''
    
    print("Search by Workflow:")
    print(search_by_workflow_cmd)
    print()
    
    # Step 4: Alternative delete methods
    print("🔧 Step 4: Alternative delete methods")
    print("-" * 40)
    
    alternatives = [
        {
            "method": "Delete by Source/Target Nodes",
            "command": f'''curl -X DELETE \\
  -H "Authorization: Bearer {TOKEN}" \\
  "{BASE_URL}/node-connections/delete_by_nodes/?source_node=source-uuid&target_node=target-uuid"''',
            "use_case": "When you know the source and target nodes"
        },
        {
            "method": "Delete from Node",
            "command": f'''curl -X DELETE \\
  -H "Authorization: Bearer {TOKEN}" \\
  "{BASE_URL}/nodes/node-uuid/delete_connections/"''',
            "use_case": "Delete all connections for a specific node"
        },
        {
            "method": "Bulk Delete",
            "command": f'''curl -X POST \\
  -H "Authorization: Bearer {TOKEN}" \\
  -H "Content-Type: application/json" \\
  -d '{{"connection_ids": ["conn-1", "conn-2"]}}' \\
  "{BASE_URL}/node-connections/bulk_delete/"''',
            "use_case": "Delete multiple connections at once"
        }
    ]
    
    for alt in alternatives:
        print(f"🎯 {alt['method']}:")
        print(f"   Use case: {alt['use_case']}")
        print(f"   Command: {alt['command']}")
        print()

def common_issues_and_solutions():
    """Common issues and their solutions"""
    
    print("🚨 Common Issues & Solutions")
    print("=" * 50)
    
    issues = [
        {
            "issue": "Connection ID not found",
            "causes": [
                "Connection was already deleted",
                "Wrong connection ID copied",
                "Connection belongs to another user's workflow"
            ],
            "solutions": [
                "List all connections and find the correct ID",
                "Check if connection still exists in UI",
                "Verify you have permission to access this connection"
            ]
        },
        {
            "issue": "Permission denied",
            "causes": [
                "Connection belongs to another user",
                "Invalid or expired JWT token",
                "User doesn't own the workflow"
            ],
            "solutions": [
                "Ensure you're using the correct user token",
                "Refresh your authentication token",
                "Verify workflow ownership"
            ]
        },
        {
            "issue": "Connection already deleted",
            "causes": [
                "Another user/process deleted it",
                "Frontend shows stale data",
                "Race condition in concurrent operations"
            ],
            "solutions": [
                "Refresh the workflow diagram",
                "Check if connection still exists",
                "Implement optimistic UI updates carefully"
            ]
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. ❌ {issue['issue']}")
        print("   Possible causes:")
        for cause in issue['causes']:
            print(f"     • {cause}")
        print("   Solutions:")
        for solution in issue['solutions']:
            print(f"     ✅ {solution}")
        print()

def javascript_debug_helper():
    """JavaScript helper for debugging connection issues"""
    
    js_code = '''
// JavaScript Debug Helper for Connection Issues

class ConnectionDebugger {
  constructor(token, baseUrl = '/api/v1/workflow/api') {
    this.token = token;
    this.baseUrl = baseUrl;
  }

  async checkConnectionExists(connectionId) {
    try {
      const response = await fetch(`${this.baseUrl}/node-connections/${connectionId}/`, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });

      if (response.ok) {
        const connection = await response.json();
        console.log('✅ Connection found:', connection);
        return { exists: true, connection };
      } else if (response.status === 404) {
        console.log('❌ Connection not found');
        return { exists: false, error: 'Not found' };
      } else {
        console.log('❌ Error checking connection:', response.status);
        return { exists: false, error: response.status };
      }
    } catch (error) {
      console.error('❌ Network error:', error);
      return { exists: false, error: error.message };
    }
  }

  async findConnectionByNodes(sourceNodeId, targetNodeId) {
    try {
      const response = await fetch(
        `${this.baseUrl}/node-connections/?source_node=${sourceNodeId}&target_node=${targetNodeId}`,
        { headers: { 'Authorization': `Bearer ${this.token}` } }
      );

      if (response.ok) {
        const data = await response.json();
        console.log('🔍 Found connections:', data.results);
        return data.results;
      }
    } catch (error) {
      console.error('❌ Search error:', error);
    }
    return [];
  }

  async safeDeleteConnection(connectionId) {
    console.log(`🗑️ Attempting to delete connection: ${connectionId}`);
    
    // Step 1: Check if connection exists
    const checkResult = await this.checkConnectionExists(connectionId);
    
    if (!checkResult.exists) {
      console.log('ℹ️ Connection does not exist, no need to delete');
      return { success: true, message: 'Connection already deleted or not found' };
    }

    // Step 2: Attempt deletion
    try {
      const response = await fetch(`${this.baseUrl}/node-connections/${connectionId}/`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${this.token}` }
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Connection deleted successfully:', result);
        return { success: true, result };
      } else {
        const error = await response.json();
        console.error('❌ Delete failed:', error);
        
        // Try alternative methods
        return await this.tryAlternativeDelete(checkResult.connection);
      }
    } catch (error) {
      console.error('❌ Delete error:', error);
      return { success: false, error: error.message };
    }
  }

  async tryAlternativeDelete(connection) {
    console.log('🔄 Trying alternative delete methods...');
    
    // Method 1: Delete by nodes
    try {
      const response = await fetch(
        `${this.baseUrl}/node-connections/delete_by_nodes/?source_node=${connection.source_node.id}&target_node=${connection.target_node.id}&connection_type=${connection.connection_type}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${this.token}` }
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Alternative delete successful:', result);
        return { success: true, method: 'by_nodes', result };
      }
    } catch (error) {
      console.log('❌ Alternative delete failed:', error);
    }

    return { success: false, error: 'All delete methods failed' };
  }

  async debugWorkflowConnections(workflowId) {
    console.log(`🔍 Debugging connections for workflow: ${workflowId}`);
    
    try {
      const response = await fetch(
        `${this.baseUrl}/node-connections/?workflow=${workflowId}`,
        { headers: { 'Authorization': `Bearer ${this.token}` } }
      );

      if (response.ok) {
        const data = await response.json();
        console.log(`📊 Found ${data.count} connections in workflow`);
        
        data.results.forEach((conn, index) => {
          console.log(`${index + 1}. ${conn.id}`);
          console.log(`   ${conn.source_node?.title || 'Unknown'} → ${conn.target_node?.title || 'Unknown'}`);
          console.log(`   Type: ${conn.connection_type}`);
        });
        
        return data.results;
      }
    } catch (error) {
      console.error('❌ Debug error:', error);
    }
    
    return [];
  }
}

// Usage Examples
const debugger = new ConnectionDebugger('your-jwt-token');

// Debug the problematic connection
debugger.safeDeleteConnection('0c172da6-6946-44d2-bea5-797aa72b6c94');

// Debug all connections in a workflow
debugger.debugWorkflowConnections('your-workflow-id');

// Check if specific connection exists
debugger.checkConnectionExists('0c172da6-6946-44d2-bea5-797aa72b6c94');
'''
    
    print("💻 JavaScript Debug Helper")
    print("=" * 50)
    print(js_code)

def recommended_approach():
    """Recommended approach for handling this issue"""
    
    print("🎯 Recommended Approach")
    print("=" * 50)
    
    steps = [
        {
            "step": "1. Verify Connection Exists",
            "action": "GET /node-connections/{id}/",
            "purpose": "Check if the connection actually exists and you have permission"
        },
        {
            "step": "2. List All Connections", 
            "action": "GET /node-connections/",
            "purpose": "See all connections you have access to and find the correct ID"
        },
        {
            "step": "3. Use Alternative Delete",
            "action": "DELETE /node-connections/delete_by_nodes/",
            "purpose": "Delete by source/target nodes if you know them"
        },
        {
            "step": "4. Frontend Cleanup",
            "action": "Remove from UI state",
            "purpose": "Clean up UI even if backend delete fails"
        }
    ]
    
    for step in steps:
        print(f"🔸 {step['step']}")
        print(f"   Action: {step['action']}")
        print(f"   Purpose: {step['purpose']}")
        print()
    
    print("💡 Pro Tips:")
    print("✅ Always check if connection exists before deleting")
    print("✅ Implement graceful error handling in frontend")
    print("✅ Use optimistic UI updates with rollback on failure")
    print("✅ Log connection operations for debugging")
    print("❌ Don't assume deletion always succeeds")

if __name__ == "__main__":
    debug_connection_delete()
    common_issues_and_solutions()
    javascript_debug_helper()
    recommended_approach()
    
    print("\n🎯 Quick Fix for Your Issue:")
    print("1. Check if connection exists: GET /node-connections/0c172da6-6946-44d2-bea5-797aa72b6c94/")
    print("2. List all your connections: GET /node-connections/")
    print("3. Use alternative delete if needed: DELETE /node-connections/delete_by_nodes/")
    print("4. Update your UI state regardless of backend result")
