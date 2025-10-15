from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from billing.serializers import PurchasesSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from billing.models import Purchases


class PaymentHistory(APIView):
    serializer_class = PurchasesSerializer
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        try:
            purchases = Purchases.objects.filter(user=self.request.user).order_by('-created_at')
            serializer = self.serializer_class(purchases, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f"error: {str(e)}", status=status.HTTP_400_BAD_REQUEST)
