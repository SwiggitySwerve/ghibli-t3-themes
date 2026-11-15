"""Kiki's Delivery Service: Kiki and Jiji ride the broom over Koriko on a bright sea-wind morning.

Static layer (PNG, 15 colours): sky, cumulus, sea, the green hill, the town climbing to the clock
tower, quay, jetty and sailboat.
Sprites (SVG), back to front: airship, gulls, Kiki + Jiji + radio on the broom, sea glints.
Kiki hovers on screen (a slow diagonal bob, bow and hem fluttering) instead of crossing: she is the
only thing that says which film this is, so she must be there whenever the scene fades in. The
crossing "moments" are the gulls and the very slow airship.

Size notes: the town is ~half of the PNG. Odd house widths (even pitch) and roofs that only taper in
their top rows compress much better than free widths and full trapezoids.
"""
import math, random
from lib import Canvas, W, H

NAME = "Kiki's Delivery Service"
COLORS = 16

S = ["#3a74c4", "#5490d8", "#7aafe8", "#a6cff4", "#d6ecfb"]   # sky top -> horizon
WHITE, DEEP = "#ffffff", "#2a5aa6"
CREAM, SHADE, TERRA, RUST, TEAL = "#f4e4c1", "#c7a488", "#cf5f3c", "#8e3b2f", "#3c8a86"
NAVY, GREEN, DKGREEN = "#1c2340", "#5d9c4c", "#3b7044"
HZ = 86          # horizon row
TX = 146         # clock tower centre


def bands(cv, y, rows):
    """rows: [(y_end, colour)]. Flat bands, each seam softened by one checker row."""
    prev = None
    for y1, c in rows:
        for yy in range(y, y1):
            for x in range(cv.w):
                cv.set(x, yy, prev if prev and yy == y and (x + yy) % 2 else c)
        prev, y = c, y1


def cloud(cv, circles, base):
    """Daylight cumulus: white balls painted back to front, each with a pale-blue belly; flat base."""
    for cx, cy, r in circles:
        for y in range(int(cy - r), min(base, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + .5 - cx, y + .5 - cy
                if math.hypot(dx, dy) <= r:
                    cv.set(x, y, S[4] if (.45 * dx + .9 * dy) > .5 * r or base - y <= 2 else WHITE)


def house(cv, x, base, w, h, roof, rh, win, foot=3):
    """Cream wall lit from the left, pitched roof with a dark eave, one row of windows.
    foot: how far the wall runs below the base line (the quay-front row runs down to the quay)."""
    cv.rect(x, base - h, w, h + foot, CREAM)
    cv.rect(x + w - 2, base - h, 2, h + foot, SHADE)
    if win:
        for wx in range(x + 1, x + w - 3, 4):
            cv.rect(wx, base - h + 1 + (foot > 3), 1, 2 + (foot > 3), NAVY)   # taller on the quay front
    for i in range(rh):
        k = INSET[i]
        cv.rect(x - 1 + k, base - h - 1 - i, w + 2 - 2 * k, 1, RUST if i == 0 else roof)


def tower(cv, cx, top, base):
    cv.rect(cx, top - 3, 1, 3, NAVY)                          # spire
    for i in range(10):                                       # steep teal roof
        cv.rect(cx - i // 2 - 1, top + i, 2 * (i // 2) + 3, 1, TEAL)
    cv.rect(cx - 7, top + 10, 15, 1, NAVY)
    cv.rect(cx - 6, top + 11, 13, 13, CREAM)                  # clock stage
    cv.rect(cx + 5, top + 11, 2, 13, SHADE)
    for dy, hw in enumerate([2, 3, 4, 4, 4, 4, 4, 3, 2]):     # clock face with a dark rim
        cv.rect(cx - hw, top + 13 + dy, 2 * hw + 1, 1, NAVY)
        if 0 < dy < 8:
            cv.rect(cx - hw + 1, top + 13 + dy, 2 * hw - 1, 1, WHITE)
    cv.rect(cx, top + 15, 1, 3, NAVY)                         # hands
    cv.rect(cx, top + 17, 3, 1, NAVY)
    cv.rect(cx - 7, top + 24, 15, 1, RUST)
    cv.rect(cx - 4, top + 25, 9, base - top - 25, CREAM)      # shaft
    cv.rect(cx + 3, top + 25, 2, base - top - 25, SHADE)
    for y in range(top + 28, base - 3, 6):                    # slit windows
        cv.rect(cx - 1, y, 1, 3, NAVY)


def sky(cv):
    bands(cv, 0, [(14, S[0]), (32, S[1]), (52, S[2]), (70, S[3]), (HZ, S[4])])
    bands(cv, HZ, [(90, S[1]), (99, S[0]), (H, DEEP)])


def clouds(cv):
    # a tall cumulus tower on the left, a lower bank sinking behind the hill on the right
    cloud(cv, [(34, 52, 10), (20, 66, 12), (47, 66, 13), (63, 75, 9), (5, 76, 9), (33, 76, 12)], HZ - 2)
    cloud(cv, [(206, 57, 8), (219, 49, 10), (233, 56, 10)], 80)


def land(cv):
    for x in range(66, W):                                    # green hill under and behind the town
        yt = int(round(79 - 13 * math.sin(max(0, x - 96) / 150 * 1.9) - 3 * math.sin(x * .09) + max(0, 96 - x) * .9))
        cv.rect(x, yt, 1, H - yt, GREEN)
    for x, y in TREES:                                        # dark trees on the open hillside
        cv.rect(x + 1, y, 4, 1, DKGREEN)
        cv.rect(x, y + 1, 6, 2, DKGREEN)


def town(cv):
    """Tiers back to front; each row of houses steps down the slope away from the tower."""
    r = random.Random(TSEED)
    for ti, (x0, x1, yb, slope, hh, ww) in enumerate(TIERS):
        x = x0
        while x < x1:
            w = ww + r.choice(WVAR)
            h = hh + r.randrange(0, 2)
            base = int(yb + slope * abs(x + w / 2 - TX))
            if not (ti == 0 and abs(x + w / 2 - TX) < 9):
                house(cv, x, base, w, h, TEAL if r.random() < TEALP else TERRA, 3 + ti // 2, ti > 0,
                      109 - base if ti == 3 else 3)
            x += w + 1
        if ti == 0:
            tower(cv, TX, 38, 82)


def front(cv):
    cv.rect(60, 109, W - 60, 1, CREAM)                        # quay wall; the sea wraps round the foreground
    cv.rect(60, 110, W - 60, 3, SHADE)
    cv.rect(60, 113, W - 60, 1, NAVY)
    cv.rect(60, 114, W - 60, H - 114, DEEP)
    cv.rect(42, 109, 18, 1, NAVY)                             # jetty, a sailboat, ripples
    for x in (44, 50, 56):
        cv.rect(x, 110, 1, 2, NAVY)
    for x, y, n in RIPPLES:
        cv.rect(x, y, n, 1, S[2] if y < 90 else S[1] if y < 99 else S[0])
    cv.paint(["..w..", ".ww..", ".www.", "wwww.", "..n..", "nnnnn"], {"w": WHITE, "n": NAVY}, 24, 91)


TREES = [(194, 71), (206, 76), (220, 69), (231, 79), (217, 83), (234, 91)]
RIPPLES = [(6, 88, 8), (40, 88, 5), (14, 94, 6), (46, 96, 7), (2, 103, 6), (30, 107, 8), (100, 116, 9), (166, 116, 7)]
TSEED = 43
TEALP = .3
INSET = [0, 0, 1, 2, 3]
WVAR = [1, 3]
TIERS = [(112, 190, 77, .14, 3, 7), (98, 208, 85, .10, 4, 8), (84, 224, 94, .07, 4, 10), (70, 238, 104, .04, 5, 12)]


def draw():
    cv = Canvas()
    for part in (sky, clouds, land, town, front):
        part(cv)
    return cv


def runs(rows, pal, x0, y0):
    """ASCII art -> one stroked <path> per colour, 1px runs joined by relative moves. Horizontal or
    vertical runs, whichever is shorter for that colour."""
    out = ""
    for ch, col in pal.items():
        best = None
        for vert in (0, 1):
            g = [list(c) for c in zip(*rows)] if vert else rows
            d, px, py = "", 0, 0
            for j, row in enumerate(g):
                i = 0
                while i < len(row):
                    if row[i] != ch:
                        i += 1
                        continue
                    n = 1
                    while i + n < len(row) and row[i + n] == ch:
                        n += 1
                    if vert:
                        d += (f"M{x0 + j}.5 {y0 + i}" if not d else f"m{j - px} {i - py}") + f"v{n}"
                        px, py = j, i + n
                    else:
                        d += (f"M{x0 + i} {y0 + j}.5" if not d else f"m{i - px} {j - py}") + f"h{n}"
                        px, py = i + n, j
                    i += n
            d = d.replace(" -", "-")
            if d and (best is None or len(d) < len(best)):
                best = d
        if best:
            out += f"<path stroke='{col}' d='{best}'/>"
    return out


# Kiki, facing right. r bow/shoes/radio, h hair, s skin, k dress, o satchel, c Jiji, w eyes/dial,
# y/Y broom straw, b handle
KIKI = [
    ".....................rrr...rrr..............",
    "....................rrrrr.rrrrr.............",
    "....................rrrrrrrrrrr.............",
    "......................rrrrrrr...............",
    ".......................hhhhhhh..............",
    "......................hhhhhhhhh.............",
    "....c...c.............hhhhhhhss.............",
    "....ccccc.............hhhhhsshs.............",
    "....cwcwc.............hhhhssssss............",
    "....ccccc..............hhhsssss.............",
    ".....cccc..............kkkkkk...............",
    "..c.ccccc.............kkkkkkkk..............",
    "..c.ccccc.............kkkkkkkkk.............",
    "..ccccccc............oookkkkkkk.............",
    "yyycccccc............oookkkkkkkk............",
    ".yyyyyyyy..........kkoookkkkk.kkk...........",
    "yyyyyyyyyy........kkkkkkkkkkkk..ss..........",
    "yyyyyyyyyybbbbbbbkkkkkkkkkkkkkbbbbbbbbbbbbb.",
    ".bbbbbbbbb.......kkkkkkkkkkkk...........h...",
    "bbbbbbbbb.........kkkkkkkkkss.........rrrrr.",
    ".bbbbbb............kkkkkk..ss.........rwrrr.",
    "...........................ss.........rrrrr.",
    "...........................rrrr.............",
]
# second frame, added on top: the bow lifts and the hem trails
FLAP = [
    "....................r.......................",
    "...................r........................",
    "...................r........................",
] + ["............................................"] * 15 + [
    "................k...........................",
    "................kk..........................",
    ".................kk.........................",
]
PAL = {"k": "#325", "r": "#d23", "h": "#321", "s": "#fdb", "o": "orange", "c": "#111", "w": "#fff",
       "y": "#eb6", "b": "#853"}
KX, KY = 82, 28

GULL_A = "h1m5 0h1m-6 1h2m1 0h2m-4 1h1"            # wings up, relative to a start point
GULL_B = "h1m-3 1h2m1 0h2m-6 1h1m5 0h1"            # wings down (start point is 3px further right)
GULLS = [(-40, 12), (-27, 19), (-55, 23)]

SPRITES = (
    # airship, drawn at 2x inside scale(.5) so the shared 600px keyframe moves it only 300px
    "<g transform='scale(.5)'><g class='kk-t'><ellipse cx='-60' cy='26' rx='28' ry='9' fill='#dde'/>"
    "<path fill='#9ac' d='M-84 28h48v4h-6v2h-12v6h-12v-6h-12v-2h-6zm-4-12h8v6h-8zm0 14h8v6h-8z'/>"
    "<path stroke='#d23' stroke-width='2' d='M-78 24h36'/></g></g>"
    # gulls: two wing frames swapped with steps(); mirrored so they reuse the airship keyframes
    + "<g transform='matrix(-1 0 0 1 225 0)'><g class='kk-t kk-g' stroke='#fff'>"
    + "<path class='kk-f' d='" + "".join(f"M{x} {y}.5{GULL_A}" for x, y in GULLS) + "'/>"
    + "<path class='kk-f kk-e' d='" + "".join(f"M{x + 3} {y}.5{GULL_B}" for x, y in GULLS) + "'/></g></g>"
    # Kiki
    + f"<g class='kk-b'>{runs(KIKI, PAL, KX, KY)}<g class='kk-f'>{runs(FLAP, PAL, KX, KY)}</g></g>"
    # sea glints
    + "<path class='kk-a' stroke='#fff' d='M8 93.5h5m28 5h4m-30 9h5'/>"
      "<path class='kk-a kk-e' stroke='#fff' d='M30 100.5h5m-28 4h4m44-9h4'/>"
)
CSS = (
    ".kk-t{animation:kk-t 300s -70s linear infinite}@keyframes kk-t{to{transform:translateX(600px)}}"
    ".kk-g{animation-duration:46s}"
    ".kk-b{animation:kk-b 2.3s ease-in-out infinite alternate}@keyframes kk-b{to{transform:translate(2px,3px)}}"
    ".kk-f{animation:kk-o .8s steps(1) infinite}.kk-a{animation:kk-o 4s infinite}@keyframes kk-o{50%{opacity:0}}"
    ".kk-e{animation-delay:-2s}"
)
