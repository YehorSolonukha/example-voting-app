from fastapi import Request
from .base import WAFRule
from .rule_config import rule_manager


class UserAgentRule(WAFRule):
    """Blocks requests from known malicious or automated scanning tools.

    Config (live-updated via admin API):
      bad_agents  list[str]  — substrings matched case-insensitively
                               against the User-Agent header
    """

    async def inspect(self, request: Request) -> str | None:
        config = rule_manager.get_config(
            "UserAgentRule", {"bad_agents": ["sqlmap", "nikto", "nmap", "masscan"]}
        )
        if config is None:
            return None

        ua = request.headers.get("user-agent", "").lower()
        for bad in config.get("bad_agents", []):
            if bad.lower() in ua:
                return f"Blocked User-Agent: '{bad}'."

        return None
