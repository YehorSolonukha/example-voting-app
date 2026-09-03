from abc import ABC, abstractmethod
from fastapi import Request


class WAFRule(ABC):
    """Base class for all WAF rules.

    Each rule receives the raw request and returns either:
    - None  → request is clean, continue to next rule
    - str   → block reason, request is denied immediately
    """

    @abstractmethod
    async def inspect(self, request: Request) -> str | None:
        pass
