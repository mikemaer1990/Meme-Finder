#!/usr/bin/env python3
"""
Weekly Meme Fetcher
Scrapes trending memes from Reddit and sends them to Discord via webhook.
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
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

# User agent to avoid being blocked by Reddit
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def fetch_memes_from_reddit(subreddit: str, limit: int = 5) -> List[Dict]:
    """
    Scrape memes from a Reddit subreddit's top posts of the week.

    Args:
        subreddit: Name of the subreddit (e.g., 'memes', 'dankmemes')
        limit: Maximum number of memes to fetch

    Returns:
        List of dictionaries containing meme data (title, image_url, post_url, score)
    """
    url = f"https://old.reddit.com/r/{subreddit}/top/?t=week"
    memes = []

    print(f"Fetching memes from r/{subreddit}...")

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all post containers
            posts = soup.find_all('div', class_='thing')

            for post in posts:
                if len(memes) >= limit:
                    break

                try:
                    # Extract title
                    title_elem = post.find('a', class_='title')
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)

                    # Extract post URL
                    post_url = title_elem.get('href')
                    if post_url and not post_url.startswith('http'):
                        post_url = f"https://old.reddit.com{post_url}"

                    # Extract image URL from data-url attribute
                    image_url = post.get('data-url')

                    # Filter for image posts only
                    if image_url and any(image_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.gifv']):
                        # Handle .gifv (convert to .gif or use as-is)
                        if image_url.endswith('.gifv'):
                            image_url = image_url.replace('.gifv', '.gif')

                        # Extract upvote score
                        score_elem = post.find('div', class_='score unvoted')
                        if not score_elem:
                            score_elem = post.find('div', class_='score')
                        score = score_elem.get_text(strip=True) if score_elem else '0'

                        memes.append({
                            'title': title,
                            'image_url': image_url,
                            'post_url': post_url,
                            'score': score
                        })

                except Exception as e:
                    print(f"Error parsing post: {e}")
                    continue

            print(f"Successfully fetched {len(memes)} memes from r/{subreddit}")
            return memes

        except requests.RequestException as e:
            print(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                print(f"Failed to fetch memes after {MAX_RETRIES} attempts")
                return memes

    return memes


def send_to_discord(memes: List[Dict], webhook_url: str) -> bool:
    """
    Send memes to Discord via webhook with rich embeds.

    Args:
        memes: List of meme dictionaries
        webhook_url: Discord webhook URL

    Returns:
        True if successful, False otherwise
    """
    if not memes:
        print("No memes to send")
        # Send notification that no memes were found
        payload = {
            "content": "⚠️ No memes found this week. Please check the scraper configuration."
        }
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return False
        except Exception as e:
            print(f"Error sending notification: {e}")
            return False

    # Create embeds for each meme
    embeds = []
    for i, meme in enumerate(memes, 1):
        embed = {
            "title": f"{i}. {meme['title'][:250]}",  # Discord title limit is 256 chars
            "url": meme['post_url'],
            "image": {"url": meme['image_url']},
            "footer": {"text": f"👍 {meme['score']} upvotes"},
            "color": 16734003  # Orange color
        }
        embeds.append(embed)

    # Prepare payload
    payload = {
        "content": "🔥 **Top 5 Memes This Week** 🔥",
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

    # Try multiple subreddits in order of preference
    subreddits = ['memes', 'dankmemes', 'ProgrammerHumor']
    all_memes = []

    for subreddit in subreddits:
        memes = fetch_memes_from_reddit(subreddit, limit=5)
        all_memes.extend(memes)

        # If we have enough memes, stop
        if len(all_memes) >= 5:
            break

        # Small delay between subreddit requests
        time.sleep(1)

    # Take top 5 memes
    top_memes = all_memes[:5]

    if len(top_memes) < 5:
        print(f"⚠️ Warning: Only found {len(top_memes)} memes (target was 5)")

    # Send to Discord
    success = send_to_discord(top_memes, DISCORD_WEBHOOK_URL)

    if success:
        print("\n✅ Meme fetcher completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Meme fetcher encountered errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
