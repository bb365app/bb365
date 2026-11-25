"""BB365 events robot.

Reads the official IFBB Pro League schedule (https://www.ifbbpro.com/schedule/) and writes events.json
with every upcoming men's pro show (Open, 212, Classic Physique, Men's Physique, Wheelchair).
Shows in the same city on the same dates are merged into one event.
Women's divisions are not used. If the page cannot be read or parsed, events.json is left as it is.

Run it on a saved copy:  python scripts/fetch_events.py data/ifbbpro_schedule.html
"""
import html
import json
import re
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "events.json"
URL = "https://www.ifbbpro.com/schedule/"
TABLES = {  # table id on the official page -> division id in the app
    "men-open-bodybuilding": "open",
    "men-212-bodybuilding": "212",
    "men-classic-physique": "classic",
    "men-physique": "physique",
    "men-wheelchair": "wheelchair",
}
ORDER = ["open", "212", "classic", "physique", "wheelchair"]
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
KEEP_UPPER = {"USA", "UK", "NPC", "IFBB", "AGP", "EVLS", "GRL", "PWR", "EMPRO", "II", "III"}


def text(cell):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", cell))).strip()


def nice_name(raw):
    m = re.match(r"(\d{4})\s+(.*)", raw)
    year, rest = (m.group(1), m.group(2)) if m else ("", raw)
    words = []
    for w in rest.split():
        words.append(w if w in KEEP_UPPER else w[:1] + w[1:].lower())
    name = " ".join(words).replace("Mr ", "Mr. ")
    return (name + (" " + year if year else "")).strip(), int(year) if year else None


def parse_dates(raw, year):
    """'Nov 29' / 'Dec 4-6' / 'Jul 30-Aug 1' -> (start, end, label)"""
    m = re.match(r"([A-Za-z]{3})\w*\.?\s+(\d{1,2})(?:\s*[-–]\s*(?:([A-Za-z]{3})\w*\.?\s+)?(\d{1,2}))?", raw.strip())
    if not m or not year:
        return None
    m1, d1, m2, d2 = m.group(1).lower(), int(m.group(2)), (m.group(3) or m.group(1)).lower(), m.group(4)
    if m1 not in MONTHS or m2 not in MONTHS:
        return None
    start = date(year, MONTHS[m1], d1)
    end = date(year + (1 if MONTHS[m2] < MONTHS[m1] else 0), MONTHS[m2], int(d2)) if d2 else start
    mon = lambda d: d.strftime("%b")
    if end == start:
        label = f"{mon(start)} {start.day}, {start.year}"
    elif end.month == start.month:
        label = f"{mon(start)} {start.day}–{end.day}, {end.year}"
    else:
        label = f"{mon(start)} {start.day}–{mon(end)} {end.day}, {end.year}"
    return start, end, label


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def parse(page):
    shows = {}
    for tid, div in TABLES.items():
        m = re.search(r'<table id="tablepress-[^"]*?' + re.escape(tid) + r'"[^>]*>(.*?)</table>', page, re.S)
        if not m:
            continue
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(1), re.S):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
            if len(cells) < 3:
                continue
            raw_name = text(re.sub(r"<div>.*?</div>", "", cells[0], flags=re.S))
            classes = text(re.search(r"<div>(.*?)</div>", cells[0], re.S).group(1)) if "<div>" in cells[0] else "OPEN"
            name, year = nice_name(raw_name)
            try:
                d = parse_dates(text(cells[1]), year)
            except ValueError:  # an impossible date on the page (for example "Feb 30")
                d = None
            if not d:
                continue
            place = text(cells[2])
            key = (raw_name.upper(), d[0])
            s = shows.setdefault(key, {"name": name, "start": d[0], "end": d[1], "date": d[2], "place": place, "divs": [], "classes": set()})
            if div not in s["divs"]:
                s["divs"].append(div)
            s["classes"].add(classes)
    return list(shows.values())


def merge_same_place(shows):
    """Shows in the same city on the same dates become one event."""
    groups = {}
    for s in sorted(shows, key=lambda x: (x["start"], x["name"])):
        groups.setdefault((s["start"], s["end"], s["place"].lower()), []).append(s)
    events = []
    for items in groups.values():
        items.sort(key=lambda x: (-len(x["divs"]), len(x["name"])))  # the main show names the event
        first = items[0]
        divs = [d for d in ORDER if any(d in x["divs"] for x in items)]
        masters_only = all(all("OPEN" not in c.upper() for c in x["classes"]) for x in items)
        if len(items) > 1:
            names = [x["name"] for x in items]
            about = f"{len(items)} IFBB Pro League shows in {first['place']} on the same dates: " + ", ".join(names[:-1]) + " and " + names[-1] + "."
        else:
            about = "IFBB Pro League show. Divisions and dates are from the official pro schedule and can change; check the official page before you travel."
        if masters_only:
            about += " Masters classes only."
        events.append({
            "id": "ifbb" + slug(first["name"] + first["start"].isoformat()).replace("-", ""),
            "name": first["name"], "date": first["date"], "place": first["place"],
            "start": first["start"].isoformat(), "end": first["end"].isoformat(),
            "divs": divs, "shows": [x["name"] for x in items], "about": about,
        })
    seen = {}
    for e in events:  # two events with the same name (same promoter, different city) get the city added
        if e["name"] in seen:
            e["name"] = f"{e['name']} ({e['place'].split(',')[0].strip()})"
        seen[e["name"]] = True
    return events


def main():
    if len(sys.argv) > 1:
        page = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    else:
        try:
            req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (BB365 events robot)"})
            page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except Exception as err:
            print("Could not read the official schedule:", err, "- events.json left unchanged.")
            return
    today = datetime.now(timezone.utc).date()
    events = [e for e in merge_same_place(parse(page)) if date.fromisoformat(e["end"]) >= today]
    if not events:
        print("No men's shows found on the page (layout may have changed). events.json left unchanged.")
        return
    updated = re.search(r"Last Updated:</strong>\s*([A-Za-z]+ \d{1,2}, \d{4})", page)
    data = {"source": URL, "pageUpdated": updated.group(1) if updated else "", "events": events}
    try:
        old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    except ValueError:
        old = {}
    if not isinstance(old, dict):
        old = {}
    if old.get("events") == events:
        print(f"No schedule change ({len(events)} shows).")
        return
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {len(events)} upcoming men's shows to events.json")


if __name__ == "__main__":
    main()
