#!/usr/bin/env python
"""
اسکریپت تست اتصال پروکسی به Telegram API
این اسکریپت مستقیماً پروکسی رو test می‌کنه بدون نیاز به Django
"""

import requests
import sys

# پروکسی از دیتابیس (همون که در admin هست)
PROXY_HTTP = "http://14a1807971f02:6e78a55404@45.40.121.203:12324"
PROXY_HTTPS = "http://14a1807971f02:6e78a55404@45.40.121.203:12324"

# Telegram API test endpoint
TEST_BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"  # توکن fake برای تست
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TEST_BOT_TOKEN}/getMe"

def test_direct_connection():
    """تست اتصال مستقیم بدون پروکسی"""
    print("=" * 60)
    print("🔍 TEST 1: Direct connection (بدون پروکسی)")
    print("=" * 60)
    try:
        response = requests.get(TELEGRAM_API_URL, timeout=5)
        print(f"✅ Status Code: {response.status_code}")
        print(f"📦 Response: {response.text[:200]}")
        return True
    except requests.exceptions.Timeout:
        print("❌ Timeout: سرور به Telegram دسترسی مستقیم نداره (انتظار داشتیم)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_proxy_connection():
    """تست اتصال از طریق پروکسی"""
    print("\n" + "=" * 60)
    print("🔍 TEST 2: Proxy connection (با پروکسی)")
    print("=" * 60)
    
    proxies = {
        "http": PROXY_HTTP,
        "https": PROXY_HTTPS
    }
    
    print(f"🔒 Proxy Config:")
    print(f"   http:  {PROXY_HTTP}")
    print(f"   https: {PROXY_HTTPS}")
    print()
    
    try:
        print("📡 Sending request through proxy...")
        response = requests.get(TELEGRAM_API_URL, proxies=proxies, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        print(f"📦 Response: {response.text[:200]}")
        
        # بررسی response
        if response.status_code == 200:
            print("\n🎉 SUCCESS: پروکسی کار می‌کنه!")
            return True
        elif response.status_code == 401:
            print("\n⚠️ Telegram API responded (پروکسی کار می‌کنه، ولی توکن invalid)")
            return True
        else:
            print(f"\n⚠️ Unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: پروکسی جواب نمیده یا خیلی کنده")
        return False
    except requests.exceptions.ProxyError as e:
        print(f"❌ Proxy Error: {e}")
        print("   مشکلات احتمالی:")
        print("   - پروکسی down هست")
        print("   - username/password اشتباهه")
        print("   - IP سرور block شده")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

def test_proxy_with_real_bot_token():
    """تست با توکن واقعی bot (اگر موجود باشه)"""
    print("\n" + "=" * 60)
    print("🔍 TEST 3: Test با توکن واقعی (اختیاری)")
    print("=" * 60)
    
    real_token = input("توکن واقعی bot رو وارد کن (یا Enter برای skip): ").strip()
    
    if not real_token:
        print("⏭️ Skipped")
        return None
    
    url = f"https://api.telegram.org/bot{real_token}/getMe"
    proxies = {
        "http": PROXY_HTTP,
        "https": PROXY_HTTPS
    }
    
    try:
        print("📡 Testing with real bot token...")
        response = requests.get(url, proxies=proxies, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print(f"🎉 SUCCESS: Bot connected!")
                print(f"📋 Bot info: {data.get('result')}")
                return True
        else:
            print(f"📦 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Telegram Proxy Connection Test")
    print("=" * 60)
    print()
    
    # Test 1: بدون پروکسی
    direct_ok = test_direct_connection()
    
    # Test 2: با پروکسی
    proxy_ok = test_proxy_connection()
    
    # Test 3: با توکن واقعی (اختیاری)
    # real_ok = test_proxy_with_real_bot_token()
    
    # نتیجه نهایی
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Direct connection:  {'✅ OK' if direct_ok else '❌ FAILED (expected in Iran)'}")
    print(f"Proxy connection:   {'✅ OK' if proxy_ok else '❌ FAILED'}")
    print()
    
    if proxy_ok:
        print("✅ نتیجه: پروکسی درست کار می‌کنه!")
        print("   مشکل باید از جای دیگه‌ای باشه.")
        sys.exit(0)
    else:
        print("❌ نتیجه: پروکسی کار نمی‌کنه!")
        print("   باید پروکسی رو چک کنی:")
        print("   1. آیا پروکسی up هست؟")
        print("   2. آیا username/password درسته؟")
        print("   3. آیا IP سرور در whitelist پروکسی هست؟")
        sys.exit(1)

if __name__ == "__main__":
    main()

