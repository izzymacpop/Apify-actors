# App Store Reviews Scraper (iPhone & iPad)

Download **App Store reviews** for any iOS app: star rating, title, text, author, app version, votes and date, across as many countries as you like. Uses Apple's official public review feed, so it is fast and reliable, with no login or proxies.

## Features
- Input App Store URLs, numeric IDs, **or just app names** (it finds the app for you).
- Multiple countries per run: reviews are stored per country, so add `us, gb, ca, au, ie, nz` for more coverage.
- Filter by star rating (e.g. only 1–2 star reviews for complaint analysis).
- Optional app details: name, developer, average rating, total ratings, price, genre.

## Output example
```json
{
  "appId": "324684580", "appName": "Spotify: Music and Podcasts", "country": "gb",
  "reviewId": "14774960554", "rating": 5, "title": "Is cool", "text": "Yep",
  "author": "Stick bot fan", "appVersion": "9.1.98", "voteCount": 0, "voteSum": 0,
  "date": "2026-11-10T13:21:30-07:00", "url": "https://apps.apple.com/gb/app/id324684580?see-all=reviews"
}
```

## Use cases
- Competitor and product research, feature requests, bug reports
- Sentiment analysis and AI summaries of what users love or hate
- Monitoring new 1-star reviews after a release (schedule daily runs)

## Pricing
**$0.25 per 1,000 reviews.** You only pay for reviews delivered.

## Limits
Apple's public feed returns up to the 500 most recent reviews per app per country. Add more countries to collect more.

## Input example
```json
{
  "apps": [
    "https://apps.apple.com/gb/app/spotify-music-and-podcasts/id324684580"
  ],
  "countries": [
    "gb",
    "us"
  ],
  "maxReviewsPerCountry": 500,
  "sortBy": "mostrecent",
  "includeAppDetails": true
}
```

## Run it via API, schedules or AI agents
- **API:** `POST https://api.apify.com/v2/acts/jbyzl~app-store-reviews-scraper/run-sync-get-dataset-items?token=YOUR_TOKEN` with the input above as the JSON body. Results come back as JSON; CSV, Excel and XML exports are available from the dataset.
- **Schedules & integrations:** run it daily or hourly with Apify Schedules and send results to Google Sheets, Slack, Zapier, Make or n8n.
- **AI agents (MCP):** available through the Apify MCP server (`mcp.apify.com`), so Claude, ChatGPT, Cursor and other agents can call it as a tool: ask your agent to use `jbyzl/app-store-reviews-scraper`.

## FAQ
**Do I need an API key or login?**
No. It uses Apple's public customer-reviews feed.

**How many reviews can I get?**
Apple's public feed returns up to 500 of the most recent reviews per app per country. Add more countries to get more.

**Can I get only bad reviews?**
Yes, use the star filter to keep 1-2 star reviews for complaint analysis.

## Also known as
Apple App Store review scraper, iOS app reviews export, app ratings to CSV/JSON, alternative to AppFollow and Appbot exports.
