import logging
from django.core.management.base import BaseCommand
from django.db.models import Q
from message.models import Customer
from message.services.telegram_service import TelegramService
from message.services.instagram_service import InstagramService
from settings.models import TelegramChannel, InstagramChannel
import requests
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update existing customers with profile pictures from Instagram and Telegram'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['telegram', 'instagram', 'all'],
            default='all',
            help='Update profile pictures for specific source or all',
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Update profile pictures even if customer already has one',
        )
        parser.add_argument(
            '--customer-id',
            type=int,
            help='Update specific customer by ID',
        )

    def handle(self, *args, **options):
        source = options.get('source')
        force_update = options.get('force_update')
        customer_id = options.get('customer_id')
        
        self.stdout.write(
            self.style.SUCCESS('🖼️ Customer Profile Picture Update Tool\n')
        )

        # Filter customers
        if customer_id:
            try:
                customers = Customer.objects.filter(id=customer_id)
                if not customers.exists():
                    self.stdout.write(
                        self.style.ERROR(f"❌ Customer with ID {customer_id} not found")
                    )
                    return
                self.stdout.write(f"🎯 Processing specific customer: ID {customer_id}")
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f"❌ Invalid customer ID: {customer_id}")
                )
                return
        else:
            # Build filter for customers
            customer_filter = Q()
            
            if source == 'telegram':
                customer_filter = Q(source='telegram')
            elif source == 'instagram':
                customer_filter = Q(source='instagram')
            else:  # all
                customer_filter = Q(source__in=['telegram', 'instagram'])
            
            if not force_update:
                # Only update customers without profile pictures or with default ones
                customer_filter &= (
                    Q(profile_picture__isnull=True) | 
                    Q(profile_picture='') | 
                    Q(profile_picture='customer_img/default.png')
                )
            
            customers = Customer.objects.filter(customer_filter)

        total_customers = customers.count()
        self.stdout.write(f"🔍 Found {total_customers} customers to process")

        if total_customers == 0:
            self.stdout.write(
                self.style.WARNING("⚠️ No customers found matching criteria")
            )
            return

        success_count = 0
        skip_count = 0
        error_count = 0

        for customer in customers:
            self.stdout.write(f"\n👤 Processing: {customer.first_name} {customer.last_name} ({customer.source})")
            self.stdout.write(f"   🆔 Customer ID: {customer.id}, Source ID: {customer.source_id}")
            
            # Check if customer already has profile picture
            has_picture = customer.profile_picture and customer.profile_picture != "customer_img/default.png"
            if has_picture and not force_update:
                self.stdout.write(f"   ⏭️ Already has profile picture, skipping")
                skip_count += 1
                continue

            if customer.source == 'telegram':
                success = self._update_telegram_customer_picture(customer)
            elif customer.source == 'instagram':
                success = self._update_instagram_customer_picture(customer)
            else:
                self.stdout.write(f"   ❌ Unsupported source: {customer.source}")
                error_count += 1
                continue

            if success:
                success_count += 1
            else:
                error_count += 1

        # Summary
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"   ✅ Success: {success_count}")
        self.stdout.write(f"   ⏭️ Skipped: {skip_count}")
        self.stdout.write(f"   ❌ Errors: {error_count}")
        self.stdout.write(f"   📈 Total processed: {success_count + skip_count + error_count}")

    def _update_telegram_customer_picture(self, customer):
        """Update profile picture for Telegram customer"""
        try:
            # Find a Telegram channel to use for API calls
            # We'll use any active channel since we just need to make API calls
            telegram_channel = TelegramChannel.objects.filter(is_connect=True).first()
            
            if not telegram_channel:
                self.stdout.write(f"   ❌ No connected Telegram channels found")
                return False

            telegram_service = TelegramService(telegram_channel.bot_token)
            
            self.stdout.write(f"   📸 Fetching Telegram profile picture...")
            profile_image = telegram_service.download_profile_picture(customer.source_id)
            
            if profile_image:
                customer.profile_picture = profile_image
                customer.save()
                self.stdout.write(f"   ✅ Telegram profile picture updated successfully")
                return True
            else:
                self.stdout.write(f"   📷 No Telegram profile picture found")
                return False
                
        except Exception as e:
            self.stdout.write(f"   ❌ Error updating Telegram profile picture: {e}")
            return False

    def _update_instagram_customer_picture(self, customer):
        """Update profile picture for Instagram customer"""
        try:
            # Find an Instagram channel for this customer's conversations
            # or use any active channel for API calls
            instagram_channel = InstagramChannel.objects.filter(
                is_connect=True,
                access_token__isnull=False
            ).exclude(access_token='').first()
            
            if not instagram_channel:
                self.stdout.write(f"   ❌ No connected Instagram channels with access tokens found")
                return False

            self.stdout.write(f"   📸 Fetching Instagram profile picture...")
            
            # Use the same logic as in the webhook
            user_details = self._get_instagram_user_details_for_update(customer.source_id, instagram_channel.access_token)
            
            if user_details and user_details.get('profile_pic'):
                profile_pic_url = user_details['profile_pic']
                profile_image = self._download_instagram_profile_picture(profile_pic_url, customer.source_id)
                
                if profile_image:
                    customer.profile_picture = profile_image
                    customer.save()
                    self.stdout.write(f"   ✅ Instagram profile picture updated successfully")
                    return True
                else:
                    self.stdout.write(f"   📷 Failed to download Instagram profile picture")
                    return False
            else:
                self.stdout.write(f"   📷 No Instagram profile picture URL found")
                return False
                
        except Exception as e:
            self.stdout.write(f"   ❌ Error updating Instagram profile picture: {e}")
            return False

    def _get_instagram_user_details_for_update(self, user_id: str, access_token: str) -> dict:
        """Fetch Instagram user details using correct API fields"""
        try:
            url = f"https://graph.instagram.com/v23.0/{user_id}"
            
            # Use correct field names as per Instagram API documentation
            params = {
                'fields': 'id,name,username,profile_pic,is_verified_user,follower_count',
                'access_token': access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching Instagram user details for {user_id}: {e}")
            return {}

    def _download_instagram_profile_picture(self, picture_url: str, user_id: str):
        """Download Instagram profile picture"""
        try:
            if not picture_url:
                return None
                
            response = requests.get(picture_url, timeout=15)
            response.raise_for_status()
            
            if response.status_code == 200:
                image_content = ContentFile(response.content)
                image_content.name = f"instagram_profile_{user_id}.jpg"
                return image_content
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error downloading Instagram profile picture for {user_id}: {e}")
            return None 