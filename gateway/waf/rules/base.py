from abc import ABC, abstractmethod
from fastapi import Request

class WAFRule(ABC):
    
    @abstractmethod
    async def inspect(self, request: Request) -> str | None:
        """
        Takes a FastAPI Request object.
        Returns a String (the block reason) if the request is malicious.
        Returns None if the request is safe.
        """
        pass
