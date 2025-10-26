"""
WebSocket consumers for accounts app
Handles real-time updates for wizard status and user profile changes
"""

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
import logging
from settings.models import AIPrompts, InstagramChannel, TelegramChannel

logger = logging.getLogger(__name__)


class WizardStatusConsumer(AsyncWebsocketConsumer):
    """
    Real-time wizard status updates consumer
    
    WebSocket URL: ws://domain/ws/wizard-status/
    
    Sends real-time updates when:
    - User profile changes (name, phone, business_type)
    - Manual prompt is updated
    - Instagram/Telegram channel is connected/disconnected
    
    Message Types:
    - 'wizard_status': Initial status or update
    - 'refresh': Client request for fresh status
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope.get('user')
        
        # Reject unauthenticated connections
        if not self.user or not self.user.is_authenticated:
            logger.warning("Unauthenticated WebSocket connection attempt to wizard-status")
            await self.close()
            return
        
        # Join user-specific group for targeted updates
        self.group_name = f'wizard_status_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        
        await self.accept()
        logger.info(f"User {self.user.id} connected to wizard-status WebSocket")
        
        # Send initial status immediately after connection
        await self.send_wizard_status()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"User {self.user.id} disconnected from wizard-status WebSocket")
    
    async def receive(self, text_data):
        """
        Handle incoming messages from client
        
        Expected message format:
        {
            "type": "refresh"  // Request fresh status
            "type": "ping"     // Keepalive ping
        }
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'refresh':
                logger.debug(f"Refresh requested by user {self.user.id}")
                await self.send_wizard_status()
            elif message_type == 'ping':
                # Respond to keepalive ping
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in wizard-status WebSocket")
            await self.send(text_data=json.dumps({
                'error': 'invalid_json'
            }))
    
    async def send_wizard_status(self):
        """
        Send current wizard status to client
        
        Response format:
        {
            "type": "wizard_status",
            "wizard_complete": boolean,
            "can_complete": boolean,
            "missing_fields": [],
            "details": {
                "first_name": boolean,
                "last_name": boolean,
                "phone_number": boolean,
                "business_type": boolean,
                "manual_prompt": boolean,
                "channel_connected": boolean,
                "instagram_connected": boolean,
                "telegram_connected": boolean
            },
            "timestamp": "ISO-8601 datetime"
        }
        """
        status = await self.get_wizard_status()
        await self.send(text_data=json.dumps(status))
    
    async def wizard_status_updated(self, event):
        """
        Called when wizard status changes (triggered by Django signals)
        Automatically sends updated status to client
        """
        logger.debug(f"Wizard status updated for user {self.user.id}")
        await self.send_wizard_status()
    
    @database_sync_to_async
    def get_wizard_status(self):
        """
        Get current wizard completion status
        Uses same logic as WizardCompleteAPIView for consistency
        
        Returns:
            dict: Wizard status with all required fields
        """
        from django.utils import timezone
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        # Refresh user from database to get latest values
        user = User.objects.get(id=self.user.id)
        missing_fields = []
        details = {
            'first_name': bool(user.first_name),
            'last_name': bool(user.last_name),
            'phone_number': bool(user.phone_number),
            'business_type': bool(user.business_type),
            'manual_prompt': False,
            'channel_connected': False,
        }
        
        # Check basic user fields
        if not user.first_name:
            missing_fields.append('first_name')
        if not user.last_name:
            missing_fields.append('last_name')
        if not user.phone_number:
            missing_fields.append('phone_number')
        if not user.business_type:
            missing_fields.append('business_type')
        
        # Check manual_prompt from AIPrompts
        try:
            ai_prompts = AIPrompts.objects.get(user=user)
            if ai_prompts.manual_prompt and ai_prompts.manual_prompt.strip():
                details['manual_prompt'] = True
            else:
                missing_fields.append('manual_prompt')
        except AIPrompts.DoesNotExist:
            missing_fields.append('manual_prompt')
        
        # Check if at least one channel (Instagram or Telegram) is connected
        instagram_connected = InstagramChannel.objects.filter(
            user=user, 
            is_connect=True
        ).exists()
        telegram_connected = TelegramChannel.objects.filter(
            user=user, 
            is_connect=True
        ).exists()
        
        if instagram_connected or telegram_connected:
            details['channel_connected'] = True
            details['instagram_connected'] = instagram_connected
            details['telegram_connected'] = telegram_connected
        else:
            missing_fields.append('channel_connected')
            details['instagram_connected'] = False
            details['telegram_connected'] = False
        
        is_complete = len(missing_fields) == 0
        
        return {
            'type': 'wizard_status',
            'wizard_complete': is_complete,
            'can_complete': is_complete,
            'missing_fields': missing_fields,
            'details': details,
            'timestamp': timezone.now().isoformat()
        }

