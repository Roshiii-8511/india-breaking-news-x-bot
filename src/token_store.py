"""Firestore-based token storage for X OAuth2 refresh tokens.

This module manages the rotating refresh_token used for X OAuth2 authentication.
The token is stored in Firestore and rotated on each successful refresh.

Setup:
    1. Create a GCP Service Account with Firestore permissions
    2. Add the service account JSON as env var GCP_SERVICE_ACCOUNT_KEY
    3. Manually set the initial refresh_token in Firestore console:
       - Collection: x_tokens
       - Document: personal_bot
       - Field: refresh_token = (your token)
    4. After first run, the token will be automatically rotated
"""

import logging
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

from src.config import GCP_SERVICE_ACCOUNT_KEY, FIRESTORE_COLLECTION, FIRESTORE_DOCUMENT


logger = logging.getLogger(__name__)


def get_firestore_client() -> firestore.Client:
    """
    Initialize and return a Firestore client using service account credentials.
    
    Returns:
        Initialized Firestore Client
    """
    credentials = service_account.Credentials.from_service_account_info(
        GCP_SERVICE_ACCOUNT_KEY
    )
    client = firestore.Client(credentials=credentials)
    return client


def get_refresh_token() -> str:
    """
    Retrieve the current refresh token from Firestore.
    
    Reads from:
        Collection: x_tokens
        Document: personal_bot
        Field: refresh_token
    
    Returns:
        The refresh token string
        
    Raises:
        ValueError: If token not found in Firestore
        Exception: If Firestore operation fails
    """
    try:
        client = get_firestore_client()
        doc = client.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOCUMENT).get()
        
        if not doc.exists:
            raise ValueError(
                f"Firestore document {FIRESTORE_COLLECTION}/{FIRESTORE_DOCUMENT} does not exist. "
                "Please initialize it manually with a refresh_token field."
            )
        
        refresh_token = doc.get("refresh_token")
        if not refresh_token:
            raise ValueError(
                f"Field 'refresh_token' not found in {FIRESTORE_COLLECTION}/{FIRESTORE_DOCUMENT}"
            )
        
        logger.info("Successfully retrieved refresh token from Firestore")
        return refresh_token
        
    except Exception as e:
        logger.error(f"Failed to retrieve refresh token: {e}")
        raise


def update_refresh_token(new_token: str) -> None:
    """
    Update the refresh token in Firestore.
    
    Writes to:
        Collection: x_tokens
        Document: personal_bot
        Fields:
            - refresh_token: new token
            - updated_at: current timestamp
    
    Args:
        new_token: The new refresh token to store
        
    Raises:
        Exception: If Firestore operation fails
    """
    try:
        client = get_firestore_client()
        client.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOCUMENT).update({
            "refresh_token": new_token,
            "updated_at": datetime.utcnow(),
        })
        logger.info("Successfully updated refresh token in Firestore")
        
    except Exception as e:
        logger.error(f"Failed to update refresh token: {e}")
        raise
