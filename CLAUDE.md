# BB365: notes for Claude

BB365 is a men's bodybuilding app for Kuwait and Saudi Arabia, in the spirit of 365Scores: news, results, events, drama between athletes, predictions, a smart coach and challenges between friends. Live at https://bb365app.github.io/bb365/ (GitHub Pages).

## The owner
- A complete beginner in programming. Talk to him in **Kuwaiti Arabic**, simply, one small step at a time. No jargon; when he must click something, say exactly where.
- He reviews on an iPhone (Safari) and a Windows PC.

## Rules that he has set
- **Design: black and gold, 6 tabs** (Home, Events, Clubs, Tools, Shop, Profile). He rejected other looks several times (navy/lime, a simplified 4-tab version, a red "Fight Night" version). Do not redesign without asking; show options first.
- **Men only.** No women's divisions or women's news anywhere (no Bikini, Wellness, Figure, Women's Physique, Ms. Olympia).
- **Everything real and sourced.** Events, results and news must come from real sources (IFBB Pro League, Fitness Volt, Generation Iron, Muscle & Fitness, NPC News Online). Never guess a date or a result; write "Date not announced" when it isn't. Put a source link on what you add.
- **Arabic everywhere** when the app is in Arabic, including athlete names (see the Arabic name list near the end of `src/template.html`).
- Clubs and Shop show "Coming soon" until partners sign (full screens kept as `clubsFull` / `shopFull`).
- Prices: KD for Kuwait, SAR for Saudi Arabia; country is detected from the phone's time zone and can be changed in Profile.
- Welcome flow: animated logo and stage light, then Create account / Sign in (English), then language choice last. Accounts are demo only (saved on the phone; passwords never stored).
- Tools page: two-column grid of gold drawings.
- Featured athletes: عشوي العنزي (@3shwe) and بدران (@vbadrann). Featured clubs: SHPOOOV and OXYGEN.

## How the code is laid out
- `src/template.html` is the whole app (vanilla JS single page: `SCREENS`, state `S` in localStorage key `bb365-demo-v2`, `data-act` → `ACT` click handlers, hash routing). The English UI is translated by the `AR` dictionary and `AR_RX` patterns. `src/img/` holds the pictures.
- `index.html` in the root is **built**; never edit it by hand. After changing `src/template.html`:
  ```
  python3 src/build.py src/template.html src/img /tmp/bb365_page.html /tmp/bb365_standalone.html
  python3 src/make_site.py /tmp/bb365_page.html index.html
  ```
  Then open it in a phone-sized browser (390x844) in both English and Arabic and check there are no page errors.
- Data files the app reads when hosted (no rebuild needed):
  - `news.json` from `scripts/fetch_news.py` (hourly GitHub Action)
  - `news_ar.json` Arabic headlines by story link (filled every 4 hours by a scheduled Claude task)
  - `events.json` from `scripts/fetch_events.py`, which reads the official IFBB Pro schedule (hourly)
  - `events_manual.json` hand-checked events not on that schedule yet (updated by a weekly scheduled Claude check, Saturdays 09:34 Riyadh)
  - `streams.json` live-stream links by event id (YouTube plays inside the app; Instagram/TikTok open a button)
  - `athletes.json` full pro records (men only) from the Fitness Volt database, by `scripts/fetch_athletes.py` (weekly, `.github/workflows/athletes.yml`): the world's top athletes by wins, every Gulf athlete, and every athlete named in the app's own results. The Rankings screen (Kuwait, Saudi Arabia, Gulf, World level) ranks by first places, then second, then third, with no extra weight for any show (owner's rule).
  - `athletes_ar.json` Arabic athlete names, countries, divisions and the words inside contest names. New names the robot brings in need adding here.
- `.github/workflows/publish.yml` runs the robots and publishes to GitHub Pages on every push to `main` and every hour.

## Publishing
- **Owner's rule (Nov 26, 2026): show every change first, publish only after he says yes.** Make the change, rebuild, then show him screenshots (phone size, Arabic) and update the in-Claude preview artifact. Do NOT push app changes to `main` (the live site) until he approves in chat. Ask: "أنزله على الموقع؟"
Changes go live only when they reach `main`. If you worked on a branch, tell the owner in plain words how to merge the pull request (or ask him whether you may push to `main`).

## Ideas he has asked about for later
- Live results room: an admin page to enter placings at the venue, shown instantly to everyone (needs Supabase; he has not created the account yet).
- Streams robot (YouTube API key) and adding stream links in the weekly check.
- Real accounts, real registrations and tickets for events he partners with, payments (KNET / mada) after a commercial licence.
- Kuwait Pro Qualifier 2026 full placings (only pro card winners are published); he believes Ali Alhaddad (علي الهداد) placed first in a division but no source has been found yet.
