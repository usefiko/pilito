from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from accounts.models.user import EmailConfirmationToken
import logging

logger = logging.getLogger(__name__)


def send_email_confirmation(user):
    """
    Send email confirmation code to user
    """
    # Create or get existing token
    token, created = EmailConfirmationToken.objects.get_or_create(
        user=user,
        is_used=False,
        defaults={}
    )
    
    if not created:
        # If token already exists, update it with new code and expiry
        token.save()  # This will regenerate code and expiry
    
    # Email subject and message
    subject = 'Email Confirmation - Fiko'
    
    # Convert code to individual digits for template
    confirmation_code = list(str(token.code))
    
    # Render HTML email template
    html_message = render_to_string('emails/email_confirmation.html', {
        'user_email': user.email,
        'user_name': user.first_name or user.username,
        'confirmation_code': confirmation_code,
    })
    
    # Plain text version
    plain_message = f"""
    Welcome to Fiko!
    
    Hello {user.first_name or user.email},
    
    Thank you for signing up! Please use the confirmation code below to verify your email address:
    
    Confirmation Code: {token.code}
    
    Important:
    - This code will expire in 15 minutes
    - Enter this code in the app to complete your registration
    - If you didn't create an account, please ignore this email
    
    This is an automated message from Fiko.
    If you need help, contact us at support@pilito.com
    """
    
    try:
        logger.info(f"Attempting to send email confirmation to {user.email}")
        logger.info(f"Using SMTP settings - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}, From: {settings.DEFAULT_FROM_EMAIL}")
        
        # Try to send email
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL_DISPLAY', 'Pilito <noreply@mail.pilito.com>'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        if result > 0:
            logger.info(f"✅ Email successfully sent to {user.email}. Result: {result}")
            return True, token.code
        else:
            logger.warning(f"⚠️ Email sending returned 0 for {user.email}")
            return False, "Email sending returned 0 (no emails sent)"
            
    except Exception as e:
        # Log the detailed error with full traceback
        logger.error(f"❌ Email sending failed for user {user.email}: {str(e)}", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        
        # Return detailed error information
        error_msg = str(e)
        if "Authentication" in error_msg or "authentication" in error_msg.lower():
            error_msg = f"SMTP authentication failed. Please check Liara credentials. Original error: {error_msg}"
            logger.error(f"🔐 Authentication error detected")
        elif "550" in error_msg:
            error_msg = f"Email rejected by server. The sender email may not be verified in Liara. Original error: {error_msg}"
            logger.error(f"📧 Email verification error detected")
        elif "timeout" in error_msg.lower():
            error_msg = f"Email server timeout. Please try again later. Original error: {error_msg}"
            logger.error(f"⏱️ Timeout error detected")
        elif "Connection refused" in error_msg:
            error_msg = f"Connection refused by SMTP server. Check host/port settings. Original error: {error_msg}"
            logger.error(f"🔌 Connection refused error detected")
        else:
            logger.error(f"🔥 Unknown error: {error_msg}")
        
        return False, error_msg
