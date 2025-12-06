"""X (Twitter) API client for posting tweets.

This module handles:
- Posting individual tweets
- Creating tweet threads (tweet + replies)
- Error handling and logging
"""

import logging
import requests

from src.config import X_TWEET_URL


logger = logging.getLogger(__name__)


def post_tweet(
    access_token: str,
    text: str,
    in_reply_to_tweet_id: str | None = None,
) -> str:
    """
    Post a single tweet to X.
    
    Args:
        access_token: Valid X access token
        text: Tweet text (max 280 chars)
        in_reply_to_tweet_id: Optional tweet ID to reply to
        
    Returns:
        The posted tweet's ID
        
    Raises:
        ValueError: If posting fails
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {"text": text}
    
    if in_reply_to_tweet_id:
        payload["reply"] = {"in_reply_to_tweet_id": in_reply_to_tweet_id}
    
    try:
        logger.info(f"Posting tweet: {text[:50]}...")
        response = requests.post(X_TWEET_URL, json=payload, headers=headers)
        
        if response.status_code not in [200, 201]:
            logger.error(
                f"Failed to post tweet. Status: {response.status_code}. "
                f"Response: {response.text}"
            )
            raise ValueError(
                f"Failed to post tweet. Status: {response.status_code}. "
                f"Response: {response.text}"
            )
        
        data = response.json()
        tweet_id = data.get("data", {}).get("id")
        
        if not tweet_id:
            logger.error(f"Response missing tweet ID: {data}")
            raise ValueError(f"Response missing tweet ID: {data}")
        
        logger.info(f"Successfully posted tweet: {tweet_id}")
        return tweet_id
        
    except requests.RequestException as e:
        logger.error(f"Network error posting tweet: {e}")
        raise ValueError(f"Network error posting tweet: {e}") from e
    except Exception as e:
        logger.error(f"Error posting tweet: {e}")
        raise


def post_thread(access_token: str, tweets: list[str]) -> list[str]:
    """
    Post a thread of tweets to X.
    
    Posts the first tweet, then replies to it with subsequent tweets.
    
    Args:
        access_token: Valid X access token
        tweets: List of tweet texts
        
    Returns:
        List of posted tweet IDs in order
        
    Raises:
        ValueError: If posting any tweet fails
    """
    if not tweets:
        raise ValueError("No tweets to post")
    
    tweet_ids = []
    
    try:
        # Post first tweet
        first_id = post_tweet(access_token, tweets[0])
        tweet_ids.append(first_id)
        logger.info(f"Posted thread start: {first_id}")
        
        # Post replies
        for i, tweet_text in enumerate(tweets[1:], start=1):
            reply_id = post_tweet(
                access_token,
                tweet_text,
                in_reply_to_tweet_id=tweet_ids[-1],
            )
            tweet_ids.append(reply_id)
            logger.info(f"Posted tweet {i+1}/{len(tweets)}: {reply_id}")
        
        logger.info(f"Successfully posted thread of {len(tweet_ids)} tweets")
        return tweet_ids
        
    except Exception as e:
        logger.error(f"Failed to post thread: {e}")
        raise ValueError(f"Failed to post thread: {e}") from e
