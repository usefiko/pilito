"""
API views for linking email/phone to existing accounts
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from accounts.serializers import (
    SendEmailCodeForLinkingSerializer,
    VerifyEmailCodeForLinkingSerializer,
    SendOTPForLinkingSerializer,
    VerifyOTPForLinkingSerializer
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)


class LinkingRateThrottle(UserRateThrottle):
    """Custom throttle for linking endpoints to prevent abuse"""
    rate = '10/min'  # 10 requests per minute for authenticated users


class AddEmailSendCodeAPIView(APIView):
    """
    API endpoint to send verification code to email for linking to phone-based account.
    
    Authenticated users who registered with phone number can use this endpoint
    to add an email address to their account. A 4-digit verification code
    will be sent to the provided email.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [LinkingRateThrottle]
    
    @swagger_auto_schema(
        operation_description="""
        Send verification code to email address for linking to your account.
        
        **Requirements:**
        - User must be authenticated
        - Email must not be already linked to another account
        - Rate limited to prevent abuse
        
        **Flow:**
        1. User provides email address
        2. System sends 4-digit verification code to email
        3. Code is valid for 15 minutes
        4. User verifies code using verify endpoint
        """,
        request_body=SendEmailCodeForLinkingSerializer,
        responses={
            200: openapi.Response(
                description="Verification code sent successfully",
                examples={
                    "application/json": {
                        "email": "user@example.com",
                        "message": "Verification code sent to your email",
                        "expires_in": 900
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid email or validation error",
                examples={
                    "application/json": {
                        "email": ["This email is already linked to another account."]
                    }
                }
            ),
            401: "Unauthorized - Authentication required",
            429: openapi.Response(
                description="Rate limit exceeded",
                examples={
                    "application/json": {
                        "detail": "Please wait 1 minute(s) and 30 second(s) before requesting a new code."
                    }
                }
            )
        },
        tags=['Account Linking']
    )
    def post(self, request):
        """Send verification code to email"""
        serializer = SendEmailCodeForLinkingSerializer(
            data=request.data,
            context={'user': request.user}
        )
        
        if serializer.is_valid():
            try:
                result = serializer.save()
                return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error sending email verification code: {str(e)}")
                return Response(
                    {'detail': 'Failed to send verification code. Please try again later.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Handle validation errors (including rate limiting)
        errors = serializer.errors
        if 'non_field_errors' in errors:
            return Response(
                {'detail': errors['non_field_errors'][0]},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class AddEmailVerifyCodeAPIView(APIView):
    """
    API endpoint to verify email code and link email to account.
    
    This endpoint verifies the code sent to the email and links
    the email address to the authenticated user's account.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [LinkingRateThrottle]
    
    @swagger_auto_schema(
        operation_description="""
        Verify email verification code and link email to your account.
        
        **Requirements:**
        - User must be authenticated
        - Valid 4-digit verification code
        - Code must not be expired (15 minutes validity)
        
        **Flow:**
        1. User provides verification code received via email
        2. System validates the code
        3. Email is linked and marked as verified on user account
        """,
        request_body=VerifyEmailCodeForLinkingSerializer,
        responses={
            200: openapi.Response(
                description="Email verified and linked successfully",
                examples={
                    "application/json": {
                        "message": "Email linked successfully!",
                        "email": "user@example.com",
                        "email_confirmed": True
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid or expired code",
                examples={
                    "application/json": {
                        "code": ["Invalid verification code."]
                    }
                }
            ),
            401: "Unauthorized - Authentication required"
        },
        tags=['Account Linking']
    )
    def post(self, request):
        """Verify email code and link email to account"""
        serializer = VerifyEmailCodeForLinkingSerializer(
            data=request.data,
            context={'user': request.user}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            response_data = {
                'message': 'Email linked successfully!',
                'email': user.email,
                'email_confirmed': user.email_confirmed
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddPhoneSendOTPAPIView(APIView):
    """
    API endpoint to send OTP to phone number for linking to email-based account.
    
    Authenticated users who registered with email can use this endpoint
    to add a phone number to their account. A 4-digit OTP will be sent
    to the provided phone number via SMS.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [LinkingRateThrottle]
    
    @swagger_auto_schema(
        operation_description="""
        Send OTP code to phone number for linking to your account.
        
        **Requirements:**
        - User must be authenticated
        - Phone number must not be already linked to another account
        - Rate limited to 1 request per 5 minutes per phone number
        
        **Flow:**
        1. User provides phone number
        2. System sends 4-digit OTP via SMS
        3. OTP is valid for 5 minutes
        4. User verifies OTP using verify endpoint
        """,
        request_body=SendOTPForLinkingSerializer,
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                examples={
                    "application/json": {
                        "phone_number": "+989123456789",
                        "message": "OTP sent successfully",
                        "expires_in": 300
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid phone number or validation error",
                examples={
                    "application/json": {
                        "phone_number": ["This phone number is already linked to another account."]
                    }
                }
            ),
            401: "Unauthorized - Authentication required",
            429: openapi.Response(
                description="Rate limit exceeded - Too many OTP requests",
                examples={
                    "application/json": {
                        "detail": "Too many OTP requests. Please wait 4 minute(s) and 30 second(s) before requesting a new OTP."
                    }
                }
            )
        },
        tags=['Account Linking']
    )
    def post(self, request):
        """Send OTP to phone number"""
        serializer = SendOTPForLinkingSerializer(
            data=request.data,
            context={'user': request.user}
        )
        
        if serializer.is_valid():
            try:
                result = serializer.save()
                return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error sending OTP: {str(e)}")
                return Response(
                    {'detail': 'Failed to send OTP. Please try again later.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Handle validation errors (including rate limiting)
        errors = serializer.errors
        if 'non_field_errors' in errors:
            return Response(
                {'detail': errors['non_field_errors'][0]},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class AddPhoneVerifyOTPAPIView(APIView):
    """
    API endpoint to verify OTP and link phone number to account.
    
    This endpoint verifies the OTP sent to the phone number and links
    the phone number to the authenticated user's account.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [LinkingRateThrottle]
    
    @swagger_auto_schema(
        operation_description="""
        Verify OTP code and link phone number to your account.
        
        **Requirements:**
        - User must be authenticated
        - Valid 4-digit OTP code
        - OTP must not be expired (5 minutes validity)
        - Maximum 3 verification attempts per OTP
        
        **Flow:**
        1. User provides phone number and OTP code received via SMS
        2. System validates the OTP
        3. Phone number is linked to user account
        """,
        request_body=VerifyOTPForLinkingSerializer,
        responses={
            200: openapi.Response(
                description="Phone number verified and linked successfully",
                examples={
                    "application/json": {
                        "message": "Phone number linked successfully!",
                        "phone_number": "+989123456789"
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid or expired OTP",
                examples={
                    "application/json": {
                        "code": ["Invalid OTP code. 2 attempt(s) remaining."]
                    }
                }
            ),
            401: "Unauthorized - Authentication required"
        },
        tags=['Account Linking']
    )
    def post(self, request):
        """Verify OTP and link phone number to account"""
        serializer = VerifyOTPForLinkingSerializer(
            data=request.data,
            context={'user': request.user}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            response_data = {
                'message': 'Phone number linked successfully!',
                'phone_number': user.phone_number
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

