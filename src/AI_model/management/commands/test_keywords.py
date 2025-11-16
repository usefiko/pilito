"""
Management command برای تست keywords از database vs defaults
Usage: python manage.py test_keywords
"""

from django.core.management.base import BaseCommand
from django.db import models
from AI_model.models import IntentKeyword
from AI_model.services.query_router import QueryRouter
from accounts.models import User


class Command(BaseCommand):
    help = 'Test keywords loading from database vs defaults'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username or email to test with (optional)',
            default=None
        )

    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write(self.style.SUCCESS("🔍 تست Keywords: Database vs Defaults"))
        self.stdout.write("="*80)
        
        # Get user if provided
        user = None
        if options['user']:
            try:
                user = User.objects.get(username=options['user']) or User.objects.get(email=options['user'])
                self.stdout.write(f"\n👤 کاربر: {user.username} ({user.email})")
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠️ کاربر '{options['user']}' پیدا نشد - از global keywords استفاده می‌کنم"))
        
        # 1. بررسی Database Keywords
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write("1️⃣ بررسی Database Keywords")
        self.stdout.write(f"{'='*80}")
        
        db_keywords = IntentKeyword.objects.filter(is_active=True)
        if user:
            db_keywords = db_keywords.filter(models.Q(user=user) | models.Q(user__isnull=True))
        else:
            db_keywords = db_keywords.filter(user__isnull=True)  # Only global
        
        count = db_keywords.count()
        self.stdout.write(f"✅ تعداد Keywords در Database: {count}")
        
        if count > 0:
            self.stdout.write(f"\n📄 نمونه Keywords (اولین 10 تا):")
            for i, kw in enumerate(db_keywords[:10], 1):
                user_str = f"[{kw.user.username}]" if kw.user else "[Global]"
                self.stdout.write(f"  {i}. {user_str} {kw.get_language_display()} - {kw.get_intent_display()}: '{kw.keyword}' (weight: {kw.weight})")
        else:
            self.stdout.write(self.style.WARNING("⚠️ هیچ keyword در database نیست - از defaults استفاده می‌شود"))
        
        # 2. بررسی Default Keywords
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write("2️⃣ بررسی Default Keywords (هاردکد)")
        self.stdout.write(f"{'='*80}")
        
        default_keywords = QueryRouter.DEFAULT_KEYWORDS
        total_defaults = sum(len(langs) for langs in default_keywords.values())
        self.stdout.write(f"✅ تعداد Default Keywords: {total_defaults} intent/lang combinations")
        
        for intent, langs in default_keywords.items():
            total_kw = sum(len(kw_list) for kw_list in langs.values())
            self.stdout.write(f"  {intent}: {total_kw} keywords ({', '.join(langs.keys())})")
        
        # 3. تست Loading Keywords
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write("3️⃣ تست Loading Keywords (از QueryRouter)")
        self.stdout.write(f"{'='*80}")
        
        # Clear cache first
        from django.core.cache import cache
        cache_key = f"intent_keywords:{user.id if user else 'global'}"
        cache.delete(cache_key)
        self.stdout.write("✅ Cache cleared")
        
        # Load keywords
        loaded_keywords = QueryRouter._load_keywords(user)
        
        self.stdout.write(f"\n📊 Keywords Loaded:")
        for intent, langs in loaded_keywords.items():
            total_kw = sum(len(kw_list) for kw_list in langs.values())
            self.stdout.write(f"  {intent}: {total_kw} keywords")
            for lang, kw_list in langs.items():
                if kw_list:
                    self.stdout.write(f"    {lang}: {len(kw_list)} keywords (first 3: {kw_list[:3]})")
        
        # 4. مقایسه Database vs Loaded
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write("4️⃣ مقایسه Database vs Loaded")
        self.stdout.write(f"{'='*80}")
        
        # Check if loaded keywords match database
        if count > 0:
            # Check a specific intent/lang
            test_intent = 'contact'
            test_lang = 'fa'
            
            db_kw_list = list(
                db_keywords.filter(intent=test_intent, language=test_lang)
                .values_list('keyword', flat=True)
            )
            
            loaded_kw_list = loaded_keywords.get(test_intent, {}).get(test_lang, [])
            
            self.stdout.write(f"\n📊 مقایسه برای intent='{test_intent}', lang='{test_lang}':")
            self.stdout.write(f"  Database: {len(db_kw_list)} keywords")
            self.stdout.write(f"  Loaded: {len(loaded_kw_list)} keywords")
            
            if db_kw_list:
                self.stdout.write(f"  Database keywords: {db_kw_list[:5]}")
            if loaded_kw_list:
                self.stdout.write(f"  Loaded keywords: {loaded_kw_list[:5]}")
            
            # Check if they match
            if set(db_kw_list) == set(loaded_kw_list):
                self.stdout.write(self.style.SUCCESS("  ✅ Database و Loaded یکسان هستند!"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠️ Database و Loaded متفاوت هستند!"))
                only_in_db = set(db_kw_list) - set(loaded_kw_list)
                only_in_loaded = set(loaded_kw_list) - set(db_kw_list)
                if only_in_db:
                    self.stdout.write(f"    فقط در Database: {only_in_db}")
                if only_in_loaded:
                    self.stdout.write(f"    فقط در Loaded: {only_in_loaded}")
        else:
            self.stdout.write("⚠️ Database خالی است - از defaults استفاده می‌شود")
            # Check if loaded matches defaults
            if loaded_keywords == default_keywords:
                self.stdout.write(self.style.SUCCESS("  ✅ Loaded keywords = Default keywords (درست است)"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠️ Loaded keywords ≠ Default keywords (مشکل!)"))
        
        # 5. تست Routing با یک سوال واقعی
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write("5️⃣ تست Routing با سوال واقعی")
        self.stdout.write(f"{'='*80}")
        
        test_queries = [
            "یک بیوگرافی از مزونتون میدی بهم کامل",
            "قیمت کت هرمس چنده؟",
            "چطور میتونم خرید کنم؟",
        ]
        
        for query in test_queries:
            self.stdout.write(f"\n📝 سوال: '{query}'")
            routing = QueryRouter.route_query(query, user=user)
            self.stdout.write(f"  Intent: {routing['intent']} (confidence: {routing['confidence']:.2f})")
            self.stdout.write(f"  Primary Source: {routing['primary_source']}")
            self.stdout.write(f"  Keywords Matched: {routing.get('keywords_matched', [])[:3]}")
        
        # خلاصه
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write("📊 خلاصه:")
        self.stdout.write(f"{'='*80}")
        self.stdout.write(f"✅ Database Keywords: {count}")
        self.stdout.write(f"✅ Default Keywords: {total_defaults} intent/lang combinations")
        
        if count > 0:
            self.stdout.write(self.style.SUCCESS("\n✅ Database keywords وجود دارند - باید از database استفاده شود"))
        else:
            self.stdout.write(self.style.WARNING("\n⚠️ Database keywords وجود ندارند - از defaults استفاده می‌شود"))
            self.stdout.write("   → می‌توانید keywords را در admin panel اضافه کنید")
        
        self.stdout.write(f"\n💡 نکات:")
        self.stdout.write(f"   - Keywords در admin panel قابل مدیریت هستند")
        self.stdout.write(f"   - اگر database keywords وجود داشته باشد، از database استفاده می‌شود")
        self.stdout.write(f"   - اگر database خالی باشد، از DEFAULT_KEYWORDS استفاده می‌شود")
        self.stdout.write(f"   - Cache برای 1 ساعت ذخیره می‌شود")

