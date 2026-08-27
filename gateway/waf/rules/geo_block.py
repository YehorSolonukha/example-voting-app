import httpx
import ipaddress
from fastapi import Request
from .base import WAFRule

class GeoBlockRule(WAFRule):
    def __init__(self, blocked_countries: list[str] = None):
        # A list of ISO Country Codes to block
        self.blocked_countries = blocked_countries or ["RU", "CN", "KP"]
        
    async def inspect(self, request: Request) -> str | None:
        client_ip_str = request.client.host
        
        # Use Python's built-in IP library to flawlessly detect ALL private/local IPs
        try:
            ip_obj = ipaddress.ip_address(client_ip_str)
            if ip_obj.is_private or ip_obj.is_loopback:
                return None
        except ValueError:
            pass
            
        try:
            # NOTE: ip-api.com ONLY works on http:// (unencrypted). 
            # If you try https:// it requires a premium license key!
            url = f"http://ip-api.com/json/{client_ip_str}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=2.0)
                
            if response.status_code == 200:
                data = response.json()
                country_code = data.get("countryCode")
                
                if country_code in self.blocked_countries:
                    return f"Geo-Block: Traffic from {country_code} is restricted."
                    
        except Exception as e:
            # If the API fails or is too slow, allow the traffic
            print(f"[WAF] Geo-IP lookup failed: {e}")
            
        return None
