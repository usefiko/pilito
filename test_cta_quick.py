#!/usr/bin/env python3
"""
تست سریع CTA Utils
اجرا: python3 test_cta_quick.py
"""

def test_cta_extraction():
    """تست extraction ساده"""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    from message.utils.cta_utils import extract_cta_from_text
    
    print("🧪 شروع تست CTA Utils...\n")
    
    # Test 1: یک CTA ساده
    text1 = "برای اطلاعات بیشتر [[CTA:سایت فیکو|https://fiko.ai]] ببینید"
    clean1, buttons1 = extract_cta_from_text(text1)
    
    assert "[[CTA" not in clean1, "❌ CTA token باید حذف شود"
    assert buttons1 is not None, "❌ باید دکمه برگردد"
    assert len(buttons1) == 1, f"❌ باید 1 دکمه باشد، ولی {len(buttons1)} هست"
    assert buttons1[0]['title'] == "سایت فیکو", f"❌ عنوان: {buttons1[0]['title']}"
    assert buttons1[0]['url'] == "https://fiko.ai", f"❌ URL: {buttons1[0]['url']}"
    
    print("✅ Test 1: یک CTA ساده - PASSED")
    print(f"   Clean text: {clean1}")
    print(f"   Buttons: {buttons1}\n")
    
    # Test 2: چند CTA
    text2 = """برای اطلاعات:
[[CTA:سایت|https://fiko.ai]]
[[CTA:قیمت|https://fiko.ai/pricing]]
[[CTA:تماس|https://fiko.ai/contact]]"""
    
    clean2, buttons2 = extract_cta_from_text(text2)
    
    assert buttons2 is not None, "❌ باید دکمه‌ها برگردد"
    assert len(buttons2) == 3, f"❌ باید 3 دکمه باشد، ولی {len(buttons2)} هست"
    
    print("✅ Test 2: چند CTA - PASSED")
    print(f"   تعداد دکمه: {len(buttons2)}")
    print(f"   Buttons: {buttons2}\n")
    
    # Test 3: بدون CTA
    text3 = "سلام! چطور می‌تونم کمکتون کنم؟"
    clean3, buttons3 = extract_cta_from_text(text3)
    
    assert buttons3 is None, "❌ نباید دکمه‌ای برگردد"
    assert clean3 == text3, "❌ متن نباید تغییر کند"
    
    print("✅ Test 3: بدون CTA - PASSED")
    print(f"   Text unchanged: {clean3}\n")
    
    # Test 4: URL نامعتبر
    text4 = "لینک [[CTA:Test|ftp://invalid.com]] نامعتبر"
    clean4, buttons4 = extract_cta_from_text(text4)
    
    assert buttons4 is None or len(buttons4) == 0, "❌ URL نامعتبر باید رد شود"
    
    print("✅ Test 4: URL نامعتبر - PASSED")
    print(f"   Invalid URL rejected\n")
    
    # Test 5: فاصله‌های اضافی
    text5 = "قبل  [[CTA:Test|https://test.com]]  بعد"
    clean5, buttons5 = extract_cta_from_text(text5)
    
    # بررسی فاصه‌های اضافی پاک شده باشند
    assert "  " not in clean5, "❌ فاضله‌های اضافی باید پاک شوند"
    
    print("✅ Test 5: فاصله‌های اضافی - PASSED")
    print(f"   Clean text: '{clean5}'\n")
    
    print("🎉 همه تست‌ها موفقیت‌آمیز بودند!")
    return True


if __name__ == '__main__':
    try:
        test_cta_extraction()
    except AssertionError as e:
        print(f"\n❌ تست ناموفق: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

