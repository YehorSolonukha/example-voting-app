import redis.asyncio as redis
from fastapi import Request
from .base import WAFRule
from core.config import WAF_REDIS_URL

class RateLimitRule(WAFRule):
    def __init__(self, max_requests: int = 50, window_seconds: int = 10):
        self.redis = redis.from_url(WAF_REDIS_URL, decode_responses=True)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def inspect(self, request: Request) -> str | None:
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        try:
            count = await self.redis.incr(key)
            
            if count == 1:
                await self.redis.expire(key, self.window_seconds)
                
            if count > self.max_requests:
                return f"Rate Limit Exceeded: Allowed {self.max_requests} requests per {self.window_seconds}s."
                
        except Exception as e:
            print(f"[WAF] Redis connection error: {e}")
            
        return None
