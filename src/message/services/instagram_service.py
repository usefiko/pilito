import logging
from typing import Optional, Dict, Any
from settings.models import InstagramChannel
from message.models import Message, Conversation, Customer
from core.utils import make_request_with_proxy

logger = logging.getLogger(__name__)


class InstagramService:
    """Service for sending messages to Instagram API"""
    
    # Updated to latest API version
    BASE_URL = "https://graph.instagram.com/v23.0"
    
    def __init__(self, access_token: str, instagram_user_id: str):
        self.access_token = access_token
        self.instagram_user_id = instagram_user_id
    
    def send_message(self, recipient_id: str, message_text: str) -> Dict[str, Any]:
        """
        Send a message to a specific Instagram user
        
        Args:
            recipient_id: Instagram user ID of the recipient
            message_text: Message text to send
            
        Returns:
            Dict containing API response
        """
        url = f"{self.BASE_URL}/{self.instagram_user_id}/messages"
        
        # Updated payload format according to Instagram API documentation
        payload = {
            'recipient': {
                'id': recipient_id
            },
            'message': {
                'text': message_text
            }
        }
        
        # Updated headers format according to Instagram API documentation
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # ✅ Send Instagram message with automatic fallback proxy
            response = make_request_with_proxy('post', url, json=payload, headers=headers, timeout=30)
            
            # Log the response for debugging
            logger.info(f"Instagram API response status: {response.status_code}")
            logger.info(f"Instagram API response body: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # Instagram API returns different structure than Telegram
            if 'message_id' in result or 'recipient_id' in result:
                logger.info(f"Message sent successfully to Instagram user {recipient_id}")
                return {
                    'success': True,
                    'message_id': result.get('message_id'),
                    'recipient_id': result.get('recipient_id'),
                    'data': result
                }
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                logger.error(f"Instagram API error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Error sending message to Instagram user {recipient_id}: {e}")
            # ✅ make_request_with_proxy already handles fallback automatically
            try:
                response = make_request_with_proxy('post', url, json=payload, headers=headers, timeout=30, use_fallback=True)
                response.raise_for_status()
                result = response.json()
                if 'message_id' in result or 'recipient_id' in result:
                    logger.info(f"✅ Message sent via fallback proxy to Instagram user {recipient_id}")
                    return {
                        'success': True,
                        'message_id': result.get('message_id'),
                        'recipient_id': result.get('recipient_id'),
                        'data': result
                    }
            except Exception as fallback_error:
                logger.error(f"Fallback proxy also failed: {fallback_error}")
            return {'success': False, 'error': 'Request timeout'}
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"{e.response.status_code} {e.response.reason}"
            try:
                error_response = e.response.json()
                if 'error' in error_response:
                    error_detail = error_response['error']
                    if isinstance(error_detail, dict):
                        error_code = error_detail.get('code')
                        error_msg = f"{error_msg}: {error_detail.get('message', 'Unknown error')}"
                        if 'error_user_msg' in error_detail:
                            error_msg += f" - {error_detail['error_user_msg']}"
                        
                        # Check for token expiration
                        if error_code == 190:  # Token expired
                            logger.warning(f"🔄 Instagram access token expired, attempting refresh...")
                            refreshed = self._attempt_token_refresh()
                            if refreshed:
                                logger.info(f"✅ Token refreshed, retrying message send...")
                                # Retry the send with refreshed token
                                return self.send_message(recipient_id, message_text)
                            else:
                                error_msg = "Token expired and refresh failed - user needs to reconnect"
                    else:
                        error_msg = f"{error_msg}: {error_detail}"
            except:
                # If we can't parse the error response, use the original error
                pass
            
            logger.error(f"HTTP error sending message to Instagram user {recipient_id}: {error_msg}")
            logger.error(f"Response body: {e.response.text}")
            return {'success': False, 'error': error_msg}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error sending message to Instagram user {recipient_id}: {e}")
            return {'success': False, 'error': str(e)}
            
        except Exception as e:
            logger.error(f"Unexpected error sending message to Instagram user {recipient_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_message_to_customer(self, customer: Customer, message_text: str) -> Dict[str, Any]:
        """
        Send message to a customer via their Instagram ID
        
        Args:
            customer: Customer instance with Instagram source
            message_text: Text to send
            
        Returns:
            Dict containing send result
        """
        if customer.source != 'instagram':
            return {'success': False, 'error': 'Customer is not from Instagram'}
        
        if not customer.source_id:
            return {'success': False, 'error': 'Customer has no Instagram ID'}
        
        return self.send_message(customer.source_id, message_text)
    
    @classmethod
    def get_service_for_conversation(cls, conversation: Conversation) -> Optional['InstagramService']:
        """
        Get InstagramService instance for a specific conversation
        
        Args:
            conversation: Conversation instance
            
        Returns:
            InstagramService instance or None if not found
        """
        try:
            if conversation.source != 'instagram':
                return None
                
            channel = InstagramChannel.objects.get(
                user=conversation.user,
                is_connect=True
            )
            
            if not channel.access_token or not channel.instagram_user_id:
                logger.error(f"Instagram channel for user {conversation.user.id} missing access token or user ID")
                return None
                
            return cls(channel.access_token, channel.instagram_user_id)
            
        except InstagramChannel.DoesNotExist:
            logger.error(f"No connected Instagram channel found for user {conversation.user.id}")
            return None
        except Exception as e:
            logger.error(f"Error getting Instagram service for conversation {conversation.id}: {e}")
            return None
    
    def get_user_info(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get information about Instagram user INCLUDING biography
        
        Note: biography field only available for Business/Creator accounts
        """
        target_user_id = user_id or self.instagram_user_id
        url = f"{self.BASE_URL}/{target_user_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Added biography, followers_count, follows_count for persona extraction
        params = {
            'fields': 'id,username,account_type,media_count,biography,followers_count,follows_count'
        }
        
        try:
            # ✅ Get Instagram user info with automatic fallback proxy
            response = make_request_with_proxy('get', url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if not result.get('error'):
                # Biography only available for Business accounts
                # Add empty bio if not present (Personal accounts)
                if 'biography' not in result:
                    result['biography'] = ""
                    logger.debug(f"Biography not available for user {target_user_id} (likely Personal account)")
                
                return {'success': True, 'data': result}
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Error getting Instagram user info: {e}")
            return {'success': False, 'error': str(e)}
    
    def verify_webhook_signature(self, payload: str, signature: str, app_secret: str) -> bool:
        """
        Verify Instagram webhook signature for security
        
        Args:
            payload: Raw webhook payload
            signature: X-Hub-Signature-256 header value
            app_secret: Instagram app secret
            
        Returns:
            Boolean indicating if signature is valid
        """
        import hmac
        import hashlib
        
        try:
            expected_signature = hmac.new(
                app_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Remove 'sha256=' prefix from signature if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying Instagram webhook signature: {e}")
            return False

    def _attempt_token_refresh(self):
        """
        Attempt to refresh the current access token
        Returns True if refresh was successful, False otherwise
        """
        try:
            # Find the channel with this access token
            channel = InstagramChannel.objects.filter(access_token=self.access_token).first()
            if not channel:
                logger.error("Could not find Instagram channel for token refresh")
                return False
            
            # Try to refresh the token using Facebook Graph API first
            new_token, expires_in = self._exchange_for_long_lived_token(self.access_token)
            
            if not new_token:
                # If Facebook API fails, try Instagram API
                new_token, expires_in = self._refresh_long_lived_instagram_token(self.access_token)
            
            if new_token:
                # Update the channel and this service instance
                self._update_channel_and_service_token(channel, new_token, expires_in)
                return True
            
            # Token refresh failed - likely expired beyond grace period
            logger.error("All token refresh methods failed")
            logger.warning(f"🔗 Instagram token for user {channel.user.email if channel.user else 'unknown'} needs manual reconnection")
            
            # Mark the channel as needing reconnection (if field exists)
            try:
                if hasattr(channel, 'needs_reconnection'):
                    channel.needs_reconnection = True
                    channel.save()
            except Exception as e:
                logger.debug(f"Could not mark channel for reconnection: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error during token refresh attempt: {e}")
            return False

    def _exchange_for_long_lived_token(self, short_lived_token):
        """Exchange short-lived token for long-lived token using Instagram Graph API"""
        try:
            url = 'https://graph.instagram.com/access_token'
            params = {
                'grant_type': 'ig_exchange_token',
                'client_secret': '071f08aea723183951494234746982e4',  # Could be moved to settings
                'access_token': short_lived_token
            }
            
            # ✅ Token exchange with automatic fallback proxy
            response = make_request_with_proxy('get', url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('access_token'), data.get('expires_in')
            else:
                try:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get('error', {}).get('message', 'Unknown error') if isinstance(error_data.get('error'), dict) else str(error_data.get('error', 'Unknown error'))
                    logger.warning(f"Facebook token exchange failed: {response.status_code} - {error_message}")
                except:
                    logger.warning(f"Facebook token exchange failed: {response.status_code}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error during Facebook token exchange: {e}")
            return None, None

    def _refresh_long_lived_instagram_token(self, current_token):
        """Refresh Instagram long-lived token"""
        try:
            url = "https://graph.instagram.com/refresh_access_token"
            params = {
                'grant_type': 'ig_refresh_token',
                'access_token': current_token
            }
            
            # ✅ Token refresh with automatic fallback proxy
            response = make_request_with_proxy('get', url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('access_token'), data.get('expires_in')
            else:
                try:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get('error', {}).get('message', 'Unknown error') if isinstance(error_data.get('error'), dict) else str(error_data.get('error', 'Unknown error'))
                    logger.warning(f"Instagram token refresh failed: {response.status_code} - {error_message}")
                except:
                    logger.warning(f"Instagram token refresh failed: {response.status_code}")
                return None, None
                
        except Exception as e:
            logger.error(f"Error during Instagram token refresh: {e}")
            return None, None

    def _update_channel_and_service_token(self, channel, new_token, expires_in):
        """Update both the channel in database and this service instance"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            # Update channel in database
            channel.access_token = new_token
            
            if expires_in:
                expiration_time = timezone.now() + timedelta(seconds=int(expires_in))
                channel.token_expires_at = expiration_time
                logger.info(f"Token refreshed for {channel.username}, expires at {expiration_time}")
            else:
                logger.info(f"Token refreshed for {channel.username}, expiration unknown")
            
            channel.save()
            
            # Update this service instance
            self.access_token = new_token
            
        except Exception as e:
            logger.error(f"Error updating channel and service token: {e}")
            raise 