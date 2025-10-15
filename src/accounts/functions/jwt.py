from datetime import datetime, timedelta
import jwt
import hashlib
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from accounts.selectors import user_exists
from core.settings import ACCESS_TTL, JWT_SECRET, REFRESH_TTL
import logging

logger = logging.getLogger(__name__)


def gen_token(data):
    try:
        return jwt.encode(payload=data, key=JWT_SECRET, algorithm="HS512")
    except Exception as e:
        logger.error(f"Token generation failed: {e}")
        return None


def __gen_tokens(user_id):
    data = {
        "user_id": user_id,
        "created_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S %z"),
        "type": "access",
    }
    access_token = gen_token(data=data)
    data["type"] = "refresh"
    data["access"] = access_token
    refresh_token = gen_token(data=data)
    # Use SHA256 hash of token as cache key to avoid length issues
    access_key = hashlib.sha256(access_token.encode()).hexdigest()
    refresh_key = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    cache.set(f"jwt_access_{access_key}", "", timeout=ACCESS_TTL * 24 * 3600)
    cache.set(f"jwt_refresh_{refresh_key}", "", timeout=REFRESH_TTL * 24 * 3600)
    return access_token, refresh_token


def login(user):
    return __gen_tokens(user_id=str(user.id))


def claim_token(token):
    return jwt.decode(jwt=token, key=JWT_SECRET, algorithms=["HS512"])


def __has_keys(data: dict, *keys):
    return all([i in data.keys() for i in keys])


def validate_token(token, check_time=True):
    """
    Validate JWT token with improved error handling and development mode support
    """
    # In development mode, be more flexible with cache checking
    if check_time and not getattr(settings, 'DEBUG', False):
        try:
            # Use SHA256 hash of token as cache key
            token_key = hashlib.sha256(token.encode()).hexdigest()
            cache_key = f"jwt_access_{token_key}"
            
            # Try both access and refresh patterns for compatibility
            if not cache.has_key(cache_key) and not cache.has_key(f"jwt_refresh_{token_key}"):
                logger.warning(f"Token not found in cache: {token[:20]}...")
                return False
        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            # In case of cache error, continue with validation
    
    try:
        data = claim_token(token)
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return False
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return False
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        return False
    
    if "type" not in data.keys():
        logger.warning("Token missing 'type' field")
        return False
    
    delta = timedelta(days=ACCESS_TTL)
    if data.get("type") == "refresh":
        if not __has_keys(data, "user_id", "created_at", "type", "access"):
            logger.warning("Refresh token missing required fields")
            return False
        access = data.get("access")
        if not validate_token(access, check_time=False):
            logger.warning("Access token in refresh token is invalid")
            return False
        delta = timedelta(days=REFRESH_TTL)
    elif data.get("type") != "access" or not __has_keys(
        data, "user_id", "created_at", "type"
    ):
        logger.warning("Access token missing required fields or wrong type")
        return False
    
    user_id = data.get("user_id")
    if not user_exists(id=user_id):
        logger.warning(f"User {user_id} does not exist")
        return False
    
    try:
        data_created_at_str = data.get("created_at")
        data_created_at = datetime.strptime(
            data_created_at_str, "%Y-%m-%d %H:%M:%S %z"
        )
        if check_time and timezone.now() > data_created_at + delta:
            logger.warning(f"Token expired. Created: {data_created_at}, Now: {timezone.now()}")
            return False
    except Exception as e:
        logger.error(f"Error parsing token timestamp: {e}")
        return False
    
    return True


def refresh(token):
    if not validate_token(token):
        raise ValueError("Invalid refresh token")
    jwt_data = claim_token(token)
    if jwt_data.get("type") != "refresh":
        raise ValueError("Token is not a refresh token")
    # Use SHA256 hash for cache keys
    refresh_key = hashlib.sha256(token.encode()).hexdigest()
    cache.delete(f"jwt_refresh_{refresh_key}")
    data_access = jwt_data.get("access")
    if data_access:
        access_key = hashlib.sha256(data_access.encode()).hexdigest()
        cache.delete(f"jwt_access_{access_key}")
    user_id = jwt_data.get("user_id")
    return __gen_tokens(user_id=user_id)


def expire(token):
    try:
        # Use SHA256 hash of token as cache key
        token_key = hashlib.sha256(token.encode()).hexdigest()
        cache.delete(f"jwt_access_{token_key}")
        cache.delete(f"jwt_refresh_{token_key}")
        return True
    except Exception:
        return False
