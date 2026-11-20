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
