import asyncio
import json

class RuleConfigManager:
    def __init__(self):
        self.rules_config = {}
        self.db_pool = None

    def set_pool(self, pool):
        self.db_pool = pool
        asyncio.create_task(self.poll_database())

    async def poll_database(self):
        while True:
            if self.db_pool:
                try:
                    records = await self.db_pool.fetch("SELECT rule_name, is_enabled, config_data FROM waf_rules")
                    for r in records:
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
            
            await asyncio.sleep(60)

    def get_config(self, rule_name: str, default: dict = None) -> dict | None:
        rule = self.rules_config.get(rule_name)
        
        if not rule:
            return default or {}
            
        if not rule.get("is_enabled", True):
            return None
            
        return rule.get("config", default or {})

rule_manager = RuleConfigManager()
