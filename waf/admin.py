"""Admin dashboard API and WebSocket live feed.

This module is purely about the admin interface.
It has zero knowledge of proxying or WAF inspection logic.
Those live in main.py and rules/ respectively.

Routes registered here:
  GET  /admin            → redirect to /admin/
  GET  /api/stats        → total/blocked request counts + rule breakdown
  GET  /api/logs         → recent blocked request audit log
  GET  /api/rules        → current in-memory rule configs
  PUT  /api/rules/{name} → update a rule (DB + in-memory cache)
  WS   /ws/live-feed     → real-time blocked-request feed for the dashboard
"""
import json
from fastapi import APIRouter, WebSocket, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from shared.redis_client import redis_client
from rules.rule_config import rule_manager

router = APIRouter()


# ---------------------------------------------------------------------------
# WebSocket live feed
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Tracks open admin dashboard WebSocket connections and broadcasts to all."""

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._connections:
            self._connections.remove(ws)

    async def broadcast(self, payload: dict):
        """Send a JSON payload to every connected admin dashboard tab."""
        dead = []
        for ws in self._connections:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


# Singleton exported so main.py can call live_feed.broadcast() after a block
live_feed = ConnectionManager()


@router.websocket("/ws/live-feed")
async def websocket_live_feed(ws: WebSocket):
    """Admin dashboard live feed. Pushes blocked-request events in real time."""
    await live_feed.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep connection alive; browser only listens
    except Exception:
        live_feed.disconnect(ws)


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

@router.get("/admin")
async def admin_redirect():
    return RedirectResponse(url="/admin/")


@router.get("/api/stats")
async def get_stats(request: Request):
    """Returns total/blocked request counts and a per-rule block breakdown."""
    pool = request.app.state.db_pool
    records = await pool.fetch(
        "SELECT rule_name, COUNT(*) AS count "
        "FROM security_audit_logs GROUP BY rule_name"
    )
    rule_breakdown = {r["rule_name"]: r["count"] for r in records}
    total = await redis_client.get("waf_total_requests") or 0
    blocked = await redis_client.get("waf_blocked_requests") or 0
    return {
        "total_requests": int(total),
        "blocked_requests": int(blocked),
        "rule_breakdown": rule_breakdown,
    }


@router.get("/api/logs")
async def get_logs(request: Request, limit: int = 50):
    """Returns the most recent blocked-request audit log entries."""
    pool = request.app.state.db_pool
    records = await pool.fetch(
        "SELECT * FROM security_audit_logs ORDER BY timestamp DESC LIMIT $1",
        limit,
    )
    return [dict(r) for r in records]


@router.get("/api/rules")
async def get_rules():
    """Returns the currently active in-memory rule configuration."""
    return rule_manager.rules_config


class RuleUpdate(BaseModel):
    is_enabled: bool
    config: dict


@router.put("/api/rules/{rule_name}")
async def update_rule(rule_name: str, update: RuleUpdate, request: Request):
    """Updates a rule's config in the database and instantly in memory."""
    pool = request.app.state.db_pool
    await pool.execute(
        "UPDATE waf_rules SET is_enabled = $1, config_data = $2 WHERE rule_name = $3",
        update.is_enabled,
        json.dumps(update.config),
        rule_name,
    )
    # Instant in-memory update — no need to wait for the 60s poll cycle
    await rule_manager.update(rule_name, update.is_enabled, update.config)
    return {"status": "ok", "rule": rule_name}
