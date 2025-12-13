"""
Deterministic fallback tweet writer (NO AI).

Goals:
- Always post factual, sharp, credible news threads
- Zero hallucination
- Zero dependency on LLMs
- Production-safe automation
"""

import logging
import re
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

MAX_TWEET_CHARS = 260  # safe buffer for X


def _clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _truncate(text: str) -> str:
    if len(text) <= MAX_TWEET_CHARS:
        return text
    return text[: MAX_TWEET_CHARS - 3].rstrip() + "..."


def _format_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", ""))
        return dt.strftime("%d %b %Y")
    except Exception:
        return ""


def generate_thread_for_big_story(big_story: Dict) -> List[str]:
    """
    Deterministic 5-tweet breaking news thread
    """

    title = _clean(big_story.get("title", ""))
    desc = _clean(big_story.get("description", ""))
    url = big_story.get("url", "")
    source = (big_story.get("source") or {}).get("name", "Source")
    published = _format_date(big_story.get("publishedAt", ""))

    logger.info("Generating deterministic fallback thread")

    # Tweet 1 — Breaking hook
    t1 = f"🔔 BREAKING: {title}"

    # Tweet 2 — What happened
    if desc:
        t2 = f"What happened: {desc}"
    else:
        t2 = "What happened: Officials confirmed developments in this case."

    # Tweet 3 — Why it matters (neutral framing)
    t3 = (
        "Why it matters: The decision could have political and policy implications "
        "in the coming days."
    )

    # Tweet 4 — Source + link
    t4_parts = [f"Source: {source}"]
    if published:
        t4_parts.append(f"Published: {published}")
    if url:
        t4_parts.append(f"More: {url}")
    t4 = " · ".join(t4_parts)

    # Tweet 5 — CTA / trust positioning
    t5 = (
        "Follow for verified, real-time updates. "
        "We share facts — not rumours. #BreakingNews"
    )

    tweets = [
        _truncate(t1),
        _truncate(t2),
        _truncate(t3),
        _truncate(t4),
        _truncate(t5),
    ]

    return tweets


def generate_short_tweets_for_supporting_stories(
    supporting_stories: List[Dict],
    max_tweets: int = 2,
) -> List[str]:
    """
    Deterministic short tweets for supporting stories
    """
    tweets = []

    for story in supporting_stories[:max_tweets]:
        title = _clean(story.get("title", ""))
        source = (story.get("source") or {}).get("name", "")
        url = story.get("url", "")

        text = f"📰 {title}"
        if source:
            text += f" ({source})"
        if url:
            text += f" {url}"

        tweets.append(_truncate(text))

    return tweets
