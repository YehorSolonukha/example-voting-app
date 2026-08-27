from fastapi import Request
from .base import WAFRule
from core.rule_config import rule_manager

class UserAgentRule(WAFRule):
    async def inspect(self, request: Request) -> str | None:
        # Ask RuleManager for config. If None, rule is disabled in the database.
        default_config = {"bad_agents": ["curl", "python-requests", "bot", "spider", "sqlmap"]}
        config = rule_manager.get_config("UserAgentRule", default_config)
        
        if config is None:
            return None # Disabled
            
        bad_agents = config.get("bad_agents", [])
        user_agent = request.headers.get("user-agent", "").lower()
        
        for bad_word in bad_agents:
            if bad_word in user_agent:
                return f"Malicious User-Agent: {bad_word}"
                
        return None  # Safe
