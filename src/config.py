"""
Configuration module for India Breaking News X Bot.
Handles:
- News API
- Firestore
- X (Twitter) OAuth
"""

import os
import json


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value


# =============================================================================
# News API
# =============================================================================
NEWS_API_KEY = get_required_env("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
NEWS_COUNTRY = "in"
NEWS_PAGE_SIZE = 20

# Only consider news from last X hours
NEWS_MAX_AGE_HOURS = 24


# =============================================================================
# Google Cloud Firestore
# =============================================================================
GCP_SERVICE_ACCOUNT_KEY_JSON = get_required_env("GCP_SERVICE_ACCOUNT_KEY")

try:
    GCP_SERVICE_ACCOUNT_KEY = json.loads(GCP_SERVICE_ACCOUNT_KEY_JSON)
except json.JSONDecodeError as e:
    raise ValueError(f"GCP_SERVICE_ACCOUNT_KEY is not valid JSON: {e}")

FIRESTORE_COLLECTION = "x_tokens"
FIRESTORE_DOCUMENT = "personal_bot"


# =============================================================================
# X (Twitter) API
# =============================================================================
X_CLIENT_ID = get_required_env("X_CLIENT_ID")
X_CLIENT_SECRET = get_required_env("X_CLIENT_SECRET")

X_OAUTH_TOKEN_URL = "https://api.x.com/2/oauth2/token"
X_TWEET_URL = "https://api.x.com/2/tweets"


# =============================================================================
# Debug
# =============================================================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
