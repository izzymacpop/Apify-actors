"""ATS Jobs Scraper: unified job listings from public ATS job-board feeds."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import urlparse

import httpx
from apify import Actor
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (compatible; ats-jobs-scraper/1.0)"}
PLATFORMS = ["greenhouse", "lever", "ashby", "smartrecruiters", "recruitee", "workable"]


def html_to_text(html: str | None) -> str | None:
    if not html:
        return None
    text = BeautifulSoup(unescape(html), "html.parser").get_text("\n")
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def parse_company(entry: str) -> tuple[list[str], str]:
    """Return (platforms_to_try, slug) for a URL or plain slug."""
    entry = entry.strip()
    if "://" not in entry and "." not in entry:
        return PLATFORMS, entry
    u = urlparse(entry if "://" in entry else "https://" + entry)
    host, parts = u.netloc.lower(), [p for p in u.path.split("/") if p]
    if "greenhouse.io" in host:
        if "for" in u.query:  # embed?for=slug
            m = re.search(r"for=([^&]+)", u.query)
            if m:
                return ["greenhouse"], m.group(1)
        return ["greenhouse"], parts[0] if parts else ""
    if "lever.co" in host:
        return ["lever-eu" if ".eu." in host else "lever"], parts[0] if parts else ""
    if "ashbyhq.com" in host:
        return ["ashby"], parts[0] if parts else ""
    if "smartrecruiters.com" in host:
        return ["smartrecruiters"], parts[0] if parts else ""
    if host.endswith("recruitee.com"):
        return ["recruitee"], host.split(".")[0]
    if "workable.com" in host:
        return ["workable"], parts[0] if parts else host.split(".")[0]
    # unknown domain: treat first label as slug
    return PLATFORMS, host.split(".")[0]


def ms_to_iso(ms) -> str | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).isoformat()
    except Exception:
        return None


async def get_json(client: httpx.AsyncClient, url: str, **kw):
    method = kw.pop("method", "GET")
    for attempt in range(4):
        try:
            r = await client.request(method, url, **kw)
        except httpx.HTTPError as e:
            Actor.log.debug(f"{url}: {e}")
            await asyncio.sleep(1.5 * (attempt + 1))
            continue
        if r.status_code == 404:
            return None
        if r.status_code in (429, 500, 502, 503, 504):
            await asyncio.sleep(2 * (attempt + 1))
            continue
        if r.status_code >= 400:
            return None
        try:
            return r.json()
        except ValueError:
            return None
    return None


async def fetch_greenhouse(c, slug, desc):
    data = await get_json(c, f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", params={"content": "true"})
    if not data or "jobs" not in data:
        return None
    out = []
    for j in data["jobs"]:
        loc = (j.get("location") or {}).get("name")
        html = unescape(j.get("content") or "") if desc else None
        out.append({
            "platform": "greenhouse", "company": j.get("company_name") or slug, "companySlug": slug,
            "jobId": str(j.get("id")), "title": j.get("title"),
            "department": ", ".join(d["name"] for d in j.get("departments") or []) or None,
            "location": loc, "remote": bool(loc and "remote" in loc.lower()),
            "employmentType": None, "salary": None,
            "postedAt": j.get("first_published") or j.get("updated_at"), "updatedAt": j.get("updated_at"),
            "url": j.get("absolute_url"), "applyUrl": j.get("absolute_url"),
            "descriptionHtml": html, "descriptionText": html_to_text(html) if desc else None,
        })
    return out


async def fetch_lever(c, slug, desc, eu=False):
    base = "https://api.eu.lever.co" if eu else "https://api.lever.co"
    data = await get_json(c, f"{base}/v0/postings/{slug}", params={"mode": "json"})
    if not isinstance(data, list):
        return None
    out = []
    for j in data:
        cat = j.get("categories") or {}
        wt = (j.get("workplaceType") or "").lower()
        html = None
        if desc:
            html = (j.get("description") or "") + "".join(
                f"<h3>{l.get('text')}</h3><ul>{l.get('content')}</ul>" for l in j.get("lists") or []) + (j.get("additional") or "")
        sal = j.get("salaryRange")
        salary = f"{sal.get('currency','')} {sal.get('min')}–{sal.get('max')} {sal.get('interval','')}".strip() if sal else None
        out.append({
            "platform": "lever", "company": slug, "companySlug": slug, "jobId": j.get("id"), "title": j.get("text"),
            "department": cat.get("team") or cat.get("department"), "location": cat.get("location"),
            "remote": wt == "remote" or "remote" in (cat.get("location") or "").lower(),
            "employmentType": cat.get("commitment"), "salary": salary,
            "postedAt": ms_to_iso(j.get("createdAt")), "updatedAt": None,
            "url": j.get("hostedUrl"), "applyUrl": j.get("applyUrl"),
            "descriptionHtml": html, "descriptionText": html_to_text(html) if desc else None,
        })
    return out


async def fetch_ashby(c, slug, desc):
    data = await get_json(c, f"https://api.ashbyhq.com/posting-api/job-board/{slug}", params={"includeCompensation": "true"})
    if not data or "jobs" not in data:
        return None
    out = []
    for j in data["jobs"]:
        if j.get("isListed") is False:
            continue
        comp = (j.get("compensation") or {}).get("compensationTierSummary")
        out.append({
            "platform": "ashby", "company": slug, "companySlug": slug, "jobId": j.get("id"), "title": j.get("title"),
            "department": j.get("department") or j.get("team"), "location": j.get("location"),
            "remote": bool(j.get("isRemote")) or (j.get("workplaceType") or "").lower() == "remote",
            "employmentType": j.get("employmentType"), "salary": comp,
            "postedAt": j.get("publishedAt"), "updatedAt": None,
            "url": j.get("jobUrl"), "applyUrl": j.get("applyUrl"),
            "descriptionHtml": j.get("descriptionHtml") if desc else None,
            "descriptionText": j.get("descriptionPlain") if desc else None,
        })
    return out


async def fetch_smartrecruiters(c, slug, desc, limit):
    out, offset = [], 0
    while True:
        data = await get_json(c, f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
                              params={"limit": 100, "offset": offset})
        if not data or "content" not in data:
            return out or None
        if not data["content"] and offset == 0:
            return None
        for j in data["content"]:
            loc = j.get("location") or {}
            html = None
            if desc:
                det = await get_json(c, f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{j['id']}")
                secs = ((det or {}).get("jobAd") or {}).get("sections") or {}
                html = "".join(f"<h3>{s.get('title','')}</h3>{s.get('text','')}" for s in secs.values() if isinstance(s, dict))
            out.append({
                "platform": "smartrecruiters", "company": (j.get("company") or {}).get("name") or slug, "companySlug": slug,
                "jobId": j.get("id"), "title": j.get("name"),
                "department": (j.get("department") or {}).get("label") or (j.get("function") or {}).get("label"),
                "location": loc.get("fullLocation") or ", ".join(x for x in [loc.get("city"), loc.get("country")] if x),
                "remote": bool(loc.get("remote")), "employmentType": (j.get("typeOfEmployment") or {}).get("label"),
                "salary": None, "postedAt": j.get("releasedDate"), "updatedAt": None,
                "url": f"https://jobs.smartrecruiters.com/{slug}/{j.get('id')}",
                "applyUrl": f"https://jobs.smartrecruiters.com/{slug}/{j.get('id')}",
                "descriptionHtml": html, "descriptionText": html_to_text(html) if desc else None,
            })
            if limit and len(out) >= limit:
                return out
        offset += 100
        if offset >= data.get("totalFound", 0):
            return out


async def fetch_recruitee(c, slug, desc):
    data = await get_json(c, f"https://{slug}.recruitee.com/api/offers/")
    if not data or "offers" not in data:
        return None
    out = []
    for j in data["offers"]:
        html = ((j.get("description") or "") + (j.get("requirements") or "")) if desc else None
        sal = j.get("salary") or {}
        salary = None
        if sal.get("min") or sal.get("max"):
            salary = f"{sal.get('currency') or ''} {sal.get('min') or ''}–{sal.get('max') or ''} {sal.get('period') or ''}".strip()
        loc = ", ".join(x for x in [j.get("city"), j.get("country")] if x) or j.get("location")
        out.append({
            "platform": "recruitee", "company": j.get("company_name") or slug, "companySlug": slug,
            "jobId": str(j.get("id")), "title": j.get("title"), "department": j.get("department"),
            "location": loc, "remote": bool(j.get("remote")), "employmentType": j.get("employment_type_code"),
            "salary": salary, "postedAt": j.get("published_at") or j.get("created_at"), "updatedAt": None,
            "url": j.get("careers_url"), "applyUrl": j.get("careers_apply_url"),
            "descriptionHtml": html, "descriptionText": html_to_text(html) if desc else None,
        })
    return out


async def fetch_workable(c, slug, desc):
    data = await get_json(c, f"https://apply.workable.com/api/v1/widget/accounts/{slug}", params={"details": "true" if desc else "false"})
    if not data or "jobs" not in data:
        return None
    out = []
    for j in data["jobs"]:
        loc = ", ".join(x for x in [j.get("city"), j.get("state"), j.get("country")] if x)
        html = j.get("description") if desc else None
        out.append({
            "platform": "workable", "company": data.get("name") or slug, "companySlug": slug,
            "jobId": j.get("shortcode"), "title": j.get("title"), "department": j.get("department"),
            "location": loc or None, "remote": bool(j.get("telecommuting")), "employmentType": j.get("employment_type"),
            "salary": None, "postedAt": j.get("published_on") or j.get("created_at"), "updatedAt": None,
            "url": j.get("url") or j.get("shortlink"), "applyUrl": j.get("application_url") or j.get("url"),
            "descriptionHtml": html, "descriptionText": html_to_text(html) if desc else None,
        })
    return out


def parse_date(s):
    if not s:
        return None
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def keep(job, kw, locs, remote_only, since):
    if kw and not any(k in (job["title"] or "").lower() for k in kw):
        return False
    if locs and not any(l in (job["location"] or "").lower() for l in locs):
        return False
    if remote_only and not job["remote"]:
        return False
    if since:
        d = parse_date(job["postedAt"]) or parse_date(job["updatedAt"])
        if d and d < since:
            return False
    return True


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        companies = [c for c in inp.get("companies") or [] if c and c.strip()]
        if not companies:
            await Actor.fail(status_message="Add at least one company URL or slug.")
            return
        kw = [k.lower() for k in inp.get("keywords") or [] if k]
        locs = [l.lower() for l in inp.get("locations") or [] if l]
        remote_only = bool(inp.get("remoteOnly"))
        days = int(inp.get("postedWithinDays") or 0)
        since = datetime.now(timezone.utc) - timedelta(days=days) if days else None
        desc = inp.get("includeDescription", True)
        limit = int(inp.get("maxJobsPerCompany") or 0)

        total, stop = 0, False
        sem = asyncio.Semaphore(5)
        async with httpx.AsyncClient(headers=UA, timeout=40, follow_redirects=True) as client:

            async def run_one(entry):
                platforms, slug = parse_company(entry)
                if not slug:
                    Actor.log.warning(f"Could not read a company from '{entry}'")
                    return entry, None, []
                async with sem:
                    for p in platforms:
                        if p == "greenhouse": jobs = await fetch_greenhouse(client, slug, desc)
                        elif p == "lever": jobs = await fetch_lever(client, slug, desc) or await fetch_lever(client, slug, desc, eu=True)
                        elif p == "lever-eu": jobs = await fetch_lever(client, slug, desc, eu=True)
                        elif p == "ashby": jobs = await fetch_ashby(client, slug, desc)
                        elif p == "smartrecruiters": jobs = await fetch_smartrecruiters(client, slug, desc, limit)
                        elif p == "recruitee": jobs = await fetch_recruitee(client, slug, desc)
                        else: jobs = await fetch_workable(client, slug, desc)
                        if jobs:
                            return entry, p, jobs
                return entry, None, []

            for coro in asyncio.as_completed([run_one(e) for e in companies]):
                entry, platform, jobs = await coro
                if not platform:
                    Actor.log.warning(f"No job board found for '{entry}'")
                    continue
                jobs = [j for j in jobs if keep(j, kw, locs, remote_only, since)]
                if limit:
                    jobs = jobs[:limit]
                Actor.log.info(f"{entry}: {len(jobs)} jobs ({platform})")
                for j in jobs:
                    j["scrapedAt"] = datetime.now(timezone.utc).isoformat()
                    res = await Actor.push_data(j, charged_event_name="job")
                    total += 1
                    if res and getattr(res, "event_charge_limit_reached", False):
                        stop = True
                        break
                if stop:
                    Actor.log.info("Spending limit reached, stopping.")
                    break
        await Actor.set_status_message(f"Done: {total} jobs from {len(companies)} companies.")
