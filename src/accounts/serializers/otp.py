from rest_framework import serializers
from accounts.models import User, OTPToken
from django.contrib.auth import authenticate
from accounts.functions.jwt import login as generate_jwt_tokens
import re


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP to phone number"""
    phone_number = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Phone number in international format (e.g., +989123456789)"
    )
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        # Remove any spaces or special characters except +
        phone_number = re.sub(r'[^\d+]', '', value)
        
        # Basic validation for Iranian phone numbers
        if not phone_number.startswith('+98') and not phone_number.startswith('09'):
            raise serializers.ValidationError(
                "Please provide a valid Iranian phone number starting with +98 or 09"
            )
        
        # Normalize to international format
        if phone_number.startswith('09'):
            phone_number = '+98' + phone_number[1:]
        
        return phone_number
    
    def create(self, validated_data):
        """Create and send OTP"""
        from django.conf import settings
        from kavenegar import KavenegarAPI, APIException, HTTPException
        from django.utils import timezone
        from datetime import timedelta
        
        phone_number = validated_data['phone_number']
        
        # Check for rate limiting - prevent sending too many OTPs
        recent_otps = OTPToken.objects.filter(
            phone_number=phone_number,
            created_at__gte=timezone.now() - timedelta(minutes=2)
        ).count()
        
        if recent_otps >= 3:
            raise serializers.ValidationError({
                'phone_number': 'Too many OTP requests. Please try again in 2 minutes.'
            })
        
        # Invalidate all previous unused OTPs for this phone number
        OTPToken.objects.filter(
            phone_number=phone_number,
            is_used=False
        ).update(is_used=True)
        
        # Create new OTP
        otp_token = OTPToken.objects.create(phone_number=phone_number)
        
        # Send OTP via Kavenegar
        try:
            api_key = settings.KAVENEGAR_API_KEY
            if not api_key:
                raise serializers.ValidationError({
                    'detail': 'SMS service is not configured. Please contact support.'
                })
            
            api = KavenegarAPI(api_key)
            
            # Prepare SMS message
            message = f"کد تایید شما: {otp_token.code}\n\nاین کد تا {settings.OTP_EXPIRY_TIME // 60} دقیقه اعتبار دارد."
            
            # Remove + from phone number for Kavenegar
            recipient = phone_number.replace('+', '')
            
            # Kavenegar expects parameters as keyword arguments, not a dictionary
            params = {
                'sender': settings.KAVENEGAR_SENDER,
                'receptor': recipient,
                'message': message,
            }
            
            response = api.sms_send(params)
            
            return {
                'phone_number': phone_number,
                'message': 'OTP sent successfully',
                'expires_in': settings.OTP_EXPIRY_TIME
            }
            
        except (APIException, HTTPException) as e:
            # Log the error with more details
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Kavenegar API error: {str(e)}")
            logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details'}")
            print(f"Kavenegar error: {str(e)}")
            print(f"Error type: {type(e)}")
            raise serializers.ValidationError({
                'detail': f'Failed to send OTP: {str(e)}'
            })
        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error sending OTP: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            print(f"Unexpected error sending OTP: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(traceback.format_exc())
            raise serializers.ValidationError({
                'detail': f'An error occurred: {str(e)}'
            })


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP and logging in"""
    phone_number = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Phone number used to receive OTP"
    )
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        required=True,
        help_text="6-digit OTP code received via SMS"
    )
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        # Remove any spaces or special characters except +
        phone_number = re.sub(r'[^\d+]', '', value)
        
        # Normalize to international format
        if phone_number.startswith('09'):
            phone_number = '+98' + phone_number[1:]
        
        return phone_number
    
    def validate_code(self, value):
        """Validate OTP code format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must contain only digits")
        return value
    
    def validate(self, attrs):
        """Verify OTP and authenticate user"""
        phone_number = attrs['phone_number']
        code = attrs['code']
        
        # Find the most recent valid OTP for this phone number
        try:
            otp_token = OTPToken.objects.filter(
                phone_number=phone_number,
                is_used=False
            ).order_by('-created_at').first()
            
            if not otp_token:
                raise serializers.ValidationError({
                    'code': 'No active OTP found. Please request a new one.'
                })
            
            # Check if OTP is expired or attempts exceeded
            if not otp_token.is_valid():
                raise serializers.ValidationError({
                    'code': 'OTP has expired or maximum attempts exceeded. Please request a new one.'
                })
            
            # Verify the code
            if otp_token.code != code:
                otp_token.increment_attempts()
                remaining_attempts = 3 - otp_token.attempts
                if remaining_attempts > 0:
                    raise serializers.ValidationError({
                        'code': f'Invalid OTP code. {remaining_attempts} attempt(s) remaining.'
                    })
                else:
                    raise serializers.ValidationError({
                        'code': 'Maximum attempts exceeded. Please request a new OTP.'
                    })
            
            # Mark OTP as used
            otp_token.is_used = True
            otp_token.save()
            
            # Find or create user with this phone number
            user, created = User.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'username': phone_number.replace('+', ''),  # Use phone as username
                    'email': f"{phone_number.replace('+', '')}@temp.pilito.com",  # Temporary email
                }
            )
            
            # If user is newly created, set a flag
            attrs['is_new_user'] = created
            attrs['user'] = user
            
            # Generate JWT tokens
            access_token, refresh_token = generate_jwt_tokens(user)
            
            attrs['access_token'] = access_token
            attrs['refresh_token'] = refresh_token
            
            return attrs
            
        except OTPToken.DoesNotExist:
            raise serializers.ValidationError({
                'code': 'Invalid or expired OTP. Please request a new one.'
            })

