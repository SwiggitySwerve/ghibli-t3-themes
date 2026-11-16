"""Rebuild the three Nyx themes into ../themes/.

    python -I nyx/build.py

Each theme is the stock Nyx theme (base/nyx.json) with motion CSS appended:
- nyx-aurora-ocean: aurora glow, local flares, stars + the generated particle ocean (gen_ocean.py)
- nyx-animated:     "Aurora Pulse", shared motion layers + variant-aurora.css
- nyx-wave-streams: "Data Streams", shared motion layers + variant-streams.css
The file names are the theme ids T3 uses, so they match already-installed copies.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
THEMES = os.path.join(HERE, "..", "themes")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)


def run(*args):
    subprocess.run([sys.executable, "-I", *args], check=True, cwd=HERE)


ocean = os.path.join(OUT, "variant-ocean.css")
run("gen_ocean.py", ocean)
for theme_id, name, css in [
    ("nyx-aurora-ocean", "Nyx · Aurora Ocean", ["nyx-aurora-ocean.css", ocean]),
    ("nyx-animated", "Nyx · Aurora Pulse", ["nyx-common.css", "variant-aurora.css"]),
    ("nyx-wave-streams", "Nyx · Data Streams", ["nyx-common.css", "variant-streams.css"]),
]:
    run("build_nyx_animated.py", os.path.join("base", "nyx.json"), os.path.join(THEMES, f"{theme_id}.json"), name, *css)
