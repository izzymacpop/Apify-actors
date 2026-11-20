# Google Play Reviews Scraper

Get **Google Play Store reviews** for any Android app: rating, text, thumbs-up count, app version, date, and the developer's reply. Thousands of reviews per app, with no login or proxies.

## Features
- Input Play Store URLs or package IDs (e.g. `com.spotify.music`).
- Sort by newest or most relevant; choose language and country.
- Filter by star rating, or stop at a date for incremental daily runs.
- Developer replies included, which is great for support-quality analysis.
- Optional app details: title, developer, rating, total ratings, installs, genre.

## Output example
```json
{
  "appId": "com.spotify.music", "appName": "Spotify: Music and Podcasts",
  "reviewId": "b6a1...", "rating": 4, "text": "Love it but...", "thumbsUp": 12,
  "appVersion": "9.0.92.1015", "userName": "A Google user", "date": "2026-11-19T22:09:04",
  "replyText": "Hey! Thanks for...", "repliedAt": "2026-11-20T08:00:00"
}
```

## Use cases
- App competitor research and feature-gap analysis
- Sentiment dashboards and AI review summaries
- Daily alerts for new negative reviews

## Pricing
**$0.25 per 1,000 reviews.** Pay only for what you get.
