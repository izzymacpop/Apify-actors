"""UK Used Car Deals Finder: Gumtree cars, vans and motorbikes with a deal score."""
from __future__ import annotations

import asyncio
import re
import statistics

import httpx
from apify import Actor
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
      "Accept-Language": "en-GB,en;q=0.9", "Accept": "text/html,application/xhtml+xml"}
BASE = "https://www.gumtree.com"
CATS = {"cars": "cars", "vans": "vans", "motorbikes": "motorbikes", "campervans": "campervans-motorhomes"}
FUELS = ("Petrol", "Diesel", "Electric", "Hybrid", "Plug-in Hybrid", "LPG")


async def get(c, url, params=None):
    for attempt in range(3):
        try:
            r = await c.get(url, params=params)
            if r.status_code == 429 or r.status_code >= 500:
                await asyncio.sleep(4 * (attempt + 1)); continue
            return r
        except httpx.HTTPError:
            await asyncio.sleep(4 * (attempt + 1))
    return None


def num(s):
    d = re.sub(r"[^\d]", "", s or "")
    return int(d) if d else None


def parse(text, vehicle_type, loc):
    soup = BeautifulSoup(text, "html.parser"); out = []
    for card in soup.select('[data-q="search-result"]'):
        a = card.select_one('a[data-q="search-result-anchor"]') or card.find("a", href=True)
        title_el = card.select_one('[data-q="tile-title"]')
        if not a or not title_el:
            continue
        href = a["href"]; url = href if href.startswith("http") else BASE + href
        title = title_el.get_text(" ", strip=True)
        attrs_el = card.select_one('[data-q="tile-attributes"]')
        attrs = [s.get_text(" ", strip=True) for s in attrs_el.find_all("span", recursive=True) if s.get_text(strip=True)] if attrs_el else []
        attrs = list(dict.fromkeys(attrs))
        joined = " | ".join(attrs)
        year = next((int(x) for x in attrs if re.fullmatch(r"(19|20)\d\d", x)), None)
        miles = next((num(x) for x in attrs if "mile" in x.lower()), None)
        fuel = next((x for x in attrs if x in FUELS), None)
        seller = "Private" if "Private" in attrs else ("Trade" if "Trade" in attrs else None)
        cc = next((num(x) for x in attrs if x.lower().endswith("cc")), None)
        price_el = card.select_one('[data-q="tile-price"]')
        locn = card.select_one('[data-q="tile-location"]')
        img = card.find("img")
        m = re.search(r"/p/([^/]+)/([^/]+)/", url)
        make_slug = m.group(1) if m else ""
        toks = [t for t in (m.group(2) if m else "").split("-") if t and not re.fullmatch(r"(19|20)\d\d", t)]
        mk = make_slug.split("-")
        while toks and mk and toks[0] == mk[0]:
            toks.pop(0); mk.pop(0)
        make = make_slug.replace("-", " ").title() if make_slug else None
        model = toks[0].title() if toks and not re.fullmatch(r"[\d.]+", toks[0]) else None
        trans = "Automatic" if re.search(r"\bauto", title, re.I) else ("Manual" if re.search(r"\bmanual\b", title, re.I) else None)
        out.append({
            "title": title, "price": num(price_el.get_text() if price_el else ""), "currency": "GBP",
            "year": year or (int(re.search(r"\b(19|20)\d\d\b", title).group(0)) if re.search(r"\b(19|20)\d\d\b", title) else None),
            "mileage": miles, "fuel": fuel, "transmission": trans, "engineCc": cc, "sellerType": seller,
            "make": make, "model": model,
            "location": locn.get_text(" ", strip=True) if locn else None,
            "vehicleType": vehicle_type, "attributes": joined,
            "url": url, "listingId": url.rstrip("/").split("/")[-1],
            "imageUrl": (img.get("src") or img.get("data-src")) if img else None, "searchLocation": loc,
        })
    return out


def score(rows):
    """Deal score: % below (+) or above (-) the median price of similar listings (same make, model, +-1 year)."""
    for r in rows:
        if not r["price"] or not r["make"]:
            r["dealScore"] = None; r["similarListings"] = 0; r["medianSimilarPrice"] = None; continue
        sim = [x["price"] for x in rows if x is not r and x["price"] and x["make"] == r["make"]
               and (x["model"] or "") == (r["model"] or "") and r["year"] and x["year"] and abs(x["year"] - r["year"]) <= 1]
        if len(sim) >= 3:
            med = statistics.median(sim)
            r["dealScore"] = round((med - r["price"]) / med * 100, 1)
            r["medianSimilarPrice"] = int(med); r["similarListings"] = len(sim)
        else:
            r["dealScore"] = None; r["medianSimilarPrice"] = None; r["similarListings"] = len(sim)
    return rows


async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        locs = [l.strip() for l in inp.get("locations") or [] if l.strip()] or ["uk"]
        queries = [q.strip() for q in inp.get("searchTerms") or [] if q.strip()] or [""]
        vtype = inp.get("vehicleType") or "cars"
        max_per = int(inp.get("maxResultsPerSearch") or 200)
        params_base = {"search_category": CATS.get(vtype, "cars")}
        for k_in, k_out in (("minPrice", "min_price"), ("maxPrice", "max_price"), ("distanceMiles", "distance")):
            if inp.get(k_in) not in (None, ""):
                params_base[k_out] = str(inp[k_in])
        if inp.get("privateSellersOnly"):
            params_base["seller_type"] = "private"
        max_miles = inp.get("maxMileage"); min_year = inp.get("minYear")
        only_deals = inp.get("onlyDealsBelowMedianPercent")
        all_rows = []; seen = set()
        async with httpx.AsyncClient(headers=UA, follow_redirects=True, timeout=40) as c:
            for loc in locs:
                for q in queries:
                    n = 0
                    for page in range(1, 100):
                        params = dict(params_base, search_location=loc, page=page)
                        if q:
                            params["q"] = q
                        r = await get(c, BASE + "/search", params)
                        if not r or r.status_code != 200:
                            break
                        items = parse(r.text, vtype, loc)
                        new = [i for i in items if i["listingId"] not in seen]
                        if not new:
                            break
                        for i in new:
                            seen.add(i["listingId"])
                            if max_miles and i["mileage"] and i["mileage"] > int(max_miles):
                                continue
                            if min_year and i["year"] and i["year"] < int(min_year):
                                continue
                            i["searchTerm"] = q or None
                            all_rows.append(i); n += 1
                            if n >= max_per:
                                break
                        if n >= max_per:
                            break
                        await asyncio.sleep(0.8)
                    Actor.log.info(f"{loc} / '{q}': {n} listings")
        score(all_rows)
        if only_deals not in (None, ""):
            all_rows = [r for r in all_rows if r["dealScore"] is not None and r["dealScore"] >= float(only_deals)]
        all_rows.sort(key=lambda r: -(r["dealScore"] if r["dealScore"] is not None else -999))
        total = 0
        for i in range(0, len(all_rows), 200):
            res = await Actor.push_data(all_rows[i:i + 200], charged_event_name="listing")
            total += len(all_rows[i:i + 200])
            if res and getattr(res, "event_charge_limit_reached", False):
                break
        await Actor.set_status_message(f"Done: {total} listings.")
