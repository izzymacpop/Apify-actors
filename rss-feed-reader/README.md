# RSS Feed Reader & Feed Finder

Turn any **RSS or Atom feed, or just a website URL**, into clean, structured JSON. Feeds are discovered automatically, and every format (RSS 0.9–2.0, Atom, RDF, podcast feeds) is normalised into one schema.

## Features
- Paste feed URLs **or website URLs**: the Actor finds the site's feeds for you.
- One consistent output: title, link, date (ISO), author, summary, full content, categories, image, enclosure.
- Filter by date and keywords. Great for scheduled monitoring.
- Handles broken and non-standard feeds gracefully.

## Output example
```json
{
  "feedTitle": "BBC News", "feedUrl": "https://feeds.bbci.co.uk/news/rss.xml",
  "title": "Headline...", "url": "https://www.bbc.co.uk/news/articles/...",
  "publishedAt": "2026-11-20T21:04:00+00:00", "author": null,
  "summary": "...", "categories": [], "imageUrl": "https://ichef.bbci.co.uk/..."
}
```

## Use cases
- News and blog monitoring, content aggregation, AI newsletters
- Competitor content tracking
- Feeding Slack, Google Sheets or databases via schedules and webhooks

## Pricing
**$0.50 per 1,000 items.**

## Input example
```json
{
  "urls": [
    "https://www.bbc.co.uk/news",
    "https://hnrss.org/frontpage"
  ],
  "maxItemsPerFeed": 100,
  "includeContent": true
}
```

## Run it via API, schedules or AI agents
- **API:** `POST https://api.apify.com/v2/acts/jbyzl~rss-feed-reader/run-sync-get-dataset-items?token=YOUR_TOKEN` with the input above as the JSON body. Results come back as JSON; CSV, Excel and XML exports are available from the dataset.
- **Schedules & integrations:** run it daily or hourly with Apify Schedules and send results to Google Sheets, Slack, Zapier, Make or n8n.
- **AI agents (MCP):** available through the Apify MCP server (`mcp.apify.com`), so Claude, ChatGPT, Cursor and other agents can call it as a tool: ask your agent to use `jbyzl/rss-feed-reader`.

## FAQ
**I don't know the feed URL. Can I paste a website?**
Yes. Paste the site URL and the tool finds its feeds automatically.

**Can I get the full article text?**
Yes, where the feed includes full content.

**Can I monitor feeds?**
Yes, schedule it and use the date filter to only get new items.

## Also known as
RSS feed reader API, RSS to JSON, Atom feed parser, automatic feed finder from website URL, news and blog monitoring.
