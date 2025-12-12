"""
AI tweet writer using Gemini 2.5 Flash.

Responsibilities:
- Call Gemini via google-genai SDK
- Generate:
    - 5-tweet thread for a big story
    - 1–2 short standalone tweets for supporting stories
- Enforce conservative character limits per tweet
"""

import logging
import re
from typing import List, Dict

from google import genai
from src.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

# Configure Gemini API
client = genai.Client(api_key=GEMINI_API_KEY)
model = client.models.generate_content

MAX_TWEET_CHARS = 130


# ------------------------------------------------------------
# Helper: Clean & truncate
# ------------------------------------------------------------
def truncate_to_280(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", "", text).strip()
    if len(text) <= MAX_TWEET_CHARS:
        return text

    return text[: MAX_TWEET_CHARS - 3].rstrip() + "..."


def _clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


# ------------------------------------------------------------
# Gemini wrapper
# ------------------------------------------------------------
def _call_gemini(messages: List[Dict], max_tokens: int = 300, temperature: float = 0.7) -> str:
    """
    Convert OpenAI-style messages into a flat prompt for Gemini 2.5 Flash.
    """
    logger.info("Calling Gemini with model %s", GEMINI_MODEL)

    parts = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")

        if role == "system":
            parts.append(f"System:\n{content}\n")
        elif role == "user":
            parts.append(f"User:\n{content}\n")
        elif role == "assistant":
            parts.append(f"Assistant:\n{content}\n")

    full_prompt = "\n".join(parts)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        return response.text
    except Exception as e:
        logger.error("Gemini API call failed: %s", e)
        raise


# ------------------------------------------------------------
# Split tweets from model output
# ------------------------------------------------------------
def _split_tweets_from_response(content: str, expected_count: int) -> List[str]:
    if not content:
        return []

    parts = re.split(r"\n\s*---\s*\n", content.strip())
    cleaned = []

    for part in parts:
        txt = part.strip()
        txt = re.sub(r"^Tweet\s*\d+:?\s*", "", txt, flags=re.IGNORECASE)
        txt = re.sub(r"^\d+\.\s*", "", txt)

        txt = truncate_to_280(_clean_spaces(txt))
        if txt:
            cleaned.append(txt)

    while len(cleaned) < expected_count:
        cleaned.append("More updates soon. #India #News")

    return cleaned[:expected_count]


# ------------------------------------------------------------
# Big story thread (5 tweets)
# ------------------------------------------------------------
def generate_thread_for_big_story(big_story: Dict) -> List[str]:
    title = big_story.get("title", "")
    description = big_story.get("description", "")
    url = big_story.get("url", "")
    source_name = (big_story.get("source") or {}).get("name", "")
    published_at = big_story.get("publishedAt", "")

    logger.info("Generating 5-tweet thread for: %s", title[:80])

    system_prompt = (
        "You are an assistant that writes India-focused X (Twitter) threads.\n"
        "Rules:\n"
        "- Neutral, factual, India-focused tone.\n"
        "- Under 280 characters per tweet.\n"
        "- Output exactly 5 tweets separated using:\n"
        "---\n"
        "- Do NOT number tweets.\n"
    )

    user_prompt = (
        "Create a 5-tweet thread about this India news.\n\n"
        f"Title: {title}\n"
        f"Description: {description}\n"
        f"Source: {source_name}\n"
        f"Published at: {published_at}\n"
        f"URL (context only): {url}\n\n"
        "Structure:\n"
        "Tweet 1: Breaking-style hook + hashtags\n"
        "Tweet 2: Background\n"
        "Tweet 3: Key facts\n"
        "Tweet 4: Impact\n"
        "Tweet 5: Conclusion + question\n\n"
        "Separate tweets with:\n"
        "---"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        content = _call_gemini(messages, max_tokens=400)
    except Exception as e:
        raise ValueError(f"Tweet generation failed: {e}") from e

    return _split_tweets_from_response(content, 5)


# ------------------------------------------------------------
# Supporting story tweets
# ------------------------------------------------------------
def generate_short_tweets_for_supporting_stories(stories: List[Dict], max_tweets: int = 2) -> List[str]:
    if not stories:
        return []

    formatted = []
    for i, s in enumerate(stories[:max_tweets], start=1):
        formatted.append(
            f"{i}) {s.get('title','')}\nDescription: {s.get('description','')}\nSource: {(s.get('source') or {}).get('name','')}"
        )

    block = "\n\n".join(formatted)

    system_prompt = (
        "You are an assistant that writes short India-focused tweets.\n"
        "Each < 280 characters.\n"
        "Use 1–2 relevant hashtags.\n"
        "Separate tweets with:\n"
        "---"
    )

    user_prompt = (
        "Write tweets for these news stories:\n\n"
        f"{block}\n\n"
        "Output up to {max_tweets} tweets, separated with:\n"
        "---"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        content = _call_gemini(messages, max_tokens=300)
    except Exception:
        return []

    return _split_tweets_from_response(content, max_tweets)
