"""Format reference only (a plain hillside meadow). Not one of the ten scenes.

A scene file defines:
  NAME     display name
  COLORS   palette size for PNG quantization (fewer colours = smaller file)
  draw()   -> lib.Canvas, the static 240x135 pixel layer
  SPRITES  raw SVG drawn over the pixel layer in the same 240x135 coordinates (use '#' colours freely)
  CSS      keyframes for the sprites. Every class and @keyframes name MUST start with this scene's
           prefix (here 'ex-') because all scenes share one <style> in the final theme.
"""
import math, random
from lib import Canvas, W, H, sprite

NAME = "Example meadow"
COLORS = 32


def draw():
    cv = Canvas()
    cv.bands(0, 100, ["#3f7fd0", "#4f92dc", "#64a6e6", "#7fbaee", "#9ccdf3", "#bfe0f7"])
    cv.blob([(175, 52, 16), (195, 48, 19), (214, 56, 14), (186, 36, 14), (203, 28, 13)],
            "#ffffff", "#eef3fb", "#c7d3e8")
    cv.ridge(86, [(4, .025, 2), (2, .09, 0)], "#86b9c4", 2, 0)
    p = cv.ridge(104, [(7, .018, 1.4), (2, .05, 2)], "#62a94a", 4, 1, "#86c661")
    r = random.Random(9)
    for _ in range(200):
        x, y = r.randrange(W), r.randrange(110, H)
        cv.set(x, y, r.choice(["#4b8f3d", "#ffffff", "#ffe08a"]))
    return cv


# A sprite from ASCII art: '.' is transparent. Two frames, toggled with steps(1) for a pixel blink.
SHEEP = ["..wwww..", ".wwwwwwk", "wwwwwwkk", ".wwwwww.", ".k.k.k.."]
SHEEP_BLINK = ["........", ".......w", "........", "........", "........"]
PAL = {"w": "#f4f1ea", "k": "#2a2a30"}

SPRITES = (
    "<path fill='#fff' class='ex-d' d='M6 14h8v2h4v2h3v3h2v3H0v-3h2v-3h2v-2h2z'/>"
    "<path fill='#334' class='ex-b' d='M0 30h1v1h2v1h1v-1h2v-1h1v1h-1v1h-2v1h-1v-1h-2v-1h-1z'/>"
    f"<g class='ex-graze'>{sprite(SHEEP, PAL, 90, 104)}<g class='ex-blink'>{sprite(SHEEP_BLINK, PAL, 90, 104)}</g></g>"
)
CSS = (
    ".ex-d{animation:ex-d 140s linear infinite}@keyframes ex-d{from{transform:translateX(-30px)}to{transform:translateX(250px)}}"
    ".ex-b{animation:ex-b 38s linear infinite}@keyframes ex-b{from{transform:translate(-10px,10px)}to{transform:translate(250px,-6px)}}"
    ".ex-graze{animation:ex-g 20s steps(10) infinite alternate}@keyframes ex-g{to{transform:translateX(20px)}}"
    ".ex-blink{opacity:0;animation:ex-k 4s steps(1) infinite}@keyframes ex-k{90%{opacity:1}}"
)
