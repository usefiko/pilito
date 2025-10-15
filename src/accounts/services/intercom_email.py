"""
Intercom Email Service

Send emails to users via Intercom's messaging API.
Supports both single emails and bulk email campaigns.
"""

import requests
import logging
from typing import Dict, Optional, Any, List
from django.conf import settings

logger = logging.getLogger(__name__)


class IntercomEmailService:
    """
    Service for sending emails via Intercom.
    
    Uses Intercom Messages API to send emails to contacts.
    Documentation: https://developers.intercom.com/docs/references/rest-api/api-intercom-io/messages/
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
    def send_email_to_user(
        user_id: int,
        subject: str,
        body: str,
        from_admin_id: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send an email to a specific user via Intercom.
        
        Args:
            user_id: Fiko user ID (external_id in Intercom)
            subject: Email subject line
            body: Email body (HTML supported)
            from_admin_id: Optional admin ID to send from
            template_id: Optional Intercom template ID
            
        Returns:
            Message object if successful, None otherwise
        """
        url = f"{IntercomEmailService.BASE_URL}/messages"
        
        message_data = {
            "message_type": "email",
            "subject": subject,
            "body": body,
            "from": {
                "type": "admin",
                "id": from_admin_id if from_admin_id else None
            },
            "to": {
                "type": "user",
                "id": str(user_id)
            }
        }
        
        if template_id:
            message_data["template"] = template_id
        
        # Remove None values
        message_data = {k: v for k, v in message_data.items() if v is not None}
        
        try:
            response = requests.post(
                url,
                json=message_data,
                headers=IntercomEmailService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            message = response.json()
            logger.info(f"✅ Sent email to user {user_id}: {subject}")
            
            return message
            
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"❌ HTTP error sending email to user {user_id}: "
                f"{e.response.status_code} - {e.response.text}"
            )
            return None
            
        except Exception as e:
            logger.error(f"❌ Error sending email to user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def send_email_to_contact(
        email: str,
        subject: str,
        body: str,
        from_admin_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send an email to a contact by email address.
        
        Args:
            email: Contact's email address
            subject: Email subject line
            body: Email body (HTML supported)
            from_admin_id: Optional admin ID to send from
            
        Returns:
            Message object if successful, None otherwise
        """
        url = f"{IntercomEmailService.BASE_URL}/messages"
        
        message_data = {
            "message_type": "email",
            "subject": subject,
            "body": body,
            "from": {
                "type": "admin",
                "id": from_admin_id if from_admin_id else None
            },
            "to": {
                "type": "contact",
                "email": email
            }
        }
        
        # Remove None values
        message_data = {k: v for k, v in message_data.items() if v is not None}
        
        try:
            response = requests.post(
                url,
                json=message_data,
                headers=IntercomEmailService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            message = response.json()
            logger.info(f"✅ Sent email to {email}: {subject}")
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error sending email to {email}: {str(e)}")
            return None
    
    @staticmethod
    def send_bulk_email(
        user_ids: List[int],
        subject: str,
        body: str,
        from_admin_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Send emails to multiple users (batch operation).
        
        Args:
            user_ids: List of Fiko user IDs
            subject: Email subject line
            body: Email body (HTML supported)
            from_admin_id: Optional admin ID to send from
            
        Returns:
            Dictionary with stats (success, failed counts)
        """
        stats = {
            'total': len(user_ids),
            'success': 0,
            'failed': 0
        }
        
        logger.info(f"📧 Starting bulk email send to {stats['total']} users...")
        
        for user_id in user_ids:
            try:
                result = IntercomEmailService.send_email_to_user(
                    user_id=user_id,
                    subject=subject,
                    body=body,
                    from_admin_id=from_admin_id
                )
                
                if result:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error sending email to user {user_id}: {str(e)}")
                stats['failed'] += 1
        
        logger.info(
            f"✅ Bulk email send completed: {stats['success']} success, "
            f"{stats['failed']} failed out of {stats['total']} total"
        )
        
        return stats
    
    @staticmethod
    def send_in_app_message(
        user_id: int,
        body: str,
        from_admin_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send an in-app message (shows in Messenger) to a user.
        
        Args:
            user_id: Fiko user ID
            body: Message body
            from_admin_id: Optional admin ID to send from
            
        Returns:
            Message object if successful, None otherwise
        """
        url = f"{IntercomEmailService.BASE_URL}/messages"
        
        message_data = {
            "message_type": "inapp",
            "body": body,
            "from": {
                "type": "admin",
                "id": from_admin_id if from_admin_id else None
            },
            "to": {
                "type": "user",
                "id": str(user_id)
            }
        }
        
        # Remove None values
        message_data = {k: v for k, v in message_data.items() if v is not None}
        
        try:
            response = requests.post(
                url,
                json=message_data,
                headers=IntercomEmailService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            message = response.json()
            logger.info(f"✅ Sent in-app message to user {user_id}")
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error sending in-app message to user {user_id}: {str(e)}")
            return None

