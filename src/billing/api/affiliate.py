"""
API endpoints for affiliate/referral system
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from decimal import Decimal
from accounts.models import User
from billing.models import Payment, WalletTransaction
from settings.models import AffiliationConfig


class AffiliateStatsView(APIView):
    """
    Get affiliate statistics for the current user
    
    Returns:
    - Total commission earned
    - Total amount from referrals' payments
    - Number of registrations via invite code
    - List of referred users with their payments and registration time
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Check if user has affiliate system active
        if not user.affiliate_active:
            return Response({
                'affiliate_active': False,
                'message': 'Affiliate system is not active for your account',
                'invite_code': user.invite_code
            })
        
        # Get all users referred by this user
        referred_users = User.objects.filter(referred_by=user).select_related()
        
        # Calculate total commission from wallet transactions
        total_commission = WalletTransaction.objects.filter(
            user=user,
            transaction_type='commission'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get all payments made by referred users (completed only)
        referred_payments = Payment.objects.filter(
            user__referred_by=user,
            status='completed'
        ).select_related('user')
        
        # Calculate total amount from referrals' payments
        total_amount_from_referrals = referred_payments.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Build list of referred users with their payment info
        referred_users_list = []
        for referred_user in referred_users:
            # Get all completed payments for this referred user
            user_payments = Payment.objects.filter(
                user=referred_user,
                status='completed'
            ).order_by('-created_at')
            
            # Calculate total paid by this user
            total_paid = user_payments.aggregate(total=Sum('amount'))['total'] or 0
            
            # Get commission earned from this specific user
            commission_from_user = WalletTransaction.objects.filter(
                user=user,
                referred_user=referred_user,
                transaction_type='commission'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Build payment history for this user
            payment_history = [{
                'payment_id': payment.id,
                'amount': float(payment.amount),
                'payment_date': payment.payment_date,
                'plan_name': payment.token_plan.name if payment.token_plan else (
                    payment.full_plan.name if payment.full_plan else 'N/A'
                )
            } for payment in user_payments[:10]]  # Limit to last 10 payments
            
            referred_users_list.append({
                'user_id': referred_user.id,
                'email': referred_user.email,
                'username': referred_user.username,
                'first_name': referred_user.first_name,
                'last_name': referred_user.last_name,
                'registered_at': referred_user.created_at,
                'total_paid': float(total_paid),
                'commission_earned_from_user': float(commission_from_user),
                'payment_count': user_payments.count(),
                'payments': payment_history
            })
        
        # Get affiliation config
        try:
            config = AffiliationConfig.get_config()
            commission_percentage = float(config.percentage)
        except:
            commission_percentage = 0.0
        
        # Build response
        response_data = {
            'affiliate_active': True,
            'invite_code': user.invite_code,
            'commission_percentage': commission_percentage,
            'stats': {
                'total_commission_earned': float(total_commission),
                'total_amount_from_referrals': float(total_amount_from_referrals),
                'total_registrations': referred_users.count(),
                'active_referrals': referred_users.filter(is_active=True).count(),
            },
            'referred_users': referred_users_list,
            'recent_commissions': self._get_recent_commissions(user)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _get_recent_commissions(self, user, limit=10):
        """Get recent commission transactions"""
        recent = WalletTransaction.objects.filter(
            user=user,
            transaction_type='commission'
        ).select_related('referred_user', 'related_payment')[:limit]
        
        return [{
            'transaction_id': trans.id,
            'amount': float(trans.amount),
            'from_user': {
                'email': trans.referred_user.email if trans.referred_user else None,
                'username': trans.referred_user.username if trans.referred_user else None,
            },
            'payment_amount': float(trans.related_payment.amount) if trans.related_payment else None,
            'date': trans.created_at,
            'description': trans.description,
            'balance_after': float(trans.balance_after)
        } for trans in recent]


class ToggleAffiliateSystemView(APIView):
    """
    Toggle affiliate system on/off for the current user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        action = request.data.get('action', 'toggle')  # 'toggle', 'enable', 'disable'
        
        if action == 'enable':
            user.affiliate_active = True
        elif action == 'disable':
            user.affiliate_active = False
        else:  # toggle
            user.affiliate_active = not user.affiliate_active
        
        user.save(update_fields=['affiliate_active', 'updated_at'])
        
        return Response({
            'success': True,
            'affiliate_active': user.affiliate_active,
            'invite_code': user.invite_code,
            'message': f"Affiliate system {'enabled' if user.affiliate_active else 'disabled'} successfully"
        }, status=status.HTTP_200_OK)

