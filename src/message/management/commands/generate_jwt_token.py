from django.core.management.base import BaseCommand
from accounts.functions.jwt import login
from accounts.models import User


class Command(BaseCommand):
    help = 'Generate JWT token for a user (useful for WebSocket testing)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            required=True,
            help='Email of user to generate token for'
        )

    def handle(self, *args, **options):
        try:
            user_email = options['user_email']
            user = User.objects.get(email=user_email)
            
            # Generate tokens
            access_token, refresh_token = login(user)
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ JWT tokens generated for {user_email}")
            )
            self.stdout.write(f"\n📋 User Info:")
            self.stdout.write(f"   Email: {user.email}")
            self.stdout.write(f"   ID: {user.id}")
            self.stdout.write(f"   Name: {user.first_name} {user.last_name}")
            
            self.stdout.write(f"\n🔑 Access Token:")
            self.stdout.write(f"   {access_token}")
            
            self.stdout.write(f"\n🔄 Refresh Token:")
            self.stdout.write(f"   {refresh_token}")
            
            self.stdout.write(f"\n💻 Use in WebSocket connection:")
            self.stdout.write(f"   ws://localhost:8000/ws/chat/CONVERSATION_ID/?token={access_token}")
            
            self.stdout.write(f"\n🌐 Use in Browser Console:")
            self.stdout.write(f"""
const ws = new WebSocket('ws://localhost:8000/ws/chat/CONVERSATION_ID/?token={access_token}');
ws.onopen = () => console.log('Connected');
ws.onerror = (error) => console.error('Error:', error);
ws.onclose = (event) => console.log('Closed:', event.code, event.reason);
            """)
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ User with email '{user_email}' not found")
            )
            
            # Show available users (first 5)
            users = User.objects.all()[:5]
            if users:
                self.stdout.write("\n📋 Available users (first 5):")
                for user in users:
                    self.stdout.write(f"   - {user.email}")
            else:
                self.stdout.write("\n📋 No users found in database")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error generating token: {e}")
            ) 