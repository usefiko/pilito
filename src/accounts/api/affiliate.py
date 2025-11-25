from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.serializers import AffiliateSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class AffiliateInfoAPIView(APIView):
    """
    API endpoint for getting user's affiliate information including:
    - Invite link
    - Invite code
    - Direct referrals list
    - Total referrals count
    - Wallet balance
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get affiliate marketing information for the authenticated user",
        responses={
            200: openapi.Response(
                description="Affiliate information",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'invite_link': openapi.Schema(type=openapi.TYPE_STRING, description='Full invite link'),
                        'invite_code': openapi.Schema(type=openapi.TYPE_STRING, description='User invite code'),
                        'direct_referrals': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'username': openapi.Schema(type=openapi.TYPE_STRING),
                                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                                    'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                }
                            )
                        ),
                        'total_referrals': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total count of referrals'),
                        'wallet_balance': openapi.Schema(type=openapi.TYPE_STRING, description='Current wallet balance'),
                    }
                )
            ),
            401: 'Unauthorized'
        },
        tags=['Affiliate Marketing']
    )
    def get(self, request):
        """Get affiliate information for the authenticated user"""
        user = request.user
        serializer = AffiliateSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

