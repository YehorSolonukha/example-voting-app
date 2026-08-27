import re
from fastapi import Request
from .base import WAFRule
from core.rule_config import rule_manager

class SqlInjectionRule(WAFRule):
    async def inspect(self, request: Request) -> str | None:
        # Ask RuleManager for config. If None, rule is disabled in the database.
        default_config = {"patterns": [r"drop\s+table", r"union\s+select", r"or\s+1\s*=\s*1", r"--"]}
        config = rule_manager.get_config("SqlInjectionRule", default_config)
        
        if config is None:
            return None # Disabled

        patterns = config.get("patterns", [])
        
        # Read the raw body bytes and decode to text
        body_bytes = await request.body()
        body_text = body_bytes.decode("utf-8", errors="ignore").lower()
        
        for pattern in patterns:
            print(f"[WAF DEBUG] Testing SQL pattern: {pattern} against body: '{body_text}'")
            if re.search(pattern, body_text):
                return "SQL Injection Detected!"
                
        return None
