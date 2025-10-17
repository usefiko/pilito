#!/usr/bin/env python
"""
Quick test script to verify workflow API endpoints
Run this to check if the workflow system is properly configured
"""

import requests
import json
from urllib.parse import urljoin

# Base URL for your Fiko API
BASE_URL = "https://app.pilito.com/api/v1/workflow/api/"

# Test endpoints
ENDPOINTS_TO_TEST = [
    "node-workflows/",
    "when-nodes/",
    "condition-nodes/", 
    "action-nodes/",
    "waiting-nodes/",
    "node-connections/",
    "workflow-nodes/"
]

def test_workflow_endpoints():
    """Test if workflow API endpoints are accessible"""
    print("🔍 Testing Workflow API Endpoints...\n")
    
    results = {}
    
    for endpoint in ENDPOINTS_TO_TEST:
        url = urljoin(BASE_URL, endpoint)
        print(f"Testing: {url}")
        
        try:
            # Note: You'll need to add proper authentication headers
            headers = {
                'Content-Type': 'application/json',
                # 'Authorization': 'Bearer YOUR_TOKEN_HERE'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Working (200 OK)")
                results[endpoint] = "✅ Working"
            elif response.status_code == 401:
                print(f"🔐 {endpoint} - Needs Authentication (401)")
                results[endpoint] = "🔐 Auth Required"
            elif response.status_code == 403:
                print(f"🚫 {endpoint} - Permission Denied (403)")
                results[endpoint] = "🚫 Permission Denied"
            elif response.status_code == 404:
                print(f"❌ {endpoint} - Not Found (404)")
                results[endpoint] = "❌ Not Found"
            else:
                print(f"⚠️ {endpoint} - Status: {response.status_code}")
                results[endpoint] = f"⚠️ Status: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Connection Error: {str(e)}")
            results[endpoint] = f"❌ Connection Error"
        
        print()
    
    # Summary
    print("=" * 50)
    print("📊 SUMMARY:")
    print("=" * 50)
    
    for endpoint, status in results.items():
        print(f"{status} {endpoint}")
    
    # Check for critical issues
    critical_issues = [k for k, v in results.items() if "❌ Not Found" in v]
    if critical_issues:
        print(f"\n🚨 CRITICAL: {len(critical_issues)} endpoints not found!")
        print("This indicates the workflow URLs might not be properly configured.")
    
    auth_needed = [k for k, v in results.items() if "🔐" in v or "🚫" in v]
    if auth_needed:
        print(f"\n🔐 INFO: {len(auth_needed)} endpoints need authentication (this is normal)")

if __name__ == "__main__":
    test_workflow_endpoints()
