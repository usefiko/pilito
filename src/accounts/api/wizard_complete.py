from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.serializers import WizardCompleteSerializer
from rest_framework.permissions import IsAuthenticated
from settings.models import AIPrompts, InstagramChannel, TelegramChannel
import logging

logger = logging.getLogger(__name__)


class WizardCompleteAPIView(APIView):
    serializer_class = WizardCompleteSerializer
    permission_classes = [IsAuthenticated]

    def _check_wizard_requirements(self, user):
        """
        Check if user has completed all wizard requirements
        Returns: (is_complete: bool, missing_fields: list, details: dict)
        """
        missing_fields = []
        details = {
            'first_name': bool(user.first_name),
            'last_name': bool(user.last_name),
            'phone_number': bool(user.phone_number),
            'business_type': bool(user.business_type),
            'manual_prompt': False,
            'channel_connected': False,
        }
        
        # Check basic user fields
        if not user.first_name:
            missing_fields.append('first_name')
        if not user.last_name:
            missing_fields.append('last_name')
        if not user.phone_number:
            missing_fields.append('phone_number')
        if not user.business_type:
            missing_fields.append('business_type')
        
        # Check manual_prompt from AIPrompts
        try:
            ai_prompts = AIPrompts.objects.get(user=user)
            if ai_prompts.manual_prompt and ai_prompts.manual_prompt.strip():
                details['manual_prompt'] = True
            else:
                missing_fields.append('manual_prompt')
        except AIPrompts.DoesNotExist:
            missing_fields.append('manual_prompt')
        
        # Check if at least one channel (Instagram or Telegram) is connected
        instagram_connected = InstagramChannel.objects.filter(
            user=user, 
            is_connect=True
        ).exists()
        telegram_connected = TelegramChannel.objects.filter(
            user=user, 
            is_connect=True
        ).exists()
        
        if instagram_connected or telegram_connected:
            details['channel_connected'] = True
            details['instagram_connected'] = instagram_connected
            details['telegram_connected'] = telegram_connected
        else:
            missing_fields.append('channel_connected')
            details['instagram_connected'] = False
            details['telegram_connected'] = False
        
        is_complete = len(missing_fields) == 0
        
        return is_complete, missing_fields, details

    def patch(self, request, *args, **kwargs):
        """
        DEPRECATED: Wizard now auto-completes when all requirements are met.
        This endpoint is kept for backward compatibility only.
        
        The wizard is automatically completed by signals when:
        - User fills all required fields (first_name, last_name, phone, business_type)
        - Manual prompt is saved
        - At least one channel (Instagram/Telegram) is connected
        
        Frontend should now just check wizard_complete status via GET request.
        """
        user = request.user
        
        # Check all wizard requirements
        is_complete, missing_fields, details = self._check_wizard_requirements(user)
        
        # If already completed
        if user.wizard_complete:
            return Response({
                "success": True,
                "message": "Wizard already completed",
                "wizard_complete": True,
                "details": details
            }, status=status.HTTP_200_OK)
        
        # If can complete, do it manually (shouldn't happen as signals auto-complete)
        if is_complete:
            data = {"wizard_complete": True}
            serializer = self.serializer_class(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Wizard manually completed for user: {user.email}")
                return Response({
                    "success": True,
                    "message": "Wizard completed successfully",
                    "wizard_complete": True,
                    "details": details
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Requirements not met
        return Response({
            "success": False,
            "message": "Cannot complete wizard. Missing required fields.",
            "missing_fields": missing_fields,
            "details": details,
            "wizard_complete": False
        }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        """
        Get the current wizard_complete status with detailed requirements check
        """
        user = request.user
        
        # Check all wizard requirements
        is_complete, missing_fields, details = self._check_wizard_requirements(user)
        
        return Response({
            "wizard_complete": user.wizard_complete,
            "can_complete": is_complete,
            "missing_fields": missing_fields,
            "details": details
        }, status=status.HTTP_200_OK)


class WizardCompleteForceAPIView(APIView):
    """
    Force complete the wizard without checking any prerequisites.
    Sets wizard_complete to True directly.
    """
    serializer_class = WizardCompleteSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        """
        Force complete the wizard by setting wizard_complete to True
        without checking any prerequisites.
        """
        user = request.user
        
        # Set wizard_complete to True without any checks
        data = {"wizard_complete": True}
        serializer = self.serializer_class(user, data=data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Wizard force completed for user: {user.email}")
            return Response({
                "success": True,
                "message": "Wizard force completed successfully",
                "wizard_complete": True
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
