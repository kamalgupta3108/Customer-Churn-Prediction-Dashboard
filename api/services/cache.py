"""
api/services/cache.py
-----------------------
Our "sticky note board" (Redis wrapper).

WHY A SEPARATE FILE?
Same reason as before - if we ever swapped Redis for a different caching
tool, only this file would need to change, nothing else in our app.

HOW WE DECIDE WHAT "THE SAME REQUEST" MEANS:
Two prediction requests are "the same" if every input field is identical.
We can't use the customer dictionary directly as a Redis key (Redis keys
must be simple strings), so we convert the dictionary into a consistent
string and then hash it into a short fixed-length fingerprint. This
fingerprint is our cache key.
"""

import os
import json
import hashlib
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = 300  # sticky notes auto-expire after 5 minutes

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def _make_cache_key(customer: dict) -> str:
    """
    Turn a customer dictionary into a short, consistent string key.

    sort_keys=True is important: {"a":1,"b":2} and {"b":2,"a":1} are the
    SAME customer, and must produce the SAME cache key, even though
    dictionaries don't guarantee insertion order is preserved consistently
    across requests.
    """
    serialized = json.dumps(customer, sort_keys=True)
    fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
    return f"prediction:{fingerprint}"


def get_cached_prediction(customer: dict) -> dict | None:
    """Check the sticky note board. Returns the cached result, or None if
    this exact customer profile hasn't been predicted recently."""
    key = _make_cache_key(customer)
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None


def set_cached_prediction(customer: dict, result: dict) -> None:
    """Write a new sticky note, with an expiry time (TTL) attached."""
    key = _make_cache_key(customer)
    redis_client.set(key, json.dumps(result), ex=CACHE_TTL_SECONDS)


def check_rate_limit(user_id: int, max_requests: int = 5, window_seconds: int = 60) -> bool:
    """
    A simple rate limiter: "this user may make at most `max_requests`
    batch uploads per `window_seconds`."

    HOW IT WORKS: we use Redis's INCR (increment) on a per-user counter key.
    The first request creates the counter at 1 and sets it to expire after
    `window_seconds`. Every subsequent request within that window just
    increments the same counter. Once the window passes, Redis automatically
    deletes the key, and the next request starts a fresh count at 1.

    Returns True if the request is allowed, False if the limit was hit.
    """
    key = f"ratelimit:batch:{user_id}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window_seconds)
    return current <= max_requests
