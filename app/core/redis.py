import redis

from core.config import get_settings


def get_redis_client():
    """
    Returns a Redis client instance.
    """
    settings = get_settings()
    redis_settings = settings.redis_settings
    redis_client = redis.Redis(
        host=redis_settings.HOST,
        port=redis_settings.PORT,
        db=redis_settings.DB,
        decode_responses=True,
    )
    return redis_client
