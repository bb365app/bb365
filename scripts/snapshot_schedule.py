"""Saves a copy of the official IFBB Pro League schedule page (used to build and check the events robot)."""
import urllib.request
from pathlib import Path
out = Path(__file__).resolve().parent.parent / "data" / "ifbbpro_schedule.html"
req = urllib.request.Request("https://www.ifbbpro.com/schedule/", headers={"User-Agent": "Mozilla/5.0 (BB365 events robot)"})
try:
    out.write_bytes(urllib.request.urlopen(req, timeout=30).read())
    print("saved", out.stat().st_size, "bytes")
except Exception as err:
    print("could not fetch the schedule:", err)
