UPDATE waf_rules 
SET config_data = '{"patterns": ["drop\\s+table", "union\\s+select", "or\\s+1\\s*=\\s*1", "--"]}'::jsonb 
WHERE rule_name = 'SqlInjectionRule';
