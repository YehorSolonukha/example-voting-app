import httpx
import ipaddress
from fastapi import Request
from .base import WAFRule

class GeoBlockRule(WAFRule):
    def __init__(self, blocked_countries: list[str] = None):
        self.blocked_countries = blocked_countries or ["RU", "CN", "KP"]
        
    async def inspect(self, request: Request) -> str | None:
        client_ip_str = request.client.host
        
        try:
            ip_obj = ipaddress.ip_address(client_ip_str)
            if ip_obj.is_private or ip_obj.is_loopback:
                return None
        except ValueError:
            pass
            
        try:
            url = f"http://ip-api.com/json/{client_ip_str}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=2.0)
                
            if response.status_code == 200:
                data = response.json()
                country_code = data.get("countryCode")
                
                if country_code in self.blocked_countries:
                    return f"Geo-Block: Traffic from {country_code} is restricted."
                    
        except Exception as e:
            print(f"[WAF] Geo-IP lookup failed: {e}")
            
        return None
