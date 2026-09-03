from fastapi import Request
from .base import WAFRule
from .ip_blocklist import IPBlocklistRule
from .rate_limit import RateLimitRule
from .time_access import TimeAccessRule
from .user_agent import UserAgentRule
from .sql_injection import SqlInjectionRule
from .geo_block import GeoBlockRule


class WAFEngine:
    """Runs all WAF rules in priority order.

    Rules are ordered cheapest-first:
    1. IP blocklist  — pure in-memory set lookup, near zero cost
    2. Rate limiter  — one Redis INCR, very fast
    3. Time access   — datetime comparison, zero I/O
    4. User-Agent    — string search, zero I/O
    5. SQL injection — regex on body/query, slightly more work
    6. Geo-block     — external HTTP call, most expensive — runs last
    """

    def __init__(self):
        self.rules: list[WAFRule] = [
            IPBlocklistRule(),
            RateLimitRule(),
            TimeAccessRule(),
            UserAgentRule(),
            SqlInjectionRule(),
            GeoBlockRule(),
        ]

    async def startup(self):
        """Called at app startup — allows rules to initialise async resources."""
        for rule in self.rules:
            if hasattr(rule, "startup"):
                await rule.startup()

    async def inspect(self, request: Request) -> tuple[str, str] | None:
        """Runs every rule in order. Short-circuits on first block.

        Returns (rule_class_name, block_reason) if blocked, else None.
        """
        for rule in self.rules:
            reason = await rule.inspect(request)
            if reason:
                return rule.__class__.__name__, reason
        return None
