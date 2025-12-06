"""
News API client for fetching India news.

This module handles:
- Fetching India-related news from NewsAPI (/v2/everything)
- Filtering and sorting by date
- Selecting 1 big story + 2-3 supporting stories
"""

import logging
from datetime import datetime
from typing import List, Dict, Tuple

import requests

from src.config import NEWS_API_KEY, NEWS_API_URL, NEWS_PAGE_SIZE

logger = logging.getLogger(__name__)


def fetch_top_headlines() -> List[Dict]:
    """
    Fetch India-related news from News API using the /v2/everything endpoint.

    We no longer rely on `top-headlines?country=in` because that can return
    0 results on some free-tier setups. Instead we use a keyword search:

        q = "India"
        language = "en"
        sortBy = "publishedAt"

    Args:
        None

    Returns:
        List of article dicts, each with:
            - title: str
            - description: str
            - url: str
            - source: dict with 'name' key
            - publishedAt: str (ISO datetime)

    Raises:
        ValueError: If API request fails or NewsAPI returns an error.
    """
    try:
        params = {
            # Keyword-based search focused on India
            "q": "India",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": NEWS_PAGE_SIZE,
            "apiKey": NEWS_API_KEY,
        }

        logger.info(f"Fetching India news from {NEWS_API_URL}...")
        response = requests.get(NEWS_API_URL, params=params, timeout=30)

        if response.status_code != 200:
            logger.error(
                "News API returned status %s: %s",
                response.status_code,
                response.text,
            )
            raise ValueError(
                f"Failed to fetch news. Status: {response.status_code}. "
                f"Response: {response.text}"
            )

        data = response.json()

        # NewsAPI sometimes returns {"status": "error", "code": "...", "message": "..."}
        status = data.get("status")
        if status != "ok":
            code = data.get("code")
            message = data.get("message")
            logger.error(
                "News API error. status=%s, code=%s, message=%s",
                status,
                code,
                message,
            )
            raise ValueError(f"News API error: {code} - {message}")

        articles = data.get("articles", [])
        logger.info("Retrieved %d articles from News API", len(articles))

        simplified: List[Dict] = []
        for article in articles:
            simplified.append(
                {
                    "title": article.get("title", "No title"),
                    "description": article.get("description", "") or "",
                    "url": article.get("url", ""),
                    "source": article.get("source", {}) or {},
                    "publishedAt": article.get("publishedAt", "") or "",
                }
            )

        return simplified

    except requests.RequestException as e:
        logger.error("Network error fetching news: %s", e)
        raise ValueError(f"Network error fetching news: {e}") from e
    except Exception as e:
        logger.error("Unexpected error fetching news: %s", e)
        raise


def select_big_and_supporting_stories(
    articles: List[Dict],
) -> Tuple[Dict, List[Dict]]:
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
        ValueError: If list is empty.
    """
    if not articles:
        raise ValueError("No articles available to select stories from")

    try:
        def _parse_ts(ts: str) -> str:
            # publishedAt is ISO like "2025-12-05T15:37:33Z"
            # Lexicographic sort on ISO strings works fine for our case,
            # but we normalize missing/empty to "".
            return ts or ""

        # Sort by publishedAt descending (most recent first)
        sorted_articles = sorted(
            articles,
            key=lambda x: _parse_ts(x.get("publishedAt", "")),
            reverse=True,
        )

        big_story = sorted_articles[0]
        logger.info("Selected big story: %s...", big_story.get("title", "")[:80])

        # Select 2-3 supporting stories from different sources
        supporting_stories: List[Dict] = []
        seen_sources = {big_story.get("source", {}).get("name", "")}

        for article in sorted_articles[1:]:
            if len(supporting_stories) >= 3:
                break

            title = article.get("title") or ""
            desc = article.get("description") or ""
            if not title.strip() or not desc.strip():
                continue

            source_name = article.get("source", {}).get("name", "")

            # Prefer different sources, but allow same source if we still need more
            if source_name and source_name not in seen_sources:
                supporting_stories.append(article)
                seen_sources.add(source_name)
            elif len(supporting_stories) < 2:
                supporting_stories.append(article)

        if not supporting_stories:
            # Fallback: just take the next 2 most recent
            supporting_stories = sorted_articles[1:3]

        logger.info("Selected %d supporting stories", len(supporting_stories))

        return big_story, supporting_stories

    except Exception as e:
        logger.error("Error selecting stories: %s", e)
        raise
