from datetime import datetime, timezone
from fastapi import Request
from .base import WAFRule
from .rule_config import rule_manager


class TimeAccessRule(WAFRule):
    """Blocks access during a configured UTC hour window.

    Config (live-updated via admin API):
      start_hour  int  — first blocked hour (UTC, 0–23, inclusive)
      end_hour    int  — last blocked hour (UTC, 0–23, exclusive)

    Default: block 1:00–3:00 AM UTC. All other hours are open.

    Uses datetime.now(timezone.utc) explicitly so behaviour is always
    deterministic, regardless of what timezone the container runs in.
    Without this, the same code gives different results on different
    machines depending on the host OS timezone — a very common bug.
    """

    async def inspect(self, request: Request) -> str | None:
        config = rule_manager.get_config(
            "TimeAccessRule", {"start_hour": 1, "end_hour": 3}
        )
        if config is None:
            return None  # Rule is disabled

        start = config.get("start_hour", 1)
        end = config.get("end_hour", 3)
        current_hour = datetime.now(timezone.utc).hour

        if start <= current_hour < end:
            return (
                f"Time-based block: service unavailable {start:02d}:00–{end:02d}:00 UTC."
            )

        return None
