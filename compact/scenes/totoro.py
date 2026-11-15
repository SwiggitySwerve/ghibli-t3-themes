"""My Neighbor Totoro: the rainy-night bus stop. Totoro stands under a too-small umbrella beside
Satsuki (Mei asleep on her back) in the pool of a lone streetlamp, the camphor tree looms behind
the forest edge, paddies open out to the right, and the Catbus bounds along the power line once
per cycle.

Static layer (PNG, 16 colours): sky, far hills, paddies, camphor, forest, pole + lamp, road and
every character. Sprites (SVG): Catbus, the drip + blink + splash, lamp light (cone, pool, puddle
streaks), rain as one scrolling <pattern>.

Custom properties inherit, so nested animated groups reset --x/--y (see CSS).
"""
import math
from lib import Canvas, W, H

NAME = "My Neighbor Totoro"
COLORS = 16

S = ["#1b2a62", "#27477f", "#33658f", "#4f8ba3"]     # sky top -> horizon
CAM, FOR, LEAF = "#1b3a56", "#0c1c28", "#24504a"
SHADE, TOT, CREAM, WHITE = "#4a5266", "#778899", "#e6dfc0", "#ffffff"
BLACK, YEL, RED, SKIN, BLUE = "#0a0c16", "#ffdd77", "#e0603a", "#f4c09a", "#4a7fd0"
RD = 103             # road top row; feet stand on row 107
TX, PX = 136, 116    # Totoro centre, utility pole


def bands(cv, y, rows):
    """rows: [(y_end, colour)]. Flat bands with a 3-row ordered-dither seam (25/50/75%)."""
    prev = None
    for y1, c in rows:
        for yy in range(y, y1):
            k = yy - y
            for x in range(cv.w):
                mix = prev and ((k == 0 and (x % 4 != (yy % 2) * 2)) or (k == 1 and (x + yy) % 2)
                                or (k == 2 and x % 4 == (yy % 2) * 2))
                cv.set(x, yy, prev if mix else c)
        prev, y = c, y1


def canopy(cv, circles, mid, hi=None, ymax=H):
    """Circles painted back to front, optionally with a lit upper-left rim."""
    for cx, cy, r in circles:
        for y in range(int(cy - r), min(ymax, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + .5 - cx, y + .5 - cy
                d = math.hypot(dx, dy)
                if d <= r:
                    rim = hi and d > r - 1.7 and (-.6 * dx - .8 * dy) > .3 * r
                    cv.set(x, y, hi if rim else mid)


def cedar(cv, cx, top, hw, c):
    """A tiered conifer silhouette from `top` down to the road."""
    for y in range(top, RD):
        k = y - top
        w = min(hw, 1 + k // 6 + (k % 6) // 3)
        cv.rect(cx - w, y, 2 * w, 1, c)


def totoro(cv, cx, by):
    hw = [4, 6, 7, 8, 8, 9, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 13, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14,
          13, 13, 12, 11, 9]
    top = by - len(hw)
    for i, w in enumerate(hw):
        cv.rect(cx - w, top + i, 2 * w, 1, TOT)
        if i > 3:
            cv.rect(cx + w - 2, top + i, 2, 1, SHADE)       # shadow side, away from the lamp
        if i > 12:                                           # belly
            b = min(w - 3, int(round(10.5 * math.sqrt(max(0, 1 - ((i - 22) / 10.5) ** 2)))))
            cv.rect(cx - b, top + i, 2 * b, 1, CREAM)
    for s in (1, -1):                                        # ears
        for k, (a, n) in enumerate([(9, 1), (9, 2), (9, 3), (9, 3), (8, 3), (7, 3)]):   # leaf-shaped, tilted out
            x = cx - a if s > 0 else cx + a - n
            cv.rect(x, top - 5 + k, n, 1, TOT)
    for ex in (cx - 7, cx + 3):                              # eyes
        cv.rect(ex, top + 5, 4, 4, WHITE)
        cv.rect(ex + 1, top + 6, 2, 2, BLACK)
        for dx, dy in ((0, 0), (3, 0), (0, 3), (3, 3)):
            cv.set(ex + dx, top + 5 + dy, TOT)
    cv.rect(cx - 2, top + 6, 4, 1, BLACK)                    # nose
    cv.rect(cx - 1, top + 7, 2, 1, BLACK)
    for x, y in [(-6, 15), (-1, 15), (4, 15), (-8, 19), (-3, 19), (2, 19), (7, 19)]:   # chest chevrons
        cv.set(cx + x, top + y, TOT)
        cv.set(cx + x - 1, top + y + 1, TOT)
        cv.set(cx + x + 1, top + y + 1, TOT)
    for s in (1, -1):                                        # whiskers
        for k in (0, 2):
            cv.rect(cx - 13 - k if s > 0 else cx + 10 + k, top + 9 + k, 3, 1, TOT)
    cv.rect(cx - 13, top + 14, 1, 9, SHADE)                  # hanging arm
    cv.rect(cx - 12, top + 23, 2, 1, SHADE)
    for x in (cx - 9, cx + 5):                               # toes
        cv.rect(x, by - 1, 4, 1, SHADE)
    # umbrella: canopy slightly off his head, shaft down the side of his face into a paw
    ux = cx + 7
    for k, w in enumerate([1, 4, 7, 9, 11, 12, 12]):
        cv.rect(ux - w, top - 13 + k, 2 * w, 1, BLACK)
        if 0 < k < 5:
            cv.rect(ux - w, top - 13 + k, 3, 1, TOT)         # lamp-lit rim
    for x in range(ux - 12, ux + 12, 6):
        cv.rect(x, top - 6, 1, 1, BLACK)
    cv.rect(ux - 1, top - 15, 1, 2, BLACK)
    cv.rect(cx + 10, top - 6, 1, 18, BLACK)
    cv.rect(cx + 8, top + 11, 4, 3, TOT)
    cv.rect(cx + 8, top + 14, 4, 1, SHADE)


GIRLS = [
    ".......o.......",
    "....ooooooo....",
    "..ooooooooooo..",
    ".ooooooooooooo.",
    "ooooooooooooooo",
    "......kkkk.p...",
    ".....kkkkkkp...",
    ".....ksssskp...",
    ".mmm.ksssskp...",
    "mmmm..ssss.p...",
    "msss.yyyyyys...",
    ".ccccyyyyyy....",
    ".ccccyyyyyy....",
    ".cccoooooo.....",
    "..ccoooooo.....",
    "..s.oooooooo...",
    "..y.oooooooo...",
    "......s..s.....",
    "......s..s.....",
    "......s..s.....",
    "......s..s.....",
    "......c..c.....",
    ".....kk.kk.....",
]
CHU = [
    ".b....b.",
    ".b....b.",
    ".bbbbbb.",
    "bwkbbkwb",
    "bbbbbbbb",
    "bbccccbb",
    "bccccccb",
    "bccccccb",
    ".bbbbbb.",
]
CHIBI = [
    "w...w",
    "w...w",
    "wwwww",
    "wkwkw",
    "wwwww",
    ".www.",
]
PAL = {"o": RED, "k": BLACK, "s": SKIN, "y": YEL, "c": CREAM, "m": RED, "p": SHADE, "b": BLUE, "w": WHITE}


def draw():
    cv = Canvas()
    bands(cv, 0, [(14, S[0]), (34, S[1]), (56, S[2]), (RD, S[3])])
    for x, y, n, c in [(18, 20, 46, S[0]), (30, 21, 22, S[0]), (160, 9, 50, S[1]), (176, 40, 44, S[1]),
                       (190, 41, 20, S[1])]:
        cv.rect(x, y, n, 1, c)                # thin rain-cloud streaks
    # far hills, a farmhouse with one lit window, paddies reflecting the sky
    for x in range(150, W):
        h = int(round(5 + 3 * math.sin(x * .05)))
        cv.rect(x, 80 - h, 1, h, CAM)
    for y0, y1, c in [(80, 84, S[3]), (84, 90, S[2]), (90, RD, S[1])]:
        cv.rect(150, y0, W - 150, y1 - y0, c)
        cv.rect(150, y0, W - 150, 1, CAM)
    cv.rect(211, 75, 9, 2, FOR)
    cv.rect(212, 77, 7, 3, CAM)
    cv.rect(214, 77, 2, 2, YEL)
    for y, n in ((87, 4), (95, 6)):       # seedling rows
        for x in range(190 + y % 3, W, n):
            cv.set(x, y, CAM)
    # the camphor tree: one huge crown behind the forest
    canopy(cv, [(84, 58, 13), (156, 58, 13), (97, 46, 18), (143, 46, 18), (120, 36, 24), (106, 25, 14),
                (133, 23, 15)], CAM, LEAF)
    # forest edge: cedars framing the left, broadleaf bumps across to the paddies
    for cx, top, hw in [(6, 20, 9), (23, 33, 8), (39, 26, 8), (171, 38, 7), (184, 52, 6)]:
        cedar(cv, cx, top, hw, FOR)
    canopy(cv, [(x, 70 + (i * 5) % 7, 10) for i, x in enumerate(range(48, 176, 12))], FOR, ymax=RD)
    cv.rect(44, 78, 136, RD - 78, FOR)
    # lamp-lit foliage behind the cast, so the black umbrella has something to stand against
    canopy(cv, [(x, 96 + (i * 3) % 5, 9) for i, x in enumerate(range(64, 180, 13))]
           + [(106, 92, 14), (124, 82, 13), (146, 78, 21), (165, 94, 11)], LEAF, ymax=RD)
    # utility pole, crossarm, sagging wire, streetlamp
    for x in range(W):
        cv.set(x, 45 + int(round(3 * (1 - ((x - PX) % 120 - 60) ** 2 / 3600))), SHADE)
    cv.rect(PX, 42, 2, RD - 42, SHADE)
    cv.rect(PX - 5, 44, 12, 1, SHADE)
    cv.rect(PX + 2, 54, 4, 1, SHADE)
    cv.rect(PX + 5, 55, 5, 1, BLACK)
    cv.rect(PX + 4, 56, 7, 1, BLACK)
    cv.rect(PX + 5, 57, 5, 1, YEL)
    cv.rect(PX + 6, 58, 3, 1, WHITE)
    # road
    cv.rect(0, RD, W, H - RD, SHADE)
    cv.rect(0, RD, W, 1, FOR)
    for x, y, n in [(20, 110, 16), (150, 112, 22), (60, 115, 30), (186, 108, 12)]:
        cv.rect(x, y, n, 1, S[2])
    # the little Inari shrine gate by the stop, then the bus stop sign
    cv.rect(57, 87, 18, 2, RED)
    cv.rect(60, 92, 12, 1, RED)
    for x in (61, 69):
        cv.rect(x, 89, 2, RD - 89, RED)
    cv.rect(91, 86, 1, 22, SHADE)
    canopy(cv, [(91.5, 82.5, 3.6)], CREAM)
    cv.rect(88, 82, 7, 1, RED)
    cv.rect(89, 88, 5, 4, CREAM)
    # the cast
    cv.paint(GIRLS, PAL, 97, 85)
    totoro(cv, TX, 108)
    cv.paint(CHU, PAL, 152, 99)
    cv.paint(CHIBI, PAL, 161, 102)
    return cv


def catbus():
    """Faces right, parked off-canvas left. Legs are one dashed stroke that scrolls backwards."""
    o, b, y = "#d93", "#a52", "#fe8"
    return (
        "<g transform='translate(-90 30)'><g class='tt-c'><g class='tt-b'>"
        f"<path fill='{y}' opacity='.25' d='M45 4l40-5v18l-40-9z'/>"
        f"<path class='tt-g' stroke='{o}' stroke-width='5' stroke-dasharray='2 4' d='M9 14.5h30'/>"
        f"<path fill='{o}' d='M1 0h2v3h1v2h1v1h1v3h-2v-1h-1v-1h-1v-2h-1v-2h-1v-2h1z"
        "M8 3h26v9h-26v-1h-1v-1h-1v-5h1v-1h1z"
        "M35 0h9v1h1v1h1v9h-1v1h-1v1h-9v-1h-1v-1h-1v-9h1v-1h1z"
        "M35-3h1v1h1v2h-3v-2h1zM43-3h1v1h1v2h-3v-2h1z'/>"
        f"<path stroke='{y}' stroke-width='3' stroke-dasharray='5 1' d='M9 7.5h23'/>"
        "<path stroke='#fff' stroke-width='3' stroke-dasharray='3 1' d='M34 10.5h11M35 4.5h3m3 0h3'/>"
        f"<path stroke='{b}' d='M10 3.5h3m3 0h3m3 0h3m3 0h3M0 2.5h3m-1 3h3M39 7.5h2M36 4.5h1m5 0h1'/>"
        "</g></g></g>"
    )


SPRITES = (
    catbus()
    # a drip swells on the wire, falls onto the umbrella; Totoro blinks as it lands
    + "<path class='tt-d' fill='#9cf' d='M143 47h1v2h-1z'/>"
      "<g class='tt-k'><path fill='#789' d='M129 81h4v4h-4zm10 0h4v4h-4z'/>"
      "<path stroke='#012' d='M129 83.5h4m6 0h4'/><path stroke='#9cf' d='M140 60.5h1m3 0h1m-6-1h1m5 0h1'/></g>"
    # lamp light: cone, pool on the road, two lit puddle streaks
    + "<g class='tt-f' fill='#fd8'><path opacity='.22' d='M121 59h5l36 49h-77z'/>"
      "<path opacity='.25' d='M93 107h60v1h8v3h-8v1h-60v-1h-8v-3h8zm9 7h12v1h-12zm30 1h16v1h-16z'/></g>"
    # rain
    + "<pattern id='tt-p' x='.5' width='30' height='40' patternUnits='userSpaceOnUse'>"
      "<path stroke='#9cf' d='M3 1v3M18 6v3M10 13v3M26 19v3M6 25v3M21 30v3M14 36v3'/></pattern>"
      "<rect class='tt-r' y='-40' width='240' height='175' fill='url(#tt-p)' opacity='.35'/>"
)
CSS = (
    "@keyframes tt-m{to{transform:translate(var(--x,0),var(--y,0))}}"
    ".tt-c{--x:1500px;animation:tt-m 50s linear infinite}"
    ".tt-b{--x:0;--y:-3px;animation:tt-m .3s steps(3) infinite alternate}"
    ".tt-g{--x:-6px;--y:0;animation:tt-m .3s steps(3) infinite}"
    ".tt-d{--y:13px;animation:tt-m 6s cubic-bezier(.9,0,1,0) infinite}"
    ".tt-r{--y:40px;animation:tt-m .5s steps(10) infinite}"
    ".tt-k{animation:tt-k 6s steps(1) infinite}@keyframes tt-k{4%{opacity:0}}"
    ".tt-f{animation:tt-f 9s steps(1) infinite}@keyframes tt-f{95%{opacity:.6}}"
)
