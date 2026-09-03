import os
from dotenv import load_dotenv

load_dotenv()
UPSTREAM_URL = os.getenv("VOTE_SERVICE_URI", "http://vote:80")
WAF_DB_URL = os.getenv("WAF_DB_URL", "postgres://postgres:super_secret_password_here@waf-db:5432/waf_logs")
WAF_REDIS_URL = os.getenv("WAF_REDIS_URL", "redis://waf-redis:6379")
RESULT_SERVICE_URI = os.getenv("RESULT_SERVICE_URI", "http://result:80")
