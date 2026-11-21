# Hacker News Scraper: search stories, comments, Show HN, Ask HN & jobs

Search and export **Hacker News** (news.ycombinator.com) via the official Algolia HN API. Get stories, comments, Show HN, Ask HN, "Who is hiring" jobs and polls, with points, comment counts, authors, URLs and optional full comment trees.

## Features
- Keyword search across all of HN history, sorted by relevance or date.
- Filter by type, author, minimum points and comments, and date range.
- Current **front page** in one click.
- Optional nested comment threads for each story.

## Output example
```json
{ "type": "story", "id": "41234567", "title": "Show HN: ...", "url": "https://example.com",
  "hnUrl": "https://news.ycombinator.com/item?id=41234567", "author": "pg", "points": 512,
  "comments": 230, "createdAt": "2026-11-20T15:00:00Z", "storyText": null }
```

## Use cases
- Product launch and brand monitoring on HN
- Lead generation from Show HN launches and hiring threads
- Datasets for tech trend analysis and AI training

## Pricing
**$0.50 per 1,000 items.**

## Input example
```json
{
  "searchQueries": [
    "Claude"
  ],
  "contentType": "story",
  "sortBy": "date",
  "maxItems": 200
}
```

## Run it via API, schedules or AI agents
- **API:** `POST https://api.apify.com/v2/acts/jbyzl~hacker-news-scraper/run-sync-get-dataset-items?token=YOUR_TOKEN` with the input above as the JSON body. Results come back as JSON; CSV, Excel and XML exports are available from the dataset.
- **Schedules & integrations:** run it daily or hourly with Apify Schedules and send results to Google Sheets, Slack, Zapier, Make or n8n.
- **AI agents (MCP):** available through the Apify MCP server (`mcp.apify.com`), so Claude, ChatGPT, Cursor and other agents can call it as a tool: ask your agent to use `jbyzl/hacker-news-scraper`.

## FAQ
**Is this the official API?**
It uses HN's official Algolia search API, so it is fast and stable.

**Can I get comment threads?**
Yes, turn on nested comments to save the full thread for each story.

**Can I monitor a keyword?**
Yes, search by keyword sorted by date and schedule the tool to run daily.

## Also known as
Hacker News API scraper, HN search, Show HN and Ask HN export, Hacker News comments to JSON/CSV, tech trend monitoring.
