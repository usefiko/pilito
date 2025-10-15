"""
Intercom serializers for API request/response validation.

Provides serializers for Intercom JWT generation and validation endpoints.
"""

from rest_framework import serializers


class IntercomJWTRequestSerializer(serializers.Serializer):
    """
    Serializer for Intercom JWT generation request.
    """
    
    expiration_minutes = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=60,
        help_text="Token expiration time in minutes (1-60)"
    )
    
    custom_attributes = serializers.DictField(
        child=serializers.CharField(max_length=500),
        required=False,
        allow_empty=True,
        help_text="Additional user attributes to include in JWT"
    )


class IntercomJWTResponseSerializer(serializers.Serializer):
    """
    Serializer for Intercom JWT generation response.
    """
    
    intercom_user_jwt = serializers.CharField(
        help_text="JWT token for Intercom authentication"
    )
    
    expires_at = serializers.DateTimeField(
        help_text="Token expiration timestamp"
    )
    
    user_id = serializers.CharField(
        help_text="User identifier"
    )
    
    expires_in_seconds = serializers.IntegerField(
        help_text="Token validity duration in seconds"
    )


class IntercomConfigResponseSerializer(serializers.Serializer):
    """
    Serializer for Intercom configuration response.
    """
    
    app_id = serializers.CharField(
        help_text="Intercom App ID"
    )
    
    api_base = serializers.URLField(
        help_text="Intercom API base URL"
    )
    
    session_duration = serializers.IntegerField(
        help_text="Session duration in milliseconds"
    )


class IntercomUserHashResponseSerializer(serializers.Serializer):
    """
    Serializer for Intercom user hash response (legacy).
    """
    
    user_hash = serializers.CharField(
        help_text="HMAC hash for user verification"
    )
    
    user_id = serializers.CharField(
        help_text="User identifier"
    )


class IntercomValidateJWTRequestSerializer(serializers.Serializer):
    """
    Serializer for JWT validation request.
    """
    
    jwt_token = serializers.CharField(
        help_text="JWT token to validate"
    )


class IntercomValidateJWTResponseSerializer(serializers.Serializer):
    """
    Serializer for JWT validation response.
    """
    
    valid = serializers.BooleanField(
        help_text="Whether the JWT is valid"
    )
    
    payload = serializers.DictField(
        required=False,
        help_text="Decoded JWT payload"
    )
    
    user_id = serializers.CharField(
        required=False,
        help_text="User identifier from JWT"
    )
    
    error = serializers.CharField(
        required=False,
        help_text="Error message if validation failed"
    )
