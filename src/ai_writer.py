"""AI-powered tweet generation using OpenAI.

This module uses OpenAI's chat completion API to generate:
- 5-tweet detailed threads for big stories
- 1-2 short standalone tweets for supporting stories
"""

import logging
from openai import OpenAI

from src.config import OPENAI_API_KEY, AI_MODEL


logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    """
    Initialize and return OpenAI client.
    
    Returns:
        Initialized OpenAI client
    """
    return OpenAI(api_key=OPENAI_API_KEY)


def truncate_to_280(text: str) -> str:
    """
    Truncate text to 280 characters for X/Twitter compliance.
    
    Args:
        text: Input text
        
    Returns:
        Text truncated to max 280 chars, with "..." if needed
    """
    if len(text) <= 280:
        return text
    return text[:277] + "..."


def generate_thread_for_big_story(big_story: dict) -> list[str]:
    """
    Generate a 5-tweet thread for the big story using AI.
    
    Args:
        big_story: Dict with title, description, source, url
        
    Returns:
        List of exactly 5 tweet strings (each <= 280 chars)
        
    Raises:
        ValueError: If AI response is malformed or generation fails
    """
    title = big_story.get("title", "")
    description = big_story.get("description", "")
    source = big_story.get("source", {}).get("name", "News")
    url = big_story.get("url", "")
    
    prompt = f"""You are a professional social media manager for India news.
    
Generate a 5-tweet thread about this India news story. Each tweet must:
- Be exactly 5 tweets separated by a line with just '---'
- Tweet 1: Breaking news hook with emojis and relevant hashtags
- Tweet 2: Background and why this matters now
- Tweet 3: Key details and facts
- Tweet 4: Impact on Indians
- Tweet 5: Balanced conclusion and open question
- Max 280 characters per tweet
- Tone: Diplomatic, neutral, analytical, India-focused
- No hate speech, no misinformation, no personal attacks

Story:
Title: {title}
Description: {description}
Source: {source}
URL: {url}

Generate the 5-tweet thread now:"""
    
    try:
        client = get_openai_client()
        logger.info(f"Generating 5-tweet thread for: {title[:50]}...")
        
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a skilled social media manager."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Split by '---' separator
        tweets = content.split("---")
        tweets = [t.strip() for t in tweets if t.strip()]
        
        # Clean up tweet labels if present (e.g., "Tweet 1:", "Tweet 1")
        cleaned_tweets = []
        for tweet in tweets:
            # Remove "Tweet X:" prefix if present
            for i in range(1, 10):
                if tweet.startswith(f"Tweet {i}:"):
                    tweet = tweet[len(f"Tweet {i}:"):].strip()
                    break
            # Truncate to 280
            tweet = truncate_to_280(tweet)
            cleaned_tweets.append(tweet)
        
        if len(cleaned_tweets) < 5:
            logger.warning(
                f"AI returned {len(cleaned_tweets)} tweets, expected 5. Padding with empty tweets."
            )
            while len(cleaned_tweets) < 5:
                cleaned_tweets.append("")
        
        final_tweets = cleaned_tweets[:5]
        logger.info(f"Generated 5-tweet thread successfully")
        return final_tweets
        
    except Exception as e:
        logger.error(f"Failed to generate thread: {e}")
        raise ValueError(f"AI generation failed: {e}") from e


def generate_short_tweets_for_supporting_stories(
    supporting_stories: list[dict],
    max_tweets: int = 2,
) -> list[str]:
    """
    Generate short standalone tweets for supporting stories.
    
    Args:
        supporting_stories: List of story dicts
        max_tweets: Maximum number of tweets to generate (default 2)
        
    Returns:
        List of tweet strings (each <= 280 chars)
        
    Raises:
        ValueError: If AI generation fails
    """
    if not supporting_stories:
        logger.warning("No supporting stories provided")
        return []
    
    stories_text = "\n".join([
        f"- {story.get('title', '')}: {story.get('description', '')[:100]}"
        for story in supporting_stories[:max_tweets]
    ])
    
    prompt = f"""You are a professional social media manager for India news.
    
Generate {max_tweets} short, standalone tweets for these India news stories. Each tweet must:
- Be independent (not part of a thread)
- Max 280 characters
- Include 1-2 relevant hashtags
- Be diplomatic, analytical, India-focused
- No hate speech, no misinformation
- Separate each tweet with a line containing only '---'

Stories:
{stories_text}

Generate {max_tweets} tweets now:"""
    
    try:
        client = get_openai_client()
        logger.info(f"Generating {max_tweets} short tweets for supporting stories")
        
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a skilled social media manager."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Split by '---'
        tweets = content.split("---")
        tweets = [truncate_to_280(t.strip()) for t in tweets if t.strip()]
        
        # Limit to max_tweets
        final_tweets = tweets[:max_tweets]
        logger.info(f"Generated {len(final_tweets)} short tweets")
        return final_tweets
        
    except Exception as e:
        logger.error(f"Failed to generate short tweets: {e}")
        raise ValueError(f"AI generation failed: {e}") from e
