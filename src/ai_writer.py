"""
AI tweet writer using Google Gemini (google-genai SDK).

This module is resilient to multiple SDK versions and response shapes:
- Tries `client.models.generate_content(...)` (new style)
- Falls back to `client.generate_text(...)` or `client.generate_content(...)`
- Extracts text from response.text, response.output, response.candidates, or dict keys
- On permanent failure returns a safe fallback thread (so the workflow can continue)
"""
import logging
import re
from typing import List, Dict, Optional

from google import genai
from google.genai import errors as genai_errors

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS_THREAD,
    GEMINI_MAX_TOKENS_SHORT,
)

logger = logging.getLogger(__name__)

# Initialize client once; if it fails we set client = None and handle later
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    logger.exception("Failed to initialize genai.Client: %s", e)
    client = None

# Conservative tweet length so we stay safe (leaves buffer for emoji/urls)
MAX_TWEET_CHARS = 260


def truncate_to_limit(text: str, limit: int = MAX_TWEET_CHARS) -> str:
    """Clean simple HTML tags and trim text to `limit` chars."""
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


def _extract_text_from_response(response) -> Optional[str]:
    """
    Try various ways to extract textual output from different SDK versions / shapes.
    Returns the extracted string or None.
    """
    try:
        # 1) Modern simple .text property
        if hasattr(response, "text") and response.text:
            return response.text

        # 2) Some responses have .output which is a list of parts
        output = getattr(response, "output", None)
        if output:
            texts = []
            for part in output:
                # part may be an object with .text
                if hasattr(part, "text") and part.text:
                    texts.append(part.text)
                # or dict-like with content/text
                elif isinstance(part, dict):
                    # try common keys
                    for k in ("content", "text", "message", "output_text"):
                        if part.get(k):
                            texts.append(part.get(k))
                            break
            if texts:
                return "\n".join(texts)

        # 3) Some versions use .candidates list with content/text
        candidates = getattr(response, "candidates", None)
        if candidates:
            # candidate might be object or dict
            first = candidates[0]
            if hasattr(first, "content") and first.content:
                return first.content
            if isinstance(first, dict):
                for k in ("content", "text"):
                    if first.get(k):
                        return first.get(k)

        # 4) If it's a mapping/dict with common keys
        if isinstance(response, dict):
            for key in ("text", "output", "content", "result", "response"):
                val = response.get(key)
                if isinstance(val, str) and val:
                    return val
                if isinstance(val, dict):
                    # dig one level
                    for subk in ("text", "content"):
                        if val.get(subk):
                            return val.get(subk)
                if isinstance(val, list) and val:
                    # join text fields
                    parts = []
                    for item in val:
                        if isinstance(item, str):
                            parts.append(item)
                        elif isinstance(item, dict):
                            for subk in ("text", "content"):
                                if item.get(subk):
                                    parts.append(item.get(subk))
                                    break
                    if parts:
                        return "\n".join(parts)

    except Exception as e:
        logger.debug("Exception while extracting text from response: %s", e)

    return None


def _call_gemini_try_variants(
    prompt: str,
    max_output_tokens: int = 300,
    temperature: float = 0.7,
) -> str:
    """
    Try multiple client call signatures to support different google-genai SDK versions.
    Returns the output text or raises an Exception if all attempts fail.
    """
    if client is None:
        raise RuntimeError("Gemini client is not initialized (client is None)")

    last_error = None

    # Attempt A: new-style client.models.generate_content(model=..., contents=..., max_output_tokens=...)
    try:
        logger.info("Attempting client.models.generate_content(model=%s)", GEMINI_MODEL)
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        text = _extract_text_from_response(resp)
        if text:
            logger.info("Generation successful with client.models.generate_content")
            return text
        last_error = Exception("No text in response from client.models.generate_content")
    except TypeError as e:
        # signature mismatch (e.g., unexpected keyword 'generation_config' etc.)
        logger.warning("client.models.generate_content TypeError: %s", e)
        last_error = e
    except genai_errors.APIError as e:
        logger.error("Gemini APIError on client.models.generate_content: %s", e)
        last_error = e
    except Exception as e:
        logger.exception("Error calling client.models.generate_content: %s", e)
        last_error = e

    # Attempt B: client.generate_text(...) (older helper)
    try:
        logger.info("Attempting client.generate_text(model=%s)", GEMINI_MODEL)
        # Not all SDKs have this, but try it
        resp = client.generate_text(
            model=GEMINI_MODEL,
            prompt=prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        text = _extract_text_from_response(resp)
        if text:
            logger.info("Generation successful with client.generate_text")
            return text
        last_error = Exception("No text in response from client.generate_text")
    except AttributeError as e:
        logger.debug("client.generate_text not available: %s", e)
        last_error = e
    except Exception as e:
        logger.exception("Error calling client.generate_text: %s", e)
        last_error = e

    # Attempt C: client.generate_content(...) (alternate location)
    try:
        logger.info("Attempting client.generate_content(model=%s)", GEMINI_MODEL)
        resp = client.generate_content(
            model=GEMINI_MODEL,
            prompt=prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        text = _extract_text_from_response(resp)
        if text:
            logger.info("Generation successful with client.generate_content")
            return text
        last_error = Exception("No text in response from client.generate_content")
    except AttributeError as e:
        logger.debug("client.generate_content not available: %s", e)
        last_error = e
    except Exception as e:
        logger.exception("Error calling client.generate_content: %s", e)
        last_error = e

    # Attempt D: Try passing a dict "generation_config" if earlier versions expect it (last resort)
    try:
        logger.info("Attempting client.models.generate_content with generation_config (last-resort)")
        gen_cfg = {"max_output_tokens": max_output_tokens, "temperature": temperature}
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            prompt=prompt,
            generation_config=gen_cfg,
        )
        text = _extract_text_from_response(resp)
        if text:
            logger.info("Generation successful with generation_config style call")
            return text
        last_error = Exception("No text in response from generation_config style call")
    except Exception as e:
        logger.debug("Generation-config style call failed: %s", e)
        last_error = e

    # If all failed, raise the last error for visibility
    logger.error("All Gemini generation attempts failed. Last error: %s", last_error)
    raise last_error or Exception("Unknown error calling Gemini")


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
        content = _call_gemini_try_variants(
            prompt, max_output_tokens=GEMINI_MAX_TOKENS_THREAD, temperature=0.65
        )
    except Exception as e:
        logger.error("Tweet generation failed: %s", e)
        logger.info("Returning fallback thread.")
        return FALLBACK_THREAD

    tweets = _split_tweets_from_response(content, expected_count=5)
    logger.info("Generated %d tweets from Gemini.", len(tweets))
    return tweets


def generate_short_tweets_for_supporting_stories(
    supporting_stories: List[Dict], max_tweets: int = 2
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

    stories_block = "\n\n".join(formatted_stories)

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

    user_prompt_lines = [
        "Write short standalone tweets for the following India-related news stories.",
        "",
        stories_block,
        "",
        "Output:",
        f"- Up to {max_tweets} tweets, separated by a line of '---'.",
    ]
    user_prompt = "\n".join(user_prompt_lines)
    prompt = system_prompt + "\n\n" + user_prompt

    try:
        content = _call_gemini_try_variants(
            prompt, max_output_tokens=GEMINI_MAX_TOKENS_SHORT, temperature=0.6
        )
    except Exception as e:
        logger.error("Failed to generate short tweets: %s", e)
        return []

    tweets = _split_tweets_from_response(content, expected_count=max_tweets)
    logger.info("Generated %d short supporting tweets.", len(tweets))
    return tweets
