from datetime import datetime
from fastapi import Request
from .base import WAFRule
from core.rule_config import rule_manager

class TimeAccessRule(WAFRule):
    async def inspect(self, request: Request) -> str | None:
        config = rule_manager.get_config("TimeAccessRule", {"start_hour": 8, "end_hour": 20})
        if config is None:
            return None

        start_hour = config.get("start_hour", 8)
        end_hour = config.get("end_hour", 20)
        current_hour = datetime.now().hour

        if current_hour < start_hour or current_hour >= end_hour:
            return f"Time-based Block: Application only available between {start_hour}:00 and {end_hour}:00."

        return None
