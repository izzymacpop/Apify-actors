# UK Used Car Deals Finder: Gumtree + Deal Score

Search **Gumtree UK** for used **cars, vans, motorbikes and campervans** by town, make, model and price, and see instantly **which ones are cheap**. Every listing gets a **deal score**: how far its price is below the median of similar vehicles (same make and model, year ±1) in your search. Results are sorted best deal first.

## What you get
- Title, **price**, **year**, **mileage**, fuel, transmission, engine size
- **Private or trade seller**
- Make, model, location and listing link, photo
- **Deal score** (% below similar listings), median similar price and how many similar listings it was compared against

## Who uses it
- **Car traders and flippers** hunting underpriced private sales
- **Dealers** checking local prices before buying stock or pricing a car
- **Buyers** comparing what a fair price is
- **Price-comparison sites, valuation tools and researchers**

## Input example
```json
{
  "locations": ["Leeds", "Bradford"],
  "searchTerms": ["ford fiesta", "vw golf"],
  "maxPrice": 8000,
  "privateSellersOnly": true,
  "onlyDealsBelowMedianPercent": 15
}
```

## Output example
```json
{
  "title": "FORD FIESTA 1.4 ZETEC 93k MOT OCTOBER 2027 5 DOOR 12 REG",
  "price": 1650,
  "year": 2012,
  "mileage": 93000,
  "fuel": "Petrol",
  "engineCc": 1388,
  "sellerType": "Private",
  "make": "Ford",
  "model": "Fiesta",
  "location": "Roundhay, West Yorkshire",
  "dealScore": 62.9,
  "medianSimilarPrice": 4445,
  "similarListings": 12,
  "url": "https://www.gumtree.com/p/ford/ford-fiesta-1.4-zetec-93k-mot-october-2027-5-door-12-reg/1804608546"
}
```

## Pricing
**$1.50 per 1,000 listings.**

## Tips
- **Schedule it every hour or day** with *Private sellers only* and a deal threshold, and connect a webhook or Telegram/Slack integration to get alerted to bargains first.
- The deal score is relative to what this run finds. Search wider areas or more pages for more reliable scores.
- A very high deal score can mean spares/repairs, high mileage or a write-off: always check the listing.

## Use it from your code, Make, Zapier or an AI agent
Call it from the Apify API, schedule it, or connect it to Make, Zapier, n8n or any MCP client (Claude, Cursor) via the Apify MCP server.

## FAQ
**AutoTrader?** Not included. This Actor focuses on Gumtree, where most private sellers list.

*Also known as: Gumtree car scraper, used car deals UK, cheap cars near me, car flipping tool, Gumtree vans scraper, used car price checker, private seller cars UK.*
