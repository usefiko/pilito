import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from workflow.models import (
    Workflow, 
    WhenNode, 
    ActionNode, 
    NodeConnection
)

User = get_user_model()


class WorkflowExportImportTestCase(TestCase):
    """Test cases for workflow export/import functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create a simple test workflow
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            description='A test workflow for export/import',
            status='DRAFT',
            created_by=self.user
        )
        
        # Create a simple when node
        self.when_node = WhenNode.objects.create(
            workflow=self.workflow,
            title='When Message Received',
            position_x=100,
            position_y=100,
            when_type='receive_message',
            keywords=['hello']
        )
        
        # Create a simple action node
        self.action_node = ActionNode.objects.create(
            workflow=self.workflow,
            title='Send Response',
            position_x=300,
            position_y=100,
            action_type='send_message',
            message_content='Hello!'
        )
        
        # Create connection
        self.connection = NodeConnection.objects.create(
            workflow=self.workflow,
            source_node=self.when_node,
            target_node=self.action_node,
            connection_type='success'
        )
    
    def test_workflow_export_method(self):
        """Test the export_to_dict method on Workflow model"""
        export_data = self.workflow.export_to_dict()
        
        # Check basic structure
        self.assertIn('workflow', export_data)
        self.assertIn('nodes', export_data)
        self.assertIn('connections', export_data)
        self.assertIn('export_metadata', export_data)
        
        # Check workflow data
        workflow_data = export_data['workflow']
        self.assertEqual(workflow_data['name'], 'Test Workflow')
        
        # Check nodes
        nodes = export_data['nodes']
        self.assertEqual(len(nodes), 2)  # 2 nodes created
        
        # Check connections
        connections = export_data['connections']
        self.assertEqual(len(connections), 1)
    
    def test_workflow_import_method(self):
        """Test the import_from_dict class method"""
        export_data = self.workflow.export_to_dict()
        export_data['workflow']['name'] = 'Imported Workflow'
        
        imported_workflow = Workflow.import_from_dict(export_data, created_by=self.user)
        
        self.assertEqual(imported_workflow.name, 'Imported Workflow')
        self.assertNotEqual(imported_workflow.id, self.workflow.id)
        self.assertEqual(imported_workflow.nodes.count(), 2)
        self.assertEqual(imported_workflow.connections.count(), 1)
    
    def test_export_api_endpoint(self):
        """Test the export API endpoint"""
        url = f'/workflow/api/workflows/{self.workflow.id}/export/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('workflow', response.data)
        self.assertIn('nodes', response.data)
    
    def test_import_api_endpoint(self):
        """Test the import API endpoint"""
        export_data = self.workflow.export_to_dict()
        export_data['workflow']['name'] = 'API Imported Workflow'
        
        url = '/workflow/api/workflows/import_workflow/'
        response = self.client.post(url, {
            'workflow_data': export_data
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('workflow', response.data)
        
        # Verify workflow was created
        imported_workflow_data = response.data['workflow']
        imported_workflow = Workflow.objects.get(id=imported_workflow_data['id'])
        self.assertEqual(imported_workflow.name, 'API Imported Workflow')
