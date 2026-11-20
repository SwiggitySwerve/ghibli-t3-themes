"""Append motion CSS files to stock nyx.json and write a new theme file.

Usage: python -I build_nyx_animated.py [--step-fps=N] <nyx.json> <out.json> <theme name> <css>...

--step-fps=N makes the appended CSS animations advance in steps at N frames a
second (see step_motion.py).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step_motion import step_motion  # noqa: E402


def minify(css):
    """Drop comments and collapse whitespace; punctuation is left alone so the
    SVG data URIs (which hold single spaces between attributes) stay intact."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.sub(r"\s+", " ", css).strip()


args = sys.argv[1:]
step_fps = int(args.pop(0).split("=", 1)[1]) if args[0].startswith("--step-fps=") else None
src, out, name, *css_files = args
theme = json.load(open(src, encoding="utf-8"))
theme["name"] = name
motion = "".join(minify(open(path, encoding="utf-8").read()) for path in css_files)
theme["css"] += step_motion(motion, step_fps) if step_fps else motion
# T3 Code allowed 50,000 chars of theme CSS until late 2026 and 100,000 since
if len(theme["css"]) > 100000:
    sys.exit(f"css is {len(theme['css'])} chars, over T3's 100,000 limit")
json.dump(theme, open(out, "w", encoding="utf-8"), separators=(",", ":"))
print(f"wrote {out}: css {len(theme['css'])} chars")
