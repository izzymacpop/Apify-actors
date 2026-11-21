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

## Input example
```json
{
  "searchPosts": [
    "#history"
  ],
  "sort": "latest",
  "profileData": [
    "details",
    "posts"
  ],
  "maxItems": 200
}
```

## Run it via API, schedules or AI agents
- **API:** `POST https://api.apify.com/v2/acts/jbyzl~bluesky-scraper/run-sync-get-dataset-items?token=YOUR_TOKEN` with the input above as the JSON body. Results come back as JSON; CSV, Excel and XML exports are available from the dataset.
- **Schedules & integrations:** run it daily or hourly with Apify Schedules and send results to Google Sheets, Slack, Zapier, Make or n8n.
- **AI agents (MCP):** available through the Apify MCP server (`mcp.apify.com`), so Claude, ChatGPT, Cursor and other agents can call it as a tool: ask your agent to use `jbyzl/bluesky-scraper`.

## FAQ
**Do I need a Bluesky account?**
No. It uses Bluesky's public AppView API.

**Can I search hashtags?**
Yes, add terms like #history to the search box, with optional date and language filters.

**Can I export followers?**
Yes, choose followers or following in the profile options.

## Also known as
Bluesky post scraper, Bluesky search API, bsky.app profile and follower export, Bluesky hashtag monitoring, social listening data.
