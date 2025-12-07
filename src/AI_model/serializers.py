from rest_framework import serializers
from .models import AIGlobalConfig, AIUsageTracking, AIUsageLog

class AIGlobalConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for global AI configuration
    """
    api_configured = serializers.SerializerMethodField()
    
    class Meta:
        model = AIGlobalConfig
        fields = [
            'id', 'model_name', 'temperature', 'max_tokens',
            'auto_response_enabled', 'response_delay_seconds', 'business_hours_only',
            'business_start_time', 'business_end_time', 'timezone', 'created_at', 'updated_at',
            'api_configured'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'api_configured']
    
    def get_api_configured(self, obj):
        """Check if Gemini API key is configured in service"""
        from AI_model.services.gemini_service import GeminiChatService
        try:
            # Create a dummy service to check configuration
            # We can't pass a specific user here, so we'll just check the API key
            from AI_model.services.gemini_service import gemini_api_key
            return bool(gemini_api_key and gemini_api_key != "YOUR_ACTUAL_API_KEY_HERE")
        except Exception:
            return False


class AIUsageLogSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed AI usage logs
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    section_display = serializers.CharField(source='get_section_display', read_only=True)
    
    class Meta:
        model = AIUsageLog
        fields = [
            'id', 'user', 'user_username', 'user_email', 'section', 'section_display',
            'prompt_tokens', 'completion_tokens', 'total_tokens', 
            'response_time_ms', 'success', 'model_name', 'error_message',
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'user_username', 'user_email', 'section_display', 'created_at']


class AIUsageLogCreateSerializer(serializers.Serializer):
    """
    Serializer for creating AI usage logs via API
    """
    section = serializers.ChoiceField(
        choices=AIUsageLog.SECTION_CHOICES,
        help_text="Section/feature that used AI"
    )
    prompt_tokens = serializers.IntegerField(
        min_value=0, 
        default=0,
        help_text="Number of input tokens"
    )
    completion_tokens = serializers.IntegerField(
        min_value=0, 
        default=0,
        help_text="Number of output tokens"
    )
    response_time_ms = serializers.IntegerField(
        min_value=0,
        default=0,
        help_text="Response time in milliseconds"
    )
    success = serializers.BooleanField(
        default=True,
        help_text="Whether the request was successful"
    )
    model_name = serializers.CharField(
        max_length=100,
        default="gemini-flash-latest",
        required=False,
        help_text="AI model used"
    )
    error_message = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Error details if request failed"
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Additional context (conversation_id, message_id, etc.)"
    )


class AIUsageTrackingSerializer(serializers.ModelSerializer):
    """
    Serializer for AI usage tracking (daily aggregates)
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = AIUsageTracking
        fields = [
            'id', 'user', 'user_username', 'date', 'total_requests', 
            'total_prompt_tokens', 'total_completion_tokens', 'total_tokens',
            'total_response_time_ms', 'average_response_time_ms',
            'successful_requests', 'failed_requests', 'success_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_username', 'success_rate', 'created_at', 'updated_at'
        ]
    
    def get_success_rate(self, obj):
        """Calculate success rate percentage"""
        if obj.total_requests > 0:
            return round((obj.successful_requests / obj.total_requests) * 100, 2)
        return 0.0


# Request/Response serializers for API endpoints

class AskQuestionRequestSerializer(serializers.Serializer):
    """
    Serializer for ask question API request
    """
    question = serializers.CharField(max_length=2000, help_text="The question to ask the AI")
    conversation_id = serializers.CharField(required=False, help_text="Optional conversation ID for context")


class AskQuestionResponseSerializer(serializers.Serializer):
    """
    Serializer for ask question API response
    """
    success = serializers.BooleanField()
    response = serializers.CharField(allow_null=True)
    response_time_ms = serializers.IntegerField()
    message_id = serializers.IntegerField(required=False, help_text="ID of created message")
    metadata = serializers.DictField(required=False)
    error = serializers.CharField(required=False)


class ConversationStatusRequestSerializer(serializers.Serializer):
    """
    Serializer for conversation status update request
    """
    status = serializers.ChoiceField(
        choices=['active', 'support_active'],
        help_text="active = AI handles, support_active = Manual/Support handles"
    )


class ConversationStatusResponseSerializer(serializers.Serializer):
    """
    Serializer for conversation status response
    """
    conversation_id = serializers.CharField()
    status = serializers.CharField()
    ai_handling = serializers.BooleanField()
    user_default_handler = serializers.CharField(required=False)
    can_switch_to_ai = serializers.BooleanField(required=False)
    can_switch_to_manual = serializers.BooleanField(required=False)
    customer_name = serializers.CharField(required=False)
    source = serializers.CharField(required=False)
    created_at = serializers.DateTimeField(required=False)
    updated_at = serializers.DateTimeField(required=False)


class BulkConversationStatusRequestSerializer(serializers.Serializer):
    """
    Serializer for bulk conversation status update request
    """
    conversation_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of conversation IDs to update"
    )
    status = serializers.ChoiceField(
        choices=['active', 'support_active'],
        help_text="New status for all conversations"
    )


class UserDefaultHandlerRequestSerializer(serializers.Serializer):
    """
    Serializer for user default handler update request
    """
    default_reply_handler = serializers.ChoiceField(
        choices=['Manual', 'AI'],
        help_text="Default handler for new conversations"
    )


class UserDefaultHandlerResponseSerializer(serializers.Serializer):
    """
    Serializer for user default handler response
    """
    default_reply_handler = serializers.CharField()
    ai_configured = serializers.BooleanField()
    active_conversations_count = serializers.IntegerField()
    support_active_conversations_count = serializers.IntegerField()


class UsageStatsResponseSerializer(serializers.Serializer):
    """
    Serializer for usage statistics response
    """
    total_requests = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    total_prompt_tokens = serializers.IntegerField()
    total_completion_tokens = serializers.IntegerField()
    successful_requests = serializers.IntegerField()
    failed_requests = serializers.IntegerField()
    success_rate = serializers.FloatField()
    average_response_time_ms = serializers.FloatField()
    days_included = serializers.IntegerField()
    date_range = serializers.DictField()
    daily_breakdown = serializers.ListField(child=serializers.DictField(), required=False)


class GlobalUsageStatsResponseSerializer(serializers.Serializer):
    """
    Serializer for global usage statistics response
    """
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_requests = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    successful_requests = serializers.IntegerField()
    failed_requests = serializers.IntegerField()
    success_rate = serializers.FloatField()
    days_included = serializers.IntegerField()
    date_range = serializers.DictField()
    top_users = serializers.ListField(child=serializers.DictField(), required=False)


class AIConfigurationStatusSerializer(serializers.Serializer):
    """
    Serializer for AI configuration status
    """
    ai_configured = serializers.BooleanField()
    global_enabled = serializers.BooleanField()
    api_key_configured = serializers.BooleanField()
    model_initialized = serializers.BooleanField()
    has_prompts = serializers.BooleanField()
    issues = serializers.ListField(child=serializers.CharField(), required=False)
    model_name = serializers.CharField(required=False)


class RAGStatusResponseSerializer(serializers.Serializer):
    """
    Serializer for RAG (Retrieval Augmented Generation) status API response
    """
    rag_enabled = serializers.BooleanField(help_text="Whether RAG system is enabled and operational")
    pgvector_available = serializers.BooleanField(help_text="Whether pgvector extension is installed")
    embedding_service_available = serializers.BooleanField(help_text="Whether OpenAI embedding service is configured")
    
    knowledge_base = serializers.DictField(help_text="Knowledge base statistics by chunk type")
    embedding_stats = serializers.DictField(help_text="Embedding generation statistics")
    
    intent_routing = serializers.DictField(help_text="Intent routing configuration status")
    session_memory = serializers.DictField(help_text="Session memory statistics")
    
    last_updated = serializers.DateTimeField(allow_null=True, help_text="Last knowledge base update timestamp")
    health_status = serializers.CharField(help_text="Overall RAG health: healthy, degraded, or unavailable")
    issues = serializers.ListField(child=serializers.CharField(), help_text="List of any detected issues")


class AIUsageLogStatsSerializer(serializers.Serializer):
    """
    Serializer for detailed AI usage log statistics
    """
    total_requests = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    total_prompt_tokens = serializers.IntegerField()
    total_completion_tokens = serializers.IntegerField()
    successful_requests = serializers.IntegerField()
    failed_requests = serializers.IntegerField()
    success_rate = serializers.FloatField()
    average_response_time_ms = serializers.FloatField()
    average_tokens_per_request = serializers.FloatField()
    days_included = serializers.IntegerField()
    date_range = serializers.DictField()
    by_section = serializers.DictField(help_text="Usage breakdown by section/feature")
    daily_breakdown = serializers.ListField(child=serializers.DictField(), required=False)
    recent_logs = serializers.ListField(child=serializers.DictField(), required=False)