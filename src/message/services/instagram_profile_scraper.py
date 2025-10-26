"""
Instagram Profile Scraper Service using RapidAPI

This service fetches public Instagram profile data including biography
using a third-party API (instagram-looter2 via RapidAPI).

Legal & Ethical Considerations:
- Only fetches publicly available data
- Uses a legitimate third-party API service
- Respects rate limiting and caching
- Falls back gracefully on errors
"""

import json
import logging
from typing import Dict, Optional
from django.core.cache import cache
from django.conf import settings
from core.utils import make_request_with_proxy

logger = logging.getLogger(__name__)


class InstagramProfileScraper:
    """
    Fetch Instagram profile data using RapidAPI
    
    Configuration (add to settings):
    RAPIDAPI_KEY = "your-api-key"
    INSTAGRAM_PROFILE_CACHE_TTL = 30 * 24 * 60 * 60  # 30 days
    """
    
    API_HOST = "instagram-looter2.p.rapidapi.com"
    CACHE_PREFIX = "instagram_profile:"
    DEFAULT_CACHE_TTL = 30 * 24 * 60 * 60  # 30 days
    
    @classmethod
    def get_profile(cls, username: str, use_cache: bool = True) -> Dict:
        """
        Get Instagram profile data for a username
        
        Args:
            username: Instagram username
            use_cache: Whether to use cached data (default: True)
            
        Returns:
            Dict with keys:
                - username
                - full_name
                - biography
                - is_verified
                - is_private
                - followers_count
                - following_count
                - profile_pic_url
                - fetch_status: "ok" | "not_found" | "error" | "rate_limited" | "no_api_key" | "geo_blocked"
                - error_message: str (if error)
        """
        
        # Check cache first
        if use_cache:
            cached = cls._get_from_cache(username)
            if cached:
                logger.info(f"📦 Using cached Instagram profile for @{username}")
                return cached
        
        # Check if API key is configured
        api_key = getattr(settings, 'RAPIDAPI_KEY', None)
        if not api_key:
            logger.warning("⚠️ RAPIDAPI_KEY not configured, skipping Instagram profile fetch")
            return cls._error_response(username, "no_api_key", "RapidAPI key not configured")
        
        # Fetch from API
        try:
            logger.info(f"🔍 Fetching Instagram profile for @{username} via RapidAPI (with proxy)")
            
            # ✅ استفاده از make_request_with_proxy برای پشتیبانی از پروکسی و fallback
            url = f"https://{cls.API_HOST}/profile"
            
            headers = {
                'x-rapidapi-key': api_key,
                'x-rapidapi-host': cls.API_HOST
            }
            
            params = {
                'username': username
            }
            
            # ✅ Send request with automatic proxy fallback
            # Increased timeout to 30s for Iran proxy connections
            response = make_request_with_proxy(
                'get', 
                url, 
                params=params,
                headers=headers, 
                timeout=30,  # Increased from 15s to 30s for slow proxy connections
                use_fallback=True
            )
            
            # Parse response
            if response.status_code == 200:
                result = response.json()
                
                # Check if profile found
                if not result.get('status'):
                    logger.warning(f"❌ Profile not found for @{username}")
                    return cls._error_response(username, "not_found", "Profile not found")
                
                # Extract relevant data
                profile = cls._parse_profile(result, username)
                
                # Cache the result
                cls._save_to_cache(username, profile)
                
                logger.info(
                    f"✅ Fetched Instagram profile: @{username} "
                    f"(verified: {profile.get('is_verified')}, "
                    f"followers: {profile.get('followers_count')})"
                )
                
                return profile
                
            elif response.status_code == 429:
                logger.warning(f"⚠️ Rate limited by RapidAPI for @{username}")
                return cls._error_response(username, "rate_limited", "API rate limit exceeded")
                
            elif response.status_code == 451:
                logger.error(f"❌ Geographic restriction (451) for @{username} - proxy may be needed")
                return cls._error_response(username, "geo_blocked", "Service unavailable in this region")
                
            else:
                error_msg = f"API returned status {response.status_code}"
                logger.error(f"❌ Error fetching profile for @{username}: {error_msg}")
                logger.error(f"Response body: {response.text[:200]}")
                return cls._error_response(username, "error", error_msg)
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON response for @{username}: {e}")
            return cls._error_response(username, "error", "Invalid API response")
            
        except Exception as e:
            logger.error(f"❌ Exception fetching profile for @{username}: {e}")
            logger.error(f"    Error type: {type(e).__name__}")
            return cls._error_response(username, "error", str(e))
    
    @classmethod
    def _parse_profile(cls, data: Dict, username: str) -> Dict:
        """Parse API response into standardized format"""
        
        biography = data.get('biography', '')
        
        # Extract bio from biography_with_entities if available
        if not biography and 'biography_with_entities' in data:
            bio_entities = data['biography_with_entities']
            if isinstance(bio_entities, dict):
                biography = bio_entities.get('raw_text', '')
        
        return {
            'username': username,
            'full_name': data.get('full_name', ''),
            'biography': biography,
            'is_verified': data.get('is_verified', False),
            'is_private': data.get('is_private', False),
            'followers_count': data.get('edge_followed_by', {}).get('count', 0),
            'following_count': data.get('edge_follow', {}).get('count', 0),
            'profile_pic_url': data.get('profile_pic_url_hd') or data.get('profile_pic_url'),
            'fetch_status': 'ok',
            'source': 'rapidapi_instagram_looter'
        }
    
    @classmethod
    def _error_response(cls, username: str, status: str, message: str) -> Dict:
        """Create error response"""
        return {
            'username': username,
            'full_name': None,
            'biography': None,
            'is_verified': False,
            'is_private': None,
            'followers_count': None,
            'following_count': None,
            'profile_pic_url': None,
            'fetch_status': status,
            'error_message': message
        }
    
    @classmethod
    def _get_from_cache(cls, username: str) -> Optional[Dict]:
        """Get profile from cache"""
        cache_key = f"{cls.CACHE_PREFIX}{username.lower()}"
        return cache.get(cache_key)
    
    @classmethod
    def _save_to_cache(cls, username: str, profile: Dict):
        """Save profile to cache"""
        cache_key = f"{cls.CACHE_PREFIX}{username.lower()}"
        ttl = getattr(settings, 'INSTAGRAM_PROFILE_CACHE_TTL', cls.DEFAULT_CACHE_TTL)
        cache.set(cache_key, profile, ttl)
        logger.debug(f"💾 Cached Instagram profile for @{username} (TTL: {ttl}s)")
    
    @classmethod
    def invalidate_cache(cls, username: str):
        """Manually invalidate cache for a username"""
        cache_key = f"{cls.CACHE_PREFIX}{username.lower()}"
        cache.delete(cache_key)
        logger.info(f"🗑️ Invalidated cache for @{username}")

