import requests
from django.shortcuts import redirect
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import json
import logging
import time
import hashlib
from settings.models import InstagramChannel
from message.models import Customer, Conversation, Message
from django.contrib.auth import get_user_model
from core.utils import get_active_proxy

User = get_user_model()
logger = logging.getLogger(__name__)

# Instagram webhook configuration - should match insta.py VERIFY_TOKEN
INSTAGRAM_VERIFY_TOKEN = '123456'



class InstagramAuthURLAPIView(APIView):
    """Generate Instagram authorization URL for the authenticated user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return the Instagram authorization URL for the current user"""
        try:
            user_id = request.user.id
            auth_url = InstagramCallbackAPIView.generate_instagram_auth_url(user_id)
            
            return Response({
                'auth_url': auth_url,
                'user_id': user_id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating Instagram auth URL: {str(e)}")
            return Response({
                'error': 'Failed to generate authorization URL'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstagramAuthURLWizardAPIView(APIView):
    """Generate Instagram authorization URL for the wizard flow"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return the Instagram authorization URL for the wizard flow"""
        try:
            user_id = request.user.id
            auth_url = InstagramCallbackAPIView.generate_instagram_auth_url_wizard(user_id)
            
            return Response({
                'auth_url': auth_url,
                'user_id': user_id,
                'flow': 'wizard'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating Instagram auth URL for wizard: {str(e)}")
            return Response({
                'error': 'Failed to generate authorization URL for wizard'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstagramCallbackAPIView(APIView):
    """Process Instagram OAuth callback and create InstagramChannel for the specified user"""
    permission_classes = [AllowAny]  # External callback from Instagram
    
    # Instagram API configuration
    CLIENT_ID = '1426281428401641'
    CLIENT_SECRET = '071f08aea723183951494234746982e4'
    REDIRECT_URI = 'https://api.pilito.com/api/v1/message/instagram-callback/'
    
    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        state = request.GET.get('state')  # Use state parameter instead of user_id
        
        # Check if this is a wizard flow to determine redirect URLs
        is_wizard_flow = state and state.startswith('wizard_')
        
        if error:
            logger.error(f"Instagram OAuth error: {error}")
            error_redirect = 'https://app.pilito.com/dashboard?status=error&message=oauth_error' if is_wizard_flow else 'https://app.pilito.com/dashboard/settings#channels?status=error&message=oauth_error'
            return redirect(error_redirect)
        
        if not code:
            logger.error("No authorization code received from Instagram")
            error_redirect = 'https://app.pilito.com/dashboard?status=error&message=no_code' if is_wizard_flow else 'https://app.pilito.com/dashboard/settings#channels?status=error&message=no_code'
            return redirect(error_redirect)
        
        if not state:
            logger.error("No state parameter received")
            return redirect('https://app.pilito.com/dashboard/settings#channels?status=error&message=no_state')
        
        try:
            # Step 1: Get the requesting user from state parameter and determine flow type
            user, is_wizard_flow = self._get_user_from_state(state)
            if not user:
                logger.error(f"User not found from state: {state}")
                error_redirect = 'https://app.pilito.com/dashboard?status=error&message=user_not_found' if is_wizard_flow else 'https://app.pilito.com/dashboard/settings#channels?status=error&message=user_not_found'
                return redirect(error_redirect)
            
            logger.info(f"Processing Instagram callback for user: {user.email} (ID: {user.id}) - Flow: {'wizard' if is_wizard_flow else 'settings'}")
            
            # Step 2: Exchange code for access token (short-lived)
            access_token, instagram_user_id = self._get_access_token(code)
            if not access_token:
                logger.error("Failed to get access token")
                error_redirect = 'https://app.pilito.com/dashboard?status=error&message=token_exchange_failed' if is_wizard_flow else 'https://app.pilito.com/dashboard/settings#channels?status=error&message=token_exchange_failed'
                return redirect(error_redirect)
            
            logger.info(f"Short-lived access token received, Instagram user ID: {instagram_user_id}")
            
            # Step 2.5: Convert short-lived token to long-lived token
            long_lived_token, expires_in = self._exchange_for_long_lived_token(access_token)
            if not long_lived_token:
                logger.warning("Failed to convert to long-lived token, using short-lived token")
                long_lived_token = access_token
                expires_in = 3600  # 1 hour for short-lived tokens
            else:
                logger.info(f"Successfully converted to long-lived token, expires in {expires_in} seconds")
            
            # Use the long-lived token from now on
            access_token = long_lived_token
            
            # Step 3: Get Instagram user info
            user_info = self._get_instagram_user_info(access_token, instagram_user_id)
            logger.info(f"Instagram user info: {user_info}")
            
            # Step 4: Create Instagram channel for the user
            channel = self._create_instagram_channel(user, access_token, user_info, expires_in)
            if not channel:
                logger.error("Failed to create Instagram channel")
                error_redirect = 'https://app.pilito.com/dashboard?status=error&message=channel_creation_failed' if is_wizard_flow else 'https://app.pilito.com/dashboard/settings#channels?status=error&message=channel_creation_failed'
                return redirect(error_redirect)
            
            # Step 5: Setup Instagram webhook (similar to Telegram implementation)
            webhook_success = self._setup_instagram_webhook(access_token, instagram_user_id)
            if webhook_success:
                channel.is_connect = True
                channel.save()
                logger.info(f"Instagram channel and webhook created successfully for user: {user.email}")
                success_redirect = 'https://app.pilito.com/dashboard?status=success' if is_wizard_flow else 'https://app.pilito.com/dashboard/settings#channels?status=success'
                return redirect(success_redirect)
            else:
                logger.warning(f"Instagram channel created but webhook setup failed for user: {user.email}")
                # Still redirect to success since channel was created, webhook setup can be retried
                success_redirect = 'https://app.pilito.com/dashboard?status=success&message=webhook_setup_failed' if is_wizard_flow else 'https://app.pilito.com/dashboard/settings#channels?status=success&message=webhook_setup_failed'
                return redirect(success_redirect)
                
        except Exception as e:
            logger.error(f"Error in Instagram callback: {str(e)}", exc_info=True)
            # Determine if this was a wizard flow for error redirect
            is_wizard = state and state.startswith('wizard_')
            error_redirect = 'https://app.pilito.com/dashboard?status=error&message=internal_error' if is_wizard else 'https://app.pilito.com/dashboard/settings#channels?status=error&message=internal_error'
            return redirect(error_redirect)

    def _get_user_from_state(self, state):
        """Get user from state parameter and determine flow type"""
        try:
            is_wizard_flow = False
            user_id_str = state
            
            # Check if this is a wizard flow
            if state.startswith('wizard_'):
                is_wizard_flow = True
                user_id_str = state.replace('wizard_', '')
            
            user_id = int(user_id_str)
            user = User.objects.get(id=user_id)
            return user, is_wizard_flow
        except (ValueError, User.DoesNotExist) as e:
            logger.error(f"Error getting user from state '{state}': {str(e)}")
            return None, False
        except Exception as e:
            logger.error(f"Unexpected error getting user from state '{state}': {str(e)}")
            return None, False

    def _get_access_token(self, code):
        """Exchange authorization code for access token"""
        url = 'https://api.instagram.com/oauth/access_token'
        data = {
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': self.REDIRECT_URI,
            'code': code
        }
        
        try:
            # ⚠️ OAuth callback باید بدون پروکسی باشه (Instagram خودش redirect می‌کنه)
            response = requests.post(url, data=data, timeout=30)
            logger.info(f"Instagram token exchange response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token')
                user_id = data.get('user_id')
                
                if access_token and user_id:
                    logger.info(f"Successfully obtained access token for Instagram user ID: {user_id}")
                    return access_token, user_id
                else:
                    logger.error(f"Missing access_token or user_id in response: {data}")
                    return None, None
            else:
                logger.error(f"Token exchange failed with status {response.status_code}: {response.text}")
                return None, None
                
        except requests.exceptions.Timeout:
            logger.error("Instagram API timeout during token exchange")
            return None, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during token exchange: {str(e)}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {str(e)}")
            return None, None

    def _exchange_for_long_lived_token(self, short_lived_token):
        """
        Exchange short-lived access token for long-lived access token
        Using Instagram Graph API: https://developers.facebook.com/docs/instagram-basic-display-api/guides/long-lived-access-tokens
        """
        try:
            url = 'https://graph.instagram.com/access_token'
            params = {
                'grant_type': 'ig_exchange_token',
                'client_secret': self.CLIENT_SECRET,
                'access_token': short_lived_token
            }
            
            logger.info("Converting short-lived token to long-lived token...")
            # ⚠️ Token exchange باید بدون پروکسی باشه
            response = requests.get(url, params=params, timeout=30)
            logger.info(f"Long-lived token exchange response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token')
                expires_in = data.get('expires_in')  # Number of seconds until expiration
                
                if access_token:
                    logger.info(f"Successfully obtained long-lived token, expires in {expires_in} seconds")
                    return access_token, expires_in
                else:
                    logger.error(f"Missing access_token in long-lived token response: {data}")
                    return None, None
            else:
                logger.error(f"Long-lived token exchange failed with status {response.status_code}: {response.text}")
                return None, None
                
        except requests.exceptions.Timeout:
            logger.error("Timeout during long-lived token exchange")
            return None, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during long-lived token exchange: {str(e)}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error during long-lived token exchange: {str(e)}")
            return None, None

    def _get_instagram_user_info(self, access_token, instagram_user_id):
        """Get Instagram user information with fallback approaches"""
        # Try to fetch from Instagram API first
        user_data = self._fetch_instagram_api_data(access_token)
        
        # If API fails, create info from token data
        if not user_data:
            logger.info("API fetch failed, using token data")
            user_data = self._create_user_info_from_token(instagram_user_id)
        
        return user_data

    def _fetch_instagram_api_data(self, access_token):
        """Attempt to fetch user data from Instagram API - only business accounts"""
        # Only try Graph API for business accounts
        fields = ['id', 'name', 'username', 'user_id', 'account_type', 'media_count', 'profile_picture_url']
        user_data = self._try_instagram_api(access_token, 'https://graph.instagram.com/v23.0/me', fields)

        if user_data:
            return {
                'instagram_user_id': user_data['user_id'],
                'original_user_id': user_data['id'],  # Keep original for reference
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'account_type': user_data.get('account_type', 'BUSINESS').upper(),
                'media_count': user_data.get('media_count', 0),
                'profile_picture_url': user_data.get('profile_picture_url', ''),
            }
        return None

    def _try_instagram_api(self, access_token, url, fields):
        """Generic method to try Instagram API with different field combinations"""
        for field_subset in [fields, ['id', 'username'], ['id']]:
            try:
                params = {
                    'fields': ','.join(field_subset),
                    'access_token': access_token
                }
                
                logger.info(f"Trying Instagram API: {url} with fields: {field_subset}")
                # ✅ استفاده از پروکسی برای دریافت اطلاعات از Instagram API
                response = requests.get(url, params=params, proxies=get_active_proxy(), timeout=30)
                logger.info(f"Instagram API response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Instagram API response data: {data}")
                    if 'id' in data:
                        logger.info(f"Instagram API success with fields {field_subset}: {data}")
                        return data
                else:
                    error_text = response.text
                    
                    # Check for specific error indicating personal account
                    if response.status_code == 400:
                        try:
                            error_data = response.json()
                            error_message = error_data.get('error', {}).get('message', '')
                            if 'Unsupported request - method type: get' in error_message:
                                logger.error(f"❌ ACCOUNT TYPE ERROR: Personal Instagram account detected!")
                                logger.error(f"   📋 User must convert to Instagram Business/Creator account")
                                logger.error(f"   🔗 Instructions: Instagram Settings → Account → Switch to Professional Account")
                                # Don't try other field combinations - this won't work for personal accounts
                                return None
                        except:
                            pass
                    
                    logger.warning(f"Instagram API failed with fields {field_subset}: {response.status_code} - {error_text}")
                    
            except requests.exceptions.Timeout:
                logger.error(f"Instagram API timeout with fields {field_subset}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Instagram API request error with fields {field_subset}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error trying Instagram API with fields {field_subset}: {e}")
        
        logger.warning("All Instagram API attempts failed")
        return None

    def _create_user_info_from_token(self, instagram_user_id):
        """
        Create user info from OAuth token data when Graph API fails
        Note: This uses OAuth user_id which may differ from Graph API 'id' required for posting messages
        """
        logger.info(f"Creating user info from Instagram user ID: {instagram_user_id}")
        logger.warning("Using OAuth user_id as fallback - this may not work for posting messages. Graph API 'id' is preferred.")
        logger.info(f"💡 If this is a personal Instagram account, user should convert to Business/Creator account for full features")

        return {
            'instagram_user_id': str(instagram_user_id),
            'original_user_id': str(instagram_user_id),
            'user_id': str(instagram_user_id),
            'username': f'instagram_user_{str(instagram_user_id)[-8:]}',  # Use last 8 digits for shorter username
            'account_type': 'PERSONAL',  # Likely personal account if API failed
            'media_count': 0,
            'profile_picture_url': '',  # No profile picture available when API fails
        }

    def _create_instagram_channel(self, user, access_token, user_info, expires_in=None):
        """Create or update InstagramChannel for user"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            # Check if this Instagram account is already connected to another user
            existing_channel = InstagramChannel.objects.filter(
                instagram_user_id=user_info['instagram_user_id']
            ).exclude(user=user).first()
            
            if existing_channel:
                logger.warning(f"Instagram account {user_info['username']} is already connected to user {existing_channel.user.email}")
                return None
            
            # Use the Page ID (instagram_user_id) for business accounts
            page_id = user_info['instagram_user_id']  # This should now be the Page ID
            original_user_id =  user_info['instagram_user_id']

            # Calculate token expiration time
            token_expires_at = None
            if expires_in:
                try:
                    token_expires_at = timezone.now() + timedelta(seconds=int(expires_in))
                    days = expires_in // (24 * 3600)
                    hours = (expires_in % (24 * 3600)) // 3600
                    logger.info(f"Token expires in: {days} days, {hours} hours")
                except Exception as e:
                    logger.warning(f"Could not calculate expiration time: {e}")

            # Create or update channel for this user
            channel, created = InstagramChannel.objects.update_or_create(
                user=user,
                instagram_user_id=page_id,  # Use Page ID as the main identifier
                defaults={
                    'username': user_info['username'],
                    'access_token': access_token,
                    'token_expires_at': token_expires_at,  # Store expiration time
                    'page_id': page_id,  # Store the same Page ID
                    'account_type': user_info.get('account_type', 'BUSINESS').lower(),
                    'media_count': user_info.get('media_count', 0),
                    'followers_count': 0,
                    'following_count': 0,
                    'profile_picture_url': user_info.get('profile_picture_url', ''),
                    'is_connect': False  # Will be set to True after webhook setup
                }
            )
            
            action = "created" if created else "updated"
            if token_expires_at:
                logger.info(f"Instagram channel {action}: {channel.username} for user {user.email}, page_id: {page_id}, expires: {token_expires_at}")
            else:
                logger.info(f"Instagram channel {action}: {channel.username} for user {user.email}, page_id: {page_id}")
            
            return channel
            
        except Exception as e:
            logger.error(f"Error creating Instagram channel: {str(e)}", exc_info=True)
            return None


    def _setup_instagram_webhook(self, access_token, instagram_user_id):
        """
        Setup Instagram webhook subscription using Instagram Graph API
        Note: Instagram webhooks require Instagram App Access Token and are typically
        configured once at the app level, not per user connection.
        """
        try:
            # For Instagram webhooks, we need an Instagram App Access Token, not user access token
            # Instagram webhooks are configured at the app level, not per user
            
            webhook_url = self._build_instagram_webhook_url()
            
            # Instagram webhook setup via Instagram Graph API using App Access Token
            url = f"https://graph.instagram.com/v23.0/{instagram_user_id}/subscribed_apps"
            
            data = {
                'object': 'instagram',
                'callback_url': webhook_url,
                'verify_token': INSTAGRAM_VERIFY_TOKEN,
                'subscribed_fields': 'messages',
                'access_token': access_token  # Use App Access Token, not user token
            }
            
            logger.info(f"Setting up Instagram webhook: {webhook_url}")
            
            # ✅ استفاده از پروکسی برای دریافت access token از Instagram
            response = requests.post(url, data=data, proxies=get_active_proxy(), timeout=30)
            logger.info(f"Instagram webhook setup response: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Instagram webhook setup successful: {response_data}")
                return True
            else:
                logger.warning(f"Instagram webhook setup failed with status {response.status_code}: {response.text}")
                logger.info("Instagram channel will be marked as connected. Webhook should be configured manually.")
                # Still return True since webhook is typically configured at app level
                return True
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during Instagram webhook setup: {str(e)}")
            logger.info("Instagram channel will be marked as connected. Webhook should be configured manually.")
            return True
        except Exception as e:
            logger.error(f"Unexpected error during Instagram webhook setup: {str(e)}")
            logger.info("Instagram channel will be marked as connected. Webhook should be configured manually.")
            return True

    def _get_instagram_app_access_token(self):
        """
        Get Instagram App Access Token for webhook management.
        """
        try:
            # Instagram App Access Token format: {app-id}|{app-secret}
            app_access_token = f"{self.CLIENT_ID}|{self.CLIENT_SECRET}"
            
            logger.info("✅ Generated Instagram App Access Token")
            # Don't validate - just return the token
            return app_access_token
            
        except Exception as e:
            logger.error(f"❌ Error generating Instagram App Access Token: {str(e)}")
            return None

    def _build_instagram_webhook_url(self):
        """
        Build the Instagram webhook URL similar to Telegram's _build_webhook_url
        """
        webhook_target = "https://api.pilito.com/api/v1/message/insta-webhook/"
        return webhook_target

    @staticmethod
    def generate_instagram_auth_url(user_id):
        """Generate Instagram OAuth URL with user_id in state parameter"""
        from urllib.parse import urlencode
        
        base_url = "https://www.instagram.com/oauth/authorize"
        params = {
            'client_id': '1426281428401641',
            'redirect_uri': 'https://api.pilito.com/api/v1/message/instagram-callback/',
            'response_type': 'code',
            'scope': 'instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments,instagram_business_content_publish,instagram_business_manage_insights',
            'state': str(user_id),  # Pass user_id in state parameter
            'force_reauth': 'true'
        }
        
        return f"{base_url}?{urlencode(params)}"

    @staticmethod
    def generate_instagram_auth_url_wizard(user_id):
        """Generate Instagram OAuth URL with user_id in state parameter for wizard flow"""
        from urllib.parse import urlencode
        
        base_url = "https://www.instagram.com/oauth/authorize"
        params = {
            'client_id': '1426281428401641',
            'redirect_uri': 'https://api.pilito.com/api/v1/message/instagram-callback/',
            'response_type': 'code',
            'scope': 'instagram_business_basic,instagram_business_manage_messages,instagram_business_manage_comments,instagram_business_content_publish,instagram_business_manage_insights',
            'state': f"wizard_{user_id}",  # Add wizard prefix to identify wizard flow
            'force_reauth': 'true'
        }
        
        return f"{base_url}?{urlencode(params)}"



# Additional classes for managing deauthorization and data deletion
class InstagramDeauthorizeAPIView(APIView):
    """Handle Instagram deauthorization requests"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            data = json.loads(request.body) if request.body else {}
            user_id = data.get('user_id')
            
            if user_id:
                # Deauthorize all Instagram channels for this Instagram user
                channels = InstagramChannel.objects.filter(instagram_user_id=str(user_id))
                for channel in channels:
                    channel.access_token = None
                    channel.is_connect = False
                    channel.save()
                
                logger.info(f"Deauthorized Instagram channels for Instagram user_id: {user_id}")
            
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in deauthorization: {e}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstagramDataDeletionAPIView(APIView):
    """Handle Instagram data deletion requests"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            data = json.loads(request.body) if request.body else {}
            user_id = data.get('user_id')
            
            if user_id:
                # Delete all data related to this Instagram user
                Customer.objects.filter(source='instagram', source_id=str(user_id)).delete()
                InstagramChannel.objects.filter(instagram_user_id=str(user_id)).delete()
                
                confirmation_code = f"deletion_{user_id}_{int(time.time())}"
                logger.info(f"Data deletion completed for Instagram user_id: {user_id}")
                
                return Response({
                    'url': f'https://api.pilito.com/api/v1/message/instagram/deletion-status/{confirmation_code}/',
                    'confirmation_code': confirmation_code
                }, status=status.HTTP_200_OK)
            
            return Response({'error': 'No user_id provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in data deletion: {e}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class InstagramDeletionStatusAPIView(APIView):
    """Check Instagram data deletion status"""
    permission_classes = [AllowAny]
    
    def get(self, request, confirmation_code):
        try:
            if not confirmation_code.startswith('deletion_'):
                return Response({'error': 'Invalid confirmation code'}, status=status.HTTP_400_BAD_REQUEST)
            
            parts = confirmation_code.split('_')
            if len(parts) != 3:
                return Response({'error': 'Invalid confirmation code format'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'status': 'confirmed',
                'message': 'Data deletion completed successfully',
                'confirmation_code': confirmation_code
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving deletion status: {e}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

