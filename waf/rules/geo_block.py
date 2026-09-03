import ipaddress
import httpx
from fastapi import Request
from .base import WAFRule
from .rule_config import rule_manager


class GeoBlockRule(WAFRule):
    """Blocks traffic from specific countries using the ip-api.com free API.

    Config (live-updated via admin API):
      blocked_countries  list[str]  — ISO 3166-1 alpha-2 codes (e.g. "RU", "CN")

    Private and loopback IPs are always allowed (they are internal Docker calls).
    Fails open on API errors — if ip-api.com is unreachable, the request passes.

    Note: ip-api.com is rate-limited at 45 req/min on the free tier and adds
    network latency to every inspected request. For high-traffic production use,
    replace this with a local MaxMind GeoLite2 database (zero latency, no limits).
    """

    async def inspect(self, request: Request) -> str | None:
        config = rule_manager.get_config(
            "GeoBlockRule", {"blocked_countries": ["RU", "CN", "KP"]}
        )
        if config is None:
            return None

        ip_str = request.client.host
        try:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback:
                return None
        except ValueError:
            return None

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"http://ip-api.com/json/{ip_str}")
            if response.status_code == 200:
                country = response.json().get("countryCode")
                if country in config.get("blocked_countries", []):
                    return f"Geo-block: traffic from {country} is restricted."
        except Exception as e:
            # Fail open — don't block traffic just because the geo API is slow
            print(f"[WAF] GeoBlock lookup failed (failing open): {e}")

        return None
