#!/usr/bin/env python3
"""Poster grid for a movie folder. Builds one HTML page, opens it, exits. Click a poster to play in IINA."""
import html, json, re, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "~/Downloads/Archive/Movies").expanduser()
CACHE = Path("~/.cache/movieshelf").expanduser()
VIDEO = {".mkv", ".mp4", ".m4v", ".avi", ".mov"}


def video_of(p):
    if p.is_file():
        return p if p.suffix.lower() in VIDEO else None
    vids = [f for f in p.rglob("*") if f.suffix.lower() in VIDEO and "sample" not in f.name.lower()]
    return max(vids, key=lambda f: f.stat().st_size, default=None)


def parse(name):
    name = re.sub(r"^www\.\S+\s+-\s+", "", name)
    m = re.match(r"(.+?)[. (]+((?:19|20)\d\d)\b", name)
    return (m[1].replace(".", " ").strip(), int(m[2])) if m else (name, None)


def poster(title, year):
    out = CACHE / f"{title} {year}.jpg"
    if out.exists():
        return out
    q = urllib.parse.quote(title.lower())
    d = json.load(urllib.request.urlopen(f"https://v3.sg.media-imdb.com/suggestion/x/{q}.json", timeout=10)).get("d", [])
    hits = [h for h in d if h.get("qid") == "movie" and "i" in h]
    hit = next((h for h in hits if h.get("y") == year), hits[0] if hits else None)
    if not hit:
        return None
    url = hit["i"]["imageUrl"].replace("._V1_.jpg", "._V1_SX400.jpg")  # ponytail: relies on IMDb's resize suffix
    out.write_bytes(urllib.request.urlopen(url, timeout=10).read())
    return out


CACHE.mkdir(parents=True, exist_ok=True)
cards = []
for p in sorted(ROOT.iterdir(), key=lambda p: parse(p.name)[0].lower()):
    if p.name.startswith(".") or not (v := video_of(p)):
        continue
    title, year = parse(p.name)
    try:
        img = poster(title, year)
    except Exception as e:
        print(f"no poster for {title}: {e}", file=sys.stderr)
        img = None
    link = "iina://open?url=" + urllib.parse.quote(v.as_uri(), safe="")
    pic = f'<img src="{img.as_uri()}">' if img else '<div class="none"></div>'
    cards.append(f'<a href="{link}">{pic}<b>{html.escape(title)}</b><i>{year or ""}</i></a>')

page = CACHE / "index.html"
page.write_text(f"""<!doctype html><meta charset=utf-8><title>Movies</title><style>
body{{margin:0;padding:24px;background:#111;color:#eee;font:14px -apple-system,sans-serif}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:20px}}
a{{color:inherit;text-decoration:none}} a:hover img{{outline:3px solid #fff}}
img,.none{{width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:6px;background:#333;display:block}}
b{{display:block;margin-top:6px}} i{{color:#999;font-style:normal}}
</style><main>{''.join(cards)}</main>""")
subprocess.run(["open", page])
