"""Substack Scraper (cursor-based archive API)."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from apify import Actor
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"}


def base_url(entry: str) -> str:
    entry = entry.strip().rstrip("/")
    if "://" not in entry:
        entry = f"https://{entry}.substack.com" if "." not in entry else "https://" + entry
    u = urlparse(entry)
    return f"{u.scheme}://{u.netloc}"


def text_of(html):
    if not html:
        return None
    t = BeautifulSoup(html, "html.parser").get_text("\n")
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()


async def get_json(c, url, params=None):
    for attempt in range(4):
        try:
            r = await c.get(url, params=params)
        except httpx.HTTPError:
            await asyncio.sleep(2 * (attempt + 1)); continue
        if r.status_code in (429, 500, 502, 503):
            await asyncio.sleep(3 * (attempt + 1)); continue
        if r.status_code >= 400:
            Actor.log.debug(f"{url} -> {r.status_code} {r.text[:200]}")
            return None
        try:
            return r.json()
        except ValueError:
            return None
    return None


def to_item(p, pub_host, include):
    bylines = p.get("publishedBylines") or []
    html = p.get("body_html") if include else None
    return {
        "publication": pub_host, "postId": p.get("id"), "title": p.get("title"), "subtitle": p.get("subtitle"),
        "author": ", ".join(b.get("name", "") for b in bylines) or None,
        "authorHandle": bylines[0].get("handle") if bylines else None,
        "publishedAt": p.get("post_date"), "type": p.get("type"), "audience": p.get("audience"),
        "likes": p.get("reaction_count"), "comments": p.get("comment_count"),
        "restacks": p.get("restacks"), "wordcount": p.get("wordcount"),
        "section": p.get("section_name"), "tags": [t.get("name") for t in p.get("postTags") or []],
        "coverImage": p.get("cover_image"), "url": p.get("canonical_url"),
        "description": p.get("description") or p.get("search_engine_description"),
        "contentHtml": html, "contentText": text_of(html) if include else None,
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
    }


def after_ok(p, after):
    if not after:
        return True
    try:
        return datetime.fromisoformat(p.get("post_date", "").replace("Z", "+00:00")) >= after
    except ValueError:
        return True


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        pubs = [p for p in inp.get("publications") or [] if p and p.strip()]
        queries = [q for q in inp.get("searchQueries") or [] if q and q.strip()]
        if not pubs and not queries:
            await Actor.fail(status_message="Add a newsletter or a search query."); return
        cap = int(inp.get("maxPostsPerSource") or 50)
        include = inp.get("includeContent", True)
        free_only = inp.get("freeOnly", False)
        after = None
        if inp.get("publishedAfter"):
            try:
                after = datetime.fromisoformat(inp["publishedAfter"].replace("Z", "+00:00"))
                if not after.tzinfo:
                    after = after.replace(tzinfo=timezone.utc)
            except ValueError:
                Actor.log.warning("Could not read 'publishedAfter'; ignoring it.")
        total = 0
        async with httpx.AsyncClient(headers=UA, timeout=40, follow_redirects=True) as c:
            for pub in pubs:
                base = base_url(pub); host = urlparse(base).netloc
                got, cursor, done = 0, None, False
                while not done:
                    params = {"sort": "new", "limit": 20}
                    if cursor:
                        params["cursor"] = cursor
                    data = await get_json(c, f"{base}/api/v1/archive", params)
                    if data is None:
                        Actor.log.warning(f"{pub}: could not read archive (not a Substack?)"); break
                    posts = data.get("posts") if isinstance(data, dict) else data
                    if not posts:
                        break
                    batch = []
                    for p in posts:
                        if not after_ok(p, after):
                            done = True; break
                        if free_only and p.get("audience") not in (None, "everyone"):
                            continue
                        batch.append(to_item(p, host, include))
                    batch = batch[: cap - got]
                    if batch:
                        res = await Actor.push_data(batch, charged_event_name="post")
                        got += len(batch); total += len(batch)
                        if res and getattr(res, "event_charge_limit_reached", False):
                            Actor.log.info("Spending limit reached."); await Actor.set_status_message(f"Done: {total} posts."); return
                    cursor = data.get("nextCursor") if isinstance(data, dict) else None
                    if got >= cap or not cursor:
                        break
                Actor.log.info(f"{pub}: {got} posts")

            for q in queries:
                got, cursor = 0, None
                while got < cap:
                    params = {"query": q}
                    if cursor:
                        params["cursor"] = cursor
                    data = await get_json(c, "https://substack.com/api/v1/top/search", params)
                    items = (data or {}).get("items") or []
                    if not items:
                        break
                    batch = []
                    for it in items:
                        if it.get("type") != "post":
                            continue
                        ctx = it.get("context") or {}
                        p = it.get("post") or ctx.get("post") or (it.get("entity") or {})
                        if not p or not p.get("title"):
                            continue
                        if not after_ok(p, after) or (free_only and p.get("audience") not in (None, "everyone")):
                            continue
                        pub = it.get("publication") or ctx.get("publication") or {}
                        host = pub.get("custom_domain") or (f"{pub.get('subdomain')}.substack.com" if pub.get("subdomain") else None)
                        item = to_item(p, host, include and bool(p.get("body_html")))
                        item["searchQuery"] = q
                        if not item["url"] and host and p.get("slug"):
                            item["url"] = f"https://{host}/p/{p['slug']}"
                        batch.append(item)
                    batch = batch[: cap - got]
                    if batch:
                        await Actor.push_data(batch, charged_event_name="post")
                        got += len(batch); total += len(batch)
                    cursor = (data or {}).get("nextCursor")
                    if not cursor:
                        break
                Actor.log.info(f"search '{q}': {got} posts")
        await Actor.set_status_message(f"Done: {total} posts.")
