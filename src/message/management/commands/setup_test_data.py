from django.core.management.base import BaseCommand
from accounts.models import User
from message.models import Customer, Conversation, Message
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create test data for WebSocket development'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Setting up test data for WebSocket development...")
        
        # Create test user if not exists
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Created test user: {user.email}"))
        else:
            self.stdout.write(f"ℹ️  Test user already exists: {user.email}")

        # Create test customers
        customers_data = [
            {'first_name': 'Alice', 'last_name': 'Johnson', 'source': 'telegram', 'source_id': '12345'},
            {'first_name': 'Bob', 'last_name': 'Smith', 'source': 'instagram', 'source_id': '67890'},
            {'first_name': 'Charlie', 'last_name': 'Brown', 'source': 'telegram', 'source_id': '11111'},
        ]
        
        for customer_data in customers_data:
            customer, created = Customer.objects.get_or_create(
                source=customer_data['source'],
                source_id=customer_data['source_id'],
                defaults=customer_data
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created customer: {customer.first_name} {customer.last_name}"))
            
            # Create conversation
            conversation, conv_created = Conversation.objects.get_or_create(
                user=user,
                customer=customer,
                source=customer_data['source'],
                defaults={
                    'title': f"Chat with {customer.first_name}",
                    'status': 'active'
                }
            )
            
            if conv_created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created conversation: {conversation.id}"))
                
                # Add some test messages
                Message.objects.create(
                    conversation=conversation,
                    content=f"Hello! I'm {customer.first_name}",
                    type='customer',
                    customer=customer
                )
                
                Message.objects.create(
                    conversation=conversation,
                    content=f"Hi {customer.first_name}! How can I help you?",
                    type='support'
                )
        
        self.stdout.write("\n🎉 Test data setup complete!")
        self.stdout.write(f"📧 Test user email: {user.email}")
        self.stdout.write(f"🔑 Test user password: testpass123")
        self.stdout.write(f"👤 User ID: {user.id}")
        
        conversations = Conversation.objects.filter(user=user)
        self.stdout.write(f"\n💬 Available conversations:")
        for conv in conversations:
            self.stdout.write(f"   - {conv.id}: {conv.title}")
        
        self.stdout.write(f"\n🔗 Test WebSocket URLs:")
        self.stdout.write(f"   - Conversations: ws://localhost:8000/ws/conversations/")
        for conv in conversations:
            self.stdout.write(f"   - Chat {conv.title}: ws://localhost:8000/ws/chat/{conv.id}/")
        
        self.stdout.write(f"\n💡 Quick test command:")
        self.stdout.write(f"   docker exec -it django_app python manage.py simple_websocket_test") 