"""Website Contact & Social Links Extractor."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import unquote, urljoin, urlparse

import httpx
import phonenumbers
import tldextract
from apify import Actor
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
      "Accept-Language": "en-GB,en;q=0.9"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")
OBF_RE = re.compile(r"([A-Za-z0-9._%+-]+)\s*(?:\[at\]|\(at\)|\{at\}| at )\s*([A-Za-z0-9-]+(?:\s*(?:\[dot\]|\(dot\)|\{dot\}| dot |\.)\s*[A-Za-z0-9-]+)+)", re.I)
BAD_EMAIL_END = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js", ".avif")
BAD_EMAIL_PARTS = ("example.com", "sentry", "wixpress", "domain.com", "email.com", "yourdomain", "@2x", "u003e")
SOCIAL = {
    "facebook": re.compile(r"https?://(?:www\.|m\.|business\.)?(?:facebook|fb)\.com/(?!sharer|share|dialog|plugins|tr\b|events/|groups/?$)[^\s\"'<>?#]+", re.I),
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/(?!p/|reel/|explore/|accounts/)[A-Za-z0-9_.]+", re.I),
    "linkedin": re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/(?:company|in|school|showcase)/[^\s\"'<>?#]+", re.I),
    "twitter": re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/(?!intent|share|home|search|hashtag|i/)[A-Za-z0-9_]{1,15}(?![A-Za-z0-9_])", re.I),
    "tiktok": re.compile(r"https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.]+", re.I),
    "youtube": re.compile(r"https?://(?:www\.)?youtube\.com/(?:@[A-Za-z0-9_.-]+|channel/[A-Za-z0-9_-]+|c/[^\s\"'<>?#/]+|user/[^\s\"'<>?#/]+)", re.I),
    "pinterest": re.compile(r"https?://(?:[a-z]{2}\.|www\.)?pinterest\.(?:com|co\.uk)/(?!pin/)[A-Za-z0-9_]+", re.I),
    "threads": re.compile(r"https?://(?:www\.)?threads\.(?:net|com)/@[A-Za-z0-9_.]+", re.I),
    "bluesky": re.compile(r"https?://bsky\.app/profile/[A-Za-z0-9_.:-]+", re.I),
    "whatsapp": re.compile(r"https?://(?:wa\.me/\d+|(?:api|chat)\.whatsapp\.com/[^\s\"'<>]+)", re.I),
}
TLD = tldextract.TLDExtract(suffix_list_urls=())
PRIORITY = ["contact", "kontakt", "contacto", "contatti", "get-in-touch", "about", "team", "people", "impressum",
            "imprint", "legal", "support", "help", "privacy", "locations", "find-us", "visit"]


def cf_decode(hexstr):
    try:
        key = int(hexstr[:2], 16)
        return "".join(chr(int(hexstr[i:i + 2], 16) ^ key) for i in range(2, len(hexstr), 2))
    except ValueError:
        return None


def clean_email(e):
    e = unquote(e).strip().strip(".").lower()
    if e.startswith("mailto:"):
        e = e[7:]
    e = e.split("?")[0]
    if not EMAIL_RE.fullmatch(e) or e.endswith(BAD_EMAIL_END) or any(b in e for b in BAD_EMAIL_PARTS):
        return None
    ext = TLD(e.split("@", 1)[1])
    if not ext.suffix or not ext.domain:
        return None
    return e


def norm_social(u):
    u = u.rstrip("/.,);'\"")
    u = re.sub(r"^http://", "https://", u)
    return u


async def fetch(c, url):
    try:
        r = await c.get(url)
        if r.status_code >= 400 or "html" not in r.headers.get("content-type", "html"):
            return None, None
        return str(r.url), r.text[:1_500_000]
    except (httpx.HTTPError, UnicodeDecodeError):
        return None, None


def extract(html, page_url, region, found):
    soup = BeautifulSoup(html, "html.parser")
    for el in soup.select("[data-cfemail]"):
        d = cf_decode(el.get("data-cfemail", ""))
        if d and (e := clean_email(d)):
            found["emails"].add(e)
    for a in soup.select('a[href*="/cdn-cgi/l/email-protection#"]'):
        d = cf_decode(a["href"].split("#", 1)[1])
        if d and (e := clean_email(d)):
            found["emails"].add(e)
    links = []
    for a in soup.find_all("a", href=True):
        h = a["href"].strip()
        if h.lower().startswith("mailto:"):
            if (e := clean_email(h)):
                found["emails"].add(e)
        elif h.lower().startswith("tel:"):
            found["tel"].add(unquote(h[4:]))
        else:
            links.append(urljoin(page_url, h))
    for s in soup(["script", "style", "noscript"]):
        if s.name == "script" and s.get("type") == "application/ld+json":
            continue
        s.decompose()
    text = unescape(soup.get_text(" "))
    raw = text + " " + " ".join(links) + " " + html[:300000]
    for e in EMAIL_RE.findall(text):
        if (e := clean_email(e)):
            found["emails"].add(e)
    for m in OBF_RE.finditer(text):
        dom = re.sub(r"\s*(?:\[dot\]|\(dot\)|\{dot\}| dot )\s*", ".", m.group(2), flags=re.I).replace(" ", "")
        if (e := clean_email(f"{m.group(1)}@{dom}")):
            found["emails"].add(e)
    for name, rx in SOCIAL.items():
        for u in rx.findall(raw):
            found[name].add(norm_social(u))
    for num in list(found["tel"]):
        found["phonesRaw"].add(num)
    try:
        for m in phonenumbers.PhoneNumberMatcher(text, region, leniency=phonenumbers.Leniency.VALID):
            found["phonesRaw"].add(phonenumbers.format_number(m.number, phonenumbers.PhoneNumberFormat.E164))
    except Exception:
        pass
    if not found.get("companyName"):
        og = soup.find("meta", attrs={"property": "og:site_name"})
        found["companyName"] = (og.get("content") if og else None) or (soup.title.string.split("|")[0].split(" - ")[0].strip() if soup.title and soup.title.string else None)
    return links


def fmt_phones(raw, region):
    out = []
    for p in raw:
        try:
            n = phonenumbers.parse(p, region)
            if phonenumbers.is_valid_number(n):
                out.append(phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
        except phonenumbers.NumberParseException:
            continue
    return sorted(set(out))


async def process(c, site, max_pages, region, same_domain):
    if "://" not in site:
        site = "https://" + site
    found = {k: set() for k in ["emails", "tel", "phonesRaw", *SOCIAL]}
    found["companyName"] = None
    url, html = await fetch(c, site)
    if not html and site.startswith("https://"):
        url, html = await fetch(c, "http://" + site[8:])
    if not html:
        return {"website": site, "error": "Could not load website"}
    host = urlparse(url).netloc.lower()
    domain = host[4:] if host.startswith("www.") else host
    scanned = [url]
    links = extract(html, url, region, found)
    cands = []
    for l in dict.fromkeys(links):
        p = urlparse(l)
        if p.netloc.lower().removeprefix("www.") != domain or re.search(r"\.(pdf|jpg|png|zip|docx?)$", p.path, re.I):
            continue
        score = next((i for i, k in enumerate(PRIORITY) if k in p.path.lower()), None)
        if score is not None:
            cands.append((score, len(p.path), l.split("#")[0]))
    for _, _, l in sorted(set(cands))[: max_pages - 1]:
        if l in scanned:
            continue
        u2, h2 = await fetch(c, l)
        if h2:
            scanned.append(u2); extract(h2, u2, region, found)
    emails = sorted(found["emails"])
    if same_domain:
        emails = [e for e in emails if e.split("@")[1].endswith(domain)]
    own = [e for e in emails if e.split("@")[1].endswith(domain.split(".", 1)[-1] if domain.count(".") > 1 else domain)]
    emails = own + [e for e in emails if e not in own]
    row = {"website": site, "domain": domain, "companyName": found["companyName"], "emails": emails,
           "primaryEmail": emails[0] if emails else None,
           "phones": fmt_phones(found["phonesRaw"], region)}
    for k in SOCIAL:
        row[k] = sorted(found[k])[:10]
    row["pagesScanned"] = scanned
    return row


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        sites = list(dict.fromkeys(s.strip() for s in inp.get("websites") or [] if s and s.strip()))
        if not sites:
            await Actor.fail(status_message="Add at least one website."); return
        max_pages = int(inp.get("maxPagesPerSite") or 8)
        region = (inp.get("phoneRegion") or "GB").upper()
        same = inp.get("sameDomainEmailsOnly", False)
        sem = asyncio.Semaphore(10)
        total = found_n = 0
        limits = httpx.Limits(max_connections=40)
        async with httpx.AsyncClient(headers=UA, timeout=20, follow_redirects=True, limits=limits, verify=False) as c:
            async def run(s):
                async with sem:
                    try:
                        return await asyncio.wait_for(process(c, s, max_pages, region, same), timeout=120)
                    except Exception as e:
                        return {"website": s, "error": f"{type(e).__name__}"}
            for coro in asyncio.as_completed([run(s) for s in sites]):
                row = await coro
                row["scrapedAt"] = datetime.now(timezone.utc).isoformat()
                has = any(row.get(k) for k in ["emails", "phones", *SOCIAL])
                total += 1
                if has:
                    found_n += 1
                    res = await Actor.push_data(row, charged_event_name="website")
                    if res and getattr(res, "event_charge_limit_reached", False):
                        Actor.log.info("Spending limit reached."); break
                else:
                    await Actor.push_data(row)
        await Actor.set_status_message(f"Done: {found_n} of {total} websites had contacts.")
