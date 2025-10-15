import requests
import logging
from typing import Optional, Dict, Any
from io import BytesIO
from django.core.files.base import ContentFile
from settings.models import TelegramChannel
from message.models import Message, Conversation, Customer

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending messages to Telegram bot API"""
    
    BASE_URL = "https://api.telegram.org/bot{token}"
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = self.BASE_URL.format(token=bot_token)
    
    def send_message(self, chat_id: str, text: str, parse_mode: str = 'HTML') -> Dict[str, Any]:
        """
        Send a text message to a specific chat
        
        Args:
            chat_id: Telegram chat ID
            text: Message text to send
            parse_mode: Message parse mode (HTML, Markdown, etc.)
            
        Returns:
            Dict containing API response
        """
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                logger.info(f"Message sent successfully to chat {chat_id}")
                return {
                    'success': True,
                    'message_id': result.get('result', {}).get('message_id'),
                    'data': result
                }
            else:
                logger.error(f"Telegram API error: {result.get('description')}")
                return {
                    'success': False,
                    'error': result.get('description', 'Unknown error')
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout sending message to chat {chat_id}")
            return {'success': False, 'error': 'Request timeout'}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error sending message to chat {chat_id}: {e}")
            return {'success': False, 'error': str(e)}
            
        except Exception as e:
            logger.error(f"Unexpected error sending message to chat {chat_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_message_to_customer(self, customer: Customer, message_text: str) -> Dict[str, Any]:
        """
        Send message to a customer via their Telegram ID
        
        Args:
            customer: Customer instance with Telegram source
            message_text: Text to send
            
        Returns:
            Dict containing send result
        """
        if customer.source != 'telegram':
            return {'success': False, 'error': 'Customer is not from Telegram'}
        
        if not customer.source_id:
            return {'success': False, 'error': 'Customer has no Telegram ID'}
        
        return self.send_message(customer.source_id, message_text)
    
    def get_user_profile_photos(self, user_id: str, limit: int = 1) -> Dict[str, Any]:
        """
        Get user profile photos from Telegram API
        
        Args:
            user_id: Telegram user ID
            limit: Number of photos to fetch (default 1 for latest)
            
        Returns:
            Dict containing profile photos data or error
        """
        url = f"{self.base_url}/getUserProfilePhotos"
        
        params = {
            'user_id': user_id,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('ok'):
                photos_data = result.get('result', {})
                total_count = photos_data.get('total_count', 0)
                photos = photos_data.get('photos', [])
                
                if total_count > 0 and photos:
                    # Get the largest size of the first (latest) photo
                    latest_photo = photos[0]  # Array of photo sizes
                    largest_photo = max(latest_photo, key=lambda p: p.get('file_size', 0))
                    
                    logger.info(f"✅ Found profile photo for user {user_id}: {largest_photo['file_id']}")
                    return {
                        'success': True,
                        'has_photo': True,
                        'photo_data': largest_photo,
                        'total_count': total_count
                    }
                else:
                    logger.info(f"ℹ️ No profile photos found for user {user_id}")
                    return {
                        'success': True,
                        'has_photo': False,
                        'total_count': 0
                    }
            else:
                error_msg = result.get('description', 'Unknown error')
                logger.error(f"❌ Telegram API error getting profile photos: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Error getting user profile photos for {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_file_download_url(self, file_id: str) -> Dict[str, Any]:
        """
        Get download URL for a Telegram file
        
        Args:
            file_id: Telegram file ID
            
        Returns:
            Dict containing file info and download URL
        """
        url = f"{self.base_url}/getFile"
        
        params = {'file_id': file_id}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('ok'):
                file_info = result.get('result', {})
                file_path = file_info.get('file_path')
                
                if file_path:
                    download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                    return {
                        'success': True,
                        'file_info': file_info,
                        'download_url': download_url
                    }
                else:
                    return {'success': False, 'error': 'No file path in response'}
            else:
                error_msg = result.get('description', 'Unknown error')
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"Error getting file download URL for {file_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def download_profile_picture(self, user_id: str) -> Optional[ContentFile]:
        """
        Download user's profile picture and return as ContentFile
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            ContentFile object or None if failed
        """
        try:
            # Get user profile photos
            photos_result = self.get_user_profile_photos(user_id)
            
            if not photos_result.get('success') or not photos_result.get('has_photo'):
                logger.info(f"📷 No profile photo available for Telegram user {user_id}")
                return None
            
            photo_data = photos_result['photo_data']
            file_id = photo_data['file_id']
            
            # Get file download URL
            file_result = self.get_file_download_url(file_id)
            
            if not file_result.get('success'):
                logger.error(f"❌ Failed to get download URL for file {file_id}")
                return None
            
            download_url = file_result['download_url']
            
            # Download the image
            logger.info(f"📸 Downloading Telegram profile picture from: {download_url}")
            response = requests.get(download_url, timeout=15)
            response.raise_for_status()
            
            if response.status_code == 200:
                # Create ContentFile from image data
                image_content = ContentFile(response.content)
                # Generate filename based on user_id and file extension
                file_extension = file_result['file_info'].get('file_path', '').split('.')[-1] or 'jpg'
                image_content.name = f"telegram_profile_{user_id}.{file_extension}"
                
                logger.info(f"✅ Successfully downloaded Telegram profile picture for user {user_id}")
                return image_content
            else:
                logger.error(f"❌ Failed to download profile picture: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading Telegram profile picture for {user_id}: {e}")
            return None
    
    @classmethod
    def get_service_for_conversation(cls, conversation: Conversation) -> Optional['TelegramService']:
        """
        Get TelegramService instance for a specific conversation
        
        Args:
            conversation: Conversation instance
            
        Returns:
            TelegramService instance or None if not found
        """
        try:
            if conversation.source != 'telegram':
                return None
                
            channel = TelegramChannel.objects.get(
                user=conversation.user,
                is_connect=True
            )
            return cls(channel.bot_token)
            
        except TelegramChannel.DoesNotExist:
            logger.error(f"No connected Telegram channel found for user {conversation.user.id}")
            return None
        except Exception as e:
            logger.error(f"Error getting Telegram service for conversation {conversation.id}: {e}")
            return None
    
    def get_bot_info(self) -> Dict[str, Any]:
        """Get information about the bot"""
        url = f"{self.base_url}/getMe"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('ok'):
                return {'success': True, 'data': result.get('result')}
            else:
                return {'success': False, 'error': result.get('description')}
                
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return {'success': False, 'error': str(e)} 