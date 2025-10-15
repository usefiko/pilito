import requests
from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """Service for handling Google OAuth operations"""
    
    GOOGLE_ID_TOKEN_INFO_URL = 'https://www.googleapis.com/oauth2/v3/tokeninfo'
    GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
    
    @classmethod
    def verify_google_token(cls, id_token_string: str) -> dict:
        """
        Verify Google ID token and return user information
        
        Args:
            id_token_string: The Google ID token to verify
            
        Returns:
            dict: User information from Google
            
        Raises:
            serializers.ValidationError: If token is invalid
        """
        try:
            # Verify the token signature
            id_info = id_token.verify_oauth2_token(
                id_token_string, 
                google_requests.Request(), 
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            
            # Verify the issuer
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise serializers.ValidationError('Invalid token issuer')
            
            # Extract user information
            user_data = {
                'google_id': id_info.get('sub'),
                'email': id_info.get('email'),
                'first_name': id_info.get('given_name', ''),
                'last_name': id_info.get('family_name', ''),
                'google_avatar_url': id_info.get('picture', ''),
                'email_verified': id_info.get('email_verified', False)
            }
            
            # Validate required fields
            if not user_data['google_id'] or not user_data['email']:
                raise serializers.ValidationError('Missing required user information')
            
            if not user_data['email_verified']:
                raise serializers.ValidationError('Email not verified by Google')
            
            return user_data
            
        except ValueError as e:
            logger.error(f"Google token verification failed: {e}")
            raise serializers.ValidationError('Invalid Google token')
        except Exception as e:
            logger.error(f"Unexpected error during Google token verification: {e}")
            raise serializers.ValidationError('Token verification failed')
    
    @classmethod
    def get_user_info_by_access_token(cls, access_token: str) -> dict:
        """
        Get user information using Google access token
        
        Args:
            access_token: Google access token
            
        Returns:
            dict: User information from Google
            
        Raises:
            serializers.ValidationError: If request fails
        """
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(cls.GOOGLE_USER_INFO_URL, headers=headers)
            
            if response.status_code != 200:
                raise serializers.ValidationError('Failed to fetch user info from Google')
            
            user_info = response.json()
            
            user_data = {
                'google_id': user_info.get('id'),
                'email': user_info.get('email'),
                'first_name': user_info.get('given_name', ''),
                'last_name': user_info.get('family_name', ''),
                'google_avatar_url': user_info.get('picture', ''),
                'email_verified': user_info.get('verified_email', False)
            }
            
            if not user_data['google_id'] or not user_data['email']:
                raise serializers.ValidationError('Missing required user information')
            
            if not user_data['email_verified']:
                raise serializers.ValidationError('Email not verified by Google')
            
            return user_data
            
        except requests.RequestException as e:
            logger.error(f"Google API request failed: {e}")
            raise serializers.ValidationError('Failed to communicate with Google')
        except Exception as e:
            logger.error(f"Unexpected error getting user info: {e}")
            raise serializers.ValidationError('Failed to get user information')
    
    @classmethod
    def generate_auth_url(cls, state: str = None) -> str:
        """
        Generate Google OAuth authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            str: Authorization URL
        """
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_OAUTH2_REDIRECT_URI,
            'scope': 'openid email profile',
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'select_account'
        }
        
        if state:
            params['state'] = state
        
        from urllib.parse import urlencode
        param_string = urlencode(params)
        return f"{base_url}?{param_string}"
    
    @classmethod
    def exchange_code_for_tokens(cls, code: str) -> dict:
        """
        Exchange authorization code for access and ID tokens
        
        Args:
            code: Authorization code from Google
            
        Returns:
            dict: Tokens and user info
            
        Raises:
            serializers.ValidationError: If exchange fails
        """
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.GOOGLE_OAUTH2_REDIRECT_URI,
        }
        
        try:
            # Log the token exchange attempt for debugging
            logger.info(f"Google OAuth - Attempting token exchange")
            logger.info(f"Google OAuth - Token URL: {token_url}")
            logger.info(f"Google OAuth - Client ID: {data['client_id']}")
            logger.info(f"Google OAuth - Redirect URI: {data['redirect_uri']}")
            logger.info(f"Google OAuth - Code: {code[:10]}...")
            
            response = requests.post(token_url, data=data)
            logger.info(f"Google OAuth - Token exchange response status: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.json() if response.content else {}
                logger.error(f"Google OAuth - Token exchange failed: {error_detail}")
                error_msg = error_detail.get('error_description', 'Failed to exchange authorization code')
                raise serializers.ValidationError(f'Token exchange failed: {error_msg}')
            
            token_data = response.json()
            logger.info("Google OAuth - Token exchange successful")
            
            # Verify and extract user data from ID token
            id_token_string = token_data.get('id_token')
            if not id_token_string:
                raise serializers.ValidationError('No ID token received from Google')
            
            user_data = cls.verify_google_token(id_token_string)
            
            return {
                'user_data': user_data,
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'id_token': id_token_string
            }
            
        except requests.RequestException as e:
            logger.error(f"Token exchange request failed: {e}")
            raise serializers.ValidationError('Failed to communicate with Google')
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}")
            raise serializers.ValidationError('Token exchange failed')
