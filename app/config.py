import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

RETELL_API_KEY = os.getenv("RETELL_API_KEY")
RETELL_AGENT_ID = os.getenv("RETELL_AGENT_ID")
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "home_credit_lap")
VERIFY_RETELL_WEBHOOKS = os.getenv("VERIFY_RETELL_WEBHOOKS", "true").lower() == "true"

# CORS settings - configurable for local development
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
