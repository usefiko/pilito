"""
Utility for extracting CTA (Call-to-Action) buttons from AI responses.
Format: [[CTA:Title|https://example.com]]

این utility در message/utils قرار دارد چون:
- CTA ربط به message و کانال‌ها دارد، نه فقط AI
- می‌تواند در workflows، manual messages و جاهای دیگر استفاده شود
- multi-channel support (Instagram, WhatsApp, Telegram, Web)
"""
import re
import logging
from typing import Tuple, Optional, List, Dict

logger = logging.getLogger(__name__)

# Pattern for CTA token: [[CTA:Title|URL]]
CTA_PATTERN = r'\[\[CTA:([^\|]+)\|([^\]]+)\]\]'


def extract_cta_from_text(text: str) -> Tuple[str, Optional[List[Dict]]]:
    """
    Extract CTA buttons from text and return clean text + buttons list.
    
    Args:
        text: Message text that may contain [[CTA:Title|URL]] tokens
        
    Returns:
        Tuple of (clean_text, buttons_list or None)
        
    Example:
        Input: "برای اطلاعات بیشتر [[CTA:سایت فیکو|https://fiko.ai]] ببینید"
        Output: ("برای اطلاعات بیشتر ببینید", [{"type": "web_url", "title": "سایت فیکو", "url": "https://fiko.ai"}])
    
    Notes:
        - فقط روی پیام‌های AI یا system اعمال شود، نه پیام‌های customer
        - حداکثر 3 دکمه (محدودیت Instagram)
        - عنوان دکمه حداکثر 20 کاراکتر
        - فقط http:// و https:// مجاز است
    """
    if not text:
        return text, None
    
    # Find all CTA tokens
    matches = re.findall(CTA_PATTERN, text)
    
    if not matches:
        return text, None
    
    buttons = []
    for title, url in matches:
        title = title.strip()
        url = url.strip()
        
        # Validation
        if not url or not _is_valid_url(url):
            logger.warning(f"⚠️ Invalid URL in CTA token: {url}")
            continue
        
        # Instagram button title limit: ~20 characters
        if len(title) > 20:
            logger.debug(f"CTA title too long ({len(title)} chars), truncating: {title}")
            title = title[:17] + "..."
        
        if not title:
            title = "لینک"  # Fallback title
        
        buttons.append({
            "type": "web_url",
            "title": title,
            "url": url,
        })
    
    # Remove CTA tokens from text
    clean_text = re.sub(CTA_PATTERN, '', text)
    
    # ✅ حذف فاصله‌های اضافی (نکته از review)
    clean_text = re.sub(r'\s{2,}', ' ', clean_text).strip()
    
    # Instagram max 3 buttons
    if len(buttons) > 3:
        logger.warning(f"⚠️ Too many CTA buttons ({len(buttons)}), keeping first 3")
        buttons = buttons[:3]
    
    if buttons:
        logger.info(f"✅ Extracted {len(buttons)} CTA button(s) from text")
    
    return clean_text, buttons if buttons else None


def _is_valid_url(url: str) -> bool:
    """
    Basic URL validation for security.
    Only allows http:// and https://
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid and safe
        
    Notes:
        - فقط http:// و https:// مجاز
        - حداکثر طول 2000 کاراکتر (محدودیت Instagram)
    """
    if not url:
        return False
    
    url_lower = url.lower()
    
    # Only allow http/https
    if not (url_lower.startswith('http://') or url_lower.startswith('https://')):
        logger.warning(f"⚠️ URL must start with http:// or https://: {url}")
        return False
    
    # Basic length check (Instagram URL limit)
    if len(url) > 2000:
        logger.warning(f"⚠️ URL too long ({len(url)} chars, max 2000): {url[:50]}...")
        return False
    
    return True

