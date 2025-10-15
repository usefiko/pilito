"""
Intercom Contact Sync Service

This service handles syncing Fiko users to Intercom contacts using the REST API.
Provides functionality to create, update, and search contacts in Intercom.
"""

import requests
import logging
from typing import Dict, Optional, Any, List
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class IntercomContactSyncService:
    """
    Service for syncing Fiko users to Intercom contacts.
    
    Uses Intercom REST API v2 to create and update contacts.
    Documentation: https://developers.intercom.com/docs/references/rest-api/api-intercom-io/contacts/
    """
    
    BASE_URL = settings.INTERCOM_API_BASE_URL
    API_VERSION = settings.INTERCOM_API_VERSION
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """
        Get headers for Intercom API requests.
        
        Returns:
            Dictionary with authorization and content-type headers
        """
        if not settings.INTERCOM_ACCESS_TOKEN:
            raise ValueError("INTERCOM_ACCESS_TOKEN is not configured in settings")
        
        return {
            "Authorization": f"Bearer {settings.INTERCOM_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Intercom-Version": settings.INTERCOM_API_VERSION
        }
    
    @staticmethod
    def build_contact_data(user) -> Dict[str, Any]:
        """
        Build contact data from Fiko user object.
        
        Args:
            user: Django User instance
            
        Returns:
            Dictionary formatted for Intercom API
        """
        # Base required fields
        contact_data = {
            "external_id": str(user.id),  # Fiko user ID as external identifier
            "email": user.email,
        }
        
        # Optional user profile fields
        if user.first_name or user.last_name:
            contact_data["name"] = f"{user.first_name} {user.last_name}".strip()
        
        if user.phone_number:
            contact_data["phone"] = user.phone_number
        
        # Company info (use companies field)
        if user.organisation:
            contact_data["companies"] = [{
                "company_id": f"company_{user.id}",
                "name": user.organisation
            }]
        
        # Use signed_up_at timestamp (standard Intercom field)
        if user.created_at:
            contact_data["signed_up_at"] = int(user.created_at.timestamp())
        
        # Note: Custom attributes are NOT included to avoid validation errors
        # You can add them later in Intercom dashboard after defining them first
        
        return contact_data
    
    @staticmethod
    def create_or_update_contact(user) -> Optional[Dict[str, Any]]:
        """
        Create or update a contact in Intercom.
        
        Uses external_id to prevent duplicates. If contact exists, it will be updated.
        
        Args:
            user: Django User instance
            
        Returns:
            Intercom contact object if successful, None otherwise
        """
        url = f"{IntercomContactSyncService.BASE_URL}/contacts"
        
        try:
            contact_data = IntercomContactSyncService.build_contact_data(user)
            
            response = requests.post(
                url,
                json=contact_data,
                headers=IntercomContactSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            intercom_contact = response.json()
            logger.info(
                f"✅ Successfully synced user {user.id} ({user.email}) to Intercom. "
                f"Intercom ID: {intercom_contact.get('id')}"
            )
            
            return intercom_contact
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                # Contact already exists, try to update
                logger.info(f"Contact exists for user {user.id}, attempting update...")
                return IntercomContactSyncService.update_contact_by_email(user)
            else:
                logger.error(
                    f"❌ HTTP error syncing user {user.id} to Intercom: "
                    f"{e.response.status_code} - {e.response.text}"
                )
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error syncing user {user.id} to Intercom: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Unexpected error syncing user {user.id} to Intercom: {str(e)}")
            return None
    
    @staticmethod
    def update_contact_by_email(user) -> Optional[Dict[str, Any]]:
        """
        Update existing contact by searching with email.
        
        Args:
            user: Django User instance
            
        Returns:
            Updated Intercom contact object if successful, None otherwise
        """
        try:
            # First, search for the contact
            contact = IntercomContactSyncService.search_contact_by_email(user.email)
            
            if not contact:
                logger.warning(f"Could not find contact for user {user.id} with email {user.email}")
                return None
            
            # Update the contact
            contact_id = contact.get('id')
            url = f"{IntercomContactSyncService.BASE_URL}/contacts/{contact_id}"
            
            contact_data = IntercomContactSyncService.build_contact_data(user)
            
            # Remove external_id for updates (it's immutable in Intercom)
            contact_data.pop('external_id', None)
            
            response = requests.put(
                url,
                json=contact_data,
                headers=IntercomContactSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            intercom_contact = response.json()
            logger.info(f"✅ Successfully updated Intercom contact {contact_id} for user {user.id}")
            
            return intercom_contact
            
        except Exception as e:
            logger.error(f"❌ Error updating contact for user {user.id}: {str(e)}")
            return None
    
    @staticmethod
    def search_contact_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Search for a contact in Intercom by email.
        
        Args:
            email: Email address to search for
            
        Returns:
            Intercom contact object if found, None otherwise
        """
        url = f"{IntercomContactSyncService.BASE_URL}/contacts/search"
        
        search_query = {
            "query": {
                "field": "email",
                "operator": "=",
                "value": email
            }
        }
        
        try:
            response = requests.post(
                url,
                json=search_query,
                headers=IntercomContactSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            results = response.json()
            contacts = results.get('data', [])
            
            if contacts:
                logger.info(f"✅ Found Intercom contact for email: {email}")
                return contacts[0]
            else:
                logger.info(f"No Intercom contact found for email: {email}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error searching for contact with email {email}: {str(e)}")
            return None
    
    @staticmethod
    def search_contact_by_external_id(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Search for a contact in Intercom by external_id (Fiko user ID).
        
        Args:
            user_id: Fiko user ID
            
        Returns:
            Intercom contact object if found, None otherwise
        """
        url = f"{IntercomContactSyncService.BASE_URL}/contacts/search"
        
        search_query = {
            "query": {
                "field": "external_id",
                "operator": "=",
                "value": str(user_id)
            }
        }
        
        try:
            response = requests.post(
                url,
                json=search_query,
                headers=IntercomContactSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            results = response.json()
            contacts = results.get('data', [])
            
            if contacts:
                logger.info(f"✅ Found Intercom contact for user ID: {user_id}")
                return contacts[0]
            else:
                logger.info(f"No Intercom contact found for user ID: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error searching for contact with user ID {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def delete_contact(user_id: int) -> bool:
        """
        Delete a contact from Intercom.
        
        Args:
            user_id: Fiko user ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, find the contact
            contact = IntercomContactSyncService.search_contact_by_external_id(user_id)
            
            if not contact:
                logger.warning(f"Cannot delete - contact not found for user ID: {user_id}")
                return False
            
            contact_id = contact.get('id')
            url = f"{IntercomContactSyncService.BASE_URL}/contacts/{contact_id}"
            
            response = requests.delete(
                url,
                headers=IntercomContactSyncService.get_headers(),
                timeout=10
            )
            
            response.raise_for_status()
            
            logger.info(f"✅ Successfully deleted Intercom contact for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting contact for user {user_id}: {str(e)}")
            return False
    
    @staticmethod
    def sync_all_users(batch_size: int = 50) -> Dict[str, int]:
        """
        Sync all Fiko users to Intercom (bulk operation).
        
        Use this for initial sync or periodic full sync.
        
        Args:
            batch_size: Number of users to process in each batch
            
        Returns:
            Dictionary with sync statistics
        """
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        users = User.objects.all()
        stats['total'] = users.count()
        
        logger.info(f"🔄 Starting bulk sync of {stats['total']} users to Intercom...")
        
        for user in users:
            try:
                # Skip users without email
                if not user.email:
                    stats['skipped'] += 1
                    continue
                
                result = IntercomContactSyncService.create_or_update_contact(user)
                
                if result:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error syncing user {user.id}: {str(e)}")
                stats['failed'] += 1
        
        logger.info(
            f"✅ Bulk sync completed: {stats['success']} success, "
            f"{stats['failed']} failed, {stats['skipped']} skipped"
        )
        
        return stats

