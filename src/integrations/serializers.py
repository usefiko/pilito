from rest_framework import serializers
from integrations.models import (
    IntegrationToken, WooCommerceEventLog,
    WordPressContent, WordPressContentEventLog
)


class IntegrationTokenSerializer(serializers.ModelSerializer):
    """Serializer for IntegrationToken (safe - doesn't expose full token)"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    integration_type_display = serializers.CharField(
        source='get_integration_type_display',
        read_only=True
    )
    is_valid_status = serializers.SerializerMethodField()
    
    class Meta:
        model = IntegrationToken
        fields = [
            'id', 'user_id', 'user_email',
            'integration_type', 'integration_type_display',
            'name', 'token_preview',
            'is_active', 'is_valid_status',
            'last_used_at', 'usage_count',
            'allowed_ips',
            'created_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'token_preview', 'last_used_at', 'usage_count', 'created_at'
        ]
    
    def get_is_valid_status(self, obj):
        """Check if token is currently valid"""
        return obj.is_valid()


class IntegrationTokenCreateSerializer(serializers.Serializer):
    """Serializer for creating new integration tokens"""
    
    user_id = serializers.IntegerField(
        required=False,
        help_text="User ID (admin can create for other users)"
    )
    integration_type = serializers.ChoiceField(
        choices=IntegrationToken.INTEGRATION_TYPES,
        default='woocommerce'
    )
    name = serializers.CharField(
        max_length=100,
        help_text="Friendly name (e.g., 'Main Store')"
    )
    allowed_ips = serializers.ListField(
        child=serializers.IPAddressField(),
        required=False,
        allow_empty=True,
        default=list,
        help_text="List of allowed IPs (optional)"
    )
    expires_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Expiration date (optional)"
    )
    
    def validate_user_id(self, value):
        """Validate user exists"""
        if value:
            from accounts.models import User
            if not User.objects.filter(id=value).exists():
                raise serializers.ValidationError("User not found")
        return value


class WooCommerceEventLogSerializer(serializers.ModelSerializer):
    """Serializer for WooCommerce Event Logs"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    token_name = serializers.CharField(source='token.name', read_only=True, allow_null=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = WooCommerceEventLog
        fields = [
            'id', 'event_id', 'event_type', 'event_type_display',
            'user', 'user_email',
            'token', 'token_name',
            'woo_product_id',
            'payload',
            'processed_successfully', 'error_message', 'processing_time_ms',
            'source_ip', 'user_agent',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WooCommerceWebhookSerializer(serializers.Serializer):
    """Serializer for incoming WooCommerce webhook payloads"""
    
    event_id = serializers.CharField(required=True)
    event_type = serializers.ChoiceField(
        choices=WooCommerceEventLog.EVENT_TYPES,
        required=True
    )
    product = serializers.DictField(required=True)
    
    def validate_product(self, value):
        """Validate product data"""
        required_fields = ['id', 'name']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        return value


class WordPressContentSerializer(serializers.ModelSerializer):
    """Serializer for WordPress Content"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    
    class Meta:
        model = WordPressContent
        fields = [
            'id', 'user', 'user_email',
            'wp_post_id', 'content_type', 'content_type_display', 'post_type_slug',
            'title', 'content', 'excerpt', 'permalink',
            'author', 'categories', 'tags', 'featured_image',
            'is_published', 'modified_date',
            'content_hash', 'last_synced_at',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'content_hash', 'last_synced_at', 'created_at', 'updated_at']


class WordPressContentWebhookSerializer(serializers.Serializer):
    """Serializer for incoming WordPress content webhook"""
    
    event_id = serializers.CharField(required=True)
    event_type = serializers.ChoiceField(
        choices=WordPressContentEventLog.EVENT_TYPES,
        required=True
    )
    content = serializers.DictField(required=True)
    
    def validate_content(self, value):
        """Validate content data"""
        required_fields = ['id', 'title', 'post_type']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        return value

