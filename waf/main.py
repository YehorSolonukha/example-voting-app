"""WAF service — entry point.

Request flow:
  Browser
    │
    ├─ /admin*, /api/*, /ws/live-feed  ──► admin.py (handled locally)
    │
    ├─ WebSocket (any other path)      ──► forwarder.forward_websocket()
    │                                       → proxy → result
    │
    └─ HTTP (any path)
         │
         ├─ WAF inspection (rules/engine.py)
         │    blocked ──► 403 + audit log + live feed broadcast
         │
         └─ clean ──► forwarder.forward_http() → proxy → vote or result
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from config import PROXY_URL
from shared.redis_client import redis_client
from shared.db_pool import init_pool
from rules.rule_config import rule_manager
from rules.engine import WAFEngine
from admin import router as admin_router, live_feed
import forwarder

waf_engine = WAFEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────
    app.state.db_pool = await init_pool()
    print("[WAF] Database pool ready.")

    rule_manager.start(app.state.db_pool)
    print("[WAF] Rule config manager started.")

    await waf_engine.startup()
    print("[WAF] Engine ready.")

    await forwarder.init()
    print(f"[WAF] HTTP forwarder ready → {PROXY_URL}")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    rule_manager.stop()
    await forwarder.close()
    await app.state.db_pool.close()
    await redis_client.aclose()
    print("[WAF] Shutdown complete.")


app = FastAPI(lifespan=lifespan)

# Static files for the admin dashboard UI.
# Must be mounted before the catch-all route so FastAPI sees it first.
app.mount("/admin/", StaticFiles(directory="static", html=True), name="admin")

# Admin API endpoints and live-feed WebSocket (/ws/live-feed)
app.include_router(admin_router)


# ── WebSocket catch-all ────────────────────────────────────────────────────
# Tunnels any WebSocket that wasn't handled by admin_router (i.e. not
# /ws/live-feed) straight through to the proxy service.
# The proxy then routes it to the correct backend (e.g. result's socket.io).
@app.websocket("/{path:path}")
async def websocket_proxy(websocket: WebSocket, path: str):
    await websocket.accept()
    await forwarder.forward_websocket(websocket, path)


# ── HTTP catch-all ─────────────────────────────────────────────────────────
# Every HTTP request that wasn't matched by the admin router lands here.
# 1. Increment the total request counter.
# 2. Run WAF inspection — block if any rule fires.
# 3. Forward clean requests to the proxy.
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])
async def http_proxy(request: Request, path: str):
    await redis_client.incr("waf_total_requests")

    result = await waf_engine.inspect(request)
    if result:
        rule_name, reason = result
        await redis_client.incr("waf_blocked_requests")

        # Broadcast to all open admin dashboard tabs
        await live_feed.broadcast({
            "client_ip": request.client.host,
            "method": request.method,
            "path": f"/{path}",
            "rule": rule_name,
            "reason": reason,
        })

        # Write audit log — don't let a slow DB delay the 403 response
        try:
            await request.app.state.db_pool.execute(
                "INSERT INTO security_audit_logs "
                "(client_ip, method, blocked_path, rule_name, reason) "
                "VALUES ($1, $2, $3, $4, $5)",
                request.client.host,
                request.method,
                f"/{path}",
                rule_name,
                reason,
            )
        except Exception as e:
            print(f"[WAF] Audit log write failed: {e}")

        return Response(content=f"Blocked: {reason}", status_code=403)

    # Request passed all WAF rules — forward to the proxy
    return await forwarder.forward_http(request)
