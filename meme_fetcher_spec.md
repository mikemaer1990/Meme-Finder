# Weekly Meme Fetcher - Project Specification

## Overview
Build a Python script that runs every Monday at 5:30 AM PST (accounting for daylight savings) to fetch 5 trending memes from the past week and send them to a Discord channel via webhook.

## Requirements

### Core Functionality
- Scrape trending memes from Reddit (no API required)
- Target subreddits: r/memes, r/dankmemes, or r/ProgrammerHumor
- Get the top 5 memes from the past week
- Send memes to Discord via webhook with titles and images
- Schedule to run every Monday at 5:30 AM PST/PDT (auto-adjust for DST)

### Technical Constraints
- **NO APIs** except Discord webhook
- Use web scraping for Reddit
- Use GitHub Actions for scheduling (it handles DST automatically when using America/Los_Angeles timezone)
- Python 3.9+

## Project Structure

```
weekly-meme-fetcher/
├── meme_fetcher.py          # Main Python script
├── requirements.txt          # Python dependencies
├── .github/
│   └── workflows/
│       └── weekly_memes.yml  # GitHub Actions workflow
├── .env.example             # Example environment variables
└── README.md                # Setup instructions
```

## File Specifications

### 1. meme_fetcher.py

**Purpose**: Scrape memes and send to Discord

**Key Functions**:
- `fetch_memes_from_reddit(subreddit, limit)` - Scrapes memes using BeautifulSoup
  - Use `old.reddit.com` for easier scraping
  - Target `/top/?t=week` for weekly top posts
  - Extract: title, image URL, Reddit post URL, upvotes
  - Filter for image posts only (.jpg, .png, .gif, .gifv)
  
- `send_to_discord(memes, webhook_url)` - Sends formatted memes to Discord
  - Create rich embeds for each meme
  - Include: title, image, link to Reddit post, upvote count
  - Send one message with multiple embeds
  - Handle rate limits (wait if needed)

**Error Handling**:
- Retry logic for network failures (3 attempts)
- Graceful degradation if fewer than 5 memes found
- Log errors to console
- Validate webhook URL exists

**Dependencies**:
- requests
- beautifulsoup4
- python-dotenv (for local testing)

### 2. requirements.txt

```
requests>=2.31.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
```

### 3. .github/workflows/weekly_memes.yml

**Purpose**: GitHub Actions workflow for scheduling

**Configuration**:
- Trigger: Cron schedule `30 13 * * 1` (5:30 AM PST = 1:30 PM UTC, Monday)
- Timezone handling: GitHub Actions runs in UTC, so calculate offset
- Also include `workflow_dispatch` for manual testing
- Use `America/Los_Angeles` timezone context in the script

**Steps**:
1. Checkout code
2. Set up Python 3.11
3. Install dependencies from requirements.txt
4. Run meme_fetcher.py
5. Use GitHub Secrets for DISCORD_WEBHOOK_URL

**Important**: 
- PST is UTC-8, PDT is UTC-7
- Schedule for 1:30 PM UTC (covers PST) but add logic in Python to check timezone
- OR use `30 13 * * 1` and document that it's 5:30 AM PST

### 4. .env.example

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE
```

### 5. README.md

Include:
- Project description
- Setup instructions
- How to get Discord webhook URL
- How to set GitHub Secret
- How to test locally
- How to manually trigger the workflow
- Troubleshooting section

## Implementation Details

### Reddit Scraping Strategy
1. Use `old.reddit.com` (easier to parse than new Reddit)
2. URL format: `https://old.reddit.com/r/{subreddit}/top/?t=week`
3. Parse HTML with BeautifulSoup
4. Find posts using class selectors: `div.thing`
5. Extract:
   - Title: `a.title`
   - Image URL: `data-url` attribute
   - Post URL: href from title link
   - Score: `div.score.unvoted`

### Discord Webhook Format
```python
{
    "content": "🔥 **Top 5 Memes This Week** 🔥",
    "embeds": [
        {
            "title": "Meme Title",
            "url": "https://reddit.com/r/...",
            "image": {"url": "https://i.redd.it/..."},
            "footer": {"text": "👍 12.3k upvotes"},
            "color": 16734003  # Orange color
        }
    ]
}
```

### Timezone Handling
Since GitHub Actions runs in UTC:
- **Option 1**: Use cron `30 13 * * 1` for 5:30 AM PST (1:30 PM UTC)
  - This is 5:30 AM PST and 6:30 AM PDT
  - Add a note in README about DST shift
  
- **Option 2** (Recommended): Add timezone check in Python
  ```python
  from datetime import datetime
  import pytz
  
  pst = pytz.timezone('America/Los_Angeles')
  current_time = datetime.now(pst)
  # Verify it's actually 5:30 AM PST/PDT
  ```

### Testing
- Include manual trigger in GitHub Actions (`workflow_dispatch`)
- Local testing with `.env` file
- Test with different subreddits
- Verify Discord formatting

## Edge Cases to Handle
1. Reddit changes HTML structure → Add try/except blocks
2. No memes found → Send notification that no memes available
3. Discord webhook rate limits → Add delays between requests
4. Images fail to load → Include fallback to post URL
5. Webhook URL missing → Fail gracefully with clear error

## Security
- Never commit webhook URL
- Use GitHub Secrets for DISCORD_WEBHOOK_URL
- Include .env in .gitignore
- Use environment variables only

## Future Enhancements (Optional)
- Support multiple subreddits
- Configurable number of memes
- Filter NSFW content
- Deduplicate if same meme appears multiple times
- Add video support (v.redd.it links)

## Success Criteria
✅ Runs every Monday at 5:30 AM PST  
✅ Fetches exactly 5 trending memes  
✅ Sends formatted message to Discord  
✅ Works without any APIs (except Discord webhook)  
✅ Handles DST automatically  
✅ Can be manually triggered for testing  
✅ Clear error messages if something fails  

---

**Note**: Feed this entire specification to Claude Code and it will generate all the necessary files and help you set up the project.
