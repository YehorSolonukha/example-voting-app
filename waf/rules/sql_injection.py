import re
import urllib.parse
from fastapi import Request
from .base import WAFRule
from .rule_config import rule_manager


class SqlInjectionRule(WAFRule):
    """Scans URL query strings and request bodies for SQL injection patterns.

    Config (live-updated via admin API):
      patterns  list[str]  — Python regex patterns, matched case-insensitively

    URL-decodes content before matching so encoded payloads like
    %27%20OR%201%3D1 are caught the same as their plain-text equivalents.
    """

    async def inspect(self, request: Request) -> str | None:
        config = rule_manager.get_config(
            "SqlInjectionRule",
            {
                "patterns": [
                    r"drop\s+table",
                    r"union\s+select",
                    r"or\s+1\s*=\s*1",
                    r"--",
                ]
            },
        )
        if config is None:
            return None

        body_bytes = await request.body()
        # unquote_plus decodes both %XX sequences AND + as space.
        # This is required for query strings and form bodies where + encodes a space.
        body = urllib.parse.unquote_plus(body_bytes.decode("utf-8", errors="ignore")).lower()
        query = urllib.parse.unquote_plus(request.url.query).lower()
        content = body + " " + query

        for pattern in config.get("patterns", []):
            if re.search(pattern, content, re.IGNORECASE):
                return "SQL injection pattern detected."

        return None
