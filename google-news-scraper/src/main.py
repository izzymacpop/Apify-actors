"""Google News Scraper with decoded article URLs."""
from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus, urlencode

import feedparser
import httpx
from apify import Actor
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"}


def edition_params(edition: str):
    hl, gl = edition.split(":")
    lang = hl.split("-")[0]
    return {"hl": hl, "gl": gl, "ceid": f"{gl}:{lang}"}


async def fetch(c, url, **kw):
    for attempt in range(4):
        try:
            r = await c.get(url, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                await asyncio.sleep(3 * (attempt + 1)); continue
            return r
        except httpx.HTTPError:
            await asyncio.sleep(2 * (attempt + 1))
    return None


async def decode_url(c, gnews_url: str) -> str | None:
    m = re.search(r"/articles/([^?/]+)", gnews_url)
    if not m:
        return None
    art = m.group(1)
    r = await fetch(c, f"https://news.google.com/rss/articles/{art}")
    if not r or r.status_code != 200:
        return None
    sig = re.search(r'data-n-a-sg="([^"]+)"', r.text)
    ts = re.search(r'data-n-a-ts="([^"]+)"', r.text)
    if not sig or not ts:
        return None
    req = [["Fbv4je", f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{art}",{ts.group(1)},"{sig.group(1)}"]']]
    for attempt in range(3):
        try:
            p = await c.post("https://news.google.com/_/DotsSplashUi/data/batchexecute",
                             data={"f.req": json.dumps([req])},
                             headers={"content-type": "application/x-www-form-urlencoded;charset=UTF-8"})
            if p.status_code == 429:
                await asyncio.sleep(3 * (attempt + 1)); continue
            body = p.text.split("\n\n", 1)[1]
            data = json.loads(body)[:-2]
            return json.loads(data[0][2])[1]
        except Exception:
            await asyncio.sleep(1)
    return None


async def article_meta(c, url):
    r = await fetch(c, url)
    if not r or r.status_code != 200 or "html" not in r.headers.get("content-type", ""):
        return {}
    s = BeautifulSoup(r.text[:400000], "html.parser")
    def meta(*names):
        for n in names:
            t = s.find("meta", attrs={"property": n}) or s.find("meta", attrs={"name": n})
            if t and t.get("content"):
                return t["content"].strip()
        return None
    return {"description": meta("og:description", "description", "twitter:description"),
            "imageUrl": meta("og:image", "twitter:image"), "author": meta("author", "article:author")}


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        queries = [q.strip() for q in inp.get("queries") or [] if q and q.strip()]
        topics = inp.get("topics") or []
        if not queries and not topics:
            await Actor.fail(status_message="Add at least one search query or topic."); return
        ed = edition_params(inp.get("edition") or "en-GB:GB")
        tf = inp.get("timeframe") or "any"
        cap = int(inp.get("maxArticlesPerQuery") or 100)
        decode = inp.get("decodeUrls", True)
        details = inp.get("fetchArticleDetails", False)

        feeds = []
        for q in queries:
            qq = q + (f" when:{tf}" if tf != "any" else "")
            feeds.append(("query", q, f"https://news.google.com/rss/search?q={quote_plus(qq)}"))
        for t in topics:
            url = "https://news.google.com/rss" if t == "TOP" else f"https://news.google.com/rss/headlines/section/topic/{t}"
            feeds.append(("topic", t, url))

        total, seen = 0, set()
        sem = asyncio.Semaphore(4)
        async with httpx.AsyncClient(headers=UA, timeout=30, follow_redirects=True) as c:
            for kind, label, url in feeds:
                r = await fetch(c, url + ("&" if "?" in url else "?") + urlencode(ed))
                if not r or r.status_code != 200:
                    Actor.log.warning(f"Could not load feed for {label}"); continue
                entries = feedparser.parse(r.text).entries[:cap]

                async def build(e):
                    src = e.get("source") or {}
                    title = e.get("title", "")
                    sname = src.get("title")
                    if sname and title.endswith(" - " + sname):
                        title = title[: -len(" - " + sname)]
                    try:
                        pub = parsedate_to_datetime(e.published).astimezone(timezone.utc).isoformat()
                    except Exception:
                        pub = e.get("published")
                    item = {kind: label, "title": title, "source": sname, "sourceUrl": src.get("href"),
                            "publishedAt": pub, "url": None, "googleNewsUrl": e.get("link")}
                    async with sem:
                        if decode:
                            item["url"] = await decode_url(c, e.get("link", ""))
                        if details and item["url"]:
                            item.update(await article_meta(c, item["url"]))
                    item["url"] = item["url"] or e.get("link")
                    item["edition"] = f"{ed['hl']}:{ed['gl']}"
                    item["scrapedAt"] = datetime.now(timezone.utc).isoformat()
                    return item

                items = await asyncio.gather(*[build(e) for e in entries])
                items = [i for i in items if (i["googleNewsUrl"], label) not in seen]
                for i in items:
                    seen.add((i["googleNewsUrl"], label))
                if items:
                    res = await Actor.push_data(items, charged_event_name="article")
                    total += len(items)
                    Actor.log.info(f"{label}: {len(items)} articles")
                    if res and getattr(res, "event_charge_limit_reached", False):
                        Actor.log.info("Spending limit reached."); break
        await Actor.set_status_message(f"Done: {total} articles.")
