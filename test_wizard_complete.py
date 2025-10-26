#!/usr/bin/env python3
"""
Test Script for Wizard Complete API
این اسکریپت وضعیت ویزارد رو بررسی می‌کنه و اگه همه چیز OK بود تکمیلش می‌کنه
"""

import requests
import json
from pprint import pprint

# ⚙️ تنظیمات
BASE_URL = "http://localhost:8000"
EMAIL = "omidlog@gmail.com"
PASSWORD = input("Enter your password: ")  # برای امنیت از کاربر می‌گیریم

print("\n" + "="*60)
print("🧪 Wizard Complete API Test Script")
print("="*60 + "\n")

try:
    # 1️⃣ لاگین و دریافت توکن
    print("1️⃣  در حال لاگین...")
    login_response = requests.post(
        f"{BASE_URL}/api/v1/accounts/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"❌ خطا در لاگین: {login_response.text}")
        exit(1)
    
    token = login_response.json()['access']
    print("✅ لاگین موفق\n")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 2️⃣ بررسی وضعیت ویزارد
    print("2️⃣  در حال بررسی وضعیت ویزارد...")
    status_response = requests.get(
        f"{BASE_URL}/api/v1/accounts/wizard-complete",
        headers=headers,
        timeout=10
    )
    
    if status_response.status_code != 200:
        print(f"❌ خطا در دریافت وضعیت: {status_response.text}")
        exit(1)
    
    status = status_response.json()
    print("✅ وضعیت دریافت شد\n")
    
    # نمایش وضعیت فعلی
    print("="*60)
    print("📊 وضعیت فعلی ویزارد:")
    print("="*60)
    print(f"🎯 Wizard Complete: {'✅ بله' if status['wizard_complete'] else '❌ خیر'}")
    print(f"🎯 می‌تونه تکمیل کنه: {'✅ بله' if status['can_complete'] else '❌ خیر'}")
    print()
    
    # نمایش جزئیات
    print("📝 جزئیات:")
    print("-" * 60)
    details = status['details']
    field_labels = {
        'first_name': 'نام',
        'last_name': 'نام خانوادگی',
        'phone_number': 'شماره تماس',
        'business_type': 'نوع بیزنس',
        'manual_prompt': 'منوال پرامپت',
        'channel_connected': 'کانال متصل',
        'instagram_connected': 'Instagram',
        'telegram_connected': 'Telegram'
    }
    
    for key, value in details.items():
        label = field_labels.get(key, key)
        icon = "✅" if value else "❌"
        print(f"  {icon} {label:20s}: {value}")
    
    print()
    
    # نمایش موارد کم شده
    if status['missing_fields']:
        print("⚠️  موارد کم شده:")
        print("-" * 60)
        for field in status['missing_fields']:
            label = field_labels.get(field, field)
            print(f"  ❌ {label}")
        print()
    
    # 3️⃣ تلاش برای تکمیل ویزارد
    if status['can_complete']:
        print("="*60)
        print("3️⃣  همه شرایط کامل است! در حال تکمیل ویزارد...")
        print("="*60 + "\n")
        
        complete_response = requests.patch(
            f"{BASE_URL}/api/v1/accounts/wizard-complete",
            headers=headers,
            timeout=10
        )
        
        if complete_response.status_code == 200:
            result = complete_response.json()
            print("✅ ویزارد با موفقیت تکمیل شد! 🎉")
            print("\nجزئیات:")
            pprint(result, width=60)
            print("\n🎯 حالا می‌تونید در Admin Panel تیک سبز رو ببینید!")
        else:
            print(f"❌ خطا در تکمیل ویزارد:")
            pprint(complete_response.json(), width=60)
    else:
        print("="*60)
        print("⚠️  نمی‌تونه ویزارد رو تکمیل کنه!")
        print("="*60)
        print("\n📋 لطفاً ابتدا موارد زیر را تکمیل کنید:\n")
        for field in status['missing_fields']:
            label = field_labels.get(field, field)
            
            # پیشنهاد راه‌حل
            if field == 'first_name' or field == 'last_name':
                hint = "→ Settings > Account > اسم و فامیلیتون رو پر کنید"
            elif field == 'phone_number':
                hint = "→ Settings > Account > شماره تماس رو پر کنید"
            elif field == 'business_type':
                hint = "→ Settings > Account > نوع بیزنستون رو انتخاب کنید"
            elif field == 'manual_prompt':
                hint = "→ Settings > AI & Prompts > Manual Prompt رو پر کنید"
            elif field == 'channel_connected':
                hint = "→ Settings > Channels > Instagram یا Telegram رو وصل کنید"
            else:
                hint = ""
            
            print(f"  ❌ {label}")
            if hint:
                print(f"     {hint}")
        
        print("\n💡 بعد از تکمیل این موارد، دوباره این اسکریپت رو اجرا کنید.")
    
    print("\n" + "="*60)
    print("✅ تست تمام شد")
    print("="*60 + "\n")

except requests.exceptions.ConnectionError:
    print("\n❌ خطا: نمی‌تونم به سرور وصل بشم!")
    print("   مطمئن بشید که Django سرور در حال اجراست:")
    print("   → python manage.py runserver")
    print()

except requests.exceptions.Timeout:
    print("\n❌ خطا: Timeout - سرور خیلی دیر جواب داد")
    print()

except KeyError as e:
    print(f"\n❌ خطا: کلید {e} در پاسخ پیدا نشد")
    print("   احتمالاً ساختار response تغییر کرده")
    print()

except Exception as e:
    print(f"\n❌ خطای غیرمنتظره: {e}")
    print()
    import traceback
    traceback.print_exc()

