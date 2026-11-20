# Bluesky Scraper: posts, search, profiles & followers

Scrape **Bluesky** (bsky.app) with no login: search posts by keyword or hashtag, get any profile's posts, profile details, followers and following, or search users. Uses Bluesky's official public AT Protocol API, so it is fast and stable.

## Features
- **Post search** with Bluesky syntax (`#tag`, `from:handle`, `"exact phrase"`), latest or top, date range, language.
- **Profiles**: details (followers, following, posts count, bio, created date), posts, followers, following.
- **User search** by name or bio keywords.
- Engagement on every post: likes, reposts, replies, quotes. Plus links, images, hashtags and mentions.

## Output example (post)
```json
{
  "type": "post", "uri": "at://did:plc:.../app.bsky.feed.post/3n2r...",
  "url": "https://bsky.app/profile/someone.bsky.social/post/3n2r...",
  "authorHandle": "someone.bsky.social", "authorName": "Someone",
  "text": "Today in #history...", "createdAt": "2026-11-20T09:12:00.000Z",
  "likes": 120, "reposts": 14, "replies": 9, "quotes": 2,
  "hashtags": ["history"], "links": [], "images": ["https://cdn.bsky.app/..."], "lang": ["en"]
}
```

## Use cases
- Social listening and brand monitoring as people move to Bluesky
- Influencer discovery and audience research
- Datasets for sentiment and trend analysis

## Pricing
**$0.50 per 1,000 items** (posts, profiles or followers).
