"""Main orchestrator for the Crypto Institutional Twitter Bot."""

import os
import sys
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

import config
from news_fetcher import NewsFetcher
from analyzer import NewsAnalyzer
from poster import TwitterPoster
from storage import NewsStorage

# Load environment variables (override=True to pick up .env changes)
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CryptoTwitterBot:
    def __init__(self, hours_override: int = None, topic_filter: str = None):
        """Initialize the bot with all components."""
        logger.info("Initializing Crypto Twitter Bot...")

        try:
            self.fetcher = NewsFetcher()
            self.analyzer = NewsAnalyzer()
            self.poster = TwitterPoster()
            self.storage = NewsStorage()

            # Configuration
            self.scan_interval = int(os.getenv("SCAN_INTERVAL_HOURS", 8))

            # Allow command-line override for fetch hours
            self.fetch_hours = hours_override if hours_override else self.scan_interval

            # Optional topic filter
            self.topic_filter = topic_filter

            logger.info("Bot initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            sys.exit(1)

    def run_cycle(self):
        """Run one complete cycle: fetch, curate, analyze, and post."""
        logger.info("=" * 60)
        logger.info(f"Starting bot cycle at {datetime.now()}")
        logger.info("=" * 60)

        try:
            # Step 1: Fetch all recent headlines
            logger.info(f"Step 1: Fetching headlines from last {self.fetch_hours} hours...")
            headlines = self.fetcher.get_all_headlines(hours=self.fetch_hours, limit=50)

            if not headlines:
                logger.warning("No headlines found. Skipping this cycle.")
                return

            logger.info(f"  Found {len(headlines)} headlines for AI curation")

            # Step 2: AI curates top 5 most important headlines
            logger.info("Step 2: AI selecting most critical headlines...")
            # Single-subject deep dive: select only the #1 most critical story
            selected_ids = self.analyzer.select_top_headlines(headlines, top_k=1, topic=self.topic_filter)

            if not selected_ids:
                logger.warning("AI selection failed. Skipping this cycle.")
                return

            # Step 3: Get full articles for selected IDs
            logger.info("Step 3: Fetching full articles for selected headlines...")
            selected_articles = self.fetcher.get_articles_by_ids(selected_ids)
            logger.info(f"  Retrieved {len(selected_articles)} articles")

            for i, article in enumerate(selected_articles, 1):
                logger.info(f"  [{i}] {article['title'][:60]}...")

            # Step 4: Check if already posted
            new_articles = []
            for article in selected_articles:
                if not self.storage.is_already_posted(article["title"], article["source"]):
                    new_articles.append(article)

            if not new_articles:
                logger.warning("All selected articles have been posted before. Skipping this cycle.")
                return

            logger.info(f"Step 4: Found {len(new_articles)} new articles to analyze")

            # Step 5: Deep analysis with LLM
            logger.info("Step 5: Deep analysis with LLM...")
            tweets = self.analyzer.analyze_news(new_articles)

            if not tweets:
                logger.warning("No tweets generated from analysis. Skipping this cycle.")
                return

            logger.info(f"Step 6: Generated market update ({len(tweets)} tweet{'s' if len(tweets) > 1 else ''})")
            for i, tweet in enumerate(tweets, 1):
                logger.info(f"  Part {i}: {tweet[:60]}...")

            # Save draft to file for easy review
            tweet_content = "\n\n---\n\n".join(tweets)
            with open("latest_tweet.md", "w") as f:
                f.write(tweet_content)
            print("Draft saved to latest_tweet.md")

            # Archive to persistent history file
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open("tweet_archive.md", "a") as f:
                f.write(f"\n\n--- [{timestamp}] ---\n\n")
                f.write(tweet_content)
            print("Archived to tweet_archive.md")

            # Step 7: Post to Twitter
            logger.info("Step 7: Posting to Twitter...")
            success = self.poster.post_thread(tweets)

            if success:
                # Mark articles as posted
                tweet_text = "\n".join(tweets)
                for article in new_articles:
                    self.storage.mark_as_posted(
                        article["title"],
                        article["source"],
                        tweet_text
                    )
                logger.info("✓ Cycle completed successfully!")
            else:
                logger.error("✗ Failed to post tweets")

        except Exception as e:
            logger.error(f"Error during bot cycle: {e}", exc_info=True)

    def test_apis(self):
        """Test API connections before running."""
        logger.info("Testing API connections...")

        # Test Twitter
        if not self.poster.test_connection():
            logger.error("Twitter API test failed!")
            return False

        # Test news fetching
        test_articles = self.fetcher.fetch_recent_news(hours=24)
        logger.info(f"News fetch test: Found {len(test_articles)} articles")

        logger.info("All API tests passed!")
        return True


def main():
    """Main entry point - runs once and exits (suitable for cron)."""
    print("""
    ╔════════════════════════════════════════════╗
    ║  Crypto Institutional Twitter Bot v1.0     ║
    ║  Professional Market Analysis & Posting    ║
    ╚════════════════════════════════════════════╝
    """)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Crypto Institutional Twitter Bot")
    parser.add_argument("--hours", type=int, default=None,
                        help="Override news fetch window (default: 8 hours)")
    parser.add_argument("--skip-test", action="store_true",
                        help="Skip API connection tests")
    parser.add_argument("--live", action="store_true",
                        help="Enable live posting to Twitter (disables DRY_RUN)")
    parser.add_argument("--topic", type=str, default=None,
                        help="Filter news by keyword (e.g., --topic 'ETF')")
    parser.add_argument("--retry-post", action="store_true",
                        help="Re-post content from latest_tweet.md (skip fetching)")
    args = parser.parse_args()

    # Handle live mode
    if args.live:
        print("LIVE MODE: Posting to Twitter enabled!")
        config.DRY_RUN = False
    else:
        print("DRY RUN: Posting disabled (Default). Use --live to post.")

    # Initialize bot with optional overrides
    bot = CryptoTwitterBot(hours_override=args.hours, topic_filter=args.topic)

    # Log the fetch window being used
    if args.hours:
        logger.info(f"Using custom fetch window: {args.hours} hours")
    else:
        logger.info(f"Using default fetch window: {bot.fetch_hours} hours")

    # Log topic filter if provided
    if args.topic:
        print(f"TOPIC FILTER: Searching for '{args.topic}'")
    else:
        print("TOPIC FILTER: None (auto-selection)")

    # Test APIs first (unless skipped)
    if not args.skip_test:
        if not bot.test_apis():
            logger.error("API tests failed. Please check your credentials.")
            sys.exit(1)

    # Handle --retry-post: re-post from latest_tweet.md
    if args.retry_post:
        try:
            with open("latest_tweet.md", "r") as f:
                tweet_content = f.read().strip()
            if not tweet_content:
                logger.error("latest_tweet.md is empty. Nothing to retry.")
                sys.exit(1)
            print(f"RETRY MODE: Posting content from latest_tweet.md ({len(tweet_content)} chars)")
            success = bot.poster.post_thread([tweet_content])
            if success:
                logger.info("✓ Retry post completed successfully!")
            else:
                logger.error("✗ Retry post failed")
        except FileNotFoundError:
            logger.error("latest_tweet.md not found. Run the bot first to generate content.")
            sys.exit(1)
    else:
        # Run normal cycle
        bot.run_cycle()

    logger.info("Bot execution complete. Exiting.")


if __name__ == "__main__":
    main()
