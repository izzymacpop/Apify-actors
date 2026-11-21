"""Remote startup jobs alerts: fetch public ATS job feeds, post NEW remote jobs to Telegram.

Env vars (set as GitHub Actions secrets/variables):
  TELEGRAM_BOT_TOKEN   bot token from @BotFather (secret)
  PAID_CHAT_ID         channel id/@username that gets every new job (the paid channel)
  FREE_CHAT_ID         optional public channel that gets a short daily teaser
  PREMIUM_LINK         optional link to join the paid channel (shown in the teaser)
  TEASER_HOUR_UTC      hour to post the daily teaser (default 9)
No token = dry run (prints messages).
"""
import html, json, os, re, sys, time, concurrent.futures as cf
from datetime import datetime, timezone
from pathlib import Path
import httpx

HERE = Path(__file__).parent
STATE = Path(os.environ.get("STATE_FILE", HERE / "state" / "seen.json"))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
PAID = os.environ.get("PAID_CHAT_ID", "").strip()
FREE = os.environ.get("FREE_CHAT_ID", "").strip()
PREMIUM_LINK = os.environ.get("PREMIUM_LINK", "").strip()
TEASER_HOUR = int(os.environ.get("TEASER_HOUR_UTC", "9") or 9)
MAX_POST = int(os.environ.get("MAX_JOBS_PER_RUN", "40"))
REMOTE_RE = re.compile(r"\b(remote|anywhere|distributed|work from home|wfh)\b", re.I)

client = httpx.Client(timeout=30, headers={"User-Agent": "remote-jobs-alerts/1.0"}, follow_redirects=True)

def gh(board):
    d = client.get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs").json()
    name = d.get("meta", {}).get("company_name") if isinstance(d.get("meta"), dict) else None
    for j in d.get("jobs", []):
        loc = (j.get("location") or {}).get("name", "")
        yield dict(id=f"gh:{board}:{j['id']}", title=j.get("title", ""), company=j.get("company_name") or name or board.title(),
                   location=loc, url=j.get("absolute_url", ""), remote=bool(REMOTE_RE.search(loc)))

def lv(board):
    for j in client.get(f"https://api.lever.co/v0/postings/{board}?mode=json").json():
        c = j.get("categories") or {}
        loc = c.get("location", "") or ", ".join(c.get("allLocations", []) or [])
        remote = j.get("workplaceType") == "remote" or bool(REMOTE_RE.search(loc))
        yield dict(id=f"lv:{board}:{j['id']}", title=j.get("text", ""), company=board.title(), location=loc,
                   url=j.get("hostedUrl", ""), remote=remote)

def ab(board):
    d = client.get(f"https://api.ashbyhq.com/posting-api/job-board/{board}").json()
    for j in d.get("jobs", []):
        if j.get("isListed") is False:
            continue
        loc = j.get("location", "") or ""
        wt = (j.get("workplaceType") or "").lower()
        remote = wt == "remote" or (wt == "" and bool(j.get("isRemote"))) or bool(REMOTE_RE.search(loc))
        yield dict(id=f"ab:{board}:{j['id']}", title=j.get("title", ""), company=board.title(), location=loc,
                   url=j.get("jobUrl", ""), remote=remote)

FETCH = {"gh": gh, "lv": lv, "ab": ab}
NICE = {"gleanwork": "Glean", "grafanalabs": "Grafana Labs", "matchgroup": "Match Group", "openai": "OpenAI",
        "posthog": "PostHog", "elevenlabs": "ElevenLabs", "clickhouse": "ClickHouse", "mongodb": "MongoDB", "sofi": "SoFi"}

def fetch_all():
    lines = [l.strip() for l in (HERE / "companies.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
    def one(line):
        p, b = line.split(":", 1)
        try:
            jobs = list(FETCH[p](b))
            for j in jobs:
                if p != "gh" or j["company"] == b.title():
                    j["company"] = NICE.get(b, j["company"])
            return jobs
        except Exception as e:
            print(f"warn {line}: {e}", file=sys.stderr)
            return []
    with cf.ThreadPoolExecutor(16) as ex:
        return [j for jobs in ex.map(one, lines) for j in jobs]

def tg(chat, text):
    if not TOKEN:
        print(f"--- [dry run -> {chat or 'no chat'}]\n{text}\n")
        return
    for attempt in range(5):
        r = client.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                        json={"chat_id": chat, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True})
        if r.status_code == 429:
            time.sleep(r.json().get("parameters", {}).get("retry_after", 5) + 1); continue
        if r.status_code != 200:
            print(f"telegram error {r.status_code}: {r.text[:200]}", file=sys.stderr)
        return
    time.sleep(1.2)

def fmt(j):
    e = html.escape
    return f"<b>{e(j['title'])}</b>\n🏢 {e(j['company'])}  ·  📍 {e(j['location'] or 'Remote')}\n🔗 {e(j['url'])}"

def main():
    if not TOKEN and os.environ.get("GITHUB_ACTIONS"):
        print("TELEGRAM_BOT_TOKEN not set yet, skipping."); return
    state = json.loads(STATE.read_text()) if STATE.exists() else {"seen": {}, "teaser_day": ""}
    seen = state["seen"]
    jobs = [j for j in fetch_all() if j["remote"] and j["url"]]
    now = datetime.now(timezone.utc)
    first_run = not seen
    new = [j for j in jobs if j["id"] not in seen]
    print(f"{len(jobs)} remote jobs, {len(new)} new, first_run={first_run}")
    for j in new:
        seen[j["id"]] = now.isoformat()
    # forget jobs not seen for 60 days so the state file stays small
    live = {j["id"] for j in jobs}
    state["seen"] = {k: v for k, v in seen.items() if k in live or (now - datetime.fromisoformat(v)).days < 60}
    if first_run:
        new = new[:10]  # don't flood the channel on the very first run
    to_post = new[:MAX_POST]
    if PAID or not TOKEN:
        for i in range(0, len(to_post), 8):
            chunk = to_post[i:i + 8]
            tg(PAID, "🆕 <b>New remote jobs</b>\n\n" + "\n\n".join(fmt(j) for j in chunk))
    # daily teaser for the free channel
    today = now.strftime("%Y-%m-%d")
    if FREE and now.hour >= TEASER_HOUR and state.get("teaser_day") != today:
        recent = [j for j in jobs if j["id"] in state["seen"] and (now - datetime.fromisoformat(state["seen"][j["id"]])).total_seconds() < 86400]
        if recent:
            n = len(recent)
            msg = f"🌍 <b>{n} new remote jobs at top tech companies in the last 24h</b>\n\nToday's picks:\n\n" + "\n\n".join(fmt(j) for j in recent[:3])
            if PREMIUM_LINK:
                msg += f"\n\n🔓 Get all {n} the moment they're posted: {html.escape(PREMIUM_LINK)}"
            tg(FREE, msg)
            state["teaser_day"] = today
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state))

if __name__ == "__main__":
    main()
