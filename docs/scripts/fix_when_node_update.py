#!/usr/bin/env python3
"""
Fix When Node Update - Correct request format and common issues
"""

import json

def fix_when_node_update():
    """Show correct format for When Node updates"""
    
    print("🔧 Fix When Node Update Request")
    print("=" * 50)
    
    NODE_ID = "96d57219-5bd2-4b4b-b50a-525b79a4a76c"
    
    # Your problematic request
    print("❌ Your Current Request (Causing 500 Error):")
    problematic_request = {
        "id": "",  # ❌ Problem: Empty ID should not be included
        "node_type": "when",
        "when_type": "receive_message", 
        "title": "new when node",
        "position_x": 280,
        "position_y": 260,
        "keywords": ["apelfp[a"],
        "channels": ["all"]  # ❌ Problem: "all" may not be valid channel
    }
    
    print(json.dumps(problematic_request, indent=2))
    
    print("\n✅ Corrected Request (Should Work):")
    corrected_request = {
        "node_type": "when",
        "workflow": "your-workflow-uuid",  # ✅ Required field
        "title": "new when node",
        "when_type": "receive_message",
        "keywords": ["hello", "help", "start"],  # ✅ Valid keywords
        "channels": ["telegram", "instagram"],  # ✅ Valid channels
        "position_x": 280,
        "position_y": 260,
        "is_active": True  # ✅ Good practice to include
        # ✅ No "id" field in PUT request
    }
    
    print(json.dumps(corrected_request, indent=2))
    
    print("\n🔍 Key Changes Made:")
    changes = [
        "❌ Removed empty 'id' field",
        "✅ Added required 'workflow' field", 
        "✅ Fixed 'channels' from ['all'] to specific channels",
        "✅ Added 'is_active' field",
        "✅ Fixed 'keywords' format"
    ]
    
    for change in changes:
        print(f"  {change}")

def valid_when_node_fields():
    """Show all valid fields and values for When Node"""
    
    print("\n📋 Valid When Node Fields")
    print("=" * 50)
    
    fields = {
        "Required Fields": {
            "node_type": "Must be 'when'",
            "workflow": "UUID of the workflow",
            "title": "String - node title",
            "when_type": "One of: receive_message, new_customer, add_tag, scheduled"
        },
        "Optional Fields": {
            "keywords": "Array of strings - trigger keywords",
            "channels": "Array of strings - telegram, instagram, whatsapp, email, sms",
            "customer_tags": "Array of strings - customer tags to filter",
            "schedule_frequency": "For scheduled type: once, daily, weekly, monthly, yearly",
            "schedule_date": "For scheduled type: YYYY-MM-DD",
            "schedule_time": "For scheduled type: HH:MM:SS", 
            "position_x": "Integer - X position in canvas",
            "position_y": "Integer - Y position in canvas",
            "is_active": "Boolean - true/false",
            "description": "String - optional description"
        }
    }
    
    for category, field_list in fields.items():
        print(f"\n{category}:")
        for field, desc in field_list.items():
            print(f"  {field}: {desc}")

def complete_examples():
    """Complete examples for different When Node types"""
    
    print("\n🎯 Complete When Node Examples")
    print("=" * 50)
    
    examples = [
        {
            "type": "Receive Message",
            "data": {
                "node_type": "when",
                "workflow": "workflow-uuid",
                "title": "New Message Trigger",
                "when_type": "receive_message",
                "keywords": ["hello", "hi", "help", "support"],
                "channels": ["telegram", "instagram"],
                "position_x": 100,
                "position_y": 200,
                "is_active": True
            }
        },
        {
            "type": "New Customer",
            "data": {
                "node_type": "when", 
                "workflow": "workflow-uuid",
                "title": "Welcome New Customer",
                "when_type": "new_customer",
                "customer_tags": ["new", "trial"],
                "channels": ["telegram", "email"],
                "position_x": 100,
                "position_y": 300,
                "is_active": True
            }
        },
        {
            "type": "Scheduled",
            "data": {
                "node_type": "when",
                "workflow": "workflow-uuid", 
                "title": "Daily Check-in",
                "when_type": "scheduled",
                "schedule_frequency": "daily",
                "schedule_time": "09:00:00",
                "channels": ["telegram"],
                "position_x": 100,
                "position_y": 400,
                "is_active": True
            }
        },
        {
            "type": "Tag Added",
            "data": {
                "node_type": "when",
                "workflow": "workflow-uuid",
                "title": "VIP Customer Tagged", 
                "when_type": "add_tag",
                "customer_tags": ["vip", "premium"],
                "channels": ["telegram", "email"],
                "position_x": 100,
                "position_y": 500,
                "is_active": True
            }
        }
    ]
    
    for example in examples:
        print(f"\n📝 {example['type']} Example:")
        print(json.dumps(example['data'], indent=2))

def curl_examples():
    """cURL examples with correct syntax"""
    
    print("\n🌐 Correct cURL Examples")
    print("=" * 50)
    
    NODE_ID = "96d57219-5bd2-4b4b-b50a-525b79a4a76c"
    
    # Complete update
    print("✅ Complete Update (PUT):")
    put_command = f'''curl -X PUT \\
  -H "Authorization: Bearer your-jwt-token" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "node_type": "when",
    "workflow": "your-workflow-uuid",
    "title": "Updated When Node",
    "when_type": "receive_message",
    "keywords": ["hello", "help", "start"],
    "channels": ["telegram", "instagram"], 
    "position_x": 280,
    "position_y": 260,
    "is_active": true
  }}' \\
  "https://api.fiko.net/api/v1/workflow/api/nodes/{NODE_ID}/"'''
    
    print(put_command)
    
    # Partial update
    print("\n✅ Partial Update (PATCH) - Recommended:")
    patch_command = f'''curl -X PATCH \\
  -H "Authorization: Bearer your-jwt-token" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "title": "Updated When Node",
    "keywords": ["hello", "help", "start"],
    "channels": ["telegram", "instagram"],
    "position_x": 280,
    "position_y": 260
  }}' \\
  "https://api.fiko.net/api/v1/workflow/api/nodes/{NODE_ID}/"'''
    
    print(patch_command)

def javascript_examples():
    """JavaScript examples with error handling"""
    
    js_code = '''
// JavaScript Examples with Proper Error Handling

class WhenNodeUpdater {
  constructor(token) {
    this.token = token;
    this.baseUrl = '/api/v1/workflow/api';
  }

  async updateWhenNode(nodeId, updates) {
    try {
      // Validate required fields for complete update
      if (updates.node_type && !updates.workflow) {
        throw new Error('workflow field is required for complete updates');
      }

      // Clean the data
      const cleanData = { ...updates };
      
      // Remove empty or invalid fields
      if (cleanData.id === '' || cleanData.id === null) {
        delete cleanData.id;
      }

      // Validate channels
      if (cleanData.channels) {
        const validChannels = ['telegram', 'instagram', 'whatsapp', 'email', 'sms'];
        cleanData.channels = cleanData.channels.filter(channel => 
          validChannels.includes(channel) || channel !== 'all'
        );
      }

      console.log('🔄 Updating When Node:', nodeId);
      console.log('📝 Data:', cleanData);

      const response = await fetch(`${this.baseUrl}/nodes/${nodeId}/`, {
        method: updates.node_type ? 'PUT' : 'PATCH',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cleanData)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ When Node updated successfully:', result);
        return { success: true, data: result };
      } else {
        const errorData = await response.json();
        console.error('❌ Update failed:', response.status, errorData);
        return { success: false, error: errorData, status: response.status };
      }

    } catch (error) {
      console.error('❌ Network error:', error);
      return { success: false, error: error.message };
    }
  }

  async safeUpdateWhenNode(nodeId, updates) {
    // Get current node data first
    try {
      const currentResponse = await fetch(`${this.baseUrl}/nodes/${nodeId}/`, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });

      if (currentResponse.ok) {
        const currentNode = await currentResponse.json();
        
        // Merge with current data for safer update
        const mergedData = {
          ...currentNode,
          ...updates,
          // Always ensure required fields
          node_type: 'when',
          workflow: currentNode.workflow
        };

        return await this.updateWhenNode(nodeId, mergedData);
      }
    } catch (error) {
      console.error('❌ Failed to get current node:', error);
    }

    // Fallback to direct update
    return await this.updateWhenNode(nodeId, updates);
  }
}

// Usage Examples
const updater = new WhenNodeUpdater('your-jwt-token');

// Fix your problematic request
const fixProblematicRequest = async () => {
  const nodeId = '96d57219-5bd2-4b4b-b50a-525b79a4a76c';
  
  // Fixed version of your request
  const correctData = {
    title: "new when node",
    when_type: "receive_message", 
    keywords: ["hello", "help"],  // Fixed from ["apelfp[a"]
    channels: ["telegram"],       // Fixed from ["all"]
    position_x: 280,
    position_y: 260
  };

  const result = await updater.safeUpdateWhenNode(nodeId, correctData);
  
  if (result.success) {
    console.log('✅ Fixed and updated successfully!');
  } else {
    console.error('❌ Still failing:', result.error);
  }
};

// Complete update example
const completeUpdate = async () => {
  const result = await updater.updateWhenNode('node-id', {
    node_type: "when",
    workflow: "workflow-uuid", 
    title: "Complete When Node",
    when_type: "receive_message",
    keywords: ["hello", "help", "support"],
    channels: ["telegram", "instagram"],
    position_x: 100,
    position_y: 200,
    is_active: true
  });
};

// Partial update example (safer)
const partialUpdate = async () => {
  const result = await updater.updateWhenNode('node-id', {
    title: "Updated Title",
    keywords: ["new", "keywords"],
    position_x: 300
  });
};
'''
    
    print("\n💻 JavaScript Examples with Error Handling")
    print("=" * 50)
    print(js_code)

def common_500_errors():
    """Common causes of 500 errors and solutions"""
    
    print("\n🚨 Common 500 Error Causes & Solutions")
    print("=" * 50)
    
    errors = [
        {
            "cause": "Empty 'id' field in request",
            "solution": "Remove 'id' field completely from PUT/PATCH requests",
            "example": "Remove: \"id\": \"\""
        },
        {
            "cause": "Missing required 'workflow' field",
            "solution": "Always include workflow UUID in complete updates",
            "example": "Add: \"workflow\": \"your-workflow-uuid\""
        },
        {
            "cause": "Invalid channel values",
            "solution": "Use valid channels: telegram, instagram, whatsapp, email, sms",
            "example": "Change: [\"all\"] → [\"telegram\"]"
        },
        {
            "cause": "Invalid when_type value", 
            "solution": "Use: receive_message, new_customer, add_tag, scheduled",
            "example": "Ensure: \"when_type\": \"receive_message\""
        },
        {
            "cause": "Database constraint violations",
            "solution": "Ensure node belongs to your workflow and you have permissions",
            "example": "Verify node ownership and workflow access"
        },
        {
            "cause": "Serializer validation errors",
            "solution": "Follow exact field requirements and data types",
            "example": "Use integers for position_x/y, arrays for keywords/channels"
        }
    ]
    
    for i, error in enumerate(errors, 1):
        print(f"{i}. ❌ {error['cause']}")
        print(f"   ✅ Solution: {error['solution']}")
        print(f"   📝 Example: {error['example']}")
        print()

if __name__ == "__main__":
    fix_when_node_update()
    valid_when_node_fields()
    complete_examples()
    curl_examples()
    javascript_examples()
    common_500_errors()
    
    print("\n🎯 Quick Fix for Your Request:")
    print("1. Remove: \"id\": \"\"")
    print("2. Add: \"workflow\": \"your-workflow-uuid\"") 
    print("3. Change: \"channels\": [\"all\"] → [\"telegram\"]")
    print("4. Fix: \"keywords\": [\"apelfp[a\"] → [\"hello\", \"help\"]")
    print("5. Use PATCH instead of PUT for partial updates")
