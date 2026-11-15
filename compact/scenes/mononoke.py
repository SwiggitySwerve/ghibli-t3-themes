"""Princess Mononoke: the ancient cedar forest at night. San, masked, rides Moro on a mossy rise
between huge trunks; kodama perch on roots and a bough and rattle their heads; beyond the trunks
the Nightwalker wades slowly past over the moonlit ridges.

Static layer (PNG, 14 colours): sky, moon, three ridges, trunks, roots, moss, Moro + San, kodama.
Sprites (SVG): the Nightwalker inside a clip-path that is the sky gap between the trunks (so he
passes BEHIND trunks and the near ridge although sprites draw over the PNG), kodama heads that
click round in 90-degree steps (pixel-exact because the head is a 6x6 square drawn once around the
origin and placed with <use>), drifting fireflies.
"""
import math
from lib import Canvas, W, H

NAME = "Princess Mononoke"
COLORS = 16

S0, S1, S2, S3, S4 = "#101a4a", "#1a3068", "#25508a", "#3a7aa0", "#62a8b0"
WHITE, WSH = "#eeffee", "#a8c4d4"
T0, T1, T2 = "#112222", "#1a3c44", "#1f5058"
M0, M1 = "#2e7040", "#6cbc50"
RED, SKIN = "#dd3838", "#e8b088"

LT = (36, 80)      # left foreground trunk x-range
MT = (150, 157)    # slimmer trunk further back
RT = (172, 204)    # right foreground trunk
GROUND = 108


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


def near(x):
    """Near ridge top, stepped every 4 px so the clip-path can follow it cheaply."""
    x = x // 4 * 4
    return int(round(71 - (x - 66) * .06 + 2.5 * math.sin(x * .09)))


def trace(rows, x0=0, y0=0, sy=1, on="#"):
    """ASCII bitmap -> one compact outline path (h/v only). Each ASCII row is sy pixels tall."""
    cells = {(x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch in on}
    nxt = {}
    for x, y in cells:
        for free, a, b in (((x, y - 1), (x, y), (x + 1, y)), ((x + 1, y), (x + 1, y), (x + 1, y + 1)),
                           ((x, y + 1), (x + 1, y + 1), (x, y + 1)), ((x - 1, y), (x, y + 1), (x, y))):
            if free not in cells:
                nxt.setdefault(a, []).append(b)
    out, cur = "", None
    while nxt:
        start = min(nxt, key=lambda p: (p[1], p[0]))
        pts, p = [start], start
        while True:
            q = nxt[p].pop()
            if not nxt[p]:
                del nxt[p]
            if q == start:
                break
            pts.append(q)
            p = q
        # drop collinear points
        keep = [pts[i] for i in range(len(pts))
                if (pts[i - 1][0] == pts[i][0]) != (pts[(i + 1) % len(pts)][0] == pts[i][0])]
        sx, sy0 = keep[0][0] + x0, keep[0][1] * sy + y0
        out += f"M{sx} {sy0}" if cur is None else f"m{sx - cur[0]} {sy0 - cur[1]}"
        cur = (sx, sy0)
        for a, b in zip(keep, keep[1:]):
            out += f"h{b[0] - a[0]}" if a[1] == b[1] else f"v{(b[1] - a[1]) * sy}"
        out += "z"
    return out


MORO = [
    "...............................WW...WW........",
    "...............................WWW.WWW........",
    "..............................WWWWWWWWW.......",
    ".............................WWWWWWWWWWWW.....",
    "............................WWWWWWWWkWWWWWW...",
    "...........................WWWWWWWWWWWWWWWWWWk",
    "...........WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    ".WWWW....WWWWWWWWWWWWWWWWWWWWWWWWWWWWWgkkkkkk.",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWggg...",
    ".WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWgg......",
    "....gggWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWg........",
    "...WWWgWWWWWWWWWWWWWWWWWWWWWWWWWWWWWg.........",
    "..WWWWWgWWWWWWWWWWWWWWWWWWWWWWWWWWWWg.........",
    ".WWWWW.WWWWWWWWWWWWWWWWWWWWWWWWWWWWg..........",
    "WWWWW..WWWWWWWWWWWWWWWWWWWWWWWWWWWWg..........",
    "WWWW...WWWWWWWWWWWWWWWWWWWWWWWWWWWg...........",
    ".WW....WWWWWWWWWWWWWWWWWWWWWWWWWWg............",
    ".......WWWWWWWWWWgggggggggWWWWWWWgggg.........",
    ".......WWWWWWWWgggg.......gWWWWWW.ggg.........",
    ".......WWWWWWg..ggg........WWWWWg.ggg.........",
    ".......WWWWWg...ggg........WWWWWg.ggg.........",
    "......WWWWWg....ggg........WWWWg..ggg.........",
    "......WWWWg.....ggg........WWWWg..ggg.........",
    "......WWWWg.....ggg........WWWWg..ggg.........",
    "......WWWWg.....ggg........WWWWg..ggg.........",
    "......WWWWWg....gggg.......WWWWWg.gggg........",
]
SAN = [
    "........w",
    "........w",
    "..WWWW..s",
    ".WWRRR..s",
    "WWRyRyR.s",
    "WWRRRRR.s",
    "WWWRRR..s",
    "WWWWWW..s",
    "WWWWWWsss",
    ".WWWWW..s",
    ".nnnnn..s",
    "..nnnss.s",
    "...nss..s",
    "....s...s",
]
KODAMA = [
    ".WWWW.",
    "WWWWWW",
    "WkWWkW",
    "WWWWWW",
    "WWkWWW",
    ".WWWW.",
    "..WW..",
    ".WWWW.",
    "W.WW.W",
    "..gW..",
    ".W..W.",
]
KOD_S = [
    ".WW.",
    "WWWW",
    "kWkW",
    "WWWW",
    ".WW.",
    "WWWW",
    "W..W",
]
PAL = {"W": WHITE, "g": WSH, "k": T0, "R": RED, "y": WHITE, "s": SKIN, "n": S1, "w": WHITE}
# kodama whose heads rattle: (x, y of head top-left)
HEADS = [(82, 86), (66, 52), (159, 70), (142, 97)]
MX, MY = 92, GROUND - 26


def trunk(cv, x0, x1, side, clumps):
    """Foreground trunk: dark bark with regular furrows, a gently flared foot and moss clumps on
    the moonlit edge (kept inside the trunk so the edge stays straight for the clip-path)."""
    for y in range(H):
        f = max(0, y - 88) // 4
        cv.rect(x0 - f, y, x1 - x0 + 2 * f, 1, T0)
    for i, x in enumerate(range(x0 + 4, x1 - 3, 5)):
        for y in range(GROUND):
            if (y + i * 9) % 27 > 2:
                cv.set(x, y, T1)
    ex = x1 - 1 if side > 0 else x0
    for y0, n in clumps:
        for i in range(n):
            d = min(i + 1, n - i, 3)
            cv.rect(min(ex, ex - side * d), y0 + i, d + 1, 1, M0)
            if i < n * 2 // 3:
                cv.set(ex, y0 + i, M1)
        cv.rect(min(ex, ex - side * 2), y0 + 1, 3, 1, M1)


def root(cv, x0, n, side, y0):
    """A mossy buttress root: steep at the trunk, flattening out onto the ground."""
    for i in range(n):
        x, y = x0 + side * i, y0 + int((GROUND - y0) * (1 - (1 - i / n) ** 2))
        cv.rect(x, y, 1, GROUND - y, T0)
        cv.rect(x, y, 1, 3, M0)
        cv.set(x, y, M1)


def shelf(cv, x, y, n):
    cv.rect(x + 1, y, n - 2, 1, M1)
    cv.rect(x, y + 1, n, 1, M0)
    cv.rect(x + 2, y + 2, n - 4, 1, M0)


def draw():
    cv = Canvas()
    bands(cv, 0, [(8, S0), (20, S1), (33, S2), (46, S3), (H, S4)])
    for x, y in [(84, 5), (118, 11), (136, 4), (162, 14), (126, 26), (86, 30)]:
        cv.set(x, y, WHITE)
    # moon
    for y in range(12, 26):
        for x in range(92, 106):
            if math.hypot(x + .5 - 99, y + .5 - 19) <= 6.3:
                cv.set(x, y, WHITE)
    for x, y in [(96, 16), (97, 16), (101, 21), (100, 22), (101, 22), (96, 21)]:
        cv.set(x, y, WSH)
    # far ridges
    for x in range(W):
        a = int(round(53 + 4 * math.sin(x * .05 + 1.2) + 2 * math.sin(x * .13)))
        b = int(round(61 + 3 * math.sin(x * .07 + 4) + 1.5 * math.sin(x * .19 + 1)))
        cv.rect(x, a, 1, H, S3)
        cv.rect(x, b, 1, H, S2)
        cv.rect(x, near(x), 1, H, T2)
    # slim trunk further back, bough from the right trunk
    cv.rect(MT[0], 0, MT[1] - MT[0], GROUND, T1)
    cv.rect(160, 81, 14, 3, T0)
    cv.rect(158, 80, 4, 2, T0)
    cv.rect(162, 80, 10, 1, M1)
    cv.rect(164, 81, 8, 1, M0)
    # dark depths beyond the outer trunks
    cv.rect(0, 0, LT[0], H, T1)
    cv.rect(RT[1], 0, W - RT[1], H, T1)
    cv.rect(0, 0, 14, H, T0)
    cv.rect(222, 0, 18, H, T0)
    cv.rect(21, 0, 5, H, T2)
    cv.rect(211, 0, 4, H, T2)
    # ground
    cv.rect(0, GROUND, W, H, M0)
    cv.rect(0, GROUND, W, 1, M1)
    for x in range(W):
        cv.rect(x, GROUND + 4 + (x % 2), 1, H, T0)
    trunk(cv, LT[0], LT[1], 1, [(3, 16), (27, 10), (43, 18), (70, 12)])
    trunk(cv, RT[0], RT[1], -1, [(9, 12), (29, 19), (56, 10), (88, 9)])
    root(cv, LT[1] + 1, 24, 1, 93)
    root(cv, RT[0] - 2, 16, -1, 97)
    shelf(cv, 63, 63, 12)
    shelf(cv, 44, 34, 9)
    shelf(cv, 184, 50, 10)
    shelf(cv, 190, 100, 9)
    # heroes
    cv.paint(MORO, PAL, MX, MY)
    cv.paint(SAN, PAL, MX + 21, MY - 6)
    # kodama
    for x, y in HEADS:
        cv.paint(KODAMA, PAL, x, y)
    for x, y in [(46, 27), (187, 43), (192, 93)]:
        cv.paint(KOD_S, PAL, x, y)
    return cv


# Nightwalker, each ASCII row = 2 px
NW = [
    ".......................#####.........",
    "............#.........#########......",
    ".............#........###########....",
    "........#.....#.......##########.....",
    ".........#.....#.......#######.......",
    "..........#.....##...######..........",
    ".....#.....#.....##..#####...........",
    "......#.....##....########...........",
    ".......#.....##...#######............",
    "..#.....##....###.#######............",
    "...#.....##....###########...........",
    "....##....###...############.........",
    ".....##....####################......",
    ".#....###...####################.....",
    "..##...####.#####################....",
    "...###...########################....",
    ".....####.#######################....",
    ".......##################.#######....",
    "..........###############..######....",
    "..........###############..######....",
    "...........##############...#####....",
    "...........##############...#####....",
    "...........#############....#####....",
    "...........#############.....####....",
    "...........#############.....####....",
    "...........#############.....####....",
    "...........##############....#####...",
    "..........###############.....####...",
    "..........################....###....",
    "..........################...........",
    "..........################...........",
    "..........################...........",
    "..........################...........",
    "..........################...........",
    "..........################...........",
    "..........################...........",
]
NX, NY = -62, 4


def clip():
    d = ""
    for xa, xb in ((LT[1], MT[0]), (MT[1], RT[0])):
        d += f"M{xa} 0H{xb}"
        y = 0
        for x in range(xb - 1, xa - 1, -1):
            if near(x) != y:
                d += f"V{near(x)}H{x + 1}" if y else f"V{near(x)}"
                y = near(x)
        d += f"H{xa}z"
    return d


SPRITES = (
    f"<clipPath id='pm-c'><path d='{clip()}'/></clipPath>"
    f"<g clip-path='url(#pm-c)'><g class='pm-n'><g class='pm-b'>"
    f"<path fill='#8ef' opacity='.5' d='{trace(NW, NX, NY, 2)}'/>"
    f"<path stroke='#eff' d='M{NX + 14} {NY + 30}.5h1m5 4h1m-9 5h1m5 3h1m4-7h1m-8 14h1m5 5h1m-2-32h1m7-18h1'/>"
    "</g></g></g>"
    "<defs><g id='pm-h'><path fill='#efe' d='M-2-3h4v1h1v4h-1v1h-4v-1h-1v-4h1z'/>"
    "<path stroke='#122' d='M-2-.5h1m2 0h1m-3 2h1'/></g></defs>"
    + "".join(f"<g transform='translate({x + 3} {y + 3})'><use href='#pm-h' class='pm-k' style='--d:{i}'/></g>"
              for i, (x, y) in enumerate(HEADS))
    + "<path class='pm-f' stroke='#fd6' d='M88 70.5h1m34-22h1m30 44h1m-90 8h1m60-40h1'/>"
      "<path class='pm-f pm-g' stroke='#fd6' d='M104 58.5h1m52-12h1m-80 34h1m90 20h1m-40-60h1'/>"
)
CSS = (
    ".pm-n{animation:pm-n 90s -20s linear infinite}@keyframes pm-n{to{transform:translateX(300px)}}"
    ".pm-b{animation:pm-b 3s ease-in-out infinite alternate}@keyframes pm-b{to{transform:translateY(2px)}}"
    ".pm-k{animation:pm-k 7s calc(var(--d)*-.6s) steps(1) infinite}"
    "@keyframes pm-k{84%{transform:rotate(90deg)}92%{transform:rotate(-90deg)}}"
    ".pm-f{animation:pm-d 11s ease-in-out infinite alternate,pm-o 3s infinite alternate}.pm-g{animation-delay:-11s,-3s}"
    "@keyframes pm-d{to{transform:translate(9px,-7px)}}@keyframes pm-o{to{opacity:.1}}"
)
