from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from accounts.serializers.password_reset import ForgetPasswordSerializer, ResetPasswordSerializer
from accounts.models import PasswordResetToken
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class ForgetPasswordAPIView(APIView):
    """
    API endpoint for requesting password reset
    """
    permission_classes = []
    
    def post(self, request):
        serializer = ForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Invalidate any existing reset tokens for this user
                PasswordResetToken.objects.filter(
                    user=user, 
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).update(is_used=True)
                
                # Create new reset token
                reset_token = PasswordResetToken.objects.create(user=user)
                
                # Generate reset link (you'll need to configure your frontend URL)
                frontend_url = getattr(settings, 'FRONTEND_URL', 'https://app.pilito.com')
                reset_link = f"{frontend_url}/auth/reset-password?token={reset_token.token}"
                
                # Send email
                subject = "Password Reset Request - Fiko"
                
                # Render HTML email template
                html_message = render_to_string('emails/password_reset.html', {
                    'user_name': user.first_name or user.username,
                    'reset_link': reset_link,
                })
                
                # Plain text version for email clients that don't support HTML
                plain_message = f"""
Hello {user.first_name or user.username},

You have requested to reset your password for your Fiko account.

Reset your password by clicking this link:
{reset_link}

Important:
- This link will expire in 1 hour
- You can only use this link once
- If you didn't request this, please ignore this email

This is an automated message from Fiko.
If you need help, contact us at support@pilito.com
                """
                
                try:
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL_DISPLAY', 'Pilito <noreply@mail.pilito.com>'),
                        recipient_list=[email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    logger.info(f"Password reset email sent to {email}")
                    
                except Exception as e:
                    logger.error(f"Failed to send password reset email to {email}: {e}")
                    return Response(
                        {"error": "Failed to send reset email. Please try again later."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
            except User.DoesNotExist:
                # For security reasons, we don't reveal if an email exists or not
                logger.info(f"Password reset requested for non-existent email: {email}")
            
            # Always return success response to prevent email enumeration
            return Response(
                {"message": "If your email is registered, you'll receive a reset link shortly."},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordAPIView(APIView):
    """
    API endpoint for resetting password with token
    """
    permission_classes = []
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                reset_token = PasswordResetToken.objects.get(token=token)
                
                if not reset_token.is_valid():
                    return Response(
                        {"error": "Reset token is invalid or has expired."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Reset the password
                user = reset_token.user
                user.set_password(new_password)
                user.save()
                
                # Mark token as used
                reset_token.is_used = True
                reset_token.save()
                
                logger.info(f"Password reset successful for user: {user.email}")
                
                return Response(
                    {"message": "Password has been reset successfully."},
                    status=status.HTTP_200_OK
                )
                
            except PasswordResetToken.DoesNotExist:
                return Response(
                    {"error": "Invalid reset token."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
