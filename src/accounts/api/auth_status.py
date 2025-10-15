from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.serializers import GoogleUserSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class AuthStatusAPIView(APIView):
    """
    Check current authentication status
    """
    permission_classes = [AllowAny]  # Allow both authenticated and unauthenticated users
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Authentication status",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'authenticated': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'cookies': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'headers': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            )
        },
        operation_description="Check authentication status and debug token information"
    )
    def get(self, request):
        """Check authentication status"""
        try:
            # Check if user is authenticated
            is_authenticated = request.user.is_authenticated
            
            # Prepare response data
            response_data = {
                'authenticated': is_authenticated,
                'timestamp': str(timezone.now()),
                'cookies_present': {},
                'headers_present': {},
                'user': None
            }
            
            # Check for authentication cookies
            response_data['cookies_present'] = {
                'HTTP_ACCESS': 'HTTP_ACCESS' in request.COOKIES,
                'HTTP_REFRESH': 'HTTP_REFRESH' in request.COOKIES,
                'USER_INFO': 'USER_INFO' in request.COOKIES,
                'sessionid': 'sessionid' in request.COOKIES,
            }
            
            # Check for authorization headers
            response_data['headers_present'] = {
                'Authorization': 'Authorization' in request.headers,
                'HTTP_AUTHORIZATION': 'HTTP_AUTHORIZATION' in request.META,
            }
            
            # If user is authenticated, include user data
            if is_authenticated:
                user_serializer = GoogleUserSerializer(request.user)
                response_data['user'] = user_serializer.data
                logger.info(f"Auth status check: User {request.user.email} is authenticated")
            else:
                logger.info("Auth status check: No authenticated user")
                
                # Check if there are cookies but user is not authenticated
                if any(response_data['cookies_present'].values()):
                    logger.warning("Auth status: Cookies present but user not authenticated - possible token issue")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error checking auth status: {e}")
            return Response(
                {
                    'error': 'Failed to check authentication status',
                    'authenticated': False
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardAccessAPIView(APIView):
    """
    Test endpoint that requires authentication - simulates dashboard access
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Dashboard access successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'dashboard_data': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            401: openapi.Response(description="Authentication required")
        },
        operation_description="Test endpoint requiring authentication - simulates dashboard access"
    )
    def get(self, request):
        """Test authenticated dashboard access"""
        try:
            user_serializer = GoogleUserSerializer(request.user)
            
            # Simulate dashboard data
            dashboard_data = {
                'welcome_message': f"Welcome back, {request.user.first_name or request.user.email}!",
                'last_login': str(request.user.last_login) if request.user.last_login else 'First login',
                'account_type': 'Google User' if request.user.is_google_user else 'Regular User',
                'email_confirmed': request.user.email_confirmed,
                'wizard_complete': request.user.wizard_complete,
                'profile_complete': request.user.is_profile_fill(),
            }
            
            logger.info(f"Dashboard access granted for user: {request.user.email}")
            
            return Response({
                'message': 'Dashboard access successful',
                'user': user_serializer.data,
                'dashboard_data': dashboard_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Dashboard access error for user {request.user.email}: {e}")
            return Response(
                {'error': 'Dashboard access failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
