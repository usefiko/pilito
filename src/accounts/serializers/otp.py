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
    
    def validate(self, attrs):
        """Validate rate limiting before creating OTP"""
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta
        
        phone_number = attrs['phone_number']
        
        # Check for rate limiting - only allow 1 OTP per 5 minutes
        # Get the most recent OTP for this phone number
        last_otp = OTPToken.objects.filter(
            phone_number=phone_number
        ).order_by('-created_at').first()
        
        if last_otp:
            # Calculate time since last OTP
            time_since_last = timezone.now() - last_otp.created_at
            wait_time_seconds = settings.OTP_RESEND_WAIT_TIME  # Get from settings (default: 5 minutes)
            
            # If last OTP was sent within the wait time
            if time_since_last < timedelta(seconds=wait_time_seconds):
                # Calculate remaining wait time
                remaining_seconds = (timedelta(seconds=wait_time_seconds) - time_since_last).total_seconds()
                remaining_minutes = int(remaining_seconds // 60)
                remaining_secs = int(remaining_seconds % 60)
                
                if remaining_minutes > 0:
                    error_msg = f'Too many OTP requests. Please wait {remaining_minutes} minute(s) and {remaining_secs} second(s) before requesting a new OTP.'
                else:
                    error_msg = f'Too many OTP requests. Please wait {remaining_secs} second(s) before requesting a new OTP.'
                
                # Raise as non_field_errors so it shows clearly
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
            
            # Log OTP sending attempt
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Attempting to send OTP via Kavenegar Verify:")
            logger.info(f"  Receptor: {recipient}")
            logger.info(f"  Template: otp-verify")
            logger.info(f"  Token: {otp_token.code}")
            
            # Use Kavenegar's Verify/Lookup service (better for OTP, no sender required!)
            # Template 'verify' should exist in your Kavenegar panel
            # Go to: https://panel.kavenegar.com/client/verification/add
            # Create a template named "verify" with pattern like: "کد تایید شما: %token%"
            params = {
                'receptor': recipient,
                'token': otp_token.code,
                'template': 'otp-verify',  # Template name from Kavenegar panel
            }
            
            try:
                response = api.verify_lookup(params)
                logger.info(f"OTP sent successfully via Verify service")
            except Exception as verify_error:
                # If verify_lookup fails (e.g., template not found), fallback to regular SMS
                logger.warning(f"Verify lookup failed: {verify_error}")
                logger.info("Falling back to regular SMS send...")
                
                # Fallback to regular SMS (requires sender number)
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
            # Log the error with more details
            import logging
            logger = logging.getLogger(__name__)
            
            # Decode Persian error message
            error_msg = str(e)
            try:
                # Try to decode if it's bytes
                if isinstance(e, bytes):
                    error_msg = e.decode('utf-8')
                elif hasattr(e, 'args') and e.args:
                    error_msg = str(e.args[0])
                    if isinstance(error_msg, bytes):
                        error_msg = error_msg.decode('utf-8')
            except:
                pass
            
            logger.error(f"Kavenegar API error: {error_msg}")
            logger.error(f"Sender used: {settings.KAVENEGAR_SENDER}")
            logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details'}")
            print(f"Kavenegar error: {error_msg}")
            print(f"Error type: {type(e)}")
            
            # Provide user-friendly error messages based on error code
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
        max_length=4,
        min_length=4,
        required=True,
        help_text="4-digit OTP code received via SMS"
    )
    affiliate = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Affiliate/invite code for referral (optional)"
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
            
            # Process affiliate/referral code (for new users or users without referrer)
            # Note: Commission is paid when referred user makes payments, not at registration
            # See billing/signals.py process_affiliate_commission for commission logic
            affiliate_code = attrs.get('affiliate', None)
            if affiliate_code and not user.referred_by:  # Don't update if already has referrer
                try:
                    referrer = User.objects.get(invite_code=affiliate_code)
                    user.referred_by = referrer
                    user.save()
                except User.DoesNotExist:
                    # Invalid affiliate code, but don't fail registration
                    pass
            
            # Generate JWT tokens
            access_token, refresh_token = generate_jwt_tokens(user)
            
            attrs['access_token'] = access_token
            attrs['refresh_token'] = refresh_token
            
            return attrs
            
        except OTPToken.DoesNotExist:
            raise serializers.ValidationError({
                'code': 'Invalid or expired OTP. Please request a new one.'
            })

