from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum
from .models import TokenPlan, FullPlan, Subscription, Payment, TokenUsage, Purchases
from .utils import enforce_account_deactivation_for_user

User = get_user_model()


class TokenPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for subscription plans
    """
    class Meta:
        model = TokenPlan
        fields = [
            'id', 'name', 'price_en', 'price_tr', 'price_ar', 'tokens_included', 
            'is_recurring', 'is_active', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FullPlanSerializer(serializers.ModelSerializer):
    user_has_active_subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = FullPlan
        fields = [
            'id', 'name', 'tokens_included', 'duration_days', 'is_recommended', 'is_yearly',
            'price_en', 'price_tr', 'price_ar', 'is_active', 'description', 
            'user_has_active_subscription', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_has_active_subscription(self, obj):
        """
        Check if the current user has an active subscription
        
        Returns:
            bool: True if user has active subscription, False otherwise
        """
        # Get user from request context
        request = self.context.get('request')
        
        # If no request (e.g., admin interface), return False
        if not request or not hasattr(request, 'user'):
            return False
        
        user = request.user
        
        # If user not authenticated, return False
        if not user or not user.is_authenticated:
            return False
        
        # Check if user has subscription
        try:
            subscription = user.subscription
            # Use the model's method to check if subscription is active
            return subscription.is_subscription_active()
        except Subscription.DoesNotExist:
            # User has no subscription
            return False
        except Exception:
            # Any other error, return False
            return False


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for user subscriptions
    """
    token_plan_details = TokenPlanSerializer(source='token_plan', read_only=True)
    full_plan_details = FullPlanSerializer(source='full_plan', read_only=True)
    queued_full_plan_details = FullPlanSerializer(source='queued_full_plan', read_only=True)
    queued_token_plan_details = TokenPlanSerializer(source='queued_token_plan', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_subscription_active = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_email', 
            'token_plan', 'token_plan_details', 
            'full_plan', 'full_plan_details', 
            'queued_full_plan', 'queued_full_plan_details',
            'queued_token_plan', 'queued_token_plan_details',
            'queued_tokens_amount',
            'start_date', 'end_date', 'tokens_remaining', 
            'is_active', 'status', 'trial_end', 'days_remaining',
            'is_subscription_active', 'cancel_at_period_end', 'canceled_at', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'canceled_at']

    def get_days_remaining(self, obj):
        return obj.days_remaining()

    def get_is_subscription_active(self, obj):
        return obj.is_subscription_active()


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for payments
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    plan_name = serializers.SerializerMethodField()
    subscription_id = serializers.IntegerField(source='subscription.id', read_only=True)
    is_subscription_canceled = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'subscription', 'subscription_id', 
            'token_plan', 'full_plan', 'plan_name', 'amount', 'payment_date', 'payment_method', 
            'status', 'transaction_id', 'payment_gateway_response', 
            'ref_id', 'authority', 'is_subscription_canceled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_plan_name(self, obj):
        if obj.token_plan:
            return obj.token_plan.name
        if obj.full_plan:
            return obj.full_plan.name
        return None
    
    def get_is_subscription_canceled(self, obj):
        """Check if the subscription for this payment is canceled"""
        if obj.subscription:
            return obj.subscription.cancel_at_period_end or obj.subscription.canceled_at is not None
        return False


class TokenUsageSerializer(serializers.ModelSerializer):
    """
    Serializer for token usage tracking
    """
    user_email = serializers.CharField(source='subscription.user.email', read_only=True)
    plan_name = serializers.CharField(source='subscription.plan.name', read_only=True)

    class Meta:
        model = TokenUsage
        fields = [
            'id', 'subscription', 'user_email', 'plan_name', 'used_tokens', 
            'usage_date', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PurchasePlanSerializer(serializers.Serializer):
    """
    Serializer for purchasing a plan
    """
    token_plan_id = serializers.IntegerField(required=False)
    full_plan_id = serializers.IntegerField(required=False)
    payment_method = serializers.ChoiceField(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        default='credit_card'
    )
    transaction_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        token_plan_id = attrs.get('token_plan_id')
        full_plan_id = attrs.get('full_plan_id')
        if bool(token_plan_id) == bool(full_plan_id):
            raise serializers.ValidationError("Provide exactly one of token_plan_id or full_plan_id.")
        if token_plan_id:
            try:
                TokenPlan.objects.get(id=token_plan_id, is_active=True)
            except TokenPlan.DoesNotExist:
                raise serializers.ValidationError({"token_plan_id": "Invalid or inactive token plan."})
        if full_plan_id:
            try:
                FullPlan.objects.get(id=full_plan_id, is_active=True)
            except FullPlan.DoesNotExist:
                raise serializers.ValidationError({"full_plan_id": "Invalid or inactive full plan."})
        return attrs


class ConsumeTokensSerializer(serializers.Serializer):
    """
    Serializer for consuming tokens
    """
    tokens = serializers.IntegerField(min_value=1)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_tokens(self, value):
        user = self.context['request'].user
        try:
            subscription = user.subscription
            if not subscription.is_subscription_active():
                raise serializers.ValidationError("No active subscription found.")
            if subscription.tokens_remaining < value:
                raise serializers.ValidationError(
                    f"Insufficient tokens. Available: {subscription.tokens_remaining}, Requested: {value}"
                )
        except Subscription.DoesNotExist:
            raise serializers.ValidationError("No subscription found.")
        return value


class UserSubscriptionOverviewSerializer(serializers.ModelSerializer):
    """
    Serializer for user subscription overview with AI usage tracking
    """
    current_subscription = serializers.SerializerMethodField()
    total_payments = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    tokens_used_today = serializers.SerializerMethodField()
    tokens_used_this_month = serializers.SerializerMethodField()
    ai_tokens_used_today = serializers.SerializerMethodField()
    ai_tokens_used_this_month = serializers.SerializerMethodField()
    ai_tokens_total = serializers.SerializerMethodField()
    original_tokens_included = serializers.SerializerMethodField()
    actual_tokens_remaining = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'current_subscription', 'total_payments', 
            'total_spent', 'tokens_used_today', 'tokens_used_this_month',
            'ai_tokens_used_today', 'ai_tokens_used_this_month', 'ai_tokens_total',
            'original_tokens_included', 'actual_tokens_remaining'
        ]

    def get_current_subscription(self, obj):
        """
        Get subscription data with corrected tokens_remaining based on AI usage
        (same calculation as CurrentSubscriptionView)
        """
        try:
            from AI_model.models import AIUsageLog
            
            subscription = obj.subscription
            serializer = SubscriptionSerializer(subscription)
            data = serializer.data
            
            # Calculate total AI tokens used by this user since subscription started
            ai_tokens_used = AIUsageLog.objects.filter(
                user=obj,
                created_at__gte=subscription.start_date,
                success=True  # Only count successful requests
            ).aggregate(
                total=Sum('total_tokens')
            )['total'] or 0
            
            # Calculate original tokens from the plan
            original_tokens = 0
            if subscription.token_plan:
                original_tokens = subscription.token_plan.tokens_included
            elif subscription.full_plan:
                original_tokens = subscription.full_plan.tokens_included
            
            # Calculate actual remaining tokens
            actual_tokens_remaining = max(0, original_tokens - ai_tokens_used)
            
            # Add AI usage information to the response
            data['ai_usage'] = {
                'total_tokens_consumed': ai_tokens_used,
                'original_tokens_included': original_tokens,
                'actual_tokens_remaining': actual_tokens_remaining,
                'tokens_remaining_in_db': subscription.tokens_remaining,  # Original field for comparison
            }
            
            # Update the main tokens_remaining field with actual remaining
            data['tokens_remaining'] = actual_tokens_remaining
            
            return data
            
        except Subscription.DoesNotExist:
            return None

    def get_total_payments(self, obj):
        return obj.payments.filter(status='completed').count()

    def get_total_spent(self, obj):
        total = obj.payments.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total']
        return float(total or 0)

    def get_tokens_used_today(self, obj):
        """Legacy: Get tokens from TokenUsage model"""
        try:
            today = timezone.now().date()
            return obj.subscription.token_usages.filter(
                usage_date__date=today
            ).aggregate(
                total=Sum('used_tokens')
            )['total'] or 0
        except Subscription.DoesNotExist:
            return 0

    def get_tokens_used_this_month(self, obj):
        """Legacy: Get tokens from TokenUsage model"""
        try:
            now = timezone.now()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return obj.subscription.token_usages.filter(
                usage_date__gte=start_of_month
            ).aggregate(
                total=Sum('used_tokens')
            )['total'] or 0
        except Subscription.DoesNotExist:
            return 0
    
    def get_ai_tokens_used_today(self, obj):
        """Get actual AI tokens used today from AIUsageLog"""
        from AI_model.models import AIUsageLog
        
        today = timezone.now().date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        
        return AIUsageLog.objects.filter(
            user=obj,
            created_at__gte=today_start,
            success=True
        ).aggregate(
            total=Sum('total_tokens')
        )['total'] or 0
    
    def get_ai_tokens_used_this_month(self, obj):
        """Get actual AI tokens used this month from AIUsageLog"""
        from AI_model.models import AIUsageLog
        
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return AIUsageLog.objects.filter(
            user=obj,
            created_at__gte=start_of_month,
            success=True
        ).aggregate(
            total=Sum('total_tokens')
        )['total'] or 0
    
    def get_ai_tokens_total(self, obj):
        """Get total AI tokens used since subscription started"""
        from AI_model.models import AIUsageLog
        
        try:
            subscription = obj.subscription
            return AIUsageLog.objects.filter(
                user=obj,
                created_at__gte=subscription.start_date,
                success=True
            ).aggregate(
                total=Sum('total_tokens')
            )['total'] or 0
        except Subscription.DoesNotExist:
            return 0
    
    def get_original_tokens_included(self, obj):
        """Get original tokens included in the plan"""
        try:
            subscription = obj.subscription
            if subscription.token_plan:
                return subscription.token_plan.tokens_included
            elif subscription.full_plan:
                return subscription.full_plan.tokens_included
            return 0
        except Subscription.DoesNotExist:
            return 0
    
    def get_actual_tokens_remaining(self, obj):
        """Calculate actual remaining tokens based on AI usage"""
        original_tokens = self.get_original_tokens_included(obj)
        ai_tokens_used = self.get_ai_tokens_total(obj)
        return max(0, original_tokens - ai_tokens_used)


# Legacy serializers for backward compatibility
class PlanSerializer(serializers.ModelSerializer):
    """
    Legacy serializer for old Plan model from accounts app
    """
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        from accounts.models import Plan
        model = Plan
        fields = ['id', 'user', 'user_email', 'days', 'tokens', 'emails', 'updated_at']
        read_only_fields = ['id', 'user', 'updated_at']


class PurchasesSerializer(serializers.ModelSerializer):
    """
    Legacy serializer for old Purchases model
    """
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Purchases
        fields = [
            'id', 'name', 'user', 'user_email', 'price', 'created_at', 
            'paid', 'description', 'ref_id', 'authority'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class ZarinpalPaymentSerializer(serializers.Serializer):
    """
    Serializer for Zarinpal payment initiation
    """
    token_plan_id = serializers.IntegerField(required=False, allow_null=True)
    full_plan_id = serializers.IntegerField(required=False, allow_null=True)
    language = serializers.ChoiceField(
        choices=['en', 'tr', 'ar'],
        default='en',
        help_text="Language for pricing selection"
    )

    def validate(self, attrs):
        token_plan_id = attrs.get('token_plan_id')
        full_plan_id = attrs.get('full_plan_id')
        
        # Ensure exactly one plan is selected
        if bool(token_plan_id) == bool(full_plan_id):
            raise serializers.ValidationError(
                "Provide exactly one of token_plan_id or full_plan_id."
            )
        
        # Validate token plan
        if token_plan_id:
            try:
                plan = TokenPlan.objects.get(id=token_plan_id, is_active=True)
                attrs['plan'] = plan
                attrs['plan_type'] = 'token'
            except TokenPlan.DoesNotExist:
                raise serializers.ValidationError({
                    "token_plan_id": "Invalid or inactive token plan."
                })
        
        # Validate full plan
        if full_plan_id:
            try:
                plan = FullPlan.objects.get(id=full_plan_id, is_active=True)
                attrs['plan'] = plan
                attrs['plan_type'] = 'full'
            except FullPlan.DoesNotExist:
                raise serializers.ValidationError({
                    "full_plan_id": "Invalid or inactive full plan."
                })
        
        return attrs

    def get_plan_price(self, plan, language='en'):
        """Get the price based on the selected language"""
        price_field = f'price_{language}'
        return getattr(plan, price_field, plan.price_en)