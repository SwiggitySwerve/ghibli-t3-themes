"""The Wind Rises: the summer hillside. Nahoko paints at her easel under the big white parasol,
Jiro reaches up as a paper plane rides the wind past them, and a silver gull-winged prototype
crosses the sky once per cycle.

Static layer (PNG, 16 colours): sky, cumulus, far hills, the hill, Jiro, Nahoko, easel.
Sprites (SVG): the fighter, the paper plane, parasol (sways), hat ribbon (flutters), wind
streaks in the grass.
"""
import math
from lib import Canvas, W, H

NAME = "The Wind Rises"
COLORS = 16

S = ["#2866c4", "#3d82d6", "#5b9fe3", "#7fbaec", "#b0d8f4"]     # sky top -> horizon
WH, SH = "#ffffff", "#c5d3ee"                                    # cloud / cloth light and shadow
FAR, MID = "#7fb0c8", "#5c9f86"                                  # far mountains, middle hills
G1, G2, G3, G4 = "#a5d95a", "#77c043", "#4f9f3c", "#2f7d3b"      # hill: rim, body, shade, foreground
SKIN, DARK, BROWN = "#f4c49a", "#2b2433", "#8a5a34"
CX, CY = 143, 80     # hill crest


def bands(cv, y, rows, soft=True):
    """rows: [(y_end, colour)]. Flat bands with an ordered-dither seam (see spirited_away)."""
    prev = None
    for y1, c in rows:
        for yy in range(y, y1):
            k = yy - y + (0 if soft else 1)
            for x in range(cv.w):
                mix = prev and ((k == 0 and (x % 4 != (yy % 2) * 2)) or (k == 1 and (x + yy) % 2)
                                or (k == 2 and soft and x % 4 == (yy % 2) * 2))
                cv.set(x, yy, prev if mix else c)
        prev, y = c, y1


def cloud(cv, circles, base, dim):
    """Summer cumulus: white balls painted back to front; a ball with sh=1 gets a shadowed
    lower-right crescent, so nearer white balls bite cauliflower edges into it. Flat shadowed base."""
    for cx, cy, r, sh in circles:
        for y in range(int(cy - r), min(base, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + .5 - cx, y + .5 - cy
                if math.hypot(dx, dy) <= r:
                    shade = (sh and (.5 * dx + .86 * dy) > .3 * r) or y >= dim
                    cv.set(x, y, SH if shade else WH)


def hill(x):
    d = x - CX
    return CY + (.0042 if d < 0 else .0012) * d * d


PAL = {"w": WH, "l": SH, "s": SKIN, "k": DARK, "b": BROWN, "g": G2, "c": S[2]}
JIRO = [
    "............ss",
    "...........ss.",
    "...........ww.",
    "...wwww....ww.",
    "..wwwwww..ww..",
    "..kkkkkk..ww..",
    "lwwwwwwww.ww..",
    "..kkssss.ww...",
    "..ksskskwww...",
    "..ksssssww....",
    "...ssss.wl....",
    "..wwwwwwwl....",
    ".wwwwkwwl.....",
    ".wlwwkwwl.....",
    ".wlwwkwwl.....",
    ".wlwwwwwl.....",
    ".wlwwwwwl.....",
    ".wlwwwwwl.....",
    ".s.wwlww......",
    "...wwlww......",
    "...wwlww......",
    "...ww.wl......",
    "...ww.wl......",
    "...ww.wl......",
    "...ww.wl......",
    "...ww.wl......",
    "..bbb.bbb.....",
]
NAHOKO = [
    "....wwwww....",
    "...wwwwwww...",
    "...wwwwwww...",
    "wwwwwwwwwwwwl",
    "...ssskkk....",
    "..ssskkkkk...",
    "...sskkkkk...",
    "....swkkk....",
    "...wwwwwl....",
    "sswwwwwwl....",
    "...wwwwwl....",
    "...wwwwl.....",
    "...lllll.....",
    "..wwwwwwl....",
    "..wwwwwwwl...",
    "..wwwwlwwl...",
    ".wwwwwlwwwl..",
    ".wwwwwlwwwl..",
    ".wwwwlwwwwwl.",
    ".wwwwlwwwwwll",
    "wwwwwlwwwwwwl",
    ".wwwwwwwwwwl.",
    "....s...s....",
    "....s...s....",
    "...bb..bb....",
]
EASEL = [
    "....b.....",
    ".wwwwwwww.",
    ".wccccccw.",
    ".wcwwcccw.",
    ".wccccwcw.",
    ".wcgggccw.",
    ".wggggggw.",
    ".wwwwwwww.",
    "bbbbbbbbbb",
    ".b..b...b.",
    ".b..b...b.",
    ".b..b...b.",
    ".b...b..b.",
    ".b...b..b.",
    ".b...b..b.",
    "b....b...b",
    "b.....b..b",
    "b.....b..b",
    "b.....b..b",
]


def draw():
    cv = Canvas()
    bands(cv, 0, [(16, S[0]), (38, S[1]), (62, S[2]), (84, S[3]), (H, S[4])])
    for x, y, n, c in [(150, 9, 44, S[1]), (164, 10, 20, S[1]), (104, 25, 30, S[2]), (112, 26, 12, S[2]),
                       (178, 29, 34, S[2]), (186, 48, 22, S[3])]:
        cv.rect(x, y, n, 1, c)        # thin high streaks
    # cumulus: a tall tower on the left, a lower bank on the right
    cloud(cv, [(44, 30, 13, 0), (36, 50, 22, 0), (30, 74, 30, 0), (62, 78, 20, 0),
               (44, 21, 9, 0), (58, 30, 7, 1), (30, 33, 10, 0), (66, 45, 9, 1), (46, 40, 11, 1),
               (14, 50, 11, 0), (34, 51, 12, 0), (76, 62, 9, 1), (56, 59, 12, 1), (26, 63, 12, 1),
               (3, 66, 12, 0), (40, 69, 13, 0), (80, 79, 9, 1), (60, 78, 10, 1), (14, 78, 13, 0)], 98, 90)
    cloud(cv, [(220, 76, 20, 0), (217, 51, 9, 0), (229, 60, 10, 1), (205, 62, 9, 0), (214, 70, 10, 1),
               (238, 74, 9, 1), (196, 78, 8, 0)], 92, 92)
    # far mountains and middle hills
    cv.ridge(94, [(4, .03, 1), (2, .11, 0)], FAR, 3, 0)
    cv.ridge(104, [(4, .045, 2.5), (1.5, .16, 0)], MID, 5, 0)
    # the hill: lit rim, body, shaded right flank, dark band at the foot
    for x in range(W):
        y0 = int(round(hill(x)))
        for y in range(y0, H):
            d = y - y0
            e = y - (92 + .25 * (190 - x))
            c = G3 if e > 0 or (e > -1 and (x + y) % 2) else G2
            if d < 2 + (x < CX):
                c = G1
            if y > 121 + (x + y) % 2:
                c = G4
            cv.set(x, y, c)
        if x % 5 == 2 and x > 58:
            cv.set(x, y0 - 1, G1)   # grass tips along the skyline
    cv.paint(JIRO, PAL, 96, int(hill(100)) - 26)
    cv.paint(EASEL, PAL, CX - 21, CY - 17)
    cv.rect(CX - 11, CY - 15, 2, 1, BROWN)      # her brush
    cv.paint(NAHOKO, PAL, CX - 9, CY - 24)
    return cv


# The fighter and the paper plane are parked off-canvas in their own coordinates and each run one
# linear `to` keyframe. Small details are stroked 1px runs at y+.5.
FX, FY = -60, 30      # fighter, nose right
PX, PY = -30, 124     # paper plane
SPRITES = (
    f"<g class='wr-j'><path fill='#eef' d='M{FX + 1} {FY}h2v2h22v3h-21v-1h-3v-1h-1v-2h1z'/>"
    f"<path fill='#abc' d='M{FX + 4} {FY + 4}h9v1h11v1h-3v1h-6v-1h-3v-1h-8z'/>"
    f"<path fill='#334' d='M{FX + 25} {FY + 2}h2v3h-2zm-7-1h2v1h-2zm-1 6h2v1h-2z'/>"
    f"<path fill='red' d='M{FX + 8} {FY + 2}h2v2h-2z'/>"
    f"<path stroke='#334' d='M{FX + 28}.5 {FY}v7'/></g>"
    # paper plane (before the parasol, so it slips behind the canopy)
    f"<g class='wr-a'><g class='wr-b'><path stroke='#fff' d='M{PX} {PY}.5h2m-1 1h5m-4 1h9m-3 1h4'/>"
    f"<path stroke='#abc' d='M{PX + 3} {PY + 3}.5h5m-4 1h3'/></g></g>"
    # parasol: pole, canopy, shaded panels; sways about the foot of the pole
    "<g class='wr-p'><path stroke='#853' d='M153 33v48'/>"
    "<path fill='#fff' d='M149 35h8v1h4v1h3v1h2v1h1v1h1v1h1v4h-2v-2h-8v2h-2v-2h-8v2h-2v-2h-8v2h-2v-4h1v-1h1v-1h1v-1h2v-1h3v-1h4z'/>"
    "<path fill='#cde' d='M159 36h2v1h3v1h2v1h1v1h1v1h1v4h-2v-2h-8z'/></g>"
    # hat ribbon and its fluttering tail
    "<path stroke='#d33' d='M137 58.5h7'/><path class='wr-f' stroke='#d33' d='M147 59.5h2m0 1h2'/>"
    # wind running through the grass
    "<g stroke='#ce8'><path class='wr-g' d='M92 97.5h5m7-5h6m2 9h5m5-13h5m-29 18h6'/>"
    "<path class='wr-g' style='animation-delay:-1.5s' d='M138 90.5h6m6 7h5m7-9h6m-24 16h6m20-9h5'/>"
    "<path class='wr-g' style='animation-delay:-3s' d='M184 92.5h5m9-3h6m-12 11h6m14-6h5m5-1h4'/></g>"
)
CSS = (
    ".wr-j{animation:wr-j 80s -64s linear infinite}@keyframes wr-j{to{transform:translate(1160px,-46px)}}"
    ".wr-p{transform-origin:153px 81px;animation:wr-p 3.4s ease-in-out infinite alternate}"
    "@keyframes wr-p{from{transform:rotate(-14deg)}to{transform:rotate(-6deg)}}"
    ".wr-f{animation:wr-f .6s steps(1) infinite}@keyframes wr-f{50%{transform:translateY(-1px)}}"
    ".wr-g{animation:wr-g 4.5s linear infinite}"
    "@keyframes wr-g{from{transform:translateX(-10px);opacity:0}50%{opacity:1}to{transform:translateX(14px);opacity:0}}"
    ".wr-a{animation:wr-a 40s linear infinite}@keyframes wr-a{to{transform:translate(635px,-349px)}}"
    ".wr-b{animation:wr-b 2.3s ease-in-out infinite alternate}@keyframes wr-b{to{transform:translateY(4px)}}"
)
