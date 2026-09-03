import asyncio
import json
import asyncpg


class RuleConfigManager:
    """Polls the database every 60 seconds and keeps rule configs in memory.

    Rules read their config from here on every request, so any change made
    via the admin API is live within one poll cycle — or instantly after a
    PUT /api/rules/{name} call updates the in-memory cache directly.
    """

    def __init__(self):
        self.rules_config: dict = {}
        self._pool: asyncpg.Pool | None = None
        self._task: asyncio.Task | None = None

    def start(self, pool: asyncpg.Pool):
        """Called once at application startup inside the lifespan context."""
        self._pool = pool
        self._task = asyncio.create_task(self._poll_loop())

    def stop(self):
        """Called at shutdown to cleanly cancel the background task."""
        if self._task:
            self._task.cancel()

    async def _poll_loop(self):
        while True:
            await self._sync()
            await asyncio.sleep(60)

    async def _sync(self):
        try:
            records = await self._pool.fetch(
                "SELECT rule_name, is_enabled, config_data FROM waf_rules"
            )
            for r in records:
                config_data = r["config_data"]
                # asyncpg returns JSONB as a dict; handle legacy string values too
                if isinstance(config_data, str):
                    config_data = json.loads(config_data)
                self.rules_config[r["rule_name"]] = {
                    "is_enabled": r["is_enabled"],
                    "config": config_data,
                }
            print(f"[WAF] Synced {len(records)} rule configs from database.")
        except Exception as e:
            print(f"[WAF] Rule config sync failed: {e}")

    def get_config(self, rule_name: str, default: dict | None = None) -> dict | None:
        """Returns the config dict for a rule, or None if the rule is disabled.

        Returns the default dict if the rule has not been loaded from DB yet
        (e.g. on the first few requests before the initial poll completes).
        Returning None signals the rule to skip its inspection entirely.
        """
        rule = self.rules_config.get(rule_name)
        if rule is None:
            return default or {}
        if not rule.get("is_enabled", True):
            return None  # Disabled — tell the rule to pass through
        return rule.get("config", default or {})

    async def update(self, rule_name: str, is_enabled: bool, config: dict):
        """Instantly updates the in-memory cache after an admin API write.

        This means the new config takes effect on the very next request,
        without waiting for the next 60-second poll cycle.
        """
        self.rules_config[rule_name] = {
            "is_enabled": is_enabled,
            "config": config,
        }


# Module-level singleton — imported by all rules and the admin router
rule_manager = RuleConfigManager()
