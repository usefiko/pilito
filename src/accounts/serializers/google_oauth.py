from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.services.google_oauth import GoogleOAuthService
from accounts.functions.jwt import login
from accounts.models.user import EmailConfirmationToken
from django.db import transaction
from django.utils.crypto import get_random_string
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import logging
import requests
import uuid
import os

User = get_user_model()
logger = logging.getLogger(__name__)


class GoogleProfilePictureService:
    """Service for handling Google profile picture downloads"""
    
    @staticmethod
    def download_and_save_profile_picture(user, google_avatar_url):
        """
        Download Google profile picture and save it as user's profile picture
        
        Args:
            user: User instance
            google_avatar_url: URL of the Google profile picture
            
        Returns:
            bool: True if successfully downloaded and saved, False otherwise
        """
        if not google_avatar_url:
            logger.info(f"No Google avatar URL provided for user {user.email}")
            return False
            
        try:
            # Check if user already has a custom profile picture (not default)
            if (user.profile_picture and 
                user.profile_picture.name != "user_img/default.png" and
                not user.profile_picture.name.startswith('user_img/google_')):
                logger.info(f"User {user.email} already has a custom profile picture, skipping Google avatar")
                return False
            
            # Download the image from Google
            logger.info(f"Downloading Google profile picture for user {user.email} from {google_avatar_url}")
            response = requests.get(google_avatar_url, timeout=10)
            response.raise_for_status()
            
            # Check if the response contains image data
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"Invalid content type for profile picture: {content_type}")
                return False
            
            # Generate unique filename
            file_extension = '.jpg'  # Default to jpg for Google profile pictures
            if 'image/png' in content_type:
                file_extension = '.png'
            elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
                file_extension = '.jpg'
            
            filename = f"user_img/google_{user.id}_{uuid.uuid4().hex[:8]}{file_extension}"
            
            # Save the image
            image_content = ContentFile(response.content)
            user.profile_picture.save(filename, image_content, save=False)
            user.save()
            
            logger.info(f"Successfully saved Google profile picture for user {user.email} as {filename}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to download Google profile picture for user {user.email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving Google profile picture for user {user.email}: {e}")
            return False


class GoogleOAuthLoginSerializer(serializers.Serializer):
    """Serializer for Google OAuth login using ID token"""
    
    id_token = serializers.CharField(
        required=True,
        help_text="Google ID token received from frontend"
    )
    
    def validate_id_token(self, value):
        """Validate the Google ID token"""
        try:
            user_data = GoogleOAuthService.verify_google_token(value)
            return user_data
        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.error(f"ID token validation error: {e}")
            raise serializers.ValidationError("Invalid Google ID token")
    
    def create(self, validated_data):
        """Create or login user with Google OAuth"""
        user_data = validated_data['id_token']
        
        try:
            with transaction.atomic():
                # Check if user exists by Google ID
                user = None
                try:
                    user = User.objects.get(google_id=user_data['google_id'])
                except User.DoesNotExist:
                    # Check if user exists by email
                    try:
                        user = User.objects.get(email=user_data['email'])
                        # Link existing account with Google
                        user.google_id = user_data['google_id']
                        user.is_google_user = True
                        user.google_avatar_url = user_data['google_avatar_url']
                        # Since Google verified the email, mark it as confirmed
                        user.email_confirmed = True
                        user.save()
                    except User.DoesNotExist:
                        # Create new user
                        user = self._create_google_user(user_data)
                
                # Update user info from Google if needed
                self._update_user_info(user, user_data)
                
                # Generate JWT tokens
                access_token, refresh_token = login(user)
                
                return {
                    'user': user,
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'message': 'Login successful'
                }
        
        except Exception as e:
            logger.error(f"Google OAuth login error: {e}")
            raise serializers.ValidationError("Login failed")
    
    def _create_google_user(self, user_data):
        """Create a new user from Google data"""
        # Generate unique username from email
        email_prefix = user_data['email'].split('@')[0]
        username = email_prefix
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{email_prefix}{counter}"
            counter += 1
        
        user = User.objects.create(
            email=user_data['email'],
            username=username,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            google_id=user_data['google_id'],
            is_google_user=True,
            google_avatar_url=user_data['google_avatar_url'],
            email_confirmed=True,  # Google has already verified the email
            # Set random password for Google users (they won't use it)
            password=get_random_string(32)
        )
        
        # Set password unusable since they use Google OAuth
        user.set_unusable_password()
        user.save()
        
        # Download and save Google profile picture
        GoogleProfilePictureService.download_and_save_profile_picture(
            user, user_data['google_avatar_url']
        )
        
        return user
    
    def _update_user_info(self, user, user_data):
        """Update user information from Google if needed"""
        updated = False
        
        # Update avatar URL if changed
        if user.google_avatar_url != user_data['google_avatar_url']:
            user.google_avatar_url = user_data['google_avatar_url']
            updated = True
            
            # Download and update profile picture if avatar URL changed
            GoogleProfilePictureService.download_and_save_profile_picture(
                user, user_data['google_avatar_url']
            )
        
        # Update name if empty
        if not user.first_name and user_data['first_name']:
            user.first_name = user_data['first_name']
            updated = True
        
        if not user.last_name and user_data['last_name']:
            user.last_name = user_data['last_name']
            updated = True
        
        if updated:
            user.save()


class GoogleOAuthCodeSerializer(serializers.Serializer):
    """Serializer for Google OAuth login using authorization code"""
    
    code = serializers.CharField(
        required=True,
        help_text="Authorization code received from Google"
    )
    state = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="State parameter for CSRF protection"
    )
    
    def validate_code(self, value):
        """Validate the authorization code and exchange for tokens"""
        try:
            token_data = GoogleOAuthService.exchange_code_for_tokens(value)
            return token_data
        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.error(f"Code validation error: {e}")
            raise serializers.ValidationError("Invalid authorization code")
    
    def create(self, validated_data):
        """Create or login user using authorization code"""
        token_data = validated_data['code']
        user_data = token_data['user_data']
        
        try:
            with transaction.atomic():
                # Check if user exists by Google ID
                user = None
                try:
                    user = User.objects.get(google_id=user_data['google_id'])
                except User.DoesNotExist:
                    # Check if user exists by email
                    try:
                        user = User.objects.get(email=user_data['email'])
                        # Link existing account with Google
                        user.google_id = user_data['google_id']
                        user.is_google_user = True
                        user.google_avatar_url = user_data['google_avatar_url']
                        # Since Google verified the email, mark it as confirmed
                        user.email_confirmed = True
                        user.save()
                    except User.DoesNotExist:
                        # Create new user
                        user = self._create_google_user(user_data)
                
                # Update user info from Google if needed
                self._update_user_info(user, user_data)
                
                # Generate JWT tokens
                access_token, refresh_token = login(user)
                
                return {
                    'user': user,
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'google_access_token': token_data.get('access_token'),
                    'google_refresh_token': token_data.get('refresh_token'),
                    'message': 'Login successful'
                }
        
        except Exception as e:
            logger.error(f"Google OAuth code login error: {e}")
            raise serializers.ValidationError("Login failed")
    
    def _create_google_user(self, user_data):
        """Create a new user from Google data"""
        # Generate unique username from email
        email_prefix = user_data['email'].split('@')[0]
        username = email_prefix
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{email_prefix}{counter}"
            counter += 1
        
        user = User.objects.create(
            email=user_data['email'],
            username=username,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            google_id=user_data['google_id'],
            is_google_user=True,
            google_avatar_url=user_data['google_avatar_url'],
            email_confirmed=True,  # Google has already verified the email
            # Set random password for Google users (they won't use it)
            password=get_random_string(32)
        )
        
        # Set password unusable since they use Google OAuth
        user.set_unusable_password()
        user.save()
        
        # Download and save Google profile picture
        GoogleProfilePictureService.download_and_save_profile_picture(
            user, user_data['google_avatar_url']
        )
        
        return user
    
    def _update_user_info(self, user, user_data):
        """Update user information from Google if needed"""
        updated = False
        
        # Update avatar URL if changed
        if user.google_avatar_url != user_data['google_avatar_url']:
            user.google_avatar_url = user_data['google_avatar_url']
            updated = True
            
            # Download and update profile picture if avatar URL changed
            GoogleProfilePictureService.download_and_save_profile_picture(
                user, user_data['google_avatar_url']
            )
        
        # Update name if empty
        if not user.first_name and user_data['first_name']:
            user.first_name = user_data['first_name']
            updated = True
        
        if not user.last_name and user_data['last_name']:
            user.last_name = user_data['last_name']
            updated = True
        
        if updated:
            user.save()


class GoogleOAuthAuthURLSerializer(serializers.Serializer):
    """Serializer to generate Google OAuth authorization URL"""
    
    state = serializers.CharField(
        required=False,
        help_text="State parameter for CSRF protection"
    )
    
    def to_representation(self, instance):
        """Generate the authorization URL"""
        state = self.validated_data.get('state')
        auth_url = GoogleOAuthService.generate_auth_url(state)
        return {
            'auth_url': auth_url,
            'state': state
        }


class GoogleUserSerializer(serializers.ModelSerializer):
    """Serializer for Google user response"""
    email_confirmation_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'google_id', 'is_google_user', 'google_avatar_url',
            'profile_picture', 'business_type', 'wizard_complete', 
            'email_confirmed', 'email_confirmation_status', 'created_at'
        ]
        read_only_fields = ['id', 'google_id', 'is_google_user', 'email_confirmed', 'created_at']
    
    def get_email_confirmation_status(self, obj):
        """Get email confirmation status for Google users"""
        # For Google users, email is always confirmed
        return {
            'email_confirmed': obj.email_confirmed,
            'has_pending_confirmation': False,
            'pending_tokens_count': 0,
            'confirmation_required': not obj.email_confirmed,
            'latest_token_expires_at': None,
            'can_resend_confirmation': False,  # Google users don't need email confirmation
            'google_verified': obj.is_google_user
        }
