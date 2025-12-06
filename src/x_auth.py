import logging
import base64
from typing import Tuple

import requests

from . import config
from .token_store import get_refresh_token, update_refresh_token

logger = logging.getLogger(__name__)


def refresh_access_token() -> Tuple[str, str]:
    """
    Refresh the X access token using the long-lived refresh_token stored in Firestore.

    Flow:
      1. Read current refresh_token from Firestore.
      2. Call X OAuth2 token endpoint with grant_type=refresh_token
         using Basic auth (client_id:client_secret).
      3. Parse access_token + new refresh_token from response.
      4. Store new refresh_token back to Firestore.
      5. Return (access_token, new_refresh_token).

    Raises:
        ValueError: if the refresh fails or tokens are missing.
    """
    logger.info("Retrieving refresh token from Firestore...")
    refresh_token = get_refresh_token()

    token_url = getattr(config, "X_OAUTH_TOKEN_URL", "https://api.x.com/2/oauth2/token")
    logger.info("Refreshing access token via %s...", token_url)

    # Build Basic auth header: base64(client_id:client_secret)
    creds = f"{config.X_CLIENT_ID}:{config.X_CLIENT_SECRET}".encode("utf-8")
    basic_token = base64.b64encode(creds).decode("utf-8")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic_token}",
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    try:
        response = requests.post(token_url, headers=headers, data=data, timeout=30)
    except requests.RequestException as e:
        logger.error("Network error while refreshing X access token: %s", e)
        raise ValueError(
            f"Network error while refreshing X access token: {e}"
        ) from e

    if response.status_code != 200:
        logger.error(
            "X OAuth2 refresh failed with status %s: %s",
            response.status_code,
            response.text,
        )
        raise ValueError(
            "Failed to refresh X access token. Status: "
            f"{response.status_code}. Response: {response.text}. "
            "This may indicate an invalid or expired refresh_token. "
            "Re-authorize the X app to get a new token."
        )

    payload = response.json()
    access_token = payload.get("access_token")
    new_refresh_token = payload.get("refresh_token")

    if not access_token or not new_refresh_token:
        logger.error(
            "X OAuth2 refresh response missing access_token or refresh_token: %s",
            payload,
        )
        raise ValueError(
            "X OAuth2 refresh response missing access_token or refresh_token."
        )

    # Persist new refresh_token for next runs
    update_refresh_token(new_refresh_token)
    logger.info(
        "Successfully refreshed X access token and updated refresh token in Firestore."
    )

    return access_token, new_refresh_token
