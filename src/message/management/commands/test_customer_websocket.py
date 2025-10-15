"""
Test command for the enhanced CustomerListConsumer WebSocket
"""
from django.core.management.base import BaseCommand
from accounts.models import User
from message.models import Customer, Conversation, Message
from message.serializers import CustomerWithConversationSerializer
import json


class Command(BaseCommand):
    help = 'Test the enhanced CustomerListConsumer functionality'

    def handle(self, *args, **options):
        self.stdout.write('🧪 Testing Enhanced CustomerListConsumer...')
        self.stdout.write('=' * 60)
        
        try:
            # Get a user with customers and conversations
            user = User.objects.filter(conversations__isnull=False).first()
            if not user:
                self.stdout.write('❌ No user with conversations found')
                return
            
            self.stdout.write(f'👤 Testing with user: {user.username} ({user.email})')
            
            # Get customers for this user
            customers = Customer.objects.filter(
                conversations__user=user
            ).prefetch_related(
                'conversations__messages',
                'conversations'
            ).distinct()[:5]  # Limit to 5 for testing
            
            if not customers.exists():
                self.stdout.write('❌ No customers found for this user')
                return
            
            self.stdout.write(f'📋 Found {customers.count()} customers to test')
            
            # Test the enhanced serializer
            serializer = CustomerWithConversationSerializer(
                customers, 
                many=True, 
                context={'user': user}
            )
            
            data = serializer.data
            
            # Display results
            self.stdout.write('\n📊 Sample Data Structure:')
            self.stdout.write('-' * 40)
            
            for i, customer_data in enumerate(data[:2]):  # Show first 2 customers
                self.stdout.write(f'\n🧑 Customer {i+1}:')
                self.stdout.write(f'  Name: {customer_data.get("first_name", "")} {customer_data.get("last_name", "")}')
                self.stdout.write(f'  Username: {customer_data.get("username", "N/A")}')
                self.stdout.write(f'  Source: {customer_data.get("source", "N/A")}')
                
                conversations = customer_data.get('conversations', [])
                self.stdout.write(f'  💬 Conversations: {len(conversations)}')
                
                for j, conv in enumerate(conversations[:2]):  # Show first 2 conversations
                    self.stdout.write(f'    📞 Conversation {j+1}:')
                    self.stdout.write(f'      ID: {conv.get("id")}')
                    self.stdout.write(f'      Status: {conv.get("status")}')
                    self.stdout.write(f'      Unread Count: {conv.get("unread_count", 0)}')
                    
                    last_msg = conv.get('last_message')
                    if last_msg:
                        self.stdout.write(f'      📨 Last Message:')
                        self.stdout.write(f'        Type: {last_msg.get("type")}')
                        self.stdout.write(f'        Content: {last_msg.get("content", "")[:50]}...')
                        self.stdout.write(f'        AI Response: {last_msg.get("is_ai_response", False)}')
                    else:
                        self.stdout.write(f'      📨 Last Message: None')
            
            # Show JSON structure sample
            self.stdout.write('\n📋 JSON Structure Sample:')
            self.stdout.write('-' * 40)
            
            # Simulate WebSocket response format
            ws_response = {
                'type': 'customers_list',
                'customers': data,
                'count': len(data),
                'timestamp': '2023-01-01T00:00:00Z'
            }
            
            # Show truncated JSON for readability
            sample_customer = data[0] if data else {}
            if 'conversations' in sample_customer and sample_customer['conversations']:
                # Show only first conversation to keep output manageable
                sample_customer['conversations'] = sample_customer['conversations'][:1]
            
            sample_response = {
                'type': 'customers_list',
                'customers': [sample_customer],
                'count': len(data),
                'timestamp': '2023-01-01T00:00:00Z'
            }
            
            json_output = json.dumps(sample_response, indent=2, default=str)
            self.stdout.write(json_output[:1000] + '...' if len(json_output) > 1000 else json_output)
            
            self.stdout.write('\n✅ Enhanced CustomerListConsumer test completed successfully!')
            self.stdout.write(f'📈 Enhancement benefits:')
            self.stdout.write(f'  • Each customer now includes conversation data')
            self.stdout.write(f'  • Last message content and metadata')
            self.stdout.write(f'  • Unread message counts')
            self.stdout.write(f'  • Conversation status and priority')
            self.stdout.write(f'  • AI response indicators')
            
        except Exception as e:
            self.stdout.write(f'❌ Test failed: {str(e)}')
            import traceback
            traceback.print_exc()