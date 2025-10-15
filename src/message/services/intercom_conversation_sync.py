"""
Intercom Conversation Sync Service

Handles syncing Fiko conversations/tickets with Intercom conversations.
Allows bidirectional sync of messages between Fiko and Intercom.
"""

import requests
import logging
from typing import Dict, Optional, Any, List
from django.conf import settings

logger = logging.getLogger(__name__)


class IntercomConversationSyncService:
    """
    Service for syncing conversations between Fiko and Intercom.
    
    Uses Intercom REST API v2 to create and manage conversations.
    Documentation: https://developers.intercom.com/docs/references/rest-api/api-intercom-io/conversations/
    """
    
    BASE_URL = settings.INTERCOM_API_BASE_URL
    API_VERSION = settings.INTERCOM_API_VERSION
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """Get headers for Intercom API requests."""
        if not settings.INTERCOM_ACCESS_TOKEN:
            raise ValueError("INTERCOM_ACCESS_TOKEN is not configured in settings")
        
        return {
            "Authorization": f"Bearer {settings.INTERCOM_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Intercom-Version": settings.INTERCOM_API_VERSION
        }
    
    @staticmethod
    def create_conversation(user_id: int, message_text: str, subject: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new conversation in Intercom from a Fiko user message.
        
        Args:
            user_id: Fiko user ID (used as external_id in Intercom)
            message_text: The message content
            subject: Optional subject for the conversation
            
        Returns:
            Intercom conversation object if successful, None otherwise
        """
        url = f"{IntercomConversationSyncService.BASE_URL}/conversations"
        
        conversation_data = {
            "from": {
                "type": "user",
                "id": str(user_id)  # Using Fiko user ID as external_id
            },
            "body": message_text
        }
        
        if subject:
            conversation_data["subject"] = subject
        
        try:
            response = requests.post(
                url,
                json=conversation_data,
                headers=IntercomConversationSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            conversation = response.json()
            logger.info(
                f"✅ Created Intercom conversation {conversation.get('id')} for user {user_id}"
            )
            
            return conversation
            
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"❌ HTTP error creating conversation for user {user_id}: "
                f"{e.response.status_code} - {e.response.text}"
            )
            return None
            
        except Exception as e:
            logger.error(f"❌ Error creating conversation for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def add_message_to_conversation(
        conversation_id: str,
        message_text: str,
        message_type: str = "comment",
        admin_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a message/reply to an existing conversation.
        
        Args:
            conversation_id: Intercom conversation ID
            message_text: The message content
            message_type: Type of message ("comment", "note", etc.)
            admin_id: Optional admin ID if message is from admin
            
        Returns:
            Updated conversation object if successful, None otherwise
        """
        url = f"{IntercomConversationSyncService.BASE_URL}/conversations/{conversation_id}/parts"
        
        message_data = {
            "message_type": message_type,
            "type": "comment",
            "body": message_text
        }
        
        if admin_id:
            message_data["admin_id"] = admin_id
        
        try:
            response = requests.post(
                url,
                json=message_data,
                headers=IntercomConversationSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Added message to Intercom conversation {conversation_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error adding message to conversation {conversation_id}: {str(e)}")
            return None
    
    @staticmethod
    def close_conversation(conversation_id: str, admin_id: Optional[str] = None) -> bool:
        """
        Close an Intercom conversation.
        
        Args:
            conversation_id: Intercom conversation ID
            admin_id: Optional admin ID who is closing the conversation
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{IntercomConversationSyncService.BASE_URL}/conversations/{conversation_id}/parts"
        
        close_data = {
            "message_type": "close",
            "type": "admin"
        }
        
        if admin_id:
            close_data["admin_id"] = admin_id
        
        try:
            response = requests.post(
                url,
                json=close_data,
                headers=IntercomConversationSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            logger.info(f"✅ Closed Intercom conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error closing conversation {conversation_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a conversation from Intercom.
        
        Args:
            conversation_id: Intercom conversation ID
            
        Returns:
            Conversation object if found, None otherwise
        """
        url = f"{IntercomConversationSyncService.BASE_URL}/conversations/{conversation_id}"
        
        try:
            response = requests.get(
                url,
                headers=IntercomConversationSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            conversation = response.json()
            logger.info(f"✅ Retrieved Intercom conversation {conversation_id}")
            
            return conversation
            
        except Exception as e:
            logger.error(f"❌ Error retrieving conversation {conversation_id}: {str(e)}")
            return None
    
    @staticmethod
    def search_conversations_by_user(user_id: int) -> List[Dict[str, Any]]:
        """
        Search for all conversations for a specific user.
        
        Args:
            user_id: Fiko user ID
            
        Returns:
            List of conversation objects
        """
        url = f"{IntercomConversationSyncService.BASE_URL}/conversations/search"
        
        search_query = {
            "query": {
                "field": "contact_ids",
                "operator": "=",
                "value": str(user_id)
            }
        }
        
        try:
            response = requests.post(
                url,
                json=search_query,
                headers=IntercomConversationSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            results = response.json()
            conversations = results.get('conversations', [])
            
            logger.info(f"✅ Found {len(conversations)} conversations for user {user_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Error searching conversations for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    def assign_conversation_to_admin(
        conversation_id: str,
        admin_id: str,
        assignee_type: str = "admin"
    ) -> bool:
        """
        Assign a conversation to a specific admin or team.
        
        Args:
            conversation_id: Intercom conversation ID
            admin_id: Admin or team ID
            assignee_type: "admin" or "team"
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{IntercomConversationSyncService.BASE_URL}/conversations/{conversation_id}/parts"
        
        assignment_data = {
            "message_type": "assignment",
            "type": "admin",
            "admin_id": admin_id,
            "assignee_id": admin_id
        }
        
        try:
            response = requests.post(
                url,
                json=assignment_data,
                headers=IntercomConversationSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            logger.info(f"✅ Assigned conversation {conversation_id} to {assignee_type} {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error assigning conversation {conversation_id}: {str(e)}")
            return False

