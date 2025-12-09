from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.functions import login
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from accounts.models.user import EmailConfirmationToken
import re

class UserShortSerializer(serializers.ModelSerializer):
    email_confirmation_status = serializers.SerializerMethodField()
    free_trial_days_left = serializers.SerializerMethodField()
    free_trial = serializers.SerializerMethodField()
    referrer_username = serializers.SerializerMethodField()
    
    class Meta:
        model = get_user_model()
        fields = ('is_profile_fill','id','first_name','last_name','email','phone_number','username','age',
                  'gender','address','organisation','description','profile_picture','updated_at','created_at',
                  'state','zip_code','country','language','time_zone','currency','business_type','default_reply_handler',
                  'wizard_complete','email_confirmed','email_confirmation_status','free_trial_days_left','free_trial',
                  'invite_code','referred_by','referrer_username','affiliate_active','wallet_balance','pass_correct')
    
    def get_referrer_username(self, obj):
        """Get the username of the user who referred this user"""
        if obj.referred_by:
            return obj.referred_by.username
        return None
    
    def get_email_confirmation_status(self, obj):
        """Get email confirmation status and details"""
        # Check for pending tokens
        pending_tokens = EmailConfirmationToken.objects.filter(
            user=obj,
            is_used=False
        )
        
        valid_tokens = [token for token in pending_tokens if token.is_valid()]
        
        return {
            'email_confirmed': obj.email_confirmed,
            'has_pending_confirmation': len(valid_tokens) > 0,
            'pending_tokens_count': len(valid_tokens),
            'confirmation_required': not obj.email_confirmed,
            'latest_token_expires_at': valid_tokens[0].expires_at.isoformat() if valid_tokens else None
        }
    
    def get_free_trial_days_left(self, obj):
        from billing.utils import free_trial_days_left_for_user
        return free_trial_days_left_for_user(obj)
    
    def get_free_trial(self, obj):
        from django.utils import timezone
        try:
            subscription = obj.subscription
            now = timezone.now()
            return (
                subscription.full_plan is not None
                and subscription.full_plan.name == 'Free Trial'
                and subscription.end_date is not None
                and now <= subscription.end_date
            )
        except Exception:
            return False

class UserSerializer(serializers.ModelSerializer):
    email_confirmation_status = serializers.SerializerMethodField()
    free_trial_days_left = serializers.SerializerMethodField()
    free_trial = serializers.SerializerMethodField()
    current_subscription = serializers.SerializerMethodField()
    subscription_remaining = serializers.SerializerMethodField()
    token_usage_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = get_user_model()
        fields = "__all__"
    
    def get_email_confirmation_status(self, obj):
        """Get email confirmation status and details"""
        # Check for pending tokens
        pending_tokens = EmailConfirmationToken.objects.filter(
            user=obj,
            is_used=False
        )
        
        valid_tokens = [token for token in pending_tokens if token.is_valid()]
        
        return {
            'email_confirmed': obj.email_confirmed,
            'has_pending_confirmation': len(valid_tokens) > 0,
            'pending_tokens_count': len(valid_tokens),
            'confirmation_required': not obj.email_confirmed,
            'latest_token_expires_at': valid_tokens[0].expires_at.isoformat() if valid_tokens else None,
            'can_resend_confirmation': not obj.email_confirmed
        }
    
    def get_free_trial_days_left(self, obj):
        from billing.utils import free_trial_days_left_for_user
        return free_trial_days_left_for_user(obj)
    
    def get_free_trial(self, obj):
        from django.utils import timezone
        try:
            subscription = obj.subscription
            now = timezone.now()
            return (
                subscription.full_plan is not None
                and subscription.full_plan.name == 'Free Trial'
                and subscription.end_date is not None
                and now <= subscription.end_date
            )
        except Exception:
            return False

    def get_current_subscription(self, obj):
        try:
            from billing.serializers import SubscriptionSerializer
            subscription = obj.subscription
            return SubscriptionSerializer(subscription).data
        except Exception:
            return None

    def get_subscription_remaining(self, obj):
        """Get subscription remaining as percentage (0-100)"""
        try:
            subscription = obj.subscription
            if subscription.is_subscription_active():
                days_remaining = subscription.days_remaining()
                if days_remaining is None:
                    return 100  # Unlimited subscription = 100%
                total_days = None
                if subscription.end_date and subscription.start_date:
                    total_days = (subscription.end_date - subscription.start_date).days
                if total_days and total_days > 0:
                    percentage = (days_remaining / total_days) * 100
                    return max(0, min(100, round(percentage, 1)))
                else:
                    return 100
            else:
                return 0
        except Exception:
            return 0

    def get_token_usage_remaining(self, obj):
        """Get token usage remaining as percentage (0-100) based on ACTUAL AI usage"""
        try:
            from billing.utils import get_accurate_tokens_remaining
            
            subscription = obj.subscription
            if subscription.is_subscription_active():
                # Use ACCURATE token calculation from actual AI usage
                original_tokens, consumed_tokens, tokens_remaining = get_accurate_tokens_remaining(obj)
                
                if original_tokens > 0:
                    percentage = (tokens_remaining / original_tokens) * 100
                    return max(0, min(100, round(percentage, 1)))
                else:
                    return 0
            else:
                return 0
        except Exception:
            return 0

class LoginSerializer(serializers.Serializer):
    email_or_username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email_or_username = data.get('email_or_username')
        password = data.get('password')
        
        if not email_or_username or not password:
            raise serializers.ValidationError("Email or username and password are required.")
        
        # Check if the input is an email format
        is_email = self._is_email(email_or_username)
        
        # Try to get user by email or username
        User = get_user_model()
        user = None
        
        try:
            if is_email:
                user = User.objects.get(email=email_or_username)
            else:
                user = User.objects.get(username=email_or_username)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email/username or password.")
        
        # Authenticate the user with their email (since USERNAME_FIELD is email)
        authenticated_user = authenticate(username=user.email, password=password)
        if authenticated_user is None:
            raise serializers.ValidationError("Invalid email/username or password.")
        
        try:
            access, refresh = login(authenticated_user)
        except Exception as e:
            raise serializers.ValidationError(f"Token generation error: {str(e)}")
        
        return {
            "refresh_token": refresh,
            "access_token": access,
            "user_data": UserShortSerializer(authenticated_user).data,
        }
    
    def _is_email(self, value):
        """Check if the value is a valid email format"""
        try:
            validate_email(value)
            return True
        except ValidationError:
            return False

class UserUpdateSerializer(serializers.ModelSerializer):
    email_confirmation_status = serializers.SerializerMethodField()
    free_trial_days_left = serializers.SerializerMethodField()
    free_trial = serializers.SerializerMethodField()
    
    class Meta:
        model = get_user_model()
        fields = ('first_name','last_name','age','gender','address','organisation','description','phone_number','state','zip_code','country','language','time_zone','currency','business_type','wizard_complete','email_confirmed','email_confirmation_status','free_trial_days_left','free_trial','pass_correct')
        read_only_fields = ('email_confirmed', 'free_trial_days_left', 'free_trial', 'pass_correct')  # These fields should be read-only
    
    def get_email_confirmation_status(self, obj):
        """Get email confirmation status and details"""
        # Check for pending tokens
        pending_tokens = EmailConfirmationToken.objects.filter(
            user=obj,
            is_used=False
        )
        
        valid_tokens = [token for token in pending_tokens if token.is_valid()]
        
        return {
            'email_confirmed': obj.email_confirmed,
            'has_pending_confirmation': len(valid_tokens) > 0,
            'pending_tokens_count': len(valid_tokens),
            'confirmation_required': not obj.email_confirmed,
            'latest_token_expires_at': valid_tokens[0].expires_at.isoformat() if valid_tokens else None,
            'can_resend_confirmation': not obj.email_confirmed
        }
    
    def get_free_trial_days_left(self, obj):
        from django.utils import timezone
        from math import ceil
        try:
            subscription = obj.subscription
            now = timezone.now()
            if (
                subscription.end_date
                and subscription.full_plan
                and subscription.full_plan.name == 'Free Trial'
                and now <= subscription.end_date
            ):
                remaining = subscription.end_date - now
                total_seconds = max(0, remaining.total_seconds())
                days_left = int(ceil(total_seconds / 86400))
                return f"{days_left} {'day' if days_left == 1 else 'days'} left"
        except Exception:
            pass
        return "0 days left"
    
    def get_free_trial(self, obj):
        from django.utils import timezone
        try:
            subscription = obj.subscription
            now = timezone.now()
            return (
                subscription.full_plan is not None
                and subscription.full_plan.name == 'Free Trial'
                and subscription.end_date is not None
                and now <= subscription.end_date
            )
        except Exception:
            return False

class UserOverviewSerializer(serializers.ModelSerializer):
    free_trial_days_left = serializers.SerializerMethodField()
    free_trial = serializers.SerializerMethodField()
    subscription_remaining = serializers.SerializerMethodField()
    token_usage_remaining = serializers.SerializerMethodField()
    response_rate_with_comparison = serializers.SerializerMethodField()
    user_conversations_count = serializers.SerializerMethodField()
    user_customers_count = serializers.SerializerMethodField()
    user_channels_count = serializers.SerializerMethodField()
    user_workflows_count = serializers.SerializerMethodField()
    all_conversations_count = serializers.SerializerMethodField()
    all_customers_count = serializers.SerializerMethodField()
    all_channels_count = serializers.SerializerMethodField()
    all_workflows_count = serializers.SerializerMethodField()
    
    class Meta:
        model = get_user_model()
        fields = (
            'id', 'created_at', 'free_trial_days_left', 'free_trial',
            'subscription_remaining', 'token_usage_remaining', 'response_rate_with_comparison',
            'current_subscription',
            'user_conversations_count', 'user_customers_count', 'user_channels_count', 'user_workflows_count',
            'all_conversations_count', 'all_customers_count', 'all_channels_count', 'all_workflows_count'
        )

    current_subscription = serializers.SerializerMethodField()
    
    def get_free_trial_days_left(self, obj):
        from billing.utils import free_trial_days_left_for_user
        return free_trial_days_left_for_user(obj)
    
    def get_free_trial(self, obj):
        from django.utils import timezone
        try:
            subscription = obj.subscription
            now = timezone.now()
            return (
                subscription.full_plan is not None
                and subscription.full_plan.name == 'Free Trial'
                and subscription.end_date is not None
                and now <= subscription.end_date
            )
        except Exception:
            return False
    
    def get_subscription_remaining(self, obj):
        """Get subscription remaining as percentage (0-100)"""
        try:
            subscription = obj.subscription
            if subscription.is_subscription_active():
                days_remaining = subscription.days_remaining()
                if days_remaining is None:
                    return 100  # Unlimited subscription = 100%
                
                # Calculate percentage based on subscription window if available
                total_days = None
                if subscription.end_date and subscription.start_date:
                    total_days = (subscription.end_date - subscription.start_date).days
                if total_days and total_days > 0:
                    percentage = (days_remaining / total_days) * 100
                    return max(0, min(100, round(percentage, 1)))  # Ensure 0-100 range
                else:
                    return 100  # No duration limit = 100%
            else:
                return 0  # Inactive subscription = 0%
        except:
            # Check if user has a legacy plan
            try:
                from accounts.models import Plan
                plan = Plan.objects.get(user=obj)
                # For legacy plans, assume they start with full allocation
                # Since we don't track original values, return current as percentage of some baseline
                # This is a fallback - ideally migrate to new subscription system
                return min(100, (plan.days / 30) * 100) if plan.days > 0 else 0
            except Plan.DoesNotExist:
                return 0
    
    def get_token_usage_remaining(self, obj):
        """Get token usage remaining as percentage (0-100) based on actual AI usage"""
        try:
            from AI_model.models import AIUsageLog
            from django.db.models import Sum
            
            subscription = obj.subscription
            if subscription.is_subscription_active():
                # Calculate original tokens from the plan
                original_tokens = 0
                if subscription.token_plan:
                    original_tokens = subscription.token_plan.tokens_included
                elif subscription.full_plan:
                    original_tokens = subscription.full_plan.tokens_included
                
                # Calculate actual AI tokens used since subscription started
                ai_tokens_used = AIUsageLog.objects.filter(
                    user=obj,
                    created_at__gte=subscription.start_date,
                    success=True
                ).aggregate(
                    total=Sum('total_tokens')
                )['total'] or 0
                
                # Calculate actual remaining tokens
                actual_tokens_remaining = max(0, original_tokens - ai_tokens_used)
                
                if original_tokens > 0:
                    percentage = (actual_tokens_remaining / original_tokens) * 100
                    return max(0, min(100, round(percentage, 1)))  # Ensure 0-100 range
                else:
                    return 0
            else:
                return 0  # Inactive subscription = 0%
        except:
            # Check if user has a legacy plan
            try:
                from accounts.models import Plan
                plan = Plan.objects.get(user=obj)
                # For legacy plans, assume they start with full allocation
                # Since we don't track original values, return current as percentage of some baseline
                baseline_tokens = 1000000  # 1M tokens baseline for legacy plans
                if plan.tokens > 0:
                    percentage = (plan.tokens / baseline_tokens) * 100
                    return min(100, round(percentage, 1))
                return 0
            except Plan.DoesNotExist:
                return 0
    
    def get_response_rate_with_comparison(self, obj):
        """Get response rate with comparison to previous period.
        Response rate = (Number of messages that received a response) / (Total incoming messages) × 100
        - Incoming message: A user message from social media (type='customer')
        - Response message: An AI-generated or human reply (is_answered=True)
        """
        try:
            from django.utils import timezone
            from datetime import timedelta
            from message.models import Message
            
            # Current period: last 30 days
            current_period_end = timezone.now()
            current_period_start = current_period_end - timedelta(days=30)
            
            # Get total incoming messages (customer messages) for current period
            current_incoming = Message.objects.filter(
                conversation__user=obj,
                type='customer',
                created_at__gte=current_period_start,
                created_at__lte=current_period_end
            ).count()
            
            # Get customer messages that received a response
            current_answered = Message.objects.filter(
                conversation__user=obj,
                type='customer',
                is_answered=True,
                created_at__gte=current_period_start,
                created_at__lte=current_period_end
            ).count()
            
            # Calculate current response rate
            if current_incoming > 0:
                current_rate = round((current_answered / current_incoming) * 100, 1)
            else:
                current_rate = 0.0
            
            return current_rate
            
        except Exception as e:
            return 0.0


    def get_current_subscription(self, obj):
        """
        Get subscription data with corrected tokens_remaining based on AI usage
        (same calculation as CurrentSubscriptionView and BillingOverviewView)
        """
        try:
            from billing.serializers import SubscriptionSerializer
            from billing.utils import get_accurate_tokens_remaining
            
            subscription = obj.subscription
            serializer = SubscriptionSerializer(subscription)
            data = serializer.data
            
            # Use centralized accurate token calculation
            original_tokens, consumed_tokens, tokens_remaining = get_accurate_tokens_remaining(obj)
            
            # Add AI usage information to the response
            data['ai_usage'] = {
                'total_tokens_consumed': consumed_tokens,
                'original_tokens_included': original_tokens,
                'actual_tokens_remaining': tokens_remaining,
                'tokens_remaining_in_db': subscription.tokens_remaining,  # Original field for comparison
            }
            
            # Update the main tokens_remaining field with actual remaining
            data['tokens_remaining'] = tokens_remaining
            
            return data
        except Exception:
            return None

    # --- Count fields ---
    def get_user_conversations_count(self, obj):
        try:
            from message.models import Conversation
            return Conversation.objects.filter(user=obj).count()
        except Exception:
            return 0

    def get_user_customers_count(self, obj):
        try:
            from message.models import Customer
            return Customer.objects.filter(conversations__user=obj).distinct().count()
        except Exception:
            return 0

    def get_user_channels_count(self, obj):
        # Derive channels from Conversation.source values for this user
        try:
            from message.models import Conversation
            return Conversation.objects.filter(user=obj).values_list('source', flat=True).distinct().count()
        except Exception:
            return 0

    def get_user_workflows_count(self, obj):
        try:
            from workflow.models import Workflow
            return Workflow.objects.filter(created_by=obj).count()
        except Exception:
            return 0

    def get_all_conversations_count(self, obj):
        try:
            from message.models import Conversation
            return Conversation.objects.all().count()
        except Exception:
            return 0

    def get_all_customers_count(self, obj):
        try:
            from message.models import Customer
            return Customer.objects.all().count()
        except Exception:
            return 0

    def get_all_channels_count(self, obj):
        # Derive channels from Conversation.source across all users
        try:
            from message.models import Conversation
            return Conversation.objects.values_list('source', flat=True).distinct().count()
        except Exception:
            return 0

    def get_all_workflows_count(self, obj):
        try:
            from workflow.models import Workflow
            return Workflow.objects.all().count()
        except Exception:
            return 0


class UserProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("profile_picture",)



class DefaultReplyHandlerSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("default_reply_handler",)


class WizardCompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("wizard_complete",)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        """Validate that the current password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        """Validate new password meets requirements"""
        # Minimum 8 characters long
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        # At least one lowercase character
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase character.")
        
        # At least one number, symbol, or whitespace character
        if not re.search(r'[\d\W]', value):
            raise serializers.ValidationError("Password must contain at least one number, symbol, or whitespace character.")
        
        return value

    def validate(self, data):
        """Validate that new password and confirm password match"""
        new_password = data.get('new_password')
        confirm_new_password = data.get('confirm_new_password')
        
        if new_password != confirm_new_password:
            raise serializers.ValidationError("New password and confirm password do not match.")
        
        return data

    def save(self):
        """Update the user's password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_deletion = serializers.CharField(write_only=True)

    def validate_password(self, value):
        """Validate that the password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value

    def validate_confirm_deletion(self, value):
        """Validate that user typed 'DELETE' to confirm deletion"""
        if value.upper() != 'DELETE':
            raise serializers.ValidationError("Please type 'DELETE' to confirm account deletion.")
        return value

    def save(self):
        """Delete the user account and related data"""
        user = self.context['request'].user
        
        # The user deletion will be handled in the view
        # to properly manage file cleanup and token invalidation
        return user
