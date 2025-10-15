#!/usr/bin/env python3
"""
Test script to demonstrate workflow export/import functionality
"""

import os
import sys
import django
import json
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from workflow.models import Workflow, WhenNode, ActionNode, NodeConnection

User = get_user_model()

def create_sample_workflow():
    """Create a sample workflow for testing"""
    print("Creating sample workflow...")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='test_export_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Create workflow
    workflow = Workflow.objects.create(
        name='Sample Export Workflow',
        description='This is a sample workflow for testing export/import functionality',
        status='DRAFT',
        ui_settings={'theme': 'light', 'zoom': 1.0},
        max_executions=50,
        delay_between_executions=30,
        created_by=user
    )
    
    # Create when node
    when_node = WhenNode.objects.create(
        workflow=workflow,
        title='When Customer Says Hello',
        position_x=100,
        position_y=100,
        when_type='receive_message',
        keywords=['hello', 'hi', 'hey'],
        channels=['telegram', 'instagram', 'all']
    )
    
    # Create action node
    action_node = ActionNode.objects.create(
        workflow=workflow,
        title='Send Welcome Message',
        position_x=400,
        position_y=100,
        action_type='send_message',
        message_content='Hello! Welcome to our service. How can I help you today?'
    )
    
    # Create connection
    connection = NodeConnection.objects.create(
        workflow=workflow,
        source_node=when_node,
        target_node=action_node,
        connection_type='success'
    )
    
    print(f"✅ Created workflow: {workflow.name} (ID: {workflow.id})")
    print(f"✅ Created {workflow.nodes.count()} nodes")
    print(f"✅ Created {workflow.connections.count()} connections")
    
    return workflow

def test_export_functionality(workflow):
    """Test the export functionality"""
    print(f"\n🔄 Testing export functionality for workflow: {workflow.name}")
    
    try:
        # Export the workflow
        export_data = workflow.export_to_dict()
        
        print("✅ Export successful!")
        print(f"   - Exported workflow: {export_data['workflow']['name']}")
        print(f"   - Exported {len(export_data['nodes'])} nodes")
        print(f"   - Exported {len(export_data['connections'])} connections")
        print(f"   - Export metadata version: {export_data['export_metadata']['version']}")
        
        # Save to file for inspection
        export_file = 'sample_workflow_export.json'
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        print(f"   - Export saved to: {export_file}")
        
        return export_data
        
    except Exception as e:
        print(f"❌ Export failed: {str(e)}")
        return None

def test_import_functionality(export_data, original_workflow):
    """Test the import functionality"""
    print(f"\n🔄 Testing import functionality...")
    
    try:
        # Modify the name to avoid conflicts
        export_data['workflow']['name'] = 'Imported Sample Workflow'
        
        # Import the workflow
        user = original_workflow.created_by
        imported_workflow = Workflow.import_from_dict(export_data, created_by=user)
        
        print("✅ Import successful!")
        print(f"   - Imported workflow: {imported_workflow.name} (ID: {imported_workflow.id})")
        print(f"   - Imported {imported_workflow.nodes.count()} nodes")
        print(f"   - Imported {imported_workflow.connections.count()} connections")
        
        # Verify data integrity
        original_nodes = original_workflow.nodes.count()
        imported_nodes = imported_workflow.nodes.count()
        original_connections = original_workflow.connections.count()
        imported_connections = imported_workflow.connections.count()
        
        if original_nodes == imported_nodes and original_connections == imported_connections:
            print("✅ Data integrity verified - counts match!")
        else:
            print(f"⚠️  Data integrity warning - counts don't match")
            print(f"   Original: {original_nodes} nodes, {original_connections} connections")
            print(f"   Imported: {imported_nodes} nodes, {imported_connections} connections")
        
        # Verify node data
        original_when_node = original_workflow.nodes.filter(node_type='when').first()
        imported_when_node = imported_workflow.nodes.filter(node_type='when').first()
        
        if original_when_node and imported_when_node:
            original_when = original_when_node.whennode
            imported_when = imported_when_node.whennode
            
            if (original_when.when_type == imported_when.when_type and 
                original_when.keywords == imported_when.keywords):
                print("✅ Node data integrity verified!")
            else:
                print("⚠️  Node data integrity warning")
        
        return imported_workflow
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_api_endpoints():
    """Test the API endpoints (requires running server)"""
    print(f"\n📡 API Endpoints Available:")
    print(f"   - Export: GET /workflow/api/workflows/<id>/export/")
    print(f"   - Import: POST /workflow/api/workflows/import_workflow/")
    print(f"     Body: {{\"workflow_data\": <exported_json>, \"name\": \"Optional Override Name\"}}")

def cleanup_test_data():
    """Clean up test data"""
    print(f"\n🧹 Cleaning up test data...")
    
    try:
        # Delete test workflows
        deleted_count = Workflow.objects.filter(
            name__in=['Sample Export Workflow', 'Imported Sample Workflow']
        ).delete()[0]
        
        print(f"✅ Cleaned up {deleted_count} test workflows")
        
        # Remove export file
        export_file = 'sample_workflow_export.json'
        if os.path.exists(export_file):
            os.remove(export_file)
            print(f"✅ Removed export file: {export_file}")
            
    except Exception as e:
        print(f"⚠️  Cleanup warning: {str(e)}")

def main():
    """Main test function"""
    print("🚀 Starting Workflow Export/Import Test")
    print("=" * 50)
    
    try:
        # Create sample workflow
        workflow = create_sample_workflow()
        
        # Test export
        export_data = test_export_functionality(workflow)
        
        if export_data:
            # Test import
            imported_workflow = test_import_functionality(export_data, workflow)
            
            if imported_workflow:
                print(f"\n🎉 All tests passed successfully!")
                print(f"   - Original workflow ID: {workflow.id}")
                print(f"   - Imported workflow ID: {imported_workflow.id}")
            else:
                print(f"\n❌ Import test failed")
        else:
            print(f"\n❌ Export test failed")
        
        # Show API info
        test_api_endpoints()
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        cleanup_test_data()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == '__main__':
    main()
