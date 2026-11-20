"""Podcast Scraper: Apple Podcasts directory + RSS feeds."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser
import httpx
from apify import Actor

UA = {"User-Agent": "Mozilla/5.0 (compatible; podcast-scraper/1.0)"}


async def get(c, url, **kw):
    for attempt in range(3):
        try:
            r = await c.get(url, **kw)
            if r.status_code in (403, 429) or r.status_code >= 500:
                await asyncio.sleep(3 * (attempt + 1)); continue
            return r
        except httpx.HTTPError:
            await asyncio.sleep(2 * (attempt + 1))
    return None


def dt(entry):
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    if not t:
        return None
    try:
        return datetime.fromtimestamp(mktime(t), tz=timezone.utc)
    except Exception:
        return None


def from_apple(r):
    return {"type": "podcast", "name": r.get("collectionName"), "author": r.get("artistName"),
            "genre": r.get("primaryGenreName"), "genres": [g for g in r.get("genres") or [] if g != "Podcasts"],
            "appleId": r.get("collectionId"), "appleUrl": r.get("collectionViewUrl"), "feedUrl": r.get("feedUrl"),
            "artworkUrl": r.get("artworkUrl600"), "explicit": r.get("collectionExplicitness") == "explicit",
            "country": r.get("country"), "appleEpisodeCount": r.get("trackCount"),
            "lastReleaseDate": r.get("releaseDate")}


async def enrich_rss(c, pod, max_eps):
    """Read RSS for owner contact, episode stats and episodes."""
    if not pod.get("feedUrl"):
        return pod, []
    r = await get(c, pod["feedUrl"])
    if not r or r.status_code != 200:
        return pod, []
    f = feedparser.parse(r.content)
    ch = f.feed
    owner = ch.get("publisher_detail") or {}
    email = owner.get("email")
    if not email:
        m = re.search(r"<itunes:email>\s*([^<\s]+)\s*</itunes:email>", r.text[:200000])
        email = m.group(1) if m else None
    name = owner.get("name")
    if not name:
        m = re.search(r"<itunes:name>\s*([^<]+?)\s*</itunes:name>", r.text[:200000])
        name = m.group(1) if m else None
    dates = [d for d in (dt(e) for e in f.entries) if d]
    pod.update({
        "name": pod.get("name") or ch.get("title"), "author": pod.get("author") or ch.get("author"),
        "description": ch.get("subtitle") or ch.get("summary"), "website": ch.get("link"),
        "language": ch.get("language"), "ownerName": name, "ownerEmail": email,
        "episodeCount": len(f.entries),
        "firstEpisodeAt": min(dates).isoformat() if dates else None,
        "lastEpisodeAt": max(dates).isoformat() if dates else None,
    })
    eps = []
    for e in f.entries[:max_eps]:
        enc = (e.get("enclosures") or [{}])[0]
        d = dt(e)
        eps.append({"type": "episode", "podcastName": pod.get("name"), "podcastFeedUrl": pod.get("feedUrl"),
                    "title": e.get("title"), "publishedAt": d.isoformat() if d else None,
                    "duration": e.get("itunes_duration"), "episodeNumber": e.get("itunes_episode"),
                    "season": e.get("itunes_season"), "audioUrl": enc.get("href"), "url": e.get("link"),
                    "description": re.sub(r"<[^>]+>", " ", e.get("summary") or "")[:5000].strip() or None})
    return pod, eps


async def resolve_input(c, url):
    m = re.search(r"/id(\d+)", url)
    if m:
        r = await get(c, "https://itunes.apple.com/lookup", params={"id": m.group(1), "entity": "podcast"})
        res = (r.json().get("results") if r and r.status_code == 200 else None) or []
        return from_apple(res[0]) if res else None
    return {"type": "podcast", "feedUrl": url.strip()}


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        terms = [t for t in inp.get("searchTerms") or [] if t and t.strip()]
        urls = [u for u in inp.get("podcasts") or [] if u and u.strip()]
        if not terms and not urls:
            await Actor.fail(status_message="Add a search term or podcast URL."); return
        country = (inp.get("country") or "us").lower()
        cap = int(inp.get("maxPodcastsPerSearch") or 50)
        rss = inp.get("includeOwnerContact", True)
        max_eps = int(inp.get("maxEpisodesPerPodcast") or 0)
        days = int(inp.get("activeWithinDays") or 0)
        since = datetime.now(timezone.utc) - timedelta(days=days) if days else None
        pods, seen = [], set()
        async with httpx.AsyncClient(headers=UA, timeout=30, follow_redirects=True) as c:
            for t in terms:
                r = await get(c, "https://itunes.apple.com/search",
                              params={"term": t, "media": "podcast", "entity": "podcast", "country": country, "limit": min(cap, 200)})
                res = (r.json().get("results") if r and r.status_code == 200 else None) or []
                for x in res:
                    p = from_apple(x); p["searchTerm"] = t
                    key = p.get("appleId") or p.get("feedUrl")
                    if key not in seen:
                        seen.add(key); pods.append(p)
                Actor.log.info(f"'{t}': {len(res)} podcasts found")
            for u in urls:
                p = await resolve_input(c, u)
                if p and (p.get("appleId") or p.get("feedUrl")) not in seen:
                    seen.add(p.get("appleId") or p.get("feedUrl")); pods.append(p)
                elif not p:
                    Actor.log.warning(f"Podcast not found: {u}")

            sem = asyncio.Semaphore(8)

            async def work(p):
                async with sem:
                    if rss or max_eps or since:
                        return await enrich_rss(c, p, max_eps)
                    return p, []

            total_p = total_e = 0
            for coro in asyncio.as_completed([work(p) for p in pods]):
                p, eps = await coro
                if since:
                    last = p.get("lastEpisodeAt") or p.get("lastReleaseDate")
                    try:
                        if not last or datetime.fromisoformat(last.replace("Z", "+00:00")) < since:
                            continue
                    except ValueError:
                        pass
                p["scrapedAt"] = datetime.now(timezone.utc).isoformat()
                res = await Actor.push_data(p, charged_event_name="podcast"); total_p += 1
                if res and getattr(res, "event_charge_limit_reached", False):
                    break
                if eps:
                    res = await Actor.push_data(eps, charged_event_name="episode"); total_e += len(eps)
                    if res and getattr(res, "event_charge_limit_reached", False):
                        break
        await Actor.set_status_message(f"Done: {total_p} podcasts, {total_e} episodes.")
