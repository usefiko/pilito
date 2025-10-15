#!/usr/bin/env python3
"""
Test examples for Waiting Node API based on user's screenshots
Shows proper data mapping between frontend and backend
"""

import json
# import requests  # Not needed for examples

# مثال‌های دقیق برای ارسال داده به Waiting Node API

def test_waiting_node_examples():
    """Test different waiting node scenarios"""
    
    BASE_URL = "http://localhost:8000/api/v1/workflow/api"
    TOKEN = "your-jwt-token"
    WORKFLOW_ID = "your-workflow-uuid"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Waiting Node Examples")
    print("=" * 50)
    
    # Example 1: From User's Screenshot - Time Limit ON
    print("\n📱 Example 1: Based on User's Screenshot")
    screenshot_data = {
        "node_type": "waiting",
        "workflow": WORKFLOW_ID,
        "title": "new waiting node",
        "answer_type": "text",
        "storage_type": "database",
        "storage_field": "user_input",
        "customer_message": "salam",
        "allowed_errors": 3,
        "response_time_limit_enabled": True,  # Time limit is ON
        "response_timeout_amount": 30,       # Required when time limit is ON
        "response_timeout_unit": "minutes",  # Required when time limit is ON
        "skip_keywords": [],
        "position_x": 100,
        "position_y": 200
    }
    
    print("Request Data:")
    print(json.dumps(screenshot_data, indent=2))
    
    # Example 2: Time Limit OFF - No delay_time and time_unit needed
    print("\n🚫 Example 2: Time Limit OFF")
    time_limit_off_data = {
        "node_type": "waiting",
        "workflow": WORKFLOW_ID,
        "title": "Get Customer Name",
        "answer_type": "text",
        "storage_type": "user_profile",
        "storage_field": "full_name",
        "customer_message": "Please enter your full name:",
        "allowed_errors": 3,
        "response_time_limit_enabled": False,  # Time limit is OFF
        # No response_timeout_amount and response_timeout_unit when OFF
        "skip_keywords": ["skip", "later"],
        "position_x": 200,
        "position_y": 300
    }
    
    print("Request Data:")
    print(json.dumps(time_limit_off_data, indent=2))
    
    # Example 3: Choice Type with Time Limit
    print("\n🔘 Example 3: Choice Type with Time Limit")
    choice_data = {
        "node_type": "waiting",
        "workflow": WORKFLOW_ID,
        "title": "Choose Department",
        "answer_type": "choice",
        "storage_type": "session",
        "storage_field": "selected_department",
        "customer_message": "Which department do you need help with?",
        "choice_options": [
            "Technical Support",
            "Billing",
            "Sales",
            "General Inquiry"
        ],
        "allowed_errors": 3,
        "response_time_limit_enabled": True,
        "response_timeout_amount": 2,
        "response_timeout_unit": "minutes",
        "skip_keywords": [],
        "position_x": 300,
        "position_y": 400
    }
    
    print("Request Data:")
    print(json.dumps(choice_data, indent=2))
    
    # Example 4: Email with Custom Field Storage
    print("\n📧 Example 4: Email Collection")
    email_data = {
        "node_type": "waiting",
        "workflow": WORKFLOW_ID,
        "title": "Email Collection",
        "answer_type": "email",
        "storage_type": "custom_field",
        "storage_field": "email_address",
        "customer_message": "Please provide your email address for updates:",
        "allowed_errors": 2,
        "response_time_limit_enabled": True,
        "response_timeout_amount": 5,
        "response_timeout_unit": "minutes",
        "skip_keywords": ["skip"],
        "position_x": 400,
        "position_y": 500
    }
    
    print("Request Data:")
    print(json.dumps(email_data, indent=2))
    
    # Example 5: Temporary Storage (No storage_field needed)
    print("\n⏳ Example 5: Temporary Storage")
    temp_data = {
        "node_type": "waiting",
        "workflow": WORKFLOW_ID,
        "title": "Quick Feedback",
        "answer_type": "text",
        "storage_type": "temporary",
        # No storage_field needed for temporary storage
        "customer_message": "Any quick feedback?",
        "allowed_errors": 1,
        "response_time_limit_enabled": False,
        "skip_keywords": ["no", "skip"],
        "position_x": 500,
        "position_y": 600
    }
    
    print("Request Data:")
    print(json.dumps(temp_data, indent=2))
    
    return [screenshot_data, time_limit_off_data, choice_data, email_data, temp_data]

def frontend_to_backend_mapping():
    """Show exact field mapping from frontend to backend"""
    
    print("\n🔄 Frontend to Backend Field Mapping")
    print("=" * 50)
    
    mapping = {
        "Frontend Field": "Backend Field",
        "answer_type": "answer_type",
        "storage_location": "storage_type", 
        "customer_message": "customer_message",
        "max_errors": "allowed_errors",
        "response_time_limit": "response_time_limit_enabled",
        "delay_time": "response_timeout_amount",
        "time_unit": "response_timeout_unit",
        "exit_keywords": "skip_keywords"
    }
    
    for frontend, backend in mapping.items():
        print(f"{frontend:20} → {backend}")
    
    print("\n📝 Important Notes:")
    print("1. delay_time and time_unit are ONLY sent when response_time_limit is TRUE")
    print("2. storage_field is automatically generated or required based on storage_type")
    print("3. choice_options is only required for answer_type='choice'")

def validation_examples():
    """Show validation scenarios"""
    
    print("\n✅ Validation Examples")
    print("=" * 50)
    
    # Valid examples
    print("\n✅ VALID: Time limit enabled with delay fields")
    valid_with_time = {
        "response_time_limit_enabled": True,
        "response_timeout_amount": 30,
        "response_timeout_unit": "minutes"
    }
    print(json.dumps(valid_with_time, indent=2))
    
    print("\n✅ VALID: Time limit disabled without delay fields")
    valid_without_time = {
        "response_time_limit_enabled": False
        # No timeout fields needed
    }
    print(json.dumps(valid_without_time, indent=2))
    
    # Invalid examples
    print("\n❌ INVALID: Time limit enabled but missing delay fields")
    invalid_example = {
        "response_time_limit_enabled": True
        # Missing response_timeout_amount and response_timeout_unit
    }
    print(json.dumps(invalid_example, indent=2))
    print("Error: 'Timeout amount is required when time limit is enabled'")
    
    print("\n❌ INVALID: Choice type without options")
    invalid_choice = {
        "answer_type": "choice",
        "choice_options": []  # Empty array
    }
    print(json.dumps(invalid_choice, indent=2))
    print("Error: 'At least 2 choice options are required'")

def javascript_frontend_example():
    """JavaScript example for frontend implementation"""
    
    js_code = '''
// JavaScript Frontend Implementation
const createWaitingNode = (formData) => {
  const backendData = {
    node_type: "waiting",
    workflow: formData.workflow,
    title: formData.title,
    answer_type: formData.answer_type,
    storage_type: formData.storage_location,
    customer_message: formData.customer_message,
    allowed_errors: parseInt(formData.max_errors),
    response_time_limit_enabled: formData.response_time_limit,
    skip_keywords: formData.exit_keywords || []
  };

  // Add storage_field for non-temporary storage
  if (formData.storage_location !== 'temporary') {
    backendData.storage_field = generateStorageField(formData.answer_type);
  }

  // Only add timeout fields if time limit is enabled
  if (formData.response_time_limit) {
    backendData.response_timeout_amount = formData.delay_time;
    backendData.response_timeout_unit = formData.time_unit;
  }

  // Add choice options for choice type
  if (formData.answer_type === 'choice') {
    backendData.choice_options = formData.choice_options;
  }

  return backendData;
};

// Example usage:
const frontendForm = {
  title: "new waiting node",
  answer_type: "text",
  storage_location: "database",
  customer_message: "salam",
  max_errors: "3",
  response_time_limit: true,  // Time limit is ON
  delay_time: 30,            // Only sent when time limit is ON
  time_unit: "minutes",      // Only sent when time limit is ON
  exit_keywords: [],
  workflow: "workflow-uuid"
};

const apiPayload = createWaitingNode(frontendForm);
console.log("API Payload:", apiPayload);
'''
    
    print("\n💻 JavaScript Frontend Example")
    print("=" * 50)
    print(js_code)

if __name__ == "__main__":
    # Run all examples
    examples = test_waiting_node_examples()
    frontend_to_backend_mapping()
    validation_examples()
    javascript_frontend_example()
    
    print("\n🎉 All examples completed!")
    print("\nKey Points:")
    print("1. ✅ Time limit ON → Include delay_time and time_unit")
    print("2. ✅ Time limit OFF → Exclude delay_time and time_unit")
    print("3. ✅ Use storage_type instead of storage_location")
    print("4. ✅ Use allowed_errors instead of max_errors")
    print("5. ✅ Use skip_keywords instead of exit_keywords")
