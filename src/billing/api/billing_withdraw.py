from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from billing.models import BillingInformation, Withdraw, WalletTransaction
from billing.serializers import (
    BillingInformationSerializer,
    WithdrawSerializer,
    CreateWithdrawSerializer
)


class BillingInformationView(APIView):
    """
    Get, create, or update billing information for the authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get user's billing information"""
        try:
            billing_info = request.user.billing_information
            serializer = BillingInformationSerializer(billing_info)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BillingInformation.DoesNotExist:
            return Response(
                {'message': 'No billing information found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        """Create billing information"""
        # Check if user already has billing information
        if hasattr(request.user, 'billing_information'):
            return Response(
                {'error': 'Billing information already exists. Use PUT to update.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BillingInformationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {
                    'message': 'Billing information created successfully',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """Update billing information"""
        try:
            billing_info = request.user.billing_information
        except BillingInformation.DoesNotExist:
            return Response(
                {'error': 'No billing information found. Use POST to create.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BillingInformationSerializer(
            billing_info,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Billing information updated successfully',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete billing information"""
        try:
            billing_info = request.user.billing_information
            billing_info.delete()
            return Response(
                {'message': 'Billing information deleted successfully'},
                status=status.HTTP_200_OK
            )
        except BillingInformation.DoesNotExist:
            return Response(
                {'error': 'No billing information found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CreateWithdrawView(APIView):
    """
    Create a withdrawal request
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """Create a withdrawal request"""
        serializer = CreateWithdrawSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']
        user = request.user

        # Create withdrawal request
        withdraw = Withdraw.objects.create(
            user=user,
            amount=amount,
            status='pending'
        )

        # Deduct amount from wallet and create transaction record
        user.wallet_balance -= Decimal(str(amount))
        user.save(update_fields=['wallet_balance', 'updated_at'])

        # Create wallet transaction
        wallet_transaction = WalletTransaction.objects.create(
            user=user,
            transaction_type='withdrawal',
            amount=-Decimal(str(amount)),
            balance_after=user.wallet_balance,
            description=f"Withdrawal request #{withdraw.id} - {amount} Tomans"
        )

        # Link transaction to withdrawal
        withdraw.wallet_transaction = wallet_transaction
        withdraw.save(update_fields=['wallet_transaction'])

        return Response(
            {
                'message': 'Withdrawal request created successfully',
                'data': WithdrawSerializer(withdraw).data
            },
            status=status.HTTP_201_CREATED
        )


class WithdrawHistoryView(generics.ListAPIView):
    """
    Get withdrawal history for the authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WithdrawSerializer

    def get_queryset(self):
        """Return withdrawals for the current user"""
        return Withdraw.objects.filter(user=self.request.user).order_by('-created_at')


class WithdrawDetailView(APIView):
    """
    Get details of a specific withdrawal request
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Get withdrawal details"""
        try:
            withdraw = Withdraw.objects.get(pk=pk, user=request.user)
            serializer = WithdrawSerializer(withdraw)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Withdraw.DoesNotExist:
            return Response(
                {'error': 'Withdrawal request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

