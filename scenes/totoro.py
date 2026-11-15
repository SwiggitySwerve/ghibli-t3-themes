"""My Neighbor Totoro: the rainy-night bus stop, played out as the film's scene (320x180, 120 s loop).

Totoro waits under a too-small umbrella beside Satsuki, who carries sleeping Mei on her back, in the cone
of a lone streetlamp. The Catbus gallops in along the power line, Totoro hands Satsuki a leaf-wrapped
bundle and leaps up into it, and it gallops on along the wire. Then Dad's bus pulls in,
Dad comes round the front of it, and the bus leaves the three of them standing in the rain. See the
timeline above CSS.

Static layer (one PNG): sky, clouds, hills, paddies and the Kusakabe house, camphor, forest, torii, fox
and Jizo statues, lit bushes, pole + lamp, road with baked lamp light, the bus-stop sign, Satsuki + Mei.
Sprites are listed in depth order (see sprites()). No url(#id) references anywhere: clips are nested <svg>
viewports and the rain is a PNG strip (see rain()).

Every animation is stepped in whole pixels (the exceptions are Totoro's 2% breathing stretch and the
sprouts' growth), and everything sits parked at a constant value between appearances, so the image only
re-rasterizes when something actually moves. The rain is the one full-canvas animated layer: a 1-bit PNG
strip stepping at 10 fps. Dad's bus is drawn at half size and doubled (scale(2)).
"""
import base64, math, struct, zlib
from lib import Canvas, UNPAINTED, hx

NAME = "My Neighbor Totoro"
SIZE = W, H = 320, 180
COLORS = 48

K = ["#121a40", "#1b2a62", "#27477f", "#33658f", "#4f8ba3"]        # sky top -> horizon
CAM_D, CAM, CAM_H = "#0c2030", "#13303e", "#2a5f5c"                  # camphor: shade, mid, rim
HAZE = {CAM_D: "#173843", CAM: "#1f4a54", CAM_H: "#3a7468", "#08131d": "#10262f", "#10262f": "#1a3a3c"}   # in the lamp cone
FOR, FOR2 = "#08131d", "#10262f"                                    # forest edge: near, mid
LEAF, LEAF_L, LEAF_H = "#1c463e", "#35694a", "#7a9c58"              # bushes: unlit -> lamp-lit
ROAD_D, ROAD, ROAD_L, ROAD_H = "#262c40", "#41485c", "#666869", "#948a6c"
POLE = "#59607a"
BLACK, WHITE, CREAM, CREAM_D = "#0a0c16", "#ffffff", "#ece4c4", "#b9b49c"
TOT_D, TOT, TOT_L = "#4d596f", "#77879a", "#a3b1bc"
YEL, RED, RED_D, SKIN, SKIN_D = "#ffdd77", "#e0603a", "#96382e", "#f4c09a", "#c98a6c"
HAIR, MEI, LEMON, PINK, PINK_D = "#2a2030", "#b86a34", "#fff3b0", "#ee8078", "#b84a4c"
BLUE, HYD, HYD2 = "#4a7fd0", "#7f9fe0", "#a88fd0"

RD = 138             # road top row
GY = 146             # ground line: feet end on row GY-1
TX = 150             # Totoro centre
SX, SY = 179, GY - 27   # Satsuki art top-left
LX, LY = 171, 69     # lamp bulb = apex of the light cone
PX = 174             # utility pole
ACORNS = 84, 91, 98  # left edges of the three acorns on the road (row GY)
WIRE = 51            # the power line's row where it meets a pole (poles every 150 px; only the one at PX is in view)


def sag(x):
    """Rows the wire hangs below WIRE at column x: 0 at a pole, 4 at mid-span. The flat runs end on
    multiples of 6 px from the pole (4 % of a span), which is what lets the Catbus's feet track it exactly."""
    u = (x - PX) % 150
    return next(r for end, r in ((6, 0), (18, 1), (30, 2), (48, 3), (102, 4), (120, 3), (132, 2), (144, 1), (150, 0)) if u < end)


# ------------------------------------------------------------------ helpers
def png(cv, x0, y0, w, h, at=None, attr=""):
    """A canvas region (magenta = transparent) as a base64 palette PNG <image>, hand-encoded so the bit
    depth and deflate settings can be whichever comes out smallest. `at` places it somewhere other than
    (x0, y0); `attr` is extra attribute text."""
    px = [cv.px[y][x0:x0 + w] for y in range(y0, y0 + h)]
    cols = [UNPAINTED] + sorted({p for row in px for p in row if p != UNPAINTED})
    n, best = len(cols), None
    for bits in {1 if n <= 2 else 2 if n <= 4 else 4 if n <= 16 else 8, 8}:
        raw, per = bytearray(), 8 // bits
        for row in px:
            raw.append(0)
            ix = [cols.index(p) for p in row]
            ix += [0] * (-len(ix) % per)
            raw += bytes(sum(v << bits * (per - 1 - j) for j, v in enumerate(ix[i:i + per])) for i in range(0, len(ix), per))
        for wb in (15, 12, 10, 9):
            for st in (0, 1):
                c = zlib.compressobj(9, 8, wb, 9, st)
                d = c.compress(bytes(raw)) + c.flush()
                if best is None or len(d) < len(best[1]):
                    best = bits, d
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    data = (b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, best[0], 3, 0, 0, 0))
            + ch(b"PLTE", bytes(v for c in cols for v in c)) + ch(b"tRNS", b"\0") + ch(b"IDAT", best[1])
            + ch(b"IEND", b""))
    x0, y0 = at or (x0, y0)
    return (f"<image{attr} x='{x0}' y='{y0}' width='{w}' height='{h}' "
            f"href='data:image/png;base64,{base64.b64encode(data).decode()}'/>")


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


def disc(cv, circles, c, ymax=H):
    """Union of filled circles, clipped below ymax."""
    for cx, cy, r in circles:
        for y in range(int(cy - r), min(ymax, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                if math.hypot(x + .5 - cx, y + .5 - cy) <= r:
                    cv.set(x, y, c)


def clump(cv, circles, on, hi, lo, lx=-.6, ly=-.8):
    """Leaf clusters inside an existing canopy: a lit rim arc facing (lx, ly) and, if `lo` is given, a
    flat shade crescent on the far side. Only repaints pixels that are already canopy (`on`)."""
    on = {hx(o) for o in on}
    for cx, cy, r in circles:
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + .5 - cx, y + .5 - cy
                d = math.hypot(dx, dy)
                if d > r or not (0 <= x < cv.w and 0 <= y < cv.h) or cv.get(x, y) not in on:
                    continue
                k = (dx * lx + dy * ly) / r
                if d > r - 1.3 and k > .45:
                    cv.set(x, y, hi)
                elif lo and d > r - 5 and k < -.55:
                    cv.set(x, y, lo)


def cedar(cv, cx, top, hw, c, hi):
    """A tiered conifer silhouette from `top` down to the road, sky-lit on the left of each tier."""
    for y in range(top, RD):
        k = y - top
        w = min(hw, 1 + k // 7 + (k % 7) // 3)
        cv.rect(cx - w, y, 2 * w, 1, c)
        if k % 7 == 6 and 2 < w < hw:
            cv.rect(cx - w, y, 3, 1, hi)


def relight(cv, test, table):
    """Bake lamp light: repaint pixels where test(x, y) -> 0..1 coverage, through a colour table.
    Partial coverage becomes ordered dither."""
    table = {hx(a): hx(b) for a, b in table.items()}
    for y in range(cv.h):
        for x in range(cv.w):
            t = test(x, y)
            if t > 0 and (t >= 1 or (x + y) % 2 == 0) and cv.px[y][x] in table:
                cv.px[y][x] = table[cv.px[y][x]]


def in_cone(x, y):
    if not LY <= y < RD:
        return 0
    d = 3 + 57 * (y - LY) / (GY - LY) - abs(x + .5 - LX)
    return 1 if d > 2 else .5 if d > 0 else 0


def in_pool(rx, ry):
    def f(x, y):
        d = ((x + .5 - LX) / rx) ** 2 + ((y + .5 - GY - 1) / ry) ** 2
        return 0 if y < RD + 1 else 1 if d < .8 else .5 if d < 1 else 0
    return f


# ------------------------------------------------------------------ the cast
THW = [5, 7, 9, 10, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 19, 20,
       20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 19, 19, 19, 18, 17, 16, 14, 11]


EAR = [(12, 1), (12, 2), (12, 3), (11, 3), (11, 4), (10, 3), (10, 3), (9, 3), (9, 3)]   # leaf-shaped, tilted out


def totoro(cv, cx, by):
    """50 px tall, lit from the lamp at upper right. Drawn on a scratch canvas and cropped to its own PNG."""
    top = by - 50
    P = lambda x, y, c: cv.set(cx + x, top + y, c)
    R = lambda x, y, n, c: cv.rect(cx + x, top + y, n, 1, c)
    for i, w in enumerate(THW):                                # body: mid grey, lit right rim, shaded left
        for x in range(-w, w):
            c = TOT
            if x >= w - 2 or (x == w - 3 and i % 2):
                c = TOT_L
            if x < -w + 3 or (x < -w + 6 and (x + i) % 2 == 0) or (i > 45 and (x + i) % 2 == 0):
                c = TOT_D
            P(x, i, c)
    for i in range(6, 44, 5):                                  # fur: a few strokes where shade meets mid
        R(-THW[i] + 8 + i % 3, i, 2, TOT_D)
        R(THW[i] - 8 - i % 2, i + 2, 2, TOT_L)
    for i in range(14, 45, 3):                                 # tufts breaking the outline
        P(THW[i], i, TOT_L)
        P(-THW[i] - 1, i + 1, TOT_D)
    for k, (a, n) in enumerate(EAR):                           # right ear (the left one is a sprite, it twitches)
        R(a - n, k - 7, n, TOT)
        P(a - 1, k - 7, TOT_L)
    for i in range(17, 48):                                    # belly
        b = min(THW[i] - 3, int(round(16 * math.sqrt(max(0, 1 - ((i - 32) / 15.5) ** 2)))))
        for x in range(-b, b):
            P(x, i, CREAM_D if x < -b + 2 or (x < -b + 5 and (x + i) % 2 == 0) or i > 45 else CREAM)
    for y, xs in ((22, (-9, -2, 5)), (27, (-13, -6, 2, 9))):   # chest marks
        for x in xs:
            R(x + 1, y, 2, TOT)
            P(x, y + 1, TOT)
            P(x + 3, y + 1, TOT)
    for ex, px_ in ((-11, -9), (6, 7)):                        # eyes
        for k in range(5):
            R(ex + (k in (0, 4)), 8 + k, 5 - 2 * (k in (0, 4)), WHITE)
        cv.rect(cx + px_, top + 10, 2, 2, BLACK)
    R(-2, 9, 4, BLACK)                                         # nose
    R(-1, 10, 2, BLACK)
    for s in (1, -1):                                          # whiskers
        f = lambda x, y, n: R(x if s > 0 else -x - n, y, n, TOT_D)
        f(-18, 14, 4), f(-22, 13, 4), f(-23, 16, 8), f(-19, 18, 4), f(-23, 19, 4)
    for i in range(21, 37):                                    # hanging arm, with claws
        R(-THW[i], i, 5 if 22 < i < 36 else 4, TOT_D)
        P(-THW[i] + (5 if 22 < i < 36 else 4), i, TOT)
    for x in (-19, -17):
        P(x, 37, CREAM_D)
    for s in (1, -1):                                          # feet and claws
        f = lambda x, y, n, c: R(x if s > 0 else -x - n, y, n, c)
        f(-17, 47, 9, TOT_D), f(-18, 48, 11, TOT), f(-18, 49, 11, TOT)
        for x in (-18, -15, -12):
            f(x, 49, 1, BLACK)
    # the umbrella: canopy sits over the right of his head, shaft comes down past his cheek to a paw
    ux = 9
    for k, w in enumerate([2, 5, 8, 10, 12, 13, 13, 13]):
        R(ux - w, k - 18, 2 * w, BLACK)
        if 0 < k < 6:
            R(ux + w - 4, k - 18, 3, TOT_D)                    # lamp sheen
    for x in (-13, -7, 0, 6, 12):
        P(ux + x, -10, BLACK)
    cv.rect(cx + ux, top - 21, 1, 3, BLACK)
    cv.rect(cx + 11, top - 10, 1, 15, BLACK)
    cv.rect(cx + 12, top + 5, 1, 17, BLACK)
    for i, (a, n) in enumerate([(10, 5), (9, 7), (9, 7), (9, 7), (10, 5)]):   # the paw holding it
        R(a, 19 + i, n, TOT_L)
    R(10, 24, 5, TOT_D)
    for i in range(22, 27):                                    # forearm tucked along his side
        R(16, i, THW[i] - 18, TOT_L)
        P(15 if i < 26 else 16, i + 1, TOT_D)
    for y in (20, 22):
        P(9, y, BLACK)


GIRLS = [
    ".......kkkkkk.........",
    ".....kkkkkkkkkk.......",
    ".....kkkkkkkkkk..m.m..",
    ".....kkskkksskk.mmmmm.",
    ".....ksssssssskmmmmmmm",
    ".....ksessssesksssssmm",
    ".....ksessssesksdssdsm",
    ".....kssssssssk.spss..",
    "......sssddsss..ssss..",
    ".........ss....ll.....",
    "......yylssslllyy.....",
    ".....yyyoyyyyoyyy.....",
    ".....yyyoyyyyoyyy.....",
    "....lsyyooooooyysl....",
    "...lls.oooooooo.sll...",
    "...ll..oooooooo..ll...",
    "...ss.oooooooooo.ss...",
    "...rr.oooooooooo.rr...",
    "...rroooooooooooorr...",
    ".....oOOooooooOOo.....",
    ".......ss....ss.......",
    ".......ss....ss.......",
    ".......ss....ss.......",
    ".......sd....sd.......",
    ".......ww....ww.......",
    ".......ww....ww.......",
    "......RRR....RRR......",
]
GPAL = {"k": HAIR, "s": SKIN, "d": SKIN_D, "e": BLACK, "y": YEL, "o": RED, "O": RED_D, "w": WHITE, "m": MEI,
        "l": LEMON, "r": PINK_D, "R": RED_D, "p": PINK}
SIGN = [      # "basu" in katakana on the disc
    ".....rrrrr.....",
    "...rrcccccrr...",
    "..rcccccccccr..",
    ".rcccccccccccr.",
    ".rcccccccccccr.",
    "rccccckcckkkkcr",
    "rcckckckcccckcr",
    "rcckckcccckcccr",
    "rckccckccckckcr",
    "rckccckcckccckr",
    ".rcccccccccccr.",
    ".rcccccccccccr.",
    "..rcccccccccr..",
    "...rrcccccrr...",
    ".....rrrrr.....",
]
PLATE = [     # the stop's name down the plate: three kanji-like blocks
    "rrrrrrrrr",
    "ccccccccc",
    "cckkkkkcc",
    "cckckckcc",
    "cckkkkkcc",
    "cccckcccc",
    "cckkkkkcc",
    "ccccccccc",
    "ccckckccc",
    "cckkkkkcc",
    "cckckcccc",
    "cckckkkcc",
    "cckckckcc",
    "ccccccccc",
    "cckccckcc",
    "cckkkkkcc",
    "cckkckccc",
    "cckkckkcc",
    "cckcckkcc",
    "ccccccccc",
]


def girls(cv):
    x, y = SX, SY
    for k, w in enumerate([2, 5, 8, 10, 11, 12, 12]):         # her umbrella, lit from straight above
        cv.rect(x + 10 - w, y - 10 + k, 2 * w + 1, 1, PINK if k < 5 else PINK_D)
        if k in (1, 2, 3):
            cv.rect(x + 10 - w + 2, y - 10 + k, w, 1, "#f9b4a4")
    for dx in (-12, -6, 0, 6, 12):
        cv.set(x + 10 + dx, y - 3, PINK_D)
    cv.rect(x + 10, y - 12, 1, 2, PINK_D)
    cv.rect(x + 10, y - 3, 1, 3, HAIR)
    cv.paint([r if not 1 < i < 9 else r[:15] for i, r in enumerate(GIRLS)], GPAL, x, y)   # Mei's head is a sprite


def draw():
    cv = Canvas(W, H)
    bands(cv, 0, [(12, K[0]), (30, K[1]), (54, K[2]), (82, K[3]), (RD, K[4])])
    # a pale cloud bank behind the camphor so its crown reads as a silhouette, and thin streaks
    disc(cv, [(52, 44, 13), (76, 34, 17), (104, 24, 15), (196, 26, 16), (224, 36, 17), (250, 46, 12), (274, 50, 9)],
         K[2], 54)
    disc(cv, [(88, 44, 13), (214, 46, 12), (150, 12, 12)], K[2], 54)
    disc(cv, [(64, 48, 8), (236, 49, 8), (112, 40, 9), (190, 40, 9)], K[3], 54)
    for x, y, n, c in [(8, 22, 40, K[0]), (22, 23, 18, K[0]), (262, 16, 50, K[0]), (250, 70, 60, K[2]),
                       (272, 71, 26, K[2]), (0, 62, 30, K[2])]:
        cv.rect(x, y, n, 1, c)
    # far hills, mist, paddies reflecting the sky, a farmhouse with one lit window
    for x in range(236, W):
        cv.rect(x, 94 - int(round(7 + 4 * math.sin(x * .045) + 2 * math.sin(x * .13))), 1, 30, K[2])
    for x in range(236, W):
        cv.rect(x, 100 - int(round(4 + 3 * math.sin(x * .06 + 2))), 1, 12, CAM)
    for y0, y1, c in [(101, 105, K[4]), (105, 112, K[3]), (112, 123, K[2]), (123, RD, K[1])]:
        cv.rect(236, y0, W - 236, y1 - y0, c)
        cv.rect(236, y0, W - 236, 1 + (y0 > 110), CAM)        # dikes
    for y in range(101, RD):                                   # dikes running away to a vanishing point
        for xb in (236, 262, 298, 344):
            cv.rect(int(266 + (xb - 266) * (y - 96) / (RD - 96)), y, 1 + (y > 118), 1, CAM)
    for y, n in ((108, 4), (116, 5), (119, 5), (128, 7), (133, 7)):   # seedling rows
        for x in range(240 + y % 3, W, n):
            if cv.get(x, y) != hx(CAM):
                cv.set(x, y, CAM)
    for x, h in ((252, 5), (261, 4), (267, 3)):                # power poles marching off to the farm
        cv.rect(x, 101 - h, 1, h, FOR)
        cv.rect(x - 1, 102 - h, 3, 1, FOR)
    # the Kusakabe house: long tiled roof, the red-gabled western wing with its attic window, a tree
    cv.rect(275, 91, 15, 3, FOR)
    cv.rect(277, 90, 11, 1, FOR)
    cv.rect(276, 94, 13, 6, CAM_D)
    for k, w in enumerate((1, 2, 3, 4, 5)):
        cv.rect(271 - w, 87 + k, 2 * w, 1, RED_D)
    cv.rect(267, 92, 8, 8, CAM)
    cv.set(270, 90, YEL)
    cv.rect(269, 94, 2, 3, YEL)
    disc(cv, [(295, 93, 4), (299, 96, 3)], FOR, 100)
    cv.rect(280, 96, 3, 3, YEL)
    for y in (103, 105):
        cv.rect(280, y, 3, 1, YEL)
    # the camphor: one huge crown, with rim-lit leaf clusters
    cv.rect(112, 80, 80, 36, CAM)                              # trunk mass, closes the gap under the crown
    crown = [(96, 82, 20), (198, 84, 20), (112, 64, 24), (182, 64, 25), (146, 52, 35), (124, 36, 19),
             (168, 34, 21), (146, 24, 16)]
    disc(cv, crown, CAM)
    clump(cv, crown + [(132, 60, 14), (162, 58, 15), (104, 78, 11), (190, 80, 12), (146, 40, 12),
                       (146, 74, 13)], [CAM, CAM_D, CAM_H], CAM_H, CAM_D)
    # forest edge: cedars framing both sides, two layers of broadleaf bumps between them
    disc(cv, [(x, 102 + (i * 5) % 8, 12) for i, x in enumerate(range(58, 236, 15))], FOR2, RD)
    for cx, top, hw in [(10, 26, 12), (34, 44, 10), (56, 32, 11), (232, 50, 9), (247, 68, 7)]:
        cedar(cv, cx, top, hw, FOR, FOR2)
    disc(cv, [(x, 114 + (i * 3) % 7, 11) for i, x in enumerate(range(52, 240, 13))], FOR, RD)
    cv.rect(0, 122, 242, RD - 122, FOR)
    # the little Inari gate under the cedars
    cv.rect(77, 116, 23, 2, RED_D)
    cv.rect(76, 115, 25, 1, RED)
    cv.rect(80, 121, 17, 1, RED_D)
    for x in (81, 93):
        cv.rect(x, 118, 3, RD - 118, RED_D)
        cv.rect(x + 2, 118, 1, RD - 118, RED)
    cv.paint(["..c..", ".CCC.", "CCCCC", ".kYk.", ".kYk.", "ccccc", "..c..", "..c..", "..c..", ".ccc.", "ccccc"],
             {"c": ROAD, "C": POLE, "k": ROAD_D, "Y": YEL}, 68, 127)   # stone lantern
    cv.paint([".c..c.", ".cccc.", ".ccccc", ".ccc..", "c.ccc.", "c.ccc.", "cccccc", ".cccc.", "CCCCCC", ".CCCC.", ".CCCC.",
              "CCCCCC"], {"c": ROAD_L, "C": ROAD}, 58, 126)                # the Inari fox on its plinth
    cv.rect(79, 134, 19, 2, FOR2)                              # stone steps up to the shrine
    cv.rect(77, 136, 23, 2, ROAD_D)
    # bushes behind the stop, then the lamp light baked over everything so far
    bush = [(x, 128 + (i * 3) % 5, 10) for i, x in enumerate(range(108, 240, 12))] + [(140, 120, 14), (196, 118, 15),
                                                                                     (168, 112, 12), (222, 124, 10)]
    disc(cv, bush, LEAF, RD)
    clump(cv, bush, [LEAF, LEAF_L], LEAF_L, None, .2, -.9)
    for i, (x, y) in enumerate([(116, 129), (123, 123), (131, 131), (206, 121), (214, 128), (224, 119), (229, 130),
                                (198, 131), (100, 131), (236, 124)]):
        cv.rect(x, y, 3, 2, HYD if i % 3 else HYD2)
        cv.rect(x + 1, y - 1, 2, 4, HYD if i % 3 else HYD2)
        cv.set(x + 1, y, WHITE if i % 2 else K[4])
    relight(cv, in_cone, {**HAZE, LEAF: LEAF_L, LEAF_L: LEAF_H, K[3]: K[4], K[2]: K[3]})
    halo = lambda r: lambda x, y: (lambda d: 1 if d < r - 2 else .5 if d < r else 0)(math.hypot(x - LX, y - LY + 2))
    relight(cv, halo(9), HAZE)
    relight(cv, halo(5), {HAZE[CAM_D]: HAZE[CAM], HAZE[CAM]: HAZE[CAM_H]})
    # utility pole, crossarm, sagging wire, streetlamp
    for x in range(W):
        cv.set(x, WIRE + sag(x), POLE)
    cv.rect(PX, 48, 2, RD - 48, POLE)
    cv.rect(PX + 1, 70, 1, RD - 70, ROAD)
    cv.rect(PX - 7, 51, 16, 1, POLE)
    cv.rect(PX - 6, 50, 1, 1, POLE)
    cv.rect(PX + 7, 50, 1, 1, POLE)
    cv.rect(PX - 4, 63, 4, 1, POLE)
    cv.rect(PX - 7, 64, 7, 1, BLACK)
    cv.rect(PX - 8, 65, 9, 2, BLACK)
    cv.rect(PX - 6, 67, 5, 1, YEL)
    cv.rect(PX - 5, 68, 3, 1, WHITE)
    # road: wet dirt, darker towards the viewer, a grassy verge, ruts and puddles
    bands(cv, RD, [(150, ROAD), (H, ROAD_D)])
    cv.rect(0, RD, W, 1, FOR)
    for x in range(2, W, 5):                                   # grass tufts along the verge
        if (x * 7) % 11 < 6:
            c = FOR if x < 104 or x > 236 else LEAF
            cv.rect(x, RD - 1 - (x * 3) % 2, 1, 2 + (x * 3) % 2, c)
            cv.set(x + 1, RD, c)
    for x, y, n in [(0, 142, 96), (230, 142, 90), (0, 148, 70), (252, 148, 68)]:   # ruts worn by the bus
        cv.rect(x, y, n, 1, ROAD_D)
        cv.rect(x + (8 if x else -8) , y + 1, n, 1, ROAD_D)
    relight(cv, in_pool(62, 11), {ROAD: ROAD_L, ROAD_D: ROAD})
    relight(cv, in_pool(40, 6), {ROAD_L: ROAD_H})
    for x, y, n in [(30, 149, 26), (34, 150, 16), (258, 146, 30), (264, 147, 18)]:   # puddles hold the sky
        cv.rect(x, y, n, 1, K[2])
    for x, y, n in [(196, 152, 22), (200, 153, 12), (128, 154, 18)]:
        cv.rect(x, y, n, 1, K[3])
    cv.rect(LX - 4, 152, 8, 1, YEL)                            # the lamp, caught in a puddle
    cv.rect(LX - 2, 154, 5, 1, ROAD_H)
    # contact shadows and wet reflection for what never leaves: Satsuki and the sign
    for x0, x1 in ((SX + 5, SX + 16), (108, 114)):
        cv.rect(x0, GY, x1 - x0, 1, ROAD_D)
        cv.rect(x0 + 2, GY + 1, x1 - x0 - 4, 1, ROAD)
    # bus-stop sign
    cv.rect(110, 108, 2, GY - 108, POLE)
    cv.paint(SIGN, {"r": RED, "c": CREAM, "k": HAIR}, 103, 94)
    cv.paint(PLATE, {"r": RED, "c": CREAM, "k": HAIR}, 106, 111)
    for x in (205, 211, 217):                                  # three roadside Jizo in red bibs
        cv.paint([".ccc.", ".ccc.", ".ccc.", "rrrrr", "crrrc", "ccccc", "ccccc", "ccccc"], {"c": ROAD_L, "r": RED}, x, RD - 8)
    dim = {hx(a): b for a, b in {RED: RED_D, YEL: ROAD_H, SKIN: SKIN_D, PINK: PINK_D, LEMON: ROAD_H}.items()}
    src = Canvas(W, H)
    girls(src)
    for k in range(3):                                         # her reflection: squashed, dimmed scanlines
        for x in range(W):
            c = dim.get(src.px[GY - 8 - 10 * k][x])
            if c and (k < 2 or x % 2):
                cv.set(x, GY + 2 + 2 * k, c)
    for x in ACORNS:                                           # acorns dropped from the sack
        cv.rect(x, GY, 3, 1, HAIR)
        cv.rect(x, GY + 1, 3, 2, MEI)
        cv.set(x + 1, GY + 3, MEI)
    girls(cv)
    return cv


# ------------------------------------------------------------------ sprites
def runs(rows, pal, x0, y0):
    """ASCII art -> one stroked path per colour: 1px runs at y+.5 chained with relative moves."""
    out = {}
    for dy, row in enumerate(rows):
        x = 0
        while x < len(row):
            n = 1
            while x + n < len(row) and row[x + n] == row[x]:
                n += 1
            if row[x] in pal:
                out.setdefault(row[x], []).append((x0 + x, y0 + dy, n))
            x += n
    s = ""
    for ch, rs in out.items():
        d, ex, ey = "", 0, 0
        for x, y, n in rs:
            d += f"m{x - ex} {y - ey}h{n}" if d else f"M{x} {y}.5h{n}"
            ex, ey = x + n, y
        s += f"<path stroke='{pal[ch]}' d='{d}'/>"
    return s


BUS_HEAD = [   # broad round face: low ears, board on the forehead, slit pupils in round pale-yellow eyes with an
               # ochre rim, a rose nose, tabby marks on the cheeks, a lighter muzzle, and the grin: a banana lying
               # on its back, thickest in the middle with rounded upturned tips, one row of seven narrow teeth
    "O....................O",
    "OO..................OO",
    "OBO................OBO",
    ".OBO..OKKKKKKKKO..OBO.",
    ".OOOOOOKGKGGKGKOOOOOO.",
    "..OOOOOKKKKKKKKOOOOO..",
    ".OORRROOOOOOOOOORRROO.",
    "OOYYKYYOOOOOOOOYYKYYOO",
    "BOYYKYYOOOOOOOOYYKYYOB",
    "OOYYKYYOOOOOOOOYYKYYOO",
    "BOYYKYYOONNNNOOYYKYYOB",
    "OOORRRLLLLnnLLLLRRROOO",
    "LKLLLLLLLLLLLLLLLLLLKL",
    "LKKKLLLLLLLLLLLLLLKKKL",
    "LKWKKKKKKKKKKKKKKKKWKL",
    "LLKKWWKWWKWWKWWKWWKKLL",
    "LLLKWWKWWKWWKWWKWWKLLL",
    "LLLLKKKWWKWWKWWKKKLLLL",
    ".LLLLLKKKKKKKKKKLLLLL.",
    "..LLLLLLLLLLLLLLLLLL..",
    "...SSSSSSSSSSSSSSSS...",
    ".....SSSSSSSSSSSS.....",
]
BUS_X, BUS_T0 = -126, 52.8    # where it is parked (its beams just off-canvas), and when in the 120 s cycle it sets off
BELLY = 47                     # the row under the waiting Catbus's body; Totoro vanishes as he rises past it
STRIDE_PX, STRIDE_S = 3, .096  # it advances 3 px every 0.096 s, so a 150 px span of wire takes 4.8 s
HALT = 82                      # strides before it pulls up above the stop. It waits 9.6 s there (two tt-W periods,
                               # so its feet are back in step with the wire when it sets off), then 67 more take it out


def catbus():
    """Faces right, parked off-canvas left; `tt-c` carries it along the wire in 3 px steps to above the stop,
    and later on along the wire and out of frame. It never comes down.

    Feet on the wire: the body and each of the six near legs follow the wire's sag separately. They all run
    the same 4.8 s keyframes (`tt-W`, the wire's profile over one span), each delayed by its own distance
    along the wire, so every foot is on the wire's row at its own column on every step. A leg is a bar,
    narrowing to a paw, whose top hides behind the body; alternate legs lift 2 px on alternate beats, and
    the body dips 1 px. The six far legs are short dark stubs in the PNG that never reach the wire."""
    # the film's colours, by lamplight: caramel fur (= #b84, the vector legs), lighter tan on the muzzle and lower
    # body, a deeper shade underneath and on the rump, a cool blue-brown for what is on its far side, chocolate
    # stripes, amber windows
    O, L, S, C, B, A = "#bb8844", "#ddaa66", "#885a3c", "#5e4a48", "#4e2e1a", "#f4c868"
    cv = Canvas(66, 27)
    for i, (x, n) in enumerate([(3, 5), (2, 7), (1, 8), (0, 8), (0, 7), (0, 6), (0, 7), (1, 7), (1, 8), (2, 8), (3, 8),
                                (4, 7)]):
        cv.rect(x, 2 + i, n, 1, B if i % 3 == 1 else S if i > 8 else O)   # bushy striped tail curling up and forward
    for x in range(8, 48):                                     # body, column by column: an arched roof that is
        top = next(r for end, r in ((9, 10), (10, 9), (12, 8), (14, 7), (17, 6), (22, 5), (37, 4), (41, 5),   # highest
                                    (44, 6), (46, 7), (48, 8)) if x < end)                                   # amidships,
        for y in range(top, 24 - (4 if x < 9 else 3 if x < 10 else 2 if x < 12 else 1)):      # a rounded rump and belly,
            cv.set(x, y, B if y < top + 2 else S if y > 21 or x < 11 else L if y > 18 else O)  # and a dark-furred roof
    for x in (9, 15, 21, 27, 33, 39):                          # far legs, mid-stride, in shadow
        cv.rect(x, 23, 2, 3, C)
    cv.rect(9, 18, 38, 1, B)                                   # the dark belt under the windows
    for x in (21, 32, 43):                                     # tabby stripes: down between the windows, curving back
        cv.rect(x, 6, 2, 8, B)
        cv.rect(x - 1, 14, 1, 2, B)
    for x in (14, 25, 36):                                     # and across the flanks
        cv.rect(x, 20, 2, 1, B)
        cv.rect(x + 1, 21, 2, 1, B)
    for x in (12, 23, 34):                                     # arched windows, amber-lit, with brown seat backs
        cv.rect(x + 2, 10, 5, 1, A)
        cv.rect(x + 1, 11, 7, 1, A)
        cv.rect(x, 12, 9, 6, A)
        for sx in (x + 1, x + 5):
            cv.rect(sx, 15, 3, 3, S)
    for x, y in ((10, 6), (41, 4)):                            # the mouse lamps on the roof corners, glowing pink-violet
        cv.rect(x, y, 2, 2, "#e89ad8")
        cv.set(x + 1, y, "#f8d4f0")
    cv.paint(BUS_HEAD, {"O": O, "L": L, "S": S, "B": B, "Y": "#f2e48a", "R": "#c8a040", "K": "#20120e", "W": "#f2eedc",
                        "N": "#d07070", "n": "#9c4444", "G": "#77dd66"}, 44, 2)
    wire = lambda x: f"{-round(((BUS_X + x - PX) * STRIDE_S / STRIDE_PX - BUS_T0) % 4.8, 3):g}s"   # tt-W delay at local x
    legs = "".join(f"<path class='tt-G' style='animation-delay:{wire(x)},{-.192 * (i % 2):g}s' d='M{x} 20h3v8h-1v1h-2z'/>"
                   for i, x in enumerate(range(12, 48, 6)))
    # headlight beams: three stepped cones laid over each other, so the light is strongest near the eyes;
    # 60 px long, flaring to 31 px. tt-B brings them up in three steps as the nose reaches the canvas edge,
    # so the light arrives with the cat instead of sweeping in two seconds ahead of it. After 83 strides it
    # halts above the stop, where a still copy stands in for it (tt-W would go on rising and falling under a
    # runner that had stopped); 9.6 s later, with Totoro aboard, the runner carries on out of frame
    cone = lambda n: "M66 8" + "h5v-1" * (n - 1) + f"h5v{2 * n + 4}" + "h-5v-1" * (n - 1) + "h-5z"
    # where it waits: the same image and beams (<use>), standing still on legs cut to the wire under each one
    hx0 = BUS_X + STRIDE_PX * HALT
    hy = WIRE - 29 + sag(hx0 + 27)
    stand = "".join(f"M{hx0 + x} {hy + 20}h3V{WIRE + sag(hx0 + x) - 1}h-1v1h-2z" for x in range(12, 48, 6))
    wait = (f"<g class='tt-H'><path fill='#b84' d='{stand}'/>"
            f"<use href='#tt-bm' x='{hx0}' y='{hy}'/><use href='#tt-cb' x='{hx0}' y='{hy}'/></g>")
    return (wait + f"<g transform='translate({BUS_X} {WIRE - 29})'><g class='tt-c'>"
            f"<g fill='#b84'>{legs}</g>"
            f"<g class='tt-W' style='animation-delay:{wire(27)}'>"
            f"<g class='tt-B'><path id='tt-bm' fill='#fe8' fill-opacity='.14' d='{cone(12)}{cone(8)}{cone(4)}'/></g>"
            f"<g class='tt-m' style='animation-duration:.384s'>{png(cv, 0, 0, 66, 27, attr=" id='tt-cb'")}</g></g></g></g>")


CHU = [       # chu-Totoro with the acorn sack over his shoulder
    "......b.....b...",
    ".....bb.....bb..",
    ".....bb.....bb..",
    "......bbbbbbb...",
    ".tt..bbbbbbbbb..",
    "tsst.bwwbbbwwb..",
    "sssstbwkbkbkwb..",
    "ssssbbbbbbbbbbb.",
    "ssssbbcccccccbb.",
    ".ssbbcccccccccbb",
    "...bbcccccccccbb",
    "...bbcccccccccbb",
    "....bbcccccccbb.",
    ".....bbb...bbb..",
]
CHIBI = [
    "w.....w",
    "w.....w",
    "ww...ww",
    ".wwwww.",
    "wwwwwww",
    "wkwwwkw",
    "wwwwwww",
    "wwwwwww",
    ".ww.ww.",
]
DAD = [       # Dad off the bus: umbrella, glasses, suit and tie, briefcase
    "........kk.........",
    ".....kkkkkkkk......",
    "...kkkkkkkkkkkk....",
    ".kkkkkkkkkkkkkkkk..",
    "kkkkkkkkkkkkkkkkkk.",
    "k....k..k...k....k.",
    "......hhhhh........",
    ".....hhhhhhh.......",
    ".....hsssssh.......",
    ".....skkskks.......",
    ".....sssssss.......",
    "......sssss........",
    ".......wtw.........",
    ".....jjwtwjj.......",
    "....jjjjtjjjj......",
    "....jjjjtjjjj......",
    "...jjjjjtjjjjj.....",
    "...jj.jjjjj.jj.....",
    "...jj.jjjjj.jj.....",
    "...jj.jjjjj.jj.....",
    "...jj.jjjjj.jj.....",
    "...ss.jjjjj.ss.....",
    "......ppppp.bbb....",
    "......ppppp.bbb....",
    "......ppppp.bbb....",
    "......pp.pp........",
    "......pp.pp........",
    "......pp.pp........",
    "......pp.pp........",
    "......pp.pp........",
    "......pp.pp........",
    "......pp.pp........",
    "......pp.pp........",
    "......pp.pp........",
    "......pp.pp........",
    "......pp.pp........",
    "......pp.pp........",
    ".....kkk.kkk.......",
]
SPAL = {"w": "#fff", "k": "#012"}
CX_, CY_ = 112, GY - 14  # chu-Totoro image top-left (his body starts 3 px in, after the sack)
BX, BY = 104, GY - 9     # chibi-Totoro top-left
DX = TX                  # Dad's left edge once he has stepped clear of the bus: where Totoro stood


def art(rows, pal, x, y, attr=""):
    """ASCII art as a small nested PNG placed at (x, y)."""
    cv = Canvas(len(rows[0]), len(rows))
    cv.paint(rows, pal, 0, 0)
    return png(cv, 0, 0, cv.w, cv.h, (x, y), attr)


def cast():
    cv = Canvas(W, H)
    totoro(cv, TX, GY)
    t, e = TX, GY - 50   # eye rows are e+8..e+12
    ear = runs([" " * (12 - a) + "d" + "t" * (n - 1) for a, n in EAR], {"d": TOT_D, "t": TOT}, t - 12, e - 7)
    blink = (f"<g class='tt-k'><path fill='{TOT}' d='M{t - 11} {e + 8}h5v5h-5zm17 0h5v5h-5z'/>"
             f"<path stroke='#012' d='M{t - 11} {e + 10}.5h5m12 0h5'/></g>")
    eye = "h3v1h1v1h1v3h-1v1h-1v1h-3v-1h-1v-1h-1v-3h1v-1h1z"
    wide = (f"<g class='tt-w'><path fill='#fff' d='M{t - 10} {e + 7}{eye}m17 0{eye}'/>"
            f"<path stroke='#012' d='M{t - 9} {e + 10}.5h1m16 0h1'/></g>")
    grin = (f"<g class='tt-r'><path fill='#012' d='M{t - 13} {e + 13}h1v1h24v-1h1v3h-1v1h-1v1h-1v1h-20v-1h-1v-1h-1v-1h-1z'/>"
            f"<path stroke='#fff' stroke-width='2' stroke-dasharray='3 1' d='M{t - 10} {e + 16}h19'/></g>")
    side = (f"<g class='tt-g'><path fill='#fff' d='M{t - 9} {e + 10}h2v2h-2zm16 0h2v2h-2z'/>"
            f"<path fill='#012' d='M{t - 8} {e + 10}h2v2h-2zm16 0h2v2h-2z'/></g>")
    return (f"<g class='tt-h'><g class='tt-b'><g class='tt-e'>{ear}</g>{png(cv, TX - 24, GY - 72, 48, 72)}"
            f"{side}{blink}{wide}{grin}</g>"
            # the drip that lands on his head rides with him when he hops
            f"<path class='tt-i' style='--d:.6;--y:7px' fill='#bdf' d='M{TX - 4} {GY - 59}h1v2h-1z'/></g>")


def dads_bus():
    """A 1950s bonnet bus, heading right, so its door is on the far side, facing the stop. Drawn at half
    size and doubled, because it pulls up on the road in front of everyone. Parked off-canvas left."""
    cv = Canvas(56, 26)
    for y in range(2, 22):                                     # coach body, rounded roof
        i = 2 if y == 2 else 1 if y == 3 else 0
        cv.rect(2 + i, y, 40 - 2 * i, 1, CREAM_D if y < 4 else CREAM)
    cv.rect(42, 13, 11, 9, CREAM)                              # bonnet
    cv.rect(42, 12, 10, 1, CREAM_D)
    cv.rect(53, 15, 1, 7, CREAM)
    cv.rect(2, 15, 52, 2, RED_D)                               # waistband
    cv.rect(2, 21, 52, 1, TOT_D)
    for x in range(5, 39, 7):                                  # lit windows
        cv.rect(x, 6, 6, 6, YEL)
    cv.rect(40, 6, 2, 6, K[4])                                 # windscreen
    for x in (8, 43):                                          # wheels
        cv.rect(x + 1, 20, 4, 6, BLACK)
        cv.rect(x, 21, 6, 4, BLACK)
        cv.rect(x + 2, 22, 2, 2, POLE)
    cv.rect(53, 17, 2, 2, YEL)                                 # headlamp, bumper
    cv.rect(51, 22, 5, 1, POLE)
    return (f"<g class='tt-U'><g transform='translate(-250 {GY - 52})scale(2)'>"
            "<path fill='#fe8' fill-opacity='.16' d='M56 16h5v-1h5v-1h5v8h-5v-1h-5v-1h-5z'/>"
            f"{png(cv, 0, 0, 56, 26)}</g></g>")


RAIN = ((5, 2), (37, 7), (21, 14), (53, 20), (12, 27), (45, 31), (29, 38), (60, 43))   # one 64x48 tile of drops
CONE = ((128, 15, GY), (168, 4, GY), (177, 25, 114), (188, 15, 109), (196, 34, 111),   # lamp-lit drop columns:
        (203, 42, GY), (208, 4, GY), (217, 25, GY))                                    # x, phase, row it lands on
DRY = SX - 2, SX + 23    # between these columns it only rains down to Satsuki's umbrella


def rain():
    """The scrolling rain, with no clip-paths (T3 rejects url(#id), even inside the SVG).
    Everywhere: one pre-tiled 1-bit PNG strip, a tile taller than the canvas, shown through three nested
    <svg> viewports: left of Satsuki, right of her, and above her umbrella, so nothing falls on the girls.
    (Totoro's umbrella is too small to keep anything off him, and he is drawn over the rain anyway.)
    Inside the lamp cone: brighter drops, each column in its own 1px-wide viewport from the cone's edge
    down to whatever it lands on (the road, or Satsuki's umbrella)."""
    cv = Canvas(W, H + 48)
    for x, y in RAIN:
        for k in range(W // 64):
            for j in range(5):
                cv.rect(x + 64 * k, y + 48 * j, 1, 5, "#446688")
    out = "<defs>" + png(cv, 0, 0, W, H + 48, (0, -48), " id='tt-R'") + "</defs>"
    for x, w, h in ((0, DRY[0], H), (DRY[0], DRY[1] - DRY[0], SY - 10), (DRY[1], W - DRY[1], H)):
        out += f"<svg x='{x}' width='{w}' height='{h}'><use class='tt-n' href='#tt-R' x='{-x}'/></svg>"
    out += "<g class='tt-v' stroke='#eed'>"
    for x, y, end in CONE:
        top = math.ceil(LY - .5 + max(LX - 2 - (x + .5), x + .5 - (LX + 2), 0) * (GY - LY) / 52)
        a = (y - top) % 48 - 48                                    # first drop, one period above the viewport
        out += f"<svg x='{x}' y='{top}' width='1' height='{end - top}'><path d='M.5{a}v4{'m0 44v4' * ((end - top - a) // 48)}'/></svg>"
    return out + "</g>"


def sprites():
    """Back to front. Sprites always draw over the PNG, so the order here is the depth order. Depth on the
    road is the base row: a lower base is nearer, and the two vehicles that pull up at the stop are nearest."""
    sx, sy = SX, SY
    ring = lambda pts: (f"<path class='tt-a' d='{''.join(f'M{x - 1} {y}.5h2' for x, y in pts)}'/>"
                        f"<path class='tt-o' d='{''.join(f'M{x - 2} {y - 1}.5h4m-5 1h1m4 0h1m-5 1h4' for x, y in pts)}'/>")
    shower = "".join(f"M{x}.5-{8 + (i * 29) % 70}v5" for i, x in enumerate(
        [112 + (i * 13) % 34 for i in range(8)] + [DRY[1] + (i * 7) % 20 for i in range(6)]))
    drip = lambda x, y, n, d: f"<path class='tt-i' style='--d:{d};--y:{n}px' d='M{x} {y}h1v2h-1z'/>"
    return (
        # 1. the water surface: puddle rings and the lamp's shimmer. Everything that moves draws over them.
        f"<g stroke='#8ac'>{ring([(140, 152), (216, 148), (66, 151), (242, 152)])}</g>"
        f"<path class='tt-o' style='animation-duration:1.7s' stroke='#fd7' d='M{LX - 7} 152.5h2m10 0h2m-9 2h2'/>"
        # 2. the Catbus, up on the wire
        + catbus()
        # 3. the lantern's flame
        + "<path class='tt-g' style='animation-duration:3.7s' fill='#d73' d='M70 130h1v2h-1z'/>"
        # 4. rain: in front of the scenery, behind the cast
        + rain()
        # 5. Totoro, then the small Totoros and sprouts, who follow half a second behind. The nested <svg> starts
        #    at the waiting Catbus's belly and ends at the road, so when they leap up to it they vanish into it
        + f"<g class='tt-T'><path class='tt-sh' stroke='#bdf' d='{shower}'/></g>"
          f"<svg y='{BELLY}' height='{GY - BELLY}' viewBox='0 {BELLY} {W} {GY - BELLY}'><g class='tt-T'>"
        + cast() + "</g>"
        + f"<g class='tt-T' style='animation-delay:.5s;--x:24px'><g class='tt-x'>{runs(CHIBI, SPAL, BX, BY)}</g>"
          f"<g class='tt-m'>{art(CHU, {'b': BLUE, 'c': CREAM, 'w': WHITE, 'k': '#001122', 's': '#c8a060', 't': '#7a5a30'}, CX_, CY_)}"
          f"<path class='tt-k' style='animation-duration:4.1s' stroke='{BLUE}' d='M{CX_ + 6} {CY_ + 5}.5h2m3 0h2m-7 1h2m3 0h2'/></g>"
          f"<path class='tt-z' stroke='#9d5' d='{''.join(f'M{x - 1} {GY - 5}.5h2m1 0h2m-4 1h3M{x + 1}.5 {GY - 3}v3' for x in ACORNS)}'/></g>"
          "<g class='tt-T'><g fill='#bdf' stroke='#bdf'>"
          f"<path class='tt-d' d='M{TX + 9} {WIRE + sag(TX + 9) + 1}h1v3h-1z'/>"
          f"<path class='tt-p' d='M{TX + 5} {GY - 69}.5h1m7 0h1m-7-2h1m3 0h1m-3-2h1'/>{drip(TX + 21, GY - 59, 56, 2.1)}</g></g></svg>"
        # 6. Satsuki: blink, a sideways glance at Totoro (and, later, at Dad); Mei breathing
        + f"<path class='tt-k' style='animation-duration:5.3s' stroke='{SKIN}' d='M{sx + 7} {sy + 5}.5h1m4 0h1'/>"
          f"<g class='tt-g' style='animation-duration:17s'><g id='tt-ey'><path fill='{SKIN}' d='M{sx + 7} {sy + 5}h1v2h-1zm5 0h1v2h-1z'/>"
          f"<path fill='#012' d='M{sx + 6} {sy + 5}h1v2h-1zm5 0h1v2h-1z'/></g></g><use class='tt-w' href='#tt-ey'/>"
          "<use class='tt-r' href='#tt-ey'/><use class='tt-S' href='#tt-ey'/>"
        + f"<g class='tt-m' style='animation-duration:4.4s'>{runs([r[15:] for r in GIRLS[2:9]], GPAL, sx + 15, sy + 2)}</g>"
        # 7. Totoro's gift, a leaf-wrapped bundle: it crosses from his paw to her hand and she keeps hold of it
        + f"<path class='tt-N' fill='#7b5' d='M{sx + 1} {sy + 16}h1v-1h2v1h1v3h-4z'/>"
        # 8. Dad, who walks round the front of his bus to where Totoro was standing
        + f"<g class='tt-D'>{art(DAD, {'k': BLACK, 'h': HAIR, 's': SKIN, 'w': WHITE, 't': RED_D, 'j': '#6b6f66', 'p': TOT_D, 'b': MEI}, DX, GY - len(DAD))}</g>"
        # 9. falling water: drips off Satsuki's umbrella and the lamp
        + f"<g fill='#bdf'>{drip(sx - 2, sy - 2, 28, 0)}{drip(sx + 22, sy - 2, 28, 1.3)}{drip(PX - 1, 67, 77, 1.7)}</g>"
        # 10. Dad's bus at the stop, nearest of all
        + dads_bus()
        # 11. the lamp stutters as the Catbus's beams sweep over it: a brief shadow on its cone
        + f"<path class='tt-f' fill='#012' opacity='0' d='M{LX - 6} 66h11l56 78v10h-124v-10z'/>"
    )


SPRITES = sprites()
# Timing. Ambient loops have short unrelated periods. The story runs once per 120 s:
#     0-53 s   Totoro waits beside Satsuki, with the small Totoros at his feet
#     5-13 s   a drop falls on his umbrella: wide eyes, grin, hop, a shower from the tree, the acorns sprout
#    45-53 s   and again (40 s cycle; the third time he is gone)
#    53-61 s   the Catbus gallops in along the wire, beams first; the lamp stutters at 59 s; it waits overhead
#    61-62 s   Totoro hands Satsuki the bundle
#    68-69 s   Totoro leaps up into the Catbus, umbrella and all; the small Totoros hop up after him
#    70-77 s   it gallops on along the wire and out of frame
#    77-84 s   rain
#    84-91 s   Dad's bus pulls in
#    94-96 s   Dad comes round the front of it; Satsuki looks up at him
#    98-106 s  the bus pulls away
#   106-116 s  the three of them; then Dad and the bundle fade out
#   117-120 s  Totoro and the small Totoros fade back in, and it starts again
CSS = (
    # ambient
    ".tt-n,.tt-v path{animation:tt-n .6s steps(6) infinite}@keyframes tt-n{to{translate:0 48px}}"
    f".tt-b{{transform-origin:0 {GY}px;animation:tt-b 2.7s steps(3,jump-none) infinite alternate}}@keyframes tt-b{{to{{scale:1 1.02}}}}"
    ".tt-k,.tt-g,.tt-w,.tt-r,.tt-p,.tt-d,.tt-i,.tt-a,.tt-o,.tt-S,.tt-N,.tt-D,.tt-H{opacity:0}"
    ".tt-e{animation:tt-e 11s steps(1) infinite}@keyframes tt-e{62%,65%{translate:-1px 1px}63.5%,66.5%{translate:0}}"
    ".tt-g{animation:tt-g 23s steps(1) infinite}@keyframes tt-g{38%{opacity:1}56%{opacity:0}}"
    ".tt-k{animation:tt-k 7s steps(1) infinite}@keyframes tt-k{96%{opacity:1}}"
    ".tt-x{animation:tt-x 29s steps(3) infinite}@keyframes tt-x{55%,90%{opacity:1}65%,80%{opacity:.15}}"
    ".tt-m{animation:tt-m 2.6s steps(1) infinite}@keyframes tt-m{50%{translate:0 1px}}"
    ".tt-i{animation:tt-i 3.1s calc(var(--d)*-1s) steps(7) infinite}"
    "@keyframes tt-i{0%{opacity:1}30%{opacity:1;translate:0 var(--y)}31%{opacity:0}}"
    ".tt-a{animation:tt-a 2.3s steps(1) infinite}@keyframes tt-a{0%{opacity:1}9%{opacity:0}}"
    ".tt-o{animation:tt-o 2.3s steps(1) infinite}@keyframes tt-o{9%{opacity:1}22%{opacity:0}}"
    # the drip, every 40 s from 5 s: a drop swells on the wire and falls on his umbrella; wide eyes, a grin, a
    # hop in 3 px steps, a shower shaken out of the tree, and the acorns sprout
    ".tt-d{animation:tt-d 40s -35s steps(6) infinite}"
    "@keyframes tt-d{1.5%{opacity:1;translate:0 0}3.5%{opacity:1;translate:0 18px}3.6%,to{opacity:0;translate:0 18px}}"
    ".tt-p{animation:tt-p 40s -35s steps(1) infinite}@keyframes tt-p{3.5%{opacity:1}4.75%{opacity:0}}"
    ".tt-w{animation:tt-w 40s -35s steps(1) infinite}@keyframes tt-w{3.5%{opacity:1}7.5%{opacity:0}}"
    ".tt-r{animation:tt-r 40s -35s steps(1) infinite}@keyframes tt-r{7.5%{opacity:1}18.75%{opacity:0}}"
    ".tt-h{animation:tt-h 40s -35s steps(3) infinite}@keyframes tt-h{9%{translate:0 0}10.2%{translate:0 -9px}11.4%,to{translate:0 0}}"
    ".tt-sh{animation:tt-sh 40s -35s steps(16) infinite}@keyframes tt-sh{11%{translate:0 0}14.25%,to{translate:0 256px}}"
    f".tt-z{{scale:1 0;transform-origin:0 {GY}px;animation:tt-z 40s -35s steps(3) infinite}}"
    "@keyframes tt-z{12.75%{scale:1 0}13.9%,50%{scale:1 1}51%,to{scale:1 0}}"
    # the story (120 s). Totoro waits, then leaps: up fast, slowing, into the Catbus on the wire (the nested <svg>
    # clips him at its belly), and is gone; he fades back in over the last 3 s, so that the loop starts, and every
    # still preview shows, the two of them waiting. The small Totoros run the same keyframes half a second later,
    # drifting 24 px across (--x) to reach it
    ".tt-T{animation:tt-T 120s steps(4) infinite}"
    "@keyframes tt-T{56.5%{opacity:1;translate:0}56.8%{opacity:1;translate:0 -60px}57.3%{opacity:1;translate:var(--x,0) -100px}"
    "57.31%{opacity:0;translate:0 -100px}96.9%{opacity:0;translate:0}99.4%,to{opacity:1;translate:0}}"
    # the Catbus on the wire: 82 steps of 3 px in, 9.6 s waiting above the stop as a still copy (tt-H), 67 steps
    # out; tt-W is the
    # wire's sag over one 150 px span (see catbus()), tt-G a leg lifting, tt-B its beams coming up
    ".tt-c{animation:tt-c 120s steps(1) infinite}"
    "@keyframes tt-c{44%{translate:0;opacity:1;animation-timing-function:steps(82)}50.56%{translate:246px;opacity:1}"
    "50.57%,58.55%{translate:246px;opacity:0}58.56%{translate:246px;opacity:1;animation-timing-function:steps(67)}"
    "63.92%,to{translate:447px;opacity:1}}"
    ".tt-H{animation:tt-H 120s steps(1) infinite}@keyframes tt-H{50.56%{opacity:1}58.56%{opacity:0}}"
    ".tt-W{animation:tt-W 4.8s steps(1) infinite}.tt-G{animation:tt-W 4.8s steps(1) infinite,tt-G .384s steps(1) infinite}"
    "@keyframes tt-W{4%{translate:0 1px}12%{translate:0 2px}20%{translate:0 3px}32%{translate:0 4px}"
    "68%{translate:0 3px}80%{translate:0 2px}88%{translate:0 1px}96%{translate:0 0}}"
    "@keyframes tt-G{50%{transform:translateY(-2px)}}"
    ".tt-B{animation:tt-B 120s steps(3) infinite}@keyframes tt-B{0%,45.2%{opacity:0}46.1%,to{opacity:1}}"
    ".tt-f{animation:tt-f 120s steps(1) infinite}@keyframes tt-f{49.2%,49.5%{opacity:.4}49.35%,49.65%{opacity:0}}"
    # the bundle: three steps from his paw to her hand
    ".tt-N{animation:tt-N 120s steps(3) infinite}"
    "@keyframes tt-N{50.99%{opacity:0;translate:-15px -18px}51%{opacity:1;translate:-15px -18px}52%,96.5%{opacity:1;translate:0}97%,to{opacity:0}}"
    # Dad's bus: 36 steps of 8 px in, a wait, 36 out; Dad walks 48 px in 8 steps; Satsuki looks at him
    ".tt-U{animation:tt-U 120s steps(36) infinite}@keyframes tt-U{70%{translate:0}76%,82%{translate:288px}88%,to{translate:576px}}"
    ".tt-D{animation:tt-D 120s steps(8) infinite}"
    "@keyframes tt-D{77.99%{opacity:0;translate:-48px}78%{opacity:1;translate:-48px}80%,96.5%{opacity:1;translate:0}97%,to{opacity:0}}"
    ".tt-S{animation:tt-S 120s steps(1) infinite}@keyframes tt-S{78%{opacity:1}96.5%{opacity:0}}"
)
THEME = {
    "position": "center 50%",  # set by the main session for wide panes, which crop top and bottom (see wide.png)
    "canvas": "#0a1622",
    "accent": "#f5cf6e",
    "overlay": "#081320",
    "colors": {"sidebar": "#0a1520", "sidebarRowSelected": "#1b3848", "sidebarBorder": "#1a3040",
               "surface": "#10202e", "border": "#22394a", "text": "#e7eef2", "textMuted": "#93a8b8"},
}
