"""Build out/gallery_full.html: every scene's live animated SVG with its theme swatches and size.
Reads out/<slug>/scene.svg and theme.json, so run build_scene.py for each slug first."""
import json, os
from lib import svg_escape

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["spirited_away", "totoro", "mononoke", "howl", "kiki", "ponyo", "laputa", "heron", "nausicaa", "windrises"]

cards = []
for i, s in enumerate(ORDER):
    d = os.path.join(HERE, "out", s)
    t = json.load(open(os.path.join(d, "theme.json"), encoding="utf-8"))
    svg = open(os.path.join(d, "scene.svg"), encoding="utf-8").read()
    sw = "".join(f"<i style='background:{c}' title='{c}'></i>"
                 for c in (t["canvas"], t.get("colors", {}).get("sidebar", t["canvas"]), t["accent"]))
    cards.append(f"<figure><div class=f><img src=\"data:image/svg+xml,{svg_escape(svg)}\"></div><figcaption>"
                 f"<b>{i + 1}. {t['name'].split(' · ')[1]}</b><span class=m>{sw}<em>{len(t['css']):,} / 20,000</em></span>"
                 f"</figcaption></figure>")

html = ("<!doctype html><html><head><meta charset=utf-8><style>"
        ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}"
        "figure{margin:0;background:var(--card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}"
        ".f{aspect-ratio:16/9}img{width:100%;height:100%;display:block;image-rendering:pixelated}"
        "figcaption{padding:8px 12px 10px;display:flex;justify-content:space-between;align-items:center;gap:8px}"
        ".m{display:flex;align-items:center;gap:4px}.m i{width:14px;height:14px;border-radius:4px;display:inline-block;"
        "border:1px solid var(--border)}.m em{font-style:normal;color:var(--muted-foreground);font-size:12px;margin-left:6px;white-space:nowrap}"
        f"</style></head><body><div class=g>{''.join(cards)}</div></body></html>")
open(os.path.join(HERE, "out", "gallery_full.html"), "w", encoding="utf-8").write(html)
print(len(html))
