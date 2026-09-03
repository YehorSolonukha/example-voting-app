import asyncio
import ipaddress
import httpx
from fastapi import Request
from .base import WAFRule


class IPBlocklistRule(WAFRule):
    """Blocks IPs and subnets from the FireHOL Level 1 public blocklist.

    The list is fetched once at startup and refreshed every 24 hours.
    Private and loopback IPs are always allowed — they are internal
    Docker service-to-service calls, never real external threats.
    """

    BLOCKLIST_URL = (
        "https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/firehol_level1.netset"
    )

    def __init__(self):
        self._ips: set[str] = set()
        self._networks: list = []

    async def startup(self):
        asyncio.create_task(self._refresh_loop())

    async def _refresh_loop(self):
        while True:
            await self._load()
            await asyncio.sleep(86400)  # 24 hours

    async def _load(self):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.BLOCKLIST_URL)
            if response.status_code == 200:
                ips, networks = set(), []
                for line in response.text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "/" in line:
                        networks.append(ipaddress.ip_network(line, strict=False))
                    else:
                        ips.add(line)
                self._ips, self._networks = ips, networks
                print(f"[WAF] IPBlocklist loaded: {len(ips)} IPs, {len(networks)} subnets.")
        except Exception as e:
            print(f"[WAF] IPBlocklist refresh failed: {e}")

    async def inspect(self, request: Request) -> str | None:
        ip_str = request.client.host
        try:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback:
                return None
            if ip_str in self._ips:
                return f"IP {ip_str} is on the public blocklist."
            for network in self._networks:
                if ip in network:
                    return f"IP {ip_str} belongs to blocked subnet {network}."
        except ValueError:
            pass
        return None
