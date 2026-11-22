# UK Tradespeople Leads: TrustATrader + Bark

Get **lists of UK tradespeople with phone numbers** for any trade and any town, from two directories in one run. Plumbers in Manchester, electricians in Leeds, roofers in Essex: type the trade and the place, and get a clean, de-duplicated spreadsheet.

## What you get
- **Business name** and **phone numbers** (TrustATrader)
- **Rating** and **number of reviews**
- **Town**, **area covered** and postcode where listed
- Business description, logo and **profile link**
- Which directory the lead came from

## Who uses it
- **Marketing agencies and web designers** selling websites, SEO or ads to trades
- **Software companies** selling job, quoting and booking apps to tradespeople
- **Insurance, van leasing and merchant** sales teams
- **Homeowners and letting agents** comparing well-reviewed local trades

## Input example
```json
{
  "trades": ["plumber", "electrician", "roofer"],
  "locations": ["Manchester", "Leeds", "SE1"],
  "maxResultsPerSearch": 100,
  "sources": ["trustatrader", "bark"],
  "onlyWithPhone": true
}
```

## Output example
```json
{
  "source": "TrustATrader",
  "name": "AK Plumbing & Heating Services",
  "trade": "plumber",
  "searchLocation": "London",
  "phones": ["07547 107 770"],
  "rating": 4.98,
  "reviewCount": 194,
  "town": "London",
  "areaCovered": "Enfield and All Surrounding Areas",
  "profileUrl": "https://www.trustatrader.com/traders/ak-plumbing-heating-services-..."
}
```

## Pricing
**$2 per 1,000 leads.** You only pay for leads saved, so a list of 500 plumbers costs about $1.

## Tips
- Run many trades × many towns in one go; duplicates across searches are removed.
- Bark only has pages for bigger towns and cities; TrustATrader works for any town or postcode.
- Schedule it weekly to catch new businesses, and send results to Google Sheets with Apify integrations.

## Use it from your code, Make, Zapier or an AI agent
Run it through the Apify API, schedule it in Apify Schedules, or connect it to Make, Zapier, n8n or any MCP client (Claude, Cursor) through the Apify MCP server.

## FAQ
**Is this legal?** It collects business information that is publicly listed on the directories. Use it in line with UK GDPR and PECR, for example when contacting sole traders.

**Can I get emails?** The directories don't list emails publicly. Pair this with a website contact extractor if the business has a website.

*Also known as: UK tradesman leads, plumber leads UK, electrician list, builders database, TrustATrader scraper, Bark scraper, Checkatrade alternative, UK trades directory scraper.*
