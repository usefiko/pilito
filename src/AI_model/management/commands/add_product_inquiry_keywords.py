"""
Management command to add product inquiry keywords globally.
These keywords help detect when users ask about available products/services.
"""
from django.core.management.base import BaseCommand
from AI_model.models import IntentKeyword


class Command(BaseCommand):
    help = 'Add global keywords for product inquiry detection (e.g., "چه محصولاتی دارین؟")'

    def handle(self, *args, **options):
        """Add keywords that indicate user is asking about available products/services"""
        
        # Keywords for asking about products (not describing own business)
        product_inquiry_keywords = [
            # Persian - محصولات چی دارین؟
            ('product', 'fa', 'محصولات'),
            ('product', 'fa', 'محصول'),
            ('product', 'fa', 'چه محصولاتی دارین'),
            ('product', 'fa', 'چی داری'),
            ('product', 'fa', 'چی دارین'),
            ('product', 'fa', 'چه محصولاتی دارید'),
            ('product', 'fa', 'لیست محصولات'),
            ('product', 'fa', 'محصولاتتون چیه'),
            ('product', 'fa', 'محصولاتتون چیه'),
            ('product', 'fa', 'چه چیزی دارید'),
            ('product', 'fa', 'چیا دارین'),
            ('product', 'fa', 'چیزایی که دارین'),
            ('product', 'fa', 'پکیج'),
            ('product', 'fa', 'پکیج‌ها'),
            ('product', 'fa', 'پلن‌ها'),
            ('product', 'fa', 'بسته'),
            ('product', 'fa', 'بسته‌ها'),
            ('product', 'fa', 'سرویس'),
            ('product', 'fa', 'سرویس‌ها'),
            ('product', 'fa', 'خدمات'),
            ('product', 'fa', 'آیتم'),
            ('product', 'fa', 'گزینه'),
            ('product', 'fa', 'گزینه‌ها'),
            ('product', 'fa', 'انتخاب'),
            ('product', 'fa', 'انتخاب‌ها'),
            
            # Specific product name searches
            ('product', 'fa', 'داری؟'),  # "ممد داری؟"
            ('product', 'fa', 'دارین؟'),
            ('product', 'fa', 'دارید؟'),
            ('product', 'fa', 'به نام'),  # "محصولی به نام ممد"
            ('product', 'fa', 'اسم'),  # "محصول اسمش"
            
            # Purchase/Link related (لینک خریدشو بده)
            ('product', 'fa', 'لینک'),
            ('product', 'fa', 'خرید'),
            ('product', 'fa', 'خریدشو'),
            ('product', 'fa', 'بده'),
            ('product', 'fa', 'بفرست'),
            ('product', 'fa', 'ارسال'),
            ('product', 'fa', 'سفارش'),
            ('product', 'fa', 'چطوری خرید'),
            ('product', 'fa', 'کجا خرید'),
            ('product', 'fa', 'چگونه تهیه'),
            ('product', 'fa', 'آدرس'),
            ('product', 'fa', 'صفحه خرید'),
            
            # English - What products do you have?
            ('product', 'en', 'products'),
            ('product', 'en', 'what products'),
            ('product', 'en', 'product list'),
            ('product', 'en', 'what do you have'),
            ('product', 'en', 'what do you offer'),
            ('product', 'en', 'packages'),
            ('product', 'en', 'services'),
            ('product', 'en', 'options'),
            ('product', 'en', 'choices'),
            ('product', 'en', 'available products'),
            ('product', 'en', 'do you have'),
            ('product', 'en', 'product named'),
            
            # Arabic - ما هي المنتجات؟
            ('product', 'ar', 'منتجات'),
            ('product', 'ar', 'منتج'),
            ('product', 'ar', 'ما المنتجات'),
            ('product', 'ar', 'ماذا لديكم'),
            ('product', 'ar', 'قائمة المنتجات'),
            ('product', 'ar', 'خدمات'),
            ('product', 'ar', 'خيارات'),
            ('product', 'ar', 'هل لديكم'),
            ('product', 'ar', 'عندكم'),
            
            # Turkish - Hangi ürünler var?
            ('product', 'tr', 'ürünler'),
            ('product', 'tr', 'ürün'),
            ('product', 'tr', 'hangi ürünler'),
            ('product', 'tr', 'ürün listesi'),
            ('product', 'tr', 'neler var'),
            ('product', 'tr', 'hizmetler'),
            ('product', 'tr', 'seçenekler'),
            ('product', 'tr', 'paketler'),
            ('product', 'tr', 'var mı'),
        ]
        
        created_count = 0
        skipped_count = 0
        
        for intent, lang, keyword in product_inquiry_keywords:
            # Check if already exists (global keywords have user=None)
            exists = IntentKeyword.objects.filter(
                user__isnull=True,
                intent=intent,
                language=lang,
                keyword=keyword
            ).exists()
            
            if not exists:
                IntentKeyword.objects.create(
                    user=None,  # Global keyword
                    intent=intent,
                    language=lang,
                    keyword=keyword
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Added: {intent} ({lang}): "{keyword}"'))
            else:
                skipped_count += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully added {created_count} new keywords'))
        self.stdout.write(self.style.WARNING(f'⏭️  Skipped {skipped_count} existing keywords'))
        self.stdout.write('')
        self.stdout.write('🎯 Now queries like "ممد داری؟" or "چه محصولاتی دارین؟" will route to products!')

