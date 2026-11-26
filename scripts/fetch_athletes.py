"""BB365 athletes robot.

Reads the Fitness Volt pro bodybuilding database (men only) and writes athletes.json: each listed
athlete's full professional record, from his first contest on, one row per contest with its link.

Athletes read:
  - the world's top athletes by number of wins (WORLD_PAGES x 100, most wins first)
  - every male athlete from Kuwait, Saudi Arabia, the UAE, Bahrain, Oman and Qatar
  - every athlete named in the app's own results (src/template.html), found by name search
The app builds its rankings (Kuwait, Saudi Arabia, Gulf, World) from this file.

Polite by design: one request at a time with a pause between them.
If fewer than MIN_ATHLETES are read, athletes.json is left as it is.
Uses only the Python standard library.
"""
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "athletes.json"
BASE = "https://fitnessvolt.com/bodybuilding/athletes/"
CONTESTS = "https://fitnessvolt.com/bodybuilding/contests/"
UA = "Mozilla/5.0 (compatible; BB365-results-bot/1.0; +https://bb365app.github.io/bb365/)"
WORLD_PAGES = 2
GULF = {"KW": "Kuwait", "SA": "Saudi Arabia", "AE": "UAE", "BH": "Bahrain", "OM": "Oman", "QA": "Qatar"}
COUNTRY_NAMES = {"United Arab Emirates": "UAE"}  # the app's own short names
PAUSE = 1.0
MIN_ATHLETES = 100
WOMEN = re.compile(r"women|bikini|figure|wellness|fitness|\bms\.?\s", re.I)  # men only, always


def get(url):
    err = None
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                time.sleep(PAUSE)
                return r.read().decode("utf-8", "ignore")
        except Exception as e:  # network hiccup: wait and try again
            err = e
            time.sleep(4 * (i + 1))
    print(f"failed {url}: {err}", file=sys.stderr)
    return ""


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def list_slugs(country=None, pages=50):
    """Athlete slugs from the database list, most wins first."""
    out = []
    for pg in range(1, pages + 1):
        url = f"{BASE}?gender=M&sort=wins&order=DESC&per_page=100&pg={pg}" + (f"&country={country}" if country else "")
        page = get(url)
        rows = re.findall(r"<tr\b.*?</tr>", page, flags=re.S)
        found = []
        for row in rows:
            m = re.search(r'href="https://fitnessvolt\.com/bodybuilding/athletes/([a-z0-9-]+)/"', row)
            if m and m.group(1) not in found:
                found.append(m.group(1))
        out += [s for s in found if s not in out]
        if len(found) < 100:
            break
    return out


def app_names():
    """Names in the app's own result lists (REAL_EVENTS placings and RESULTS winners)."""
    try:
        s = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
        a, b = s.index("const REAL_EVENTS"), s.index("EVENTS.push(...REAL_EVENTS")
        names = set(re.findall(r'\["([A-Z][^"]+?)", "[^"]*"\]', s[a:b]))
        a, b = s.index("const RESULTS = ["), s.index("const CHAMPS")
        names |= {n.split(" · ")[0] for n in re.findall(r'\["[^"]+", "([^"]+)"\]', s[a:b])}
        return sorted(names)
    except ValueError:
        return []


def find_slug(name):
    """The database slug for an exact (case-insensitive) name match, or None."""
    page = get(f"{BASE}?gender=M&per_page=25&q=" + urllib.parse.quote(name))
    for slug, label in re.findall(r'href="https://fitnessvolt\.com/bodybuilding/athletes/([a-z0-9-]+)/"[^>]*>(.*?)</a>', page, flags=re.S):
        if clean(label).lower() == name.lower():
            return slug
    return None


def glance(text, label):
    m = re.search(rf"\n{label}\n([^\n]+)\n", text)
    return m.group(1).strip() if m else ""


def athlete(slug):
    page = get(f"{BASE}{slug}/")
    if not page:
        return None
    lines = html.unescape(re.sub(r"<[^>]+>", "\n", re.sub(r"<(script|style).*?</\1>", "", page, flags=re.S)))
    lines = "\n" + "\n".join(l.strip() for l in lines.split("\n") if l.strip()) + "\n"
    if glance(lines, "Gender") != "Male":
        return None
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, flags=re.S)
    name = clean(h1.group(1)) if h1 else slug.replace("-", " ").title()
    country = glance(lines, "Country")
    rows = []
    for tr in re.findall(r'<tr class="bb-results-row[^"]*">(.*?)</tr>', page, flags=re.S):
        cell = lambda c: re.search(rf'class="bb-results-cell--{c}"[^>]*>(.*?)</td>', tr, flags=re.S)
        year, contest, div, place = cell("year"), cell("contest"), cell("division"), cell("place")
        if not (year and contest and div and place):
            continue
        link = re.search(r'href="https://fitnessvolt\.com/bodybuilding/contests/([a-z0-9-]+)/"', contest.group(1))
        p = re.search(r"#(\d+)", clean(place.group(1)))
        division = clean(div.group(1))
        if WOMEN.search(division):
            continue
        rows.append([int(clean(year.group(1)) or 0), clean(contest.group(1)), link.group(1) if link else "", division, int(p.group(1)) if p else None])
    if not rows:
        return None
    divs = [r[3] for r in rows]
    main_div = max(set(divs), key=divs.count)  # the division he entered most
    return {"id": slug, "name": name, "country": COUNTRY_NAMES.get(country, country), "div": main_div, "rows": rows}


def main():
    slugs = list_slugs(pages=WORLD_PAGES)
    print("world list:", len(slugs))
    for code in GULF:
        got = list_slugs(country=code)
        print(code, len(got))
        slugs += [s for s in got if s not in slugs]
    for name in app_names():
        slug = find_slug(name)
        if slug and slug not in slugs:
            slugs.append(slug)
    print("with the app's own athletes:", len(slugs))
    athletes = []
    for i, slug in enumerate(slugs, 1):
        a = athlete(slug)
        if a:
            athletes.append(a)
        if i % 25 == 0:
            print(f"{i}/{len(slugs)} read, {len(athletes)} kept")
    if len(athletes) < MIN_ATHLETES:
        print(f"only {len(athletes)} athletes read; athletes.json left as it is", file=sys.stderr)
        return 1
    data = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "Fitness Volt pro bodybuilding database (results recorded from NPC Contests and the IFBB Pro League)",
        "athleteUrl": BASE, "contestUrl": CONTESTS,
        "rows": "year, contest, contest page id, division, place (null = unplaced)",
        "athletes": athletes,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT.name}: {len(athletes)} athletes, {sum(len(a['rows']) for a in athletes)} results")
    return 0


if __name__ == "__main__":
    sys.exit(main())
