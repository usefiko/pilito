import json
import logging
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import JsonResponse, HttpResponse
from settings.models import InstagramChannel
from settings.serializers import InstagramChannelSerializer
from message.models import Customer, Conversation, Message
from message.websocket_utils import notify_new_customer_message

logger = logging.getLogger(__name__)
VERIFY_TOKEN = '123456'


class InstaWebhook(APIView):
    permission_classes = [AllowAny]
    
    def get(self, *args, **kwargs):
        """Instagram webhook verification"""
        mode = self.request.query_params.get('hub.mode')
        token = self.request.query_params.get('hub.verify_token')
        challenge = self.request.query_params.get('hub.challenge')
        
        logger.info(f"Instagram webhook verification - mode: {mode}, token: {token}")
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("Instagram webhook verification successful")
            # Instagram expects the challenge as plain text response
            return Response(challenge or '', content_type='text/plain')
        
        logger.warning("Invalid Instagram webhook verification token")
        return Response('Invalid verification token', status=403)
    
    def post(self, *args, **kwargs):
        """Instagram webhook message handler"""
        try:
            data = json.loads(self.request.body.decode("utf-8"))
            logger.info(f"📩 Instagram Webhook Data: {data}")
            
            # Instagram webhook structure: { "object": "instagram", "entry": [...] }
            if data.get('object') != 'instagram':
                return JsonResponse({'status': 'ignored', 'reason': 'Not an Instagram webhook'}, status=200)
            
            entries = data.get('entry', [])
            processed_messages = []
            
            for entry in entries:
                # Process each entry in the webhook
                messages = self._process_entry(entry)
                processed_messages.extend(messages)
            
            response_data = {
                "status": "success",
                "message": "Instagram messages processed successfully",
                "processed_count": len(processed_messages),
                "data": processed_messages
            }
            
            return JsonResponse(response_data, status=200)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in Instagram webhook")
            return Response({
                "status": "error",
                "message": "Invalid JSON data",
                "error_code": "INVALID_JSON"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error processing Instagram webhook: {e}")
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _process_entry(self, entry):
        """Process a single entry from Instagram webhook"""
        processed_messages = []
        
        try:
            page_id = entry.get('id')  # Instagram page/account ID
            messaging_events = entry.get('messaging', [])
            
            logger.info(f"Processing entry for page ID: {page_id}, events: {len(messaging_events)}")
            
            for messaging in messaging_events:
                message_data = self._process_messaging_event(messaging, page_id)
                if message_data:
                    processed_messages.append(message_data)
                    
        except Exception as e:
            logger.error(f"Error processing entry: {e}")
        
        return processed_messages

    def _get_instagram_user_details(self, user_id: str, access_token: str) -> dict:
        """
        Fetch user information from Instagram Graph API using correct fields
        """
        try:
            # Instagram Graph API endpoint for user info
            url = f"https://graph.instagram.com/v23.0/{user_id}"
            
            # Use correct field names as per Instagram API documentation
            params = {
                'fields': 'id,name,username,profile_pic,is_verified_user,follower_count',
                'access_token': access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"✅ Successfully fetched Instagram user data for {user_id}: {user_data}")
                return user_data
            elif response.status_code == 400:
                # Handle token expiration
                try:
                    error_data = response.json()
                    error_code = error_data.get('error', {}).get('code')
                    
                    if error_code == 190:  # Token expired
                        logger.warning(f"🔄 Instagram access token expired, attempting refresh...")
                        refreshed_token = self._refresh_instagram_token(access_token)
                        if refreshed_token:
                            logger.info(f"✅ Token refreshed successfully, retrying...")
                            return self._get_instagram_user_details(user_id, refreshed_token)
                        else:
                            logger.error(f"❌ Failed to refresh Instagram token")
                    else:
                        logger.warning(f"❌ Instagram API error: {error_data}")
                except:
                    pass
                logger.warning(f"❌ Failed to fetch Instagram user data: {response.status_code} - {response.text}")
                return {}
            else:
                logger.warning(f"❌ Failed to fetch Instagram user data: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching Instagram user details for {user_id}: {e}")
            return {}

    def _download_profile_picture(self, picture_url: str, user_id: str) -> ContentFile:
        """
        Download profile picture from URL and return as ContentFile
        """
        try:
            if not picture_url:
                logger.info(f"📷 No profile picture URL provided for Instagram user {user_id}")
                return None
                
            logger.info(f"📸 Downloading Instagram profile picture for user {user_id} from: {picture_url}")
            response = requests.get(picture_url, timeout=15)
            response.raise_for_status()
            
            if response.status_code == 200:
                # Create a ContentFile from the image data
                image_content = ContentFile(response.content)
                # Generate a filename based on user_id
                image_content.name = f"instagram_profile_{user_id}.jpg"
                logger.info(f"✅ Successfully downloaded Instagram profile picture for user {user_id}")
                return image_content
            else:
                logger.warning(f"❌ Failed to download Instagram profile picture: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Timeout downloading Instagram profile picture for {user_id}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 Network error downloading Instagram profile picture for {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading Instagram profile picture for {user_id}: {e}")
            return None



    def _refresh_instagram_token(self, current_token: str) -> str:
        """
        Refresh Instagram access token (handles both short-lived and long-lived tokens)
        First tries to convert short-lived to long-lived, then tries to refresh long-lived
        """
        try:
            # First, try to convert short-lived token to long-lived token (Facebook Graph API)
            new_token, expires_in = self._exchange_for_long_lived_token(current_token)
            
            if new_token:
                logger.info(f"✅ Successfully converted/refreshed token via Facebook Graph API")
                # Update the token in the database
                return self._update_channel_token(current_token, new_token, expires_in)
            
            # If Facebook API failed, try Instagram API for long-lived token refresh
            logger.info("Facebook API failed, trying Instagram API for long-lived token refresh...")
            new_token, expires_in = self._refresh_long_lived_instagram_token(current_token)
            
            if new_token:
                logger.info(f"✅ Successfully refreshed token via Instagram API")
                # Update the token in the database
                return self._update_channel_token(current_token, new_token, expires_in)
            
            logger.error(f"❌ All token refresh methods failed")
            return None
                
        except Exception as e:
            logger.error(f"❌ Error refreshing Instagram token: {e}")
            return None

    def _exchange_for_long_lived_token(self, short_lived_token: str):
        """
        Exchange short-lived access token for long-lived access token using Instagram Graph API
        """
        try:
            from django.conf import settings
            
            # Use Instagram Graph API to exchange short-lived for long-lived token
            url = 'https://graph.instagram.com/access_token'
            
            # Get client credentials from settings or use hardcoded values
            client_secret = getattr(settings, 'INSTAGRAM_CLIENT_SECRET', '071f08aea723183951494234746982e4')
            
            params = {
                'grant_type': 'ig_exchange_token',
                'client_secret': client_secret,
                'access_token': short_lived_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                new_token = data.get('access_token')
                expires_in = data.get('expires_in')  # seconds until expiration
                
                if new_token:
                    logger.info(f"✅ Successfully exchanged for long-lived token, expires in {expires_in} seconds")
                    return new_token, expires_in
                else:
                    logger.error(f"❌ No access_token in exchange response: {data}")
                    return None, None
            else:
                error_data = response.json() if response.content else {}
                logger.warning(f"Facebook token exchange failed: {response.status_code} - {error_data}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error exchanging for long-lived token: {e}")
            return None, None

    def _refresh_long_lived_instagram_token(self, current_token: str):
        """
        Refresh Instagram long-lived access token using Instagram Graph API
        """
        try:
            # Instagram Graph API endpoint for refreshing long-lived tokens
            url = "https://graph.instagram.com/refresh_access_token"
            
            params = {
                'grant_type': 'ig_refresh_token',
                'access_token': current_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                new_token = data.get('access_token')
                expires_in = data.get('expires_in')  # seconds until expiration
                
                if new_token:
                    logger.info(f"✅ Successfully refreshed Instagram long-lived token, expires in {expires_in} seconds")
                    return new_token, expires_in
                else:
                    logger.error(f"❌ No access_token in Instagram refresh response: {data}")
                    return None, None
            else:
                error_data = response.json() if response.content else {}
                logger.warning(f"Instagram token refresh failed: {response.status_code} - {error_data}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error refreshing Instagram long-lived token: {e}")
            return None, None

    def _update_channel_token(self, current_token: str, new_token: str, expires_in: int = None) -> str:
        """
        Update channel token in database
        """
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            # Find the channel with this token and update it
            channel = InstagramChannel.objects.filter(access_token=current_token).first()
            if channel:
                channel.access_token = new_token
                
                # Calculate expiration time if provided
                if expires_in:
                    try:
                        expiration_time = timezone.now() + timedelta(seconds=int(expires_in))
                        channel.token_expires_at = expiration_time
                        days = expires_in // (24 * 3600)
                        hours = (expires_in % (24 * 3600)) // 3600
                        logger.info(f"✅ Instagram token updated for channel {channel.username}, expires in {days} days, {hours} hours")
                    except Exception as field_error:
                        # Field doesn't exist yet - ignore for now
                        logger.info(f"✅ Instagram token updated for channel {channel.username} (expiration tracking pending migration)")
                else:
                    logger.info(f"✅ Instagram token updated for channel {channel.username}, expiration time unknown")
                
                channel.save()
                return new_token
            else:
                logger.error(f"❌ Could not find Instagram channel with token to update")
                return None
        except Exception as e:
            logger.error(f"❌ Error updating Instagram token in database: {e}")
            return None

    def _download_profile_picture(self, picture_url: str, user_id: str) -> ContentFile:
        """
        Download profile picture from URL and return as ContentFile
        """
        try:
            if not picture_url:
                logger.info(f"📷 No profile picture URL provided for Instagram user {user_id}")
                return None
                
            logger.info(f"📸 Downloading Instagram profile picture for user {user_id} from: {picture_url}")
            response = requests.get(picture_url, timeout=15)
            response.raise_for_status()
            
            if response.status_code == 200:
                # Create a ContentFile from the image data
                image_content = ContentFile(response.content)
                # Generate a filename based on user_id
                image_content.name = f"instagram_profile_{user_id}.jpg"
                logger.info(f"✅ Successfully downloaded Instagram profile picture for user {user_id}")
                return image_content
            else:
                logger.warning(f"❌ Failed to download Instagram profile picture: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Timeout downloading Instagram profile picture for {user_id}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 Network error downloading Instagram profile picture for {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading Instagram profile picture for {user_id}: {e}")
            return None

    def _process_messaging_event(self, messaging, page_id):
        """Process a single messaging event"""
        try:
            sender_info = messaging.get('sender', {})
            sender_id = sender_info.get('id')
            recipient_info = messaging.get('recipient', {})
            recipient_id = recipient_info.get('id') 
            timestamp = messaging.get('timestamp')
            message = messaging.get('message', {})
            
            # Detect message type (text, image, voice, etc.)
            message_text = message.get('text')
            attachments = message.get('attachments', [])
            
            message_type = 'text'
            media_url = None
            placeholder_text = None
            
            # Check for image attachment
            if attachments:
                # Instagram sends attachments as array
                for attachment in attachments:
                    attach_type = attachment.get('type')
                    if attach_type == 'image':
                        message_type = 'image'
                        media_url = attachment.get('payload', {}).get('url')
                        placeholder_text = "[Image]"
                        logger.info(f"📸 Image message received from {sender_id}")
                        break
                    elif attach_type in ['audio', 'voice']:
                        message_type = 'voice'
                        media_url = attachment.get('payload', {}).get('url')
                        placeholder_text = "[Voice Message]"
                        logger.info(f"🎤 Voice message received from {sender_id}")
                        break
            
            # If no text and no supported attachment, ignore
            if not message_text and not media_url:
                logger.info("Ignoring unsupported message type")
                return None
            
            logger.info(f"Processing message from {sender_id} to {recipient_id}: {message_text}")
            
            # Determine which user is the account owner (recipient of webhook = our account)
            # In Instagram webhooks, the page that owns the webhook is the 'recipient' when receiving messages
            # and the 'sender' when sending messages
            account_owner_id = page_id  # The webhook owner's Instagram ID
            
            # Determine message direction
            is_customer_message = (sender_id != account_owner_id)
            is_owner_message = (sender_id == account_owner_id)
            
            if is_owner_message:
                # Message sent by account owner from Instagram app
                logger.info(f"📤 Detected OWNER message: Account owner {sender_id} sent message to customer {recipient_id}")
            else:
                # Message received from customer
                logger.info(f"📥 Detected CUSTOMER message: Customer {sender_id} sent message to account owner {recipient_id}")
            
            # پیدا کردن Instagram channel مناسب
            try:
                # Show all existing Instagram channels for debugging
                all_channels = InstagramChannel.objects.all()
                logger.info(f"🔍 All Instagram channels in database:")
                for ch in all_channels:
                    logger.info(f"  - Channel ID: {ch.id}, Username: {ch.username}, User: {ch.user.email}")
                    logger.info(f"    instagram_user_id: {ch.instagram_user_id}, page_id: {ch.page_id}, is_connect: {ch.is_connect}")
                
                # For owner messages, the sender_id is the account owner (our Instagram account)
                # For customer messages, the recipient_id is the account owner (our Instagram account)
                lookup_id = account_owner_id
                logger.info(f"🎯 Looking for account owner ID: {lookup_id}")
                
                # First try to find channel by page_id (webhook recipient_id)
                channel = InstagramChannel.objects.filter(
                    page_id=lookup_id,
                    is_connect=True
                ).first()
                
                if channel:
                    logger.info(f"✅ Found channel by page_id: {channel.username}")
                else:
                    logger.info(f"❌ No channel found by page_id: {lookup_id}")
                
                # If not found by page_id, try by instagram_user_id (fallback for existing channels)
                if not channel:
                    channel = InstagramChannel.objects.filter(
                        instagram_user_id=lookup_id,
                        is_connect=True
                    ).first()
                    
                    if channel:
                        logger.info(f"✅ Found channel by instagram_user_id: {channel.username}")
                        # Update the page_id for future lookups
                        channel.page_id = lookup_id
                        channel.save()
                        logger.info(f"Updated Instagram channel {channel.username} with page_id: {lookup_id}")
                    else:
                        logger.info(f"❌ No channel found by instagram_user_id: {lookup_id}")

                # Self-heal: if still not found, probe connected channels' /me id and fix mapping automatically
                if not channel:
                    try:
                        logger.info("🛠 Attempting auto-match: probing connected Instagram channels for matching Graph id")
                        connected_channels = InstagramChannel.objects.filter(is_connect=True)
                        for candidate in connected_channels:
                            try:
                                if not candidate.access_token:
                                    continue
                                url = "https://graph.instagram.com/v23.0/me"
                                params = {
                                    'fields': 'id,username',
                                    'access_token': candidate.access_token
                                }
                                # ✅ Use proxy-aware request
                                from core.utils import make_request_with_proxy
                                resp = make_request_with_proxy('get', url, params=params, timeout=10)
                                if resp.status_code != 200:
                                    continue
                                data = resp.json() if resp.content else {}
                                me_id = str(data.get('id')) if data else None
                                if me_id and me_id == str(lookup_id):
                                    # Found the correct channel; fix IDs and use it
                                    old_page_id = candidate.page_id
                                    old_instagram_user_id = candidate.instagram_user_id
                                    candidate.page_id = str(lookup_id)
                                    candidate.instagram_user_id = str(lookup_id)
                                    candidate.save(update_fields=['page_id', 'instagram_user_id'])
                                    logger.info(
                                        f"✅ Auto-matched channel {candidate.username} by Graph id. "
                                        f"Updated page_id from {old_page_id} to {candidate.page_id}, "
                                        f"instagram_user_id from {old_instagram_user_id} to {candidate.instagram_user_id}"
                                    )
                                    channel = candidate
                                    break
                            except Exception as probe_err:
                                logger.warning(f"Auto-match probe failed for channel {candidate.id}: {probe_err}")
                    except Exception as auto_err:
                        logger.warning(f"Auto-match routine error: {auto_err}")

                if not channel:
                    logger.warning(f"❌ FINAL: No Instagram channel found for account owner ID: {lookup_id}")
                    return {
                        "status": "error",
                        "message": f"Instagram channel with ID '{lookup_id}' not found",
                        "error_code": "CHANNEL_NOT_FOUND"
                    }
                
                logger.info(f"Found Instagram channel: {channel.username} for account owner {lookup_id}")
            except Exception as e:
                logger.error(f"Error finding Instagram channel: {e}")
                return {
                    "status": "error",
                    "message": f"Error finding Instagram channel: {str(e)}",
                    "error_code": "CHANNEL_LOOKUP_ERROR"
                }
            
            # Fetch detailed user information from Instagram Graph API
            # We want customer information, not account owner information
            customer_instagram_id = recipient_id if is_owner_message else sender_id
            user_details = {}
            if channel.access_token:
                logger.info(f"🔍 Fetching detailed user info for customer {customer_instagram_id}")
                user_details = self._get_instagram_user_details(customer_instagram_id, channel.access_token)
            else:
                logger.warning(f"⚠️ No access token available for channel {channel.username}, using basic info")
            
            # Extract user information - use API data if available, fallback to webhook data
            if user_details:
                # Use data from Instagram Graph API
                full_name = user_details.get('name', '')
                username = user_details.get('username', '')
                profile_pic_url = user_details.get('profile_pic', '')  # Use correct field name
                
                # Smart name processing
                if full_name:
                    # If we have a full name, use it
                    name_parts = full_name.strip().split(' ', 1)
                    first_name = name_parts[0] if name_parts else 'Instagram'
                    last_name = name_parts[1] if len(name_parts) > 1 else 'User'
                elif username:
                    # If we have username but no full name, use username creatively
                    if '.' in username:
                        # Handle usernames like "nima.dorostkar" 
                        name_parts = username.replace('_', '.').split('.')
                        first_name = name_parts[0].title() if name_parts else 'Instagram'
                        last_name = name_parts[1].title() if len(name_parts) > 1 else 'User'
                    else:
                        # Single word username
                        first_name = username.title()
                        last_name = 'User'
                else:
                    # Fallback if neither name nor username available
                    first_name = 'Instagram'
                    last_name = 'User'
                
                logger.info(f"📋 Using API data - Name: {full_name}, Username: {username}, Processed: {first_name} {last_name}")
            else:
                # Fallback to webhook data (limited) - extract customer info
                if is_owner_message:
                    # For owner messages, customer is the recipient
                    customer_info = recipient_info
                else:
                    # For customer messages, customer is the sender
                    customer_info = sender_info
                    
                first_name = customer_info.get('first_name', 'Instagram User')
                last_name = customer_info.get('last_name', ' ')
                profile_pic_url = None
                
                # If names are empty, use fallback
                if not first_name or first_name == '':
                    first_name = 'Instagram User'
                if not last_name or last_name == '':
                    last_name = str(customer_instagram_id)[-8:]  # Last 8 digits of ID
                
                logger.info(f"📋 Using webhook data - First: {first_name}, Last: {last_name}")
            
            # Prepare potential profile image
            customer_profile_image = None
            
            # Download and save profile picture if available
            if profile_pic_url:
                logger.info(f"🔍 Downloading Instagram profile picture for user {customer_instagram_id}")
                try:
                    profile_image = self._download_profile_picture(profile_pic_url, customer_instagram_id)
                    if profile_image:
                        customer_profile_image = profile_image
                        logger.info(f"✅ Instagram profile picture downloaded for user {customer_instagram_id}")
                    else:
                        logger.info(f"📷 Failed to download Instagram profile picture for user {customer_instagram_id}")
                except Exception as e:
                    logger.error(f"❌ Error downloading Instagram profile picture for {customer_instagram_id}: {e}")
            else:
                logger.info(f"📷 No Instagram profile picture available for user {customer_instagram_id}")

            # Create or update Customer but PRESERVE manual edits
            customer, created = Customer.objects.get_or_create(
                source='instagram',
                source_id=str(customer_instagram_id),
            )

            # On create, set fetched fields
            if created:
                customer.first_name = first_name
                customer.last_name = last_name
                if 'username' in locals():
                    customer.username = username
                if customer_profile_image:
                    customer.profile_picture = customer_profile_image
                customer.save()
                action = "created"
            else:
                # Only fill empty fields; do not overwrite non-empty (manual) values
                updated = False
                if not customer.first_name and first_name:
                    customer.first_name = first_name
                    updated = True
                if not customer.last_name and last_name:
                    customer.last_name = last_name
                    updated = True
                if (not customer.username) and ('username' in locals()) and username:
                    customer.username = username
                    updated = True
                # Update profile picture only if missing or default placeholder
                try:
                    has_default_avatar = not customer.profile_picture or str(customer.profile_picture) == "customer_img/default.png"
                except Exception:
                    has_default_avatar = True
                if customer_profile_image and has_default_avatar:
                    customer.profile_picture = customer_profile_image
                    updated = True
                if updated:
                    customer.save()
                action = "updated"

            logger.info(f"Customer {action}: {customer} (manual edits preserved)")

            # Assign Instagram tag when customer is created
            if created:
                from message.models import Tag
                instagram_tag, tag_created = Tag.objects.get_or_create(name="Instagram")
                customer.tag.add(instagram_tag)
                tag_action = "created" if tag_created else "found"
                logger.info(f"Instagram tag {tag_action} and assigned to customer {customer.id}")
            
            # Fetch Instagram bio for personalization (using RapidAPI scraper)
            if created or not customer.bio:
                try:
                    from message.services.instagram_profile_scraper import InstagramProfileScraper
                    
                    # Fetch full profile data using RapidAPI (includes bio)
                    profile = InstagramProfileScraper.get_profile(customer.username, use_cache=True)
                    
                    bio = profile.get('biography', '')
                    
                    if bio and profile.get('fetch_status') == 'ok':
                        # Save bio directly - Gemini will interpret it intelligently
                        customer.bio = bio
                        customer.save(update_fields=['bio'])
                        
                        logger.info(
                            f"📝 Instagram bio saved for customer {customer.id} (@{customer.username}): "
                            f"{bio[:50]}{'...' if len(bio) > 50 else ''}"
                        )
                    else:
                        fetch_status = profile.get('fetch_status', 'unknown')
                        if fetch_status == 'no_api_key':
                            logger.debug(f"⚠️ RapidAPI key not configured, skipping bio fetch for {customer.id}")
                        elif fetch_status == 'not_found':
                            logger.debug(f"Profile not found for @{customer.username}")
                        elif fetch_status == 'rate_limited':
                            logger.warning(f"⚠️ Rate limited when fetching profile for @{customer.username}")
                        else:
                            logger.debug(f"No bio available for customer {customer.id} (@{customer.username})")
                except Exception as e:
                    logger.warning(f"Failed to fetch bio for customer {customer.id}: {e}")

            # Get or create Conversation - only set status on creation
            try:
                # Try to get existing conversation first
                conversation = Conversation.objects.get(
                    user=channel.user,
                    source='instagram', 
                    customer=customer
                )
                conv_created = False
                logger.info(f"Found existing Instagram conversation: {conversation} with status: {conversation.status}")
                
            except Conversation.DoesNotExist:
                # Create new conversation with initial status
                from AI_model.utils import get_initial_conversation_status
                
                # Determine initial status based on user's default_reply_handler (only for new conversations)
                initial_status = get_initial_conversation_status(channel.user)
                
                conversation = Conversation.objects.create(
                    user=channel.user,
                    source='instagram', 
                    customer=customer,
                    status=initial_status
                )
                conv_created = True
                
                # Log the initial status for new conversation
                from AI_model.utils import log_conversation_status_change
                log_conversation_status_change(conversation, 'new', initial_status, f"Initial status based on user's default_reply_handler: {channel.user.default_reply_handler}")
                logger.info(f"Created new Instagram conversation: {conversation} with initial status: {initial_status}")
            
            # Always update conversation's updated_at field
            conversation.save(update_fields=['updated_at'])

            # Determine message type based on sender
            # If owner sent it, it's a 'support' message
            # If customer sent it, it's a 'customer' message
            msg_type = 'support' if is_owner_message else 'customer'
            
            # ✅ DEDUPLICATION: Prevent AI/Support messages from being duplicated when webhook arrives
            if is_owner_message:
                from django.utils import timezone
                from datetime import timedelta
                
                message_content = message_text or placeholder_text
                recent_cutoff = timezone.now() - timedelta(seconds=60)  # Increased to 60 seconds
                
                logger.info(f"🔍 Checking for duplicate owner messages...")
                logger.info(f"   Content: {message_content[:50]}...")
                logger.info(f"   Conversation: {conversation.id}")
                logger.info(f"   Time cutoff: {recent_cutoff}")
                
                # Check for ANY recent message (AI or support) with the EXACT same content
                existing_messages = Message.objects.filter(
                    conversation=conversation,
                    content=message_content,
                    created_at__gte=recent_cutoff,
                    type__in=['support', 'AI']
                ).order_by('-created_at')
                
                logger.info(f"   Found {existing_messages.count()} matching messages")
                
                if existing_messages.exists():
                    existing_msg = existing_messages.first()
                    logger.warning(f"⚠️⚠️⚠️ DUPLICATE DETECTED - BLOCKING WEBHOOK MESSAGE ⚠️⚠️⚠️")
                    logger.warning(f"   Existing message ID: {existing_msg.id}")
                    logger.warning(f"   Existing message type: {existing_msg.type}")
                    logger.warning(f"   Existing message is_ai: {existing_msg.is_ai_response}")
                    logger.warning(f"   Existing message created: {existing_msg.created_at}")
                    logger.warning(f"   Existing message metadata: {existing_msg.metadata}")
                    logger.warning(f"   >>> SKIPPING DUPLICATE CREATION FROM WEBHOOK <<<")
                    
                    return {
                        "status": "success",
                        "message": "Duplicate message blocked - message already exists from app",
                        "data": {
                            "message_direction": "owner_to_customer",
                            "duplicate": True,
                            "blocked": True,
                            "existing_message": {
                                "id": existing_msg.id,
                                "type": existing_msg.type,
                                "is_ai_response": existing_msg.is_ai_response,
                                "created_at": existing_msg.created_at.isoformat()
                            },
                            "conversation": {
                                "id": conversation.id,
                            }
                        }
                    }
                else:
                    logger.info(f"✅ No duplicate found - this is a NEW owner message from Instagram app")
            
            # Create Message based on type
            if message_type == 'text':
                message_obj = Message.objects.create(
                    content=message_text, 
                    conversation=conversation, 
                    customer=customer,
                    type=msg_type,
                    message_type='text',
                    processing_status='completed'
                )
                logger.info(f"✅ Text message created: {message_obj.id} (type={msg_type})")
                
                # Notify WebSocket for both customer and owner messages
                if is_customer_message:
                    notify_new_customer_message(message_obj)
                else:
                    # For owner messages sent from Instagram, broadcast to websocket
                    from message.websocket_utils import broadcast_to_chat_room, notify_conversation_status_change
                    from message.serializers import WSMessageSerializer
                    
                    broadcast_to_chat_room(
                        conversation.id,
                        'chat_message',
                        {
                            'message': WSMessageSerializer(message_obj).data,
                            'external_send_result': {'success': True, 'source': 'instagram_direct'}
                        }
                    )
                    # Update conversation list for user
                    notify_conversation_status_change(conversation)
                    logger.info(f"✅ Owner message from Instagram broadcasted to websocket: {message_obj.id}")
                
            else:
                # Image or Voice message
                message_obj = Message.objects.create(
                    content=placeholder_text,
                    conversation=conversation,
                    customer=customer,
                    type=msg_type,
                    message_type=message_type,
                    media_url=media_url,  # Instagram provides direct URL
                    processing_status='pending'
                )
                logger.info(f"✅ {message_type.capitalize()} message created (pending): {message_obj.id} (type={msg_type})")
                
                # Queue async processing
                if message_type == 'image':
                    from message.tasks_instagram_media import process_instagram_image
                    logger.info(f"📤 Queueing Instagram image processing for {message_obj.id}")
                    process_instagram_image.delay(str(message_obj.id), media_url, channel.access_token)
                elif message_type == 'voice':
                    from message.tasks_instagram_media import process_instagram_voice
                    logger.info(f"📤 Queueing Instagram voice processing for {message_obj.id}")
                    process_instagram_voice.delay(str(message_obj.id), media_url, channel.access_token)

            # Return detailed response with enhanced customer data
            return {
                "status": "success",
                "message": "Message received and processed successfully",
                "data": {
                    "message_direction": "owner_to_customer" if is_owner_message else "customer_to_owner",
                    "channel": {
                        "username": channel.username,
                        "owner": {
                            "id": channel.user.id,
                            "email": getattr(channel.user, 'email', None)
                        }
                    },
                    "customer": {
                        "id": customer.id,
                        "instagram_id": customer_instagram_id,
                        "first_name": customer.first_name,
                        "last_name": customer.last_name,
                        "full_name": f"{customer.first_name or ''} {customer.last_name or ''}".strip(),
                        "source": "instagram",
                        "has_profile_picture": bool(customer.profile_picture and customer.profile_picture != "customer_img/default.png"),
                        "profile_picture_url": customer.profile_picture.url if customer.profile_picture else None,
                        "was_created": created,
                        "enhanced_data_fetched": bool(user_details)
                    },
                    "conversation": {
                        "id": conversation.id,
                        "source": "instagram",
                        "was_created": conv_created
                    },
                    "message": {
                        "id": message_obj.id,
                        "content": message_text or placeholder_text,
                        "type": msg_type,
                        "message_type": message_type,
                        "timestamp": message_obj.created_at.isoformat()
                    }
                }
            }
            
        except KeyError as e:
            logger.error(f"Missing required field in Instagram data: {str(e)}")
            return {
                "status": "error", 
                "message": f"Missing required field in Instagram data: {str(e)}",
                "error_code": "INVALID_INSTAGRAM_DATA"
            }
        except Exception as e:
            logger.error(f"Error processing messaging event: {e}")
            return {
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }


class InstaChannelAPIView(APIView):
    serializer_class = InstagramChannelSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, *args, **kwargs):
        try:
            channel = InstagramChannel.objects.filter(user=self.request.user).last()
            if not channel:
                return Response("No channel found for this user", status=status.HTTP_404_NOT_FOUND)
            serializer = self.serializer_class(channel)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response("Channel not found or something went wrong, try again", status=status.HTTP_400_BAD_REQUEST)


class InstaChannelDebugAPIView(APIView):
    """Debug API to show all Instagram channels"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Show all channels for debugging
            all_channels = InstagramChannel.objects.all()
            
            channels_data = []
            for channel in all_channels:
                channels_data.append({
                    'id': channel.id,
                    'username': channel.username,
                    'user_email': channel.user.email,
                    'instagram_user_id': channel.instagram_user_id,
                    'page_id': channel.page_id,
                    'is_connect': channel.is_connect,
                    'account_type': channel.account_type,
                    'created_at': channel.created_at.isoformat() if hasattr(channel, 'created_at') else None
                })
            
            return Response({
                'total_channels': len(channels_data),
                'channels': channels_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in debug API: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstaChannelUpdatePageIdAPIView(APIView):
    """Debug API to update page_id for Instagram channel"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            channel_id = request.data.get('channel_id')
            new_page_id = request.data.get('page_id')
            
            if not channel_id or not new_page_id:
                return Response({
                    'error': 'Both channel_id and page_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find the channel
            try:
                channel = InstagramChannel.objects.get(id=channel_id, user=request.user)
            except InstagramChannel.DoesNotExist:
                return Response({
                    'error': 'Instagram channel not found or not owned by current user'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Update page_id
            old_page_id = channel.page_id
            channel.page_id = new_page_id
            channel.save()
            
            logger.info(f"Updated Instagram channel {channel.username} page_id from {old_page_id} to {new_page_id}")
            
            return Response({
                'message': 'Page ID updated successfully',
                'channel': {
                    'id': channel.id,
                    'username': channel.username,
                    'old_page_id': old_page_id,
                    'new_page_id': new_page_id,
                    'instagram_user_id': channel.instagram_user_id
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating page_id: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstaChannelAutoFixIDsAPIView(APIView):
    """Auto-fix Instagram channel IDs by fetching Graph API id (business page id)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            channel_id = request.data.get('channel_id')

            def _fix_channel(channel: InstagramChannel):
                try:
                    if not channel.access_token:
                        return {
                            'id': channel.id,
                            'username': channel.username,
                            'status': 'skipped',
                            'reason': 'No access_token'
                        }

                    url = 'https://graph.instagram.com/v23.0/me'
                    params = {
                        'fields': 'id,username',
                        'access_token': channel.access_token
                    }
                    resp = requests.get(url, params=params, timeout=15)
                    if resp.status_code != 200:
                        return {
                            'id': channel.id,
                            'username': channel.username,
                            'status': 'error',
                            'reason': f'API {resp.status_code}: {resp.text[:200]}'
                        }

                    data = resp.json()
                    ig_id = str(data.get('id'))
                    if not ig_id:
                        return {
                            'id': channel.id,
                            'username': channel.username,
                            'status': 'error',
                            'reason': 'No id in API response'
                        }

                    old_page_id = channel.page_id
                    old_instagram_user_id = channel.instagram_user_id
                    channel.page_id = ig_id
                    channel.instagram_user_id = ig_id
                    channel.save(update_fields=['page_id', 'instagram_user_id'])

                    return {
                        'id': channel.id,
                        'username': channel.username,
                        'status': 'updated',
                        'old_page_id': old_page_id,
                        'old_instagram_user_id': old_instagram_user_id,
                        'new_id': ig_id
                    }
                except Exception as fix_err:
                    logger.error(f"Error auto-fixing Instagram IDs for channel {channel.id}: {fix_err}")
                    return {
                        'id': channel.id,
                        'username': channel.username,
                        'status': 'error',
                        'reason': str(fix_err)
                    }

            results = []
            if channel_id:
                try:
                    channel = InstagramChannel.objects.get(id=channel_id, user=request.user)
                except InstagramChannel.DoesNotExist:
                    return Response({'error': 'Channel not found or not owned by user'}, status=status.HTTP_404_NOT_FOUND)
                results.append(_fix_channel(channel))
            else:
                channels = InstagramChannel.objects.filter(user=request.user)
                for ch in channels:
                    results.append(_fix_channel(ch))

            return Response({'results': results}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in InstaChannelAutoFixIDsAPIView: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)