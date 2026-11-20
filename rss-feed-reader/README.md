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
