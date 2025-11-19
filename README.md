# Weekly Meme Fetcher

A Python script that automatically fetches the top 5 trending memes from Reddit every Monday at 5:30 AM PST and sends them to a Discord channel via webhook.

## Features

- Scrapes trending memes from Reddit (r/memes, r/dankmemes, r/ProgrammerHumor)
- Sends formatted memes to Discord with rich embeds
- Runs automatically every Monday at 5:30 AM PST using GitHub Actions
- No Reddit API required - uses web scraping
- Handles errors gracefully with retry logic
- Easy manual testing via workflow dispatch

## Project Structure

```
weekly-meme-fetcher/
├── meme_fetcher.py          # Main Python script
├── requirements.txt          # Python dependencies
├── .github/
│   └── workflows/
│       └── weekly_memes.yml  # GitHub Actions workflow
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Setup Instructions

### 1. Get a Discord Webhook URL

1. Open Discord and navigate to your server
2. Go to **Server Settings** > **Integrations** > **Webhooks**
3. Click **New Webhook** or **Create Webhook**
4. Customize the webhook name and channel
5. Click **Copy Webhook URL**
6. Save this URL - you'll need it for the next steps

### 2. Set Up GitHub Secret (for automated runs)

1. Push this repository to GitHub
2. Go to your repository on GitHub
3. Navigate to **Settings** > **Secrets and variables** > **Actions**
4. Click **New repository secret**
5. Name: `DISCORD_WEBHOOK_URL`
6. Value: Paste your Discord webhook URL
7. Click **Add secret**

### 3. Local Testing (Optional)

If you want to test the script locally:

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd meme-finder
   ```

2. **Install Python 3.9 or higher**
   ```bash
   python --version  # Should be 3.9+
   ```

3. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv

   # On Windows:
   venv\Scripts\activate

   # On macOS/Linux:
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a .env file**
   ```bash
   cp .env.example .env
   ```

6. **Edit .env and add your webhook URL**
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE
   ```

7. **Run the script**
   ```bash
   python meme_fetcher.py
   ```

## How to Manually Trigger the Workflow

You can manually trigger the meme fetcher without waiting for Monday:

1. Go to your GitHub repository
2. Click the **Actions** tab
3. Select **Weekly Meme Fetcher** from the left sidebar
4. Click **Run workflow** dropdown on the right
5. Click the green **Run workflow** button

This is useful for testing after initial setup.

## Schedule Details

The script runs automatically:
- **Day**: Every Monday
- **Time**: 5:30 AM PST (Pacific Standard Time)
- **Note**: During Daylight Saving Time (PDT), this becomes 6:30 AM PDT due to how GitHub Actions handles UTC times
- **Cron Expression**: `30 13 * * 1` (1:30 PM UTC on Mondays)

## How It Works

1. **Scraping**: The script uses BeautifulSoup to scrape `old.reddit.com` for the top posts of the week
2. **Filtering**: Only image posts (.jpg, .png, .gif) are selected
3. **Subreddits**: Tries r/memes, r/dankmemes, and r/ProgrammerHumor in order until 5 memes are found
4. **Discord**: Sends a formatted message with embeds containing:
   - Meme title
   - Image
   - Link to original Reddit post
   - Upvote count

## Troubleshooting

### The workflow isn't running

- **Check GitHub Secrets**: Ensure `DISCORD_WEBHOOK_URL` is set correctly in repository secrets
- **Check Actions**: Go to Actions tab and verify the workflow is enabled
- **Manual Trigger**: Try manually triggering the workflow to test

### No memes appearing in Discord

- **Verify Webhook URL**: Make sure the webhook URL is valid and the webhook hasn't been deleted
- **Check Logs**: Go to Actions tab > Click on the latest run > Check the logs for error messages
- **Reddit Changes**: Reddit may have changed their HTML structure. Check if the scraper needs updating

### Script fails with connection errors

- **Network Issues**: GitHub Actions may have temporary network issues. The script will retry 3 times
- **Reddit Blocking**: Reddit may be blocking the requests. The script uses appropriate user agents, but this can still happen occasionally
- **Rate Limiting**: If running too frequently, you may hit rate limits

### Only getting a few memes (less than 5)

- **Subreddit Content**: Some subreddits may have fewer image posts in their top weekly posts
- **Filter Criteria**: The script only selects direct image links, not gallery posts or videos
- **Check Logs**: Look at the script output to see how many memes were found from each subreddit

## Security Notes

- Never commit your `.env` file or webhook URL to the repository
- The `.gitignore` file is configured to exclude `.env`
- Always use GitHub Secrets for the webhook URL in automated workflows
- If your webhook URL is ever exposed, delete it in Discord and create a new one

## Customization

You can modify the script to:

- Change subreddits: Edit the `subreddits` list in `meme_fetcher.py:170`
- Change number of memes: Modify the `limit` parameter in the fetch calls
- Change schedule: Edit the cron expression in `.github/workflows/weekly_memes.yml:7`
- Add more subreddits: Add to the `subreddits` list
- Filter NSFW: Add additional filtering logic in the scraping function

## Dependencies

- **requests**: HTTP library for making web requests
- **beautifulsoup4**: HTML parsing library for web scraping
- **python-dotenv**: Load environment variables from .env file

## License

This project is provided as-is for personal use.

## Contributing

Feel free to open issues or submit pull requests for improvements!

## Acknowledgments

- Memes sourced from Reddit communities (r/memes, r/dankmemes, r/ProgrammerHumor)
- Thanks to the Discord webhook API for easy integrations
