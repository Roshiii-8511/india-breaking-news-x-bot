"""
AI tweet writer using Google Gemini (google-genai SDK).

Responsibilities:
- Call Gemini (google-genai) generate_content API
- Generate:
    - 5-tweet thread for a big story
    - 1–2 short standalone tweets for supporting stories
- Enforce conservative character limit per tweet
- Provide safe fallback thread if model fails
"""
import logging
import re
from typing import List, Dict

from google import genai
from google.genai import errors as genai_errors

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS_THREAD,
    GEMINI_MAX_TOKENS_SHORT,
)

logger = logging.getLogger(__name__)

# Create genai client (sync)
# The new google-genai SDK uses Client(api_key=...), not configure(...)
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    # in CI / testing the constructor should work; log but continue to allow clearer errors later
    logger.exception("Failed to initialize genai.Client: %s", e)
    client = None

# Conservative tweet length so we stay safe (leaves buffer for emoji/urls)
MAX_TWEET_CHARS = 260


def truncate_to_limit(text: str, limit: int = MAX_TWEET_CHARS) -> str:
    """Trim text to a safe length and clean simple HTML tags."""
    if text is None:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _clean_spaces(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _call_gemini(
    prompt: str,
    max_output_tokens: int = 300,
    temperature: float = 0.7,
) -> str:
    """
    Call Gemini via google-genai SDK client. Returns the generated text (string).
    Raises Exception on permanent failure.
    """
    if client is None:
        raise RuntimeError("Gemini client not initialized")

    try:
        logger.info("Calling Gemini with model %s (max_tokens=%d)", GEMINI_MODEL, max_output_tokens)
        # The SDK's generate_content returns an object with .text or .response depending on version.
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        # SDK exposes response.text in examples
        # Some SDK versions use response.output[0].content — prefer .text if present
        if hasattr(response, "text") and response.text:
            return response.text
        # fallback checks
        try:
            # response.parts / response.output style
            if getattr(response, "output", None):
                parts = response.output
                # join text parts if available
                text_parts = []
                for p in parts:
                    if hasattr(p, "text"):
                        text_parts.append(p.text)
                    elif isinstance(p, dict) and p.get("content"):
                        text_parts.append(p["content"])
                if text_parts:
                    return "\n".join(text_parts)
        except Exception:
            pass

        # Last resort: stringify entire response
        logger.warning("Gemini response did not contain .text; returning str(response)")
        return str(response)

    except genai_errors.APIError as e:
        logger.error("Gemini APIError: %s", e)
        raise
    except Exception as e:
        logger.error("Gemini API call failed: %s", e)
        raise


def _split_tweets_from_response(content: str, expected_count: int = 5) -> List[str]:
    """
    Split model output into tweets using '---' delimiter. Clean & truncate.
    """
    if not content:
        return []

    parts = re.split(r"\n\s*---\s*\n", content.strip())
    cleaned: List[str] = []
    for part in parts:
        txt = part.strip()
        txt = re.sub(r"^Tweet\s*\d+:\s*", "", txt, flags=re.IGNORECASE)
        txt = re.sub(r"^\d+\.\s*", "", txt)
        txt = _clean_spaces(txt)
        txt = truncate_to_limit(txt)
        if txt:
            cleaned.append(txt)

    while len(cleaned) < expected_count:
        cleaned.append(truncate_to_limit("More updates on this story soon. #India #News"))

    return cleaned[:expected_count]


FALLBACK_THREAD = [
    "🔔 Breaking: We are monitoring a developing story. More verified updates soon. #India #News",
    "We are following official sources and will share key facts when available.",
    "We'll summarise verified impact and what it means for citizens & policy.",
    "If you have trusted sources, reply with links — we will review and cite them.",
    "Follow for real-time, verified updates. We avoid rumours. #TrustworthyNews",
]


def generate_thread_for_big_story(big_story: Dict) -> List[str]:
    """
    Generate 5-tweet thread for a big story using Gemini. On failure, return FALLBACK_THREAD.
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

    prompt = system_prompt + "\n\n" + user_prompt

    try:
        content = _call_gemini(prompt, max_output_tokens=GEMINI_MAX_TOKENS_THREAD, temperature=0.65)
    except Exception as e:
        logger.error("Failed to generate thread: %s", e)
        logger.info("Returning fallback thread.")
        return FALLBACK_THREAD

    tweets = _split_tweets_from_response(content, expected_count=5)
    logger.info("Generated %d tweets from Gemini.", len(tweets))
    return tweets


def generate_short_tweets_for_supporting_stories(
    supporting_stories: List[Dict],
    max_tweets: int = 2,
) -> List[str]:
    """
    Generate up to `max_tweets` short tweets for supporting stories.
    """
    if not supporting_stories or max_tweets <= 0:
        return []

    stories_for_prompt = supporting_stories[:max_tweets]
    formatted_stories = []
    for idx, story in enumerate(stories_for_prompt, start=1):
        t = story.get("title", "") or ""
        d = story.get("description", "") or ""
        s = (story.get("source") or {}).get("name", "") or ""
        formatted_stories.append(f"{idx}) Title: {t}\nDescription: {d}\nSource: {s}")

    system_prompt = (
        "You are an assistant that writes India-focused X (Twitter) posts.\n"
        "Rules:\n"
        "- Tone: calm, neutral, analytical, diplomatic.\n"
        "- No hate speech or personal attacks.\n"
        "- Each tweet must be under 280 characters.\n"
        "- Each tweet should mention the core point of the story.\n"
        "- Use 1–2 relevant hashtags like #India, #Economy, #Policy, etc.\n"
        "- Output one tweet per story, separated by a line containing only '---'."
    )

    user_prompt = (
        "Write short standalone tweets for the following India-related news stories.\n\n"
        f"{'\n\n'.join(formatted_stories)}\n\n"
        "Output:\n- Up to {max_tweets} tweets, separated by a line of '---'."
    )

    prompt = system_prompt + "\n\n" + user_prompt

    try:
        content = _call_gemini(prompt, max_output_tokens=GEMINI_MAX_TOKENS_SHORT, temperature=0.6)
    except Exception as e:
        logger.error("Failed to generate short tweets: %s", e)
        return []

    tweets = _split_tweets_from_response(content, expected_count=max_tweets)
    logger.info("Generated %d short supporting tweets.", len(tweets))
    return tweets
