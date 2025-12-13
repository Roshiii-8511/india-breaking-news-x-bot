"""
Configuration module for India Breaking News X Bot.

Provides environment variable management and constants for:
- News API
- Gemini (Google GenAI) API
- Google Cloud Firestore
- X (Twitter) API
"""
import os
import json

def get_required_env(name: str) -> str:
    """Get a required environment variable (raises if missing)."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value

# ======================================================================
# News API Configuration
# ======================================================================
NEWS_API_KEY = get_required_env("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
NEWS_COUNTRY = "in"
NEWS_PAGE_SIZE = 20
# Freshness (hours) for "big breaking" filter
NEWS_MAX_AGE_HOURS = int(os.getenv("NEWS_MAX_AGE_HOURS", "24"))

# ======================================================================
# Gemini / Google GenAI Configuration
# ======================================================================
# Use GEMINI_API_KEY (from GitHub Secrets). This key is for the Gemini Developer API.
# Add near other LLM config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or ""   # required in production; empty ok for dev
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
# token limits to control cost
GEMINI_MAX_TOKENS_THREAD = int(os.getenv("GEMINI_MAX_TOKENS_THREAD") or 400)
GEMINI_MAX_TOKENS_SHORT = int(os.getenv("GEMINI_MAX_TOKENS_SHORT") or 300)


# ======================================================================
# Google Cloud Firestore Configuration (token store)
# ======================================================================
GCP_SERVICE_ACCOUNT_KEY_JSON = get_required_env("GCP_SERVICE_ACCOUNT_KEY")
try:
    GCP_SERVICE_ACCOUNT_KEY = json.loads(GCP_SERVICE_ACCOUNT_KEY_JSON)
except json.JSONDecodeError as e:
    raise ValueError(f"GCP_SERVICE_ACCOUNT_KEY is not valid JSON: {e}")

FIRESTORE_COLLECTION = "x_tokens"
FIRESTORE_DOCUMENT = "personal_bot"

# ======================================================================
# X (Twitter) API Configuration
# ======================================================================
X_CLIENT_ID = get_required_env("X_CLIENT_ID")
X_CLIENT_SECRET = get_required_env("X_CLIENT_SECRET")
X_OAUTH_TOKEN_URL = "https://api.x.com/2/oauth2/token"
X_TWEET_URL = "https://api.x.com/2/tweets"

# ======================================================================
# Logging & Debug
# ======================================================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
