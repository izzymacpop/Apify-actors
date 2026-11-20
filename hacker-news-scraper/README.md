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
