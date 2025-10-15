#!/usr/bin/env python3
"""
Production Google OAuth Debug Script
Run this on your production server to diagnose Google OAuth issues
"""

import requests
import json
import sys
from urllib.parse import urlparse


def test_production_oauth():
    """Test Google OAuth endpoints in production"""
    
    base_url = "https://api.fiko.net"
    
    print("🔍 Testing Production Google OAuth Configuration...")
    print(f"🌐 Base URL: {base_url}")
    print()
    
    # Test 1: Check if the server is accessible
    print("1️⃣ Testing server accessibility...")
    try:
        response = requests.get(f"{base_url}/api/v1/usr/google/test", timeout=10)
        if response.status_code == 200:
            print("✅ Server is accessible")
            config = response.json()
            print(f"   - Configured: {config.get('configured')}")
            print(f"   - Client ID configured: {config.get('client_id_configured')}")
            print(f"   - Redirect URI: {config.get('redirect_uri')}")
        else:
            print(f"❌ Server returned status: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Cannot reach server: {e}")
        return False
    
    # Test 2: Test auth URL generation
    print("\n2️⃣ Testing auth URL generation...")
    try:
        response = requests.get(f"{base_url}/api/v1/usr/google/auth-url", timeout=10)
        if response.status_code == 200:
            auth_data = response.json()
            auth_url = auth_data.get('auth_url')
            print("✅ Auth URL generated successfully")
            print(f"   - URL: {auth_url[:100]}...")
            
            # Verify the redirect URI in the auth URL
            if "redirect_uri=https%3A//api.fiko.net" in auth_url:
                print("✅ Correct redirect URI in auth URL")
            else:
                print("❌ Incorrect redirect URI in auth URL")
                print("   Expected: https://api.fiko.net/api/v1/usr/google/callback")
        else:
            print(f"❌ Auth URL generation failed: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Auth URL request failed: {e}")
        return False
    
    # Test 3: Test callback endpoint accessibility
    print("\n3️⃣ Testing callback endpoint...")
    try:
        # Test with error parameter to see if endpoint responds
        response = requests.get(
            f"{base_url}/api/v1/usr/google/callback?error=test_error", 
            timeout=10,
            allow_redirects=False
        )
        if response.status_code in [302, 200]:
            print("✅ Callback endpoint is accessible")
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                print(f"   - Redirects to: {location}")
        else:
            print(f"❌ Callback endpoint returned: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Callback endpoint request failed: {e}")
    
    # Test 4: SSL Certificate check
    print("\n4️⃣ Testing SSL certificate...")
    try:
        response = requests.get(f"{base_url}/api/v1/usr/google/test", verify=True, timeout=10)
        print("✅ SSL certificate is valid")
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL certificate issue: {e}")
        return False
    except requests.RequestException:
        pass  # Already tested above
    
    print("\n" + "="*50)
    print("📋 CHECKLIST FOR GOOGLE OAUTH CONSOLE:")
    print("="*50)
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Navigate to: APIs & Services → Credentials")
    print("3. Edit your OAuth 2.0 Client ID")
    print("4. Ensure 'Authorized redirect URIs' contains:")
    print("   https://api.fiko.net/api/v1/usr/google/callback")
    print("5. Save the changes")
    print()
    print("📋 DEBUGGING STEPS:")
    print("="*50)
    print("1. Check production server logs:")
    print("   docker logs <container_name> | grep -i 'google\\|oauth\\|callback'")
    print()
    print("2. Monitor real-time logs during OAuth attempt:")
    print("   docker logs -f <container_name>")
    print()
    print("3. Test with actual Google OAuth flow:")
    print(f"   - Use auth URL: {base_url}/api/v1/usr/google/auth-url")
    print("   - Complete Google authentication")
    print("   - Check if user is created in database")
    
    return True


def check_dns_resolution():
    """Check if api.fiko.net resolves correctly"""
    print("\n🌐 DNS Resolution Check:")
    print("="*30)
    
    import socket
    try:
        ip = socket.gethostbyname('api.fiko.net')
        print(f"✅ api.fiko.net resolves to: {ip}")
        
        # Try to connect to port 443
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, 443))
        sock.close()
        
        if result == 0:
            print("✅ Port 443 (HTTPS) is accessible")
        else:
            print("❌ Port 443 (HTTPS) is not accessible")
            return False
            
    except socket.gaierror:
        print("❌ api.fiko.net does not resolve")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Production Google OAuth Diagnostic Tool")
    print("="*50)
    
    # Check DNS first
    if not check_dns_resolution():
        print("\n❌ DNS/Network issues detected. Fix these first.")
        sys.exit(1)
    
    # Test OAuth
    if test_production_oauth():
        print("\n✅ Basic production setup looks good!")
        print("If Google OAuth still doesn't work, the issue is likely:")
        print("1. Google OAuth Console configuration")
        print("2. Frontend integration")
        print("3. Network/firewall rules")
    else:
        print("\n❌ Production setup has issues that need to be fixed.")
        sys.exit(1)
