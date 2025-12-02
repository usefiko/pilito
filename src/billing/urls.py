from django.urls import path
from billing.api import CurrentPlanAPIView,Payment,PaymentVerify,PaymentHistory,ZPPayment,ZPVerify
from billing.api.affiliate import AffiliateStatsView, ToggleAffiliateSystemView
from billing.api.billing_withdraw import (
    BillingInformationView,
    CreateWithdrawView,
    WithdrawHistoryView,
    WithdrawDetailView
)
from .views import (
    TokenPlanListView, FullPlanListView, PlanListView, PurchasePlanView, CurrentSubscriptionView,
    ConsumeTokensView, UserPaymentHistoryView, UserSubscriptionHistoryView,
    UserTokenUsageHistoryView, BillingOverviewView, RefreshSubscriptionStatusView,
    LegacyPurchasesListView, LegacyPurchaseDetailView, StripeWebhookView,
    CreateCheckoutSessionView, CreateBillingPortalSessionView
)

urlpatterns = [
    # Affiliate/Referral System
    path('affiliate/stats/', AffiliateStatsView.as_view(), name='affiliate-stats'),
    path('affiliate/toggle/', ToggleAffiliateSystemView.as_view(), name='affiliate-toggle'),
    
    # Billing Information & Withdrawals
    path('billing-information/', BillingInformationView.as_view(), name='billing-information'),
    path('withdraw/', CreateWithdrawView.as_view(), name='create-withdraw'),
    path('withdraw/history/', WithdrawHistoryView.as_view(), name='withdraw-history'),
    path('withdraw/<int:pk>/', WithdrawDetailView.as_view(), name='withdraw-detail'),
    
    # New subscription system endpoints
    path('plans/', PlanListView.as_view(), name='plans'),
    path('plans/token/', TokenPlanListView.as_view(), name='token-plans'),
    path('plans/full/', FullPlanListView.as_view(), name='full-plans'),
    path('purchase/', PurchasePlanView.as_view(), name='purchase-plan'),
    path('subscription/', CurrentSubscriptionView.as_view(), name='current-subscription'),
    path('subscription/refresh/', RefreshSubscriptionStatusView.as_view(), name='refresh-subscription'),
    path('tokens/consume/', ConsumeTokensView.as_view(), name='consume-tokens'),
    path('stripe/checkout-session/', CreateCheckoutSessionView.as_view(), name='stripe-checkout-session'),
    path('stripe/customer-portal/', CreateBillingPortalSessionView.as_view(), name='stripe-portal'),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('payments/', UserPaymentHistoryView.as_view(), name='payment-history'),
    path('subscriptions/', UserSubscriptionHistoryView.as_view(), name='subscription-history'),
    path('tokens/usage/', UserTokenUsageHistoryView.as_view(), name='token-usage-history'),
    path('overview/', BillingOverviewView.as_view(), name='billing-overview'),
    path('legacy/purchases/', LegacyPurchasesListView.as_view(), name='legacy-purchases'),
    path('legacy/purchases/<int:pk>/', LegacyPurchaseDetailView.as_view(), name='legacy-purchase-detail'),
    # Legacy endpoints (keep for backward compatibility)
    path("current-plan", CurrentPlanAPIView.as_view(), name="current-plan"),
    path("payment", Payment.as_view(), name="payment"),
    path("payment-verify/<int:id>/", PaymentVerify.as_view(), name="payment-verify"),
    path("payment-history", PaymentHistory.as_view(), name="pay-history"),
    #Zarinpal
    path("zp-pay", ZPPayment.as_view(), name="zp-payment"),
    path("zp-verify/<int:id>/", ZPVerify.as_view(), name="zp-verify"),
]
