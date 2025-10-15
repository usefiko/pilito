from rest_framework.views import APIView
from rest_framework.response import Response
from billing.serializers import PlanSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from accounts.models import Plan


class CurrentPlanAPIView(APIView):
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]
    def get(self, *args, **kwargs):
        try:
            plan = Plan.objects.get(user=self.request.user)
            serializer = self.serializer_class(plan)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response("Plan not found or something went wrong, try again", status=status.HTTP_400_BAD_REQUEST)