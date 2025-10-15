"""
Persona Extractor - Extract user persona from Instagram bio
Lightweight, rule-based extraction (no ML required)
Safe fallback to neutral if bio is empty

Author: FIKO AI Team
Date: October 2025
Version: 1.0
"""
import re
import logging
from typing import Dict, List, Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PersonaExtractor:
    """
    Extract persona info from Instagram biography
    
    Features:
    - Interest detection (multilingual: FA, EN)
    - Tone preference detection (formal, friendly, neutral)
    - Profession detection
    - Safe fallback for empty bios
    - 30-day caching
    
    Usage:
        persona = PersonaExtractor.extract_persona(bio, username)
        # Returns: {'interests': [...], 'tone_preference': 'friendly', 'profession': 'entrepreneur'}
    """
    
    # Interest patterns (multilingual: FA + EN + emojis)
    INTEREST_PATTERNS = {
        'coffee': [
            r'coffee\s*lover', r'☕', r'espresso', r'barista', r'caffeine',
            r'قهوه', r'کافه', r'قهوه‌خور', r'اسپرسو'
        ],
        'camping': [
            r'camp(ing|er)', r'outdoor', r'hiking', r'⛺', r'nature',
            r'کمپ', r'طبیعت‌گردی', r'کوهنورد'
        ],
        'travel': [
            r'travel(er|ler)', r'wanderlust', r'✈️', r'🌍', r'globe\s*trotter',
            r'مسافر', r'سفر', r'گردشگر', r'جهانگرد'
        ],
        'fitness': [
            r'fitness', r'gym', r'workout', r'💪', r'athlete', r'bodybuilding',
            r'ورزش', r'بدنساز', r'فیتنس', r'باشگاه'
        ],
        'tech': [
            r'tech(nology)?', r'developer', r'coder', r'💻', r'startup', r'software',
            r'برنامه‌نویس', r'توسعه‌دهنده', r'تکنولوژی', r'استارتاپ'
        ],
        'food': [
            r'foodie', r'chef', r'cooking', r'🍕', r'🍔', r'culinary',
            r'آشپز', r'غذا', r'آشپزی'
        ],
        'fashion': [
            r'fashion', r'style', r'designer', r'👗', r'👔', r'boutique',
            r'مد', r'طراح', r'فشن', r'لباس'
        ],
        'photography': [
            r'photograph(y|er)', r'📷', r'📸', r'camera', r'shoot',
            r'عکاس', r'عکاسی', r'فتوگراف'
        ],
        'music': [
            r'music', r'musician', r'🎵', r'🎶', r'singer', r'dj',
            r'موسیقی', r'آهنگ', r'خواننده'
        ],
        'art': [
            r'artist', r'art', r'🎨', r'creative', r'painter',
            r'هنرمند', r'نقاش', r'هنری'
        ],
        'business': [
            r'business', r'entrepreneur', r'startup', r'founder',
            r'کسب‌وکار', r'کارآفرین', r'بنیانگذار'
        ],
        'beauty': [
            r'beauty', r'makeup', r'💄', r'skincare', r'cosmetic',
            r'آرایش', r'زیبایی', r'آرایشگر'
        ]
    }
    
    # Profession patterns
    PROFESSION_PATTERNS = {
        'entrepreneur': [
            r'founder', r'ceo', r'entrepreneur', r'startup', r'co-?founder',
            r'بنیانگذار', r'مدیرعامل', r'کارآفرین'
        ],
        'designer': [
            r'designer', r'ui/ux', r'creative\s+director', r'graphic\s+designer',
            r'طراح', r'دیزاینر'
        ],
        'coach': [
            r'coach', r'trainer', r'mentor', r'consultant',
            r'مربی', r'کوچ', r'مشاور'
        ],
        'developer': [
            r'developer', r'engineer', r'programmer', r'software',
            r'برنامه‌نویس', r'مهندس', r'توسعه‌دهنده'
        ],
        'content_creator': [
            r'creator', r'influencer', r'youtuber', r'blogger', r'vlogger',
            r'تولیدکننده\s+محتوا', r'اینفلوئنسر'
        ],
        'photographer': [
            r'photographer', r'photo\s+artist',
            r'عکاس', r'فتوگراف'
        ],
        'chef': [
            r'chef', r'cook', r'culinary',
            r'آشپز', r'سرآشپز'
        ],
        'artist': [
            r'artist', r'painter', r'sculptor',
            r'هنرمند', r'نقاش'
        ]
    }
    
    # Negative patterns (to avoid false positives)
    NEGATIVE_PATTERNS = [
        r'hate\s+{keyword}',
        r'not\s+(a\s+)?{keyword}',
        r'anti[- ]{keyword}',
        r'don\'t\s+like\s+{keyword}'
    ]
    
    @classmethod
    def extract_persona(cls, bio: str, username: str = None, source: str = 'instagram') -> Dict:
        """
        Extract persona from user biography
        
        Args:
            bio: User's biography text (from Instagram, etc.)
            username: User's username (optional, for logging)
            source: Source platform (default: 'instagram')
        
        Returns:
            {
                'interests': ['coffee', 'travel'],
                'tone_preference': 'friendly',
                'profession': 'entrepreneur',
                'source': 'instagram',
                'extracted_at': '2025-10-11T10:30:00Z'
            }
        """
        if not bio or not bio.strip():
            logger.info(f"📊 Empty bio for {username or 'unknown'}, using default persona")
            return cls._default_persona(source)
        
        bio = bio.strip()
        
        # Extract components
        interests = cls._extract_interests(bio)
        tone = cls._detect_tone(bio)
        profession = cls._detect_profession(bio)
        
        persona = {
            'interests': interests,
            'tone_preference': tone,
            'profession': profession,
            'source': source,
            'extracted_at': cls._get_timestamp()
        }
        
        logger.info(
            f"📊 Extracted persona for {username or 'unknown'}: "
            f"interests={interests}, tone={tone}, profession={profession}"
        )
        
        return persona
    
    @classmethod
    def _extract_interests(cls, bio: str) -> List[str]:
        """
        Extract interests from bio using smart pattern matching
        
        Algorithm:
        1. Check positive patterns for each interest
        2. Verify it's not a negative mention
        3. Return unique interests
        """
        bio_lower = bio.lower()
        interests = []
        
        for interest, patterns in cls.INTEREST_PATTERNS.items():
            matched = False
            
            for pattern in patterns:
                if re.search(pattern, bio_lower, re.IGNORECASE):
                    # Check if it's NOT a negative mention
                    is_negative = cls._is_negative_mention(bio_lower, interest)
                    
                    if not is_negative:
                        interests.append(interest)
                        matched = True
                        break  # فقط یک بار اضافه کن
            
            if matched:
                continue
        
        return list(set(interests))  # Remove duplicates
    
    @classmethod
    def _is_negative_mention(cls, bio_lower: str, keyword: str) -> bool:
        """Check if keyword is mentioned negatively"""
        for neg_pattern in cls.NEGATIVE_PATTERNS:
            pattern = neg_pattern.format(keyword=keyword)
            if re.search(pattern, bio_lower):
                return True
        return False
    
    @classmethod
    def _detect_tone(cls, bio: str) -> str:
        """
        Detect tone preference from bio
        
        Returns: 'formal', 'friendly', or 'neutral'
        
        Algorithm:
        1. Count emojis (more emojis → friendly)
        2. Check formal keywords (CEO, Director → formal)
        3. Check friendly keywords (lover, passionate → friendly)
        4. Decide based on scores
        """
        bio_lower = bio.lower()
        
        # Count emojis (including Persian/Arabic)
        emoji_pattern = r'[😀-🙏💀-🛿⛺☕✈️🌍💪💻📷📸🎵🎶🎨💄👗👔🍕🍔]'
        emoji_count = len(re.findall(emoji_pattern, bio))
        
        # Formal signals
        formal_keywords = [
            'founder', 'ceo', 'director', 'professional', 'consultant',
            'executive', 'manager', 'official',
            'مدیرعامل', 'بنیانگذار', 'مدیر', 'مشاور'
        ]
        formal_score = sum(1 for kw in formal_keywords if kw in bio_lower)
        
        # Friendly signals
        friendly_keywords = [
            'lover', 'passionate', 'enthusiast', 'addict', 'fan', 
            'love', 'crazy about', 'obsessed',
            'عاشق', 'علاقه‌مند'
        ]
        friendly_score = sum(1 for kw in friendly_keywords if kw in bio_lower)
        
        # Casual signals
        casual_keywords = [
            'vibes', 'chill', 'just', 'random', 'lol', 'haha',
            'fun', 'enjoying life'
        ]
        casual_score = sum(1 for kw in casual_keywords if kw in bio_lower)
        
        # Decision logic
        if formal_score >= 2:
            return 'formal'
        elif emoji_count >= 3 or friendly_score >= 2 or casual_score >= 2:
            return 'friendly'
        else:
            return 'neutral'
    
    @classmethod
    def _detect_profession(cls, bio: str) -> Optional[str]:
        """
        Detect profession from bio
        
        Returns: profession name or None
        """
        bio_lower = bio.lower()
        
        for profession, patterns in cls.PROFESSION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, bio_lower, re.IGNORECASE):
                    return profession
        
        return None
    
    @classmethod
    def _default_persona(cls, source: str = 'unknown') -> Dict:
        """Default persona for empty bio or errors"""
        return {
            'interests': [],
            'tone_preference': 'neutral',
            'profession': None,
            'source': source,
            'extracted_at': cls._get_timestamp()
        }
    
    @classmethod
    def _get_timestamp(cls) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    @classmethod
    def get_cached_persona(cls, customer_id: int) -> Dict:
        """
        Get persona from cache or return default
        
        Args:
            customer_id: Customer ID
        
        Returns:
            Cached persona or default persona
        """
        cache_key = f"persona:{customer_id}"
        persona = cache.get(cache_key)
        
        if persona:
            logger.debug(f"✅ Persona cache hit for customer {customer_id}")
            return persona
        
        logger.debug(f"⚠️ Persona cache miss for customer {customer_id}")
        return cls._default_persona()
    
    @classmethod
    def cache_persona(cls, customer_id: int, persona: Dict, timeout: int = 30*24*60*60):
        """
        Cache persona for 30 days
        
        Args:
            customer_id: Customer ID
            persona: Persona dictionary
            timeout: Cache timeout in seconds (default: 30 days)
        """
        cache_key = f"persona:{customer_id}"
        cache.set(cache_key, persona, timeout)
        logger.info(f"💾 Cached persona for customer {customer_id} (30 days)")
    
    @classmethod
    def invalidate_cache(cls, customer_id: int):
        """Invalidate cached persona for a customer"""
        cache_key = f"persona:{customer_id}"
        cache.delete(cache_key)
        logger.info(f"🗑️ Invalidated persona cache for customer {customer_id}")
    
    @classmethod
    def extract_and_cache(cls, customer_id: int, bio: str, username: str = None, source: str = 'instagram') -> Dict:
        """
        Extract persona and cache it in one step
        
        Args:
            customer_id: Customer ID
            bio: Biography text
            username: Username (optional)
            source: Source platform
        
        Returns:
            Extracted persona
        """
        persona = cls.extract_persona(bio, username, source)
        cls.cache_persona(customer_id, persona)
        return persona

