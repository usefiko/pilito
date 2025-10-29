#!/usr/bin/env python3
"""
Test script for Customer Tags Management API
Usage: python test_customer_tags_api.py
"""

import requests
import json
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:8000/api/v1/msg"
TOKEN = "your_auth_token_here"  # Replace with your actual token
CUSTOMER_ID = 1  # Replace with actual customer ID

# Setup headers
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_response(response: requests.Response):
    """Print formatted response"""
    print(f"\n{Colors.BOLD}Status Code:{Colors.END} {response.status_code}")
    try:
        print(f"{Colors.BOLD}Response:{Colors.END}")
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def test_get_customer_tags(customer_id: int) -> Dict[str, Any]:
    """Test: Get all tags for a customer"""
    print_header("TEST 1: Get Customer Tags")
    
    try:
        response = requests.get(
            f"{BASE_URL}/customer/{customer_id}/tags/",
            headers=headers
        )
        
        if response.status_code == 200:
            print_success(f"Successfully retrieved tags for customer {customer_id}")
            print_response(response)
            return response.json()
        else:
            print_error(f"Failed to get tags")
            print_response(response)
            return {}
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return {}

def test_add_tags(customer_id: int, tag_ids: List[int]) -> bool:
    """Test: Add tags to customer"""
    print_header("TEST 2: Add Tags to Customer")
    print_info(f"Adding tags {tag_ids} to customer {customer_id}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/customer/{customer_id}/tags/",
            headers=headers,
            json={"tag_ids": tag_ids}
        )
        
        if response.status_code == 200:
            print_success("Successfully added tags")
            print_response(response)
            return True
        else:
            print_error("Failed to add tags")
            print_response(response)
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_replace_tags(customer_id: int, tag_ids: List[int]) -> bool:
    """Test: Replace all customer tags"""
    print_header("TEST 3: Replace Customer Tags")
    print_info(f"Replacing all tags with {tag_ids} for customer {customer_id}")
    
    try:
        response = requests.put(
            f"{BASE_URL}/customer/{customer_id}/tags/",
            headers=headers,
            json={"tag_ids": tag_ids}
        )
        
        if response.status_code == 200:
            print_success("Successfully replaced tags")
            print_response(response)
            return True
        else:
            print_error("Failed to replace tags")
            print_response(response)
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_remove_tags(customer_id: int, tag_ids: List[int]) -> bool:
    """Test: Remove specific tags from customer"""
    print_header("TEST 4: Remove Tags from Customer")
    print_info(f"Removing tags {tag_ids} from customer {customer_id}")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/customer/{customer_id}/tags/",
            headers=headers,
            json={"tag_ids": tag_ids}
        )
        
        if response.status_code == 200:
            print_success("Successfully removed tags")
            print_response(response)
            return True
        else:
            print_error("Failed to remove tags")
            print_response(response)
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_add_single_tag(customer_id: int, tag_id: int) -> bool:
    """Test: Add a single tag to customer"""
    print_header("TEST 5: Add Single Tag")
    print_info(f"Adding tag {tag_id} to customer {customer_id}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/customer/{customer_id}/tags/{tag_id}/",
            headers=headers
        )
        
        if response.status_code == 200:
            print_success("Successfully added single tag")
            print_response(response)
            return True
        else:
            print_error("Failed to add single tag")
            print_response(response)
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_remove_single_tag(customer_id: int, tag_id: int) -> bool:
    """Test: Remove a single tag from customer"""
    print_header("TEST 6: Remove Single Tag")
    print_info(f"Removing tag {tag_id} from customer {customer_id}")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/customer/{customer_id}/tags/{tag_id}/",
            headers=headers
        )
        
        if response.status_code == 200:
            print_success("Successfully removed single tag")
            print_response(response)
            return True
        else:
            print_error("Failed to remove single tag")
            print_response(response)
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_clear_all_tags(customer_id: int) -> bool:
    """Test: Clear all tags from customer"""
    print_header("TEST 7: Clear All Tags")
    print_info(f"Clearing all tags from customer {customer_id}")
    
    try:
        response = requests.put(
            f"{BASE_URL}/customer/{customer_id}/tags/",
            headers=headers,
            json={"tag_ids": []}
        )
        
        if response.status_code == 200:
            print_success("Successfully cleared all tags")
            print_response(response)
            return True
        else:
            print_error("Failed to clear tags")
            print_response(response)
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_error_handling(customer_id: int):
    """Test: Error handling scenarios"""
    print_header("TEST 8: Error Handling")
    
    # Test 1: Invalid tag IDs
    print_info("Testing with invalid tag IDs...")
    response = requests.post(
        f"{BASE_URL}/customer/{customer_id}/tags/",
        headers=headers,
        json={"tag_ids": [9999, 8888]}
    )
    if response.status_code == 400:
        print_success("Correctly rejected invalid tag IDs")
        print_response(response)
    else:
        print_error("Did not handle invalid tag IDs correctly")
    
    # Test 2: Empty tag list for POST
    print_info("\nTesting with empty tag list for POST...")
    response = requests.post(
        f"{BASE_URL}/customer/{customer_id}/tags/",
        headers=headers,
        json={"tag_ids": []}
    )
    if response.status_code == 400:
        print_success("Correctly rejected empty tag list")
        print_response(response)
    else:
        print_error("Did not handle empty tag list correctly")
    
    # Test 3: Invalid customer ID
    print_info("\nTesting with invalid customer ID...")
    response = requests.get(
        f"{BASE_URL}/customer/99999/tags/",
        headers=headers
    )
    if response.status_code in [403, 404]:
        print_success("Correctly handled invalid customer ID")
        print_response(response)
    else:
        print_error("Did not handle invalid customer ID correctly")

def run_all_tests():
    """Run all tests in sequence"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         Customer Tags Management API - Test Suite                 ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    print_warning(f"Base URL: {BASE_URL}")
    print_warning(f"Customer ID: {CUSTOMER_ID}")
    print_warning("Make sure to update TOKEN and CUSTOMER_ID before running!")
    
    input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")
    
    # Test 1: Get current tags
    initial_tags = test_get_customer_tags(CUSTOMER_ID)
    
    # Test 2: Add tags (assuming tags 1, 2 exist)
    test_add_tags(CUSTOMER_ID, [1, 2])
    
    # Test 3: Get tags again to verify
    test_get_customer_tags(CUSTOMER_ID)
    
    # Test 4: Replace tags
    test_replace_tags(CUSTOMER_ID, [3, 4])
    
    # Test 5: Get tags again
    test_get_customer_tags(CUSTOMER_ID)
    
    # Test 6: Add single tag
    test_add_single_tag(CUSTOMER_ID, 5)
    
    # Test 7: Get tags again
    test_get_customer_tags(CUSTOMER_ID)
    
    # Test 8: Remove single tag
    test_remove_single_tag(CUSTOMER_ID, 5)
    
    # Test 9: Remove multiple tags
    test_remove_tags(CUSTOMER_ID, [3])
    
    # Test 10: Get tags again
    test_get_customer_tags(CUSTOMER_ID)
    
    # Test 11: Clear all tags
    test_clear_all_tags(CUSTOMER_ID)
    
    # Test 12: Get tags to verify clear
    test_get_customer_tags(CUSTOMER_ID)
    
    # Test 13: Error handling
    test_error_handling(CUSTOMER_ID)
    
    print_header("All Tests Completed!")
    print_success("Check the results above for any failures")

def interactive_mode():
    """Interactive mode for manual testing"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         Customer Tags Management API - Interactive Mode           ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    while True:
        print(f"\n{Colors.BOLD}Options:{Colors.END}")
        print("1. Get customer tags")
        print("2. Add tags to customer")
        print("3. Replace customer tags")
        print("4. Remove tags from customer")
        print("5. Add single tag")
        print("6. Remove single tag")
        print("7. Clear all tags")
        print("8. Test error handling")
        print("9. Run all tests")
        print("0. Exit")
        
        choice = input(f"\n{Colors.YELLOW}Enter your choice: {Colors.END}")
        
        if choice == "1":
            customer_id = int(input("Enter customer ID: "))
            test_get_customer_tags(customer_id)
        elif choice == "2":
            customer_id = int(input("Enter customer ID: "))
            tag_ids = [int(x) for x in input("Enter tag IDs (comma-separated): ").split(",")]
            test_add_tags(customer_id, tag_ids)
        elif choice == "3":
            customer_id = int(input("Enter customer ID: "))
            tag_ids = [int(x) for x in input("Enter tag IDs (comma-separated): ").split(",")]
            test_replace_tags(customer_id, tag_ids)
        elif choice == "4":
            customer_id = int(input("Enter customer ID: "))
            tag_ids = [int(x) for x in input("Enter tag IDs (comma-separated): ").split(",")]
            test_remove_tags(customer_id, tag_ids)
        elif choice == "5":
            customer_id = int(input("Enter customer ID: "))
            tag_id = int(input("Enter tag ID: "))
            test_add_single_tag(customer_id, tag_id)
        elif choice == "6":
            customer_id = int(input("Enter customer ID: "))
            tag_id = int(input("Enter tag ID: "))
            test_remove_single_tag(customer_id, tag_id)
        elif choice == "7":
            customer_id = int(input("Enter customer ID: "))
            test_clear_all_tags(customer_id)
        elif choice == "8":
            customer_id = int(input("Enter customer ID: "))
            test_error_handling(customer_id)
        elif choice == "9":
            run_all_tests()
        elif choice == "0":
            print_success("Goodbye!")
            break
        else:
            print_error("Invalid choice!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        run_all_tests()
    else:
        interactive_mode()

