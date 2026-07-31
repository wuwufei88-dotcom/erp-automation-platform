# Redis client with connection pool, cache helpers
from __future__ import annotations

import json
import hashlib
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)

_pool: aioredis.ConnectionPool | None = None
_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _pool, _client
    if _client is None:
        settings = get_settings()
        _pool = aioredis.ConnectionPool.from_url(settings.redis_url, max_connections=20)
        _client = aioredis.Redis(connection_pool=_pool)
        await _client.ping()
        logger.info("Redis connected: %s", settings.redis_url)
    return _client


async def close_redis() -> None:
    global _pool, _client
    if _client:
        await _client.close()
        _client = None
        _pool = None


# ─── Generic cache helpers ─────────────────────────────────────

async def cache_get(key: str) -> Optional[dict]:
    try:
        r = await get_redis()
        data = await r.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except Exception as e:
        logger.warning("Redis cache_set failed: %s", e)


async def cache_delete(key: str) -> None:
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception:
        pass


async def cache_delete_pattern(pattern: str) -> None:
    try:
        r = await get_redis()
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception:
        pass


# ─── Domain-specific cache keys ────────────────────────────────

def agent_output_key(project_id: str, agent_type: str) -> str:
    return f"agent_output:{project_id}:{agent_type}"


def llm_response_key(prompt_hash: str) -> str:
    return f"llm:{prompt_hash}"


def kb_search_key(query: str) -> str:
    return f"kb:{hashlib.md5(query.encode()).hexdigest()}"


def project_cache_key(project_id: str) -> str:
    return f"project:{project_id}"


def project_list_key(status: str = "all") -> str:
    return f"projects:list:{status}"


def hash_content(*texts: str) -> str:
    return hashlib.md5("|".join(texts).encode()).hexdigest()[:12]
