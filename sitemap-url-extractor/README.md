# Sitemap URL Extractor: every page URL on a website

Get a **complete list of a website's pages** from its XML sitemaps: URL, last modified date, change frequency, priority, plus image and news tags. Finds sitemaps automatically via robots.txt and common locations, and follows sitemap indexes and gzipped sitemaps.

## Features
- Input a website **or** a sitemap URL.
- Auto-discovery: robots.txt, /sitemap.xml, /sitemap_index.xml, /wp-sitemap.xml and more.
- Follows nested sitemap indexes, .xml.gz and .txt sitemaps.
- Filters: include/exclude patterns (e.g. only `/products/`), modified-after date.
- Outputs lastmod, changefreq, priority, image URLs and Google News titles.

## Output example
```json
{ "site": "https://www.example.com", "url": "https://www.example.com/blog/post-1",
  "lastmod": "2026-11-18T10:00:00+00:00", "changefreq": "weekly", "priority": 0.8,
  "images": ["https://www.example.com/img/1.jpg"], "sitemap": "https://www.example.com/post-sitemap.xml" }
```

## Use cases
- SEO audits and content inventories
- Finding new pages and products on competitor sites (schedule and use the date filter)
- Seeding crawlers and AI/RAG pipelines with a site's URLs

## Pricing
**$0.20 per 1,000 URLs.** Fast, low compute.

## Input example
```json
{
  "urls": [
    "https://www.bbc.co.uk"
  ],
  "maxUrlsPerSite": 10000
}
```

## Run it via API, schedules or AI agents
- **API:** `POST https://api.apify.com/v2/acts/jbyzl~sitemap-url-extractor/run-sync-get-dataset-items?token=YOUR_TOKEN` with the input above as the JSON body. Results come back as JSON; CSV, Excel and XML exports are available from the dataset.
- **Schedules & integrations:** run it daily or hourly with Apify Schedules and send results to Google Sheets, Slack, Zapier, Make or n8n.
- **AI agents (MCP):** available through the Apify MCP server (`mcp.apify.com`), so Claude, ChatGPT, Cursor and other agents can call it as a tool: ask your agent to use `jbyzl/sitemap-url-extractor`.

## FAQ
**Do I need the sitemap URL?**
No. Paste the homepage and it finds sitemaps through robots.txt and common locations.

**Does it handle huge sites?**
Yes, it follows sitemap indexes and compressed .gz sitemaps. Set a max URL limit to control cost.

**Can I filter URLs?**
Yes, use include/exclude patterns and last-modified date filters.

## Also known as
XML sitemap extractor, sitemap to CSV, list all pages of a website, SEO audit URL list, robots.txt sitemap finder, sitemap index and .gz support.
