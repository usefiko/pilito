from rest_framework import serializers
from accounts.serializers.user import UserShortSerializer
from accounts.functions import login
from accounts.utils import send_email_confirmation
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    affiliate = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'affiliate')
    
    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists. Please use a different email or try logging in.")
        return value
    
    def validate_username(self, value):
        """Check if username already exists"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken. Please choose a different username.")
        return value

    def create(self, validated_data):
        # Extract affiliate code from validated data
        affiliate_code = validated_data.pop('affiliate', None)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # Process affiliate/referral code
        affiliate_applied = False
        referrer_info = None
        affiliate_error = None
        
        if affiliate_code:
            try:
                referrer = User.objects.get(invite_code=affiliate_code)
                user.referred_by = referrer
                user.save()
                
                # Add referral bonus to referrer's wallet (e.g., 10.00)
                from decimal import Decimal
                referrer.wallet_balance += Decimal('10.00')
                referrer.save()
                
                affiliate_applied = True
                referrer_info = {
                    'id': referrer.id,
                    'username': referrer.username,
                    'invite_code': referrer.invite_code
                }
            except User.DoesNotExist:
                # Invalid affiliate code, but don't fail registration
                affiliate_error = "Invalid affiliate code"
                pass
        
        # Send email confirmation
        # Try async first, but use sync as immediate fallback for reliability
        email_sent = False
        email_error = None
        email_queued = False
        
        # Try synchronous sending first (same as resend endpoint that works)
        try:
            logger.info(f"📧 Sending email confirmation to user {user.id} ({user.email})")
            email_sent, result = send_email_confirmation(user)
            
            if email_sent:
                logger.info(f"✅ Email sent successfully to user {user.id}")
                print(f"✅ Email sent successfully to {user.email}")
            else:
                email_error = result
                logger.warning(f"⚠️  Email sending returned False: {result}")
                print(f"⚠️  Email sending warning: {result}")
                
                # Try async as backup
                try:
                    from accounts.tasks import send_email_confirmation_async
                    task = send_email_confirmation_async.apply_async(
                        args=[user.id],
                        countdown=5
                    )
                    email_queued = True
                    logger.info(f"📬 Email queued for retry via Celery (task: {task.id})")
                except Exception as celery_error:
                    logger.warning(f"Could not queue email task: {celery_error}")
                    
        except Exception as e:
            email_error = str(e)
            logger.error(f"❌ Email sending error for user {user.id}: {e}")
            print(f"❌ Email sending error: {str(e)}")
            
            # Try async as backup
            try:
                from accounts.tasks import send_email_confirmation_async
                task = send_email_confirmation_async.apply_async(
                    args=[user.id],
                    countdown=5
                )
                email_queued = True
                logger.info(f"📬 Email queued for retry via Celery (task: {task.id})")
            except Exception as celery_error:
                logger.warning(f"Could not queue email task: {celery_error}")
        
        try:
            access, refresh = login(user)
        except Exception as e:
            raise serializers.ValidationError(f"Token generation error: {str(e)}")
        
        response_data = {
            "refresh_token": refresh,
            "access_token": access,
            "user_data": UserShortSerializer(user).data,
            "email_confirmation_sent": email_sent or email_queued,  # True if sent or queued
            "message": "Registration successful!" + (
                " Please check your email for confirmation code." if (email_sent or email_queued)
                else " Email confirmation will be sent shortly."
            )
        }
        
        # Add email status info
        if email_queued:
            response_data["email_info"] = {
                "email_queued": True,
                "message": "Email confirmation is being sent in the background"
            }
        elif not email_sent and email_error:
            response_data["email_info"] = {
                "email_sent": False,
                "email_queued": False,
                "error": email_error,
                "can_resend": True
            }
        
        # Add affiliate information to response
        if affiliate_code:
            response_data["affiliate_info"] = {
                "affiliate_code_provided": affiliate_code,
                "affiliate_applied": affiliate_applied,
                "referrer": referrer_info,
                "error": affiliate_error
            }
        
        return response_data


class CompleteRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('first_name','last_name','age','gender','address','organisation','description','state','zip_code','country','language','time_zone','currency','business_type')