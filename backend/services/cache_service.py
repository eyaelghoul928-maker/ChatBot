import redis.asyncio as aioredis
import hashlib
import json
from config import settings
from loguru import logger


redis_client = aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


def make_cache_key(question: str) -> str:
    normalized = question.strip().lower()
    return "chat:" + hashlib.md5(normalized.encode()).hexdigest()


async def get_cached_response(question: str):
    try:
        key = make_cache_key(question)
        value = await redis_client.get(key)
        if value:
            logger.info(f"[CACHE] HIT — {question[:40]}")
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"[CACHE] Erreur lecture: {e}")
        return None


async def set_cached_response(question: str, data: dict):
    try:
        key = make_cache_key(question)
        await redis_client.setex(
            key,
            settings.cache_ttl_seconds,
            json.dumps(data, ensure_ascii=False, default=str)
        )
        logger.info(f"[CACHE] SET — {question[:40]}")
    except Exception as e:
        logger.warning(f"[CACHE] Erreur ecriture: {e}")