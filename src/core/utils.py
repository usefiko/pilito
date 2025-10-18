"""
Utility functions برای مدیریت پروکسی در درخواست‌های HTTP
"""
import logging
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_active_proxy() -> Dict[str, str]:
    """
    برگرداندن پروکسی فعال برای استفاده در requests
    
    Returns:
        dict: دیکشنری حاوی http و https proxy
        مثال: {"http": "http://user:pass@ip:port", "https": "http://user:pass@ip:port"}
        
    Usage:
        response = requests.get(url, proxies=get_active_proxy())
    """
    try:
        from .models import ProxySetting
        
        proxy = ProxySetting.objects.filter(is_active=True).first()
        if proxy:
            logger.debug(f"🔒 Using proxy: {proxy.name}")
            # ✅ Fixتبدیل به lowercase برای سازگاری با requests library
            http_proxy = proxy.http_proxy.lower() if proxy.http_proxy.startswith(('HTTP://', 'HTTPS://')) else proxy.http_proxy
            https_proxy = proxy.https_proxy.lower() if proxy.https_proxy.startswith(('HTTP://', 'HTTPS://')) else proxy.https_proxy
            
            return {
                "http": http_proxy,
                "https": https_proxy
            }
        
        logger.debug("⚠️ No active proxy found - direct connection will be used")
        return {}
        
    except Exception as e:
        logger.error(f"❌ Error getting active proxy: {e}")
        return {}


def get_fallback_proxy() -> Dict[str, str]:
    """
    برگرداندن پروکسی پشتیبان در صورت خرابی پروکسی اصلی
    
    Returns:
        dict: دیکشنری حاوی fallback http و https proxy
        
    Usage:
        try:
            response = requests.get(url, proxies=get_active_proxy())
        except:
            response = requests.get(url, proxies=get_fallback_proxy())
    """
    try:
        from .models import ProxySetting
        
        proxy = ProxySetting.objects.filter(is_active=True).first()
        if proxy and proxy.fallback_http_proxy:
            logger.info(f"🔄 Using fallback proxy: {proxy.name}")
            # ✅ Fix: تبدیل به lowercase برای سازگاری با requests library
            fallback_http = proxy.fallback_http_proxy.lower() if proxy.fallback_http_proxy.startswith(('HTTP://', 'HTTPS://')) else proxy.fallback_http_proxy
            fallback_https = proxy.fallback_https_proxy.lower() if proxy.fallback_https_proxy and proxy.fallback_https_proxy.startswith(('HTTP://', 'HTTPS://')) else proxy.fallback_https_proxy
            
            return {
                "http": fallback_http,
                "https": fallback_https
            }
        
        logger.debug("⚠️ No fallback proxy configured")
        return {}
        
    except Exception as e:
        logger.error(f"❌ Error getting fallback proxy: {e}")
        return {}


def make_request_with_proxy(
    method: str, 
    url: str, 
    use_fallback: bool = True,
    **kwargs
) -> requests.Response:
    """
    Helper function برای انجام درخواست‌های HTTP با پروکسی و fallback خودکار
    
    Args:
        method: نوع درخواست (get, post, put, delete, etc.)
        url: آدرس URL
        use_fallback: استفاده از fallback در صورت خرابی (پیش‌فرض: True)
        **kwargs: پارامترهای دیگه برای requests (params, json, headers, timeout, etc.)
    
    Returns:
        requests.Response: پاسخ درخواست
        
    Raises:
        requests.exceptions.RequestException: در صورت خرابی هر دو پروکسی
    
    Usage:
        # GET request
        response = make_request_with_proxy('get', url, params=params, timeout=10)
        
        # POST request
        response = make_request_with_proxy('post', url, json=data, timeout=30)
    """
    # اول با پروکسی اصلی امتحان کن
    try:
        proxies = get_active_proxy()
        if proxies:
            kwargs['proxies'] = proxies
            
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response
        
    except Exception as primary_error:
        logger.warning(f"⚠️ Primary proxy failed for {method.upper()} {url}: {primary_error}")
        
        # اگر fallback فعال باشه، با fallback proxy امتحان کن
        if use_fallback:
            try:
                fallback_proxies = get_fallback_proxy()
                if fallback_proxies:
                    kwargs['proxies'] = fallback_proxies
                    logger.info(f"🔄 Retrying {method.upper()} {url} with fallback proxy...")
                    
                    response = requests.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
                else:
                    logger.debug("No fallback proxy configured, raising original error")
                    
            except Exception as fallback_error:
                logger.error(f"❌ Fallback proxy also failed for {method.upper()} {url}: {fallback_error}")
        
        # اگر fallback هم fail شد یا غیرفعال بود، error اصلی رو raise کن
        raise primary_error

