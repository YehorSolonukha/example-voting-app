import httpx
import asyncpg
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import redis.asyncio as redis

from core.config import UPSTREAM_URL, WAF_DB_URL, WAF_REDIS_URL, RESULT_SERVICE_URI
from core.rule_config import rule_manager
from waf.engine import WAFEngine

app = FastAPI()

from fastapi.responses import Response, RedirectResponse

# Mount the frontend UI (must come before the catch-all proxy route)
app.mount("/admin/", StaticFiles(directory="static", html=True), name="admin")

@app.get("/admin")
async def admin_redirect():
    return RedirectResponse(url="/admin/")

# --- DASHBOARD STATE & WEBSOCKETS ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

ws_manager = ConnectionManager()
# ------------------------------------

# Initialize the WAF Engine once
waf = WAFEngine()

@app.on_event("startup")
async def startup_event():
    # We create a persistent database connection pool that our app will use
    app.state.db_pool = await asyncpg.create_pool(WAF_DB_URL, min_size=2, max_size=10)
    print("[Gateway] Database pool established!")
    
    app.state.redis_pool = redis.from_url(WAF_REDIS_URL, decode_responses=True)
    print("[Gateway] Redis connection established!")
    
    # Give the connection pool to our Rule Manager so it can start syncing configs
    rule_manager.set_pool(app.state.db_pool)
    
    # Boot up any async WAF rules
    await waf.startup()

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.db_pool.close()
    await app.state.redis_pool.close()

# --- DASHBOARD API ENDPOINTS ---
@app.get("/api/stats")
async def get_stats():
    # Query database for a breakdown of which rules are firing most often
    records = await app.state.db_pool.fetch("SELECT rule_name, COUNT(*) as count FROM security_audit_logs GROUP BY rule_name")
    rule_breakdown = {r['rule_name']: r['count'] for r in records}
    
    total_reqs = await app.state.redis_pool.get("waf_total_requests") or 0
    blocked_reqs = await app.state.redis_pool.get("waf_blocked_requests") or 0
    
    return {
        "total_requests": int(total_reqs),
        "blocked_requests": int(blocked_reqs),
        "rule_breakdown": rule_breakdown
    }

@app.get("/api/logs")
async def get_logs(limit: int = 50):
    # Fetch recent logs from DB
    records = await app.state.db_pool.fetch("SELECT * FROM security_audit_logs ORDER BY timestamp DESC LIMIT $1", limit)
    # asyncpg Record objects can't be automatically serialized to JSON by FastAPI, so we convert them to dicts
    return [dict(r) for r in records]

@app.get("/api/rules")
async def get_rules():
    # Return the currently loaded rules straight from memory
    return rule_manager.rules_config

class RuleUpdate(BaseModel):
    is_enabled: bool
    config: dict

@app.put("/api/rules/{rule_name}")
async def update_rule(rule_name: str, update_data: RuleUpdate):
    # Write the UI changes to the database
    await app.state.db_pool.execute(
        "UPDATE waf_rules SET is_enabled = $1, config_data = $2 WHERE rule_name = $3",
        update_data.is_enabled, json.dumps(update_data.config), rule_name
    )
    # Force the rule manager to pull the new DB changes immediately (no 60s wait)
    # Note: poll_database is an infinite loop, so we shouldn't await it here. 
    # Instead, we just fetch manually to update memory instantly.
    try:
        r = await app.state.db_pool.fetchrow("SELECT is_enabled, config_data FROM waf_rules WHERE rule_name = $1", rule_name)
        if r:
            rule_manager.rules_config[rule_name] = {
                "is_enabled": r['is_enabled'],
                "config": json.loads(r['config_data']) if isinstance(r['config_data'], str) else r['config_data']
            }
    except Exception as e:
        print(f"Error syncing rule update: {e}")
        
    return {"status": "success", "message": f"{rule_name} updated."}

@app.websocket("/ws/live-feed")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # We keep the connection open forever. The browser just listens.
            await websocket.receive_text()
    except Exception:
        ws_manager.disconnect(websocket)
# -------------------------------

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    
    # Ignore background requests that aren't actually meant for our backend application
    if path == "favicon.ico" or path.startswith("admin") or path.startswith("api") or path.startswith("ws"):
        # We just return 404 for them instead of proxying them to the backend 
        return Response(status_code=404)
        
    # We increment our persistent request counter in Redis
    await app.state.redis_pool.incr("waf_total_requests")

    # --- WAF INSPECTION ---
    block_result = await waf.inspect_all(request)
    if block_result:
        await app.state.redis_pool.incr("waf_blocked_requests")
        rule_name, block_reason = block_result
        
        # 1. Broadcast the attack instantly to anyone looking at the Dashboard UI
        await ws_manager.broadcast({
            "client_ip": request.client.host,
            "method": request.method,
            "blocked_path": f"/{path}",
            "rule_name": rule_name,
            "reason": block_reason
        })

        # 2. Log the enriched attack data to the database asynchronously
        try:
            await app.state.db_pool.execute(
                "INSERT INTO security_audit_logs (client_ip, method, blocked_path, rule_name, reason) VALUES ($1, $2, $3, $4, $5)",
                request.client.host, request.method, f"/{path}", rule_name, block_reason
            )
        except Exception as e:
            print(f"[Gateway] Failed to log attack to DB: {e}")
            
        # 3. Return the block response to the attacker immediately
        return Response(content=f"WAF BLOCK: {block_reason}", status_code=403)
    # ----------------------

    # Read body bytes here so we can forward them
    body_bytes = await request.body()
    
    # Check the Referer header to see if this request originated from the Result page
    referer = request.headers.get("referer", "")
    
    # Determine upstream destination based on path or referer
    if path == "result" or path.startswith("result/"):
        target_path = path[len("result"):]
        if target_path.startswith("/"):
            target_path = target_path[1:]
        target_url = f"{RESULT_SERVICE_URI}/{target_path}"
    elif path.startswith("socket.io") or "result" in referer:
        # If the path is socket.io OR the browser was on the /result page when it asked for this file (like app.js),
        # we know it belongs to the Result app!
        target_url = f"{RESULT_SERVICE_URI}/{path}"
    else:
        # Default route to vote app
        target_url = f"{UPSTREAM_URL}/{path}"
    
    # Forward the request safely
    async with httpx.AsyncClient() as client:
        upstream_response = await client.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            content=body_bytes
        )

        
    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=dict(upstream_response.headers)
    )