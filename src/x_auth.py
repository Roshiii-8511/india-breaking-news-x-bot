"""X (Twitter) OAuth2 authentication and token refresh.

This module handles:
- Retrieving current refresh token from Firestore
- Exchanging it for a new access token via X OAuth2 endpoint
- Storing the new refresh token back in Firestore
- Returning access token for API requests
"""

import logging
import requests
import base64

from src.config import (
    X_CLIENT_ID,
    X_OAUTH_TOKEN_URL,
 X_CLIENT_SECRET,
)
from src.token_store import get_refresh_token, update_refresh_token


logger = logging.getLogger(__name__)


def refresh_access_token() -> tuple[str, str]:
    """
    Refresh X access token using the stored refresh token.
    
    Steps:
        1. Get current refresh_token from Firestore
        2. POST to X OAuth2 token endpoint with client_id and grant_type
        3. Parse response to get new access_token and refresh_token
        4. Store new refresh_token in Firestore
        5. Return (access_token, new_refresh_token)
    
    Returns:
        Tuple of (access_token, refresh_token)
        
    Raises:
        ValueError: If refresh fails (invalid token, network error, etc.)
        Exception: If Firestore operations fail
    """
    try:
        # Step 1: Get current refresh token
        logger.info("Retrieving refresh token from Firestore...")
        current_refresh_token = get_refresh_token()
        
        # Step 2: Build Basic auth header (client_id:client_secret in base64)
    creds = f"{X_CLIENT_ID}:{X_CLIENT_SECRET}".encode("utf-8")
    basic_token = base64.b64encode(creds).decode("utf-8")
    
    # Step 3: Prepare headers with Basic auth
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic_token}",
    }
    
    # Step 4: Prepare body (no client_id needed for confidential client)
    body = {
        "refresh_token": current_refresh_token,
        "grant_type": "refresh_token",
    }
    
logger.info(f"Refreshing access token via {X_OAUTH_TOKEN_URL}...")
    
    # Step 5: Make POST request
    response = requests.post(X_OAUTH_TOKEN_URL, headers=headers, data=body)
        logger.info(f"Refreshing access token via {X_OAUTH_TOKEN_URL}...")
        
        # Step 3: Make POST request
        response = requests.post(X_OAUTH_TOKEN_URL, headers=headers, data=body)
        
        if response.status_code not in [200, 201]:
            logger.error(
                f"X OAuth2 refresh failed with status {response.status_code}: {response.text}"
            )
            raise ValueError(
                f"Failed to refresh X access token. Status: {response.status_code}. "
                f"Response: {response.text}. "
                "This may indicate an invalid or expired refresh_token. "
                "Re-authorize the X app to get a new token."
            )
        
        # Step 4: Parse response
        data = response.json()
        
        access_token = data.get("access_token")
        new_refresh_token = data.get("refresh_token")
        
        if not access_token or not new_refresh_token:
            logger.error(f"X OAuth2 response missing tokens: {data}")
            raise ValueError(
                "X OAuth2 response is missing 'access_token' or 'refresh_token' fields. "
                f"Got: {data}"
            )
        
        # Step 5: Store new refresh token
        logger.info("Storing new refresh token in Firestore...")
        update_refresh_token(new_refresh_token)
        
        logger.info("Successfully refreshed X access token")
        return (access_token, new_refresh_token)
        
    except requests.RequestException as e:
        logger.error(f"Network error during X OAuth2 refresh: {e}")
        raise ValueError(f"Network error refreshing X access token: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during X OAuth2 refresh: {e}")
        raise
