# Podcast Scraper: Apple Podcasts search, RSS, owner emails & episodes

Find podcasts by keyword and get **podcast details, owner contact email** (from the public RSS feed), activity status and episodes. Built for **podcast guest outreach**, sponsorship prospecting and research.

## Features
- Search the Apple Podcasts directory by keyword and country.
- Or add Apple Podcasts URLs or RSS feeds directly.
- Owner name and email as published in the podcast's RSS feed (`itunes:owner`).
- Episode count, first and last episode date, and an **activity filter** to skip dead shows.
- Optional episodes: title, date, duration, audio URL, description.

## Output example (podcast)
```json
{
  "type": "podcast",
  "name": "The Rest Is History",
  "author": "Goalhanger",
  "genre": "History",
  "appleId": 1537788786,
  "appleUrl": "https://podcasts.apple.com/gb/podcast/...",
  "feedUrl": "https://feeds.megaphone.fm/...",
  "website": "https://...",
  "ownerName": "Goalhanger",
  "ownerEmail": "contact@example.com",
  "episodeCount": 612,
  "lastEpisodeAt": "2026-11-19T22:00:00+00:00",
  "explicit": false,
  "language": "en"
}
```

## Use cases
- Pitching yourself or clients as a podcast guest
- Finding podcasts to sponsor or advertise on
- Market research on podcast niches

## Pricing
**$3 per 1,000 podcasts** and **$0.50 per 1,000 episodes.**

## Note
Emails are only those publicly listed by podcast owners in their RSS feeds. Use them responsibly and follow local email-marketing laws (e.g. GDPR/PECR in the UK and EU).

## Input example
```json
{
  "searchTerms": [
    "true crime"
  ],
  "country": "us",
  "maxPodcastsPerSearch": 50,
  "includeOwnerContact": true
}
```

## Run it via API, schedules or AI agents
- **API:** `POST https://api.apify.com/v2/acts/jbyzl~podcast-scraper/run-sync-get-dataset-items?token=YOUR_TOKEN` with the input above as the JSON body. Results come back as JSON; CSV, Excel and XML exports are available from the dataset.
- **Schedules & integrations:** run it daily or hourly with Apify Schedules and send results to Google Sheets, Slack, Zapier, Make or n8n.
- **AI agents (MCP):** available through the Apify MCP server (`mcp.apify.com`), so Claude, ChatGPT, Cursor and other agents can call it as a tool: ask your agent to use `jbyzl/podcast-scraper`.

## FAQ
**Where do the emails come from?**
Only from the owner email that podcasters publish in their public RSS feed (itunes:owner).

**Can I skip dead podcasts?**
Yes, set 'Only active podcasts' to e.g. 60 days.

**Can I get episodes too?**
Yes, set how many recent episodes to save per podcast.

## Also known as
Apple Podcasts scraper, podcast email finder, podcast contact list, podcast guest outreach leads, podcast RSS scraper, alternative to Podchaser and Rephonic exports.
