# Google Play Reviews Scraper

Get **Google Play Store reviews** for any Android app: rating, text, thumbs-up count, app version, date, and the developer's reply. Thousands of reviews per app, with no login or proxies.

## Features
- Input Play Store URLs or package IDs (e.g. `com.spotify.music`).
- Sort by newest or most relevant; choose language and country.
- Filter by star rating, or stop at a date for incremental daily runs.
- Developer replies included, which is great for support-quality analysis.
- Optional app details: title, developer, rating, total ratings, installs, genre.

## Output example
```json
{
  "appId": "com.spotify.music", "appName": "Spotify: Music and Podcasts",
  "reviewId": "b6a1...", "rating": 4, "text": "Love it but...", "thumbsUp": 12,
  "appVersion": "9.0.92.1015", "userName": "A Google user", "date": "2026-11-19T22:09:04",
  "replyText": "Hey! Thanks for...", "repliedAt": "2026-11-20T08:00:00"
}
```

## Use cases
- App competitor research and feature-gap analysis
- Sentiment dashboards and AI review summaries
- Daily alerts for new negative reviews

## Pricing
**$0.25 per 1,000 reviews.** Pay only for what you get.

## Input example
```json
{
  "apps": [
    "https://play.google.com/store/apps/details?id=com.spotify.music"
  ],
  "maxReviewsPerApp": 1000,
  "sortBy": "newest",
  "language": "en",
  "country": "us",
  "includeAppDetails": true
}
```

## Run it via API, schedules or AI agents
- **API:** `POST https://api.apify.com/v2/acts/jbyzl~google-play-reviews-scraper/run-sync-get-dataset-items?token=YOUR_TOKEN` with the input above as the JSON body. Results come back as JSON; CSV, Excel and XML exports are available from the dataset.
- **Schedules & integrations:** run it daily or hourly with Apify Schedules and send results to Google Sheets, Slack, Zapier, Make or n8n.
- **AI agents (MCP):** available through the Apify MCP server (`mcp.apify.com`), so Claude, ChatGPT, Cursor and other agents can call it as a tool: ask your agent to use `jbyzl/google-play-reviews-scraper`.

## FAQ
**Do I need an API key?**
No login or key needed.

**Can I get developer replies?**
Yes, each review includes the developer's reply and reply date where there is one.

**Can I choose the language?**
Yes, set the language and country to get reviews from that market.

## Also known as
Google Play Store review scraper, Android app reviews export, Play Store ratings to CSV/JSON, developer replies, app review analysis.
