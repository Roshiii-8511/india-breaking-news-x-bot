# src/ai_writer.py
# Replace your current ai_writer with this file.

"""
AI tweet writer (Gemini preferred). If Gemini fails, build a deterministic
5-tweet thread directly from the article fields so posts stay relevant.
"""

import logging
import re
from typing import List, Dict, Optional
from datetime import datetime
from google import genai

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS_THREAD,
    GEMINI_MAX_TOKENS_SHORT,
)

logger = logging.getLogger(__name__)

# Try to init genai client (some SDKs use genai.Client or genai.configure)
client = None
try:
    # Preferred new pattern (if present)
    client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info("Initialized genai.Client")
except Exception:
    try:
        # Older pattern (some installs)
        genai.configure(api_key=GEMINI_API_KEY)  # may raise AttributeError if not present
        client = genai
        logger.info("Initialized genai via genai.configure")
    except Exception as e:
        logger.warning("Gemini client init failed: %s", e)
        client = None

MAX_TWEET_CHARS = 260


def _clean_spaces(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: Optional[str], limit: int = MAX_TWEET_CHARS) -> str:
    if not text:
        return ""
    t = re.sub(r"<[^>]+>", "", text).strip()
    return t if len(t) <= limit else t[: limit - 3].rstrip() + "..."


def _split_tweets_from_response(content: str, expected_count: int = 5) -> List[str]:
    if not content:
        return []
    parts = re.split(r"\n\s*---\s*\n", content.strip())
    cleaned = []
    for p in parts:
        txt = re.sub(r"^Tweet\s*\d+:\s*", "", p, flags=re.IGNORECASE)
        txt = re.sub(r"^\d+\.\s*", "", txt)
        txt = _clean_spaces(txt)
        txt = truncate(txt)
        if txt:
            cleaned.append(txt)
    while len(cleaned) < expected_count:
        cleaned.append(truncate("More updates on this story soon. #India #News"))
    return cleaned[:expected_count]


def _call_gemini_try_variants(prompt: str, max_output_tokens: int = 300, temperature: float = 0.7) -> str:
    """
    Try to call Gemini in several ways depending on installed SDK.
    If all attempts fail, raise Exception.
    """
    if client is None:
        raise RuntimeError("Gemini client not initialized")

    last_err = None

    # Attempt 1: client.models.generate_content (new SDK style)
    try:
        logger.info("Attempting client.models.generate_content(model=%s)", GEMINI_MODEL)
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        # try to extract textual output in common places:
        if hasattr(resp, "text") and resp.text:
            return resp.text
        # some responses have .output or .candidates:
        if hasattr(resp, "output") and resp.output:
            parts = []
            for part in resp.output:
                if hasattr(part, "content") and part.content:
                    parts.append(part.content)
                elif hasattr(part, "text") and part.text:
                    parts.append(part.text)
            if parts:
                return "\n".join(parts)
    except Exception as e:
        logger.warning("client.models.generate_content failed: %s", e)
        last_err = e

    # Attempt 2: client.generate_text (some older helpers)
    try:
        logger.info("Attempting client.generate_text(model=%s)", GEMINI_MODEL)
        resp = client.generate_text(
            model=GEMINI_MODEL,
            prompt=prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        if hasattr(resp, "text") and resp.text:
            return resp.text
    except Exception as e:
        logger.debug("client.generate_text failed: %s", e)
        last_err = e

    # Attempt 3: client.generate_content (alternate)
    try:
        logger.info("Attempting client.generate_content(model=%s)", GEMINI_MODEL)
        resp = client.generate_content(
            model=GEMINI_MODEL,
            prompt=prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        if hasattr(resp, "text") and resp.text:
            return resp.text
    except Exception as e:
        logger.debug("client.generate_content failed: %s", e)
        last_err = e

    # nothing worked
    logger.error("All Gemini generation attempts failed. Last error: %s", last_err)
    raise last_err or Exception("Gemini generation failed (unknown reason)")


def _build_thread_from_article(big_story: Dict) -> List[str]:
    """
    Build a deterministic 5-tweet thread using article fields when LLM is unavailable.
    This ensures the bot posts real news content even if AI fails.
    """
    title = big_story.get("title", "") or ""
    description = big_story.get("description", "") or ""
    url = big_story.get("url", "") or ""
    source = (big_story.get("source") or {}).get("name", "") or ""
    published = big_story.get("publishedAt", "") or ""

    # Format publishedAt into readable (try ISO parse)
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        published_str = dt.strftime("%d %b %Y %H:%M UTC")
    except Exception:
        published_str = published

    t1 = truncate(f"🔔 BREAKING: {title} ({source})")
    t2 = truncate(f"Summary: {description}"[:MAX_TWEET_CHARS])
    t3 = truncate(f"Source: {source} · Published: {published_str}")
    t4 = truncate(f"More: {url}") if url else truncate("More updates coming as we verify sources.")
    t5 = truncate("Follow for verified updates. Reply with trusted source links and we'll review them. #India #News")

    return [t1, t2, t3, t4, t5]


def generate_thread_for_big_story(big_story: Dict) -> List[str]:
    """
    Try Gemini generation, on fail build deterministic article thread.
    """
    logger.info("Generating 5-tweet thread for: %s...", (big_story.get("title") or "")[:100])

    # Prepare system+user style prompt (LLM-friendly)
    system_prompt = (
        "You are an assistant that writes concise, accurate X (Twitter) threads about India news.\n"
        "- Tone: neutral, factual, non-inflammatory.\n"
        "- Output exactly 5 tweets separated by a line '---'.\n"
        "- Keep each tweet <280 characters.\n"
    )
    user_prompt = (
        f"Title: {big_story.get('title','')}\n"
        f"Description: {big_story.get('description','')}\n"
        f"Source: {(big_story.get('source') or {}).get('name','')}\n"
        f"Published at: {big_story.get('publishedAt','')}\n"
        f"URL: {big_story.get('url','')}\n\n"
        "Write 5 tweets (hook, background, facts, impact, conclusion) separated by a line '---'."
    )
    prompt = system_prompt + "\n\n" + user_prompt

    # Try LLM
    try:
        text = _call_gemini_try_variants(prompt, max_output_tokens=GEMINI_MAX_TOKENS_THREAD, temperature=0.65)
        tweets = _split_tweets_from_response(text, expected_count=5)
        logger.info("Generated %d tweets via Gemini", len(tweets))
        return tweets
    except Exception as e:
        logger.error("Gemini generation failed: %s", e)
        logger.info("Falling back to deterministic article-based thread")
        return _build_thread_from_article(big_story)


def generate_short_tweets_for_supporting_stories(supporting_stories: List[Dict], max_tweets: int = 2) -> List[str]:
    if not supporting_stories or max_tweets <= 0:
        return []
    # Try LLM similarly but fall back to simple headlines
    try:
        block = []
        for i, s in enumerate(supporting_stories[:max_tweets], start=1):
            block.append(f"{i}) {s.get('title','')}\n{s.get('description','')}\nSource:{(s.get('source') or {}).get('name','')}")
        prompt = "Write one short tweet for each story below, 1-2 hashtags, neutral tone, separated with '---'.\n\n" + "\n\n".join(block)
        text = _call_gemini_try_variants(prompt, max_output_tokens=GEMINI_MAX_TOKENS_SHORT, temperature=0.6)
        tweets = _split_tweets_from_response(text, expected_count=max_tweets)
        return tweets
    except Exception as e:
        logger.error("Gemini short tweets failed: %s", e)
        # Fallback: headlines only
        out = []
        for s in supporting_stories[:max_tweets]:
            out.append(truncate(f"{s.get('title','')} — {(s.get('source') or {}).get('name','')}"))
        return out
