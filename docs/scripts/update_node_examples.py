#!/usr/bin/env python3
"""
Complete examples for updating workflow nodes of different types
"""

import json

def update_node_examples():
    """Show examples for updating different types of nodes"""
    
    print("🔄 How to Update Workflow Nodes")
    print("=" * 50)
    
    TOKEN = "your-jwt-token"
    BASE_URL = "http://localhost:8000/api/v1/workflow/api"
    
    # When Node Update Example
    print("\n🔥 1. Update When Node")
    print("-" * 40)
    
    when_node_update = {
        "node_type": "when",
        "workflow": "workflow-uuid",
        "title": "Updated Message Trigger",
        "when_type": "receive_message",
        "keywords": ["hello", "hi", "start", "help"],
        "channels": ["telegram", "instagram", "whatsapp"],
        "position_x": 150,
        "position_y": 200,
        "is_active": True
    }
    
    print("Complete Update (PUT):")
    print(json.dumps(when_node_update, indent=2))
    
    when_partial = {
        "title": "New Trigger Name",
        "keywords": ["updated", "keywords"]
    }
    
    print("\nPartial Update (PATCH):")
    print(json.dumps(when_partial, indent=2))
    
    # Condition Node Update Example
    print("\n❓ 2. Update Condition Node")
    print("-" * 40)
    
    condition_node_update = {
        "node_type": "condition",
        "workflow": "workflow-uuid", 
        "title": "Updated Intent Check",
        "combination_operator": "or",
        "conditions": [
            {
                "type": "ai",
                "prompt": "Is this customer asking about pricing, billing, or payment?"
            },
            {
                "type": "message",
                "operator": "contains",
                "value": "price"
            },
            {
                "type": "message", 
                "operator": "contains",
                "value": "cost"
            }
        ],
        "position_x": 350,
        "position_y": 200,
        "is_active": True
    }
    
    print("Complete Update (PUT):")
    print(json.dumps(condition_node_update, indent=2))
    
    condition_partial = {
        "title": "Price Inquiry Check",
        "combination_operator": "and"
    }
    
    print("\nPartial Update (PATCH):")
    print(json.dumps(condition_partial, indent=2))
    
    # Action Node Update Example  
    print("\n⚡ 3. Update Action Node")
    print("-" * 40)
    
    action_node_update = {
        "node_type": "action",
        "workflow": "workflow-uuid",
        "title": "Updated Welcome Message",
        "action_type": "send_message",
        "message_content": "Hello! Welcome to our updated platform! 🚀 How can we help you today?",
        "position_x": 550,
        "position_y": 200,
        "is_active": True
    }
    
    print("Complete Update (PUT):")
    print(json.dumps(action_node_update, indent=2))
    
    action_partial = {
        "message_content": "Updated welcome message with new content!",
        "position_x": 600
    }
    
    print("\nPartial Update (PATCH):")
    print(json.dumps(action_partial, indent=2))
    
    # Waiting Node Update Example
    print("\n⏳ 4. Update Waiting Node")
    print("-" * 40)
    
    waiting_node_update = {
        "node_type": "waiting",
        "workflow": "workflow-uuid",
        "title": "Updated Email Collection",
        "answer_type": "email",
        "storage_type": "user_profile",
        "storage_field": "email_address",
        "customer_message": "Please provide your updated email address for our newsletter:",
        "allowed_errors": 2,
        "response_time_limit_enabled": True,
        "response_timeout_amount": 10,
        "response_timeout_unit": "minutes",
        "skip_keywords": ["skip", "later", "no email"],
        "position_x": 750,
        "position_y": 200,
        "is_active": True
    }
    
    print("Complete Update (PUT):")
    print(json.dumps(waiting_node_update, indent=2))
    
    waiting_partial = {
        "customer_message": "Updated: Please share your email for important updates:",
        "response_timeout_amount": 15,
        "allowed_errors": 3
    }
    
    print("\nPartial Update (PATCH):")
    print(json.dumps(waiting_partial, indent=2))

def javascript_examples():
    """JavaScript examples for updating nodes"""
    
    js_code = '''
// JavaScript Examples for Node Updates

class NodeManager {
  constructor(token, baseUrl = '/api/v1/workflow/api') {
    this.token = token;
    this.baseUrl = baseUrl;
  }

  async updateNodeComplete(nodeId, nodeData) {
    const response = await fetch(`${this.baseUrl}/nodes/${nodeId}/`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(nodeData)
    });

    if (response.ok) {
      return response.json();
    } else {
      throw new Error(`Update failed: ${response.status}`);
    }
  }

  async updateNodePartial(nodeId, changes) {
    const response = await fetch(`${this.baseUrl}/nodes/${nodeId}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(changes)
    });

    if (response.ok) {
      return response.json();
    } else {
      throw new Error(`Partial update failed: ${response.status}`);
    }
  }

  // Quick methods for common updates
  async updateNodeTitle(nodeId, newTitle) {
    return this.updateNodePartial(nodeId, { title: newTitle });
  }

  async updateNodePosition(nodeId, x, y) {
    return this.updateNodePartial(nodeId, { 
      position_x: x, 
      position_y: y 
    });
  }

  async activateNode(nodeId) {
    return this.updateNodePartial(nodeId, { is_active: true });
  }

  async deactivateNode(nodeId) {
    return this.updateNodePartial(nodeId, { is_active: false });
  }

  // Specialized update methods
  async updateActionMessage(nodeId, newMessage) {
    return this.updateNodePartial(nodeId, { 
      message_content: newMessage 
    });
  }

  async updateWaitingTimeout(nodeId, amount, unit) {
    return this.updateNodePartial(nodeId, {
      response_timeout_amount: amount,
      response_timeout_unit: unit
    });
  }

  async updateConditionOperator(nodeId, operator) {
    return this.updateNodePartial(nodeId, {
      combination_operator: operator
    });
  }
}

// Usage Examples
const nodeManager = new NodeManager('your-jwt-token');

// Complete node update
const completeUpdate = async () => {
  try {
    const result = await nodeManager.updateNodeComplete('node-uuid', {
      node_type: "action",
      workflow: "workflow-uuid", 
      title: "Completely Updated Node",
      action_type: "send_message",
      message_content: "New message content",
      position_x: 400,
      position_y: 300,
      is_active: true
    });
    console.log('✅ Complete update success:', result);
  } catch (error) {
    console.error('❌ Complete update failed:', error);
  }
};

// Partial updates
const partialUpdates = async () => {
  try {
    // Update title only
    await nodeManager.updateNodeTitle('node-uuid', 'New Title');
    
    // Update position only
    await nodeManager.updateNodePosition('node-uuid', 500, 400);
    
    // Update activation status
    await nodeManager.deactivateNode('node-uuid');
    
    // Update action message
    await nodeManager.updateActionMessage('action-node-uuid', 'Updated message');
    
    // Update waiting timeout
    await nodeManager.updateWaitingTimeout('waiting-node-uuid', 20, 'minutes');
    
    console.log('✅ All partial updates completed');
  } catch (error) {
    console.error('❌ Partial update failed:', error);
  }
};
'''
    
    print("\n💻 JavaScript Examples")
    print("=" * 50)
    print(js_code)

def react_component_example():
    """React component for node editing"""
    
    react_code = '''
// React Component for Node Editing
import React, { useState, useEffect } from 'react';

const NodeEditor = ({ nodeId, token, onUpdate }) => {
  const [node, setNode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchNode();
  }, [nodeId]);

  const fetchNode = async () => {
    try {
      const response = await fetch(`/api/v1/workflow/api/nodes/${nodeId}/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const nodeData = await response.json();
      setNode(nodeData);
    } catch (err) {
      setError('Failed to fetch node');
    }
  };

  const updateNode = async (updates) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/workflow/api/nodes/${nodeId}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        const updatedNode = await response.json();
        setNode(updatedNode);
        if (onUpdate) onUpdate(updatedNode);
        console.log('✅ Node updated successfully');
      } else {
        throw new Error('Update failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!node) return <div>Loading...</div>;

  return (
    <div className="node-editor">
      <h3>Edit {node.node_type} Node</h3>
      
      {error && <div className="error">{error}</div>}
      
      {/* Title Editor */}
      <div>
        <label>Title:</label>
        <input
          type="text"
          value={node.title}
          onChange={(e) => setNode({...node, title: e.target.value})}
          onBlur={() => updateNode({ title: node.title })}
        />
      </div>

      {/* Position Editor */}
      <div>
        <label>Position X:</label>
        <input
          type="number"
          value={node.position_x}
          onChange={(e) => setNode({...node, position_x: parseInt(e.target.value)})}
          onBlur={() => updateNode({ 
            position_x: node.position_x,
            position_y: node.position_y 
          })}
        />
        <label>Position Y:</label>
        <input
          type="number"
          value={node.position_y}
          onChange={(e) => setNode({...node, position_y: parseInt(e.target.value)})}
          onBlur={() => updateNode({ 
            position_x: node.position_x,
            position_y: node.position_y 
          })}
        />
      </div>

      {/* Active Status */}
      <div>
        <label>
          <input
            type="checkbox"
            checked={node.is_active}
            onChange={(e) => {
              const isActive = e.target.checked;
              setNode({...node, is_active: isActive});
              updateNode({ is_active: isActive });
            }}
          />
          Active
        </label>
      </div>

      {/* Node Type Specific Fields */}
      {node.node_type === 'action' && (
        <div>
          <label>Message Content:</label>
          <textarea
            value={node.message_content || ''}
            onChange={(e) => setNode({...node, message_content: e.target.value})}
            onBlur={() => updateNode({ message_content: node.message_content })}
          />
        </div>
      )}

      {node.node_type === 'waiting' && (
        <div>
          <label>Customer Message:</label>
          <textarea
            value={node.customer_message || ''}
            onChange={(e) => setNode({...node, customer_message: e.target.value})}
            onBlur={() => updateNode({ customer_message: node.customer_message })}
          />
          
          <label>Allowed Errors:</label>
          <input
            type="number"
            value={node.allowed_errors}
            onChange={(e) => setNode({...node, allowed_errors: parseInt(e.target.value)})}
            onBlur={() => updateNode({ allowed_errors: node.allowed_errors })}
          />
        </div>
      )}

      {loading && <div>Updating...</div>}
    </div>
  );
};

// Usage
const WorkflowEditor = () => {
  const [selectedNodeId, setSelectedNodeId] = useState(null);

  const handleNodeUpdate = (updatedNode) => {
    console.log('Node updated:', updatedNode);
    // Update your workflow diagram state
  };

  return (
    <div>
      {selectedNodeId && (
        <NodeEditor
          nodeId={selectedNodeId}
          token="your-jwt-token"
          onUpdate={handleNodeUpdate}
        />
      )}
    </div>
  );
};
'''
    
    print("\n⚛️ React Component Example")
    print("=" * 50)
    print(react_code)

def curl_examples():
    """cURL examples for node updates"""
    
    print("\n🌐 cURL Examples")
    print("=" * 50)
    
    examples = [
        {
            "title": "Complete Action Node Update (PUT)",
            "command": '''curl -X PUT \\
  -H "Authorization: Bearer your-jwt-token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "node_type": "action",
    "workflow": "workflow-uuid",
    "title": "Updated Send Message",
    "action_type": "send_message", 
    "message_content": "Updated message content",
    "position_x": 400,
    "position_y": 300,
    "is_active": true
  }' \\
  "http://localhost:8000/api/v1/workflow/api/nodes/node-uuid/"'''
        },
        {
            "title": "Partial Node Update (PATCH)",
            "command": '''curl -X PATCH \\
  -H "Authorization: Bearer your-jwt-token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "New Node Title",
    "position_x": 500,
    "is_active": false
  }' \\
  "http://localhost:8000/api/v1/workflow/api/nodes/node-uuid/"'''
        },
        {
            "title": "Update Waiting Node Message",
            "command": '''curl -X PATCH \\
  -H "Authorization: Bearer your-jwt-token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "customer_message": "Updated: Please provide your email:",
    "response_timeout_amount": 15
  }' \\
  "http://localhost:8000/api/v1/workflow/api/nodes/waiting-node-uuid/"'''
        }
    ]
    
    for example in examples:
        print(f"\n📝 {example['title']}:")
        print(example['command'])

def validation_and_errors():
    """Show validation rules and common errors"""
    
    print("\n✅ Validation Rules & Common Errors")
    print("=" * 50)
    
    rules = [
        "✅ node_type cannot be changed in updates",
        "✅ workflow cannot be changed in updates", 
        "✅ Node-specific required fields must be present in PUT requests",
        "✅ PATCH requests only validate provided fields",
        "✅ position_x and position_y must be positive integers",
        "✅ is_active must be boolean (true/false)",
        "❌ Cannot update non-existent node (404 error)",
        "❌ Cannot update nodes from other users' workflows",
        "❌ Invalid node_type values will be rejected",
        "❌ Missing required fields in PUT will cause validation errors"
    ]
    
    for rule in rules:
        print(f"  {rule}")
    
    print("\n🔧 Common Error Responses:")
    
    errors = [
        {
            "error": "Node not found",
            "response": {"detail": "Not found."},
            "cause": "Invalid node ID or node belongs to another user"
        },
        {
            "error": "Validation error",
            "response": {"title": ["This field is required."]},
            "cause": "Missing required field in PUT request"
        },
        {
            "error": "Permission denied", 
            "response": {"error": "Permission denied"},
            "cause": "Trying to update node from another user's workflow"
        }
    ]
    
    for error in errors:
        print(f"\n❌ {error['error']}:")
        print(f"   Response: {json.dumps(error['response'])}")
        print(f"   Cause: {error['cause']}")

def best_practices():
    """Best practices for node updates"""
    
    print("\n💡 Best Practices")
    print("=" * 50)
    
    practices = [
        "✅ Use PATCH for small changes (title, position, activation)",
        "✅ Use PUT for complete node restructuring", 
        "✅ Always validate response status before assuming success",
        "✅ Update UI state immediately after successful update",
        "✅ Show loading states during update operations",
        "✅ Implement optimistic updates for better UX",
        "✅ Batch multiple small updates when possible",
        "✅ Use the Unified API (/nodes/) for consistency",
        "❌ Don't send unchanged data in PATCH requests",
        "❌ Don't update sensitive fields without validation",
        "❌ Don't forget to handle validation errors gracefully"
    ]
    
    for practice in practices:
        print(f"  {practice}")

if __name__ == "__main__":
    update_node_examples()
    javascript_examples()
    react_component_example()
    curl_examples()
    validation_and_errors()
    best_practices()
    
    print("\n🎉 Node Update Guide Complete!")
    print("\nQuick Summary:")
    print("1. 🔄 Complete Update: PUT /nodes/{id}/ (all fields)")
    print("2. 🔧 Partial Update: PATCH /nodes/{id}/ (only changed fields)")
    print("3. 🎯 Use PATCH for most updates - it's more efficient")
    print("4. ✅ Always handle validation errors and permissions")
