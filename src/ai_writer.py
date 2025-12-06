"""
AI tweet writer using OpenRouter free-tier models.

Responsibilities:
- Call OpenRouter chat completions API
- Generate:
    - 5-tweet thread for a big story
    - 1–2 short standalone tweets for supporting stories
- Enforce 280 character limit per tweet
"""

import logging
import random
import re
from typing import List, Dict

import requests

from src.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_API_URL,
    OPENROUTER_MODEL,
)

logger = logging.getLogger(__name__)

# You can tweak / extend this list based on the free models visible in your
# OpenRouter dashboard.
FALLBACK_MODELS: List[str] = [
    OPENROUTER_MODEL,
    "meta-llama/llama-3.1-8b-instruct:free",
    "qwen/qwen2.5-7b-instruct:free",
]


def truncate_to_280(text: str) -> str:
    """Ensure tweet text is within 280 characters."""
    if text is None:
        return ""
    text = text.strip()
    if len(text) <= 280:
        return text
    return text[:277].rstrip() + "..."


def _clean_spaces(text: str) -> str:
    """Normalize whitespace in tweet text."""
    if not text:
        return ""
    # Collapse multiple spaces and strip
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _call_openrouter(
    messages: List[Dict],
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """
    Call OpenRouter chat completions endpoint.

    We try primary + fallback free models sequentially:
      - If a model returns 429 rate-limit, we log and try the next model.
      - If a model returns any other error, we raise.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional, nice to have:
        "HTTP-Referer": "https://github.com/Roshiii-8511/india-breaking-news-x-bot",
        "X-Title": "India Breaking News X Bot",
    }

    last_error = None

    for model in FALLBACK_MODELS:
        logger.info("Calling OpenRouter with model %s", model)

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            resp = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=30,
            )
        except requests.RequestException as e:
            logger.error("Network error calling OpenRouter: %s", e)
            last_error = e
            continue

        if resp.status_code == 200:
            data = resp.json()
            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                logger.error("Unexpected OpenRouter response format: %s", data)
                last_error = e
                continue
            return content

        # Non-200
        text = resp.text
        logger.error("OpenRouter API error %s: %s", resp.status_code, text)

        # If it's rate-limited for this free model, try the next model.
        if resp.status_code == 429 and "rate-limited" in text.lower():
            logger.warning(
                "Model %s is rate-limited upstream. Trying next fallback model...",
                model,
            )
            last_error = Exception(
                f"Model {model} rate-limited: {text}"
            )
            continue

        # For other errors (400, 401, etc.), don't waste time on this model.
        last_error = Exception(
            f"OpenRouter API failed with status {resp.status_code}: {text}"
        )
        # Still try next fallback model:
        continue

    # If we exhausted all models and still failed:
    if last_error is None:
        last_error = Exception("Unknown error calling OpenRouter with all models.")
    raise last_error


def _split_tweets_from_response(content: str, expected_count: int = 5) -> List[str]:
    """
    Split LLM response into individual tweets using '---' as delimiter.
    Clean each tweet and enforce 280 chars.
    """
    if not content:
        return []

    # Split on lines that contain only --- or surrounded by whitespace
    parts = re.split(r"\n\s*---\s*\n", content.strip())
    cleaned: List[str] = []

    for part in parts:
        txt = part.strip()

        # Remove "Tweet 1:", "1.", etc. if model added:
        txt = re.sub(r"^Tweet\s*\d+:\s*", "", txt, flags=re.IGNORECASE)
        txt = re.sub(r"^\d+\.\s*", "", txt)

        txt = _clean_spaces(txt)
        txt = truncate_to_280(txt)

        if txt:
            cleaned.append(txt)

    # Ensure at least expected_count items (pad with generic tweets if needed)
    while len(cleaned) < expected_count:
        cleaned.append(
            truncate_to_280(
                "More updates on this story soon. #India #News"
            )
        )

    # If too many, keep only first expected_count
    return cleaned[:expected_count]


def generate_thread_for_big_story(big_story: Dict) -> List[str]:
    """
    Generate a 5-tweet thread for the big story using OpenRouter.

    big_story dict fields:
      - title
      - description
      - url
      - source (dict with 'name')
      - publishedAt
    """
    title = big_story.get("title", "") or ""
    description = big_story.get("description", "") or ""
    url = big_story.get("url", "") or ""
    source_name = (big_story.get("source") or {}).get("name", "") or ""
    published_at = big_story.get("publishedAt", "") or ""

    logger.info("Generating 5-tweet thread for: %s...", title[:80])

    system_prompt = (
        "You are an assistant that writes India-focused X (Twitter) threads.\n"
        "Rules:\n"
        "- Tone: calm, neutral, diplomatic, analytical.\n"
        "- No hate speech, no personal attacks, no conspiracy, no unverified claims.\n"
        "- Write in simple, clear English with occasional emojis.\n"
        "- Each tweet must be under 280 characters.\n"
        "- Output exactly 5 tweets, separated by a line containing only '---'.\n"
        "- Do NOT number the tweets explicitly.\n"
        "- Use 1–2 relevant hashtags per tweet.\n"
    )

    user_prompt = (
        "Create a 5-tweet thread about the following India-related news story.\n\n"
        f"Title: {title}\n"
        f"Description: {description}\n"
        f"Source: {source_name}\n"
        f"Published at: {published_at}\n"
        f"URL (for context only, do not copy link): {url}\n\n"
        "Structure:\n"
        "Tweet 1: Big BREAKING style hook with emoji + 1–2 hashtags.\n"
        "Tweet 2: Background / why this is happening now.\n"
        "Tweet 3: Key facts or changes (can be bullet-like text).\n"
        "Tweet 4: Impact on India / economy / daily life / policy.\n"
        "Tweet 5: Balanced conclusion + question to the audience.\n\n"
        "Separate the tweets using a line that contains only:\n"
        "---"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        content = _call_openrouter(messages, max_tokens=800, temperature=0.7)
    except Exception as e:
        logger.error("Failed to generate thread: %s", e)
        raise ValueError(f"Tweet generation failed: {e}") from e

    tweets = _split_tweets_from_response(content, expected_count=5)
    logger.info("Generated 5-tweet thread.")
    return tweets


def generate_short_tweets_for_supporting_stories(
    supporting_stories: List[Dict],
    max_tweets: int = 2,
) -> List[str]:
    """
    Generate up to `max_tweets` standalone tweets about supporting stories.

    Each tweet:
      - Focuses on a different story
      - < 280 chars
      - Has 1–2 relevant hashtags
      - Neutral, diplomatic, India-focused tone
    """
    if not supporting_stories or max_tweets <= 0:
        return []

    stories_for_prompt = supporting_stories[:max_tweets]

    formatted_stories = []
    for idx, story in enumerate(stories_for_prompt, start=1):
        t = story.get("title", "") or ""
        d = story.get("description", "") or ""
        s = (story.get("source") or {}).get("name", "") or ""
        formatted_stories.append(
            f"{idx}) Title: {t}\nDescription: {d}\nSource: {s}"
        )

    stories_block = "\n\n".join(formatted_stories)

    system_prompt = (
        "You are an assistant that writes India-focused X (Twitter) posts.\n"
        "Rules:\n"
        "- Tone: calm, neutral, analytical, diplomatic.\n"
        "- No hate speech or personal attacks.\n"
        "- Each tweet must be under 280 characters.\n"
        "- Each tweet should mention the core point of the story.\n"
        "- Use 1–2 relevant hashtags like #India, #Economy, #Policy, etc.\n"
        "- Output one tweet per story, separated by a line containing only '---'.\n"
        "- Do NOT number the tweets."
    )

    user_prompt = (
        "Write short standalone tweets for the following India-related news stories.\n\n"
        f"{stories_block}\n\n"
        "Output:\n"
        f"- {max_tweets} tweets maximum (one per story).\n"
        "- Separate tweets with a line that contains only:\n"
        "---"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        content = _call_openrouter(messages, max_tokens=600, temperature=0.7)
    except Exception as e:
        logger.error("Failed to generate short tweets: %s", e)
        # For supporting tweets, we can fail softly and just return empty list
        return []

    tweets = _split_tweets_from_response(content, expected_count=max_tweets)
    logger.info("Generated %d short supporting tweets.", len(tweets))
    return tweets
