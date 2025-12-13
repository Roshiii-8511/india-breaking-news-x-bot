"""
News API client for fetching India-focused breaking news.
"""

import logging
from datetime import datetime, timedelta, timezone
import requests

from src.config import (
    NEWS_API_KEY,
    NEWS_API_URL,
    NEWS_COUNTRY,
    NEWS_PAGE_SIZE,
    NEWS_MAX_AGE_HOURS,
)

logger = logging.getLogger(__name__)


INDIA_KEYWORDS = [
    "india", "indian", "delhi", "mumbai", "bihar", "uttar pradesh",
    "supreme court", "parliament", "government of india",
    "modi", "cabinet", "election commission", "rbi",
]


def _is_recent(published_at: str) -> bool:
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "")).replace(
            tzinfo=timezone.utc
        )
        return dt >= datetime.now(timezone.utc) - timedelta(hours=NEWS_MAX_AGE_HOURS)
    except Exception:
        return False


def _is_india_relevant(article: dict) -> bool:
    text = f"{article.get('title', '')} {article.get('description', '')}".lower()
    return any(k in text for k in INDIA_KEYWORDS)


def fetch_top_headlines() -> list[dict]:
    params = {
        "country": NEWS_COUNTRY,
        "pageSize": NEWS_PAGE_SIZE,
        "apiKey": NEWS_API_KEY,
    }

    logger.info(f"Fetching India news from {NEWS_API_URL}...")
    response = requests.get(NEWS_API_URL, params=params, timeout=15)

    if response.status_code != 200:
        raise ValueError(
            f"News API error {response.status_code}: {response.text}"
        )

    data = response.json()
    articles = data.get("articles", [])

    logger.info(f"Retrieved {len(articles)} raw articles from News API")

    cleaned = []
    for a in articles:
        article = {
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "url": a.get("url", ""),
            "source": a.get("source", {}),
            "publishedAt": a.get("publishedAt", ""),
        }

        if not article["title"]:
            continue
        if not _is_recent(article["publishedAt"]):
            continue
        if not _is_india_relevant(article):
            continue

        cleaned.append(article)

    logger.info(f"India + fresh articles after filter: {len(cleaned)}")

    if not cleaned:
        raise ValueError("No recent India-relevant articles found")

    return cleaned


def select_big_and_supporting_stories(
    articles: list[dict],
) -> tuple[dict, list[dict]]:

    articles = sorted(
        articles,
        key=lambda x: x.get("publishedAt", ""),
        reverse=True,
    )

    big_story = articles[0]
    supporting = articles[1:3]

    logger.info(f"Selected big story: {big_story['title'][:80]}...")
    logger.info(f"Selected {len(supporting)} supporting stories")

    return big_story, supporting
