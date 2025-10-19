from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test Liara Email SMTP configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='mamadbayat777@gmail.com',
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        test_email = options['email']
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("🚀 Testing Liara Email SMTP Configuration"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
        self.stdout.write(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL_DISPLAY: {settings.DEFAULT_FROM_EMAIL_DISPLAY}")
        self.stdout.write(f"Test recipient: {test_email}")
        self.stdout.write("-" * 60)
        
        # Test 1: Simple text email
        self.stdout.write("\n" + self.style.WARNING("📧 Test 1: Sending simple text email..."))
        try:
            result = send_mail(
                subject='Test Email from Liara SMTP - Pilito',
                message='This is a test email to verify Liara SMTP configuration is working correctly.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[test_email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Simple email sent successfully! Result: {result}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Simple email failed!"))
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Simple email test failed: {str(e)}", exc_info=True)
        
        # Test 2: HTML email with template
        self.stdout.write("\n" + self.style.WARNING("📧 Test 2: Sending HTML email with password reset template..."))
        try:
            html_message = render_to_string('emails/password_reset.html', {
                'user_name': 'Test User',
                'reset_link': 'https://app.pilito.com/auth/reset-password?token=test123',
            })
            
            result = send_mail(
                subject='Test Password Reset Email - Pilito',
                message='Plain text version: Click the link to reset your password.',
                from_email=settings.DEFAULT_FROM_EMAIL_DISPLAY,
                recipient_list=[test_email],
                html_message=html_message,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"✅ HTML email sent successfully! Result: {result}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ HTML email failed!"))
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"HTML email test failed: {str(e)}", exc_info=True)
        
        # Test 3: Raw SMTP connection
        self.stdout.write("\n" + self.style.WARNING("📧 Test 3: Testing raw SMTP connection..."))
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            self.stdout.write(f"Connecting to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...")
            
            if settings.EMAIL_USE_TLS:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=30)
                server.ehlo()
                self.stdout.write("Starting TLS...")
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=30)
            
            self.stdout.write(self.style.SUCCESS("✅ Connected to SMTP server!"))
            
            self.stdout.write(f"Logging in with user: {settings.EMAIL_HOST_USER}...")
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            self.stdout.write(self.style.SUCCESS("✅ SMTP login successful!"))
            
            # Send test message
            msg = MIMEText('Test message from Liara SMTP via raw connection')
            msg['Subject'] = 'Test Email - Raw SMTP - Pilito'
            msg['From'] = settings.DEFAULT_FROM_EMAIL
            msg['To'] = test_email
            
            server.send_message(msg)
            self.stdout.write(self.style.SUCCESS("✅ Raw SMTP email sent successfully!"))
            
            server.quit()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Raw SMTP test failed!"))
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(f"Raw SMTP test failed: {str(e)}", exc_info=True)
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Email tests completed!"))
        self.stdout.write("=" * 60)
        self.stdout.write("\n📝 Check the logs above for any errors.")
        self.stdout.write(f"📬 Check {test_email} inbox for test emails.")

