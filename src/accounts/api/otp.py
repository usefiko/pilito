from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from accounts.serializers import SendOTPSerializer, VerifyOTPSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings


class OTPRateThrottle(AnonRateThrottle):
    """Custom throttle for OTP endpoints to prevent abuse"""
    rate = '5/min'  # 5 requests per minute for anonymous users


class SendOTPAPIView(APIView):
    """
    API endpoint to send OTP code to phone number via SMS.
    
    This endpoint sends a 6-digit OTP code to the provided phone number
    using Kavenegar SMS service. The OTP is valid for 5 minutes.
    """
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]
    
    @swagger_auto_schema(
        operation_description="Send OTP code to phone number for authentication",
        request_body=SendOTPSerializer,
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
                description="Invalid phone number or rate limit exceeded",
                examples={
                    "application/json": {
                        "phone_number": ["Please provide a valid Iranian phone number"]
                    }
                }
            ),
            429: "Too many requests"
        },
        tags=['Authentication - OTP']
    )
    def post(self, request):
        """Send OTP to phone number"""
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = serializer.save()
                return Response(result, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'detail': 'Failed to send OTP. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class VerifyOTPAPIView(APIView):
    """
    API endpoint to verify OTP code and authenticate user.
    
    This endpoint verifies the OTP code sent to the phone number.
    If valid, it creates/authenticates the user and returns JWT tokens.
    """
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]
    
    @swagger_auto_schema(
        operation_description="Verify OTP code and login/register user",
        request_body=VerifyOTPSerializer,
        responses={
            200: openapi.Response(
                description="OTP verified successfully, user authenticated",
                examples={
                    "application/json": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "is_new_user": False,
                        "user": {
                            "id": 1,
                            "phone_number": "+989123456789",
                            "email": "989123456789@temp.pilito.com"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid OTP or OTP expired",
                examples={
                    "application/json": {
                        "code": ["Invalid OTP code. 2 attempt(s) remaining."]
                    }
                }
            ),
            429: "Too many requests"
        },
        tags=['Authentication - OTP']
    )
    def post(self, request):
        """Verify OTP and authenticate user"""
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            # Get validated data including tokens
            validated_data = serializer.validated_data
            user = validated_data['user']
            
            # Prepare response data
            response_data = {
                'access_token': validated_data['access_token'],
                'refresh_token': validated_data['refresh_token'],
                'is_new_user': validated_data['is_new_user'],
                'user': {
                    'id': user.id,
                    'phone_number': user.phone_number,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            }
            
            # Set HTTP-only cookie for access token (same as login)
            response = Response(response_data, status=status.HTTP_200_OK)
            response.set_cookie(
                key="HTTP_ACCESS",
                value=f"Bearer {validated_data['access_token']}",
                httponly=True,
                max_age=settings.ACCESS_TTL * 24 * 3600,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax'
            )
            
            return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

