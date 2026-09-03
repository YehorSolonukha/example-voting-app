"""Reverse Proxy service — entry point.

Routing table (two rules, purely path-based, no heuristics):

  /result  or  /result/*          → result service  (prefix stripped)
  /*  (everything else)           → vote service

WebSocket routing follows the same rule:
  WS /result/*                    → result service  (prefix stripped)

The result app's static assets (app.js, socket.io.js, etc.) and its
socket.io endpoint (/result/socket.io/) are all served under /result/*,
so they route correctly to result without any special-casing.

This service is intentionally internal — it has no WAF, no auth, no
rate limiting. All of that lives in the WAF service that sits in front
of it. The proxy's only job is correct, fast routing.
"""
import asyncio
import os
from contextlib import asynccontextmanager

import httpx
import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response

load_dotenv()

VOTE_URI   = os.getenv("VOTE_SERVICE_URI",   "http://vote:80")
RESULT_URI = os.getenv("RESULT_SERVICE_URI", "http://result:80")

# Headers that must not be forwarded between proxies (RFC 7230 §6.1)
_HOP_BY_HOP = frozenset([
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host",
])

# Shared persistent HTTP client — created once at startup, reused for every request.
# This gives us connection pooling so we never pay TCP handshake cost per request.
_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    _client = httpx.AsyncClient(timeout=30.0)
    print(f"[Proxy] Ready. vote={VOTE_URI}  result={RESULT_URI}")
    yield
    await _client.aclose()
    print("[Proxy] Shutdown complete.")


app = FastAPI(lifespan=lifespan)


def _resolve(path: str) -> tuple[str, str]:
    """Return (target_base_url, stripped_path) for the given request path.

    If the path starts with 'result', strip that prefix and send to result.
    Everything else goes to vote as-is.
    """
    if path == "result" or path.startswith("result/"):
        stripped = path[len("result"):].lstrip("/")
        return RESULT_URI, stripped
    return VOTE_URI, path


# ── WebSocket proxy ────────────────────────────────────────────────────────

@app.websocket("/{path:path}")
async def websocket_proxy(websocket: WebSocket, path: str):
    """Tunnel WebSocket connections to the correct backend service.

    /result/* → result (socket.io lives at /result/socket.io/ after the
                result app was configured with that custom path)
    /* → vote (vote app does not currently use WebSockets)
    """
    base_uri, stripped_path = _resolve(path)
    query = websocket.scope.get("query_string", b"").decode()

    ws_uri = base_uri.replace("http://", "ws://").replace("https://", "wss://")
    target = f"{ws_uri}/{stripped_path}"
    if query:
        target += f"?{query}"

    await websocket.accept()

    try:
        async with websockets.connect(target) as upstream:

            async def client_to_upstream():
                try:
                    async for msg in websocket.iter_text():
                        await upstream.send(msg)
                except Exception:
                    pass

            async def upstream_to_client():
                try:
                    async for msg in upstream:
                        if isinstance(msg, bytes):
                            await websocket.send_bytes(msg)
                        else:
                            await websocket.send_text(msg)
                except Exception:
                    pass

            await asyncio.gather(client_to_upstream(), upstream_to_client())
    except Exception as e:
        print(f"[Proxy] WebSocket error for /{path}: {e}")


# ── HTTP proxy ─────────────────────────────────────────────────────────────

@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
)
async def http_proxy(request: Request, path: str):
    """Route HTTP requests to the correct backend and return the response.

    Returns 502 Bad Gateway on upstream connectivity errors so the WAF
    always gets a structured response rather than an unhandled exception.
    """
    base_uri, stripped_path = _resolve(path)
    url = f"{base_uri}/{stripped_path}"
    if request.url.query:
        url += f"?{request.url.query}"

    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }
    body = await request.body()

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
        print(f"[Proxy] Upstream error for /{path} → {url}: {e}")
        return Response(content="Bad Gateway", status_code=502)
