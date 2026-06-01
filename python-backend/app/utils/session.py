"""Session 管理工具"""

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.config import settings

redis_client: Optional[redis.Redis] = None


async def init_redis():
    global redis_client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


def _get_session_key(session_id: str) -> str:
    return f"session:{session_id}"


async def get_session(session_id: str) -> Optional[dict]:
    if not redis_client:
        return None
    key = _get_session_key(session_id)
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None


async def set_session(session_id: str, data: dict, expire: Optional[int] = None):
    if not redis_client:
        return
    key = _get_session_key(session_id)
    expire_time = expire or settings.session_max_age
    await redis_client.setex(key, expire_time, json.dumps(data))


async def remove_session(session_id: str):
    if not redis_client:
        return
    key = _get_session_key(session_id)
    await redis_client.delete(key)
