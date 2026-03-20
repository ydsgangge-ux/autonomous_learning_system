"""Simple TTL cache for exploration results."""
import time
from typing import Any

_cache: dict[str, tuple[Any, float]] = {}


def get(key: str) -> Any | None:
    if key in _cache:
        value, expires_at = _cache[key]
        if time.time() < expires_at:
            return value
        del _cache[key]
    return None


def set(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    _cache[key] = (value, time.time() + ttl_seconds)


def delete(key: str) -> None:
    _cache.pop(key, None)


def clear() -> None:
    _cache.clear()
