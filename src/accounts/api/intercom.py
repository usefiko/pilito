"""
Intercom API views for JWT token generation and configuration.

Provides endpoints for frontend to obtain Intercom JWT tokens and configuration
for secure Messenger integration.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.services.intercom import IntercomJWTService
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class IntercomJWTView(APIView):
    """
    Generate Intercom JWT tokens for authenticated user.
    
    This endpoint provides JWT tokens using both HS256 and HS512 algorithms
    that the frontend can use to securely authenticate users with Intercom Messenger.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate a new Intercom JWT token for the authenticated user.
        
        Request body (optional):
        {
            "expiration_minutes": 5,  // Token expiration in minutes (default: 5)
            "custom_attributes": {    // Additional user attributes
                "subscription_plan": "pro",
                "last_login": "2024-01-15"
            }
        }
        
        Response:
        {
            "intercom_user_jwt": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",  // HS256 algorithm
            "intercom_user_jwt_hs512": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9...",  // HS512 algorithm
            "expires_at": "2024-01-15T10:05:00Z",
            "user_id": "123",
            "expires_in_seconds": 300,
            "created_at": "2024-01-01T12:00:00Z"  // Optional: user registration date
        }
        """
        
        try:
            user = request.user
            
            # Get optional parameters from request
            expiration_minutes = request.data.get('expiration_minutes', 5)
            custom_attributes = request.data.get('custom_attributes', {})
            
            # Validate expiration_minutes
            if not isinstance(expiration_minutes, int) or expiration_minutes < 1 or expiration_minutes > 60:
                return Response({
                    'error': 'expiration_minutes must be an integer between 1 and 60'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate JWT tokens (both HS256 and HS512)
            jwt_token_hs256 = IntercomJWTService.generate_user_jwt(
                user=user,
                expiration_minutes=expiration_minutes,
                custom_attributes=custom_attributes
            )
            
            jwt_token_hs512 = IntercomJWTService.generate_user_jwt_hs512(
                user=user,
                expiration_minutes=expiration_minutes,
                custom_attributes=custom_attributes
            )
            
            if not jwt_token_hs256 or not jwt_token_hs512:
                logger.error(f"Failed to generate Intercom JWT tokens for user {user.id}")
                return Response({
                    'error': 'Failed to generate JWT tokens'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Calculate expiration time for frontend
            from datetime import datetime, timedelta
            from django.utils import timezone
            expires_at = timezone.now() + timedelta(minutes=expiration_minutes)
            
            # Prepare response data
            response_data = {
                'intercom_user_jwt': jwt_token_hs256,
                'intercom_user_jwt_hs512': jwt_token_hs512,
                'expires_at': expires_at.isoformat(),
                'user_id': str(user.id),
                'expires_in_seconds': expiration_minutes * 60
            }
            
            # Add created_at if available
            if user.created_at:
                response_data['created_at'] = user.created_at.isoformat()
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"Configuration error for user {request.user.id}: {str(e)}")
            return Response({
                'error': 'Intercom is not properly configured'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"Unexpected error generating Intercom JWT for user {request.user.id}: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IntercomConfigView(APIView):
    """
    Get Intercom configuration for frontend integration.
    
    Provides the necessary configuration data that the frontend needs
    to initialize Intercom Messenger.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get Intercom configuration.
        
        Response:
        {
            "app_id": "your_app_id",
            "api_base": "https://api-iam.intercom.io",
            "session_duration": 604800000
        }
        """
        
        try:
            config = IntercomJWTService.get_intercom_config()
            
            # Check if Intercom is properly configured
            if not config.get('app_id'):
                return Response({
                    'error': 'Intercom APP ID is not configured'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            return Response(config, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting Intercom config: {str(e)}")
            return Response({
                'error': 'Failed to get Intercom configuration'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IntercomUserHashView(APIView):
    """
    Generate legacy Intercom user hash for backwards compatibility.
    
    This is for legacy Identity Verification support. New implementations
    should use JWT tokens instead.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate a user hash for legacy Intercom Identity Verification.
        
        Response:
        {
            "user_hash": "a1b2c3d4e5f6...",
            "user_id": "123"
        }
        """
        
        try:
            user = request.user
            
            # Generate user hash
            user_hash = IntercomJWTService.generate_user_hash(str(user.id))
            
            if not user_hash:
                logger.error(f"Failed to generate Intercom user hash for user {user.id}")
                return Response({
                    'error': 'Failed to generate user hash'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'user_hash': user_hash,
                'user_id': str(user.id)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating Intercom user hash for user {request.user.id}: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IntercomValidateJWTView(APIView):
    """
    Validate an Intercom JWT token (for debugging purposes).
    
    This endpoint is primarily for debugging and testing JWT tokens.
    In production, validation happens on Intercom's side.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Validate an Intercom JWT token.
        
        Request body:
        {
            "jwt_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }
        
        Response:
        {
            "valid": true,
            "payload": {...},
            "user_id": "123"
        }
        """
        
        jwt_token = request.data.get('jwt_token')
        
        if not jwt_token:
            return Response({
                'error': 'jwt_token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Validate JWT token
            payload = IntercomJWTService.validate_user_jwt(jwt_token)
            
            if payload:
                return Response({
                    'valid': True,
                    'payload': payload,
                    'user_id': payload.get('user_id')
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'valid': False,
                    'error': 'Invalid or expired JWT token'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error validating Intercom JWT: {str(e)}")
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
