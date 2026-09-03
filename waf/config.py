import os
from dotenv import load_dotenv

load_dotenv()

PROXY_URL = os.getenv("PROXY_URL", "http://proxy:9091")
WAF_DB_URL = os.getenv("WAF_DB_URL", "postgres://postgres:super_secret_password_here@waf-db:5432/waf_logs")
WAF_REDIS_URL = os.getenv("WAF_REDIS_URL", "redis://waf-redis:6379")
