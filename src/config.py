"""Configuration module for India Breaking News X Bot.

Provides environment variable management and constants for:
- News API
- OpenAI API
- Google Cloud Firestore
- X (Twitter) API
"""

import os
import json


def get_required_env(name: str) -> str:
    """
    Get a required environment variable.
    
    Args:
        name: The environment variable name
        
    Returns:
        The environment variable value
        
    Raises:
        ValueError: If the environment variable is not set
    """
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value


# ============================================================================
# News API Configuration
# ============================================================================

NEWS_API_KEY = get_required_env("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
NEWS_COUNTRY = "in"
NEWS_PAGE_SIZE = 20


# ============================================================================
# OpenAI Configuration
# ============================================================================

OPENAI_API_KEY = get_required_env("OPENAI_API_KEY")
AI_MODEL = "gpt-4o-mini"  # Change as needed (e.g., "gpt-4-turbo", "gpt-4")


# ============================================================================
# Google Cloud Firestore Configuration
# ============================================================================

# GCP_SERVICE_ACCOUNT_KEY is a JSON string stored as an env variable
# It should contain the full service account credentials
GCP_SERVICE_ACCOUNT_KEY_JSON = get_required_env("GCP_SERVICE_ACCOUNT_KEY")

# Parse the JSON string into a dict for Firestore client
try:
    GCP_SERVICE_ACCOUNT_KEY = json.loads(GCP_SERVICE_ACCOUNT_KEY_JSON)
except json.JSONDecodeError as e:
    raise ValueError(
        f"GCP_SERVICE_ACCOUNT_KEY is not valid JSON: {e}"
    )

FIRESTORE_COLLECTION = "x_tokens"
FIRESTORE_DOCUMENT = "personal_bot"


# ============================================================================
# X (Twitter) API Configuration
# ============================================================================

X_CLIENT_ID = get_required_env("X_CLIENT_ID")
X_OAUTH_TOKEN_URL = "https://api.x.com/2/oauth2/token"
X_TWEET_URL = "https://api.x.com/2/tweets"


# ============================================================================
# Logging & Debugging
# ============================================================================

DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
