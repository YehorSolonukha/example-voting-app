from fastapi import Request
from .rules.user_agent import UserAgentRule
from .rules.sql_injection import SqlInjectionRule
from .rules.time_access import TimeAccessRule
from .rules.ip_blocklist import IPBlocklistRule
from .rules.rate_limit import RateLimitRule
from .rules.geo_block import GeoBlockRule

class WAFEngine:
    def __init__(self):
        self.rules = [
            IPBlocklistRule(),
            TimeAccessRule(),
            RateLimitRule(),
            UserAgentRule(),
            SqlInjectionRule(),
            GeoBlockRule()
        ]

    async def startup(self):
        for rule in self.rules:
            if hasattr(rule, "startup"):
                await rule.startup()

    async def inspect_all(self, request: Request) -> tuple[str, str] | None:
        for rule in self.rules:
            block_reason = await rule.inspect(request)
            if block_reason:
                rule_name = rule.__class__.__name__
                return rule_name, block_reason
        
        return None
