"""Sitemap URL Extractor."""
from __future__ import annotations

import asyncio
import gzip
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import httpx
from apify import Actor

UA = {"User-Agent": "Mozilla/5.0 (compatible; sitemap-url-extractor/1.0; +https://apify.com)"}
COMMON = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", "/wp-sitemap.xml", "/sitemap.xml.gz", "/sitemap/sitemap.xml", "/sitemaps.xml"]


def local(tag):
    return tag.rsplit("}", 1)[-1]


async def fetch(c, url):
    for attempt in range(3):
        try:
            r = await c.get(url)
            if r.status_code == 429 or r.status_code >= 500:
                await asyncio.sleep(2 * (attempt + 1)); continue
            if r.status_code >= 400:
                return None
            body = r.content
            if url.endswith(".gz") or body[:2] == b"\x1f\x8b":
                try:
                    body = gzip.decompress(body)
                except OSError:
                    pass
            return body
        except httpx.HTTPError:
            await asyncio.sleep(2 * (attempt + 1))
    return None


async def find_sitemaps(c, site):
    p = urlparse(site)
    base = f"{p.scheme}://{p.netloc}"
    found = []
    robots = await fetch(c, base + "/robots.txt")
    if robots:
        found += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots.decode("utf-8", "ignore"))
    if not found:
        for path in COMMON:
            b = await fetch(c, base + path)
            if b and (b"<urlset" in b[:3000] or b"<sitemapindex" in b[:3000]):
                found.append(base + path); break
    return list(dict.fromkeys(found))


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        urls = [u.strip() for u in inp.get("urls") or [] if u and u.strip()]
        if not urls:
            await Actor.fail(status_message="Add at least one website or sitemap URL."); return
        inc = [re.compile(p, re.I) for p in inp.get("includePatterns") or [] if p]
        exc = [re.compile(p, re.I) for p in inp.get("excludePatterns") or [] if p]
        after = parse_date(inp.get("modifiedAfter")) if inp.get("modifiedAfter") else None
        cap = int(inp.get("maxUrlsPerSite") or 10000)
        total = 0
        async with httpx.AsyncClient(headers=UA, timeout=60, follow_redirects=True) as c:
            for u in urls:
                if "://" not in u:
                    u = "https://" + u
                is_map = re.search(r"\.(xml|gz|txt)(\?|$)", u, re.I) is not None
                queue = [u] if is_map else await find_sitemaps(c, u)
                if not queue:
                    Actor.log.warning(f"No sitemap found for {u}"); continue
                seen_maps, seen_urls, got, buf = set(), set(), 0, []
                while queue and got < cap:
                    sm = queue.pop(0)
                    if sm in seen_maps:
                        continue
                    seen_maps.add(sm)
                    body = await fetch(c, sm)
                    if not body:
                        continue
                    if sm.lower().split("?")[0].endswith(".txt") or not body.lstrip().startswith(b"<"):
                        entries = [{"url": l.strip()} for l in body.decode("utf-8", "ignore").splitlines() if l.strip().startswith("http")]
                    else:
                        try:
                            root = ET.fromstring(body)
                        except ET.ParseError:
                            Actor.log.warning(f"Could not parse {sm}"); continue
                        if local(root.tag) == "sitemapindex":
                            for s in root:
                                loc = next((x.text for x in s if local(x.tag) == "loc"), None)
                                lm = parse_date(next((x.text for x in s if local(x.tag) == "lastmod"), None))
                                if loc and not (after and lm and lm < after):
                                    queue.append(loc.strip())
                            continue
                        entries = []
                        for node in root:
                            e = {"images": [], "newsTitle": None}
                            for x in node:
                                t = local(x.tag)
                                if t == "loc": e["url"] = (x.text or "").strip()
                                elif t == "lastmod": e["lastmod"] = (x.text or "").strip()
                                elif t == "changefreq": e["changefreq"] = (x.text or "").strip()
                                elif t == "priority":
                                    try: e["priority"] = float(x.text)
                                    except (TypeError, ValueError): pass
                                elif t == "image":
                                    for y in x:
                                        if local(y.tag) == "loc" and y.text: e["images"].append(y.text.strip())
                                elif t == "news":
                                    for y in x:
                                        if local(y.tag) == "title": e["newsTitle"] = y.text
                            if e.get("url"):
                                entries.append(e)
                    for e in entries:
                        url = e["url"]
                        if url in seen_urls:
                            continue
                        if inc and not any(p.search(url) for p in inc):
                            continue
                        if exc and any(p.search(url) for p in exc):
                            continue
                        if after:
                            lm = parse_date(e.get("lastmod"))
                            if lm and lm < after:
                                continue
                        seen_urls.add(url)
                        buf.append({"site": u, "url": url, "lastmod": e.get("lastmod"), "changefreq": e.get("changefreq"),
                                    "priority": e.get("priority"), "images": e.get("images") or [],
                                    "newsTitle": e.get("newsTitle"), "sitemap": sm})
                        got += 1
                        if got >= cap:
                            break
                        if len(buf) >= 500:
                            res = await Actor.push_data(buf, charged_event_name="url"); total += len(buf); buf = []
                            if res and getattr(res, "event_charge_limit_reached", False):
                                Actor.log.info("Spending limit reached."); return
                if buf:
                    await Actor.push_data(buf, charged_event_name="url"); total += len(buf)
                Actor.log.info(f"{u}: {got} URLs from {len(seen_maps)} sitemaps")
        await Actor.set_status_message(f"Done: {total} URLs.")
