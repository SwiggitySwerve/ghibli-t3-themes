"""Append motion CSS files to stock nyx.json and write a new theme file.

Usage: python -I build_nyx_animated.py <nyx.json> <out.json> <theme name> <css>...
"""
import json
import re
import sys


def minify(css):
    """Drop comments and collapse whitespace; punctuation is left alone so the
    SVG data URIs (which hold single spaces between attributes) stay intact."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.sub(r"\s+", " ", css).strip()


src, out, name, *css_files = sys.argv[1:]
theme = json.load(open(src, encoding="utf-8"))
theme["name"] = name
for path in css_files:
    theme["css"] += minify(open(path, encoding="utf-8").read())
if len(theme["css"]) > 50000:
    sys.exit(f"css is {len(theme['css'])} chars, over T3's 50,000 limit")
json.dump(theme, open(out, "w", encoding="utf-8"), separators=(",", ":"))
print(f"wrote {out}: css {len(theme['css'])} chars")
