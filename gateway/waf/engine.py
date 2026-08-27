from fastapi import Request
from .rules.user_agent import UserAgentRule
from .rules.sql_injection import SqlInjectionRule
from .rules.time_access import TimeAccessRule
from .rules.ip_blocklist import IPBlocklistRule
from .rules.rate_limit import RateLimitRule
from .rules.geo_block import GeoBlockRule

class WAFEngine:
    def __init__(self):
        # Instantiate our rules. ORDER MATTERS!
        # Fastest checks (memory) run first, slowest checks (network) run last.
        self.rules = [
            IPBlocklistRule(),    # 1. Very fast (memory set lookup)
            TimeAccessRule(),     # 2. Very fast (clock check)
            RateLimitRule(),      # 3. Fast (Redis network call ~1ms)
            UserAgentRule(),      # 4. Fast (String search)
            SqlInjectionRule(),   # 5. Slower (Regex on full body)
            GeoBlockRule()        # 6. Slowest (External HTTP call)
        ]

    async def startup(self):
        """Initializes any rules that require the async event loop to be active."""
        for rule in self.rules:
            if hasattr(rule, "startup"):
                await rule.startup()

    async def inspect_all(self, request: Request) -> tuple[str, str] | None:
        """
        Loops through all rules. 
        If a rule triggers, returns a tuple (RuleName, BlockReason) immediately.
        If all rules pass, returns None.
        """
        for rule in self.rules:
            block_reason = await rule.inspect(request)
            if block_reason:
                # Magic: Automatically grabs the name of the class that fired (e.g. "UserAgentRule")
                rule_name = rule.__class__.__name__
                return rule_name, block_reason
        
        return None  # Passed all checks
