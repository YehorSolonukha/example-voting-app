import httpx
import asyncio
import ipaddress
from fastapi import Request
from .base import WAFRule

class IPBlocklistRule(WAFRule):
    def __init__(self):
        # We separate exact IPs (fast lookup) from Subnets (slower lookup)
        self.malicious_ips = set()
        self.malicious_networks = []
        
    async def startup(self):
        # Start the background task once the FastAPI event loop is running
        asyncio.create_task(self.update_blocklist())

    async def update_blocklist(self):
        try:
            url = "https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/firehol_level1.netset"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                
            if response.status_code == 200:
                new_ips = set()
                new_networks = []
                
                for line in response.text.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # If the line contains a slash, it's a subnet (e.g. 192.168.0.0/16)
                        if "/" in line:
                            new_networks.append(ipaddress.ip_network(line, strict=False))
                        else:
                            new_ips.add(line)
                            
                self.malicious_ips = new_ips
                self.malicious_networks = new_networks
                print(f"[WAF] Loaded {len(self.malicious_ips)} IPs and {len(self.malicious_networks)} subnets.")
        except Exception as e:
            print(f"[WAF] Failed to load IP blocklist: {e}")

    async def inspect(self, request: Request) -> str | None:
        client_ip_str = request.client.host
        
        try:
            ip_obj = ipaddress.ip_address(client_ip_str)
            
            # 1. Protect ourselves during local testing!
            # FireHOL blocks "bogons" (private IPs like 10.x.x.x). If we don't skip private IPs,
            # we will block ourselves while testing on localhost/Docker.
            if ip_obj.is_private or ip_obj.is_loopback:
                return None
                
            # 2. Fast check: Is it an exact IP match? (O(1) time)
            if client_ip_str in self.malicious_ips:
                return f"IP Blocked: {client_ip_str} is on the blocklist."
                
            # 3. Slower check: Is it inside one of the blocked subnets? (O(N) time)
            for network in self.malicious_networks:
                if ip_obj in network:
                    return f"IP Blocked: {client_ip_str} belongs to blocked subnet {network}."
                    
        except ValueError:
            pass # Invalid IP format
            
        return None
