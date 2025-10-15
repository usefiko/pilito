"""
AI Usage Tracking Service

This service provides a unified interface for tracking AI usage across the platform.
It automatically updates both:
- AIUsageLog: Detailed per-request tracking
- AIUsageTracking: Daily aggregated statistics

Usage:
    from AI_model.services.usage_tracker import track_ai_usage
    
    track_ai_usage(
        user=request.user,
        section='chat',
        prompt_tokens=150,
        completion_tokens=80,
        response_time_ms=1200,
        success=True
    )
"""

import logging
import traceback
from datetime import date
from django.db import transaction
from django.db.models import F
from AI_model.models import AIUsageLog, AIUsageTracking

# Create dedicated logger for AI usage tracking
logger = logging.getLogger('ai_usage_tracker')
logger.setLevel(logging.DEBUG)  # Capture all levels


def track_ai_usage(
    user,
    section,
    prompt_tokens=0,
    completion_tokens=0,
    response_time_ms=0,
    success=True,
    model_name="gemini-1.5-flash",
    error_message=None,
    metadata=None
):
    """
    Track AI usage in both detailed log and daily aggregates.
    
    This function:
    1. Creates a detailed AIUsageLog entry
    2. Updates (or creates) the daily AIUsageTracking aggregate
    
    Args:
        user: User instance who triggered the AI request
        section: Section/feature name (from AIUsageLog.SECTION_CHOICES)
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        response_time_ms: Response time in milliseconds
        success: Whether the request was successful
        model_name: AI model used (default: gemini-1.5-flash)
        error_message: Error details if request failed
        metadata: Additional context dictionary
    
    Returns:
        tuple: (usage_log, usage_tracking) - Both model instances
    
    Example:
        >>> from AI_model.services.usage_tracker import track_ai_usage
        >>> 
        >>> log, tracking = track_ai_usage(
        ...     user=request.user,
        ...     section='chat',
        ...     prompt_tokens=150,
        ...     completion_tokens=80,
        ...     response_time_ms=1200,
        ...     success=True,
        ...     metadata={'conversation_id': 'abc-123'}
        ... )
    """
    # Log entry point
    logger.debug(
        f"[TRACK_START] User: {user.username if user else 'None'}, "
        f"Section: {section}, Tokens: {prompt_tokens}+{completion_tokens}, "
        f"Success: {success}"
    )
    
    try:
        # Validate inputs
        if not user:
            logger.error("[TRACK_ERROR] User is None - cannot track usage")
            return None, None
        
        if not section:
            logger.error(f"[TRACK_ERROR] Section is empty for user {user.username}")
            return None, None
        
        # Validate section choice
        valid_sections = [choice[0] for choice in AIUsageLog.SECTION_CHOICES]
        if section not in valid_sections:
            logger.warning(
                f"[TRACK_WARNING] Invalid section '{section}' for user {user.username}. "
                f"Valid choices: {valid_sections}"
            )
        
        with transaction.atomic():
            logger.debug(f"[TRACK_TRANSACTION] Starting transaction for user {user.username}")
            
            # 1. Create detailed usage log
            logger.debug(f"[TRACK_LOG] Creating AIUsageLog entry...")
            usage_log = AIUsageLog.log_usage(
                user=user,
                section=section,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time_ms=response_time_ms,
                success=success,
                model_name=model_name,
                error_message=error_message,
                metadata=metadata or {}
            )
            logger.info(
                f"[TRACK_LOG_SUCCESS] AIUsageLog created - ID: {usage_log.id}, "
                f"User: {user.username}, Section: {section}, "
                f"Tokens: {usage_log.total_tokens}"
            )
            
            # 2. Update daily aggregate
            today = date.today()
            logger.debug(
                f"[TRACK_AGGREGATE] Getting/Creating AIUsageTracking for "
                f"user {user.username}, date {today}"
            )
            
            usage_tracking, created = AIUsageTracking.objects.get_or_create(
                user=user,
                date=today,
                defaults={
                    'total_requests': 0,
                    'total_prompt_tokens': 0,
                    'total_completion_tokens': 0,
                    'total_tokens': 0,
                    'total_response_time_ms': 0,
                    'average_response_time_ms': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                }
            )
            
            if created:
                logger.info(
                    f"[TRACK_AGGREGATE_NEW] Created new AIUsageTracking for "
                    f"user {user.username}, date {today}"
                )
            else:
                logger.debug(
                    f"[TRACK_AGGREGATE_EXISTS] Found existing AIUsageTracking - "
                    f"Requests: {usage_tracking.total_requests}, "
                    f"Tokens: {usage_tracking.total_tokens}"
                )
            
            # Update the daily aggregate using the built-in method
            logger.debug(f"[TRACK_AGGREGATE] Updating stats...")
            usage_tracking.update_stats(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time_ms=response_time_ms,
                success=success
            )
            
            logger.info(
                f"[TRACK_AGGREGATE_SUCCESS] AIUsageTracking updated - "
                f"User: {user.username}, Date: {today}, "
                f"Total Requests: {usage_tracking.total_requests}, "
                f"Total Tokens: {usage_tracking.total_tokens}, "
                f"Success Rate: {usage_tracking.successful_requests}/{usage_tracking.total_requests}"
            )
            
            # Final success log
            logger.info(
                f"[TRACK_COMPLETE] ✅ Successfully tracked AI usage - "
                f"User: {user.username}, Section: {section}, "
                f"Tokens: {prompt_tokens + completion_tokens}, "
                f"Status: {'SUCCESS' if success else 'FAILED'}"
            )
            
            return usage_log, usage_tracking
            
    except Exception as e:
        logger.error(
            f"[TRACK_EXCEPTION] ❌ Error tracking AI usage for user {user.username if user else 'None'}: "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(f"[TRACK_TRACEBACK] {traceback.format_exc()}")
        # Don't raise - tracking should never break the main flow
        return None, None


def track_ai_usage_safe(
    user,
    section,
    prompt_tokens=0,
    completion_tokens=0,
    response_time_ms=0,
    success=True,
    model_name="gemini-1.5-flash",
    error_message=None,
    metadata=None
):
    """
    Safe version of track_ai_usage that never raises exceptions.
    
    Use this version in production code where tracking failures
    should not affect the main application flow.
    
    Args:
        Same as track_ai_usage
    
    Returns:
        tuple: (usage_log, usage_tracking) or (None, None) if tracking fails
    """
    try:
        return track_ai_usage(
            user=user,
            section=section,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            response_time_ms=response_time_ms,
            success=success,
            model_name=model_name,
            error_message=error_message,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Failed to track AI usage (safe mode): {str(e)}")
        return None, None


class AIUsageTracker:
    """
    Context manager for tracking AI usage with automatic timing.
    
    Usage:
        with AIUsageTracker(user, 'chat') as tracker:
            response = ai_service.generate(prompt)
            tracker.set_tokens(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )
            tracker.set_metadata({'conversation_id': conv_id})
    """
    
    def __init__(self, user, section, model_name="gemini-1.5-flash"):
        self.user = user
        self.section = section
        self.model_name = model_name
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.metadata = {}
        self.error_message = None
        self.success = True
        self.start_time = None
        self.response_time_ms = 0
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        
        # Calculate response time
        if self.start_time:
            self.response_time_ms = int((time.time() - self.start_time) * 1000)
        
        # Check if there was an exception
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)
        
        # Track the usage
        track_ai_usage_safe(
            user=self.user,
            section=self.section,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            response_time_ms=self.response_time_ms,
            success=self.success,
            model_name=self.model_name,
            error_message=self.error_message,
            metadata=self.metadata
        )
        
        # Don't suppress exceptions
        return False
    
    def set_tokens(self, prompt_tokens=0, completion_tokens=0):
        """Set token counts"""
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
    
    def set_metadata(self, metadata):
        """Set additional metadata"""
        self.metadata = metadata or {}
    
    def mark_success(self):
        """Explicitly mark as successful"""
        self.success = True
        self.error_message = None
    
    def mark_failure(self, error_message):
        """Explicitly mark as failed"""
        self.success = False
        self.error_message = error_message


# Convenience function for backward compatibility
def log_ai_usage(*args, **kwargs):
    """
    Alias for track_ai_usage_safe for backward compatibility.
    """
    return track_ai_usage_safe(*args, **kwargs)

