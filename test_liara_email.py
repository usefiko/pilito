#!/usr/bin/env python
"""
Test script for Liara Email SMTP configuration
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/Users/omidataei/Documents/GitHub/pilito2/Untitled/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def test_simple_email():
    """Test sending a simple plain text email"""
    print("=" * 60)
    print("Testing Simple Email Send")
    print("=" * 60)
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print("-" * 60)
    
    try:
        result = send_mail(
            subject='Test Email from Liara SMTP',
            message='This is a test email to verify Liara SMTP configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['mamadbayat777@gmail.com'],  # Your test email
            fail_silently=False,
        )
        print(f"✅ Email sent successfully! Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Email sending failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        # Print detailed error info
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
        return False


def test_html_email():
    """Test sending HTML email with template"""
    print("\n" + "=" * 60)
    print("Testing HTML Email with Template")
    print("=" * 60)
    
    try:
        html_message = render_to_string('emails/password_reset.html', {
            'user_name': 'Test User',
            'reset_link': 'https://app.pilito.com/auth/reset-password?token=test123',
        })
        
        result = send_mail(
            subject='Test Password Reset Email',
            message='Plain text version: Click the link to reset your password.',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL_DISPLAY', 'Pilito <noreply@mail.pilito.com>'),
            recipient_list=['mamadbayat777@gmail.com'],  # Your test email
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✅ HTML email sent successfully! Result: {result}")
        return True
    except Exception as e:
        print(f"❌ HTML email sending failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
        return False


def test_smtp_connection():
    """Test raw SMTP connection"""
    print("\n" + "=" * 60)
    print("Testing Raw SMTP Connection")
    print("=" * 60)
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        print(f"Connecting to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...")
        
        if settings.EMAIL_USE_TLS:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=30)
            server.set_debuglevel(1)  # Enable debug output
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=30)
            server.set_debuglevel(1)
        
        print(f"\n✅ Connected to server successfully!")
        print(f"Logging in with user: {settings.EMAIL_HOST_USER}...")
        
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print(f"✅ Login successful!")
        
        # Create test message
        msg = MIMEText('Test message from Liara SMTP')
        msg['Subject'] = 'Test Email - Raw SMTP'
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = 'mamadbayat777@gmail.com'
        
        print(f"\nSending test email...")
        server.send_message(msg)
        print(f"✅ Email sent successfully via raw SMTP!")
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"\n❌ SMTP connection/test failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
        return False


if __name__ == '__main__':
    print("\n🚀 Starting Liara Email SMTP Tests\n")
    
    # Test 1: Simple email
    test1 = test_simple_email()
    
    # Test 2: HTML email
    test2 = test_html_email()
    
    # Test 3: Raw SMTP connection
    test3 = test_smtp_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Simple Email: {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"HTML Email: {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"Raw SMTP: {'✅ PASSED' if test3 else '❌ FAILED'}")
    print("=" * 60)
    
    if all([test1, test2, test3]):
        print("\n🎉 All tests passed! Liara Email is configured correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)

