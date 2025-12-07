"""
AI tweet writer using OpenAI (gpt-4o-mini).

Responsibilities:
- Call OpenAI chat completions API
- Generate:
    - 5-tweet thread for a big story
    - 1–2 short standalone tweets for supporting stories
- Enforce conservative character limit per tweet
"""

import logging
import re
from typing import List, Dict

from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

# Initialize OpenAI client.
# We pass api_key explicitly, but it will also work if OPENAI_API_KEY
# is available as an environment variable.
client = OpenAI(api_key=OPENAI_API_KEY)

# Conservative tweet length so we stay safe even with emoji weighting.
MAX_TWEET_CHARS = 130


def truncate_to_280(text: str) -> str:
    """
    Ensure tweet text is within a conservative length.

    - Strip HTML-like tags (e.g. <br>, <b>)
    - Hard-limit to ~MAX_TWEET_CHARS chars so even with emoji weighting / URL rules
      we stay under X's effective limit.
    """
    if text is None:
        return ""

    # Remove simple HTML tags if model adds any
    text = re.sub(r"<[^>]+>", "", text)

    text = text.strip()
    if len(text) <= MAX_TWEET_CHARS:
        return text

    return text[: MAX_TWEET_CHARS - 3].rstrip() + "..."


def _clean_spaces(text: str) -> str:
    """Normalize whitespace in tweet text."""
    if not text:
        return ""
    # Collapse multiple spaces and strip
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _call_openai(
    messages: List[Dict],
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """
    Call OpenAI chat completions endpoint using the configured model.

    Returns the content string of the first choice.
    Raises an Exception if the API call fails.
    """
    try:
        logger.info("Calling OpenAI with model %s", OPENAI_MODEL)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("OpenAI API call failed: %s", e)
        raise


def _split_tweets_from_response(content: str, expected_count: int = 5) -> List[str]:
    """
    Split LLM response into individual tweets using '---' as delimiter.
    Clean each tweet and enforce MAX_TWEET_CHARS.
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
    Generate a 5-tweet thread for the big story using OpenAI.

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
        "- Each tweet must be under 280 characters (we will truncate further).\n"
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
        content = _call_openai(messages, max_tokens=800, temperature=0.7)
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
      - < MAX_TWEET_CHARS chars (after truncation)
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
        "- Each tweet must be under 280 characters (we will truncate further).\n"
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
        content = _call_openai(messages, max_tokens=600, temperature=0.7)
    except Exception as e:
        logger.error("Failed to generate short tweets: %s", e)
        # For supporting tweets, we can fail softly and just return empty list
        return []

    tweets = _split_tweets_from_response(content, expected_count=max_tweets)
    logger.info("Generated %d short supporting tweets.", len(tweets))
    return tweets
