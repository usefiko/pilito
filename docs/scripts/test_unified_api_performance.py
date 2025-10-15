#!/usr/bin/env python3
"""
Performance Test Script for Unified Node API
Tests the new unified node management API for performance and functionality
"""

import json
import time
import requests
import uuid
from typing import Dict, List, Any

class UnifiedNodeAPITester:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.created_nodes = []
        
    def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request with timing"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=self.headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'response_time': round((end_time - start_time) * 1000, 2),  # milliseconds
                'data': response.json() if response.status_code < 400 else response.text,
                'success': response.status_code < 400
            }
            
        except Exception as e:
            return {
                'status_code': 0,
                'response_time': -1,
                'data': str(e),
                'success': False
            }
    
    def test_node_creation(self, workflow_id: str) -> Dict[str, Any]:
        """Test creating different types of nodes"""
        print("🧪 Testing Node Creation...")
        
        test_nodes = [
            {
                'name': 'When Node',
                'data': {
                    'node_type': 'when',
                    'workflow': workflow_id,
                    'title': f'Test When Node {uuid.uuid4().hex[:8]}',
                    'when_type': 'receive_message',
                    'keywords': ['test', 'hello'],
                    'channels': ['telegram'],
                    'position_x': 100,
                    'position_y': 200
                }
            },
            {
                'name': 'Condition Node',
                'data': {
                    'node_type': 'condition',
                    'workflow': workflow_id,
                    'title': f'Test Condition Node {uuid.uuid4().hex[:8]}',
                    'combination_operator': 'and',
                    'conditions': [
                        {
                            'type': 'message',
                            'operator': 'contains',
                            'value': 'test'
                        }
                    ],
                    'position_x': 300,
                    'position_y': 200
                }
            },
            {
                'name': 'Action Node',
                'data': {
                    'node_type': 'action',
                    'workflow': workflow_id,
                    'title': f'Test Action Node {uuid.uuid4().hex[:8]}',
                    'action_type': 'send_message',
                    'message_content': 'Test message from API',
                    'position_x': 500,
                    'position_y': 200
                }
            },
            {
                'name': 'Waiting Node',
                'data': {
                    'node_type': 'waiting',
                    'workflow': workflow_id,
                    'title': f'Test Waiting Node {uuid.uuid4().hex[:8]}',
                    'answer_type': 'text',
                    'storage_type': 'temporary',
                    'customer_message': 'Please provide your response:',
                    'response_time_limit_enabled': True,
                    'response_timeout_amount': 5,
                    'response_timeout_unit': 'minutes',
                    'position_x': 700,
                    'position_y': 200
                }
            }
        ]
        
        results = []
        
        for test_node in test_nodes:
            result = self.make_request('POST', '/api/v1/workflow/api/nodes/', test_node['data'])
            results.append({
                'node_type': test_node['name'],
                'success': result['success'],
                'response_time': result['response_time'],
                'status_code': result['status_code']
            })
            
            if result['success'] and 'id' in result['data']:
                self.created_nodes.append(result['data']['id'])
                print(f"  ✅ {test_node['name']}: {result['response_time']}ms")
            else:
                print(f"  ❌ {test_node['name']}: Failed - {result['data']}")
        
        return results
    
    def test_node_retrieval(self) -> Dict[str, Any]:
        """Test retrieving nodes"""
        print("📖 Testing Node Retrieval...")
        
        if not self.created_nodes:
            print("  ⚠️ No nodes to test retrieval")
            return {}
        
        results = []
        
        # Test list all nodes
        result = self.make_request('GET', '/api/v1/workflow/api/nodes/')
        results.append({
            'operation': 'List All Nodes',
            'success': result['success'],
            'response_time': result['response_time'],
            'count': len(result['data'].get('results', [])) if result['success'] else 0
        })
        
        # Test get specific node
        for node_id in self.created_nodes[:2]:  # Test first 2 nodes
            result = self.make_request('GET', f'/api/v1/workflow/api/nodes/{node_id}/')
            results.append({
                'operation': f'Get Node {node_id[:8]}...',
                'success': result['success'],
                'response_time': result['response_time']
            })
        
        # Test filters
        filters = [
            '?node_type=action',
            '?is_active=true',
            '?search=test'
        ]
        
        for filter_param in filters:
            result = self.make_request('GET', f'/api/v1/workflow/api/nodes/{filter_param}')
            results.append({
                'operation': f'Filter {filter_param}',
                'success': result['success'],
                'response_time': result['response_time']
            })
            
        for test in results:
            status = "✅" if test['success'] else "❌"
            print(f"  {status} {test['operation']}: {test['response_time']}ms")
        
        return results
    
    def test_node_operations(self) -> Dict[str, Any]:
        """Test advanced node operations"""
        print("⚙️ Testing Advanced Operations...")
        
        if not self.created_nodes:
            print("  ⚠️ No nodes to test operations")
            return {}
        
        results = []
        node_id = self.created_nodes[0]
        
        # Test connections
        result = self.make_request('GET', f'/api/v1/workflow/api/nodes/{node_id}/connections/')
        results.append({
            'operation': 'Get Connections',
            'success': result['success'],
            'response_time': result['response_time']
        })
        
        # Test duplicate
        result = self.make_request('POST', f'/api/v1/workflow/api/nodes/{node_id}/duplicate/')
        results.append({
            'operation': 'Duplicate Node',
            'success': result['success'],
            'response_time': result['response_time']
        })
        
        if result['success'] and 'duplicated_node' in result['data']:
            self.created_nodes.append(result['data']['duplicated_node']['id'])
        
        # Test activate/deactivate
        result = self.make_request('POST', f'/api/v1/workflow/api/nodes/{node_id}/deactivate/')
        results.append({
            'operation': 'Deactivate Node',
            'success': result['success'],
            'response_time': result['response_time']
        })
        
        result = self.make_request('POST', f'/api/v1/workflow/api/nodes/{node_id}/activate/')
        results.append({
            'operation': 'Activate Node',
            'success': result['success'],
            'response_time': result['response_time']
        })
        
        # Test execution
        test_context = {
            'context': {
                'event': {
                    'type': 'MESSAGE_RECEIVED',
                    'data': {
                        'content': 'test message',
                        'user_id': 'test-user'
                    }
                }
            }
        }
        
        result = self.make_request('POST', f'/api/v1/workflow/api/nodes/{node_id}/test_execution/', test_context)
        results.append({
            'operation': 'Test Execution',
            'success': result['success'],
            'response_time': result['response_time']
        })
        
        # Test configuration endpoints
        config_endpoints = [
            '/api/v1/workflow/api/nodes/types/',
            '/api/v1/workflow/api/nodes/by_workflow/?workflow_id=test-workflow'
        ]
        
        for endpoint in config_endpoints:
            result = self.make_request('GET', endpoint)
            results.append({
                'operation': f'Config {endpoint.split("/")[-1].split("?")[0]}',
                'success': result['success'],
                'response_time': result['response_time']
            })
        
        for test in results:
            status = "✅" if test['success'] else "❌"
            print(f"  {status} {test['operation']}: {test['response_time']}ms")
        
        return results
    
    def test_bulk_operations(self, count: int = 10) -> Dict[str, Any]:
        """Test bulk operations for performance"""
        print(f"📊 Testing Bulk Operations ({count} nodes)...")
        
        # Bulk create
        start_time = time.time()
        created_count = 0
        
        for i in range(count):
            node_data = {
                'node_type': 'action',
                'workflow': 'test-workflow-bulk',
                'title': f'Bulk Test Node {i+1}',
                'action_type': 'send_message',
                'message_content': f'Message from bulk node {i+1}',
                'position_x': 100 + (i * 50),
                'position_y': 200
            }
            
            result = self.make_request('POST', '/api/v1/workflow/api/nodes/', node_data)
            if result['success']:
                created_count += 1
                self.created_nodes.append(result['data']['id'])
        
        bulk_create_time = time.time() - start_time
        
        # Bulk retrieve
        start_time = time.time()
        result = self.make_request('GET', '/api/v1/workflow/api/nodes/')
        bulk_retrieve_time = time.time() - start_time
        
        print(f"  📈 Bulk Create: {created_count}/{count} nodes in {bulk_create_time:.2f}s")
        print(f"  📈 Bulk Retrieve: {bulk_retrieve_time:.2f}s")
        
        return {
            'bulk_create': {
                'created': created_count,
                'total': count,
                'time': bulk_create_time,
                'avg_per_node': bulk_create_time / count if count > 0 else 0
            },
            'bulk_retrieve': {
                'time': bulk_retrieve_time,
                'success': result['success']
            }
        }
    
    def cleanup(self):
        """Clean up created test nodes"""
        print("🧹 Cleaning up test data...")
        
        deleted_count = 0
        for node_id in self.created_nodes:
            result = self.make_request('DELETE', f'/api/v1/workflow/api/nodes/{node_id}/')
            if result['success']:
                deleted_count += 1
        
        print(f"  🗑️ Deleted {deleted_count}/{len(self.created_nodes)} test nodes")
        self.created_nodes = []
    
    def run_complete_test(self, workflow_id: str = 'test-workflow'):
        """Run complete test suite"""
        print("🚀 Starting Unified Node API Performance Test")
        print("=" * 60)
        
        # Test node creation
        creation_results = self.test_node_creation(workflow_id)
        
        # Test node retrieval
        retrieval_results = self.test_node_retrieval()
        
        # Test advanced operations
        operations_results = self.test_node_operations()
        
        # Test bulk operations
        bulk_results = self.test_bulk_operations(5)  # Test with 5 nodes
        
        print("\n📊 Performance Summary:")
        print("=" * 60)
        
        # Creation performance
        if creation_results:
            avg_creation_time = sum(r['response_time'] for r in creation_results if r['success']) / len([r for r in creation_results if r['success']])
            success_rate = (sum(1 for r in creation_results if r['success']) / len(creation_results)) * 100
            print(f"📝 Node Creation:")
            print(f"   Average Response Time: {avg_creation_time:.2f}ms")
            print(f"   Success Rate: {success_rate:.1f}%")
        
        # Retrieval performance
        if retrieval_results:
            avg_retrieval_time = sum(r['response_time'] for r in retrieval_results if r['success']) / len([r for r in retrieval_results if r['success']])
            print(f"📖 Node Retrieval:")
            print(f"   Average Response Time: {avg_retrieval_time:.2f}ms")
        
        # Operations performance
        if operations_results:
            avg_operations_time = sum(r['response_time'] for r in operations_results if r['success']) / len([r for r in operations_results if r['success']])
            print(f"⚙️ Advanced Operations:")
            print(f"   Average Response Time: {avg_operations_time:.2f}ms")
        
        # Bulk performance
        if bulk_results:
            print(f"📊 Bulk Operations:")
            print(f"   Creation Rate: {bulk_results['bulk_create']['avg_per_node']:.3f}s per node")
            print(f"   Bulk Retrieve: {bulk_results['bulk_retrieve']['time']:.2f}s")
        
        print("\n✅ Test completed successfully!")
        
        # Cleanup
        self.cleanup()
        
        return {
            'creation': creation_results,
            'retrieval': retrieval_results,
            'operations': operations_results,
            'bulk': bulk_results
        }


def main():
    """Main function for command line usage"""
    
    # Configuration - Update these values
    BASE_URL = "http://localhost:8000"
    TOKEN = "your-jwt-token-here"  # Replace with actual token
    WORKFLOW_ID = "test-workflow-uuid"  # Replace with actual workflow ID
    
    print("🧪 Unified Node API Performance Tester")
    print("📝 Update BASE_URL and TOKEN variables before running")
    print()
    
    # Create tester instance
    tester = UnifiedNodeAPITester(BASE_URL, TOKEN)
    
    # Run complete test
    try:
        results = tester.run_complete_test(WORKFLOW_ID)
        
        # Save results to file
        with open('unified_api_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: unified_api_test_results.json")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        tester.cleanup()


if __name__ == "__main__":
    main()
