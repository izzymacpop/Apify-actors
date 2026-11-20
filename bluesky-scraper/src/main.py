"""Bluesky Scraper using the public AT Protocol AppView API."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone

import httpx
from apify import Actor

API = "https://api.bsky.app/xrpc/"
PUBLIC = "https://public.api.bsky.app/xrpc/"
UA = {"User-Agent": "bluesky-scraper/1.0"}


class Stop(Exception):
    pass


async def call(c, method, params, base=PUBLIC):
    for attempt in range(5):
        try:
            r = await c.get(base + method, params=params)
        except httpx.HTTPError:
            await asyncio.sleep(2 * (attempt + 1)); continue
        if r.status_code == 429 or r.status_code >= 500:
            await asyncio.sleep(3 * (attempt + 1)); continue
        if r.status_code == 403 and base == PUBLIC:
            base = API; continue
        if r.status_code >= 400:
            Actor.log.debug(f"{method} {params}: {r.status_code} {r.text[:200]}")
            return None
        return r.json()
    return None


def handle_of(entry: str) -> str:
    entry = entry.strip()
    m = re.search(r"bsky\.app/profile/([^/?#]+)", entry)
    h = m.group(1) if m else entry
    return h.lstrip("@")


def post_item(p, source):
    rec = p.get("record") or {}
    a = p.get("author") or {}
    rkey = p.get("uri", "").rsplit("/", 1)[-1]
    tags, links, mentions = [], [], []
    for f in rec.get("facets") or []:
        for ft in f.get("features") or []:
            t = ft.get("$type", "")
            if t.endswith("#tag"): tags.append(ft.get("tag"))
            elif t.endswith("#link"): links.append(ft.get("uri"))
            elif t.endswith("#mention"): mentions.append(ft.get("did"))
    emb = p.get("embed") or {}
    images = [i.get("fullsize") for i in emb.get("images") or []]
    if not images and isinstance(emb.get("media"), dict):
        images = [i.get("fullsize") for i in emb["media"].get("images") or []]
    ext = emb.get("external") or {}
    if ext.get("uri"): links.append(ext["uri"])
    reply = rec.get("reply") or {}
    return {"type": "post", "source": source, "uri": p.get("uri"),
            "url": f"https://bsky.app/profile/{a.get('handle')}/post/{rkey}",
            "authorHandle": a.get("handle"), "authorName": a.get("displayName"), "authorDid": a.get("did"),
            "text": rec.get("text"), "createdAt": rec.get("createdAt"), "indexedAt": p.get("indexedAt"),
            "likes": p.get("likeCount"), "reposts": p.get("repostCount"), "replies": p.get("replyCount"),
            "quotes": p.get("quoteCount"), "hashtags": tags, "links": list(dict.fromkeys(links)), "mentions": mentions,
            "images": images, "lang": rec.get("langs"), "isReply": bool(reply),
            "replyTo": (reply.get("parent") or {}).get("uri")}


def profile_item(p, source, kind="profile"):
    return {"type": kind, "source": source, "handle": p.get("handle"), "did": p.get("did"),
            "displayName": p.get("displayName"), "description": p.get("description"),
            "followers": p.get("followersCount"), "following": p.get("followsCount"), "posts": p.get("postsCount"),
            "avatar": p.get("avatar"), "createdAt": p.get("createdAt"), "indexedAt": p.get("indexedAt"),
            "url": f"https://bsky.app/profile/{p.get('handle')}"}


class Pusher:
    def __init__(self):
        self.total = 0

    async def push(self, items):
        if not items:
            return
        now = datetime.now(timezone.utc).isoformat()
        for i in items:
            i["scrapedAt"] = now
        res = await Actor.push_data(items, charged_event_name="item")
        self.total += len(items)
        if res and getattr(res, "event_charge_limit_reached", False):
            raise Stop()


async def paginate(c, method, params, key, cap, base=PUBLIC):
    got, cursor = 0, None
    while got < cap:
        p = dict(params, limit=min(100, cap - got))
        if cursor:
            p["cursor"] = cursor
        data = await call(c, method, p, base)
        if not data:
            return
        rows = data.get(key) or []
        if not rows:
            return
        yield rows[: cap - got]
        got += len(rows)
        cursor = data.get("cursor")
        if not cursor:
            return


def day_iso(s, end=False):
    if not s:
        return None
    s = s[:10]
    return f"{s}T23:59:59Z" if end else f"{s}T00:00:00Z"


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        cap = int(inp.get("maxItems") or 200)
        out = Pusher()
        async with httpx.AsyncClient(headers=UA, timeout=30) as c:
            try:
                for q in [q for q in inp.get("searchPosts") or [] if q.strip()]:
                    params = {"q": q, "sort": inp.get("sort") or "latest"}
                    if inp.get("since"): params["since"] = day_iso(inp["since"])
                    if inp.get("until"): params["until"] = day_iso(inp["until"], end=True)
                    if inp.get("language"): params["lang"] = inp["language"]
                    lo, hi = params.get("since"), params.get("until")
                    if (lo or hi) and await call(c, "app.bsky.feed.searchPosts", dict(params, limit=1), API) is None:
                        # some queries (e.g. hashtags) reject date params: filter dates ourselves
                        params.pop("since", None); params.pop("until", None)
                    else:
                        lo = hi = None
                    n = 0
                    async for rows in paginate(c, "app.bsky.feed.searchPosts", params, "posts", cap * (3 if lo or hi else 1), base=API):
                        items = [post_item(p, f"search:{q}") for p in rows]
                        if lo or hi:
                            items = [i for i in items if (not lo or (i["createdAt"] or "") >= lo) and (not hi or (i["createdAt"] or "") <= hi)]
                            if lo and rows and all(((p.get("record") or {}).get("createdAt") or "") < lo for p in rows) and params.get("sort") == "latest":
                                break
                        items = items[: cap - n]
                        await out.push(items); n += len(items)
                        if n >= cap:
                            break
                    Actor.log.info(f"search '{q}': {n} posts")

                for q in [q for q in inp.get("searchUsers") or [] if q.strip()]:
                    n = 0
                    async for rows in paginate(c, "app.bsky.actor.searchActors", {"q": q}, "actors", cap):
                        await out.push([profile_item(p, f"userSearch:{q}") for p in rows]); n += len(rows)
                    Actor.log.info(f"user search '{q}': {n} users")

                what = set(inp.get("profileData") or ["details", "posts"])
                for entry in [e for e in inp.get("profiles") or [] if e.strip()]:
                    h = handle_of(entry)
                    if "details" in what:
                        prof = await call(c, "app.bsky.actor.getProfile", {"actor": h})
                        if not prof:
                            Actor.log.warning(f"Profile not found: {entry}"); continue
                        await out.push([profile_item(prof, f"profile:{h}")])
                    if "posts" in what:
                        n = 0
                        async for rows in paginate(c, "app.bsky.feed.getAuthorFeed", {"actor": h, "filter": "posts_with_replies"}, "feed", cap):
                            await out.push([dict(post_item(r["post"], f"profile:{h}"), isRepost=bool(r.get("reason"))) for r in rows]); n += len(rows)
                        Actor.log.info(f"{h}: {n} posts")
                    for kind, method, key in (("followers", "app.bsky.graph.getFollowers", "followers"),
                                              ("following", "app.bsky.graph.getFollows", "follows")):
                        if kind in what:
                            n = 0
                            async for rows in paginate(c, method, {"actor": h}, key, cap):
                                await out.push([dict(profile_item(p, f"{kind}:{h}", "follower" if kind == "followers" else "following"), ofProfile=h) for p in rows]); n += len(rows)
                            Actor.log.info(f"{h}: {n} {kind}")
            except Stop:
                Actor.log.info("Spending limit reached.")
        await Actor.set_status_message(f"Done: {out.total} items.")
