"""App Store Reviews Scraper using Apple's public customer-review feed."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone

import httpx
from apify import Actor

UA = {"User-Agent": "Mozilla/5.0 (compatible; appstore-reviews/1.0)"}


async def get_json(c, url, **kw):
    for attempt in range(4):
        try:
            r = await c.get(url, **kw)
        except httpx.HTTPError:
            await asyncio.sleep(1.5 * (attempt + 1)); continue
        if r.status_code in (403, 429, 500, 502, 503):
            await asyncio.sleep(2 * (attempt + 1)); continue
        if r.status_code >= 400:
            return None
        try:
            return r.json()
        except ValueError:
            return None
    return None


async def resolve_app(c, entry: str, country: str):
    """Return app ID string for a URL, ID or name."""
    m = re.search(r"id(\d{6,})", entry) or re.fullmatch(r"\s*(\d{6,})\s*", entry)
    if m:
        return m.group(1)
    data = await get_json(c, "https://itunes.apple.com/search",
                          params={"term": entry, "entity": "software", "country": country, "limit": 1})
    res = (data or {}).get("results") or []
    return str(res[0]["trackId"]) if res else None


async def app_details(c, app_id, country):
    data = await get_json(c, "https://itunes.apple.com/lookup", params={"id": app_id, "country": country})
    res = (data or {}).get("results") or []
    if not res:
        return {}
    a = res[0]
    return {"appName": a.get("trackName"), "developer": a.get("artistName"), "appRating": a.get("averageUserRating"),
            "appRatingCount": a.get("userRatingCount"), "appPrice": a.get("formattedPrice"),
            "appGenre": a.get("primaryGenreName"), "appUrl": a.get("trackViewUrl")}


def lab(e, k):
    v = e.get(k) or {}
    return v.get("label") if isinstance(v, dict) else v


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        apps = [a for a in inp.get("apps") or [] if a and str(a).strip()]
        if not apps:
            await Actor.fail(status_message="Add at least one app URL, ID or name."); return
        countries = [c.strip().lower() for c in inp.get("countries") or ["us"] if c.strip()] or ["us"]
        cap = min(int(inp.get("maxReviewsPerCountry") or 500), 500)
        sort = inp.get("sortBy") or "mostrecent"
        ratings = {int(r) for r in inp.get("ratings") or [] if str(r).strip().isdigit()}
        details_on = inp.get("includeAppDetails", True)
        total = 0
        async with httpx.AsyncClient(headers=UA, timeout=30, follow_redirects=True) as c:
            for entry in apps:
                app_id = await resolve_app(c, str(entry), countries[0])
                if not app_id:
                    Actor.log.warning(f"App not found: {entry}"); continue
                for country in countries:
                    det = await app_details(c, app_id, country) if details_on else {}
                    got = 0
                    for page in range(1, 11):
                        data = await get_json(c, f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby={sort}/json")
                        entries = ((data or {}).get("feed") or {}).get("entry") or []
                        if isinstance(entries, dict):
                            entries = [entries]
                        entries = [e for e in entries if "im:rating" in e]
                        if not entries:
                            break
                        batch = []
                        for e in entries:
                            rating = int(lab(e, "im:rating") or 0)
                            if ratings and rating not in ratings:
                                continue
                            batch.append({
                                "appId": app_id, "country": country, **det,
                                "reviewId": lab(e, "id"), "rating": rating, "title": lab(e, "title"),
                                "text": lab(e, "content"), "author": lab(e.get("author") or {}, "name"),
                                "appVersion": lab(e, "im:version"), "voteCount": int(lab(e, "im:voteCount") or 0),
                                "voteSum": int(lab(e, "im:voteSum") or 0), "date": lab(e, "updated"),
                                "url": f"https://apps.apple.com/{country}/app/id{app_id}?see-all=reviews",
                                "scrapedAt": datetime.now(timezone.utc).isoformat(),
                            })
                        batch = batch[: cap - got]
                        if batch:
                            res = await Actor.push_data(batch, charged_event_name="review")
                            got += len(batch); total += len(batch)
                            if res and getattr(res, "event_charge_limit_reached", False):
                                Actor.log.info("Spending limit reached."); await Actor.set_status_message(f"Done: {total} reviews."); return
                        if got >= cap:
                            break
                    Actor.log.info(f"{entry} [{country}]: {got} reviews")
        await Actor.set_status_message(f"Done: {total} reviews.")
