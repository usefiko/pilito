"""
Query Router - Intent Classification
Routes user queries to appropriate knowledge sources
Supports multilingual keyword matching (FA, EN, AR, TR)
"""
import logging
from typing import Dict, List
from django.core.cache import cache
from django.db import models

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Hybrid intent classification using keyword matching
    Fast, rule-based routing for multilingual queries
    """
    
    # Default keywords (fallback if DB is empty)
    DEFAULT_KEYWORDS = {
        'pricing': {
            'fa': ['قیمت', 'هزینه', 'تعرفه', 'پلن', 'پکیج', 'اشتراک', 'خرید', 'فروش', 'تومان', 'دلار', 'پرداخت'],
            'en': ['price', 'cost', 'pricing', 'plan', 'package', 'subscription', 'buy', 'purchase', 'payment', 'dollar'],
            'ar': ['سعر', 'تكلفة', 'خطة', 'اشتراك', 'شراء', 'دفع'],
            'tr': ['fiyat', 'maliyet', 'plan', 'paket', 'abonelik', 'satın', 'ödeme']
        },
        'product': {
            'fa': ['محصول', 'سرویس', 'خدمات', 'ویژگی', 'امکانات', 'قابلیت', 'چیه', 'چیست'],
            'en': ['product', 'service', 'feature', 'functionality', 'capability', 'what does', 'what is'],
            'ar': ['منتج', 'خدمة', 'ميزة', 'وظيفة', 'ما هو'],
            'tr': ['ürün', 'hizmet', 'özellik', 'fonksiyon', 'nedir']
        },
        'howto': {
            'fa': ['چطور', 'چگونه', 'راهنما', 'آموزش', 'نحوه', 'روش', 'مراحل', 'کمک'],
            'en': ['how', 'guide', 'tutorial', 'steps', 'instruction', 'way to', 'how do i', 'help'],
            'ar': ['كيف', 'دليل', 'تعليمات', 'خطوات', 'مساعدة'],
            'tr': ['nasıl', 'rehber', 'öğretici', 'adımlar', 'yardım']
        },
        'contact': {
            'fa': ['تماس', 'ارتباط', 'پشتیبانی', 'شماره', 'ایمیل', 'آدرس', 'ساعت کاری', 'تلفن', 'بیوگرافی', 'بیو', 'درباره', 'درباره ما', 'کی هستیم', 'چه کسی', 'ما', 'مزون'],
            'en': ['contact', 'support', 'phone', 'email', 'address', 'reach', 'hours', 'location', 'call', 'about', 'about us', 'who are', 'bio', 'biography'],
            'ar': ['اتصال', 'دعم', 'هاتف', 'بريد', 'عنوان', 'موقع', 'من نحن', 'نبذة'],
            'tr': ['iletişim', 'destek', 'telefon', 'e-posta', 'adres', 'konum', 'hakkında', 'biz kimiz']
        }
    }
    
    # Default routing configuration
    DEFAULT_ROUTING = {
        'pricing': {
            'primary_source': 'faq',
            'secondary_sources': ['products', 'manual'],
            'token_budget': {'primary': 800, 'secondary': 300}
        },
        'product': {
            'primary_source': 'products',
            'secondary_sources': ['faq', 'website'],
            'token_budget': {'primary': 800, 'secondary': 300}
        },
        'howto': {
            'primary_source': 'manual',
            'secondary_sources': ['faq', 'website'],
            'token_budget': {'primary': 800, 'secondary': 300}
        },
        'contact': {
            'primary_source': 'manual',
            'secondary_sources': ['website'],
            'token_budget': {'primary': 800, 'secondary': 300}
        },
        'general': {
            'primary_source': 'faq',
            'secondary_sources': ['manual'],
            'token_budget': {'primary': 800, 'secondary': 300}
        }
    }
    
    @classmethod
    def route_query(cls, user_message: str, user=None) -> Dict:
        """
        Classify user intent and determine routing
        
        Args:
            user_message: User's question/message
            user: User instance (optional, for per-user keywords)
        
        Returns:
            {
                'intent': 'pricing',
                'confidence': 0.85,
                'primary_source': 'faq',
                'secondary_sources': ['products'],
                'token_budgets': {'primary': 800, 'secondary': 300},
                'keywords_matched': ['قیمت', 'پلن'],
                'detected_product': 'کت هرمس',
                'method': 'keyword_based'
            }
        """
        if not user_message or not user_message.strip():
            return cls._get_default_routing()
        
        # 🔍 Product Name Detection (before intent classification)
        detected_product = cls._detect_product_name(user_message, user)
        
        # Load keywords (from DB or defaults)
        keywords = cls._load_keywords(user)
        
        # Score each intent based on keyword matching
        intent_scores = {}
        matched_keywords = []
        
        message_lower = user_message.lower()
        
        for intent, lang_keywords in keywords.items():
            score = 0.0
            for lang, kw_list in lang_keywords.items():
                for keyword in kw_list:
                    if keyword.lower() in message_lower:
                        weight = cls._get_keyword_weight(keyword, user)
                        score += weight
                        matched_keywords.append(keyword)
            
            intent_scores[intent] = score
        
        # Determine best intent
        if all(s == 0 for s in intent_scores.values()):
            # No keywords matched → general intent
            best_intent = 'general'
            confidence = 0.5
        else:
            best_intent = max(intent_scores, key=intent_scores.get)
            max_score = intent_scores[best_intent]
            total_score = sum(intent_scores.values())
            confidence = min(max_score / total_score if total_score > 0 else 0.5, 1.0)
        
        # Get routing config
        routing = cls._load_routing_config(best_intent)
        
        # 🎯 Dynamic Routing: Add 'products' if product detected
        routing = cls._enhance_routing_with_product(
            routing=routing,
            detected_product=detected_product,
            intent=best_intent
        )
        
        logger.info(
            f"🎯 Intent: {best_intent} (confidence: {confidence:.2f}) "
            f"→ {routing['primary_source']} | Keywords: {matched_keywords[:3]}"
            f"{' | Product: ' + detected_product if detected_product else ''}"
        )
        
        return {
            'intent': best_intent,
            'confidence': confidence,
            'primary_source': routing['primary_source'],
            'secondary_sources': routing['secondary_sources'],
            'token_budgets': routing['token_budget'],
            'keywords_matched': matched_keywords,
            'detected_product': detected_product,
            'method': 'keyword_based'
        }
    
    @classmethod
    def _load_keywords(cls, user=None) -> Dict:
        """
        Load keywords from IntentKeyword model (database only)
        
        ⚠️ IMPORTANT: All keywords should be in database!
        Run: python manage.py seed_default_keywords to populate defaults
        
        Priority:
        1. User-specific keywords (if user provided)
        2. Global keywords from database
        3. Fallback to defaults (only if DB is empty - should not happen in production)
        
        Caches results for 1 hour
        """
        cache_key = f"intent_keywords:{user.id if user else 'global'}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            from AI_model.models import IntentKeyword
            
            # Get all intents from DB (or use defaults as fallback)
            # First, check what intents exist in DB
            db_intents = set(
                IntentKeyword.objects.filter(
                    is_active=True,
                    user__isnull=True  # Only global for intent discovery
                ).values_list('intent', flat=True).distinct()
            )
            
            # Use DB intents if available, otherwise use default intents
            intents_to_check = db_intents if db_intents else set(cls.DEFAULT_KEYWORDS.keys())
            
            # Get keywords from DB (global + user-specific)
            db_keywords = {intent: {} for intent in intents_to_check}
            
            for intent in intents_to_check:
                for lang in ['fa', 'en', 'ar', 'tr']:
                    # Get user-specific keywords first (if user provided)
                    user_keywords = []
                    if user:
                        user_keywords = list(
                            IntentKeyword.objects.filter(
                                intent=intent,
                                language=lang,
                                is_active=True,
                                user=user
                            ).values_list('keyword', flat=True)
                        )
                    
                    # Get global keywords
                    global_keywords = list(
                        IntentKeyword.objects.filter(
                        intent=intent,
                        language=lang,
                            is_active=True,
                            user__isnull=True
                    ).values_list('keyword', flat=True)
                    )
                    
                    # Combine: user-specific first, then global
                    # User-specific keywords override global ones (no duplicates)
                    all_keywords = list(dict.fromkeys(user_keywords + global_keywords))  # Preserve order, remove duplicates
                    
                    if all_keywords:
                        db_keywords[intent][lang] = all_keywords
            
            # Check if DB has any keywords
            has_data = any(
                any(db_keywords[intent].values()) 
                for intent in db_keywords
            )
            
            if not has_data:
                # ⚠️ No keywords in DB → use defaults as fallback (should not happen in production)
                logger.warning(
                    "⚠️ No keywords found in database! Using fallback defaults. "
                    "Run: python manage.py seed_default_keywords to populate database."
                )
                db_keywords = cls.DEFAULT_KEYWORDS
            else:
                # ✅ DB has keywords → use ONLY database keywords (no fallback to defaults)
                # Fill missing intent/lang combinations with empty list (not defaults)
                for intent in intents_to_check:
                    for lang in ['fa', 'en', 'ar', 'tr']:
                        if lang not in db_keywords[intent]:
                            db_keywords[intent][lang] = []  # Empty, not default
                
                logger.info(
                    f"✅ Using DB keywords only: "
                    f"{sum(len(langs) for langs in db_keywords.values())} intent/lang combinations, "
                    f"{sum(sum(len(kw_list) for kw_list in langs.values()) for langs in db_keywords.values())} total keywords"
                )
            
            # Cache for 1 hour
            cache.set(cache_key, db_keywords, 3600)
            return db_keywords
            
        except Exception as e:
            logger.error(f"❌ Failed to load keywords from DB: {e}, using fallback defaults")
            logger.warning("⚠️ This should not happen in production. Check database connection.")
            return cls.DEFAULT_KEYWORDS
    
    @classmethod
    def _load_routing_config(cls, intent: str) -> Dict:
        """
        Load routing configuration from IntentRouting model or use defaults
        Caches results for 1 hour
        """
        cache_key = f"intent_routing:{intent}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            from AI_model.models import IntentRouting
            
            routing_obj = IntentRouting.objects.filter(
                intent=intent,
                is_active=True
            ).first()
            
            if routing_obj:
                config = {
                    'primary_source': routing_obj.primary_source,
                    'secondary_sources': routing_obj.secondary_sources,
                    'token_budget': {
                        'primary': routing_obj.primary_token_budget,
                        'secondary': routing_obj.secondary_token_budget
                    }
                }
                # Cache for 1 hour
                cache.set(cache_key, config, 3600)
                return config
            
        except Exception as e:
            logger.warning(f"Failed to load routing config from DB: {e}, using defaults")
        
        # Fallback to defaults
        return cls.DEFAULT_ROUTING.get(intent, cls.DEFAULT_ROUTING['general'])
    
    @classmethod
    def _get_keyword_weight(cls, keyword: str, user=None) -> float:
        """Get keyword weight from DB or default to 1.0"""
        try:
            from AI_model.models import IntentKeyword
            kw_obj = IntentKeyword.objects.filter(
                keyword=keyword,
                is_active=True
            ).filter(
                models.Q(user=user) | models.Q(user__isnull=True)
            ).first()
            
            return kw_obj.weight if kw_obj else 1.0
        except:
            return 1.0
    
    @classmethod
    def _get_default_routing(cls) -> Dict:
        """Return default routing for empty/invalid queries"""
        return {
            'intent': 'general',
            'confidence': 0.5,
            'primary_source': 'faq',
            'secondary_sources': ['manual'],
            'token_budgets': {'primary': 800, 'secondary': 300},
            'keywords_matched': [],
            'detected_product': None,
            'method': 'keyword_based'
        }
    
    @classmethod
    def _detect_product_name(cls, user_message: str, user) -> str:
        """
        Detect product name in user query
        
        Strategy:
        1. Exact match: "کت هرمس" in query
        2. Partial match: "کت هرمس" matches "کت هرمس Elmos"
        3. Fuzzy match: First 2-3 words of product title
        
        Args:
            user_message: User's question
            user: User instance
            
        Returns:
            Product title if found, None otherwise
        """
        if not user or not user_message:
            return None
        
        try:
            from web_knowledge.models import Product
            
            # Get active products (cached for 5 minutes)
            cache_key = f"active_products:{user.id}"
            products = cache.get(cache_key)
            
            if products is None:
                products = list(Product.objects.filter(
                    user=user,
                    is_active=True
                ).values_list('title', flat=True))
                
                # Cache for 5 minutes
                cache.set(cache_key, products, 300)
            
            if not products:
                return None
            
            query_lower = user_message.lower()
            
            # 1. Exact match (full product name in query)
            for title in products:
                title_lower = title.lower()
                if title_lower in query_lower:
                    logger.debug(f"🔍 Product detected (exact): '{title}'")
                    return title
            
            # 2. Partial match (query contains product name)
            for title in products:
                title_lower = title.lower()
                if query_lower in title_lower:
                    logger.debug(f"🔍 Product detected (partial): '{title}'")
                    return title
            
            # 3. Fuzzy match (first 2-3 words of product title)
            for title in products:
                title_words = title.lower().split()
                
                # Try first 2 words
                if len(title_words) >= 2:
                    first_two = ' '.join(title_words[:2])
                    if first_two in query_lower:
                        logger.debug(f"🔍 Product detected (fuzzy 2-word): '{title}'")
                        return title
                
                # Try first 3 words (for longer product names)
                if len(title_words) >= 3:
                    first_three = ' '.join(title_words[:3])
                    if first_three in query_lower:
                        logger.debug(f"🔍 Product detected (fuzzy 3-word): '{title}'")
                        return title
            
            # No product found
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Product detection failed: {e}")
            return None
    
    @classmethod
    def _enhance_routing_with_product(
        cls,
        routing: Dict,
        detected_product: str,
        intent: str
    ) -> Dict:
        """
        Enhance routing by adding 'products' to secondary sources if product detected
        
        Rules:
        1. If product detected AND 'products' not in primary/secondary → add to secondary
        2. If intent is already 'product' → don't modify (already optimal)
        3. If intent is 'pricing' → don't modify ('products' already in secondary)
        4. Otherwise → add 'products' to secondary sources
        
        Args:
            routing: Current routing configuration
            detected_product: Detected product name (or None)
            intent: Classified intent
            
        Returns:
            Enhanced routing configuration
        """
        # Make a copy to avoid modifying original
        routing = routing.copy()
        routing['secondary_sources'] = routing['secondary_sources'].copy()
        
        if not detected_product:
            # No product detected, return as-is
            return routing
        
        # Check if 'products' is already in primary or secondary
        if routing['primary_source'] == 'products':
            # Already optimal (intent is 'product')
            logger.debug("✅ Product intent already routes to products (no change)")
            return routing
        
        if 'products' in routing['secondary_sources']:
            # Already included (e.g., intent is 'pricing')
            logger.debug("✅ Products already in secondary sources (no change)")
            return routing
        
        # Add 'products' to secondary sources
        routing['secondary_sources'].append('products')
        logger.info(
            f"🎯 Product detected ('{detected_product}') → "
            f"Added 'products' to secondary sources for intent '{intent}'"
        )
        
        return routing

