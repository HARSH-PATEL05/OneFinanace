"""
Safe Redis client wrapper.

Exports:
 - get_redis() -> redis.Redis | None
 - redis_client  (backwards compatibility)
 - redis_safe_get()
 - redis_safe_set()
 - redis_safe_publish()
 - redis_safe_json_get()
 - redis_safe_json_set()
"""

import os
import time
import threading
import json
from typing import Optional, TYPE_CHECKING, Any

# For type hints only – Pylance safe
if TYPE_CHECKING:
    import redis
else:
    redis = None  # runtime import later


# ===================== CONFIG =====================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "2.0"))
REDIS_SOCKET_CONNECT_TIMEOUT = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "2.0"))

_lock = threading.RLock()
_redis_client: Any = None
_last_attempt = 0.0
_RECONNECT_COOLDOWN = 1.0
# ==================================================


# ------------------------ BUILD CLIENT ------------------------
def _build_client():
    """Lazy import redis and create actual client."""
    global redis
    try:
        if redis is None:
            import redis as redis_runtime
            redis = redis_runtime

        pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD or None,
            socket_timeout=REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
            decode_responses=False,
        )

        cli = redis.Redis(connection_pool=pool)
        cli.ping()
        return cli

    except Exception:
        return None


# ------------------------ GET CLIENT ------------------------
def get_redis() -> Optional[Any]:
    """Return a connected Redis client or None (safe for Pylance)."""
    global _redis_client, _last_attempt, redis

    if redis is None:
        try:
            import redis as redis_runtime
            redis = redis_runtime
        except Exception:
            return None

    with _lock:
        # Check working client
        if _redis_client is not None:
            try:
                _redis_client.ping()
                return _redis_client
            except Exception:
                _redis_client = None

        # Throttle reconnection attempts
        now = time.time()
        if now - _last_attempt < _RECONNECT_COOLDOWN:
            return None

        _last_attempt = now

        client = _build_client()
        if client:
            _redis_client = client
            return _redis_client

        return None


# Keep old variable name alive
redis_client = get_redis()


# ===============================================================
#        🔥 SAFE REDIS HELPERS (FULL PRODUCTION MODE)
# ===============================================================

def redis_safe_get(key: str) -> Optional[bytes]:
    r = get_redis()
    if not r:
        return None
    try:
        return r.get(key)
    except Exception:
        return None


def redis_safe_set(key: str, value: Any, ex: Optional[int] = None) -> bool:
    r = get_redis()
    if not r:
        return False
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value).encode("utf-8")
        elif isinstance(value, str):
            value = value.encode("utf-8")
        r.set(key, value, ex=ex)
        return True
    except Exception:
        return False


def redis_safe_publish(channel: str, message: Any) -> bool:
    r = get_redis()
    if not r:
        return False

    try:
        if isinstance(message, (dict, list)):
            message = json.dumps(message).encode("utf-8")
        elif isinstance(message, str):
            message = message.encode("utf-8")

        r.publish(channel, message)
        return True
    except Exception:
        return False


def redis_safe_json_get(key: str):
    raw = redis_safe_get(key)
    if not raw:
        return None

    try:
        if isinstance(raw, (bytes, bytearray)):
            return json.loads(raw.decode("utf-8"))
        return json.loads(raw)
    except Exception:
        return None


def redis_safe_json_set(key: str, value: Any, ex: Optional[int] = None) -> bool:
    try:
        return redis_safe_set(key, json.dumps(value), ex=ex)
    except Exception:
        return False
