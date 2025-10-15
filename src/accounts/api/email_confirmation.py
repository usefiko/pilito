from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from accounts.models.user import EmailConfirmationToken
from accounts.utils import send_email_confirmation
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailConfirmationAPIView(APIView):
    """
    Confirm email address using OTP code
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response({
                'error': 'Confirmation code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        try:
            # Find valid token for this user
            token = EmailConfirmationToken.objects.get(
                user=user,
                code=code,
                is_used=False
            )
            
            if not token.is_valid():
                return Response({
                    'error': 'Confirmation code has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark token as used
            token.is_used = True
            token.save()
            
            # Mark user email as confirmed
            user.email_confirmed = True
            user.save()
            
            return Response({
                'message': 'Email confirmed successfully!',
                'email_confirmed': True
            }, status=status.HTTP_200_OK)
            
        except EmailConfirmationToken.DoesNotExist:
            return Response({
                'error': 'Invalid confirmation code'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Email confirmation error: {str(e)}")
            return Response({
                'error': 'An error occurred during confirmation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendEmailConfirmationAPIView(APIView):
    """
    Resend email confirmation code
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Check if email is already confirmed
        if user.email_confirmed:
            return Response({
                'message': 'Email is already confirmed'
            }, status=status.HTTP_200_OK)
        
        try:
            # Invalidate any existing tokens
            EmailConfirmationToken.objects.filter(
                user=user,
                is_used=False
            ).update(is_used=True)
            
            # Send new confirmation email
            email_sent, result = send_email_confirmation(user)
            
            if email_sent:
                return Response({
                    'message': 'Confirmation email sent successfully!',
                    'email_sent': True
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': f'Failed to send confirmation email: {result}',
                    'email_sent': False
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Resend email confirmation error: {str(e)}")
            return Response({
                'error': 'An error occurred while sending confirmation email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmailConfirmationStatusAPIView(APIView):
    """
    Check email confirmation status
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Check for pending tokens
        pending_tokens = EmailConfirmationToken.objects.filter(
            user=user,
            is_used=False
        )
        
        valid_tokens = [token for token in pending_tokens if token.is_valid()]
        
        return Response({
            'email_confirmed': user.email_confirmed,
            'email': user.email,
            'has_pending_confirmation': len(valid_tokens) > 0,
            'pending_tokens_count': len(valid_tokens)
        }, status=status.HTTP_200_OK)
