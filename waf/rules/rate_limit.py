from fastapi import Request
from .base import WAFRule
from .rule_config import rule_manager
from shared.redis_client import redis_client


class RateLimitRule(WAFRule):
    """Sliding-window rate limiter per client IP, backed by Redis.

    Config (live-updated via admin API):
      max_requests    int  — maximum allowed requests in the window
      window_seconds  int  — window duration in seconds

    Uses the shared Redis singleton — no private connection pool.
    Fails open on Redis errors to prevent a Redis outage from taking
    down the entire gateway.
    """

    async def inspect(self, request: Request) -> str | None:
        config = rule_manager.get_config(
            "RateLimitRule", {"max_requests": 50, "window_seconds": 10}
        )
        if config is None:
            return None  # Rule is disabled in admin panel

        max_requests = config.get("max_requests", 50)
        window_seconds = config.get("window_seconds", 10)
        key = f"rate_limit:{request.client.host}"

        try:
            count = await redis_client.incr(key)
            if count == 1:
                # First request in this window — set the expiry
                await redis_client.expire(key, window_seconds)
            if count > max_requests:
                return f"Rate limit exceeded: {max_requests} requests per {window_seconds}s."
        except Exception as e:
            # Fail open — don't block legitimate users if Redis is temporarily down
            print(f"[WAF] RateLimitRule Redis error (failing open): {e}")

        return None
