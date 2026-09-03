# Shared Redis singleton — imported by any module that needs Redis.
# One connection pool for the entire WAF service.
import redis.asyncio as redis
from config import WAF_REDIS_URL

redis_client = redis.from_url(WAF_REDIS_URL, decode_responses=True)
