from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.serializers import WizardCompleteSerializer
from rest_framework.permissions import IsAuthenticated


class WizardCompleteAPIView(APIView):
    serializer_class = WizardCompleteSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        """
        Update the wizard_complete field to True for the authenticated user
        """
        # Set wizard_complete to True
        data = {"wizard_complete": True}
        
        serializer = self.serializer_class(request.user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Wizard completed successfully", "wizard_complete": True}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        """
        Get the current wizard_complete status for the authenticated user
        """
        return Response(
            {"wizard_complete": request.user.wizard_complete}, 
            status=status.HTTP_200_OK
        )
