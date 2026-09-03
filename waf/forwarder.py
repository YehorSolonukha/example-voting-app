"""HTTP and WebSocket forwarder to the internal proxy service.

Holds a single persistent httpx.AsyncClient created at startup and reused
for every request. This gives us proper connection pooling — no TCP handshake
overhead per request, which was the root cause of ConnectTimeout errors in
the original gateway.
"""
import asyncio
import httpx
import websockets
from fastapi import Request, WebSocket
from fastapi.responses import Response
from config import PROXY_URL

# Headers that must not be forwarded to upstream services (RFC 7230 §6.1).
# Forwarding these causes protocol-level errors between proxies.
_HOP_BY_HOP = frozenset([
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host",
])

# Shared client — created by init(), closed by close() inside the lifespan context
_client: httpx.AsyncClient | None = None


async def init():
    """Create the shared HTTP client. Call once at application startup."""
    global _client
    _client = httpx.AsyncClient(base_url=PROXY_URL, timeout=30.0)


async def close():
    """Close the shared HTTP client. Call once at application shutdown."""
    if _client:
        await _client.aclose()


async def forward_http(request: Request) -> Response:
    """Forward a clean HTTP request to the proxy and return its response.

    On any upstream connectivity error, returns 502 Bad Gateway so the
    caller always gets a structured HTTP response instead of a 500 crash.
    """
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }
    body = await request.body()
    url = request.url.path
    if request.url.query:
        url += f"?{request.url.query}"

    try:
        upstream = await _client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=dict(upstream.headers),
        )
    except Exception as e:
        print(f"[WAF] Upstream HTTP error: {e}")
        return Response(content="Bad Gateway", status_code=502)


async def forward_websocket(client_ws: WebSocket, path: str):
    """Tunnel a WebSocket connection from the browser to the proxy.

    Opens a WebSocket to the proxy, then runs two concurrent coroutines —
    one relaying frames from the browser to the proxy, one in the other
    direction — until either side closes the connection.
    """
    query = client_ws.scope.get("query_string", b"").decode()
    ws_base = PROXY_URL.replace("http://", "ws://").replace("https://", "wss://")
    target = f"{ws_base}/{path}"
    if query:
        target += f"?{query}"

    try:
        async with websockets.connect(target) as upstream_ws:

            async def browser_to_proxy():
                try:
                    async for msg in client_ws.iter_text():
                        await upstream_ws.send(msg)
                except Exception:
                    pass

            async def proxy_to_browser():
                try:
                    async for msg in upstream_ws:
                        if isinstance(msg, bytes):
                            await client_ws.send_bytes(msg)
                        else:
                            await client_ws.send_text(msg)
                except Exception:
                    pass

            await asyncio.gather(browser_to_proxy(), proxy_to_browser())
    except Exception as e:
        print(f"[WAF] WebSocket tunnel error: {e}")
