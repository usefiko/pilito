from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Test email sending functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to',
            required=True
        )
        parser.add_argument(
            '--backend',
            type=str,
            help='Email backend to use (console, smtp)',
            default='current'
        )

    def handle(self, *args, **options):
        email = options['email']
        backend = options['backend']
        
        self.stdout.write(f"🧪 Testing email functionality...")
        self.stdout.write(f"📧 Target email: {email}")
        
        # Show current email configuration
        self.stdout.write(f"⚙️  Current EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        if hasattr(settings, 'EMAIL_HOST'):
            self.stdout.write(f"📮 EMAIL_HOST: {settings.EMAIL_HOST}")
            self.stdout.write(f"🔌 EMAIL_PORT: {settings.EMAIL_PORT}")
            self.stdout.write(f"🔐 EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
            self.stdout.write(f"👤 EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        
        # Override backend if requested
        original_backend = settings.EMAIL_BACKEND
        if backend == 'console':
            settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
        elif backend == 'smtp':
            settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
            
        self.stdout.write(f"🔄 Using EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        
        try:
            # Test basic email sending
            subject = 'Test Email from Fiko Backend'
            message = '''
            Hello!
            
            This is a test email from the Fiko backend to verify email functionality.
            
            If you received this email, the email configuration is working correctly!
            
            Timestamp: {timestamp}
            Backend: {backend}
            
            Best regards,
            Fiko Team
            '''.format(
                timestamp=__import__('datetime').datetime.now().isoformat(),
                backend=settings.EMAIL_BACKEND
            )
            
            result = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            if result > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Email sent successfully! ({result} emails sent)")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️  Email sending returned 0 (no emails sent)")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Email sending failed: {str(e)}")
            )
            
            # Provide specific error guidance
            error_str = str(e).lower()
            if "authentication" in error_str:
                self.stdout.write(
                    self.style.ERROR("💡 Hint: Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
                )
            elif "550" in error_str:
                self.stdout.write(
                    self.style.ERROR("💡 Hint: Sender email may not be verified in AWS SES")
                )
            elif "timeout" in error_str:
                self.stdout.write(
                    self.style.ERROR("💡 Hint: Network timeout - check EMAIL_HOST and EMAIL_PORT")
                )
        
        finally:
            # Restore original backend
            settings.EMAIL_BACKEND = original_backend
            
        self.stdout.write("🏁 Email test completed!")
