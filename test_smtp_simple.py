#!/usr/bin/env python3
"""
Simple SMTP test for Liara Email - No Django required
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Liara SMTP Configuration
SMTP_HOST = 'smtp.c1.liara.email'
SMTP_PORT = 587
SMTP_USER = 'zen_torvalds_599nek'
SMTP_PASSWORD = '8d071fc6-a36c-43f1-9f09-b25bd408af87'
FROM_EMAIL = 'noreply@mail.pilito.com'
TO_EMAIL = 'mamadbayat777@gmail.com'  # Your email

def test_smtp_connection():
    """Test SMTP connection and email sending"""
    print("=" * 70)
    print("📧 Testing Liara Email SMTP Configuration")
    print("=" * 70)
    print(f"Host: {SMTP_HOST}")
    print(f"Port: {SMTP_PORT}")
    print(f"User: {SMTP_USER}")
    print(f"From: {FROM_EMAIL}")
    print(f"To: {TO_EMAIL}")
    print("-" * 70)
    
    try:
        print("\n1️⃣  Connecting to SMTP server...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        server.set_debuglevel(1)  # Show detailed debug info
        
        print("\n2️⃣  Starting TLS...")
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        print("\n3️⃣  Logging in...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("✅ Login successful!")
        
        print("\n4️⃣  Creating email message...")
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Test Email from Liara SMTP - Pilito'
        msg['From'] = FROM_EMAIL
        msg['To'] = TO_EMAIL
        
        # Plain text version
        text_content = """
        Hello!
        
        This is a test email from Pilito using Liara Email SMTP service.
        
        If you receive this email, it means the SMTP configuration is working correctly!
        
        Best regards,
        Pilito Team
        """
        
        # HTML version
        html_content = """
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #667eea;">Test Email from Pilito</h2>
            <p>Hello!</p>
            <p>This is a test email from <strong>Pilito</strong> using <strong>Liara Email SMTP</strong> service.</p>
            <p>If you receive this email, it means the SMTP configuration is working correctly! ✅</p>
            <hr style="border: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">
              Best regards,<br>
              Pilito Team<br>
              <a href="https://pilito.com">pilito.com</a>
            </p>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        print("\n5️⃣  Sending email...")
        server.send_message(msg)
        print("✅ Email sent successfully!")
        
        print("\n6️⃣  Closing connection...")
        server.quit()
        print("✅ Connection closed!")
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! All tests passed!")
        print("=" * 70)
        print(f"\n📬 Check your inbox at {TO_EMAIL}")
        print("   You should receive the test email shortly.")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("\n" + "=" * 70)
        print("❌ SMTP Authentication Failed!")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print("\nPossible causes:")
        print("  1. Wrong username or password")
        print("  2. SMTP access not enabled in Liara panel")
        print("  3. Account suspended or restricted")
        return False
        
    except smtplib.SMTPSenderRefused as e:
        print("\n" + "=" * 70)
        print("❌ Sender Email Rejected!")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print("\nPossible causes:")
        print(f"  1. Email address '{FROM_EMAIL}' not verified in Liara")
        print("  2. Domain 'mail.pilito.com' not configured properly")
        print("  3. SPF/DKIM records not set up")
        return False
        
    except smtplib.SMTPException as e:
        print("\n" + "=" * 70)
        print("❌ SMTP Error!")
        print("=" * 70)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        return False
        
    except ConnectionRefusedError:
        print("\n" + "=" * 70)
        print("❌ Connection Refused!")
        print("=" * 70)
        print(f"Cannot connect to {SMTP_HOST}:{SMTP_PORT}")
        print("\nPossible causes:")
        print("  1. Wrong host or port")
        print("  2. Firewall blocking connection")
        print("  3. SMTP service down")
        return False
        
    except TimeoutError:
        print("\n" + "=" * 70)
        print("❌ Connection Timeout!")
        print("=" * 70)
        print(f"Timeout connecting to {SMTP_HOST}:{SMTP_PORT}")
        print("\nPossible causes:")
        print("  1. Network connection issues")
        print("  2. Firewall blocking connection")
        print("  3. Server is slow or unavailable")
        return False
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ Unexpected Error!")
        print("=" * 70)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
        return False


if __name__ == '__main__':
    success = test_smtp_connection()
    exit(0 if success else 1)

