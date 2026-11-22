"""UK Tradespeople Leads: TrustATrader + Bark in one run."""
from __future__ import annotations

import asyncio
import re

import httpx
from apify import Actor
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
      "Accept-Language": "en-GB,en;q=0.9", "Accept": "text/html,application/xhtml+xml"}
TAAT = "https://www.trustatrader.com"
PC_RE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b", re.I)


async def get(c, url, params=None):
    for attempt in range(3):
        try:
            r = await c.get(url, params=params)
            if r.status_code == 429 or r.status_code >= 500:
                await asyncio.sleep(3 * (attempt + 1)); continue
            return r
        except httpx.HTTPError:
            await asyncio.sleep(3 * (attempt + 1))
    return None


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def parse_taat(text, trade, location):
    soup = BeautifulSoup(text, "html.parser"); out = []
    for li in soup.select("li.profile-card"):
        a = li.select_one(".profile-card__heading-link")
        if not a:
            continue
        rc = li.select_one(".profile-card__review-count")
        m = re.match(r"([\d,]+)\s+reviews?\s*/\s*([\d.]+)", rc.get_text(" ", strip=True) if rc else "")
        desc = li.select_one(".profile-card__desc")
        d = re.sub(r"\s+", " ", desc.get_text(" ", strip=True)) if desc else ""
        area = re.search(r"Covering (.+)$", d)
        town = re.search(r" in (.+?) \.", d + " .")
        logo = li.select_one(".profile-card__logo")
        lg = re.search(r"url\('([^']+)'", logo.get("style", "")) if logo else None
        pc = PC_RE.search(d)
        out.append({
            "source": "TrustATrader", "name": a.get_text(strip=True),
            "trade": trade, "searchLocation": location,
            "phones": list(dict.fromkeys(x.get_text(strip=True) for x in li.select(".profile-card__tel-no a"))),
            "rating": float(m.group(2)) if m else None, "reviewCount": int(m.group(1).replace(",", "")) if m else 0,
            "town": town.group(1).strip() if town else None,
            "areaCovered": area.group(1).strip() if area else None,
            "postcode": pc.group(1).upper() if pc else None,
            "description": d, "profileUrl": TAAT + a["href"], "logoUrl": lg.group(1) if lg else None,
            "sourceId": li.get("data-on-id"),
        })
    return out


def parse_bark(text, trade, location, url):
    soup = BeautifulSoup(text, "html.parser"); out = []
    names = soup.select("h4.popular-seller-company-name")
    for k, name_el in enumerate(names):
        stop = names[k + 1].sourceline if k + 1 < len(names) else 10 ** 9
        def nxt(*a, **kw):
            el = name_el.find_next(*a, **kw)
            return el if el is not None and el.sourceline < stop else None
        link = nxt("a", href=re.compile(r"/company/"))
        town = nxt("p", class_="text-light-grey")
        rs = nxt("div", class_="review-score"); stars = rs.select("img.star") if rs else []
        desc = nxt("p", class_="company-description")
        img = name_el.find_previous("img", class_="rounded-circle")
        href = link["href"] if link else None
        out.append({
            "source": "Bark", "name": name_el.get_text(strip=True), "trade": trade, "searchLocation": location,
            "phones": [], "rating": float(min(len(stars), 5)) if stars else None, "reviewCount": None,
            "town": town.get_text(strip=True) if town else None, "areaCovered": None, "postcode": None,
            "description": re.sub(r"\s+", " ", desc.get_text(" ", strip=True)) if desc else "",
            "profileUrl": ("https://www.bark.com" + href if href.startswith("/") else href) if href else url,
            "logoUrl": img.get("src") if img else None,
            "sourceId": href.rstrip("/").split("/")[-1] if href else slug(name_el.get_text(strip=True)),
        })
    return out


async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        trades = [t.strip() for t in inp.get("trades") or [] if t.strip()]
        locs = [l.strip() for l in inp.get("locations") or [] if l.strip()]
        if not trades or not locs:
            await Actor.fail(status_message="Add at least one trade and one location."); return
        max_per = int(inp.get("maxResultsPerSearch") or 100)
        sources = inp.get("sources") or ["trustatrader", "bark"]
        only_phone = bool(inp.get("onlyWithPhone"))
        min_rating = float(inp.get("minRating") or 0)
        seen = set(); total = 0
        async with httpx.AsyncClient(headers=UA, follow_redirects=True, timeout=30) as c:
            for trade in trades:
                for loc in locs:
                    batch = []
                    if "trustatrader" in sources:
                        n = 0
                        for page in range(1, 200):
                            r = await get(c, TAAT + "/search", {"trade_name": trade, "location_str": loc, "page": page})
                            if not r or r.status_code != 200:
                                break
                            items = parse_taat(r.text, trade, loc)
                            if not items:
                                break
                            new = [i for i in items if i["sourceId"] not in {b["sourceId"] for b in batch}]
                            if not new:
                                break
                            batch += new[:max_per - n]; n += len(new[:max_per - n])
                            if n >= max_per:
                                break
                            await asyncio.sleep(0.7)
                    if "bark" in sources:
                        tslug = slug(trade); tslug = tslug if tslug.endswith("s") else tslug + "s"
                        url = f"https://www.bark.com/en/gb/{tslug}/{slug(loc)}/"
                        r = await get(c, url)
                        if r and r.status_code == 200:
                            batch += parse_bark(r.text, trade, loc, url)[:max_per]
                        else:
                            Actor.log.info(f"Bark has no page for '{trade}' in '{loc}' ({url})")
                    out = []
                    for i in batch:
                        key = (re.sub(r"\W", "", i["name"].lower()), tuple(i["phones"][:1]))
                        if key in seen:
                            continue
                        if only_phone and not i["phones"]:
                            continue
                        if min_rating and (i["rating"] or 0) < min_rating:
                            continue
                        seen.add(key); out.append(i)
                    if out:
                        res = await Actor.push_data(out, charged_event_name="lead")
                        total += len(out)
                        if res and getattr(res, "event_charge_limit_reached", False):
                            await Actor.set_status_message(f"Spending limit reached: {total} leads."); return
                    Actor.log.info(f"{trade} / {loc}: {len(out)} leads")
        await Actor.set_status_message(f"Done: {total} leads.")
