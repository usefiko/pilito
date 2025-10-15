"""
Intercom JWT Service for secure user authentication with Intercom Messenger.

This service provides JWT token generation for Intercom authentication 
according to their security guidelines using HS256 algorithm.
"""

import jwt
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class IntercomJWTService:
    """
    Service class for generating and managing Intercom JWT tokens.
    
    According to Intercom documentation:
    - Uses HS256 (HMAC with SHA-256) algorithm
    - Requires user_id as primary identifier
    - Supports custom data attributes for secure transmission
    - Includes expiration for security
    """
    
    @staticmethod
    def generate_user_jwt(user, expiration_minutes: int = 5, custom_attributes: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate a JWT token for Intercom user authentication.
        
        Args:
            user: Django User instance
            expiration_minutes: Token expiration time in minutes (default: 5 minutes)
            custom_attributes: Additional user attributes to include in the JWT
            
        Returns:
            JWT token string or None if generation fails
            
        Raises:
            ValueError: If required settings are missing
        """
        
        # Validate required settings
        if not settings.INTERCOM_API_SECRET:
            raise ValueError("INTERCOM_API_SECRET is not configured in settings")
        
        if not settings.INTERCOM_APP_ID:
            raise ValueError("INTERCOM_APP_ID is not configured in settings")
        
        try:
            # Current timestamp
            now = timezone.now()
            expiry_time = now + timedelta(minutes=expiration_minutes)
            
            # Base payload with required fields
            payload = {
                "user_id": str(user.id),  # Required by Intercom - using user ID as primary identifier
                "email": user.email,      # Include email for user identification
                "iat": int(now.timestamp()),    # Issued at
                "exp": int(expiry_time.timestamp()),  # Expiration time
            }
            
            # Add user profile information
            if user.first_name:
                payload["name"] = f"{user.first_name} {user.last_name}".strip()
            
            if user.phone_number:
                payload["phone"] = user.phone_number
                
            if user.created_at:
                payload["created_at"] = int(user.created_at.timestamp())
                
            # Add business-related information
            if user.organisation:
                payload["company"] = {
                    "name": user.organisation
                }
                
            if user.business_type:
                payload["business_type"] = user.business_type
            
            # Add location information if available
            location_data = {}
            if user.country:
                location_data["country"] = user.country
            if user.state:
                location_data["state"] = user.state
            if user.zip_code:
                location_data["zip_code"] = user.zip_code
            if user.address:
                location_data["address"] = user.address
                
            if location_data:
                payload["location"] = location_data
            
            # Add user preferences
            if user.language:
                payload["language"] = user.language
            if user.time_zone:
                payload["time_zone"] = user.time_zone
            if user.currency:
                payload["currency"] = user.currency
                
            # Add custom attributes if provided
            if custom_attributes:
                for key, value in custom_attributes.items():
                    # Avoid overriding required fields
                    if key not in ["user_id", "iat", "exp"]:
                        payload[key] = value
            
            # Generate JWT token using HS256 algorithm
            token = jwt.encode(
                payload=payload,
                key=settings.INTERCOM_API_SECRET,
                algorithm="HS256"
            )
            
            logger.info(f"Generated Intercom JWT for user {user.id} with expiry {expiry_time}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate Intercom JWT for user {user.id}: {str(e)}")
            return None
    
    @staticmethod
    def generate_user_jwt_hs512(user, expiration_minutes: int = 5, custom_attributes: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate a JWT token for user authentication using HS512 algorithm.
        
        Args:
            user: Django User instance
            expiration_minutes: Token expiration time in minutes (default: 5 minutes)
            custom_attributes: Additional user attributes to include in the JWT
            
        Returns:
            JWT token string or None if generation fails
            
        Raises:
            ValueError: If required settings are missing
        """
        
        # Validate required settings
        if not settings.INTERCOM_API_SECRET:
            raise ValueError("INTERCOM_API_SECRET is not configured in settings")
        
        if not settings.INTERCOM_APP_ID:
            raise ValueError("INTERCOM_APP_ID is not configured in settings")
        
        try:
            # Current timestamp
            now = timezone.now()
            expiry_time = now + timedelta(minutes=expiration_minutes)
            
            # Base payload with required fields
            payload = {
                "user_id": str(user.id),  # Required by Intercom - using user ID as primary identifier
                "email": user.email,      # Include email for user identification
                "iat": int(now.timestamp()),    # Issued at
                "exp": int(expiry_time.timestamp()),  # Expiration time
            }
            
            # Add user profile information
            if user.first_name:
                payload["name"] = f"{user.first_name} {user.last_name}".strip()
            
            if user.phone_number:
                payload["phone"] = user.phone_number
                
            if user.created_at:
                payload["created_at"] = int(user.created_at.timestamp())
                
            # Add business-related information
            if user.organisation:
                payload["company"] = {
                    "name": user.organisation
                }
                
            if user.business_type:
                payload["business_type"] = user.business_type
            
            # Add location information if available
            location_data = {}
            if user.country:
                location_data["country"] = user.country
            if user.state:
                location_data["state"] = user.state
            if user.zip_code:
                location_data["zip_code"] = user.zip_code
            if user.address:
                location_data["address"] = user.address
                
            if location_data:
                payload["location"] = location_data
            
            # Add user preferences
            if user.language:
                payload["language"] = user.language
            if user.time_zone:
                payload["time_zone"] = user.time_zone
            if user.currency:
                payload["currency"] = user.currency
                
            # Add custom attributes if provided
            if custom_attributes:
                for key, value in custom_attributes.items():
                    # Avoid overriding required fields
                    if key not in ["user_id", "iat", "exp"]:
                        payload[key] = value
            
            # Generate JWT token using HS512 algorithm
            token = jwt.encode(
                payload=payload,
                key=settings.INTERCOM_API_SECRET,
                algorithm="HS512"
            )
            
            logger.info(f"Generated Intercom JWT (HS512) for user {user.id} with expiry {expiry_time}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate Intercom JWT (HS512) for user {user.id}: {str(e)}")
            return None
    
    @staticmethod
    def validate_user_jwt(token: str) -> Optional[Dict[str, Any]]:
        """
        Validate and decode an Intercom JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        
        if not settings.INTERCOM_API_SECRET:
            logger.error("INTERCOM_API_SECRET is not configured")
            return None
            
        try:
            payload = jwt.decode(
                jwt=token,
                key=settings.INTERCOM_API_SECRET,
                algorithms=["HS256"]
            )
            
            # Validate required fields
            if "user_id" not in payload:
                logger.warning("JWT payload missing required user_id field")
                return None
            
            logger.info(f"Successfully validated Intercom JWT for user {payload['user_id']}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Intercom JWT has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid Intercom JWT: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error validating Intercom JWT: {str(e)}")
            return None
    
    @staticmethod
    def get_intercom_config() -> Dict[str, Any]:
        """
        Get Intercom configuration for frontend integration.
        
        Returns:
            Dictionary with Intercom configuration
        """
        return {
            "app_id": settings.INTERCOM_APP_ID,
            "api_base": "https://api-iam.intercom.io",  # Standard Intercom API base
            "session_duration": getattr(settings, 'INTERCOM_SESSION_DURATION', 604800000),  # 7 days default
        }
    
    @staticmethod
    def generate_user_hash(user_id: str) -> Optional[str]:
        """
        Generate legacy user hash for backwards compatibility with Identity Verification.
        
        Note: This is the older method. JWT is recommended for new implementations.
        
        Args:
            user_id: User identifier
            
        Returns:
            HMAC hash string or None if generation fails
        """
        
        if not settings.INTERCOM_API_SECRET:
            logger.error("INTERCOM_API_SECRET is not configured")
            return None
            
        try:
            import hmac
            import hashlib
            
            user_hash = hmac.new(
                settings.INTERCOM_API_SECRET.encode('utf-8'),
                str(user_id).encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            logger.info(f"Generated Intercom user hash for user {user_id}")
            return user_hash
            
        except Exception as e:
            logger.error(f"Failed to generate Intercom user hash for user {user_id}: {str(e)}")
            return None
