from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class ReferralUserSerializer(serializers.ModelSerializer):
    """Serializer for users who were referred (direct referrals)"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'created_at')
        read_only_fields = fields


class AffiliateSerializer(serializers.Serializer):
    """Serializer for affiliate marketing information"""
    invite_link = serializers.URLField(read_only=True)
    invite_code = serializers.CharField(read_only=True)
    direct_referrals = ReferralUserSerializer(many=True, read_only=True)
    total_referrals = serializers.IntegerField(read_only=True)
    wallet_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    def to_representation(self, instance):
        """Generate the affiliate data for the user"""
        # Build the invite link using the user's invite code
        from django.conf import settings
        base_url = getattr(settings, 'FRONTEND_URL', 'https://app.pilito.com')
        invite_link = f"{base_url}/auth/register?affiliate={instance.invite_code}"
        
        # Get all direct referrals
        direct_referrals = User.objects.filter(referred_by=instance).order_by('-created_at')
        
        return {
            'invite_link': invite_link,
            'invite_code': instance.invite_code,
            'direct_referrals': ReferralUserSerializer(direct_referrals, many=True).data,
            'total_referrals': direct_referrals.count(),
            'wallet_balance': str(instance.wallet_balance),
        }

