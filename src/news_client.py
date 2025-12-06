"""News API client for fetching India news headlines.

This module handles:
- Fetching top headlines from NewsAPI
- Filtering and sorting by date
- Selecting 1 big story + 2-3 supporting stories
"""

import logging
from datetime import datetime
import requests

from src.config import NEWS_API_KEY, NEWS_API_URL, NEWS_COUNTRY, NEWS_PAGE_SIZE


logger = logging.getLogger(__name__)


def fetch_top_headlines() -> list[dict]:
    """
    Fetch top headlines from News API for India.
    
    Args:
        None
        
    Returns:
        List of article dicts, each with:
            - title: str
            - description: str
            - url: str
            - source: dict with 'name' key
            - publishedAt: str (ISO format datetime)
            
    Raises:
        ValueError: If API request fails
    """
    try:
        params = {
            "country": NEWS_COUNTRY,
            "pageSize": NEWS_PAGE_SIZE,
            "apiKey": NEWS_API_KEY,
        }
        
        logger.info(f"Fetching top headlines from {NEWS_API_URL}...")
        response = requests.get(NEWS_API_URL, params=params)
        
        if response.status_code != 200:
            logger.error(
                f"News API returned status {response.status_code}: {response.text}"
            )
            raise ValueError(
                f"Failed to fetch news. Status: {response.status_code}. "
                f"Response: {response.text}"
            )
        
        data = response.json()
        articles = data.get("articles", [])
        
        logger.info(f"Retrieved {len(articles)} articles from News API")
        
        # Simplify and clean articles
        simplified = []
        for article in articles:
            simplified.append({
                "title": article.get("title", "No title"),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "source": article.get("source", {}),
                "publishedAt": article.get("publishedAt", ""),
            })
        
        return simplified
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching news: {e}")
        raise ValueError(f"Network error fetching news: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error fetching news: {e}")
        raise


def select_big_and_supporting_stories(
    articles: list[dict],
) -> tuple[dict, list[dict]]:
    """
    Select 1 big story and 2-3 supporting stories from article list.
    
    Strategy:
        - Sort by publishedAt (most recent first)
        - Take first as big story
        - From remaining, pick 2-3 from different sources if possible
    
    Args:
        articles: List of article dicts from fetch_top_headlines
        
    Returns:
        Tuple of (big_story_dict, supporting_stories_list)
        
    Raises:
        ValueError: If list is empty or insufficient articles
    """
    if not articles:
        raise ValueError("No articles available to select stories from")
    
    try:
        # Sort by publishedAt descending (most recent first)
        sorted_articles = sorted(
            articles,
            key=lambda x: x.get("publishedAt", ""),
            reverse=True,
        )
        
        big_story = sorted_articles[0]
        logger.info(f"Selected big story: {big_story['title'][:50]}...")
        
        # Select 2-3 supporting stories from different sources
        supporting_stories = []
        seen_sources = {big_story["source"].get("name", "")}
        
        for article in sorted_articles[1:]:
            if len(supporting_stories) >= 3:
                break
            
            source_name = article["source"].get("name", "")
            
            # Skip if no title or description
            if not article.get("title") or not article.get("description"):
                continue
            
            # Prefer different sources, but allow same source if needed
            if source_name and source_name not in seen_sources:
                supporting_stories.append(article)
                seen_sources.add(source_name)
            elif len(supporting_stories) < 2:
                # If we need more stories, accept from any source
                supporting_stories.append(article)
        
        if not supporting_stories:
            # If no supporting stories found, just take next 2
            supporting_stories = sorted_articles[1:3]
        
        logger.info(f"Selected {len(supporting_stories)} supporting stories")
        
        return (big_story, supporting_stories)
        
    except Exception as e:
        logger.error(f"Error selecting stories: {e}")
        raise
