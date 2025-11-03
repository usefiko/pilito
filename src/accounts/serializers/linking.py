"""
Serializers for linking email/phone to existing accounts
"""
from rest_framework import serializers
from accounts.models import User, OTPToken, EmailConfirmationToken
from accounts.utils import send_email_confirmation
from django.core.validators import EmailValidator
from django.utils import timezone
from datetime import timedelta
import re
import logging

logger = logging.getLogger(__name__)


class SendEmailCodeForLinkingSerializer(serializers.Serializer):
    """
    Serializer for sending email verification code to add email to phone-based account
    """
    email = serializers.EmailField(
        required=True,
        validators=[EmailValidator()],
        help_text="Email address to add to your account"
    )
    
    def validate_email(self, value):
        """Validate that email is not already in use"""
        # Normalize email
        email = value.lower().strip()
        
        # Check if email already exists on another account
        if User.objects.filter(email=email).exclude(id=self.context['user'].id).exists():
            raise serializers.ValidationError(
                "This email is already linked to another account."
            )
        
        return email
    
    def validate(self, attrs):
        """Additional validations"""
        user = self.context['user']
        email = attrs['email']
        
        # Check if user already has this email verified
        if user.email == email and user.email_confirmed:
            raise serializers.ValidationError({
                'email': 'This email is already verified on your account.'
            })
        
        # Rate limiting - check if code was sent recently
        recent_token = EmailConfirmationToken.objects.filter(
            user=user,
            is_used=False
        ).order_by('-created_at').first()
        
        if recent_token:
            time_since_last = timezone.now() - recent_token.created_at
            wait_time = timedelta(minutes=2)  # 2 minutes wait time
            
            if time_since_last < wait_time:
                remaining_seconds = (wait_time - time_since_last).total_seconds()
                remaining_minutes = int(remaining_seconds // 60)
                remaining_secs = int(remaining_seconds % 60)
                
                if remaining_minutes > 0:
                    error_msg = f'Please wait {remaining_minutes} minute(s) and {remaining_secs} second(s) before requesting a new code.'
                else:
                    error_msg = f'Please wait {remaining_secs} second(s) before requesting a new code.'
                
                raise serializers.ValidationError(error_msg)
        
        return attrs
    
    def create(self, validated_data):
        """Send email verification code"""
        user = self.context['user']
        email = validated_data['email']
        
        # Update user's email (not confirmed yet)
        user.email = email
        user.email_confirmed = False
        user.save()
        
        # Invalidate previous tokens
        EmailConfirmationToken.objects.filter(
            user=user,
            is_used=False
        ).update(is_used=True)
        
        # Create new token
        token = EmailConfirmationToken.objects.create(user=user)
        
        # Send email
        email_sent, result = send_email_confirmation(user)
        
        if not email_sent:
            logger.error(f"Failed to send email to {email}: {result}")
            raise serializers.ValidationError({
                'detail': f'Failed to send verification email: {result}'
            })
        
        return {
            'email': email,
            'message': 'Verification code sent to your email',
            'expires_in': 900  # 15 minutes
        }


class VerifyEmailCodeForLinkingSerializer(serializers.Serializer):
    """
    Serializer for verifying email code and linking email to account
    """
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        required=True,
        help_text="6-digit verification code sent to your email"
    )
    
    def validate_code(self, value):
        """Validate code format"""
        if not value.isdigit():
            raise serializers.ValidationError("Verification code must contain only digits")
        return value
    
    def validate(self, attrs):
        """Verify the code and link email"""
        user = self.context['user']
        code = attrs['code']
        
        try:
            # Find valid token
            token = EmailConfirmationToken.objects.get(
                user=user,
                code=code,
                is_used=False
            )
            
            if not token.is_valid():
                raise serializers.ValidationError({
                    'code': 'Verification code has expired. Please request a new one.'
                })
            
            # Mark token as used
            token.is_used = True
            token.save()
            
            # Mark email as confirmed
            user.email_confirmed = True
            user.save()
            
            attrs['user'] = user
            
            return attrs
            
        except EmailConfirmationToken.DoesNotExist:
            raise serializers.ValidationError({
                'code': 'Invalid verification code.'
            })


class SendOTPForLinkingSerializer(serializers.Serializer):
    """
    Serializer for sending OTP to add phone number to email-based account
    """
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
        
        # Check if phone number already exists on another account
        user = self.context['user']
        if User.objects.filter(phone_number=phone_number).exclude(id=user.id).exists():
            raise serializers.ValidationError(
                "This phone number is already linked to another account."
            )
        
        return phone_number
    
    def validate(self, attrs):
        """Additional validations and rate limiting"""
        user = self.context['user']
        phone_number = attrs['phone_number']
        
        # Check if user already has this phone verified
        if user.phone_number == phone_number:
            raise serializers.ValidationError({
                'phone_number': 'This phone number is already linked to your account.'
            })
        
        # Rate limiting - check for recent OTP
        last_otp = OTPToken.objects.filter(
            phone_number=phone_number
        ).order_by('-created_at').first()
        
        if last_otp:
            from django.conf import settings
            time_since_last = timezone.now() - last_otp.created_at
            wait_time_seconds = getattr(settings, 'OTP_RESEND_WAIT_TIME', 300)  # 5 minutes
            
            if time_since_last < timedelta(seconds=wait_time_seconds):
                remaining_seconds = (timedelta(seconds=wait_time_seconds) - time_since_last).total_seconds()
                remaining_minutes = int(remaining_seconds // 60)
                remaining_secs = int(remaining_seconds % 60)
                
                if remaining_minutes > 0:
                    error_msg = f'Too many OTP requests. Please wait {remaining_minutes} minute(s) and {remaining_secs} second(s) before requesting a new OTP.'
                else:
                    error_msg = f'Too many OTP requests. Please wait {remaining_secs} second(s) before requesting a new OTP.'
                
                raise serializers.ValidationError(error_msg)
        
        return attrs
    
    def create(self, validated_data):
        """Create and send OTP"""
        from django.conf import settings
        from kavenegar import KavenegarAPI, APIException, HTTPException
        
        phone_number = validated_data['phone_number']
        
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
            
            # Remove + from phone number for Kavenegar
            recipient = phone_number.replace('+', '')
            
            logger.info(f"Attempting to send OTP for linking to {recipient}")
            
            # Try using Verify/Lookup service first
            params = {
                'receptor': recipient,
                'token': otp_token.code,
                'template': 'otp-verify',
            }
            
            try:
                response = api.verify_lookup(params)
                logger.info(f"OTP sent successfully via Verify service")
            except Exception as verify_error:
                # Fallback to regular SMS
                logger.warning(f"Verify lookup failed: {verify_error}")
                logger.info("Falling back to regular SMS send...")
                
                message = f"کد تایید شما: {otp_token.code}\n\nاین کد تا {settings.OTP_EXPIRY_TIME // 60} دقیقه اعتبار دارد."
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
            error_msg = str(e)
            try:
                if hasattr(e, 'args') and e.args:
                    error_msg = str(e.args[0])
                    if isinstance(error_msg, bytes):
                        error_msg = error_msg.decode('utf-8')
            except:
                pass
            
            logger.error(f"Kavenegar API error: {error_msg}")
            
            # User-friendly error messages
            if '412' in error_msg or 'نامعتبر' in error_msg:
                user_msg = 'Sender number is invalid. Please contact support.'
            elif '401' in error_msg:
                user_msg = 'Invalid API key. Please contact support.'
            elif '402' in error_msg:
                user_msg = 'Insufficient credit. Please contact support.'
            else:
                user_msg = f'Failed to send OTP: {error_msg}'
            
            raise serializers.ValidationError({
                'detail': user_msg
            })
        except Exception as e:
            logger.error(f"Unexpected error sending OTP: {str(e)}")
            raise serializers.ValidationError({
                'detail': f'An error occurred: {str(e)}'
            })


class VerifyOTPForLinkingSerializer(serializers.Serializer):
    """
    Serializer for verifying OTP and linking phone to account
    """
    phone_number = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Phone number to verify"
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
        """Verify OTP and link phone to account"""
        user = self.context['user']
        phone_number = attrs['phone_number']
        code = attrs['code']
        
        # Check if phone is already linked to another account
        if User.objects.filter(phone_number=phone_number).exclude(id=user.id).exists():
            raise serializers.ValidationError({
                'phone_number': 'This phone number is already linked to another account.'
            })
        
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
            
            # Link phone number to user
            user.phone_number = phone_number
            user.save()
            
            attrs['user'] = user
            
            return attrs
            
        except OTPToken.DoesNotExist:
            raise serializers.ValidationError({
                'code': 'Invalid or expired OTP. Please request a new one.'
            })

