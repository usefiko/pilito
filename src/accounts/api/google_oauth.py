from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from accounts.serializers import (
    GoogleOAuthLoginSerializer, 
    GoogleOAuthCodeSerializer, 
    GoogleOAuthAuthURLSerializer,
    GoogleUserSerializer
)
from accounts.services.google_oauth import GoogleOAuthService
from core.settings import ACCESS_TTL
from django.conf import settings
from django.shortcuts import redirect
from urllib.parse import urlencode
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
import base64
import json

logger = logging.getLogger(__name__)


class GoogleOAuthLoginAPIView(APIView):
    """
    Google OAuth login using ID token
    This endpoint accepts a Google ID token and logs in or registers the user
    """
    permission_classes = [AllowAny]
    serializer_class = GoogleOAuthLoginSerializer
    
    @swagger_auto_schema(
        request_body=GoogleOAuthLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access_token': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(description="Bad request")
        },
        operation_description="Login or register user using Google ID token"
    )
    def post(self, request):
        """Login or register user using Google ID token"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            try:
                result = serializer.create(serializer.validated_data)
                user = result['user']
                
                # Serialize user data
                user_serializer = GoogleUserSerializer(user)
                
                response_data = {
                    'access_token': result['access_token'],
                    'refresh_token': result['refresh_token'],
                    'user': user_serializer.data,
                    'message': result['message']
                }
                
                response = Response(response_data, status=status.HTTP_200_OK)
                
                # Set HTTP-only cookie for security
                response.set_cookie(
                    key="HTTP_ACCESS",
                    value=f"Bearer {result['access_token']}",
                    httponly=True,
                    max_age=ACCESS_TTL * 24 * 3600,
                    secure=False,  # Set to True in production with HTTPS
                    samesite='Lax'
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Google OAuth login error: {e}")
                return Response(
                    {'error': 'Login failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleOAuthCodeAPIView(APIView):
    """
    Google OAuth callback endpoint - handles authorization code from Google
    This endpoint receives the authorization code from Google OAuth redirect
    """
    permission_classes = [AllowAny]
    serializer_class = GoogleOAuthCodeSerializer
    
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('code', openapi.IN_QUERY, description="Authorization code from Google", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('state', openapi.IN_QUERY, description="State parameter", type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('error', openapi.IN_QUERY, description="Error from Google", type=openapi.TYPE_STRING, required=False),
        ],
        responses={
            302: openapi.Response(description="Redirect to frontend with tokens"),
            400: openapi.Response(description="Bad request")
        },
        operation_description="Handle Google OAuth callback and redirect to frontend"
    )
    def get(self, request):
        """Handle Google OAuth callback (GET request from Google)"""
        
        # Check for errors from Google
        error = request.GET.get('error')
        if error:
            logger.error(f"Google OAuth error: {error}")
            error_params = urlencode({'error': 'google_oauth_error', 'message': error})
            return redirect(f"{settings.GOOGLE_OAUTH2_FRONTEND_REDIRECT}?{error_params}")
        
        # Get authorization code
        code = request.GET.get('code')
        state = request.GET.get('state')
        
        if not code:
            logger.error("No authorization code received from Google")
            error_params = urlencode({'error': 'missing_code', 'message': 'No authorization code received'})
            return redirect(f"{settings.GOOGLE_OAUTH2_FRONTEND_REDIRECT}?{error_params}")
        
        try:
            # Enhanced logging for debugging
            logger.info(f"Google OAuth callback - Code received: {code[:10]}...")
            logger.info(f"Google OAuth callback - State: {state}")
            logger.info(f"Google OAuth callback - Redirect URI: {settings.GOOGLE_OAUTH2_REDIRECT_URI}")
            
            # Process the authorization code
            data = {'code': code}
            if state is not None:
                data['state'] = state
            serializer = self.serializer_class(data=data)
            
            if serializer.is_valid():
                logger.info("Google OAuth callback - Serializer validation successful")
                result = serializer.create(serializer.validated_data)
                user = result['user']
                logger.info(f"Google OAuth callback - User created/logged in: {user.email}")
                
                # Prepare success data
                success_data = {
                    'access_token': result['access_token'],
                    'refresh_token': result['refresh_token'],
                    'user_id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'wizard_complete': user.wizard_complete,
                    'success': True
                }
                
                # Encode the data to pass in URL (base64 encode to handle special characters)
                success_data_encoded = base64.urlsafe_b64encode(
                    json.dumps(success_data).encode()
                ).decode()
                
                # Create redirect response
                redirect_params = urlencode({
                    'success': 'true',
                    'data': success_data_encoded
                })
                
                redirect_url = f"{settings.GOOGLE_OAUTH2_FRONTEND_REDIRECT}?{redirect_params}"
                response = redirect(redirect_url)
                
                # Determine if we're in production based on the redirect URI
                is_production = 'pilito.com' in settings.GOOGLE_OAUTH2_FRONTEND_REDIRECT
                cookie_domain = '.pilito.com' if is_production else None
                cookie_secure = is_production  # Only secure in production (HTTPS)
                
                # Set HTTP-only cookies for security and persistence
                response.set_cookie(
                    key="HTTP_ACCESS",
                    value=f"Bearer {result['access_token']}",
                    httponly=True,
                    max_age=ACCESS_TTL * 24 * 3600,
                    secure=cookie_secure,
                    samesite='Lax',
                    domain=cookie_domain
                )
                
                response.set_cookie(
                    key="HTTP_REFRESH",
                    value=result['refresh_token'],
                    httponly=True,
                    max_age=30 * 24 * 3600,  # 30 days for refresh token
                    secure=cookie_secure,
                    samesite='Lax',
                    domain=cookie_domain
                )
                
                # Also set user info cookie (not HTTP-only so frontend can read it)
                user_info = {
                    'user_id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'wizard_complete': user.wizard_complete
                }
                response.set_cookie(
                    key="USER_INFO",
                    value=base64.urlsafe_b64encode(json.dumps(user_info).encode()).decode(),
                    httponly=False,  # Frontend can read this
                    max_age=ACCESS_TTL * 24 * 3600,
                    secure=cookie_secure,
                    samesite='Lax',
                    domain=cookie_domain
                )
                
                logger.info(f"Google OAuth success for user: {user.email} - Cookies set")
                return response
                
            else:
                logger.error(f"Google OAuth callback - Serializer validation failed: {serializer.errors}")
                # Extract the specific error message for better debugging
                error_detail = str(serializer.errors)
                if 'code' in serializer.errors:
                    error_detail = serializer.errors['code'][0] if serializer.errors['code'] else 'Invalid authorization code'
                
                error_params = urlencode({
                    'error': 'validation_failed', 
                    'message': str(error_detail)
                })
                return redirect(f"{settings.GOOGLE_OAUTH2_FRONTEND_REDIRECT}?{error_params}")
                
        except Exception as e:
            logger.error(f"Google OAuth callback error: {e}")
            error_params = urlencode({
                'error': 'processing_failed', 
                'message': 'Failed to process Google authentication'
            })
            return redirect(f"{settings.GOOGLE_OAUTH2_FRONTEND_REDIRECT}?{error_params}")
    
    @swagger_auto_schema(
        request_body=GoogleOAuthCodeSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access_token': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'google_access_token': openapi.Schema(type=openapi.TYPE_STRING),
                        'google_refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(description="Bad request")
        },
        operation_description="Login or register user using Google authorization code (API endpoint)"
    )
    def post(self, request):
        """Login or register user using Google authorization code (API endpoint)"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            try:
                result = serializer.create(serializer.validated_data)
                user = result['user']
                
                # Serialize user data
                user_serializer = GoogleUserSerializer(user)
                
                response_data = {
                    'access_token': result['access_token'],
                    'refresh_token': result['refresh_token'],
                    'user': user_serializer.data,
                    'google_access_token': result.get('google_access_token'),
                    'google_refresh_token': result.get('google_refresh_token'),
                    'message': result['message']
                }
                
                response = Response(response_data, status=status.HTTP_200_OK)
                
                # Set HTTP-only cookie for security
                response.set_cookie(
                    key="HTTP_ACCESS",
                    value=f"Bearer {result['access_token']}",
                    httponly=True,
                    max_age=ACCESS_TTL * 24 * 3600,
                    secure=False,  # Set to True in production with HTTPS
                    samesite='Lax'
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Google OAuth code login error: {e}")
                return Response(
                    {'error': 'Login failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleOAuthAuthURLAPIView(APIView):
    """
    Generate Google OAuth authorization URL
    This endpoint generates the URL to redirect users to Google for authentication
    """
    permission_classes = [AllowAny]
    serializer_class = GoogleOAuthAuthURLSerializer
    
    @swagger_auto_schema(
        request_body=GoogleOAuthAuthURLSerializer,
        responses={
            200: openapi.Response(
                description="Authorization URL generated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'auth_url': openapi.Schema(type=openapi.TYPE_STRING),
                        'state': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(description="Bad request")
        },
        operation_description="Generate Google OAuth authorization URL"
    )
    def post(self, request):
        """Generate Google OAuth authorization URL"""
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            try:
                response_data = serializer.to_representation(None)
                return Response(response_data, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Error generating Google auth URL: {e}")
                return Response(
                    {'error': 'Failed to generate authorization URL'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Authorization URL generated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'auth_url': openapi.Schema(type=openapi.TYPE_STRING),
                        'state': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        },
        operation_description="Generate Google OAuth authorization URL (GET request)"
    )
    def get(self, request):
        """Generate Google OAuth authorization URL (GET method)"""
        try:
            state = request.query_params.get('state')
            auth_url = GoogleOAuthService.generate_auth_url(state)
            
            response_data = {
                'auth_url': auth_url,
                'state': state
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating Google auth URL: {e}")
            return Response(
                {'error': 'Failed to generate authorization URL'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleOAuthTestAPIView(APIView):
    """
    Test endpoint to verify Google OAuth configuration
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Configuration status",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'configured': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'client_id_configured': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'client_secret_configured': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'redirect_uri': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        },
        operation_description="Check Google OAuth configuration status"
    )
    def get(self, request):
        """Check Google OAuth configuration status"""
        from django.conf import settings
        
        response_data = {
            'configured': bool(
                getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None) and 
                getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', None)
            ),
            'client_id_configured': bool(getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)),
            'client_secret_configured': bool(getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', None)),
            'redirect_uri': getattr(settings, 'GOOGLE_OAUTH2_REDIRECT_URI', ''),
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
