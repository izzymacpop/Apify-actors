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
