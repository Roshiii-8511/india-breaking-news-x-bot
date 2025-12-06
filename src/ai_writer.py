"""AI-powered tweet generation using OpenRouter (free-tier LLM).

This module uses OpenRouter's chat completions API with free-tier models to generate:
- 5-tweet detailed threads for big stories
- 1-2 short standalone tweets for supporting stories
"""

import logging
import requests
from typing import Optional

from . import config


logger = logging.getLogger(__name__)


def _call_openrouter(
    messages: list[dict],
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """
    Call OpenRouter chat completions endpoint and return assistant content.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0.0-1.0)
        
    Returns:
        The assistant's response text
        
    Raises:
        Exception: If API call fails
    """
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Roshiii-8511/india-breaking-news-x-bot",
        "X-Title": "India Breaking News X Bot",
    }
    
    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    try:
        logger.info(f"Calling OpenRouter with model {config.OPENROUTER_MODEL}")
        response = requests.post(
            config.OPENROUTER_API_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )
        
        if response.status_code not in [200, 201]:
            logger.error(
                f"OpenRouter API error {response.status_code}: {response.text}"
            )
            raise Exception(
                f"OpenRouter API failed with status {response.status_code}: {response.text}"
            )
        
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not content:
            logger.error(f"No content in OpenRouter response: {data}")
            raise Exception("OpenRouter returned empty content")
        
        logger.info("Successfully called OpenRouter")
        return content
        
    except requests.RequestException as e:
        logger.error(f"Network error calling OpenRouter: {e}")
        raise Exception(f"Network error: {e}") from e


def _clean_spaces(text: str) -> str:
    """
    Normalize spaces in text (remove extra whitespace).
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    return " ".join(text.split())


def truncate_to_280(text: str) -> str:
    """
    Truncate text to 280 characters for X/Twitter compliance.
    
    Args:
        text: Input text
        
    Returns:
        Text truncated to max 280 chars, with "..." if needed
    """
    text = text.strip()
    if len(text) <= 280:
        return text
    return text[:277] + "..."


def generate_thread_for_big_story(big_story: dict) -> list[str]:
    """
    Generate a 5-tweet thread for the big story using OpenRouter.
    
    Args:
        big_story: Dict with title, description, source, url, publishedAt
        
    Returns:
        List of exactly 5 tweet strings (each <= 280 chars)
        
    Raises:
        ValueError: If generation fails
    """
    title = big_story.get("title", "")
    description = big_story.get("description", "")
    source = big_story.get("source", {}).get("name", "News")
    url = big_story.get("url", "")
    
    system_prompt = """You are a professional social media manager for India news. 
Generate exactly 5 tweets for a breaking news story.
Each tweet must be under 280 characters.
Separate tweets with a line containing only '---'.
Format: Tweet text, then ---, then next tweet.

Tweet guidelines:
- Tweet 1: BREAKING hook with relevant emojis and 1-2 hashtags (#India #News etc)
- Tweet 2: Background and context - why this matters now
- Tweet 3: Key facts and details changing
- Tweet 4: Impact on Indians, economy, or daily life
- Tweet 5: Balanced conclusion and thoughtful question

Tone: diplomatic, neutral, India-focused, analytical. No hate speech, no misinformation, no conspiracy theories."""
    
    user_prompt = f"""Breaking News Story:
Title: {title}
Description: {description}
Source: {source}
URL: {url}

Generate the 5-tweet thread now:"""
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        logger.info(f"Generating 5-tweet thread for: {title[:50]}...")
        content = _call_openrouter(messages, max_tokens=1000, temperature=0.7)
        
        # Split on '---' separator
        tweet_parts = content.split("---")
        tweets = []
        
        for part in tweet_parts:
            tweet = part.strip()
            if not tweet:
                continue
                
            # Remove tweet labels like "Tweet 1:" if present
            for i in range(1, 10):
                prefix = f"Tweet {i}:"
                if tweet.startswith(prefix):
                    tweet = tweet[len(prefix):].strip()
                    break
            
            # Clean and truncate
            tweet = _clean_spaces(tweet)
            tweet = truncate_to_280(tweet)
            tweets.append(tweet)
        
        # Ensure exactly 5 tweets
        if len(tweets) < 5:
            logger.warning(f"Generated {len(tweets)} tweets, padding to 5")
            while len(tweets) < 5:
                tweets.append("More updates as this story develops. #India #News")
        
        final_tweets = tweets[:5]
        logger.info(f"Generated 5-tweet thread successfully")
        return final_tweets
        
    except Exception as e:
        logger.error(f"Failed to generate thread: {e}")
        raise ValueError(f"Tweet generation failed: {e}") from e


def generate_short_tweets_for_supporting_stories(
    supporting_stories: list[dict],
    max_tweets: int = 2,
) -> list[str]:
    """
    Generate short standalone tweets for supporting stories using OpenRouter.
    
    Args:
        supporting_stories: List of story dicts
        max_tweets: Maximum number of tweets to generate (default 2)
        
    Returns:
        List of tweet strings (each <= 280 chars)
        
    Raises:
        ValueError: If generation fails
    """
    if not supporting_stories:
        logger.warning("No supporting stories provided")
        return []
    
    # Build story summaries
    stories_text = "\n".join([
        f"Story {i+1}: {story.get('title', '')[:80]} - {story.get('description', '')[:100]}"
        for i, story in enumerate(supporting_stories[:max_tweets])
    ])
    
    system_prompt = f"""You are a professional social media manager for India news.
Generate exactly {max_tweets} short, independent tweets for news stories.
Each tweet must be under 280 characters.
Separate tweets with a line containing only '---'.

Guidelines:
- Each tweet is standalone (not part of a thread)
- Include 1-2 relevant hashtags per tweet
- Tone: calm, analytical, neutral, India-focused
- No clickbait, no fake news, no misinformation
- Be informative and balanced"""
    
    user_prompt = f"""Generate {max_tweets} tweets for these news stories:

{stories_text}

Generate the {max_tweets} tweets now:"""
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        logger.info(f"Generating {max_tweets} short tweets for supporting stories")
        content = _call_openrouter(messages, max_tokens=600, temperature=0.7)
        
        # Split on '---'
        tweet_parts = content.split("---")
        tweets = []
        
        for part in tweet_parts:
            tweet = part.strip()
            if not tweet:
                continue
                
            # Remove tweet labels if present
            for i in range(1, 10):
                prefix = f"Tweet {i}:"
                if tweet.startswith(prefix):
                    tweet = tweet[len(prefix):].strip()
                    break
            
            # Clean and truncate
            tweet = _clean_spaces(tweet)
            tweet = truncate_to_280(tweet)
            tweets.append(tweet)
        
        # Limit to max_tweets
        final_tweets = tweets[:max_tweets]
        logger.info(f"Generated {len(final_tweets)} short tweets")
        return final_tweets
        
    except Exception as e:
        logger.error(f"Failed to generate short tweets: {e}")
        raise ValueError(f"Tweet generation failed: {e}") from e
