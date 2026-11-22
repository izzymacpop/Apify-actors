"""UK Salon & Beauty Leads: Fresha + Treatwell in one run."""
from __future__ import annotations

import asyncio
import json
import re

import httpx
from apify import Actor

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
      "Accept-Language": "en-GB,en;q=0.9", "Accept": "text/html,application/xhtml+xml"}
CATS = {  # key: (fresha slug, treatwell slug)
    "hair": ("hair-salons", "at-hair-salon"), "nails": ("nail-salons", "at-nail-salon"),
    "beauty": ("beauty-salons", "at-beauty-salon"), "barbers": ("barbershops", "at-barbershop"),
    "spa": ("spas", "at-day-spa"), "massage": ("massage", None),
    "lashesBrows": ("eyebrows-and-lashes", None), "aesthetics": ("aesthetics", None),
}
LD_RE = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S)


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


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def lds(text):
    out = []
    for raw in LD_RE.findall(text):
        try:
            out.append(json.loads(raw))
        except ValueError:
            pass
    return out


def businesses(text):
    found = []
    def walk(x):
        if isinstance(x, list):
            for i in x: walk(i)
        elif isinstance(x, dict):
            t = x.get("@type"); t = t if isinstance(t, list) else [t]
            if "HealthAndBeautyBusiness" in t or any(str(i).endswith(("Salon", "Spa", "BarberShop")) for i in t):
                found.append(x); return
            for k in ("@graph", "itemListElement", "item"):
                if k in x: walk(x[k])
    for j in lds(text):
        walk(j)
    return found


def row(b, source, category, loc):
    a = b.get("address") or {}; g = b.get("geo") or {}; r = b.get("aggregateRating") or {}
    t = b.get("@type"); t = [x for x in (t if isinstance(t, list) else [t]) if x and x != "HealthAndBeautyBusiness"]
    socials = b.get("sameAs") or []
    socials = socials if isinstance(socials, list) else [socials]
    img = b.get("image"); img = img[0] if isinstance(img, list) and img else img
    return {
        "source": source, "name": b.get("name"), "category": category, "businessType": t[0] if t else None,
        "phone": b.get("telephone") or None,
        "address": a.get("streetAddress"), "area": a.get("addressLocality"), "region": a.get("addressRegion"),
        "postcode": a.get("postalCode"),
        "rating": r.get("ratingValue"), "reviewCount": r.get("ratingCount") or r.get("reviewCount"),
        "priceRange": b.get("priceRange"),
        "instagram": next((s for s in socials if "instagram.com" in s), None),
        "facebook": next((s for s in socials if "facebook.com" in s), None),
        "website": next((s for s in socials if not re.search(r"instagram\.com|facebook\.com|google\.|tiktok\.com|twitter\.com|x\.com", s)), None),
        "googleMapsUrl": next((s for s in socials if "google.com/maps" in s), None),
        "latitude": g.get("latitude"), "longitude": g.get("longitude"),
        "bookingUrl": b.get("url") or b.get("@id"), "imageUrl": img, "searchLocation": loc,
    }


def place(loc):
    """'Dagenham, London' -> (city='london', area='dagenham'); 'Leeds' -> ('leeds', None)."""
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    if len(parts) >= 2:
        return slug(parts[-1]), slug(parts[0])
    return slug(parts[0]), None


async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        locs = [l.strip() for l in inp.get("locations") or [] if l.strip()]
        cats = inp.get("categories") or ["hair"]
        if not locs:
            await Actor.fail(status_message="Add at least one city or 'Area, City'."); return
        sources = inp.get("sources") or ["fresha", "treatwell"]
        max_per = int(inp.get("maxResultsPerSearch") or 200)
        subareas = bool(inp.get("includeSubAreas"))
        only_phone = bool(inp.get("onlyWithPhone"))
        seen = set(); total = 0
        async with httpx.AsyncClient(headers=UA, follow_redirects=True, timeout=40) as c:
            async def push(rows):
                nonlocal total
                out = []
                for r_ in rows:
                    key = (re.sub(r"\W", "", (r_["name"] or "").lower()), (r_["postcode"] or "").replace(" ", "").upper())
                    if key in seen or (only_phone and not r_["phone"]):
                        continue
                    seen.add(key); out.append(r_)
                if out:
                    res = await Actor.push_data(out, charged_event_name="lead")
                    total += len(out)
                    if res and getattr(res, "event_charge_limit_reached", False):
                        return None
                return len(out)

            for loc in locs:
                city, area = place(loc)
                for cat in cats:
                    fs, ts = CATS.get(cat, (None, None))
                    if "fresha" in sources and fs:
                        base = f"https://www.fresha.com/lp/en/bt/{fs}/in/gb-{city}" + (f"/{area}" if area else "")
                        r = await get(c, base); n = 0; urls_done = {base}
                        if r and r.status_code == 200:
                            k = await push([row(b, "Fresha", cat, loc) for b in businesses(r.text)][:max_per])
                            if k is None:
                                await Actor.set_status_message(f"Spending limit reached: {total}."); return
                            n += k
                            if subareas and not area:
                                subs = sorted(set(re.findall(rf'href="(https://www\.fresha\.com/lp/en/bt/{fs}/in/gb-{city}/[a-z0-9-]+)"', r.text)))
                                for su in subs:
                                    if n >= max_per:
                                        break
                                    if su in urls_done:
                                        continue
                                    urls_done.add(su)
                                    rr = await get(c, su)
                                    if rr and rr.status_code == 200:
                                        k = await push([row(b, "Fresha", cat, loc) for b in businesses(rr.text)][: max_per - n])
                                        if k is None:
                                            await Actor.set_status_message(f"Spending limit reached: {total}."); return
                                        n += k
                                    await asyncio.sleep(0.5)
                        else:
                            Actor.log.info(f"Fresha has no {fs} page for {loc}")
                        Actor.log.info(f"Fresha {cat} / {loc}: {n}")
                    if "treatwell" in sources and ts:
                        tloc = f"{area}-{city}" if area else city
                        n = 0; last = None
                        for page in range(1, 60):
                            url = f"https://www.treatwell.co.uk/places/{ts}/in-{tloc}-uk/" + (f"page-{page}/" if page > 1 else "")
                            r = await get(c, url)
                            if not r or r.status_code != 200:
                                if page == 1:
                                    Actor.log.info(f"Treatwell has no {ts} page for {loc}")
                                break
                            items = [row(b, "Treatwell", cat, loc) for b in businesses(r.text)]
                            ids = tuple(i["bookingUrl"] for i in items)
                            if not items or ids == last:
                                break
                            last = ids
                            k = await push(items[: max_per - n])
                            if k is None:
                                await Actor.set_status_message(f"Spending limit reached: {total}."); return
                            n += k
                            if n >= max_per:
                                break
                            await asyncio.sleep(0.7)
                        Actor.log.info(f"Treatwell {cat} / {loc}: {n}")
        await Actor.set_status_message(f"Done: {total} salons.")
