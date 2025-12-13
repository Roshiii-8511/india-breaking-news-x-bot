"""
Configuration module for India Breaking News X Bot.

Handles:
- News API
- Gemini REST API
- Google Firestore
- X (Twitter) API
"""

import os
import json


def get_required_env(name: str) -> str:
    """Fetch required env var or raise clear error."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value


# ============================================================================
# NEWS API CONFIG
# ============================================================================
NEWS_API_KEY = get_required_env("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
NEWS_COUNTRY = "in"
NEWS_PAGE_SIZE = 20

# Filter old news (in hours)
NEWS_MAX_AGE_HOURS = 24


# ============================================================================
# GEMINI REST API CONFIG
# ============================================================================
GEMINI_API_KEY = get_required_env("GEMINI_API_KEY")

# Default model to use
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# It will auto-build final API endpoint:
# https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key=API_KEY
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Token limits
GEMINI_MAX_TOKENS_THREAD = 400
GEMINI_MAX_TOKENS_SHORT = 200


# ============================================================================
# FIRESTORE CONFIG
# ============================================================================
GCP_SERVICE_ACCOUNT_KEY_JSON = get_required_env("GCP_SERVICE_ACCOUNT_KEY")

try:
    GCP_SERVICE_ACCOUNT_KEY = json.loads(GCP_SERVICE_ACCOUNT_KEY_JSON)
except json.JSONDecodeError as e:
    raise ValueError(f"GCP_SERVICE_ACCOUNT_KEY is not valid JSON: {e}")

FIRESTORE_COLLECTION = "x_tokens"
FIRESTORE_DOCUMENT = "personal_bot"


# ============================================================================
# X (TWITTER) API CONFIG
# ============================================================================
X_CLIENT_ID = get_required_env("X_CLIENT_ID")
X_CLIENT_SECRET = get_required_env("X_CLIENT_SECRET")

X_OAUTH_TOKEN_URL = "https://api.x.com/2/oauth2/token"
X_TWEET_URL = "https://api.x.com/2/tweets"


# ============================================================================
# DEBUG
# ============================================================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
