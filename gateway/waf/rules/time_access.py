from datetime import datetime
from fastapi import Request
from .base import WAFRule

class TimeAccessRule(WAFRule):
    def __init__(self, start_hour: int = 2, end_hour: int = 23):
        # Default: only allow traffic between 8:00 AM and 8:00 PM (20:00)
        self.start_hour = start_hour
        self.end_hour = end_hour

    async def inspect(self, request: Request) -> str | None:
        current_hour = datetime.now().hour
        
        # If current hour is OUTSIDE the allowed window
        if current_hour < self.start_hour or current_hour >= self.end_hour:
            return f"Time-based Block: Application only available between {self.start_hour}:00 and {self.end_hour}:00."
            
        return None
