from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Send test emails using the beautiful Fiko templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test emails to',
            default='test@example.com'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['confirmation', 'reset', 'both'],
            help='Type of email to send',
            default='both'
        )

    def handle(self, *args, **options):
        email = options['email']
        email_type = options['type']
        
        self.stdout.write(
            self.style.SUCCESS('🎨 Testing Beautiful Fiko Email Templates')
        )
        self.stdout.write('=' * 50)
        
        success_count = 0
        
        if email_type in ['confirmation', 'both']:
            if self.send_confirmation_test(email):
                success_count += 1
        
        if email_type in ['reset', 'both']:
            if self.send_reset_test(email):
                success_count += 1
        
        self.stdout.write('=' * 50)
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'🎉 {success_count} email(s) sent successfully!')
            )
            self.stdout.write(
                self.style.WARNING(f'📧 Check {email} for the beautiful templates!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Failed to send test emails')
            )

    def send_confirmation_test(self, email):
        """Send test email confirmation"""
        self.stdout.write('🧪 Testing Email Confirmation Template...')
        
        # Sample confirmation code
        confirmation_code = ['4', '5', '5', '7', '8']
        user_name = "Test User"
        
        try:
            # Render HTML template
            html_message = render_to_string('emails/email_confirmation.html', {
                'user_email': email,
                'user_name': user_name,
                'confirmation_code': confirmation_code,
            })
            
            # Plain text version
            plain_message = f"""
Hello {user_name},

Thank you for joining Fiko! To complete your registration, please enter this confirmation code in the app:

{''.join(confirmation_code)}

Important:
- This code will expire in 15 minutes
- Enter this code in the app to complete your registration
- If you didn't create an account, please ignore this email

This is an automated message from Fiko.
If you need help, contact us at support@fiko.net
            """
            
            result = send_mail(
                subject='Email Confirmation - Fiko (TEST)',
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL_DISPLAY', 'Fiko <noreply@fiko.net>'),
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            if result > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Email confirmation sent to {email}')
                )
                self.stdout.write(f'📧 Confirmation code: {"".join(confirmation_code)}')
                return True
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Email sending returned 0')
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send confirmation email: {e}')
            )
            return False

    def send_reset_test(self, email):
        """Send test password reset email"""
        self.stdout.write('🧪 Testing Password Reset Template...')
        
        user_name = "Test User"
        reset_link = "https://app.fiko.net/auth/reset-password?token=test-token-123456"
        
        try:
            # Render HTML template
            html_message = render_to_string('emails/password_reset.html', {
                'user_name': user_name,
                'reset_link': reset_link,
            })
            
            # Plain text version
            plain_message = f"""
Hello {user_name},

You have requested to reset your password for your Fiko account.

Reset your password by clicking this link:
{reset_link}

Important:
- This link will expire in 1 hour
- You can only use this link once
- If you didn't request this, please ignore this email

This is an automated message from Fiko.
If you need help, contact us at support@fiko.net
            """
            
            result = send_mail(
                subject='Password Reset Request - Fiko (TEST)',
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL_DISPLAY', 'Fiko <noreply@fiko.net>'),
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            if result > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Password reset email sent to {email}')
                )
                self.stdout.write(f'🔗 Reset link: {reset_link}')
                return True
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Email sending returned 0')
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send reset email: {e}')
            )
            return False
