"""Main orchestration script for India Breaking News X Bot.

This is the entry point that:
1. Refreshes X access tokens
2. Fetches India news from News API
3. Selects big + supporting stories
4. Generates tweets using AI
5. Posts thread + standalone tweets to X
6. Logs all actions for debugging
"""

import logging
import sys

from src.x_auth import refresh_access_token
from src.news_client import fetch_top_headlines, select_big_and_supporting_stories
from src.ai_writer import generate_thread_for_big_story, generate_short_tweets_for_supporting_stories
from src.x_client import post_thread, post_tweet


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run() -> None:
    """
    Run the complete pipeline:
    1. Refresh tokens
    2. Fetch and select news
    3. Generate tweets
    4. Post to X
    
    Raises:
        Exception: If any step fails
    """
    try:
        logger.info("="*80)
        logger.info("Starting India Breaking News X Bot run...")
        logger.info("="*80)
        
        # Step 1: Refresh X access token
        logger.info("\n[STEP 1] Refreshing X access token...")
        access_token, refresh_token = refresh_access_token()
        logger.info(f"✓ Access token refreshed")
        
        # Step 2: Fetch news headlines
        logger.info("\n[STEP 2] Fetching India top headlines...")
        articles = fetch_top_headlines()
        logger.info(f"✓ Fetched {len(articles)} articles")
        
        # Step 3: Select stories
        logger.info("\n[STEP 3] Selecting big + supporting stories...")
        big_story, supporting_stories = select_big_and_supporting_stories(articles)
        logger.info(f"✓ Selected big story: {big_story['title'][:50]}...")
        logger.info(f"✓ Selected {len(supporting_stories)} supporting stories")
        
        # Step 4: Generate tweets for big story (5-tweet thread)
        logger.info("\n[STEP 4] Generating 5-tweet thread for big story...")
        thread_tweets = generate_thread_for_big_story(big_story)
        logger.info(f"✓ Generated {len(thread_tweets)} tweets")
        for i, tweet in enumerate(thread_tweets, 1):
            logger.info(f"  Tweet {i} ({len(tweet)} chars): {tweet[:60]}...")
        
        # Step 5: Generate short tweets for supporting stories
        logger.info("\n[STEP 5] Generating short tweets for supporting stories...")
        short_tweets = generate_short_tweets_for_supporting_stories(
            supporting_stories, max_tweets=2
        )
        logger.info(f"✓ Generated {len(short_tweets)} short tweets")
        for i, tweet in enumerate(short_tweets, 1):
            logger.info(f"  Tweet {i} ({len(tweet)} chars): {tweet[:60]}...")
        
        # Step 6: Post thread to X
        logger.info("\n[STEP 6] Posting 5-tweet thread to X...")
        thread_ids = post_thread(access_token, thread_tweets)
        logger.info(f"✓ Posted thread with {len(thread_ids)} tweets")
        for i, tweet_id in enumerate(thread_ids, 1):
            logger.info(f"  Thread tweet {i} ID: {tweet_id}")
        
        # Step 7: Post short tweets individually
        logger.info("\n[STEP 7] Posting short tweets to X...")
        posted_short_ids = []
        for i, tweet_text in enumerate(short_tweets, 1):
            tweet_id = post_tweet(access_token, tweet_text)
            posted_short_ids.append(tweet_id)
            logger.info(f"✓ Posted short tweet {i} with ID: {tweet_id}")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        logger.info(f"Big Story: {big_story['title'][:60]}...")
        logger.info(f"Supporting Stories: {len(supporting_stories)}")
        logger.info(f"Thread tweets posted: {len(thread_ids)}")
        logger.info(f"Short tweets posted: {len(posted_short_ids)}")
        logger.info(f"Total tweets posted: {len(thread_ids) + len(posted_short_ids)}")
        logger.info("="*80)
        logger.info("✓ Run completed successfully!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error("\n" + "="*80)
        logger.error(f"✗ FATAL ERROR: {e}")
        logger.error("="*80, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
