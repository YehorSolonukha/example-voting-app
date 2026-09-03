# Shared asyncpg connection pool — initialised once at startup.
# Call init_pool() inside the lifespan context, then get_pool() everywhere else.
import asyncpg
from config import WAF_DB_URL

_pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    global _pool
    _pool = await asyncpg.create_pool(WAF_DB_URL, min_size=2, max_size=10)
    return _pool


def get_pool() -> asyncpg.Pool:
    return _pool
