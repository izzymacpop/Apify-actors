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
