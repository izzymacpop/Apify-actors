# Substack Scraper: posts, likes, comments and full text

Scrape **Substack newsletters**: every post's title, subtitle, date, author, likes, comments, restacks, word count, paid/free status and full text. Works with custom domains too. Updated for Substack's **new cursor-based archive API (2026)**.

## Features
- Add newsletter URLs, subdomains or custom domains.
- Or **search all of Substack** by keyword to find posts on any topic.
- Full post text (HTML and plain text); paid posts include the free preview.
- Filter by date and free-only.
- Engagement metrics: likes (reactions), comments, restacks.

## Output example
```json
{
  "publication": "www.lennysnewsletter.com",
  "title": "35 premium tools free for a year",
  "subtitle": "...",
  "author": "Lenny Rachitsky",
  "publishedAt": "2026-11-17T18:02:02.477Z",
  "audience": "everyone",
  "likes": 220, "comments": 13, "restacks": 9, "wordcount": 1758,
  "url": "https://www.lennysnewsletter.com/p/35-premium-tools-free-for-a-yearnow",
  "contentText": "..."
}
```

## Use cases
- Content research and finding top-performing topics in your niche
- Competitor newsletter monitoring
- Building datasets for AI summarisation or RAG
- Finding writers and sponsorship leads

## Pricing
**$2 per 1,000 posts.**

## Input example
```json
{
  "publications": [
    "https://www.lennysnewsletter.com"
  ],
  "maxPostsPerSource": 50,
  "includeContent": true
}
```

## Run it via API, schedules or AI agents
- **API:** `POST https://api.apify.com/v2/acts/jbyzl~substack-scraper/run-sync-get-dataset-items?token=YOUR_TOKEN` with the input above as the JSON body. Results come back as JSON; CSV, Excel and XML exports are available from the dataset.
- **Schedules & integrations:** run it daily or hourly with Apify Schedules and send results to Google Sheets, Slack, Zapier, Make or n8n.
- **AI agents (MCP):** available through the Apify MCP server (`mcp.apify.com`), so Claude, ChatGPT, Cursor and other agents can call it as a tool: ask your agent to use `jbyzl/substack-scraper`.

## FAQ
**Does it work with custom domains?**
Yes, e.g. lennysnewsletter.com works as well as name.substack.com.

**Can I get paid posts?**
You get metadata for paid posts (title, date, likes). Full text is only available for free posts.

**Can I search all of Substack?**
Yes, add search terms to find posts and publications across Substack.

## Also known as
Substack API scraper, Substack newsletter export, Substack posts to JSON/CSV, Substack search, newsletter research and creator analysis.
