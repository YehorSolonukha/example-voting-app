import os
from dotenv import load_dotenv

# This automatically finds the .env file and loads its contents into the OS environment variables
load_dotenv()

# We read from the environment variable first. 
# If it's not set (like when you run it locally outside of Docker), we default to "http://vote:80"
UPSTREAM_URL = os.getenv("VOTE_SERVICE_URI", "http://vote:80")

# Database connection string for our audit logs
WAF_DB_URL = os.getenv("WAF_DB_URL", "postgres://postgres:super_secret_password_here@waf-db-cluster-rw:5432/waf_logs")

# Redis connection string for rate limiting
WAF_REDIS_URL = os.getenv("WAF_REDIS_URL", "redis://waf-redis:6379")
