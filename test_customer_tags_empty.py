"""
Test script to verify customer tags can be set to empty via the customer-item API endpoint.
"""
import requests
import json

# Configuration - UPDATE THESE VALUES
BASE_URL = "http://localhost:8000"  # or your actual URL
TOKEN = "YOUR_TOKEN_HERE"  # Replace with your actual JWT token
CUSTOMER_ID = 6  # Customer ID to test with

# API endpoint
url = f"{BASE_URL}/api/v1/message/customer-item/{CUSTOMER_ID}/"

# Headers
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("=" * 60)
print("Testing Customer Tags Clear Functionality")
print("=" * 60)

# Test 1: Get current customer data
print("\n1. Getting current customer data...")
response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    customer = response.json()
    print(f"Customer ID: {customer.get('id')}")
    print(f"Current tags: {customer.get('tag', [])}")
else:
    print(f"Error: {response.text}")
    exit(1)

# Test 2: Clear all tags (send empty array)
print("\n2. Clearing all user tags (sending empty array)...")
data = {
    "tag_ids": []
}
response = requests.patch(url, headers=headers, json=data)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    customer = response.json()
    tags = customer.get('tag', [])
    print(f"Tags after clear: {tags}")
    if len(tags) == 0:
        print("✅ SUCCESS: Tags cleared successfully!")
    else:
        print(f"❌ UNEXPECTED: Tags still present: {tags}")
else:
    print(f"❌ ERROR: {response.text}")
    try:
        errors = response.json()
        print(f"Validation errors: {json.dumps(errors, indent=2)}")
    except:
        pass

# Test 3: Add some tags back
print("\n3. Adding tags back...")
print("Enter tag IDs to add (comma-separated), or press Enter to skip:")
tag_input = input("> ").strip()
if tag_input:
    try:
        tag_ids = [int(x.strip()) for x in tag_input.split(",")]
        data = {"tag_ids": tag_ids}
        response = requests.patch(url, headers=headers, json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            customer = response.json()
            print(f"Tags after adding: {customer.get('tag', [])}")
            print("✅ Tags added successfully!")
        else:
            print(f"❌ ERROR: {response.text}")
    except ValueError:
        print("Invalid input. Please enter comma-separated integers.")
else:
    print("Skipped.")

# Test 4: Update customer without touching tags
print("\n4. Updating customer without changing tags...")
data = {
    "first_name": customer.get('first_name', 'Test'),
}
response = requests.patch(url, headers=headers, json=data)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    updated = response.json()
    print(f"Tags should remain unchanged: {updated.get('tag', [])}")
    print("✅ Update without tag_ids worked!")
else:
    print(f"❌ ERROR: {response.text}")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)

