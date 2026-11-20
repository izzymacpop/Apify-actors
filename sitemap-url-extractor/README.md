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
