"""UK Events Finder: Skiddle + Eventbrite + DICE in one run."""
from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timedelta, timezone

import httpx
from apify import Actor

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
      "Accept-Language": "en-GB,en;q=0.9", "Accept": "text/html,application/xhtml+xml"}
LD_RE = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S)
NEXT_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
SKIDDLE_SECTIONS = {"all": "whats-on", "gigs": "gigs", "clubs": "clubs", "comedy": "comedy"}
EB_CATS = {"all": "events", "gigs": "music--events", "clubs": "nightlife--events", "comedy": "comedy--events",
           "theatre": "performing-arts--events", "food": "food-and-drink--events", "business": "business--events",
           "family": "family-and-education--events", "sport": "sports-and-fitness--events", "arts": "arts--events",
           "thisWeekend": "events--this-weekend"}


async def get(c, url):
    for attempt in range(3):
        try:
            r = await c.get(url)
            if r.status_code == 429 or r.status_code >= 500:
                await asyncio.sleep(3 * (attempt + 1)); continue
            return r
        except httpx.HTTPError:
            await asyncio.sleep(3 * (attempt + 1))
    return None


def city_slug(c, sep="-"):
    return re.sub(r"[^A-Za-z0-9]+", sep, c.strip()).strip(sep)


def ld_events(text):
    out = []
    def walk(x):
        if isinstance(x, list):
            for i in x: walk(i)
        elif isinstance(x, dict):
            t = x.get("@type"); t = t if isinstance(t, list) else [t]
            if any(str(i).endswith("Event") for i in t):
                out.append(x); return
            for k in ("@graph", "itemListElement", "item", "whats-on"):
                if k in x: walk(x[k])
    for raw in LD_RE.findall(text):
        try: walk(json.loads(raw))
        except ValueError: pass
    m = NEXT_RE.search(text)
    if m and not out:
        try: walk(json.loads(m.group(1))["props"]["pageProps"].get("schema", {}))
        except (ValueError, KeyError): pass
    return out


def from_ld(e, source, city, cat):
    loc = e.get("location") or {}; loc = loc[0] if isinstance(loc, list) and loc else loc
    a = loc.get("address") or {}; a = a if isinstance(a, dict) else {"streetAddress": a}
    g = loc.get("geo") or {}
    offers = e.get("offers") or []; offers = offers if isinstance(offers, list) else [offers]
    prices = [float(o["price"]) for o in offers if isinstance(o, dict) and str(o.get("price", "")).replace(".", "", 1).isdigit()]
    perf = e.get("performer") or []; perf = perf if isinstance(perf, list) else [perf]
    org = e.get("organizer") or {}; org = org[0] if isinstance(org, list) and org else org
    img = e.get("image"); img = img[0] if isinstance(img, list) and img else img
    status = (e.get("eventStatus") or "").rsplit("/", 1)[-1] or None
    return {
        "source": source, "name": (e.get("name") or "").strip(), "category": cat,
        "startDate": e.get("startDate"), "endDate": e.get("endDate"),
        "venue": loc.get("name"), "address": a.get("streetAddress"), "town": a.get("addressLocality"),
        "postcode": a.get("postalCode"),
        "latitude": float(g["latitude"]) if g.get("latitude") else None,
        "longitude": float(g["longitude"]) if g.get("longitude") else None,
        "priceFrom": min(prices) if prices else None, "currency": "GBP" if prices else None,
        "status": status, "performers": [p.get("name") for p in perf if isinstance(p, dict) and p.get("name")],
        "organizer": org.get("name") if isinstance(org, dict) else None,
        "description": (e.get("description") or "")[:1000], "url": e.get("url"), "imageUrl": img,
        "searchCity": city,
    }


def from_dice(e, city):
    v = (e.get("venues") or [{}])[0]; d = e.get("dates") or {}; p = e.get("price") or {}
    amt = p.get("amount_from") if p.get("amount_from") is not None else p.get("amount")
    loc = ((v.get("city") or {}).get("location") or {})
    imgs = e.get("images") or {}
    return {
        "source": "DICE", "name": (e.get("name") or "").strip(), "category": "gigs",
        "startDate": d.get("event_start_date"), "endDate": d.get("event_end_date"),
        "venue": v.get("name"), "address": v.get("address"), "town": (v.get("city") or {}).get("name"),
        "postcode": (re.search(r"[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}", v.get("address") or "") or [None])[0],
        "latitude": loc.get("lat"), "longitude": loc.get("lng"),
        "priceFrom": round(amt / 100, 2) if isinstance(amt, (int, float)) else None,
        "currency": p.get("currency"), "status": e.get("status"), "performers": [], "organizer": None,
        "description": "", "url": f"https://dice.fm/event/{e.get('id')}",
        "imageUrl": imgs.get("landscape") or imgs.get("square") if isinstance(imgs, dict) else None,
        "searchCity": city,
    }


async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        cities = [c.strip() for c in inp.get("cities") or [] if c.strip()]
        if not cities:
            await Actor.fail(status_message="Add at least one UK city."); return
        cats = inp.get("categories") or ["all"]
        sources = inp.get("sources") or ["skiddle", "eventbrite", "dice"]
        days = int(inp.get("nextDays") or 0)
        kw = [k.lower() for k in inp.get("keywords") or [] if k.strip()]
        max_city = int(inp.get("maxEventsPerCity") or 500)
        until = (datetime.now(timezone.utc) + timedelta(days=days)).date().isoformat() if days else None
        today = datetime.now(timezone.utc).date().isoformat()
        seen = set(); total = 0
        async with httpx.AsyncClient(headers=UA, follow_redirects=True, timeout=40) as c:
            for city in cities:
                rows = []
                urls = []
                for cat in cats:
                    if "skiddle" in sources and cat in SKIDDLE_SECTIONS:
                        urls.append(("Skiddle", cat, f"https://www.skiddle.com/{SKIDDLE_SECTIONS[cat]}/{city_slug(city)}/"))
                    if "eventbrite" in sources and cat in EB_CATS:
                        urls.append(("Eventbrite", cat, f"https://www.eventbrite.co.uk/d/united-kingdom--{city_slug(city).lower()}/{EB_CATS[cat]}/"))
                for src, cat, url in urls:
                    r = await get(c, url)
                    if not r or r.status_code != 200:
                        Actor.log.info(f"{src}: no page for {city} / {cat}"); continue
                    rows += [from_ld(e, src, city, cat) for e in ld_events(r.text)]
                    await asyncio.sleep(0.6)
                if "dice" in sources and any(k in cats for k in ("all", "gigs", "clubs")):
                    r = await get(c, f"https://dice.fm/browse/{city_slug(city).lower()}")
                    m = NEXT_RE.search(r.text) if r and r.status_code == 200 else None
                    if m:
                        try:
                            evs = json.loads(m.group(1))["props"]["pageProps"].get("events") or []
                            here = city.lower()[:4]
                            rows += [from_dice(e, city) for e in evs
                                     if here in json.dumps(e.get("venues") or []).lower()]
                        except (ValueError, KeyError):
                            pass
                    else:
                        Actor.log.info(f"DICE: no page for {city}")
                out = []
                for x in rows:
                    key = (re.sub(r"\W", "", x["name"].lower())[:60], (x["startDate"] or "")[:10], re.sub(r"\W", "", (x["venue"] or "").lower())[:20])
                    if not x["name"] or key in seen or x["url"] in seen:
                        continue
                    sd = (x["startDate"] or "")[:10]
                    if sd and (sd < today and (x["endDate"] or "")[:10] < today):
                        continue
                    if until and sd and sd > until:
                        continue
                    if kw and not any(k in (x["name"] + " " + x["description"] + " " + " ".join(x["performers"]) + " " + (x["venue"] or "")).lower() for k in kw):
                        continue
                    seen.add(key); seen.add(x["url"]); out.append(x)
                out.sort(key=lambda x: x["startDate"] or "9999")
                out = out[:max_city]
                if out:
                    res = await Actor.push_data(out, charged_event_name="event")
                    total += len(out)
                    if res and getattr(res, "event_charge_limit_reached", False):
                        await Actor.set_status_message(f"Spending limit reached: {total} events."); return
                Actor.log.info(f"{city}: {len(out)} events")
        await Actor.set_status_message(f"Done: {total} events.")
