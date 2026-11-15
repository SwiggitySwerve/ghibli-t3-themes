"""The Boy and the Heron: the overgrown tower by the pond at night. Mahito stands on the bank with
his bow, the grey heron looms in the shallows opposite him, and between them the warawara rise in a
loose double helix towards the moon. Three pelicans cross the sky once per cycle.

Static layer (PNG, 16 colours): sky, moon, hills, trees, tower + vines, pond, bank, Mahito, heron, lily pads.
Sprites (SVG), back to front: pelicans, warawara (one <marker> stamped on every vertex of three
invisible polylines), pond ripples, the heron's crest plume, reeds.
"""
import math
from lib import Canvas, W, H

NAME = "The Boy and the Heron"
COLORS = 16

N = ["#0a1233", "#111f57", "#19387c", "#295a9f", "#4f8cba"]   # sky top -> horizon
INK = N[0]
CREAM, WARM, SKIN, PINK = "#f6f1da", "#f6b84a", "#f0c49a", "#ee88aa"
T1, G1, G2 = "#0e2c3e", "#2a7a55", "#6cc070"
P1, P2 = "#165a5e", "#2a8c80"
SL, SM = "#a3adc0", "#5d6b8c"
SHORE = 85           # far shoreline row
TX = 78              # tower centre column
MX, MY = 94, 88      # Mahito top-left
HX, HY = 136, 68     # heron top-left
BANK = 110           # top of the near bank


def bands(cv, y, rows, soft=True):
    """rows: [(y_end, colour)]. Flat bands with an ordered-dither seam (same helper as spirited_away)."""
    prev = None
    for y1, c in rows:
        for yy in range(y, y1):
            k = yy - y + (0 if soft else 1)
            for x in range(cv.w):
                mix = prev and ((k == 0 and (x % 4 != (yy % 2) * 2)) or (k == 1 and (x + yy) % 2)
                                or (k == 2 and soft and x % 4 == (yy % 2) * 2))
                cv.set(x, yy, prev if mix else c)
        prev, y = c, y1


def disc(cv, cx, cy, r, c, y_max=H):
    for y in range(int(cy - r), min(y_max, int(cy + r) + 1)):
        for x in range(int(cx - r), int(cx + r) + 1):
            if math.hypot(x + .5 - cx, y + .5 - cy) <= r:
                cv.set(x, y, c)


def spire(cv, cx, top, base, c):
    """A conifer: 1px tip widening one pixel per side every two rows."""
    for y in range(top, base):
        hw = (y - top) // 2
        cv.rect(cx - hw, y, 2 * hw + 1, 1, c)


def tower(cv, cx, by):
    def stone(x0, x1, y0, y1):
        for y in range(y0, y1):
            for x in range(x0, x1):
                lit = x >= cx - 4
                cv.set(x, y, SL if lit else SM)
    stone(cx - 12, cx + 12, 42, by)                 # main drum
    stone(cx - 9, cx + 9, 30, 40)                   # upper drum
    cv.rect(cx - 14, 40, 28, 1, SL)                 # cornice
    cv.rect(cx - 14, 41, 28, 1, SM)
    stone(cx - 15, cx + 15, 77, by)                 # plinth
    for y, hw in [(29, 11), (28, 10), (27, 9), (26, 8), (25, 6), (24, 4), (23, 2)]:   # slate dome
        cv.rect(cx - hw, y, 2 * hw, 1, SM)
    cv.rect(cx - 1, 19, 1, 4, SM)                   # finial
    for x, y in [(cx + 1, 46), (cx + 7, 55), (cx - 1, 66), (cx + 6, 70), (cx + 3, 62)]:
        cv.rect(x, y, 3, 1, SM)                     # a few stone courses
    # windows: lit arch up top, dark slits and the blocked doorway below
    cv.rect(cx - 1, 33, 3, 5, WARM)
    cv.rect(cx, 32, 1, 1, WARM)
    for x, y in [(cx + 5, 34), (cx + 3, 49), (cx + 8, 49), (cx, 58), (cx + 9, 60)]:
        cv.rect(x, y, 1, 4, INK)
    cv.rect(cx, 73, 5, by - 73, INK)
    cv.rect(cx + 1, 72, 3, 1, INK)
    # vines: a green curtain spilling over the left half, a clump climbing the right foot
    drips = [(-14, 39, 50), (-13, 38, 58), (-12, 36, 68), (-11, 28, 61), (-10, 27, 72), (-9, 26, 54), (-8, 25, 64),
             (-7, 24, 47), (-6, 24, 58), (-5, 23, 43), (-4, 23, 50), (-3, 22, 36), (-2, 22, 31), (-1, 23, 27),
             (0, 22, 26), (1, 22, 28), (2, 23, 25),
             (13, 72, by), (12, 66, by), (11, 61, by), (10, 64, by), (9, 57, by), (8, 67, by), (7, 74, by), (6, 78, by),
             (-13, 74, by), (-12, 77, by), (-11, 72, by), (-10, 79, by)]
    for dx, y0, y1 in drips:
        cv.rect(cx + dx, y0, 1, y1 - y0, G1)
        cv.set(cx + dx, y1 - 1, T1)
    for dx, y in [(-11, 30), (-8, 27), (-5, 25), (-12, 40), (-9, 36), (-6, 33), (-10, 46), (-7, 42),
                  (-12, 52), (-8, 50), (11, 64), (9, 60)]:
        cv.set(cx + dx, y, G2)
    # reflection: broken streaks
    for y, x0, n, c in [(87, cx - 9, 18, SM), (89, cx - 7, 12, SM), (91, cx - 4, 8, SM), (88, cx - 12, 5, G1)]:
        cv.rect(x0, y, n, 1, c)


MAHITO = [
    "...kkkkk.......",
    "..kkkkkkk......",
    "..kkkkssk......",
    "..kkssssss.....",
    "..kksskss......",
    "..kkssssss.....",
    "...kssss.......",
    "...jwwwj.......",
    "..jjjjjjl......",
    ".jjjjjyjjj.....",
    ".jjjjjjjjjjjs..",
    ".jjjjjyjjj.....",
    ".jjjjjjjl......",
    ".jjjjjyjl......",
    "..jjjjjjl......",
    "..tttttt.......",
    "..ttt.ttt......",
    "..ttt.ttt......",
    "..ttt.ttt......",
    "..ttt.ttt......",
    "..ttt.ttt......",
    "..kkk.kkkk.....",
]
BOW = [11, 12, 12, 13, 13, 13, 14, 14, 14, 14, 14, 14, 13, 13, 13, 12, 12, 11]   # column per row, from row 2
HERON = [
    "..............kkkkk...........",
    "............wwwkkkkk..........",
    "...........wwwwwwwkk..........",
    "...........wwkwwwww...........",
    ".yyyyyyyyyywwwwwwww...........",
    ".....yyyyyywwwwwww............",
    "............wwwwwg............",
    ".............wwwwg............",
    "..............wwwwg...........",
    "...............wwwwg..........",
    "................wwwgg.........",
    "................wwwwg.........",
    "................wwwwg.........",
    "...............wwwwgg.........",
    "..............wwwwgg..........",
    ".............wwwwggg..........",
    "............wwwwggggggg.......",
    "...........wwwwgggggggggg.....",
    "...........wwwgkkggggggggg....",
    "..........wwwwgkkkggggggggg...",
    "..........wwwggkkggdddgggggg..",
    "..........wdwggggggggddddgggg.",
    "..........wwdgggggggggdddddggg",
    "...........wdwggggggggggdddddd",
    "...........wwdgggggggggggddddd",
    "............wwgggggggggggg.ddd",
    ".............wwgggggggggg...dd",
    "..............wwggggggg......d",
    "................ggggg.........",
    ".................y..y.........",
    ".................y..y.........",
    ".................y..y.........",
    "................y...y.........",
    ".................y..y.........",
    ".................y..y.........",
    ".................y..y.........",
    ".................y..y.........",
    ".................y..y.........",
]


def conifer(cv, cx, top, base, c):
    """A big tiered cedar: each tier widens a pixel per row, then steps back in."""
    hw = 0
    for y in range(top, base):
        hw = hw - 2 if (y - top) % 7 == 6 else hw + 1
        cv.rect(cx - hw, y, 2 * hw + 1, 1, c)


def draw():
    cv = Canvas()
    bands(cv, 0, [(10, N[0]), (27, N[1]), (46, N[2]), (66, N[3]), (SHORE, N[4])])
    for x, y in [(58, 5), (104, 13), (151, 6), (188, 16), (170, 30), (46, 24)]:
        cv.set(x, y, CREAM)
    disc(cv, 128, 27, 9, CREAM)
    for x, y, n, c in [(120, 30, 34, N[3]), (106, 32, 30, N[3]), (150, 39, 40, N[3]), (26, 20, 34, N[2]), (176, 13, 28, N[2])]:
        cv.rect(x, y, n, 1, c)                      # thin cloud streaks, one across the moon
    # far hill, then the tree line: tall conifers on the left behind the tower, low scrub on the right
    for x in range(W):
        y = 76 + round(3 * math.sin(x * .035 + 1) + 1.5 * math.sin(x * .11))
        cv.rect(x, y, 1, SHORE - y, N[3])
    for x in range(W):
        y = (67 if x < 106 else 80) + round(1.4 * math.sin(x * .5) + 1.2 * math.sin(x * .19))
        if 106 <= x < 116:
            y = 67 + (x - 105) * 13 // 10
        cv.rect(x, y, 1, SHORE - y, T1)
    for cx, top in [(36, 50), (45, 57), (53, 48), (61, 56), (98, 55), (105, 62), (112, 70), (176, 72), (184, 68), (192, 73)]:
        spire(cv, cx, top, SHORE, T1)
    for cx, top in [(4, 22), (22, 38), (236, 26), (218, 42), (203, 60)]:
        conifer(cv, cx, top, SHORE, INK)
    # pond: dark reflection under the far shore, then green water with a moonlit lane
    bands(cv, SHORE, [(88, T1), (H, P1)], soft=False)
    cv.rect(0, SHORE, W, 1, INK)
    for i, y in enumerate(range(90, 122, 2)):
        n = 6 + (i * 5) % 9 + i // 2
        cv.rect(128 - n + (i % 3) * 2, y, 2 * n, 1, P2)
        if i % 2 == 0:
            cv.rect(126 - (i % 3), y, 4 + i % 3, 1, CREAM)
    for x, y, n in [(20, 93, 9), (54, 97, 7), (160, 92, 8), (196, 99, 10), (176, 109, 9), (214, 113, 8), (30, 101, 6)]:
        cv.rect(x, y, n, 1, P2)
    tower(cv, TX, SHORE)
    # near bank on the left where Mahito stands
    for x in range(0, 120):
        y = BANK + (0 if x < 108 else (x - 107) // 2) + (1 if x % 7 == 3 else 0)
        cv.rect(x, y, 1, H - y, T1)
        cv.set(x, y, G1)
    pal = {"k": INK, "s": SKIN, "j": N[2], "t": N[1], "l": SM, "w": CREAM, "y": WARM}
    cv.paint(MAHITO, pal, MX, MY)
    for i, dx in enumerate(BOW):
        cv.set(MX + dx, MY + 2 + i, WARM)
    cv.paint(HERON, {"k": INK, "w": CREAM, "g": SL, "d": SM, "y": WARM}, HX, HY)
    # lily pads
    for x, y, f in [(172, 97, 0), (186, 103, 1), (200, 95, 0), (166, 110, 0), (62, 94, 0), (46, 98, 1), (28, 95, 0)]:
        cv.rect(x + 1, y, 4, 1, G2)
        cv.rect(x, y + 1, 6, 1, G2)
        cv.rect(x + 1, y + 2, 4, 1, G1)
        if f:
            cv.rect(x + 1, y - 1, 2, 1, PINK)
    return cv


def path_pts(pts):
    """Vertices -> compact relative polyline ("M118 140l7-17 2-16..."). Nothing is stroked or filled;
    the path only exists to carry a marker on every vertex."""
    s, (px, py) = f"M{pts[0][0]} {pts[0][1]}l", pts[0]
    for i, (x, y) in enumerate(pts[1:]):
        dx, dy = x - px, y - py
        s += f"{'' if i == 0 or dx < 0 else ' '}{dx}{'' if dy < 0 else ' '}{dy}"
        px, py = x, y
    return s


PERIOD = 150   # the rise keyframe moves exactly one period, so each path holds two identical periods


def strand(phase, off, jit, cx=122, amp=7, n=9):
    """One strand of the helix: a sine in x down the column, jittered. Translating it upward reads as
    a helix turning."""
    pts = []
    for k in range(2 * n):
        y = 290 - off - k * PERIOD / n
        x = cx + amp * math.sin(2 * math.pi * (y / 75) + phase) + jit[k % n]
        pts.append((round(x), round(y)))
    return path_pts(pts)


def scatter():
    base = [(30, 20), (205, 55), (60, 85), (182, 110), (48, 140), (170, 35)]
    return path_pts([(x, y + k * PERIOD) for k in range(2) for x, y in base])


def pelicans(x0=262, y=47, gaps=(0, 15, 27)):
    """Three pelicans in a line, flying left. Bodies are one path; the wings are another that flips
    about the body line (scaleY 1 -> -1) for a slow beat."""
    def row(dx, dy, shape):   # after "z" the pen is back at the subpath start, so later birds are relative moves
        return f"M{x0 + dx} {y + dy}{shape}" + "".join(f"m{b - a} 0{shape}" for a, b in zip(gaps, gaps[1:]))
    body = row(3, -2, "h2v1h5v1h1v1h-7v-1h-4v-1h3z")
    wing = row(7, -5, "h2v2h-1v2h-3v-2h1v-1h1z")
    return f"<g class='bh-g' fill='#fff'><path d='{body}'/><path class='bh-k' d='{wing}'/></g>"


SPRITES = (
    # one warawara: a white body with two eye holes
    "<marker id='bh-w' overflow='visible'>"
    "<path fill='#fff' d='M-2-2h4v1h1v3h-1v1h-4v-1h-1v-3h1zm0 2v1h1v-1zm3 0v1h1v-1z'/></marker>"
    + pelicans() +
    # warawara: the whole column leans with the same breeze as the reeds (bh-s) while it rises (bh-r)
    f"<g class='bh-s'><g class='bh-r'><path stroke-width='.6' d='{scatter()}'/>"
    f"<path d='{strand(0, 0, (0, 1, -1, 1, -1, 0, 1, -1, 1))}'/>"
    f"<path d='{strand(math.pi, 8, (1, -1, 0, 1, -1, 1, 0, -1, 1))}'/></g></g>"
    # ripples that come and go around the heron's legs and across the pond
    f"<path class='bh-f' stroke='#4ba' d='M{HX + 12} {HY + 38}.5h4m3 0h6m-17 2h7m-70-9h6m114 3h7'/>"
    # heron crest plume
    f"<path class='bh-p' stroke='#113' fill='none' d='M{HX + 19} {HY + 1}.5h4l4 2m-7-1h4l3 3'/>"
    # reeds
    "<path class='bh-s' fill='#113' d='M76 135v-34h-1v-6h3v6h-1v34zm5 0v-27h-1v-5h3v5h-1v27z"
    "M170 135v-30h-1v-6h3v6h-1v30zm6 0v-38h-1v-6h3v6h-1v38z'/>"
)
CSS = (
    ".bh-r path{fill:none;marker:url(#bh-w)}"
    ".bh-r{animation:bh-r 50s linear infinite}@keyframes bh-r{to{transform:translateY(-150px)}}"
    ".bh-g{animation:bh-g 90s linear infinite}@keyframes bh-g{to{transform:translateX(-900px)}}"
    ".bh-k,.bh-p,.bh-s{transform-origin:0 135px;animation:bh-s 4s ease-in-out infinite alternate}"
    ".bh-k{transform-origin:0 47px;animation-name:bh-k;animation-duration:1.1s}@keyframes bh-k{to{transform:scaleY(-1)}}"
    ".bh-f{animation:bh-f 5s infinite}@keyframes bh-f{50%{opacity:0}}"
    f".bh-p{{transform-origin:{HX + 19}px {HY + 2}px;animation-name:bh-p}}@keyframes bh-p{{to{{transform:rotate(14deg)}}}}"
    "@keyframes bh-s{from{transform:skewX(-2deg)}to{transform:skewX(3deg)}}"
)
