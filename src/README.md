# BB365 source

`index.html` in the repository root is built from these files. Edit `template.html`, then rebuild from the repository root:

```
python3 src/build.py src/template.html src/img /tmp/bb365_page.html /tmp/bb365_standalone.html
python3 src/make_site.py /tmp/bb365_page.html index.html
```

- `template.html`: the whole app (screens, styles, Arabic text). Images are placeholders like `__IMG_name__`.
- `img/`: the pictures; `build.py` puts them inside the page.
- `make_site.py`: adds the phone app settings (icon, home-screen name) around the page.

Data the robots and the weekly check keep up to date (no rebuild needed):
- `news.json`: news robot, every hour.
- `news_ar.json`: Arabic headlines for news.json (by story link), filled by the translation check.
- `events.json`: events robot, from the official IFBB Pro League schedule, every hour.
- `events_manual.json`: hand-checked events not on that schedule yet (for example the Arnold Classic).
- `streams.json`: live stream links per event id.
