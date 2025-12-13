import logging

from src.news_client import fetch_top_headlines, select_big_and_supporting_stories
from src.ai_writer import (
    generate_thread_for_big_story,
    generate_short_tweets_for_supporting_stories,
)
from src.x_auth import refresh_access_token
from src.x_client import post_thread, post_tweets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run():
    logger.info("=" * 80)
    logger.info("Starting India Breaking News X Bot run...")
    logger.info("=" * 80)

    logger.info("\n[STEP 1] Refreshing X access token...")
    refresh_access_token()
    logger.info("✓ Access token refreshed")

    logger.info("\n[STEP 2] Fetching India top headlines...")
    try:
        articles = fetch_top_headlines()
    except Exception as e:
        logger.error("News fetch failed: %s", e)
        return

    logger.info("✓ Fetched %d articles", len(articles))

    logger.info("\n[STEP 3] Selecting big + supporting stories...")
    big_story, supporting = select_big_and_supporting_stories(articles)
    logger.info("✓ Selected big story: %s...", big_story["title"][:60])

    logger.info("\n[STEP 4] Generating 5-tweet thread for big story...")
    tweets = generate_thread_for_big_story(big_story)
    logger.info("✓ Generated %d tweets", len(tweets))

    logger.info("\n[STEP 5] Generating short tweets for supporting stories...")
    short_tweets = generate_short_tweets_for_supporting_stories(supporting)

    logger.info("\n[STEP 6] Posting thread to X...")
    thread_ids = post_thread(tweets)
    logger.info("✓ Posted thread with %d tweets", len(thread_ids))

    if short_tweets:
        logger.info("\n[STEP 7] Posting short tweets...")
        post_tweets(short_tweets)

    logger.info("\n✓ Run completed successfully!")


if __name__ == "__main__":
    run()
