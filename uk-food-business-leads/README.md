# UK Takeaway & Restaurant Leads: New Openings + Hygiene Ratings

Get a list of **every takeaway, restaurant, cafe, pub or food shop** in any UK town or postcode, straight from the official **Food Standards Agency** register (the same data behind the green hygiene rating stickers). Every food business in the UK has to register, so this is the most complete list there is: far more than Just Eat, Deliveroo or Google Maps.

## Why it's different
- **New openings**: tick *Only NEW businesses* to get food businesses that have just registered and are still awaiting their first inspection. Reach them before your competitors do.
- **Low hygiene ratings**: set *Max hygiene rating* to 2 to find businesses that need help (food safety consultants, training, pest control).
- Official government data: reliable, no blocking, and it covers England, Wales, Scotland and Northern Ireland.

## What you get
Business name, type, full address, **postcode**, town, council, **hygiene rating**, inspection date, **GPS coordinates**, detailed scores, rating page link, and whether it's a new business.

## Who uses it
- **EPOS, card machine and delivery app** sales teams
- **Food packaging, wholesale and drinks** suppliers
- **Marketing agencies, web designers and menu printers**
- **Food safety consultants, trainers and pest control**
- Shopfitters, signage, commercial cleaning, waste and insurance

## Input example
```json
{
  "locations": ["Leeds", "Bradford", "M1"],
  "businessTypes": ["takeaway", "restaurant"],
  "onlyNewBusinesses": true
}
```

## Output example
```json
{
  "name": "953 Pizza",
  "businessType": "Takeaway/sandwich shop",
  "address": "Bingley Arms, 37 Church Lane, Bardsey, Leeds",
  "postcode": "LS17 9DR",
  "localAuthority": "Leeds",
  "hygieneRating": "AwaitingInspection",
  "isNewBusiness": true,
  "latitude": 53.8816,
  "longitude": -1.4484,
  "ratingUrl": "https://ratings.food.gov.uk/business/1937336"
}
```

## Pricing
**$1.50 per 1,000 businesses.** Every takeaway in a big city costs well under $1.

## Tips
- **Schedule it weekly** with *Only NEW businesses* to get a fresh list of new openings every Monday.
- Use postcode districts (e.g. `E1`, `RM10`) for tight areas, or towns and cities for wide ones.
- Phone numbers are rarely in the official register. Pair the names with a Google Maps scraper if you need phones and websites.

## Use it from your code, Make, Zapier or an AI agent
Run it through the Apify API, schedule it with Apify Schedules, send results to Google Sheets, or call it from Make, Zapier, n8n or any MCP client (Claude, Cursor) via the Apify MCP server.

## FAQ
**Where does the data come from?** The Food Standards Agency's public Food Hygiene Rating Scheme API (Open Government Licence).

**How fresh is it?** Councils update it continuously; each run pulls live data.

*Also known as: UK takeaway list, restaurant leads UK, new restaurant openings, food hygiene rating scraper, FSA ratings API, Just Eat alternative, UK cafe database, new business leads UK.*
