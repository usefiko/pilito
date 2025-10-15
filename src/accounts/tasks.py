"""
Celery tasks for accounts app.

Handles asynchronous operations like syncing users to Intercom.
"""

from celery import shared_task
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(
    name='accounts.sync_user_to_intercom',
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True
)
def sync_user_to_intercom_async(self, user_id: int):
    """
    Asynchronously sync a user to Intercom.
    
    Args:
        user_id: ID of the user to sync
        
    Returns:
        Dictionary with sync result
    """
    from accounts.services.intercom_contact_sync import IntercomContactSyncService
    
    try:
        user = User.objects.get(id=user_id)
        
        logger.info(f"🔄 Starting async sync for user {user_id} ({user.email}) to Intercom...")
        
        result = IntercomContactSyncService.create_or_update_contact(user)
        
        if result:
            logger.info(f"✅ Successfully synced user {user_id} to Intercom")
            return {
                'success': True,
                'user_id': user_id,
                'intercom_id': result.get('id')
            }
        else:
            logger.error(f"❌ Failed to sync user {user_id} to Intercom")
            return {
                'success': False,
                'user_id': user_id,
                'error': 'Sync failed'
            }
            
    except User.DoesNotExist:
        logger.error(f"❌ User {user_id} not found for Intercom sync")
        return {
            'success': False,
            'user_id': user_id,
            'error': 'User not found'
        }
        
    except Exception as e:
        logger.error(f"❌ Error in async sync for user {user_id}: {str(e)}")
        # Reraise to trigger Celery retry
        raise


@shared_task(
    name='accounts.bulk_sync_users_to_intercom',
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 300}
)
def bulk_sync_users_to_intercom_async(self, batch_size: int = 50):
    """
    Asynchronously sync all users to Intercom in batches.
    
    Use this for initial setup or periodic full sync.
    
    Args:
        batch_size: Number of users to process in each batch
        
    Returns:
        Dictionary with sync statistics
    """
    from accounts.services.intercom_contact_sync import IntercomContactSyncService
    
    try:
        logger.info("🔄 Starting bulk sync of all users to Intercom...")
        
        stats = IntercomContactSyncService.sync_all_users(batch_size=batch_size)
        
        logger.info(
            f"✅ Bulk sync completed: {stats['success']} success, "
            f"{stats['failed']} failed, {stats['skipped']} skipped out of {stats['total']} total"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error in bulk sync: {str(e)}")
        raise


@shared_task(
    name='accounts.delete_intercom_contact',
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def delete_intercom_contact_async(self, user_id: int):
    """
    Asynchronously delete a contact from Intercom.
    
    Args:
        user_id: ID of the user whose Intercom contact should be deleted
        
    Returns:
        Dictionary with deletion result
    """
    from accounts.services.intercom_contact_sync import IntercomContactSyncService
    
    try:
        logger.info(f"🗑️ Starting async deletion of Intercom contact for user {user_id}...")
        
        success = IntercomContactSyncService.delete_contact(user_id)
        
        if success:
            logger.info(f"✅ Successfully deleted Intercom contact for user {user_id}")
            return {
                'success': True,
                'user_id': user_id
            }
        else:
            logger.error(f"❌ Failed to delete Intercom contact for user {user_id}")
            return {
                'success': False,
                'user_id': user_id,
                'error': 'Deletion failed'
            }
            
    except Exception as e:
        logger.error(f"❌ Error deleting Intercom contact for user {user_id}: {str(e)}")
        raise

