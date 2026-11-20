"""RSS Feed Reader & Feed Finder."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from time import mktime
from urllib.parse import urljoin, urlparse

import feedparser
import httpx
from apify import Actor
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
      "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/html;q=0.8, */*;q=0.5"}
FEED_TYPES = ("application/rss+xml", "application/atom+xml", "application/rdf+xml", "application/feed+json", "application/xml", "text/xml")


async def get(c, url):
    for attempt in range(3):
        try:
            r = await c.get(url)
            if r.status_code == 429 or r.status_code >= 500:
                await asyncio.sleep(2 * (attempt + 1)); continue
            return r
        except httpx.HTTPError:
            await asyncio.sleep(2 * (attempt + 1))
    return None


def looks_like_feed(r):
    ct = r.headers.get("content-type", "").lower()
    head = r.text[:600].lower()
    return any(t in ct for t in ("rss", "atom", "xml")) or "<rss" in head or "<feed" in head or "<rdf:rdf" in head


async def discover(c, url, all_feeds):
    r = await get(c, url)
    if not r or r.status_code >= 400:
        return [], None
    if looks_like_feed(r):
        return [str(r.url)], r
    soup = BeautifulSoup(r.text[:500000], "html.parser")
    feeds = []
    for l in soup.find_all("link", rel=lambda v: v and "alternate" in v):
        if (l.get("type") or "").lower() in FEED_TYPES and l.get("href"):
            feeds.append(urljoin(str(r.url), l["href"]))
    if not feeds:  # common fallbacks
        base = f"{urlparse(str(r.url)).scheme}://{urlparse(str(r.url)).netloc}"
        here = str(r.url).split("?")[0].rstrip("/")
        cands = [here + "/rss", here + "/feed"] if here != base else []
        cands += [base + p for p in ("/feed", "/rss", "/rss.xml", "/feed.xml", "/atom.xml", "/index.xml", "/blog/feed")]
        for cand in dict.fromkeys(cands):
            t = await get(c, cand)
            if t and t.status_code == 200 and looks_like_feed(t):
                feeds.append(str(t.url)); break
    feeds = list(dict.fromkeys(feeds))
    return (feeds if all_feeds else feeds[:1]), None


def when(e):
    t = e.get("published_parsed") or e.get("updated_parsed")
    if t:
        try:
            return datetime.fromtimestamp(mktime(t), tz=timezone.utc)
        except Exception:
            return None
    return None


def strip(html):
    if not html:
        return None
    return re.sub(r"\s+", " ", BeautifulSoup(html, "html.parser").get_text(" ")).strip() or None


def image_of(e):
    for k in ("media_content", "media_thumbnail"):
        for m in e.get(k) or []:
            if m.get("url"):
                return m["url"]
    for enc in e.get("enclosures") or []:
        if (enc.get("type") or "").startswith("image") and enc.get("href"):
            return enc["href"]
    for l in e.get("links") or []:
        if (l.get("type") or "").startswith("image"):
            return l.get("href")
    m = re.search(r'<img[^>]+src="([^"]+)"', (e.get("summary") or "") + str(e.get("content") or ""))
    return m.group(1) if m else None


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        urls = [u.strip() for u in inp.get("urls") or [] if u and u.strip()]
        if not urls:
            await Actor.fail(status_message="Add at least one feed or website URL."); return
        cap = int(inp.get("maxItemsPerFeed") or 100)
        kws = [k.lower() for k in inp.get("keywords") or [] if k]
        content = inp.get("includeContent", True)
        after = None
        if inp.get("publishedAfter"):
            try:
                after = datetime.fromisoformat(inp["publishedAfter"].replace("Z", "+00:00"))
                after = after if after.tzinfo else after.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        total = 0
        async with httpx.AsyncClient(headers=UA, timeout=30, follow_redirects=True) as c:
            for u in urls:
                if "://" not in u:
                    u = "https://" + u
                feeds, first = await discover(c, u, inp.get("discoverAllFeeds", False))
                if not feeds:
                    Actor.log.warning(f"No feed found for {u}"); continue
                for f_url in feeds:
                    r = first if first is not None and str(first.url) == f_url else await get(c, f_url)
                    if not r or r.status_code >= 400:
                        Actor.log.warning(f"Could not load {f_url}"); continue
                    f = feedparser.parse(r.content)
                    ft = f.feed.get("title")
                    items = []
                    for e in f.entries:
                        d = when(e)
                        if after and d and d < after:
                            continue
                        summary = strip(e.get("summary"))
                        if kws and not any(k in ((e.get("title") or "") + " " + (summary or "")).lower() for k in kws):
                            continue
                        full = None
                        if content:
                            cs = e.get("content") or []
                            full = cs[0].get("value") if cs else e.get("summary")
                        enc = next((x for x in e.get("enclosures") or [] if x.get("href")), {})
                        items.append({
                            "feedTitle": ft, "feedUrl": f_url, "sourceInput": u,
                            "title": e.get("title"), "url": e.get("link"), "guid": e.get("id"),
                            "publishedAt": d.isoformat() if d else None, "author": e.get("author"),
                            "summary": (summary or "")[:2000] or None,
                            "contentHtml": full, "contentText": strip(full) if content else None,
                            "categories": [t.get("term") for t in e.get("tags") or [] if t.get("term")],
                            "imageUrl": image_of(e), "enclosureUrl": enc.get("href"), "enclosureType": enc.get("type"),
                            "scrapedAt": datetime.now(timezone.utc).isoformat()})
                        if len(items) >= cap:
                            break
                    if items:
                        res = await Actor.push_data(items, charged_event_name="item")
                        total += len(items)
                        if res and getattr(res, "event_charge_limit_reached", False):
                            Actor.log.info("Spending limit reached."); await Actor.set_status_message(f"Done: {total} items."); return
                    Actor.log.info(f"{f_url}: {len(items)} items")
        await Actor.set_status_message(f"Done: {total} items.")
