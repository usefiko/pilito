#!/usr/bin/env python3
"""
SMTP Connection Diagnostic Tool
Tests connectivity to Liara email service
"""

import socket
import smtplib
import os
from datetime import datetime

def test_smtp_connection():
    """Test SMTP connection to Liara email service"""
    
    # Get settings from environment or use defaults
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.c1.liara.email')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'zen_torvalds_599nek')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '8d071fc6-a36c-43f1-9f09-b25bd408af87')
    EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '30'))
    
    print("=" * 60)
    print("🔍 SMTP Connection Diagnostic Tool")
    print("=" * 60)
    print(f"\n📋 Configuration:")
    print(f"   Host: {EMAIL_HOST}")
    print(f"   Port: {EMAIL_PORT}")
    print(f"   User: {EMAIL_HOST_USER}")
    print(f"   Password: {'*' * len(EMAIL_HOST_PASSWORD)}")
    print(f"   Timeout: {EMAIL_TIMEOUT}s")
    print()
    
    # Test 1: DNS Resolution
    print("🧪 Test 1: DNS Resolution")
    try:
        ip_address = socket.gethostbyname(EMAIL_HOST)
        print(f"   ✅ DNS resolved: {EMAIL_HOST} -> {ip_address}")
    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return False
    
    # Test 2: Port Connectivity (TCP)
    print("\n🧪 Test 2: TCP Port Connectivity")
    try:
        start_time = datetime.now()
        sock = socket.create_connection((EMAIL_HOST, EMAIL_PORT), timeout=10)
        elapsed = (datetime.now() - start_time).total_seconds()
        sock.close()
        print(f"   ✅ Port {EMAIL_PORT} is open (took {elapsed:.2f}s)")
    except socket.timeout:
        print(f"   ❌ Connection timeout after 10s")
        print("   💡 Possible causes:")
        print("      - Firewall blocking outbound SMTP traffic")
        print("      - Network routing issue")
        print("      - SMTP server is down")
        return False
    except ConnectionRefusedError:
        print(f"   ❌ Connection refused")
        print("   💡 Wrong port or service not running")
        return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # Test 3: SMTP Handshake
    print("\n🧪 Test 3: SMTP Handshake")
    try:
        start_time = datetime.now()
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"   ✅ SMTP handshake successful (took {elapsed:.2f}s)")
        
        # Get server capabilities
        print(f"   📝 Server greeting: {server.getwelcome().decode('utf-8')}")
        
        server.quit()
    except socket.timeout:
        print(f"   ❌ SMTP handshake timeout")
        return False
    except Exception as e:
        print(f"   ❌ SMTP handshake failed: {e}")
        return False
    
    # Test 4: STARTTLS
    print("\n🧪 Test 4: STARTTLS Support")
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        server.starttls()
        print(f"   ✅ STARTTLS successful")
        server.quit()
    except Exception as e:
        print(f"   ❌ STARTTLS failed: {e}")
        return False
    
    # Test 5: Authentication
    print("\n🧪 Test 5: SMTP Authentication")
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        print(f"   ✅ Authentication successful")
        server.quit()
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        print("   💡 Check your EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
        return False
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return False
    
    # Test 6: Send Test Email
    print("\n🧪 Test 6: Send Test Email")
    print("   ⚠️  Skipped (would send actual email)")
    print("   💡 If all above tests pass, email sending should work")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! SMTP is configured correctly.")
    print("=" * 60)
    print("\n💡 Recommendations:")
    print("   1. If you're in Docker, ensure network connectivity")
    print("   2. Check firewall rules (allow outbound on port 587)")
    print("   3. Verify Liara email service is active")
    print("   4. Consider using Celery for async email sending")
    print()
    
    return True


def check_docker_network():
    """Check if running in Docker and test network connectivity"""
    print("\n🐳 Docker Network Check")
    
    # Check if running in Docker
    if os.path.exists('/.dockerenv'):
        print("   ✅ Running inside Docker container")
        
        # Test external connectivity
        print("\n   Testing external connectivity:")
        test_hosts = [
            ('google.com', 80),
            ('smtp.c1.liara.email', 587),
        ]
        
        for host, port in test_hosts:
            try:
                sock = socket.create_connection((host, port), timeout=5)
                sock.close()
                print(f"   ✅ Can reach {host}:{port}")
            except Exception as e:
                print(f"   ❌ Cannot reach {host}:{port} - {e}")
    else:
        print("   ℹ️  Not running in Docker")


if __name__ == "__main__":
    try:
        check_docker_network()
        print()
        test_smtp_connection()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

