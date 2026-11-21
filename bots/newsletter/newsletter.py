"""Weekly 'UK Side Hustle Weekly' digest: Google News (UK edition) -> Buttondown email.

Env: BUTTONDOWN_API_KEY (secret). Optional: SPONSOR_MD (markdown block, e.g. an affiliate link),
NEWSLETTER_STATUS (about_to_send | draft, default about_to_send). No key = prints the email.
"""
import email.utils, html, os, re, sys
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET
import httpx

SECTIONS = [  # (heading, search queries, a title must match this regex to be included)
    ("💷 Side hustles & extra income", ["side hustle UK", "second income UK", "make extra money UK"],
     r"side.?hustle|extra (cash|money|income)|second (job|income)|earn|freelanc|gig economy"),
    ("🧾 Tax & HMRC rules", ["HMRC side hustle", "HMRC online sellers", "trading allowance HMRC", "self assessment deadline"],
     r"hmrc|tax|self.?assessment|allowance"),
    ("🤖 AI & small business", ["AI side hustle", "make money with AI", "AI tools small business UK"],
     r"\bai\b|chatgpt|claude|gemini|automation"),
    ("🛒 Selling online (Etsy, eBay, Vinted)", ["Vinted sellers", "eBay sellers UK", "Etsy sellers", "TikTok Shop sellers UK"],
     r"vinted|ebay|etsy|tiktok shop|amazon seller|sellers?\b|reselling"),
    ("🏦 Money & savings", ["savings rates UK", "Martin Lewis money tips", "cost of living payment UK"],
     r"saving|money|bills?|cost of living|martin lewis|interest rate|cash|£"),
]
PER_SECTION = 4
EXCLUDE = re.compile(r"protest|stock|nasdaq|shares|ipo|investor|factory|arrest|court|police|dies|death|gta|game guide|europe|u\.s\.|america", re.I)

c = httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 newsletter-bot"})

def search(q):
    url = f"https://news.google.com/rss/search?q={quote_plus(q + ' when:7d')}&hl=en-GB&gl=GB&ceid=GB:en"
    try:
        root = ET.fromstring(c.get(url).content)
    except Exception as e:
        print(f"warn {q}: {e}", file=sys.stderr); return []
    out = []
    for it in root.iter("item"):
        t = it.findtext("title") or ""
        src = it.findtext("source") or ""
        if src and t.endswith(" - " + src):
            t = t[: -len(src) - 3]
        try:
            d = email.utils.parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:
            d = datetime.now(timezone.utc)
        out.append(dict(title=html.unescape(t.strip()), source=src, link=it.findtext("link"), date=d))
    return out

def words(t):
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", t.lower()).split() if len(w) > 3}

def similar(a, picked):
    wa = words(a)
    return any(len(wa & words(p)) / max(1, len(wa | words(p))) > 0.2 for p in picked)

def build():
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    used, parts, total = set(), [], 0
    for name, queries, must in SECTIONS:
        items = [i for q in queries for i in search(q) if i["date"] >= cutoff]
        items.sort(key=lambda i: i["date"], reverse=True)
        picked = []
        for i in items:
            t = i["title"]
            if similar(t, used) or len(t) < 25 or EXCLUDE.search(t) or not re.search(must, t, re.I):
                continue
            used.add(t); picked.append(i)
            if len(picked) == PER_SECTION:
                break
        if picked:
            total += len(picked)
            parts.append(f"## {name}\n\n" + "\n".join(
                f"- **[{i['title'][:140]}]({i['link']})**  \n  _{i['source']} · {i['date'].strftime('%a %d %b')}_" for i in picked))
    week = datetime.now(timezone.utc).strftime("%d %B %Y")
    intro = (f"Morning 👋 Here's your 5-minute roundup of the week's UK side-hustle, extra-income and money news "
             f"({total} stories), so you don't have to dig for it.\n")
    sponsor = os.environ.get("SPONSOR_MD", "").strip()
    body = intro + "\n" + "\n\n".join(parts)
    if sponsor:
        body += "\n\n---\n\n" + sponsor
    body += ("\n\n---\n\nKnow someone with a side hustle? Forward this to them, it's free.\n\n"
             "_Not financial or tax advice. Always check HMRC guidance or a qualified adviser for your situation._")
    subject = f"UK Side Hustle Weekly · {week}"
    return subject, body, total

def main():
    subject, body, total = build()
    if total < 5:
        print(f"Only {total} stories found, not sending."); return
    key_ = os.environ.get("BUTTONDOWN_API_KEY", "").strip()
    if not key_:
        if os.environ.get("GITHUB_ACTIONS"):
            print("BUTTONDOWN_API_KEY not set yet, skipping."); return
        print(subject + "\n\n" + body); return
    status = os.environ.get("NEWSLETTER_STATUS", "about_to_send") or "about_to_send"
    r = c.post("https://api.buttondown.com/v1/emails",
               headers={"Authorization": f"Token {key_}", "X-Buttondown-Live-Dangerously": "true"},
               json={"subject": subject, "body": body, "status": status})
    print(r.status_code, r.text[:300])
    r.raise_for_status()

if __name__ == "__main__":
    main()
