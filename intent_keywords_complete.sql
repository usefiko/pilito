-- ====================================================================================================
-- 📋 Complete Intent Keywords for 100% Accuracy
-- ====================================================================================================
-- این فایل شامل Keywords کامل برای همه Intents است
-- برای import: از Django Admin Panel استفاده کنید یا این SQL را اجرا کنید
-- ====================================================================================================

-- پاک کردن Keywords قبلی (اختیاری)
-- DELETE FROM intent_keywords WHERE user_id IS NULL;

-- ====================================================================================================
-- 1️⃣ PRICING Intent (قیمت و پلن‌ها)
-- ====================================================================================================

-- فارسی
INSERT INTO intent_keywords (intent, language, keyword, weight, user_id, is_active, created_at, updated_at)
VALUES
    ('pricing', 'fa', 'قیمت', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'قیمتش', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'قیمتش چنده', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'چنده', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'چند', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'هزینه', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'تعرفه', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'پلن', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'پکیج', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'اشتراک', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'خرید', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'فروش', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'تومان', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'دلار', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'پرداخت', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'پول', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'ارزون', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'گرون', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'تخفیف', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'کد تخفیف', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'میخرم', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'fa', 'میخوام بخرم', 1.0, NULL, true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- انگلیسی
INSERT INTO intent_keywords (intent, language, keyword, weight, user_id, is_active, created_at, updated_at)
VALUES
    ('pricing', 'en', 'price', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'cost', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'pricing', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'how much', 1.5, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'plan', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'package', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'subscription', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'buy', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'purchase', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'payment', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'dollar', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'cheap', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'expensive', 1.0, NULL, true, NOW(), NOW()),
    ('pricing', 'en', 'discount', 1.0, NULL, true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- ====================================================================================================
-- 2️⃣ PRODUCT Intent (اطلاعات محصول)
-- ====================================================================================================

-- فارسی
INSERT INTO intent_keywords (intent, language, keyword, weight, user_id, is_active, created_at, updated_at)
VALUES
    ('product', 'fa', 'محصول', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'محصولات', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'محصولاتتون', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'سرویس', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'خدمات', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'ویژگی', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'امکانات', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'قابلیت', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'چیه', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'چیست', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'داری', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'دارید', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'دارین', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'داری؟', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'دارید؟', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'دارین؟', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'چی داری', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'چی دارید', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'چی دارین', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'موجود', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'موجوده', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'موجودی', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'رنگبندی', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'سایز', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'مدل', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'کالکشن', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'جنس', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'کیفیت', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'نمونه', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'fa', 'مشخصات', 1.0, NULL, true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- انگلیسی
INSERT INTO intent_keywords (intent, language, keyword, weight, user_id, is_active, created_at, updated_at)
VALUES
    ('product', 'en', 'product', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'en', 'products', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'en', 'service', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'en', 'feature', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'en', 'functionality', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'en', 'capability', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'en', 'what does', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'en', 'what is', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'en', 'do you have', 1.5, NULL, true, NOW(), NOW()),
    ('product', 'en', 'available', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'en', 'in stock', 1.0, NULL, true, NOW(), NOW()),
    ('product', 'en', 'specifications', 1.0, NULL, true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- ====================================================================================================
-- 3️⃣ HOWTO Intent (آموزش و راهنما)
-- ====================================================================================================

-- فارسی
INSERT INTO intent_keywords (intent, language, keyword, weight, user_id, is_active, created_at, updated_at)
VALUES
    ('howto', 'fa', 'چطور', 2.0, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'چطوری', 2.0, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'چگونه', 1.5, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'راهنما', 1.5, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'آموزش', 1.5, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'نحوه', 1.5, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'روش', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'مراحل', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'کمک', 1.5, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'میشه', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'میتونم', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'راه', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'گام به گام', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'توضیح بده', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'توضیح', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'fa', 'یاد بده', 1.0, NULL, true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- انگلیسی
INSERT INTO intent_keywords (intent, language, keyword, weight, user_id, is_active, created_at, updated_at)
VALUES
    ('howto', 'en', 'how', 2.0, NULL, true, NOW(), NOW()),
    ('howto', 'en', 'how to', 2.0, NULL, true, NOW(), NOW()),
    ('howto', 'en', 'guide', 1.5, NULL, true, NOW(), NOW()),
    ('howto', 'en', 'tutorial', 1.5, NULL, true, NOW(), NOW()),
    ('howto', 'en', 'steps', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'en', 'instruction', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'en', 'way to', 1.0, NULL, true, NOW(), NOW()),
    ('howto', 'en', 'how do i', 2.0, NULL, true, NOW(), NOW()),
    ('howto', 'en', 'help', 1.5, NULL, true, NOW(), NOW()),
    ('howto', 'en', 'can i', 1.0, NULL, true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- ====================================================================================================
-- 4️⃣ CONTACT Intent (تماس و آدرس و ارسال) ⭐ این مهم‌ترین بخش است!
-- ====================================================================================================

-- فارسی
INSERT INTO intent_keywords (intent, language, keyword, weight, user_id, is_active, created_at, updated_at)
VALUES
    -- آدرس (با املاهای مختلف)
    ('contact', 'fa', 'آدرس', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'ادرس', 2.0, NULL, true, NOW(), NOW()),  -- ⭐ املای غلط رایج
    ('contact', 'fa', 'آدرستون', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'ادرستون', 2.0, NULL, true, NOW(), NOW()),  -- ⭐ املای غلط رایج
    ('contact', 'fa', 'آدرس شما', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'ادرس شما', 2.0, NULL, true, NOW(), NOW()),  -- ⭐ املای غلط رایج
    ('contact', 'fa', 'کجایید', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'کجاست', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'کجا', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'محل', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'موقعیت', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'لوکیشن', 1.0, NULL, true, NOW(), NOW()),
    
    -- ارسال ⭐ این کلمات قبلاً نبودند!
    ('contact', 'fa', 'ارسال', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'ارسال دارید', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'ارسال دارین', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'ارسالتون', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'نحوه ارسال', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'چطور ارسال', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'پست', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'پیک', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'تحویل', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'رایگان', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'هزینه ارسال', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'زمان ارسال', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'چقدر طول میکشه', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'کی میرسه', 1.5, NULL, true, NOW(), NOW()),
    
    -- تماس
    ('contact', 'fa', 'تماس', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'ارتباط', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'پشتیبانی', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'شماره', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'تلفن', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'موبایل', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'ایمیل', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'اینستاگرام', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'تلگرام', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'واتساپ', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'ساعت کاری', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'زمان کاری', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'باز', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'fa', 'بسته', 1.0, NULL, true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- انگلیسی
INSERT INTO intent_keywords (intent, language, keyword, weight, user_id, is_active, created_at, updated_at)
VALUES
    ('contact', 'en', 'contact', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'address', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'location', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'where', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'support', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'phone', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'email', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'reach', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'hours', 1.5, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'call', 1.0, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'shipping', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'delivery', 2.0, NULL, true, NOW(), NOW()),
    ('contact', 'en', 'ship', 1.5, NULL, true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- ====================================================================================================
-- 5️⃣ GENERAL Intent (سوالات عمومی)
-- ====================================================================================================

-- فارسی
INSERT INTO intent_keywords (intent, language, keyword, weight, user_id, is_active, created_at, updated_at)
VALUES
    ('general', 'fa', 'سلام', 0.5, NULL, true, NOW(), NOW()),
    ('general', 'fa', 'درود', 0.5, NULL, true, NOW(), NOW()),
    ('general', 'fa', 'ممنون', 0.5, NULL, true, NOW(), NOW()),
    ('general', 'fa', 'متشکرم', 0.5, NULL, true, NOW(), NOW()),
    ('general', 'fa', 'خوبی', 0.5, NULL, true, NOW(), NOW()),
    ('general', 'fa', 'چطوری', 0.5, NULL, true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- انگلیسی
INSERT INTO intent_keywords (intent, language, keyword, weight, user_id, is_active, created_at, updated_at)
VALUES
    ('general', 'en', 'hello', 0.5, NULL, true, NOW(), NOW()),
    ('general', 'en', 'hi', 0.5, NULL, true, NOW(), NOW()),
    ('general', 'en', 'thanks', 0.5, NULL, true, NOW(), NOW()),
    ('general', 'en', 'thank you', 0.5, NULL, true, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- ====================================================================================================
-- ✅ تمام شد! حالا Intent Classification باید 100% دقیق باشد
-- ====================================================================================================

