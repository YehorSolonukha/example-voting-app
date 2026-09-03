-- Security audit log: one row per blocked request
CREATE TABLE IF NOT EXISTS security_audit_logs (
    id           SERIAL PRIMARY KEY,
    client_ip    VARCHAR(50)  NOT NULL,
    method       VARCHAR(10)  NOT NULL,
    blocked_path TEXT         NOT NULL,
    rule_name    VARCHAR(50)  NOT NULL,
    reason       TEXT         NOT NULL,
    timestamp    TIMESTAMPTZ  DEFAULT NOW()
);

-- WAF rule configuration: toggled and tuned via the admin API
CREATE TABLE IF NOT EXISTS waf_rules (
    rule_name   VARCHAR(50) PRIMARY KEY,
    is_enabled  BOOLEAN     DEFAULT TRUE,
    config_data JSONB       NOT NULL
);

-- Default rule configs seeded on first boot.
-- TimeAccessRule: start_hour=1, end_hour=3 means BLOCK 1:00-3:00 AM UTC only.
-- All other hours (3:00 AM through 1:00 AM) are allowed.
INSERT INTO waf_rules (rule_name, is_enabled, config_data) VALUES
    ('UserAgentRule',    true, '{"bad_agents": ["sqlmap", "nikto", "nmap", "masscan"]}'::jsonb),
    ('SqlInjectionRule', true, '{"patterns": ["drop\\s+table", "union\\s+select", "or\\s+1\\s*=\\s*1", "--"]}'::jsonb),
    ('IPBlocklistRule',  true, '{}'::jsonb),
    ('TimeAccessRule',   true, '{"start_hour": 1, "end_hour": 3}'::jsonb),
    ('RateLimitRule',    true, '{"max_requests": 50, "window_seconds": 10}'::jsonb),
    ('GeoBlockRule',     true, '{"blocked_countries": ["RU", "CN", "KP"]}'::jsonb)
ON CONFLICT (rule_name) DO NOTHING;
