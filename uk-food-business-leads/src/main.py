"""UK Takeaway, Restaurant & Food Business Leads from the official Food Standards Agency ratings data."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import httpx
from apify import Actor

API = "https://api.ratings.food.gov.uk"
HDR = {"x-api-version": "2", "Accept": "application/json", "User-Agent": "uk-food-business-leads/1.0"}
TYPES = {"takeaway": 7844, "restaurant": 1, "pub": 7843, "hotel": 7842, "mobile": 7846, "otherCatering": 7841,
         "retailer": 4613, "supermarket": 7840, "manufacturer": 7839, "distributor": 7, "importer": 14,
         "caring": 5, "school": 7845, "farm": 7838}


async def get(c, params):
    for attempt in range(4):
        try:
            r = await c.get(API + "/Establishments", params=params)
            if r.status_code == 200:
                return r.json()
            await asyncio.sleep(2 * (attempt + 1))
        except (httpx.HTTPError, ValueError):
            await asyncio.sleep(2 * (attempt + 1))
    return None


def clean(e, loc):
    addr = ", ".join(x for x in [e.get(f"AddressLine{i}") for i in range(1, 5)] if x)
    g = e.get("geocode") or {}
    rv = e.get("RatingValue")
    return {
        "name": e.get("BusinessName"), "businessType": e.get("BusinessType"),
        "address": addr, "postcode": e.get("PostCode") or None,
        "town": e.get("AddressLine4") or e.get("AddressLine3") or None,
        "localAuthority": e.get("LocalAuthorityName"),
        "hygieneRating": rv, "isNewBusiness": rv == "AwaitingInspection",
        "ratingDate": None if (e.get("RatingDate") or "").startswith("1901") else ((e.get("RatingDate") or "")[:10] or None),
        "phone": e.get("Phone") or None,
        "latitude": float(g["latitude"]) if g.get("latitude") else None,
        "longitude": float(g["longitude"]) if g.get("longitude") else None,
        "scores": e.get("scores"),
        "fhrsId": e.get("FHRSID"),
        "ratingUrl": f"https://ratings.food.gov.uk/business/{e.get('FHRSID')}",
        "councilFoodTeamEmail": e.get("LocalAuthorityEmailAddress") or None,
        "searchLocation": loc,
    }


async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        locs = [l.strip() for l in inp.get("locations") or [] if l.strip()]
        if not locs:
            await Actor.fail(status_message="Add at least one town, city or postcode."); return
        types = inp.get("businessTypes") or ["takeaway"]
        only_new = bool(inp.get("onlyNewBusinesses"))
        max_rating = inp.get("maxHygieneRating")
        name_kw = (inp.get("nameContains") or "").strip()
        max_per = int(inp.get("maxResultsPerLocation") or 500)
        since_days = int(inp.get("ratedInLastDays") or 0)
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).date().isoformat() if since_days else None
        seen = set(); total = 0
        async with httpx.AsyncClient(headers=HDR, timeout=40) as c:
            for loc in locs:
                for t in types:
                    tid = TYPES.get(t)
                    if tid is None:
                        continue
                    params = {"address": loc, "businessTypeId": tid, "pageSize": 100}
                    if name_kw:
                        params["name"] = name_kw
                    if only_new:
                        params.update(ratingKey="AwaitingInspection", ratingOperatorKey="Equal")
                    elif max_rating not in (None, ""):
                        params.update(ratingKey=str(int(max_rating)), ratingOperatorKey="LessThanOrEqual")
                    n = 0
                    for page in range(1, 1000):
                        params["pageNumber"] = page
                        d = await get(c, params)
                        if not d or not d.get("establishments"):
                            break
                        out = []
                        for e in d["establishments"]:
                            if e.get("FHRSID") in seen:
                                continue
                            row = clean(e, loc)
                            if since and not only_new and (row["ratingDate"] or "") < since:
                                continue
                            seen.add(e.get("FHRSID")); out.append(row)
                        out = out[: max_per - n]
                        if out:
                            res = await Actor.push_data(out, charged_event_name="lead")
                            n += len(out); total += len(out)
                            if res and getattr(res, "event_charge_limit_reached", False):
                                await Actor.set_status_message(f"Spending limit reached: {total} businesses."); return
                        if n >= max_per or page >= (d.get("meta") or {}).get("totalPages", 0):
                            break
                        await asyncio.sleep(0.3)
                    Actor.log.info(f"{loc} / {t}: {n} businesses")
        await Actor.set_status_message(f"Done: {total} businesses.")
