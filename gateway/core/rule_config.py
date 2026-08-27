import asyncio
import json

class RuleConfigManager:
    def __init__(self):
        self.rules_config = {}
        self.db_pool = None

    def set_pool(self, pool):
        self.db_pool = pool
        # Start background polling loop
        asyncio.create_task(self.poll_database())

    async def poll_database(self):
        while True:
            if self.db_pool:
                try:
                    records = await self.db_pool.fetch("SELECT rule_name, is_enabled, config_data FROM waf_rules")
                    for r in records:
                        # asyncpg returns JSONB as a string if we don't have a specific decoder attached, 
                        # so we use json.loads. If it's already parsed as a dict, we just use it.
                        config_data = r['config_data']
                        if isinstance(config_data, str):
                            config_data = json.loads(config_data)
                            
                        self.rules_config[r['rule_name']] = {
                            "is_enabled": r['is_enabled'],
                            "config": config_data
                        }
                    print(f"[WAF] Synced {len(records)} rule configs from database.")
                except Exception as e:
                    print(f"[WAF] Failed to sync rules from DB: {e}")
            
            # Wait 60 seconds before checking again (as you requested!)
            await asyncio.sleep(60)

    def get_config(self, rule_name: str, default: dict = None) -> dict | None:
        """
        Returns the config dict if rule is enabled.
        Returns None if rule is completely disabled.
        """
        rule = self.rules_config.get(rule_name)
        
        # If it doesn't exist in DB yet (or on first boot), fallback to enabled with default config
        if not rule:
            return default or {}
            
        if not rule.get("is_enabled", True):
            return None # Rule is disabled in DB
            
        return rule.get("config", default or {})

# Global instance that the rest of the app can import and use
rule_manager = RuleConfigManager()
