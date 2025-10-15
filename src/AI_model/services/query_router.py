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
            'fa': ['تماس', 'ارتباط', 'پشتیبانی', 'شماره', 'ایمیل', 'آدرس', 'ساعت کاری', 'تلفن'],
            'en': ['contact', 'support', 'phone', 'email', 'address', 'reach', 'hours', 'location', 'call'],
            'ar': ['اتصال', 'دعم', 'هاتف', 'بريد', 'عنوان', 'موقع'],
            'tr': ['iletişim', 'destek', 'telefon', 'e-posta', 'adres', 'konum']
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
                'method': 'keyword_based'
            }
        """
        if not user_message or not user_message.strip():
            return cls._get_default_routing()
        
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
        
        logger.info(
            f"🎯 Intent: {best_intent} (confidence: {confidence:.2f}) "
            f"→ {routing['primary_source']} | Keywords: {matched_keywords[:3]}"
        )
        
        return {
            'intent': best_intent,
            'confidence': confidence,
            'primary_source': routing['primary_source'],
            'secondary_sources': routing['secondary_sources'],
            'token_budgets': routing['token_budget'],
            'keywords_matched': matched_keywords,
            'method': 'keyword_based'
        }
    
    @classmethod
    def _load_keywords(cls, user=None) -> Dict:
        """
        Load keywords from IntentKeyword model or use defaults
        Caches results for 1 hour
        """
        cache_key = f"intent_keywords:{user.id if user else 'global'}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            from AI_model.models import IntentKeyword
            
            # Get keywords from DB (global + user-specific)
            db_keywords = {intent: {} for intent in cls.DEFAULT_KEYWORDS.keys()}
            
            for intent in cls.DEFAULT_KEYWORDS.keys():
                for lang in ['fa', 'en', 'ar', 'tr']:
                    keywords = IntentKeyword.objects.filter(
                        intent=intent,
                        language=lang,
                        is_active=True
                    ).filter(
                        models.Q(user=user) | models.Q(user__isnull=True)
                    ).values_list('keyword', flat=True)
                    
                    if keywords:
                        db_keywords[intent][lang] = list(keywords)
            
            # Fallback to defaults if DB is empty
            has_data = any(
                any(db_keywords[intent].values()) 
                for intent in db_keywords
            )
            
            if not has_data:
                db_keywords = cls.DEFAULT_KEYWORDS
                logger.debug("Using default keywords (DB empty)")
            else:
                # Merge defaults with DB keywords
                for intent in cls.DEFAULT_KEYWORDS:
                    for lang in cls.DEFAULT_KEYWORDS[intent]:
                        if lang not in db_keywords[intent] or not db_keywords[intent][lang]:
                            db_keywords[intent][lang] = cls.DEFAULT_KEYWORDS[intent][lang]
            
            # Cache for 1 hour
            cache.set(cache_key, db_keywords, 3600)
            return db_keywords
            
        except Exception as e:
            logger.warning(f"Failed to load keywords from DB: {e}, using defaults")
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
            'method': 'keyword_based'
        }

