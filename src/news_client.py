"""
News API client with SAFE fallback logic.
Bot will NEVER die due to empty news.
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
    "supreme court", "parliament", "government", "rbi",
    "modi", "cabinet", "election", "court",
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
    text = f"{article.get('title','')} {article.get('description','')}".lower()
    return any(k in text for k in INDIA_KEYWORDS)


def _fetch(params: dict) -> list[dict]:
    r = requests.get(NEWS_API_URL, params=params, timeout=15)
    if r.status_code != 200:
        return []
    return r.json().get("articles", [])


def fetch_top_headlines() -> list[dict]:
    logger.info(f"Fetching India news from {NEWS_API_URL}...")

    # 1️⃣ Primary: country=in
    articles = _fetch({
        "country": NEWS_COUNTRY,
        "pageSize": NEWS_PAGE_SIZE,
        "apiKey": NEWS_API_KEY,
    })

    logger.info(f"Retrieved {len(articles)} raw articles from News API")

    # 2️⃣ Fallback: keyword-based India query
    if not articles:
        logger.warning("country=in returned 0 articles, using fallback query")
        articles = _fetch({
            "q": "India",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": NEWS_PAGE_SIZE,
            "apiKey": NEWS_API_KEY,
        })

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

        # 🔹 soft India relevance (not strict)
        if not _is_india_relevant(article):
            continue

        cleaned.append(article)

    logger.info(f"India + fresh articles after filter: {len(cleaned)}")

    # 3️⃣ LAST RESORT: allow ANY fresh article (bot must run)
    if not cleaned and articles:
        logger.warning("No India-filtered articles, using fresh global fallback")
        for a in articles:
            if _is_recent(a.get("publishedAt", "")):
                cleaned.append({
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "url": a.get("url", ""),
                    "source": a.get("source", {}),
                    "publishedAt": a.get("publishedAt", ""),
                })

    if not cleaned:
        raise ValueError("News API returned no usable articles")

    return cleaned


def select_big_and_supporting_stories(articles: list[dict]):
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
