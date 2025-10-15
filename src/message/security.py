import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count
from message.models import Message, Conversation
from accounts.models import User
import json

logger = logging.getLogger(__name__)

class WebSocketSecurityManager:
    """
    Security manager for WebSocket connections and message monitoring
    """
    
    # Security thresholds
    MAX_MESSAGES_PER_MINUTE = 20
    MAX_CONNECTIONS_PER_USER = 5
    MAX_FAILED_AUTH_ATTEMPTS = 5
    BLACKLIST_DURATION_HOURS = 24
    
    @classmethod
    def log_connection_attempt(cls, user_id, ip_address, success=True):
        """Log WebSocket connection attempts for monitoring"""
        try:
            cache_key = f'ws_connection_log_{ip_address}'
            current_time = timezone.now()
            
            # Get existing log
            log_data = cache.get(cache_key, {
                'total_attempts': 0,
                'failed_attempts': 0,
                'successful_attempts': 0,
                'last_attempt': None,
                'user_ids': set()
            })
            
            # Update log
            log_data['total_attempts'] += 1
            log_data['last_attempt'] = current_time.isoformat()
            log_data['user_ids'].add(user_id) if user_id else None
            
            if success:
                log_data['successful_attempts'] += 1
                log_data['failed_attempts'] = 0  # Reset failed counter on success
            else:
                log_data['failed_attempts'] += 1
            
            # Store for 24 hours
            cache.set(cache_key, log_data, timeout=86400)
            
            # Check for suspicious activity
            if log_data['failed_attempts'] >= cls.MAX_FAILED_AUTH_ATTEMPTS:
                cls.handle_suspicious_activity(ip_address, 'too_many_failed_auth')
            
            logger.info(f"WebSocket connection logged: IP={ip_address}, User={user_id}, Success={success}")
            
        except Exception as e:
            logger.error(f"Error logging WebSocket connection: {e}")

    @classmethod
    def check_message_rate_limit(cls, user_id):
        """Check if user is sending messages too quickly"""
        try:
            cache_key = f'message_rate_limit_{user_id}'
            current_time = timezone.now()
            window_start = current_time - timedelta(minutes=1)
            
            # Get message timestamps in the last minute
            message_times = cache.get(cache_key, [])
            
            # Filter to last minute
            message_times = [
                datetime.fromisoformat(ts) for ts in message_times 
                if datetime.fromisoformat(ts) > window_start
            ]
            
            # Check limit
            if len(message_times) >= cls.MAX_MESSAGES_PER_MINUTE:
                logger.warning(f"Message rate limit exceeded for user {user_id}")
                return False
            
            # Add current timestamp
            message_times.append(current_time)
            cache.set(cache_key, [t.isoformat() for t in message_times], timeout=60)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking message rate limit: {e}")
            return True  # Allow on error

    @classmethod
    def detect_spam_content(cls, content, user_id=None):
        """Basic spam detection for message content"""
        try:
            # Simple spam indicators
            spam_indicators = [
                len(content) > 500,  # Very long messages
                content.count('http') > 3,  # Multiple URLs
                content.isupper() and len(content) > 20,  # All caps
                content.count('!') > 5,  # Too many exclamations
                len(set(content.replace(' ', ''))) < 5 and len(content) > 20,  # Repetitive
            ]
            
            spam_score = sum(spam_indicators)
            
            if spam_score >= 2:
                logger.warning(f"Potential spam detected from user {user_id}: score={spam_score}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting spam: {e}")
            return False

    @classmethod
    def handle_suspicious_activity(cls, ip_address, reason, user_id=None):
        """Handle suspicious WebSocket activity"""
        try:
            logger.warning(f"Suspicious activity detected: IP={ip_address}, Reason={reason}, User={user_id}")
            
            # Log to security events
            security_event = {
                'timestamp': timezone.now().isoformat(),
                'ip_address': ip_address,
                'user_id': user_id,
                'reason': reason,
                'action': 'logged'
            }
            
            # Store security event
            cache_key = f'security_events_{ip_address}'
            events = cache.get(cache_key, [])
            events.append(security_event)
            cache.set(cache_key, events[-10:], timeout=86400)  # Keep last 10 events
            
            # Auto-blacklist based on severity
            if reason in ['too_many_failed_auth', 'message_spam', 'rate_limit_abuse']:
                from message.middleware.websocket_auth import blacklist_ip
                blacklist_ip(ip_address, cls.BLACKLIST_DURATION_HOURS)
                security_event['action'] = 'blacklisted'
                logger.warning(f"IP {ip_address} automatically blacklisted for {reason}")
            
        except Exception as e:
            logger.error(f"Error handling suspicious activity: {e}")

    @classmethod
    def get_user_websocket_stats(cls, user_id, hours=24):
        """Get WebSocket usage statistics for a user"""
        try:
            cache_key = f'user_ws_stats_{user_id}'
            stats = cache.get(cache_key)
            
            if not stats:
                # Calculate stats from database and cache
                time_threshold = timezone.now() - timedelta(hours=hours)
                
                message_count = Message.objects.filter(
                    conversation__user_id=user_id,
                    created_at__gte=time_threshold,
                    type='support'
                ).count()
                
                conversation_count = Conversation.objects.filter(
                    user_id=user_id,
                    updated_at__gte=time_threshold
                ).count()
                
                stats = {
                    'messages_sent': message_count,
                    'active_conversations': conversation_count,
                    'period_hours': hours,
                    'calculated_at': timezone.now().isoformat()
                }
                
                cache.set(cache_key, stats, timeout=3600)  # Cache for 1 hour
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting WebSocket stats for user {user_id}: {e}")
            return {}

    @classmethod
    def validate_message_content(cls, content, user_id, conversation_id):
        """Comprehensive message validation"""
        try:
            # Basic validation
            if not content or not content.strip():
                return {'valid': False, 'reason': 'Empty content'}
            
            if len(content) > 1000:
                return {'valid': False, 'reason': 'Content too long'}
            
            # Rate limiting
            if not cls.check_message_rate_limit(user_id):
                return {'valid': False, 'reason': 'Rate limit exceeded'}
            
            # Spam detection
            if cls.detect_spam_content(content, user_id):
                return {'valid': False, 'reason': 'Potential spam detected'}
            
            # Check conversation access (basic)
            try:
                conversation = Conversation.objects.get(id=conversation_id, user_id=user_id)
            except Conversation.DoesNotExist:
                return {'valid': False, 'reason': 'Unauthorized conversation access'}
            
            return {'valid': True, 'reason': 'Content validated'}
            
        except Exception as e:
            logger.error(f"Error validating message content: {e}")
            return {'valid': False, 'reason': 'Validation error'}


class WebSocketMonitor:
    """
    Real-time monitoring for WebSocket connections and activities
    """
    
    @classmethod
    def get_active_connections(cls):
        """Get count of currently active WebSocket connections"""
        try:
            # This would require extending the consumer to track active connections
            # For now, return a placeholder implementation
            cache_key = 'active_websocket_connections'
            return cache.get(cache_key, 0)
        except Exception as e:
            logger.error(f"Error getting active connections: {e}")
            return 0

    @classmethod
    def get_security_summary(cls, hours=24):
        """Get security summary for the last N hours"""
        try:
            summary = {
                'timeframe_hours': hours,
                'timestamp': timezone.now().isoformat(),
                'connection_attempts': 0,
                'failed_authentications': 0,
                'blacklisted_ips': 0,
                'spam_messages_blocked': 0,
                'rate_limit_violations': 0
            }
            
            # This would be populated by scanning security logs
            # For now, return template structure
            
            return summary
        except Exception as e:
            logger.error(f"Error generating security summary: {e}")
            return {}

    @classmethod
    def get_user_activity_report(cls, user_id):
        """Get detailed activity report for a specific user"""
        try:
            report = {
                'user_id': user_id,
                'generated_at': timezone.now().isoformat(),
                'websocket_stats': WebSocketSecurityManager.get_user_websocket_stats(user_id),
                'recent_conversations': [],
                'security_events': []
            }
            
            # Get recent conversations
            recent_conversations = Conversation.objects.filter(
                user_id=user_id
            ).order_by('-updated_at')[:10]
            
            report['recent_conversations'] = [
                {
                    'id': conv.id,
                    'source': conv.source,
                    'status': conv.status,
                    'updated_at': conv.updated_at.isoformat()
                }
                for conv in recent_conversations
            ]
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating user activity report: {e}")
            return {} 