-- 1. Security Audit Logs (Updated with new columns)
CREATE TABLE IF NOT EXISTS security_audit_logs (
    id SERIAL PRIMARY KEY,
    client_ip VARCHAR(50) NOT NULL,
    method VARCHAR(10) NOT NULL,
    blocked_path TEXT NOT NULL,
    rule_name VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 2. WAF Rules Configuration (New table)
CREATE TABLE IF NOT EXISTS waf_rules (
    rule_name VARCHAR(50) PRIMARY KEY,
    is_enabled BOOLEAN DEFAULT TRUE,
    config_data JSONB NOT NULL
);

-- 3. Insert default rule configurations if they don't already exist
INSERT INTO waf_rules (rule_name, is_enabled, config_data)
VALUES 
    ('UserAgentRule', true, '{"bad_agents": ["curl", "python-requests", "bot", "spider", "sqlmap"]}'::jsonb),
    ('SqlInjectionRule', true, '{"patterns": ["drop\\s+table", "union\\s+select", "or\\s+1\\s*=\\s*1", "--"]}'::jsonb),
    ('IPBlocklistRule', true, '{}'::jsonb),
    ('TimeAccessRule', true, '{"start_hour": 2, "end_hour": 1}'::jsonb),
    ('RateLimitRule', true, '{"max_requests": 50, "window_seconds": 10}'::jsonb),
    ('GeoBlockRule', true, '{"blocked_countries": ["RU", "CN", "KP"]}'::jsonb)
ON CONFLICT (rule_name) DO NOTHING;
