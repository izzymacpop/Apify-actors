"""Hacker News Scraper (Algolia HN Search API)."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx
from apify import Actor

API = "https://hn.algolia.com/api/v1/"


async def get(c, path, params=None):
    for attempt in range(4):
        try:
            r = await c.get(API + path, params=params)
            if r.status_code == 429 or r.status_code >= 500:
                await asyncio.sleep(3 * (attempt + 1)); continue
            if r.status_code >= 400:
                return None
            return r.json()
        except (httpx.HTTPError, ValueError):
            await asyncio.sleep(2 * (attempt + 1))
    return None


def ts(s, end=False):
    if not s:
        return None
    d = datetime.fromisoformat(s[:10]).replace(tzinfo=timezone.utc)
    return int(d.timestamp()) + (86399 if end else 0)


def tree(node):
    return {"id": str(node.get("id")), "author": node.get("author"), "text": node.get("text"),
            "createdAt": node.get("created_at"), "children": [tree(c) for c in node.get("children") or [] if c]}


def hit_item(h):
    tags = h.get("_tags") or []
    kind = next((t for t in ("comment", "show_hn", "ask_hn", "job", "poll", "story") if t in tags), "story")
    oid = h.get("objectID")
    return {"type": kind, "id": oid, "title": h.get("title") or h.get("story_title"), "url": h.get("url") or h.get("story_url"),
            "hnUrl": f"https://news.ycombinator.com/item?id={oid}", "author": h.get("author"),
            "points": h.get("points"), "comments": h.get("num_comments"), "createdAt": h.get("created_at"),
            "storyText": h.get("story_text"), "commentText": h.get("comment_text"),
            "storyId": str(h.get("story_id")) if h.get("story_id") else None,
            "parentId": str(h.get("parent_id")) if h.get("parent_id") else None}


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        queries = [q for q in inp.get("searchQueries") or [] if q and q.strip()]
        front = inp.get("frontPage", False)
        authors = [a.strip() for a in inp.get("authors") or [] if a.strip()]
        if not queries and not front and not authors:
            await Actor.fail(status_message="Add a search query, an author, or turn on 'front page'."); return
        ctype = inp.get("contentType") or "story"
        endpoint = "search_by_date" if (inp.get("sortBy") or "date") == "date" else "search"
        cap = int(inp.get("maxItems") or 200)
        nf = []
        if inp.get("minPoints"): nf.append(f"points>={int(inp['minPoints'])}")
        if inp.get("minComments"): nf.append(f"num_comments>={int(inp['minComments'])}")
        if inp.get("createdAfter"): nf.append(f"created_at_i>={ts(inp['createdAfter'])}")
        if inp.get("createdBefore"): nf.append(f"created_at_i<={ts(inp['createdBefore'], end=True)}")
        with_comments = inp.get("includeComments", False)
        jobs = [(q, ctype, None) for q in queries]
        if authors and not queries:
            jobs += [("", ctype, a) for a in authors]
        elif authors:
            jobs = [(q, ctype, a) for q, _, _ in jobs for a in authors]
        if front:
            jobs.append(("", "front_page", None))
        total = 0
        async with httpx.AsyncClient(timeout=30) as c:
            for q, t, author in jobs:
                tags = [t] + ([f"author_{author}"] if author else [])
                got, page = 0, 0
                while got < cap:
                    params = {"query": q, "tags": ",".join(tags), "hitsPerPage": min(1000, cap - got), "page": page}
                    if nf and t != "front_page":
                        params["numericFilters"] = ",".join(nf)
                    data = await get(c, "search" if t == "front_page" else endpoint, params)
                    hits = (data or {}).get("hits") or []
                    if not hits:
                        break
                    items = [hit_item(h) for h in hits][: cap - got]
                    if with_comments:
                        for it in items:
                            if it["type"] != "comment" and it["comments"]:
                                full = await get(c, f"items/{it['id']}")
                                it["commentTree"] = [tree(ch) for ch in (full or {}).get("children") or []]
                    for it in items:
                        it["query"] = q or None
                        it["scrapedAt"] = datetime.now(timezone.utc).isoformat()
                    res = await Actor.push_data(items, charged_event_name="item")
                    got += len(items); total += len(items)
                    if res and getattr(res, "event_charge_limit_reached", False):
                        Actor.log.info("Spending limit reached."); await Actor.set_status_message(f"Done: {total} items."); return
                    page += 1
                    if page >= (data or {}).get("nbPages", 0):
                        break
                Actor.log.info(f"{q or t}{' by ' + author if author else ''}: {got} items")
        await Actor.set_status_message(f"Done: {total} items.")
