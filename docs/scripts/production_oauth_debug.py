#!/usr/bin/env python3
"""
Production Google OAuth Debug Script
Run this script on your production server to diagnose OAuth issues
"""

import requests
import json
import sys
from urllib.parse import urlparse, parse_qs
import socket


def test_production_endpoints():
    """Test production OAuth endpoints"""
    base_url = "https://api.fiko.net"
    
    print("🔍 Testing Production Google OAuth...")
    print("=" * 50)
    
    # Test 1: Check if the API server is accessible
    print("1️⃣ Testing API server accessibility...")
    try:
        response = requests.get(f"{base_url}/api/v1/usr/google/test", timeout=10, verify=True)
        if response.status_code == 200:
            config = response.json()
            print("✅ API server is accessible")
            print(f"   - Configured: {config.get('configured')}")
            print(f"   - Redirect URI: {config.get('redirect_uri')}")
        else:
            print(f"❌ API server returned status: {response.status_code}")
            return False
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Certificate error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Check auth URL generation
    print("\n2️⃣ Testing auth URL generation...")
    try:
        response = requests.get(f"{base_url}/api/v1/usr/google/auth-url", timeout=10)
        if response.status_code == 200:
            auth_data = response.json()
            auth_url = auth_data.get('auth_url')
            print("✅ Auth URL generated successfully")
            
            # Parse the auth URL to verify parameters
            parsed_url = urlparse(auth_url)
            params = parse_qs(parsed_url.query)
            
            print("\n📋 Auth URL Analysis:")
            print(f"   - Domain: {parsed_url.netloc}")
            print(f"   - Client ID: {params.get('client_id', ['N/A'])[0][:20]}...")
            print(f"   - Redirect URI: {params.get('redirect_uri', ['N/A'])[0]}")
            print(f"   - Scope: {params.get('scope', ['N/A'])[0]}")
            
            # Verify the redirect URI
            redirect_uri = params.get('redirect_uri', [''])[0]
            if redirect_uri == "https://api.fiko.net/api/v1/usr/google/callback":
                print("✅ Redirect URI is correct")
            else:
                print(f"❌ Redirect URI mismatch: {redirect_uri}")
        else:
            print(f"❌ Auth URL generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Auth URL test failed: {e}")
        return False
    
    # Test 3: Test callback endpoint with error
    print("\n3️⃣ Testing callback endpoint...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/usr/google/callback?error=test_error",
            timeout=10,
            allow_redirects=False
        )
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            print("✅ Callback endpoint is responding")
            print(f"   - Redirects to: {location}")
            
            # Check if it redirects to the correct frontend
            if "app.fiko.net" in location:
                print("✅ Frontend redirect is correct")
            else:
                print(f"❌ Unexpected redirect: {location}")
        else:
            print(f"❌ Callback endpoint returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Callback test failed: {e}")
        return False
    
    print("\n✅ All basic tests passed!")
    return True


def test_dns_resolution():
    """Test DNS resolution for api.fiko.net"""
    print("\n🌐 DNS Resolution Test:")
    print("-" * 30)
    
    try:
        ip = socket.gethostbyname('api.fiko.net')
        print(f"✅ api.fiko.net resolves to: {ip}")
        
        # Test port connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, 443))
        sock.close()
        
        if result == 0:
            print("✅ Port 443 (HTTPS) is accessible")
            return True
        else:
            print("❌ Port 443 (HTTPS) is not accessible")
            return False
    except socket.gaierror:
        print("❌ api.fiko.net does not resolve")
        return False


def check_google_connectivity():
    """Check if Google can reach your server"""
    print("\n🔗 Google Connectivity Check:")
    print("-" * 30)
    
    print("📋 For Google OAuth to work, Google's servers must be able to:")
    print("1. Resolve api.fiko.net to your server's IP")
    print("2. Connect to your server on port 443 (HTTPS)")
    print("3. Successfully make HTTPS requests to your callback URL")
    
    print("\n🔧 Common issues:")
    print("- Firewall blocking Google's IP ranges")
    print("- DNS not pointing to the correct server")
    print("- SSL certificate issues")
    print("- Server not running or responding")
    print("- Load balancer/proxy configuration issues")


def show_debugging_steps():
    """Show debugging steps for production"""
    print("\n🛠️  Production Debugging Steps:")
    print("=" * 50)
    
    print("1️⃣ Monitor server logs during OAuth attempt:")
    print("   docker logs -f <container_name> | grep -i 'google\\|oauth\\|callback'")
    
    print("\n2️⃣ Test callback manually from your server:")
    print("   curl -i 'https://api.fiko.net/api/v1/usr/google/callback?error=test'")
    
    print("\n3️⃣ Check if Google can reach your server:")
    print("   - Test from external network: curl https://api.fiko.net/api/v1/usr/google/test")
    print("   - Check firewall rules for incoming HTTPS traffic")
    print("   - Verify SSL certificate: openssl s_client -connect api.fiko.net:443")
    
    print("\n4️⃣ Verify Google OAuth Console:")
    print("   - Authorized redirect URIs: https://api.fiko.net/api/v1/usr/google/callback")
    print("   - Domain verification for api.fiko.net")
    print("   - Client ID and Secret are correct")
    
    print("\n5️⃣ Test complete OAuth flow:")
    print("   - Get auth URL: curl https://api.fiko.net/api/v1/usr/google/auth-url")
    print("   - Use the URL in browser immediately")
    print("   - Monitor server logs for callback attempts")


def main():
    print("🚀 Production Google OAuth Diagnostic Tool")
    print("Run this on your production server or externally to test")
    print("=" * 60)
    
    # Test DNS first
    if not test_dns_resolution():
        print("\n❌ DNS/Network issues detected. Fix these first.")
        sys.exit(1)
    
    # Test endpoints
    if test_production_endpoints():
        print("\n📊 Basic functionality works!")
        print("If OAuth still fails, the issue is likely:")
        print("1. Google OAuth Console configuration")
        print("2. Google can't reach your server (firewall/network)")
        print("3. Server-side processing errors")
    else:
        print("\n❌ Basic functionality has issues.")
    
    # Show connectivity info
    check_google_connectivity()
    
    # Show debugging steps
    show_debugging_steps()


if __name__ == "__main__":
    main()
