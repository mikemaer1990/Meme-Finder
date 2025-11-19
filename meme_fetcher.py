#!/usr/bin/env python3
"""
Weekly Meme Fetcher
Scrapes trending memes from Reddit and sends them to Discord via webhook.
"""

import os
import sys
import time
import re
import requests
import feedparser
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load environment variables from .env file (for local testing)
load_dotenv()

# Configuration
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RATE_LIMIT_DELAY = 1  # seconds between Discord messages


def fetch_memes_from_reddit(subreddit: str, limit: int = 5) -> List[Dict]:
    """
    Fetch memes from a Reddit subreddit's top posts using RSS feeds.

    Args:
        subreddit: Name of the subreddit (e.g., 'memes', 'dankmemes')
        limit: Maximum number of memes to fetch

    Returns:
        List of dictionaries containing meme data (title, image_url, post_url, score)
    """
    # Reddit RSS feed URL for top posts
    rss_url = f"https://www.reddit.com/r/{subreddit}/top/.rss?t=week&limit=50"
    memes = []

    print(f"Fetching memes from r/{subreddit}...")

    for attempt in range(MAX_RETRIES):
        try:
            # Parse the RSS feed
            feed = feedparser.parse(rss_url)

            if not feed.entries:
                print(f"No entries found in RSS feed for r/{subreddit}")
                return memes

            # Process each entry
            for entry in feed.entries:
                if len(memes) >= limit:
                    break

                try:
                    title = entry.title
                    post_url = entry.link

                    # Extract image URL from the content
                    image_url = None

                    # Check if there's a media thumbnail
                    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0]['url']

                    # Try to find image in the content
                    if not image_url and hasattr(entry, 'content'):
                        content = entry.content[0].value
                        # Look for image tags in the HTML content
                        if '<img' in content:
                            img_match = re.search(r'<img[^>]+src="([^"]+)"', content)
                            if img_match:
                                potential_url = img_match.group(1)
                                # Decode HTML entities
                                potential_url = potential_url.replace('&amp;', '&')
                                # Check if it's an actual image (not preview)
                                if any(ext in potential_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']) and 'preview' in potential_url:
                                    image_url = potential_url

                        # Also check for direct image links in the summary
                        if not image_url:
                            link_match = re.search(r'href="([^"]+\.(jpg|jpeg|png|gif)[^"]*)"', content)
                            if link_match:
                                image_url = link_match.group(1).replace('&amp;', '&')

                    # Try the link itself if it's a direct image
                    if not image_url and hasattr(entry, 'id'):
                        if any(entry.id.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                            image_url = entry.id

                    # Extract score from the content if available
                    score = "?"
                    if hasattr(entry, 'content'):
                        content = entry.content[0].value
                        score_match = re.search(r'(\d+)\s+points?', content)
                        if score_match:
                            score = score_match.group(1)

                    # Only add if we found an image
                    if image_url:
                        memes.append({
                            'title': title,
                            'image_url': image_url,
                            'post_url': post_url,
                            'score': score
                        })

                except Exception as e:
                    print(f"Error parsing entry: {e}")
                    continue

            print(f"Successfully fetched {len(memes)} memes from r/{subreddit}")
            return memes

        except Exception as e:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                print(f"Failed to fetch memes after {MAX_RETRIES} attempts")
                return memes

    return memes


def send_to_discord(memes: List[Dict], webhook_url: str, title: str = "🔥 **Top 5 Memes This Week** 🔥", color: int = 16734003) -> bool:
    """
    Send memes to Discord via webhook with rich embeds.

    Args:
        memes: List of meme dictionaries
        webhook_url: Discord webhook URL
        title: Title for the Discord message
        color: Embed color (default: orange)

    Returns:
        True if successful, False otherwise
    """
    if not memes:
        print("No memes to send")
        return False

    # Create embeds for each meme
    embeds = []
    for i, meme in enumerate(memes, 1):
        embed = {
            "title": f"{i}. {meme['title'][:250]}",  # Discord title limit is 256 chars
            "url": meme['post_url'],
            "image": {"url": meme['image_url']},
            "footer": {"text": f"👍 {meme['score']} upvotes"},
            "color": color
        }
        embeds.append(embed)

    # Prepare payload
    payload = {
        "content": title,
        "embeds": embeds
    }

    # Send to Discord
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Sending {len(memes)} memes to Discord...")
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            print("✅ Successfully sent memes to Discord!")
            return True

        except requests.RequestException as e:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                print(f"Failed to send memes after {MAX_RETRIES} attempts")
                return False

    return False


def main():
    """Main function to orchestrate meme fetching and sending."""
    print("=== Weekly Meme Fetcher ===\n")

    # Validate webhook URL
    if not DISCORD_WEBHOOK_URL:
        print("❌ Error: DISCORD_WEBHOOK_URL environment variable not set")
        print("Please set the webhook URL in your .env file or GitHub Secrets")
        sys.exit(1)

    if not DISCORD_WEBHOOK_URL.startswith('https://discord.com/api/webhooks/'):
        print("❌ Error: Invalid Discord webhook URL")
        sys.exit(1)

    # Category 1: General trending memes
    print("📊 Fetching general trending memes...\n")
    general_subreddits = ['memes', 'dankmemes', 'ProgrammerHumor']
    general_memes = []

    for subreddit in general_subreddits:
        memes = fetch_memes_from_reddit(subreddit, limit=5)
        general_memes.extend(memes)

        # If we have enough memes, stop
        if len(general_memes) >= 5:
            break

        # Small delay between subreddit requests
        time.sleep(1)

    # Take top 5 general memes
    top_general_memes = general_memes[:5]

    if len(top_general_memes) < 5:
        print(f"⚠️ Warning: Only found {len(top_general_memes)} general memes (target was 5)\n")

    # Category 2: Customer support memes (SaaS/Tech)
    print("\n📧 Fetching customer support memes...\n")
    work_subreddits = ['talesfromtechsupport', 'iiiiiiitttttttttttt', 'sysadmin', 'techsupportgore', 'ProgrammerHumor']
    work_memes = []

    # Fetch from ALL work subreddits to get variety
    for subreddit in work_subreddits:
        memes = fetch_memes_from_reddit(subreddit, limit=2)  # Get 2 from each for variety
        work_memes.extend(memes)

        # Small delay between subreddit requests
        time.sleep(1)

    # Take top 5 work memes
    top_work_memes = work_memes[:5]

    if len(top_work_memes) < 5:
        print(f"⚠️ Warning: Only found {len(top_work_memes)} customer support memes (target was 5)\n")

    # Send both categories to Discord
    success_general = False
    success_work = False

    if top_general_memes:
        print("\n" + "="*50)
        success_general = send_to_discord(
            top_general_memes,
            DISCORD_WEBHOOK_URL,
            title="🔥 **Top 5 Trending Memes This Week** 🔥",
            color=16734003  # Orange
        )
        time.sleep(RATE_LIMIT_DELAY)  # Small delay between messages

    if top_work_memes:
        print("\n" + "="*50)
        success_work = send_to_discord(
            top_work_memes,
            DISCORD_WEBHOOK_URL,
            title="💻 **Top 5 Tech Support Memes** 💻",
            color=3447003  # Blue
        )

    # Check overall success
    if success_general or success_work:
        print("\n✅ Meme fetcher completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Meme fetcher encountered errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
