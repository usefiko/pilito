import hashlib
from typing import Dict, Any
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import logging

logger = logging.getLogger(__name__)


class WordPressContentProcessor:
    """Process WordPress Pages/Posts webhook events"""
    
    def __init__(self, user=None, token=None):
        self.user = user
        self.token = token
    
    def process_event(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Process WordPress content event"""
        event_type = payload.get('event_type')
        
        if event_type in ['page.created', 'page.updated', 'post.created', 'post.updated']:
            return self._handle_content_upsert(payload)
        elif event_type in ['page.deleted', 'post.deleted']:
            return self._handle_content_delete(payload)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def _handle_content_upsert(self, payload: Dict) -> Dict:
        """Create or update WordPress content"""
        from integrations.models import WordPressContent
        
        content_data = payload['content']
        
        # Calculate content hash
        content_hash = self._calculate_content_hash(content_data)
        
        # Determine content_type
        post_type = content_data.get('post_type', 'page')
        if post_type == 'page':
            content_type = 'page'
        elif post_type == 'post':
            content_type = 'post'
        else:
            content_type = 'custom'
        
        # Check existing
        existing = WordPressContent.objects.filter(
            user=self.user,
            wp_post_id=content_data['id'],
            post_type_slug=post_type
        ).first()
        
        needs_embedding = True
        if existing and existing.content_hash == content_hash:
            needs_embedding = False
            logger.info(f"📝 Content unchanged, skipping re-embed")
        
        # Parse modified date
        modified_date = parse_datetime(content_data.get('modified_date', ''))
        if not modified_date:
            modified_date = timezone.now()
        
        # Prepare data
        content_defaults = {
            'content_type': content_type,
            'post_type_slug': post_type,
            'title': content_data['title'][:500],
            'content': content_data.get('content', '')[:50000],  # Max 50K chars
            'excerpt': content_data.get('excerpt', '')[:1000],
            'permalink': content_data.get('permalink', ''),
            'author': content_data.get('author', '')[:200],
            'categories': content_data.get('categories', []),
            'tags': content_data.get('tags', []),
            'featured_image': content_data.get('featured_image', ''),
            'is_published': content_data.get('is_published', True),
            'modified_date': modified_date,
            'content_hash': content_hash,
            'metadata': {
                'wp_post_id': content_data['id'],
                'word_count': content_data.get('word_count', 0),
                'needs_embedding': needs_embedding,
                'last_sync_at': str(timezone.now()),
            }
        }
        
        # Create or Update
        content, created = WordPressContent.objects.update_or_create(
            user=self.user,
            wp_post_id=content_data['id'],
            post_type_slug=post_type,
            defaults=content_defaults
        )
        
        # Signal will auto-chunk
        
        action = "created" if created else "updated"
        logger.info(f"✅ WordPress content {action}: {content.title}")
        
        return {
            'status': 'success',
            'action': action,
            'content_id': str(content.id),
            'needs_embedding': needs_embedding
        }
    
    def _handle_content_delete(self, payload: Dict) -> Dict:
        """Soft delete WordPress content"""
        from integrations.models import WordPressContent
        
        content_data = payload['content']
        post_type = content_data.get('post_type', 'page')
        
        # Soft delete
        deleted_count = WordPressContent.objects.filter(
            user=self.user,
            wp_post_id=content_data['id'],
            post_type_slug=post_type
        ).update(is_published=False)
        
        # Signal will cleanup chunks
        
        logger.info(f"🗑️ WordPress content deleted: Post {content_data['id']}")
        
        return {
            'status': 'success',
            'action': 'deleted',
            'deleted_count': deleted_count
        }
    
    def _calculate_content_hash(self, content_data: Dict) -> str:
        """Calculate hash from content fields"""
        critical_fields = [
            content_data.get('title', ''),
            content_data.get('content', ''),
            content_data.get('excerpt', ''),
        ]
        content = '|'.join(critical_fields)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

