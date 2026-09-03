import re
import urllib.parse
from fastapi import Request
from .base import WAFRule
from core.rule_config import rule_manager

class SqlInjectionRule(WAFRule):
    async def inspect(self, request: Request) -> str | None:
        default_config = {"patterns": [r"drop\s+table", r"union\s+select", r"or\s+1\s*=\s*1", r"--"]}
        config = rule_manager.get_config("SqlInjectionRule", default_config)
        
        if config is None:
            return None

        patterns = config.get("patterns", [])
        
        body_bytes = await request.body()
        body_text = urllib.parse.unquote(body_bytes.decode("utf-8", errors="ignore")).lower()
        
        query_string = urllib.parse.unquote(request.url.query).lower()
        
        content_to_check = body_text + " " + query_string
        
        for pattern in patterns:
            if re.search(pattern, content_to_check):
                return "SQL Injection Detected!"
                
        return None
