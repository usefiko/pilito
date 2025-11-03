from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import timedelta
import json
import logging

# Initialize logger
logger = logging.getLogger(__name__)

try:
    import stripe
except Exception:  # pragma: no 
    stripe = None

from .models import TokenPlan, FullPlan, Subscription, Payment, TokenUsage, Purchases
from .utils import enforce_account_deactivation_for_user
from .serializers import (
    TokenPlanSerializer, FullPlanSerializer, SubscriptionSerializer, PaymentSerializer,
    TokenUsageSerializer, PurchasePlanSerializer, ConsumeTokensSerializer,
    UserSubscriptionOverviewSerializer, PurchasesSerializer
)

User = get_user_model()


class TokenPlanListView(generics.ListAPIView):
    """
    List all available subscription plans
    """
    queryset = TokenPlan.objects.filter(is_active=True)
    serializer_class = TokenPlanSerializer
    permission_classes = [IsAuthenticated]


class FullPlanListView(generics.ListAPIView):
    queryset = FullPlan.objects.filter(is_active=True)
    serializer_class = FullPlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        """
        Pass request context to serializer
        This allows serializer to access current user for user_has_active_subscription field
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PlanListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token_plans = TokenPlanSerializer(TokenPlan.objects.filter(is_active=True), many=True).data
        full_plans = FullPlanSerializer(FullPlan.objects.filter(is_active=True), many=True).data
        return Response({
            'token_plans': token_plans,
            'full_plans': full_plans
        })


class PurchasePlanView(APIView):
    """
    Purchase a subscription plan
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PurchasePlanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token_plan_id = serializer.validated_data.get('token_plan_id')
        full_plan_id = serializer.validated_data.get('full_plan_id')
        payment_method = serializer.validated_data['payment_method']
        transaction_id = serializer.validated_data.get('transaction_id', '')

        selected_token_plan = None
        selected_full_plan = None
        amount = None
        if token_plan_id:
            try:
                selected_token_plan = TokenPlan.objects.get(id=token_plan_id, is_active=True)
                amount = selected_token_plan.price
            except TokenPlan.DoesNotExist:
                return Response({'error': 'Invalid or inactive token plan'}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                selected_full_plan = FullPlan.objects.get(id=full_plan_id, is_active=True)
                amount = selected_full_plan.price
            except FullPlan.DoesNotExist:
                return Response({'error': 'Invalid or inactive full plan'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            # Create payment record (pending)
            payment = Payment.objects.create(
                user=request.user,
                token_plan=selected_token_plan,
                full_plan=selected_full_plan,
                amount=amount,
                payment_method=payment_method,
                status='pending',
                transaction_id=None
            )

            if payment_method == 'stripe':
                if stripe is None:
                    return Response({'error': 'Stripe SDK not installed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                if not getattr(settings, 'STRIPE_SECRET_KEY', None):
                    return Response({'error': 'Stripe secret key not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                stripe.api_key = settings.STRIPE_SECRET_KEY

                intent = stripe.PaymentIntent.create(
                    amount=int(float(amount) * 100),
                    currency=getattr(settings, 'STRIPE_CURRENCY', 'usd'),
                    metadata={
                        'payment_id': str(payment.id),
                        'user_id': str(request.user.id),
                        'token_plan_id': str(selected_token_plan.id) if selected_token_plan else '',
                        'full_plan_id': str(selected_full_plan.id) if selected_full_plan else ''
                    }
                )
                payment.transaction_id = intent.id
                payment.save()
                return Response({
                    'message': 'Stripe payment initiated',
                    'payment_id': payment.id,
                    'client_secret': intent.client_secret
                }, status=status.HTTP_201_CREATED)
            else:
                # For non-Stripe payments (legacy support only)
                # WARNING: This is for backward compatibility with legacy payment systems
                # For production, only Stripe should be used
                logger.warning(f"Non-Stripe payment method used: {payment_method} by user {request.user.username}")
                
                # Mark payment as pending - it should be verified through legacy system
                payment.status = 'pending'
                payment.save()
                
                return Response({
                    'message': 'Legacy payment method - please use Stripe for new purchases',
                    'payment_id': payment.id,
                    'note': 'Please contact support for legacy payment verification'
                }, status=status.HTTP_400_BAD_REQUEST)


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if stripe is None:
            logger.error("Stripe SDK not installed")
            return Response({'error': 'Stripe SDK not installed'}, status=400)
        
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        
        if not webhook_secret:
            logger.error("STRIPE_WEBHOOK_SECRET not configured in settings")
            return Response({'error': 'Webhook secret not configured'}, status=400)
        
        try:
            event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=webhook_secret)
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return Response({'error': 'Invalid payload'}, status=400)
        except stripe._error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            logger.error(f"Signature header received: {sig_header[:50] if sig_header else 'EMPTY'}")
            return Response({'error': 'Invalid signature'}, status=400)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return Response({'error': str(e)}, status=400)

        if event['type'] == 'payment_intent.succeeded':
            intent = event['data']['object']
            transaction_id = intent.get('id')
            try:
                payment = Payment.objects.select_related('user').get(transaction_id=transaction_id, status='pending')
            except Payment.DoesNotExist:
                return Response(status=200)

            with transaction.atomic():
                payment.status = 'completed'
                payment.payment_gateway_response = intent
                payment.save()

                # Create or update subscription for the user
                user = payment.user
                selected_token_plan = payment.token_plan
                selected_full_plan = payment.full_plan

                subscription, created = Subscription.objects.get_or_create(
                    user=user,
                    defaults={
                        'token_plan': selected_token_plan,
                        'full_plan': selected_full_plan,
                        'tokens_remaining': (selected_token_plan or selected_full_plan).tokens_included,
                        'start_date': timezone.now(),
                        'is_active': True
                    }
                )

                if not created:
                    # Use professional subscription update logic
                    from billing.services.stripe_service import StripeService
                    tokens_included = (selected_token_plan or selected_full_plan).tokens_included
                    subscription = StripeService._update_subscription_professional(
                        subscription=subscription,
                        selected_token_plan=selected_token_plan,
                        selected_full_plan=selected_full_plan,
                        tokens_included=tokens_included,
                        stripe_customer_id=intent.get('customer', ''),
                        stripe_subscription_id=None  # payment_intent doesn't have subscription ID
                    )

                payment.subscription = subscription
                payment.save()

            return Response(status=200)

        if event['type'] == 'payment_intent.payment_failed':
            intent = event['data']['object']
            transaction_id = intent.get('id')
            try:
                payment = Payment.objects.get(transaction_id=transaction_id)
                payment.status = 'failed'
                payment.payment_gateway_response = intent
                payment.save()
            except Payment.DoesNotExist:
                pass
            return Response(status=200)

        # Handle subscription lifecycle events
        if event['type'] == 'checkout.session.completed':
            from billing.services import StripeService
            
            session = event['data']['object']
            session_id = session.get('id')
            
            # Use StripeService to handle the successful payment
            success = StripeService.handle_successful_payment(session_id)
            if success:
                logger.info(f"Successfully processed checkout session {session_id}")
            else:
                logger.error(f"Failed to process checkout session {session_id}")
            
            return Response(status=200)

        if event['type'] == 'invoice.paid':
            invoice = event['data']['object']
            customer_id = invoice.get('customer')
            try:
                sub = Subscription.objects.get(stripe_customer_id=customer_id)
                sub.status = 'active'
                sub.is_active = True
                sub.save()
            except Subscription.DoesNotExist:
                pass
            return Response(status=200)

        if event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            customer_id = invoice.get('customer')
            try:
                sub = Subscription.objects.get(stripe_customer_id=customer_id)
                sub.status = 'past_due'
                # Don't immediately deactivate - use controlled deactivation
                # sub.is_active = False
                logger.warning(f"Invoice payment failed for customer {customer_id}")
                sub.save()
            except Subscription.DoesNotExist:
                pass
            return Response(status=200)

        # Handle subscription updates (including cancellation scheduling)
        if event['type'] == 'customer.subscription.updated':
            stripe_sub = event['data']['object']
            subscription_id = stripe_sub.get('id')
            cancel_at_period_end = stripe_sub.get('cancel_at_period_end', False)
            status_stripe = stripe_sub.get('status')
            
            try:
                sub = Subscription.objects.get(stripe_subscription_id=subscription_id)
                
                # Update cancel_at_period_end flag
                sub.cancel_at_period_end = cancel_at_period_end
                
                # Update status
                if status_stripe in ['active', 'trialing', 'past_due', 'unpaid', 'canceled', 'incomplete', 'incomplete_expired']:
                    sub.status = status_stripe
                
                # If canceled, mark the time
                if cancel_at_period_end and not sub.canceled_at:
                    sub.canceled_at = timezone.now()
                    logger.info(f"Subscription {subscription_id} scheduled for cancellation at period end")
                
                # If cancellation was reverted
                if not cancel_at_period_end and sub.canceled_at:
                    sub.canceled_at = None
                    logger.info(f"Subscription {subscription_id} cancellation reverted")
                
                sub.save()
                logger.info(f"Subscription {subscription_id} updated via Stripe webhook")
            except Subscription.DoesNotExist:
                logger.warning(f"Subscription {subscription_id} not found in database")
            
            return Response(status=200)
        
        # Handle subscription deletion (immediate cancellation)
        if event['type'] in ('customer.subscription.deleted', 'customer.subscription.canceled'):
            stripe_sub = event['data']['object']
            subscription_id = stripe_sub.get('id')
            try:
                sub = Subscription.objects.get(stripe_subscription_id=subscription_id)
                # Use controlled deactivation
                sub.deactivate_subscription(
                    reason=f'Stripe subscription {event["type"]}'
                )
                sub.status = 'canceled'
                sub.is_active = False
                sub.canceled_at = timezone.now()
                sub.cancel_at_period_end = False
                sub.save()
                logger.info(f"Subscription {subscription_id} cancelled via Stripe webhook")
            except Subscription.DoesNotExist:
                logger.warning(f"Subscription {subscription_id} not found in database")
            return Response(status=200)

        return Response(status=200)


class CreateCheckoutSessionView(APIView):
    """
    Create a Stripe Checkout Session for purchasing plans
    
    POST /billing/stripe/checkout-session/
    Body: {
        "plan_type": "token" | "full",
        "plan_id": 123,
        "success_url": "https://yoursite.com/success" (optional),
        "cancel_url": "https://yoursite.com/cancel" (optional)
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from billing.services import StripeService
        
        if not getattr(settings, 'STRIPE_ENABLED', False):
            return Response({'error': 'Stripe is not enabled'}, status=status.HTTP_400_BAD_REQUEST)
        
        plan_type = request.data.get('plan_type')
        plan_id = request.data.get('plan_id')
        success_url = request.data.get('success_url')
        cancel_url = request.data.get('cancel_url')

        if not plan_type or not plan_id:
            return Response({
                'error': 'plan_type and plan_id are required',
                'example': {
                    'plan_type': 'full',  # or 'token'
                    'plan_id': 1
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if plan_type not in ['token', 'full']:
            return Response({
                'error': 'plan_type must be either "token" or "full"'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            session_id, checkout_url = StripeService.create_checkout_session(
                user=request.user,
                plan_type=plan_type,
                plan_id=plan_id,
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            if not session_id:
                return Response({
                    'error': checkout_url or 'Failed to create checkout session'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'session_id': session_id,
                'url': checkout_url,
                'message': 'Checkout session created successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CreateBillingPortalSessionView(APIView):
    """
    Create a Stripe Customer Portal Session for subscription management
    
    POST /billing/stripe/customer-portal/
    Body: {
        "return_url": "https://yoursite.com/billing" (optional)
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from billing.services import StripeService
        
        if not getattr(settings, 'STRIPE_ENABLED', False):
            return Response({'error': 'Stripe is not enabled'}, status=status.HTTP_400_BAD_REQUEST)
        
        return_url = request.data.get('return_url')

        try:
            portal_url = StripeService.create_customer_portal_session(
                user=request.user,
                return_url=return_url
            )
            
            if not portal_url:
                return Response({
                    'error': 'Failed to create customer portal session'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'url': portal_url,
                'message': 'Portal session created successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error creating portal session: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CurrentSubscriptionView(APIView):
    """
    Get current user's subscription details with actual remaining tokens
    based on AI usage consumption
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            subscription = request.user.subscription
            serializer = SubscriptionSerializer(subscription)
            data = serializer.data
            
            # Import AIUsageLog to calculate actual token consumption
            from AI_model.models import AIUsageLog
            
            # Calculate total AI tokens used by this user since subscription started
            ai_tokens_used = AIUsageLog.objects.filter(
                user=request.user,
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
            
            return Response(data, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response(
                {'message': 'No active subscription found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ConsumeTokensView(APIView):
    """
    Consume tokens from user's subscription
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConsumeTokensSerializer(
            data=request.data, 
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        tokens = serializer.validated_data['tokens']
        description = serializer.validated_data.get('description', '')

        try:
            subscription = request.user.subscription
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'No subscription found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        if not subscription.is_subscription_active():
            return Response(
                {'error': 'Subscription is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if subscription.tokens_remaining < tokens:
            return Response(
                {'error': f'Insufficient tokens. Available: {subscription.tokens_remaining}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Deduct tokens
            subscription.tokens_remaining -= tokens
            subscription.save()

            # Create usage record
            TokenUsage.objects.create(
                subscription=subscription,
                used_tokens=tokens,
                description=description
            )

        return Response({
            'message': 'Tokens consumed successfully',
            'tokens_consumed': tokens,
            'tokens_remaining': subscription.tokens_remaining,
            'subscription_active': subscription.is_subscription_active()
        }, status=status.HTTP_200_OK)


class UserPaymentHistoryView(generics.ListAPIView):
    """
    List user's payment history
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


class UserSubscriptionHistoryView(generics.ListAPIView):
    """
    List user's subscription history
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class UserTokenUsageHistoryView(generics.ListAPIView):
    """
    List user's token usage history
    """
    serializer_class = TokenUsageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            subscription = self.request.user.subscription
            return TokenUsage.objects.filter(subscription=subscription)
        except Subscription.DoesNotExist:
            return TokenUsage.objects.none()


class BillingOverviewView(APIView):
    """
    Get comprehensive billing overview for user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSubscriptionOverviewSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RefreshSubscriptionStatusView(APIView):
    """
    Manually refresh subscription status (check expiration, etc.)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = request.user.subscription
            
            # Check if subscription should be deactivated
            if not subscription.is_subscription_active():
                # Use the new controlled deactivation method with proper logging
                subscription.deactivate_subscription(
                    reason='Manual refresh requested - subscription no longer meets active criteria'
                )
                
            serializer = SubscriptionSerializer(subscription)
            return Response({
                'message': 'Subscription status refreshed',
                'subscription': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Subscription.DoesNotExist:
            return Response(
                {'message': 'No subscription found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


# Legacy views for backward compatibility
class LegacyPurchasesListView(generics.ListCreateAPIView):
    """
    Legacy view for old Purchases model
    """
    serializer_class = PurchasesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Purchases.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LegacyPurchaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Legacy view for individual purchase records
    """
    serializer_class = PurchasesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Purchases.objects.filter(user=self.request.user)
