"""
AI Tweet writer using Gemini 2.5 Flash via REST API.
No SDK required → 100% stable in GitHub Actions.
"""

import logging
import re
import requests
from typing import List, Dict, Optional
from datetime import datetime

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS_THREAD,
    GEMINI_MAX_TOKENS_SHORT,
)

logger = logging.getLogger(__name__)

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

MAX_TWEET_CHARS = 260


def _clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def truncate(text: Optional[str], limit: int = MAX_TWEET_CHARS) -> str:
    if not text:
        return ""
    t = re.sub(r"<[^>]+>", "", text).strip()
    return t if len(t) <= limit else t[: limit - 3] + "..."


def _split_tweets(content: str, expected_count: int) -> List[str]:
    parts = re.split(r"\n\s*---\s*\n", content.strip())
    out = []
    for p in parts:
        txt = re.sub(r"^Tweet\s*\d+:\s*", "", p, flags=re.IGNORECASE)
        txt = _clean_spaces(txt)
        txt = truncate(txt)
        if txt:
            out.append(txt)
    while len(out) < expected_count:
        out.append(truncate("More updates soon. #India #News"))
    return out[:expected_count]


# === NEW: REST API CALL (WORKS 100% WITH GEMINI 2.5 FLASH) ==================

def call_gemini(prompt: str, max_tokens: int) -> str:
    """
    Direct REST API call to Gemini 2.5 Flash.
    Never depends on buggy Python SDKs.
    """
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.7
        }
    }

    r = requests.post(GEMINI_URL, json=payload, timeout=20)

    if r.status_code != 200:
        raise RuntimeError(f"Gemini API error {r.status_code}: {r.text}")

    data = r.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        raise RuntimeError(f"Unexpected Gemini response: {data}")


# === FALLBACK THREAD (if Gemini fails) =======================================

def fallback_thread(article: Dict) -> List[str]:
    title = article.get("title", "")
    desc = article.get("description", "")
    url = article.get("url", "")
    src = (article.get("source") or {}).get("name", "")
    pub = article.get("publishedAt", "")

    try:
        dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
        pub = dt.strftime("%d %b %Y %H:%M UTC")
    except:
        pass

    return [
        truncate(f"🔔 BREAKING: {title} ({src})"),
        truncate(f"Summary: {desc}"),
        truncate(f"Source: {src} · Published: {pub}"),
        truncate(f"More: {url}" if url else "More updates soon."),
        truncate("Follow for verified updates. #India #News"),
    ]


# === MAIN BIG STORY THREAD =====================================================

def generate_thread_for_big_story(article: Dict) -> List[str]:
    logger.info("Generating thread via Gemini REST API…")

    system = (
        "You are an assistant writing factual India-focused X threads.\n"
        "- Keep tweets <280 chars.\n"
        "- Output exactly 5 tweets separated by '---'.\n"
        "- Neutral, factual, verified tone.\n"
    )

    user = (
        f"Title: {article.get('title','')}\n"
        f"Description: {article.get('description','')}\n"
        f"Source: {(article.get('source') or {}).get('name','')}\n"
        f"Published: {article.get('publishedAt','')}\n"
        f"URL: {article.get('url','')}\n\n"
        "Write 5 tweets separated by '---'."
    )

    prompt = system + "\n\n" + user

    try:
        raw = call_gemini(prompt, GEMINI_MAX_TOKENS_THREAD)
        tweets = _split_tweets(raw, 5)
        logger.info("Gemini thread generated.")
        return tweets

    except Exception as e:
        logger.error("Gemini failed → using fallback. %s", e)
        return fallback_thread(article)


# === SUPPORTING STORIES ========================================================

def generate_short_tweets_for_supporting_stories(stories: List[Dict], max_tweets: int = 2) -> List[str]:
    if not stories:
        return []

    story_block = ""
    for s in stories[:max_tweets]:
        story_block += f"- {s.get('title','')} | {s.get('description','')}\n"

    prompt = (
        "Write one short tweet per story below. Neutral tone. < 280 chars. "
        "Separate tweets with '---'.\n\n" + story_block
    )

    try:
        raw = call_gemini(prompt, GEMINI_MAX_TOKENS_SHORT)
        return _split_tweets(raw, max_tweets)
    except:
        # fallback: raw headlines
        return [truncate(s.get("title", "")) for s in stories[:max_tweets]]
