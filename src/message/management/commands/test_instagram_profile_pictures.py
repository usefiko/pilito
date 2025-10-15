import logging
from django.core.management.base import BaseCommand
from message.models import Customer
from settings.models import InstagramChannel
from message.insta import InstaWebhook

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Simple test for Instagram profile picture fetching using correct API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer-id',
            type=int,
            help='Test specific customer by ID',
        )
        parser.add_argument(
            '--user-id', 
            type=str,
            help='Test specific Instagram user ID',
        )

    def handle(self, *args, **options):
        customer_id = options.get('customer_id')
        user_id = options.get('user_id')
        
        self.stdout.write(
            self.style.SUCCESS('🧪 Instagram Profile Picture Test Tool (Simplified)\n')
        )

        # Get an Instagram channel with access token
        instagram_channel = InstagramChannel.objects.filter(
            is_connect=True,
            access_token__isnull=False
        ).exclude(access_token='').first()
        
        if not instagram_channel:
            self.stdout.write(
                self.style.ERROR("❌ No connected Instagram channels with access tokens found")
            )
            return
            
        self.stdout.write(f"🔑 Using channel: @{instagram_channel.username}")

        # Create webhook instance to use its methods
        webhook = InstaWebhook()

        if customer_id:
            self._test_customer_by_id(webhook, customer_id, instagram_channel)
        elif user_id:
            self._test_by_user_id(webhook, user_id, instagram_channel)
        else:
            # Test a few existing Instagram customers
            customers = Customer.objects.filter(source='instagram')[:3]
            if not customers:
                self.stdout.write(
                    self.style.WARNING("⚠️ No Instagram customers found")
                )
                return
            
            self.stdout.write(f"🔍 Testing {customers.count()} existing Instagram customers")
            
            for customer in customers:
                self._test_customer_by_id(webhook, customer.id, instagram_channel)

    def _test_customer_by_id(self, webhook, customer_id, instagram_channel):
        """Test profile picture fetching for existing customer"""
        try:
            customer = Customer.objects.get(id=customer_id, source='instagram')
            self.stdout.write(f"\n👤 Testing Customer: {customer.first_name} {customer.last_name}")
            self.stdout.write(f"   🆔 Customer ID: {customer.id}")
            self.stdout.write(f"   📱 Instagram ID: {customer.source_id}")
            
            current_picture = customer.profile_picture
            if current_picture and current_picture != "customer_img/default.png":
                self.stdout.write(f"   📷 Current picture: {current_picture.url}")
            else:
                self.stdout.write(f"   📷 Current picture: None/Default")
            
            self._test_by_user_id(webhook, customer.source_id, instagram_channel)
            
        except Customer.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Customer with ID {customer_id} not found")
            )

    def _test_by_user_id(self, webhook, user_id, instagram_channel):
        """Test profile picture fetching by Instagram user ID using simplified method"""
        self.stdout.write(f"\n🧪 Testing Instagram User ID: {user_id}")
        
        # Test the simplified flow
        self.stdout.write(f"   🔍 Fetching user details with correct API fields...")
        user_details = webhook._get_instagram_user_details(user_id, instagram_channel.access_token)
        
        if user_details:
            self.stdout.write(
                self.style.SUCCESS(f"   ✅ User details: {user_details}")
            )
            
            # Use correct field name 'profile_pic'
            profile_url = user_details.get('profile_pic')
            if profile_url:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Profile picture URL: {profile_url}")
                )
                
                # Test download
                self.stdout.write(f"   📸 Testing download...")
                profile_image = webhook._download_profile_picture(profile_url, user_id)
                if profile_image:
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Successfully downloaded profile picture ({profile_image.name})")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"   ⚠️ Profile picture download failed")
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f"   📷 No profile_pic field in API response")
                )
        else:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Failed to fetch user details from Instagram API")
            )

        self.stdout.write(f"   📊 Test completed for user {user_id}") 