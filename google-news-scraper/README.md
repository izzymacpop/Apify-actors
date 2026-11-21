# Google News Scraper with real article URLs

Collect **Google News articles** for any keyword or topic, with each article's **real publisher URL** instead of the scrambled `news.google.com/rss/articles/...` link most scrapers give you.

## Features
- Search any keyword, with Google operators (`site:`, `OR`, quotes, `-exclude`).
- Topic headlines: World, Business, Technology, Sports, Science, Health and more.
- 13 editions: UK, US, Ireland, Australia, Canada, India, Germany, France and others.
- Time filter: past hour, day, week, month or year.
- **Real article URLs**, decoded automatically.
- Optional: open each article for its description, image and author.

## Output example
```json
{
  "query": "bitcoin",
  "title": "Bitcoin suffered identical sell-off pattern ahead of Anthropic, SpaceX IPOs",
  "source": "CNBC",
  "sourceUrl": "https://www.cnbc.com",
  "publishedAt": "2026-11-20T14:18:44+00:00",
  "url": "https://www.cnbc.com/2026/11/20/bitcoin-pre-ipo-selloff-pattern-anthropic-spacex.html",
  "googleNewsUrl": "https://news.google.com/rss/articles/CBMi..."
}
```

## Use cases
- Brand and competitor monitoring (schedule hourly or daily)
- PR and media tracking, news alerts to Slack or email via webhooks
- Feeding AI summaries, newsletters and research datasets

## Pricing
**$2 per 1,000 articles**, URL decoding included.

## Notes
Google News returns up to about 100 results per query. Use several narrower queries or time filters to collect more.

## Input example
```json
{
  "queries": [
    "artificial intelligence"
  ],
  "edition": "en-GB:GB",
  "timeframe": "any",
  "maxArticlesPerQuery": 100,
  "decodeUrls": true
}
```

## Run it via API, schedules or AI agents
- **API:** `POST https://api.apify.com/v2/acts/jbyzl~google-news-scraper/run-sync-get-dataset-items?token=YOUR_TOKEN` with the input above as the JSON body. Results come back as JSON; CSV, Excel and XML exports are available from the dataset.
- **Schedules & integrations:** run it daily or hourly with Apify Schedules and send results to Google Sheets, Slack, Zapier, Make or n8n.
- **AI agents (MCP):** available through the Apify MCP server (`mcp.apify.com`), so Claude, ChatGPT, Cursor and other agents can call it as a tool: ask your agent to use `jbyzl/google-news-scraper`.

## FAQ
**Why are the URLs different from Google News links?**
Google News wraps every article in a news.google.com redirect. This tool decodes it to the real publisher URL, so you can open or scrape the article directly.

**Which countries are supported?**
13 editions including UK, US, Canada, Australia, India, Ireland, Germany, France and Spain.

**Can I get only today's news?**
Yes, set the time filter to the past hour, day or week.

## Also known as
Google News API alternative, Google News RSS scraper, news monitoring, media monitoring, decode news.google.com links to publisher URLs.
