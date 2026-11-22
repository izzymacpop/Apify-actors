# UK Events Finder: Skiddle + Eventbrite + DICE

Get **what's on in any UK city** from three of the biggest UK ticket sites in one clean, **de-duplicated** list. Gigs, club nights, comedy, theatre, food and drink, family days out and business events, with dates, venues, postcodes, prices, line-ups and ticket links.

## What you get
- Event name, category and **start/end date-time**
- **Venue**, address, town, **postcode** and GPS coordinates
- **Price from** (where listed) and ticket status
- **Line-up / performers** and organiser (Skiddle)
- Description, image and **ticket link**
- Which site it came from

## Who uses it
- **"What's on" websites, apps and newsletters** (local guides, student sites, city blogs)
- **Promoters and venues** watching the competition and spotting clashes
- **Hotels, bars and restaurants** planning around busy nights
- **Taxi, transport and security** firms planning staff
- Brands and agencies looking for events to sponsor
- AI agents answering "what's on this weekend?"

## Input example
```json
{
  "cities": ["Manchester", "Leeds", "Liverpool"],
  "categories": ["all", "gigs", "clubs", "comedy"],
  "nextDays": 14,
  "keywords": ["techno", "drum and bass"]
}
```

## Output example
```json
{
  "source": "Skiddle",
  "name": "Crossy Presents: The Breakthrough | Leeds",
  "category": "all",
  "startDate": "2026-11-21T22:00:00+00:00",
  "venue": "Beaver Works",
  "address": "36 Whitehouse Street",
  "town": "Leeds",
  "postcode": "LS10 1AD",
  "priceFrom": 10.0,
  "performers": ["Inja", "Trafic MC", "Demolition Man", "Crossy", "Jman"],
  "organizer": "Mervyn Entertainment Ltd.",
  "url": "https://www.skiddle.com/whats-on/Leeds/Beaver-Works/..."
}
```

## Pricing
**$1 per 1,000 events.** A full city costs a few cents.

## Tips
- Pick several categories to get more events: each one is a separate listing on the ticket sites.
- **Schedule it daily or weekly** and send results to Google Sheets, Airtable or your website.
- Duplicates across Skiddle, Eventbrite and DICE are removed automatically.

## Use it from your code, Make, Zapier or an AI agent
Run it via the Apify API, schedule it, or connect it to Make, Zapier, n8n or any MCP client (Claude, Cursor) through the Apify MCP server.

## FAQ
**How many events per city?** Usually 100–300 for big cities with the default categories.

**Other countries?** UK only for now.

*Also known as: what's on API UK, UK events scraper, Skiddle scraper, Eventbrite scraper, DICE scraper, gigs near me data, nightlife events API, events this weekend UK.*
