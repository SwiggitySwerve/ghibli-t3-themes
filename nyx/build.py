"""Rebuild the three Nyx themes into ../themes/.

    python -I nyx/build.py

Each theme is the stock Nyx theme (base/nyx.json) with motion CSS appended:
- nyx-aurora-ocean: aurora glow (image baked into glow.css by tools/bake_glow.mjs), local
                    flares, stars, the teal stream (teal-stream.css, tools/bake_teal.mjs)
                    + the generated particle ocean (gen_ocean.py)
- nyx-aurora-ocean-still-sky: the same with the sky frozen (still-sky.css), so only the
                    ocean moves; much lighter on the GPU
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


# Frame rate for the Aurora Ocean motion, both inside the ocean SVG and for the
# page layers (step_motion.py). Override with NYX_FPS; the ocean needs a
# multiple of 4 so its eight wave columns share one step grid.
FPS = int(os.environ.setdefault("NYX_FPS", "20"))
PAGE_FPS = int(os.environ.get("NYX_PAGE_FPS", FPS))

ocean = os.path.join(OUT, "variant-ocean.css")
run("gen_ocean.py", ocean)
for theme_id, name, flags, css in [
    ("nyx-aurora-ocean", "Nyx · Aurora Ocean", [f"--step-fps={PAGE_FPS}"], ["nyx-aurora-ocean.css", "glow.css", "teal-stream.css", ocean]),
    ("nyx-aurora-ocean-still-sky", "Nyx · Aurora Ocean (still sky)", [f"--step-fps={PAGE_FPS}"],
     ["nyx-aurora-ocean.css", "glow.css", "teal-stream.css", ocean, "still-sky.css"]),
    ("nyx-animated", "Nyx · Aurora Pulse", [], ["nyx-common.css", "variant-aurora.css"]),
    ("nyx-wave-streams", "Nyx · Data Streams", [], ["nyx-common.css", "variant-streams.css"]),
]:
    run("build_nyx_animated.py", *flags, os.path.join("base", "nyx.json"), os.path.join(THEMES, f"{theme_id}.json"), name, *css)
