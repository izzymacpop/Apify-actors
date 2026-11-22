# UK Salon & Beauty Leads: Fresha + Treatwell

Find **hair salons, nail bars, barbers, beauty salons, spas, lash & brow studios and aesthetics clinics** anywhere in the UK, from the two biggest UK booking sites in one run. Get a clean, de-duplicated lead list with **phone numbers, websites and Instagram**.

## What you get
- Business name and type
- **Phone number** (most Fresha listings)
- Street address, area and **postcode**
- **Rating** and **review count**
- **Website, Instagram and Facebook** links
- Price range, GPS coordinates, booking page link and photo
- Which site the lead came from

## Who uses it
- **Salon software, booking app and card machine** sales teams
- **Beauty wholesalers** and product brands looking for stockists
- **Marketing agencies**, web designers and social media managers for salons
- Salon owners researching local competitors and prices
- Training academies and recruiters

## Input example
```json
{
  "locations": ["Manchester", "Leeds", "Dagenham, London"],
  "categories": ["hair", "nails", "barbers"],
  "sources": ["fresha", "treatwell"],
  "includeSubAreas": true,
  "onlyWithPhone": true
}
```

## Output example
```json
{
  "source": "Fresha",
  "name": "James at Haus of Harkin",
  "category": "hair",
  "businessType": "HairSalon",
  "phone": null,
  "address": "2 Middleton Road, Town End Works",
  "area": "Morley",
  "postcode": "LS27 8AP",
  "rating": 5,
  "reviewCount": 405,
  "priceRange": "From £23",
  "instagram": "https://www.instagram.com/jamesharkincolour",
  "website": "http://www.hausofharkin.co.uk",
  "bookingUrl": "https://www.fresha.com/a/james-at-haus-of-harkin-morley-2-middleton-road-imtr1clk"
}
```

## Pricing
**$2 per 1,000 salons.** You only pay for results saved.

## Tips
- Use a city for wide coverage, or `Area, City` (e.g. `Didsbury, Manchester`) for one neighbourhood.
- Turn on **Also search every neighbourhood** to get many more results for big cities.
- Schedule weekly and connect Google Sheets to spot new salons.

## Use it from your code, Make, Zapier or an AI agent
Call it from the Apify API, schedule it, or connect it to Make, Zapier, n8n or any MCP client (Claude, Cursor) through the Apify MCP server.

## FAQ
**Is the data public?** Yes: it's what the salons publish on their public booking pages. Use it in line with UK GDPR and PECR.

**Booksy?** Not yet. Ask in the Issues tab if you need it.

*Also known as: UK salon leads, hair salon list UK, nail salon database, barber shop leads, beauty salon scraper, Fresha scraper, Treatwell scraper, salon email list UK.*
