"""Google Play Reviews Scraper."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone

from apify import Actor
from google_play_scraper import Sort, app as gp_app, reviews as gp_reviews


def parse_id(entry: str) -> str | None:
    m = re.search(r"[?&]id=([\w.]+)", entry)
    if m:
        return m.group(1)
    entry = entry.strip()
    return entry if re.fullmatch(r"[A-Za-z][\w]*(\.[\w]+)+", entry) else None


def iso(d):
    return d.isoformat() if isinstance(d, datetime) else d


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        apps = [a for a in inp.get("apps") or [] if a and str(a).strip()]
        if not apps:
            await Actor.fail(status_message="Add at least one Google Play URL or package ID."); return
        cap = int(inp.get("maxReviewsPerApp") or 1000)
        sort = Sort.NEWEST if (inp.get("sortBy") or "newest") == "newest" else Sort.MOST_RELEVANT
        lang, country = (inp.get("language") or "en").strip(), (inp.get("country") or "us").strip().lower()
        ratings = {int(r) for r in inp.get("ratings") or [] if str(r).strip().isdigit()}
        newer = inp.get("newerThan")
        newer_dt = None
        if newer:
            try:
                newer_dt = datetime.fromisoformat(newer.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                Actor.log.warning("Could not read 'newerThan' date; ignoring it.")
        details_on = inp.get("includeAppDetails", True)
        total = 0
        for entry in apps:
            app_id = parse_id(str(entry))
            if not app_id:
                Actor.log.warning(f"Not a Play Store URL or package ID: {entry}"); continue
            det = {}
            if details_on:
                try:
                    a = await asyncio.to_thread(gp_app, app_id, lang=lang, country=country)
                    det = {"appName": a.get("title"), "developer": a.get("developer"), "appRating": a.get("score"),
                           "appRatingCount": a.get("ratings"), "appInstalls": a.get("installs"), "appGenre": a.get("genre"),
                           "appUrl": a.get("url")}
                except Exception as e:
                    Actor.log.warning(f"{app_id}: app not found ({e})"); continue
            got, token, done = 0, None, False
            while not done and got < cap:
                try:
                    batch, token = await asyncio.to_thread(
                        gp_reviews, app_id, lang=lang, country=country, sort=sort,
                        count=min(200, cap - got + 50), continuation_token=token)
                except Exception as e:
                    Actor.log.warning(f"{app_id}: error fetching reviews ({e}); retrying once")
                    await asyncio.sleep(3)
                    try:
                        batch, token = await asyncio.to_thread(gp_reviews, app_id, lang=lang, country=country, sort=sort,
                                                               count=200, continuation_token=token)
                    except Exception:
                        break
                if not batch:
                    break
                out = []
                for r in batch:
                    if newer_dt and sort == Sort.NEWEST and r.get("at") and r["at"] < newer_dt:
                        done = True; break
                    if ratings and r.get("score") not in ratings:
                        continue
                    out.append({"appId": app_id, **det, "reviewId": r.get("reviewId"), "rating": r.get("score"),
                                "text": r.get("content"), "thumbsUp": r.get("thumbsUpCount"),
                                "appVersion": r.get("appVersion") or r.get("reviewCreatedVersion"),
                                "userName": r.get("userName"), "date": iso(r.get("at")),
                                "replyText": r.get("replyContent"), "repliedAt": iso(r.get("repliedAt")),
                                "language": lang, "country": country,
                                "scrapedAt": datetime.now(timezone.utc).isoformat()})
                out = out[: cap - got]
                if out:
                    res = await Actor.push_data(out, charged_event_name="review")
                    got += len(out); total += len(out)
                    if res and getattr(res, "event_charge_limit_reached", False):
                        Actor.log.info("Spending limit reached."); done = True; cap = got
                if not token or not getattr(token, "token", None):
                    break
            Actor.log.info(f"{app_id}: {got} reviews")
        await Actor.set_status_message(f"Done: {total} reviews.")
