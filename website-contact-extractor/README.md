# Website Contact & Social Links Extractor

Give it a list of websites and get back **emails, phone numbers and social media profiles** for each one: Facebook, Instagram, LinkedIn, X/Twitter, TikTok, YouTube, Pinterest, Threads, Bluesky and WhatsApp. One clean row per website, ready for your CRM.

## How it works
For each site it reads the homepage and the pages most likely to hold contact details (Contact, About, Team, Impressum/Legal, Privacy), up to your page limit. It decodes obfuscated emails (`name [at] domain [dot] com`, Cloudflare-protected emails) and validates phone numbers with Google's libphonenumber.

## Output example
```json
{
  "website": "https://example.co.uk",
  "domain": "example.co.uk",
  "companyName": "Example Ltd",
  "emails": ["hello@example.co.uk", "support@example.co.uk"],
  "phones": ["+44 20 7946 0000"],
  "facebook": ["https://www.facebook.com/example"],
  "instagram": ["https://www.instagram.com/example"],
  "linkedin": ["https://www.linkedin.com/company/example"],
  "twitter": ["https://x.com/example"],
  "tiktok": [], "youtube": [], "pinterest": [], "threads": [], "bluesky": [], "whatsapp": [],
  "pagesScanned": ["https://example.co.uk/", "https://example.co.uk/contact"]
}
```

## Use cases
- Enrich lead lists from Google Maps, directories or Companies House with emails and socials
- Build outreach lists for agencies, B2B sales and recruiters
- Check competitors' social presence

## Pricing
**$3 per 1,000 websites**, charged only for websites where at least one contact was found.

## Responsible use
Only publicly displayed contact details are collected. Follow GDPR/PECR and anti-spam laws when contacting people.

## Input example
```json
{
  "websites": [
    "https://monzo.com"
  ],
  "maxPagesPerSite": 8,
  "phoneRegion": "GB"
}
```

## Run it via API, schedules or AI agents
- **API:** `POST https://api.apify.com/v2/acts/jbyzl~website-contact-extractor/run-sync-get-dataset-items?token=YOUR_TOKEN` with the input above as the JSON body. Results come back as JSON; CSV, Excel and XML exports are available from the dataset.
- **Schedules & integrations:** run it daily or hourly with Apify Schedules and send results to Google Sheets, Slack, Zapier, Make or n8n.
- **AI agents (MCP):** available through the Apify MCP server (`mcp.apify.com`), so Claude, ChatGPT, Cursor and other agents can call it as a tool: ask your agent to use `jbyzl/website-contact-extractor`.

## FAQ
**Which pages does it check?**
The homepage plus likely contact, about and team pages, up to your page limit.

**Am I charged for sites with no contacts?**
No. You're only charged for websites where at least one email, phone or social link was found.

**Does it find hidden emails?**
It decodes common obfuscation such as Cloudflare email protection.

## Also known as
website email scraper, contact details extractor, phone number scraper, social media links finder, lead generation from a list of websites, alternative to Hunter-style domain search.
