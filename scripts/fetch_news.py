"""BB365 news robot.

Reads bodybuilding news feeds and writes news.json, which the app shows on its home page.
GitHub runs this every 3 hours (see .github/workflows/news.yml). Uses only the Python standard library.

Items written by hand or by the daily editor (they have "keep": true) stay at the top for 14 days.
If every feed fails, news.json is left as it is.
"""
import email.utils
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "news.json"
MAX_ITEMS = 40
KEEP_DAYS = 14

# name, feed url, how to keep only bodybuilding stories:
#   "cats"  = the title or the site's own categories must mention bodybuilding (bodybuilding-focused sites)
#   "title" = the title itself must mention bodybuilding (general fitness sites that tag widely)
FEEDS = [
    ("Fitness Volt", "https://fitnessvolt.com/feed/", "cats"),
    ("Generation Iron", "https://generationiron.com/feed/", "cats"),
    ("Muscle & Fitness", "https://www.muscleandfitness.com/feed/", "title"),
    ("BarBend", "https://barbend.com/feed/", "title"),
]

BB_WORDS = re.compile(
    r"bodybuild|olympia|ifbb|npc|\bpro\b|physique|classic|bikini|wellness|figure|prep|posing|"
    r"contest|champion|walker|dauda|cbum|bumstead|lunsford|ramy|rambod|cutler|coleman|arnold|kuwait|gulf|arab|saudi|dubai|qatar|bodybuilder",
    re.I,
)
ICONS = [
    (re.compile(r"result|win|won|champion|olympia|title|place|pro\b|scorecard", re.I), "trophy"),
    (re.compile(r"diet|nutrition|calorie|protein|meal|carb|dry|water|diuretic", re.I), "flame"),
    (re.compile(r"workout|training|exercise|split|sets|reps|lift|squat|bench|deadlift", re.I), "dumbbell"),
    (re.compile(r"slam|feud|beef|robbed|callout|responds|fires back|controvers|banned", re.I), "bolt"),
]
NOT_BB = re.compile(r"powerlift|\bIPF\b|strongman|crossfit|weightlifting|arm ?wrestl", re.I)
KINDS = [
    ("result", re.compile(r"\bresults?\b|\bwins?\b|\bwon\b|crowned|scorecard|takes (the )?(title|overall|crown)|champion(s|ship)? (crowned|recap)", re.I)),
    ("drama", re.compile(r"slams?|fires? back|responds? to|calls? out|robbed|controvers|beef|feud|criticiz|blasts?|claps? back|disqualif|banned|accus|reacts? to|rips?\b", re.I)),
]
NS = {"atom": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/"}


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def parse_date(text):
    if not text:
        return None
    text = text.strip()
    try:
        d = email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def nice_date(d):
    return d.strftime("%b ") + str(d.day) + d.strftime(", %Y")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BB365-news-robot/1.0 (+https://github.com)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def read_feed(name, url, only_bb):
    root = ET.fromstring(fetch(url))
    out = []
    entries = root.findall("./channel/item") or root.findall("atom:entry", NS)
    for e in entries:
        title = clean(e.findtext("title") or e.findtext("atom:title", namespaces=NS))
        link = (e.findtext("link") or "").strip()
        if not link:
            a = e.find("atom:link", NS)
            link = a.get("href", "") if a is not None else ""
        when = parse_date(e.findtext("pubDate") or e.findtext("atom:published", namespaces=NS) or e.findtext("atom:updated", namespaces=NS))
        cats = " ".join(clean(c.text) for c in e.findall("category"))
        if not title or not link.startswith("https://") or not when:
            continue
        if not BB_WORDS.search(title if only_bb == "title" else title + " " + cats):
            continue
        if NOT_BB.search(title) and not re.search(r"bodybuild", title + " " + cats, re.I):
            continue
        icon = next((i for rx, i in ICONS if rx.search(title)), "news")
        kind = next((k for k, rx in KINDS if rx.search(title)), "news")
        out.append({"t": title[:160], "url": link, "src": name, "date": nice_date(when), "ts": int(when.timestamp()), "ic": icon, "kind": kind})
    return out


def main():
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except ValueError:
            old = {}
    now = datetime.now(timezone.utc)
    cutoff = int((now - timedelta(days=KEEP_DAYS)).timestamp())
    kept = [x for x in old.get("items", []) if x.get("keep") and x.get("ts", 0) >= cutoff]

    found, ok = [], 0
    for name, url, only_bb in FEEDS:
        try:
            items = read_feed(name, url, only_bb)
            ok += 1
            print(f"{name}: {len(items)} stories")
            found += items
        except Exception as err:  # one broken feed must not stop the others
            print(f"{name}: skipped ({err.__class__.__name__}: {err})", file=sys.stderr)
    if ok == 0:
        print("No feed could be read. news.json left unchanged.")
        return

    found.sort(key=lambda x: x["ts"], reverse=True)
    seen, items = set(), []
    for x in kept + found:
        key = (x["url"].split("?")[0].rstrip("/"), x["t"].lower()[:60])
        if key[0] in seen or key[1] in seen:
            continue
        seen.update(key)
        items.append(x)
    items = items[:MAX_ITEMS]

    if items == old.get("items", []):
        print("No new stories.")
        return
    OUT.write_text(json.dumps({"updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {len(items)} stories to news.json")


if __name__ == "__main__":
    main()
