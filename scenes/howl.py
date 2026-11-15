"""Howl's Moving Castle: the castle strides in along the ridge above the alpine lake, sits down to rest by the
water's edge, then stands and ambles off down the hill, while the household (Markl in his bearded disguise, Heen, Sophie,
Calcifer, Howl, and the Witch of the Waste in her chair) waits in the flower meadow and Turnip Head hops by.

Static layer (PNG, 320x180): sky, cumulus, snowy peaks, lake, ridge, flower meadow, Calcifer's pool of light.
Sprites (SVG), back to front: billowing cloud caps and drifting small clouds, birds, lake glints, the castle (shadow, smoke, then its parts as
viewports onto one atlas PNG: smokestacks, mast, roofs, legs, fins, stern, upper dome, bow, lower hull, front
dome, and the eyelids of its eye-ports), Turnip Head, the
stems of the flowers in front of him, the characters (one PNG, so Turnip Head passes BEHIND them) with their
blinks, flutters and greetings, Calcifer, the heads of the wind-blown flowers.

The castle's loop is 180s and starts 45s in, so the theme opens on it resting. In loop time: 0-36s it walks in
from the left, one footfall every 0.6s, 4px a footfall (each leg pair jumps ahead of the body while lifted, so a
planted foot never slides), with a ripple running through its parts on every footfall, bow first, smokestacks
last; 36-40s it sits, each part sinking a beat after the one in front, the hull settling over its legs; to 112s
it rests: fins drooped, eye-ports half shut, breathing 1px; 112-116s it stands; 117-171s it ambles off to the
right at half the pace and, from the brow of the hill at x=238, down the slope and out of the frame. The
household greets it as it arrives and sits (32-41s) and sees it off (112-122s): Sophie waves, Markl throws his
arms up, the Witch wakes, Calcifer flares.
Other moments: Turnip Head every 80s, birds every 67s.
"""
import base64, math, random, struct, zlib
from lib import Canvas, UNPAINTED, hx

NAME = "Howl's Moving Castle"
SIZE = (320, 180)
W, H = SIZE
COLORS = 64

SKY = ["#2f6cc6", "#4281d5", "#5b99e2", "#7bb3ec", "#9fcbf3", "#c4e2f8"]
WHT, C1, C2, C3 = "#ffffff", "#e8f1fb", "#c5d8f0", "#9fbbe2"
FAR, FAR2, MT1, MT2 = "#93aede", "#7f9bd0", "#6f8ec6", "#5270ad"
HILL, HILL2 = "#4c8a84", "#3b7470"
LAKE = ["#6fcbd3", "#55b9c8", "#43a5bd", "#3690b2"]
R0, R1, R2 = "#b9e67a", "#8fd062", "#72bf55"          # sunlit ridge
G1, G2, G3 = "#58ad48", "#489a42", "#35803c"          # foreground meadow
PNK, PK2, YEL, RED, LIL = "#f7a8c8", "#ea6f9f", "#ffd85e", "#f2604c", "#b9a2f2"
HZ = 92            # far shore row


def bands(cv, y, rows):
    """rows: [(y_end, colour)], flat bands with a 3-row ordered-dither seam (from spirited_away)."""
    prev = None
    for y1, c in rows:
        for yy in range(y, y1):
            k = yy - y
            for x in range(cv.w):
                mix = prev and ((k == 0 and (x % 4 != (yy % 2) * 2)) or (k == 1 and (x + yy) % 2)
                                or (k == 2 and x % 4 == (yy % 2) * 2))
                cv.set(x, yy, prev if mix else c)
        prev, y = c, y1


def cumulus(cv, puffs, base):
    """Painterly cumulus: the puffs are spheres, the nearest surface wins, and each pixel is cel-shaded in four
    tones by its surface normal (sun upper-left) with the lower half of the mass falling into blue shadow."""
    top = min(cy - r for _, cy, r in puffs)
    for y in range(max(0, int(top)), base):
        for x in range(W):
            best = None
            for cx, cy, r in puffs:
                dx, dy = x + .5 - cx, y + .5 - cy
                d2 = dx * dx + dy * dy
                if d2 <= r * r:
                    z = math.sqrt(r * r - d2)
                    if best is None or z > best[0]:
                        best = (z, dx / r, dy / r, z / r)
            if best:
                _, nx, ny, nz = best
                k = -.5 * nx - .72 * ny + .3 * nz + .3 - .75 * (y - top) / (base - top)
                c = WHT if k > .42 else C1 if k > .08 else C2 if k > -.34 else C3
                if base - y <= 2:
                    c = C3 if base - y == 1 or (x + y) % 2 else C2
                cv.set(x, y, c)


def mountains(cv, peaks, lit, shd, snow=True):
    """peaks: [(cx, top, left slope, right slope, snow depth)]. Lit left faces, shaded right faces, zigzag snow
    caps and a few diagonal gullies. Rows come in identical pairs, which halves what the slopes cost."""
    for x in range(W):
        y0, i = min((top + (cx - x) * sl if x < cx else top + (x - cx) * sr, i)
                    for i, (cx, top, sl, sr, sd) in enumerate(peaks))
        cx, top, sl, sr, sd = peaks[i]
        for y in range(int(y0) // 2 * 2, HZ):
            k = (y - top) // 2 * 2
            left = x < cx + k * .3 + (2 if k % 8 > 3 else 0)
            gully = left and k > sd and (cx - x + k // 2) % 16 < 3
            cap = snow and k < sd + ((x // 2) % 2) * 2 - (0 if left else 4)
            streak = snow and left and not cap and k < sd + 8 and (x + k // 2) % 9 == 0
            cv.set(x, y, (WHT if left else C2) if cap or streak else (lit if left and not gully else shd))


# heads of the tall wind-blown flowers, three colours of three
WIND = [(34, 146), (206, 149), (262, 152), (56, 151), (113, 146), (244, 150), (20, 152), (72, 144), (232, 153)]


TBASE = 149        # the row Turnip Head's pole stands on as he hops across the knoll (sprite, drawn over the PNG)


def g1(x):
    """Top row of the sunlit ridge the castle walks on. Past x=238 the hill rolls down to the right, 1px in
    every 6: the slope the castle follows out of the frame (see hw-h)."""
    return 117 + (x < 24) + max(0, (x - 238) // 6)


def g2(x):
    """Top row of the foreground knoll the characters stand on."""
    return 137 + (x - 150) ** 2 // 3400


def draw():
    cv = Canvas(W, H)
    bands(cv, 0, [(12, SKY[0]), (28, SKY[1]), (44, SKY[2]), (60, SKY[3]), (76, SKY[4]), (HZ, SKY[5])])
    # cumulus: a great tower behind the castle's walk, smaller masses left and right
    cumulus(cv, [(150, 54, 30), (116, 64, 24), (184, 62, 26), (138, 32, 17), (166, 36, 20), (120, 44, 15),
                 (96, 72, 16), (210, 72, 17), (192, 42, 13), (80, 80, 10), (230, 80, 10), (152, 20, 10),
                 (104, 54, 10), (206, 54, 10)], 87)
    cumulus(cv, [(290, 40, 15), (308, 54, 18), (272, 58, 12), (322, 36, 10), (282, 26, 8)], 78)
    cumulus(cv, [(20, 52, 12), (38, 62, 11), (2, 62, 12), (52, 70, 7)], 76)
    # far hazy range, then the near snowy peaks left and right, then dark foothills along the shore
    mountains(cv, [(96, 70, 1.1, .9, 4), (140, 76, 1.2, 1.3, 2), (190, 72, 1.0, 1.2, 4), (232, 78, 1.3, 1.0, 2)],
              FAR, FAR2)
    mountains(cv, [(34, 48, 1.0, 1.15, 10), (0, 60, 1.2, 1.3, 6), (70, 66, .9, 1.4, 4),
                   (270, 44, 1.05, 1.1, 12), (304, 56, 1.2, 1.2, 8), (240, 68, 1.3, 1.0, 4)], MT1, MT2)
    for x in range(W):
        y = 88 + int(1.5 * math.sin(x * .09) + 1.5 * math.sin(x * .023 + 2))
        cv.rect(x, y, 1, HZ - y, HILL if (x // 3 + y) % 2 or y > 88 else HILL2)
        cv.rect(x, HZ - 1, 1, 1, HILL2)
    # lake: lighter far water, shimmer under the far shore, reflections of the two snowy massifs
    bands(cv, HZ, [(97, LAKE[0]), (105, LAKE[1]), (116, LAKE[2]), (H, LAKE[3])])
    for x in range(0, W, 6):
        cv.rect(x, HZ + 1, 4, 1, C1)
        cv.rect(x + 3, HZ + 3, 2, 1, C1)
    for cx, n in [(34, 30), (270, 34)]:
        for i in range(5):
            cv.rect(cx - n + i * 5, HZ + 5 + 2 * i, 2 * n - i * 11, 1, LAKE[2] if i < 3 else LAKE[3])
        cv.rect(cx - 6, HZ + 6, 12, 1, C1)
        cv.rect(cx - 3, HZ + 8, 7, 1, C1)
    # the sunlit ridge with small far flowers on every third row
    far = {0: WHT, 5: PNK, 11: YEL, 16: G1, 20: WHT, 25: LIL}
    for x in range(W):
        g = g1(x)
        cv.rect(x, g, 1, 2, R0)
        for y in range(g + 2, H):
            c = R1 if y < g + 8 or (y < g + 11 and (x + y) % 2) else R2      # shaded by depth below the crest
            if y % 3 == 0 and y > g + 3 and math.sin(x * .05 + y * .6) + math.sin(x * .017 - y * .3) > -.6:
                c = far.get((x + y // 3 * 11) % 30, c)
            cv.set(x, y, c)
    # foreground knoll: a lit crest, deeper greens below, grass ticks and bigger blossoms
    for x in range(W):
        g = g2(x)
        for y in range(g, H):
            k = y - g
            cv.set(x, y, R1 if k < 1 else G1 if k < 9 or (k < 12 and (x + y) % 2) else G2)
        if x * 7 % 13 < 4:           # ragged grass along the crest
            cv.rect(x, g - 1 - (x * 5 % 17 < 3), 1, 2, G1)
    r = random.Random(11)
    for _ in range(70):              # grass tufts
        x, y = r.randrange(W), r.randrange(139, H)
        # Depth rule for everything baked into the knoll: it may reach into the rows Turnip Head's pole crosses
        # (<= TBASE) only if it is rooted no nearer than he is; otherwise the pole would be drawn over something
        # that stands in front of him. Tufts and blossoms that broke the rule are pulled back to his row.
        y = TBASE if TBASE < y < TBASE + 3 else y
        if y > g2(x) + 2:
            cv.rect(x, y - 1, 1, 2, G3 if y > g2(x) + 9 else G2)
            cv.set(x + 1, y - 2, R1 if r.random() < .3 else G1)
    for _ in range(130):             # blossoms, scattered in drifts; bigger toward the viewer
        x, y = int(r.gauss(r.choice((40, 110, 170, 230, 290)), 30)), r.randrange(139, H)
        if not 0 <= x < W or y < g2(x) + 3:
            continue
        pet, mid = r.choice(((WHT, YEL), (WHT, YEL), (PNK, PK2), (PNK, WHT), (YEL, RED), (LIL, WHT), (PK2, YEL)))
        if y > 146 and r.random() < .6:
            y = TBASE - 2 if TBASE - 2 < y < TBASE + 2 else y
            cv.rect(x - 1, y, 3, 1, pet)
            cv.rect(x, y - 1, 1, 3, pet)
            cv.set(x, y, mid)
            cv.set(x, y + 2, G3)
        else:
            y -= y == TBASE
            cv.rect(x, y, 2 if y > 142 else 1, 1, pet)
            cv.set(x, y + 1, G3)
    for x, y in WIND:                # stems of the tall flowers whose heads sway (sprites)
        cv.rect(x, y + 2, 1, 5, G3)
        cv.set(x + 1, y + 4, G2)
    # Calcifer's glow: a pool of warm light on the grass under him, two flat steps (greens only, so the
    # flowers keep their colours and the palette stays small)
    greens = {hx(c) for c in (R0, R1, R2, G1, G2, G3)}
    for y in range(FY - 5, FY + 24):
        for x in range(FX - 9, FX + 20):
            d = math.hypot(x - FX - 5, y - FY - 8.5)
            if d < 12.5 and cv.px[y][x] in greens:
                a = .34 if d < 7.5 else .16
                cv.px[y][x] = tuple(round(p * (1 - a) + q * a) for p, q in zip(cv.px[y][x], (255, 221, 102)))
    # soft shadows where the characters stand
    for x, n in [(100, 11), (121, 14), (138, 15), (177, 15), (196, 17)]:
        cv.rect(x, 153, n, 2, G3)
        cv.rect(x + 2, 155, n - 4, 1, G3)
    return cv


# ---------------------------------------------------------------------------------------------------------
# The castle, after the film's design: a tall stack of riveted domes, each with two ringed eye-ports and a
# battlement collar, over a great lower hull and jutting bow; cottages stuck on like barnacles; smokestacks, a
# mast with a crow's nest and bat-wing fins at the stern. Every part is drawn on its own layer of one shared
# canvas so the parts can heave separately (see atlas() and the hw-k wave further down).
FAM = {  # rim light, light, mid, dark, deep shadow
    "d": ["#d2ad8e", "#9d7d6c", "#735d66", "#4f445b", "#342f49"],   # the domes: rusted copper going to purple shade
    "i": ["#b9b4c6", "#8a859c", "#625f78", "#45445c", "#2e2d42"],   # purplish-grey iron
    "h": ["#cdbb8b", "#a18f63", "#786a53", "#554e4c", "#383542"],   # the lower hull: weathered ochre plate
    "k": ["#ece1ae", "#cfbb70", "#a08c4f", "#6f633d", "#463f2c"],   # cream-khaki collar bands
    "g": ["#a6cbad", "#72a690", "#4d8071", "#366056", "#254340"],   # verdigris
}
K, K2, K3 = "#211d2a", "#353040", "#575066"                          # outline and soot-black iron
WH, WHS, WHD = "#ebe4d2", "#c3b9ab", "#8f8582"                       # cottage plaster
RF, RF2, RF3 = "#c9554c", "#8e3a3b", "#e58a72"                       # red-pink roof tiles
OR, OR2, PU, PU2 = "#d98c4c", "#a4602f", "#806299", "#5a4372"        # orange tiles, purple slates
TH, TH2, LIT = "#cfa85c", "#977640", "#ffd85e"                       # thatch, lit windows
FN, FN2, FN3 = "#a497b0", "#84758f", "#4b3f58"                       # the fins' membrane and ribs
CW, CH = 74, 94


def outline(cv, c=K):
    """Dark line around everything painted so far; where parts overlap it separates them."""
    edge = [(x, y) for y in range(cv.h) for x in range(cv.w) if cv.px[y][x] == UNPAINTED and any(
        0 <= x + dx < cv.w and 0 <= y + dy < cv.h and cv.px[y + dy][x + dx] != UNPAINTED
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        cv.set(x, y, c)
    return cv


def orb(cv, cx, cy, rx, ry, fam, y1=None, seams=(), keep=None, dk=0, t=(.82, .5, .1, -.36)):
    """A riveted metal bulge: an ellipse (cut off below row y1) cel-shaded in five tones, sun upper left,
    with plate seams along the given meridians and a rivet row a third of the way down."""
    f = FAM[fam]
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2 if y1 is None else y1):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            u, v = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            if u * u + v * v > 1 or (keep and not keep(x, y)):
                continue
            k = -(u * .62 + v * .72)
            l = dk + (0 if k > t[0] else 1 if k > t[1] else 2 if k > t[2] else 3 if k > t[3] else 4)
            m = u / math.sqrt(max(.02, 1 - v * v))
            if any(abs(m - s) < .5 / rx for s in seams):
                l += 1
            elif abs(v + .3) < .5 / ry and x % 3 == 0:
                l -= 1
            elif v > -.1 and (x * 5 + int(cx)) % 9 == 0 and (x + y) % 3:
                l += 1                                   # streaks of grime running down from the rivets
            cv.set(x, y, f[max(0, min(4, l))])


def collar(cv, x0, x1, y):
    """The battlement ring round a dome's base: a cream band with merlons along its top and a row of studs."""
    k = FAM["k"]
    for x in range(x0, x1):
        t = min(3, (x - x0) * 4 // (x1 - x0))            # it turns away from the sun toward the right
        end = x in (x0, x1 - 1)
        cv.set(x, y, K if (x - x0) % 3 == 2 or end else k[max(0, t - 1)])
        cv.set(x, y + 1, k[max(0, t - 1)])
        cv.set(x, y + 2, k[4] if (x - x0) % 4 == 1 else k[t])
        cv.set(x, y + 3, K if end else k[min(4, t + 1)])
        cv.set(x, y + 4, K)


def port(cv, x, y):
    """A ringed porthole, 5px across: the 'eyes' on each dome."""
    i = FAM["i"]
    for dx in range(5):
        for dy in range(5):
            if (dx in (0, 4)) + (dy in (0, 4)) == 1:
                cv.set(x + dx, y + dy, "#e4ddcf" if dx + dy < 4 else i[1])
            elif 0 < dx < 4 and 0 < dy < 4:
                cv.set(x + dx, y + dy, K)
    cv.set(x + 1, y + 1, i[3])


def gun(cv, x0, x1, y):
    """A cannon barrel sticking out level, with a muzzle ring."""
    i = FAM["i"]
    cv.rect(x0, y, x1 - x0, 1, i[0])
    cv.rect(x0, y + 1, x1 - x0, 1, i[2])
    cv.rect(x0, y + 2, x1 - x0, 1, i[4])
    cv.rect(x1 - 2, y - 1, 2, 5, i[1])
    cv.rect(x1 - 1, y - 1, 1, 5, i[3])
    cv.set(x1 - 1, y + 1, K)


def cottage(cv, x, y, w, h, rh, lean=0, roof=(RF, RF2, RF3), wins=()):
    """A cottage stuck on like a barnacle: plaster walls from row y down h rows, a gable roof rh rows high
    above, the whole thing sheared `lean` px per 8 rows (positive tips forward)."""
    o = lambda yy: round(lean * (y + h - 1 - yy) / 8)
    for yy in range(y, y + h):
        cv.rect(x + o(yy), yy, w, 1, WH)
        cv.rect(x + o(yy) + w - 2, yy, 2, 1, WHS)
    cv.rect(x + o(y), y, w, 1, WHD)
    for i in range(rh):
        yy = y - 1 - i
        n = max(1, round((w + 2) * (rh - i) / rh))
        x0 = x - 1 + o(yy) + (w + 2 - n) // 2
        cv.rect(x0, yy, n, 1, roof[0] if i % 2 else roof[2])
        cv.rect(x0 + (n * 3 + 2) // 5, yy, n - (n * 3 + 2) // 5, 1, roof[1])
    for wx, wy, c in wins:
        cv.rect(x + wx + o(y + wy), y + wy, 1, 2, c)


def slab(cv, x, y, w, h, c1, c2):
    """A tiled roof seen side-on: rows of tiles, every third one darker, staggered row to row."""
    for r in range(h):
        for i in range(w):
            cv.set(x + i, y + r, c1 if (i + r) % 3 else c2)
    cv.rect(x - 1, y + h - 1, w + 2, 1, c2)


def stack(cv, x, top, bot, w=3, flare=False):
    """A smokestack in ringed segments, leaning back a pixel every nine rows."""
    i = FAM["i"]
    xo = lambda y: x - (bot - y) // 9
    for y in range(top, bot):
        ring = (y - top) % 5 == 3
        for n in range(w):
            cv.set(xo(y) + n, y, i[4] if ring else i[0] if n == 0 else i[1] if n < w - 1 else i[3])
    cv.rect(xo(top) - 1, top, w + 2, 2, i[2])
    cv.set(xo(top) - 1, top, i[0])
    if flare:
        cv.rect(xo(top) - 2, top - 2, w + 4, 2, i[2])
        cv.rect(xo(top) - 2, top - 2, 2, 1, i[0])
        cv.rect(xo(top) + w + 1, top - 2, 1, 2, i[4])


def hip(cv, x, y):
    cv.rect(x - 1, y, 4, 3, K2)
    cv.set(x, y, K3)


def P_stacks():
    """Smokestacks at the rear, the tallest behind the roofs, and a thin flue tucked in beside it."""
    cv = Canvas(CW, CH)
    stack(cv, 34, 1, 32, 4)
    stack(cv, 22, 13, 36, 4, True)
    stack(cv, 28, 17, 36, 3, True)
    stack(cv, 41, 9, 28, 2)
    return outline(cv)


def P_mast():
    """The mast: a crow's-nest turret on a pole, then (thin, so drawn after the outline) the yard-arm with
    its railed platform, rigging lines and a ladder."""
    cv = Canvas(CW, CH)
    i = FAM["i"]
    cv.rect(46, 7, 9, 5, i[1])                   # the nest
    cv.rect(46, 7, 3, 5, i[0])
    cv.rect(53, 7, 2, 5, i[2])
    cv.rect(48, 9, 6, 1, K2)
    cv.rect(47, 5, 7, 2, i[1])
    cv.rect(47, 5, 2, 1, i[0])
    cv.rect(45, 12, 11, 1, i[3])
    cv.rect(49, 14, 3, 12, i[2])                 # the pole
    cv.rect(51, 14, 1, 12, i[4])
    outline(cv)
    cv.rect(50, 1, 1, 3, K3)
    cv.rect(44, 18, 25, 1, K2)                   # yard-arm
    cv.rect(55, 16, 9, 1, i[1])                  # platform rail
    for x in range(55, 65, 2):
        cv.set(x, 17, i[2])
    for x, n in ((56, 8), (59, 10), (62, 10)):   # rigging
        for k in range(n):
            cv.set(x + k // 3, 19 + k, K3)
    cv.rect(65, 23, 1, 9, K3)                    # ladder
    cv.rect(67, 23, 1, 9, K3)
    for y in range(24, 32, 2):
        cv.set(66, y, K3)
    return cv


def P_roofs():
    """The buildings piled on its back, packed between the stacks and the mast: the red-roofed house and
    its lean-to, the capped tower, the long orange-roofed range, a water tank."""
    cv = Canvas(CW, CH)
    i = FAM["i"]
    cv.rect(41, 27, 9, 8, i[2])                  # tank and plating filling in behind the house
    cv.rect(41, 27, 9, 1, i[0])
    cv.rect(47, 28, 3, 7, i[3])
    cottage(cv, 35, 22, 10, 10, 8, 0, wins=[(2, 2, K), (5, 2, K), (7, 2, LIT)])
    cv.rect(44, 15, 2, 6, WHS)                   # its chimney
    cottage(cv, 44, 26, 6, 6, 3, 0, (OR, OR2, OR), [(2, 2, K)])
    cv.rect(29, 19, 5, 12, WH)                   # the little tower with a red cap
    cv.rect(32, 19, 2, 12, WHS)
    for r in range(5):
        cv.rect(28 + r, 18 - r, 7 - 2 * r if r < 3 else 1, 1, RF if r % 2 else RF3)
    cv.set(30, 22, K)
    cv.set(30, 26, K)
    slab(cv, 18, 26, 16, 5, OR, OR2)             # the orange-roofed range
    cv.rect(19, 31, 15, 12, WH)
    cv.rect(19, 31, 15, 1, WHD)
    for x in (21, 25, 29):
        cv.rect(x, 33, 1, 3, K)
    outline(cv)
    for k in range(10):                          # a derrick boom over the stern
        cv.set(17 - k, 28 - k // 2, K3)
    cv.rect(8, 24, 1, 4, K3)
    return cv


def P_rear():
    """The stern, one heavy heap: a thatched hut on stilts, a white house, a purple slate roof, a band of
    wall, a hut hung on the quarter, and the dark boiler hull bulging out below with its looping ducts."""
    cv = Canvas(CW, CH)
    i = FAM["i"]
    orb(cv, 17, 69, 12, 14, "i", seams=(.1,), dk=1)           # the quarter the fins hang from
    orb(cv, 28, 73, 16, 18, "i", seams=(-.3, .35), dk=1)
    for cx, cy, r in ((24, 71, 8), (31, 79, 7), (15, 72, 5)):  # ducts looping over it
        for a in range(0, 400, 4):
            for q in (0, 1):
                cv.set(round(cx + (r + q) * math.cos(a / 100)), round(cy + (r + q) * math.sin(a / 100)), K if q else i[1])
    cv.rect(12, 55, 21, 7, i[1])                 # a band of wall with arrow slits
    cv.rect(12, 55, 21, 1, i[0])
    cv.rect(12, 61, 21, 1, i[3])
    for x in range(14, 32, 4):
        cv.rect(x, 57, 1, 3, K)
    slab(cv, 11, 49, 21, 6, PU, PU2)
    cottage(cv, 19, 42, 12, 8, 3, 0, (OR, OR2, OR), [(2, 2, K), (5, 3, LIT), (8, 2, K)])
    for r in range(6):                           # thatch
        cv.rect(14 - r, 31 + r, 4 + 2 * r, 1, TH if r % 2 else TH2)
    cv.rect(9, 37, 12, 8, "#d3c391")
    cv.rect(9, 37, 12, 1, TH2)
    for x in (11, 15):
        cv.rect(x, 39, 1, 3, K)
    cv.rect(7, 45, 16, 1, K3)
    cv.rect(9, 46, 1, 4, K3)
    cottage(cv, 5, 64, 6, 6, 4, -1.5, wins=[(1, 2, K), (3, 2, LIT)])
    hip(cv, 25, 90)
    hip(cv, 34, 91)
    return outline(cv)


def P_dome1():
    """The upper dome with its two eye-ports and battlement collar, the gun blister beside it, and the
    patchwork under the collar: yellow tiles, a striped awning, a brick face."""
    cv = Canvas(CW, CH)
    cv.rect(30, 40, 27, 23, FAM["i"][3])         # the neck in shadow (it reaches down behind the front dome)
    orb(cv, 61, 40, 6, 6, "d", 44, seams=(0,))   # gun blister
    gun(cv, 63, 72, 39)
    cv.rect(56, 44, 11, 2, FAM["k"][2])
    cv.rect(56, 46, 11, 1, K)
    orb(cv, 43.5, 36, 13, 13, "d", 37, seams=(-.45, .15, .7), t=(.86, .62, .28, -.12))
    port(cv, 43, 28)
    port(cv, 50, 29)
    collar(cv, 29, 59, 36)
    slab(cv, 30, 41, 6, 4, "#d9bb5c", "#a08238")
    for r in range(4):                           # awning
        for n in range(9):
            cv.set(30 + n, 45 + r, WH if n % 2 else RF)
    for y in range(41, 46):                      # brick face
        for x in range(40, 57):
            cv.set(x, y, RF2 if (x + y // 2 * 2) % 4 else "#6a4a66")
    return outline(cv)


def P_dome2():
    """The big front dome: eye-ports and studded collar."""
    cv = Canvas(CW, CH)
    orb(cv, 51, 55, 12.5, 12, "d", 56, seams=(-.4, .2, .72), t=(.86, .62, .28, -.12))
    port(cv, 50, 47)
    port(cv, 57, 48)
    collar(cv, 37, 66, 55)
    return outline(cv)


def P_head():
    """The great lower hull: riveted ochre plate, the main gun in its socket, a boiler, a pipe valve, a
    cottage tucked under the collar and another hung on the bow."""
    cv = Canvas(CW, CH)
    i = FAM["i"]
    orb(cv, 47.5, 70, 19, 14.5, "h", seams=(-.55, -.1, .4), t=(.66, .26, -.16, -.52))
    for x in range(31, 64):                      # riveted strakes sweeping down toward the bow
        if x % 2:
            cv.set(x, 73 + (x - 31) // 6, FAM["h"][0])
            cv.set(x + 1, 62 + abs(x - 46) // 5, FAM["h"][4])
    cv.rect(31, 65, 6, 10, RF2)                  # boiler
    cv.rect(31, 65, 2, 10, RF)
    cv.rect(36, 65, 1, 10, "#5c2a33")
    cv.rect(30, 64, 8, 1, K3)
    cv.rect(32, 62, 4, 2, i[2])
    cv.rect(30, 70, 8, 1, K3)
    cottage(cv, 39, 64, 6, 5, 3, 0, wins=[(1, 2, K), (3, 2, LIT)])
    orb(cv, 54, 66, 5.2, 5.2, "i")               # the main gun's socket: a ringed ball with a dark bore
    for x in range(51, 58):
        cv.rect(x, 64 + (x in (51, 57)), 1, 5 - 2 * (x in (51, 57)), K)
    gun(cv, 54, 69, 64)
    cottage(cv, 57, 73, 7, 7, 4, 1.5, wins=[(1, 2, K), (4, 2, K)])
    for y in range(75, 84):                      # a duct from the boiler down to the bow
        cv.set(37 + (y - 75) // 3, y, i[1])
        cv.set(38 + (y - 75) // 3, y, i[4])
    outline(cv)
    cv.rect(66, 61, 4, 1, K3)                    # valve
    cv.rect(69, 59, 1, 5, K3)
    return cv


def P_jaw():
    """The bow under it, jutting forward: a heavy lip of lapped bands that drops open on every footfall."""
    cv = Canvas(CW, CH)
    h = FAM["h"]
    orb(cv, 52, 81, 15, 11, "h", seams=(-.5,), keep=lambda x, y: y >= 74 + (x < 50) * 3, t=(.66, .26, -.3, -.62))
    cv.rect(50, 74, 16, 3, K)                    # the dark of the mouth, hidden until the jaw drops
    for x in range(40, 67):                      # lapped lip bands sweeping down toward the bow
        y = 78 + (x - 40) // 5
        cv.set(x, y, h[0])
        cv.set(x, y + 1, h[4])
        cv.set(x, y + 5, h[1])
        cv.set(x, y + 6, h[4])
    for a in range(0, 628, 40):                  # a hub
        cv.set(round(43.5 + 2.2 * math.cos(a / 100)), round(85.5 + 2.2 * math.sin(a / 100)), FAM["i"][0 if a > 300 else 2])
    cv.rect(43, 85, 2, 2, K)
    hip(cv, 48, 90)
    hip(cv, 57, 90)
    return outline(cv)


def fin(tip):
    """A bat-wing fin at the stern: a ribbed membrane fanned from a hinge at its right, scalloped between
    the ribs; `tip` swings it (up while walking, drooped at rest)."""
    cv = Canvas(20, 34)
    a0, a1 = -.8 + tip * .12, .9 + tip * .12
    for y in range(34):
        for x in range(19):
            dx, dy = 18.5 - x, y + .5 - 15
            u = (math.atan2(dy, dx) - a0) / (a1 - a0)
            if 0 <= u <= 1 and math.hypot(dx, dy) <= 13 + 5 * abs(math.cos(3 * math.pi * u)):
                rib = min(abs(u - n / 3) for n in range(4)) < .06
                cv.set(x, y, FN3 if rib else FN if u < .45 else FN2)
    return outline(cv)


FINAT = (-6, 56)
PARTS = [("stacks", P_stacks, "--k:6;--s:2"), ("mast", P_mast, "--k:6;--s:1"), ("roofs", P_roofs, "--k:5;--s:1"),
         ("rear", P_rear, "--k:4"), ("dome1", P_dome1, "--k:3"), ("jaw", P_jaw, "--k:0;--a:2"), ("head", P_head, "--k:1"),
         ("dome2", P_dome2, "--k:2")]


# ---------------------------------------------------------------------------------------------------------
# Characters (one PNG): Heen, Sophie, Howl.
SOPHIE = [
    "......yyyyy......",
    ".....yyyyyyy.....",
    "....yyyyyyyyy....",
    "....rrrrrrrrr....",
    "..yyyyyyyyyyyyy..",
    "yyyyyyyyyyyyyyyyy",
    ".YYYYYYYYYYYYYYY.",
    "....hhhhhhhHH....",
    "....hsssssshH....",
    "....hskssksHH....",
    "....hSssssSHH....",
    "....hhssmssH.....",
    ".....hHsssHH.....",
    ".....hHwwwHh.....",
    "....BhHbwbbbB....",
    "...BBHhbbbbbBB...",
    "...BBhHbbbbbBB...",
    "...BBHhbbbbbBB...",
    "...BBhrdbbbdBB...",
    "....BBbbbbbBB....",
    "....sBbbbbbBs....",
    "....bbbbbbbbb....",
    "...bbbbBbbbbbB...",
    "...bbbbBbbbbbB...",
    "..bbbbbBbbbbbBB..",
    "..bbbbBbbbbbbBB..",
    "..bbbbBbbbbbBbB..",
    ".bbbbbBbbbbbBbBB.",
    ".bbbbBbbbbbbBbBB.",
    ".bbbbBbbbbbBBbBB.",
    "..ddddddddddddd..",
    ".....oo...oo.....",
]
HOWL = [
    "....aaaaaaa....",
    "...aaaaaaaaa...",
    "..aaaaaaaaaaA..",
    "..aaaaaaaaaAA..",
    "..aaassssaaAA..",
    "..aaskssksaAA..",
    "..aAsssssseAA..",
    "..aAAssmssAAA..",
    "...AA.sss.AA...",
    "....gwwswwg....",
    "..pPgwwwwwgPp..",
    ".pPpgwwwwwgpPp.",
    ".PpPgWwwwWgPpP.",
    ".pPpgWwwwWgpPp.",
    ".PpPgWwwwWgPpP.",
    ".pPpgwwwwwgpPp.",
    ".PpPgtttttgPpP.",
    ".pPp.ttttt.pPp.",
    ".PpP.ttttt.PpP.",
    ".pPp.ttTtt.pPp.",
    ".PpP.tt.Tt.PpP.",
    ".pPp.tt.Tt.pPp.",
    ".ggg.tt.Tt.ggg.",
    ".....tt.Tt.....",
    ".....tt.Tt.....",
    ".....tt.Tt.....",
    ".....tt.Tt.....",
    ".....tt.Tt.....",
    ".....tt.Tt.....",
    ".....tt.Tt.....",
    ".....tt.Tt.....",
    "....ooo.ooo....",
    "....ooo.ooo....",
    "...oooo.oooo...",
]
MARKL = [
    "....vvvv....",
    "...vvvvvv...",
    "..vvVssVvv..",
    "..vVskskVv..",
    "..vVsssssV..",
    "..vwwwmwwv..",
    "..vwwwwwwv..",
    ".vvwwwwwwvv.",
    ".vvhwwwwhvv.",
    ".vvvhwwhvvv.",
    ".vvvvhhvvvv.",
    ".vvVvvvvVvv.",
    ".vvVvvvvVvv.",
    "vvvVvvvvVvvv",
    "vvvVvvvvVvvv",
    "vvvvvvvvvvvv",
    ".VVVVVVVVVV.",
    "..oo....oo..",
]
WITCH = [
    "....HHHHHH......",
    "...HhhhhhhH.....",
    "...hsssssshH....",
    "...skssskssH....",
    "...sSssssSs.....",
    "...ssmmmsss.....",
    "..uussssssuu..o.",
    ".uuuuuuuuuuuu.o.",
    ".uUuuuuuuuuUu.o.",
    ".uUuuuuuuuuUu.o.",
    ".suUuuuuuuUus.o.",
    "..uuuuuuuuuuu.o.",
    "..uuuuuuuuuuuoo.",
    ".uuuuuuuuuuuuoo.",
    ".uuuuuuuuuuuuuo.",
    ".uuUuuuuuuUuuuo.",
    ".uuuuuuuuuuuuuo.",
    ".UUUUUUUUUUUUUo.",
    "..o.........o.o.",
    "..o.........o.o.",
]
HEEN = [
    "..........nnnn..",
    ".........ncccnn.",
    "........nncckcnn",
    "..nnnnccnnccccNn",
    ".cnnnnccnncccnnn",
    "cccnnccccnccccn.",
    "cccccccccccCC...",
    "cCccccccccccC...",
    ".CCccccccCCC....",
    ".C.C....C.C.....",
    ".N.N....N.N.....",
]
CPAL = {"y": "#f4d47c", "Y": "#c9a04c", "r": "#e8607a", "h": "#eef2f8", "H": "#b7c4dc", "s": "#f8d3b0",
        "S": "#f0b49c", "k": "#33304a", "m": "#c9705f", "b": "#4a78c9", "B": "#365aa6", "d": "#27437f",
        "w": "#ffffff", "o": "#5b4636", "a": "#f6dc82", "A": "#cfa64e", "e": "#3fd0c0", "g": "#f0c85a",
        "p": "#ee9bb8", "P": "#8f8fc8", "W": "#cdd6ea", "t": "#3a3550", "T": "#27243a",
        "c": "#ecd6ac", "C": "#c9a878", "n": "#8a5a3c", "N": "#5e3a2a", "v": "#3d7f6c", "V": "#2a5c52", "u": "#7a5590", "U": "#553a6b"}
CHX, CHY = 118, 118   # top-left of the character PNG; everyone's feet are on its row 35


def cast():
    """Markl, Heen, Sophie, Howl and the Witch of the Waste (the household's granny now, in her chair) on one
    canvas whose column 20 is world x = CHX."""
    cv = Canvas(114, 36)
    cv.paint(MARKL, CPAL, 1, 18)
    cv.paint(HEEN, CPAL, 20, 25)
    cv.paint(SOPHIE, CPAL, 40, 4)
    cv.paint(HOWL, CPAL, 78, 2)
    cv.paint(WITCH, CPAL, 98, 16)
    return cv


def png(cv):
    """Canvas -> base64 8-bit palette PNG, unpainted key colour transparent (index 0). One byte per
    pixel deflates smaller than 4-bit packing here, and Pillow can't write the 1-byte tRNS."""
    cols = [UNPAINTED] + sorted({p for row in cv.px for p in row if p != UNPAINTED})
    raw = b"".join(b"\0" + bytes(cols.index(p) for p in row) for row in cv.px)
    idat = min((c.compress(raw) + c.flush() for c in
                (zlib.compressobj(9, 8, wb, 9, st) for wb in (15, 12, 10, 9) for st in (0, 1))), key=len)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return base64.b64encode(
        b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 3, 0, 0, 0))
        + ch(b"PLTE", bytes(x for c in cols for x in c)) + ch(b"tRNS", b"\0") + ch(b"IDAT", idat) + ch(b"IEND", b"")).decode()


def img(cv, x, y, cls=""):
    c = f" class='{cls}'" if cls else ""
    return f"<image{c} x='{x}' y='{y}' width='{cv.w}' height='{cv.h}' href='data:image/png;base64,{png(cv)}'/>"


def art(rows, pal):
    assert len({len(r) for r in rows}) == 1, [len(r) for r in rows]
    cv = Canvas(len(rows[0]), len(rows))
    cv.paint(rows, pal, 0, 0)
    return cv


def strokes(rows, pal, x0, y0):
    """ASCII art -> one stroked path per colour, 1px runs at y+.5 with relative moves."""
    out = ""
    for ch, col in pal.items():
        d, px, py = "", 0, 0
        for dy, row in enumerate(rows):
            x = 0
            while x < len(row):
                n = 1
                while x + n < len(row) and row[x + n] == row[x]:
                    n += 1
                if row[x] == ch:
                    d += f"m{x - px} {dy - py}h{n}" if d else f"M{x0 + x} {y0 + dy}.5h{n}"
                    px, py = x + n, dy
                x += n
        if d:
            out += f"<path stroke='{col}' d='{d}'/>"
    return out


TURNIP = [
    "......kkkkkkk......",
    "......kkkkkkk......",
    "......kkkkkkk......",
    "......rrrrrrr......",
    "...kkkkkkkkkkkkk...",
    "......wwwwwww......",
    ".....wwwwwwwww.....",
    ".....wwkwwwkwwww...",
    ".....wwwwwwwwwwwww.",
    ".....wWwwmmwww.....",
    "......WWwwwww......",
    ".......WWwww.......",
    ".......rrbrr.......",
    ".ccccccccccccccccc.",
    "gcccccccccccccccccg",
    "g.cCc.ccccccc.cCc.g",
    "..c.c.ccccCcc.c.c..",
    "......cccccCc......",
    "......ccccCcc......",
    "......cccccCc......",
    ".....cccccCccc.....",
    ".....ccc.p.ccc.....",
    "....cc...p...cc....",
] + [".........p........."] * 11
TPAL = {"k": "#2a2838", "r": "#d8433f", "w": "#f6f1e6", "W": "#d3c8dc", "m": "#b0565c", "b": "#8f2a30",
        "c": "#3d4a6b", "C": "#2c3650", "g": "#e6c15a", "p": "#b08a5a"}
FIRE = [
    ".rrooorrrr.",
    ".roooooorr.",
    "rrooyyyoorr",
    "rooyyyyyoor",
    "rowwyyywwor",
    "rowkyyywkor",
    "rooyyyyyoor",
    "rrooymyoorr",
    ".rroooooor.",
    "..rrrrrrr..",
]
TIP_A = ["....r......", "...rr..r...", "...rrr.rr..", "..rrorrrr.."]
TIP_B = ["......r....", "..r..rr....", "..rr.rrr...", "..rrrrorr.."]
FLARE = [".....r.....", "....rr.....", "....rrr.r..", "..r.rrr.rr.", "..rrrorrrr.", ".rrrroorrr.", ".rrroooorr.",
         ".rroooorrr."]
FPAL = {"r": "#f4623a", "o": "#ff9d3c", "y": "#ffe066", "w": "#ffffff", "k": "#3a2030", "m": "#c2452e"}
TPAL2 = {"r": "#f4623a", "o": "#ff9d3c"}

CX0, CY = 150, 16                 # the castle canvas's top-left where it rests, by the water's edge
LEG = "v3h-1v3h1v3h1v3h4m-6 0h3"  # short, spindly bird legs: hip, hock bent back, shin, toes (stroked 2px)
leg = lambda x: f"M{CX0 + x} {CY + 92}{LEG}"
SIT = 10                          # how far the body sinks onto its folded legs


def atlas(named, pad=3):
    """Pack canvases side by side into one PNG (one palette, one deflate stream instead of one per part).
    Returns the <image> definition and {name: (x0, y0, w, h, atlas x)}: each part's padded bounding box on its
    own canvas and where that box sits in the atlas. The padding is room for the part to shift inside its
    viewport without being clipped."""
    cells, ax = {}, 0
    for name, cv in named:
        xs = [x for row in cv.px for x, p in enumerate(row) if p != UNPAINTED]
        ys = [y for y, row in enumerate(cv.px) if any(p != UNPAINTED for p in row)]
        cells[name] = (min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 1 + 2 * pad, max(ys) - min(ys) + 1 + 2 * pad, ax)
        ax += cells[name][2]
    sheet = Canvas(ax, max(c[3] for c in cells.values()))
    for name, cv in named:
        x0, y0, w, h, at = cells[name]
        for y in range(h):
            for x in range(w):
                if 0 <= x0 + x < cv.w and 0 <= y0 + y < cv.h:
                    sheet.px[y][at + x] = cv.px[y0 + y][x0 + x]
    return f"<image id='hw-a' width='{sheet.w}' height='{sheet.h}' href='data:image/png;base64,{png(sheet)}'/>", cells


SHEET, CELL = atlas([(n, f()) for n, f, _ in PARTS] + [("fin1", fin(-1)), ("fin2", fin(1))])


def part(name, style, at=None, attrs=""):
    """One part of the castle: a nested <svg> viewport onto its cell of the atlas. The <use> inside carries the
    animations, so the part moves within the viewport (no url(#id) clip needed, which T3 would reject); the
    viewport is SIT rows taller than the cell so the part can sink when the castle sits down."""
    x0, y0, w, h, ax = CELL[name]
    x, y = at or (CX0 + x0, CY + y0)
    return (f"<svg{attrs} x='{x}' y='{y}' width='{w}' height='{h + SIT}'>"
            f"<use style='{style}' href='#hw-a' x='{-ax}'/></svg>")


def puff(x, y, d=0):
    """One smoke puff: rises 2px and drifts 1px back per step, swapping small -> medium -> large shapes.
    (Written out per puff: copies stamped with <use> all run in step, whatever --d they are given.)"""
    st = f" style='--d:{d}s'" if d else ""
    return (f"<g transform='translate({x} {y})'{st}><g class='hw-s'>"
            "<path d='M-1-1h3v3h-3z'/>"
            "<path style='--e:2.4s' d='M-3-2h1v-1h4v1h1v4h-1v1h-4v-1h-1z'/>"
            "<path style='--e:1.2s' fill='#abd' d='M-4-2h1v-1h1v-1h4v1h1v1h1v4h-1v1h-1v1h-4v-1h-1v-1h-1z'/></g></g>")


SX, SY = CHX + 20, CHY + 4        # Sophie's top-left
HX, HY = CHX + 58, CHY + 2        # Howl's
FX, FY = 159, 123                 # Calcifer's (flame tips; his body starts 4 rows lower)
TX, TY = -130, 116                # Turnip Head, parked off-canvas to the left
assert TY + len(TURNIP) - 1 == TBASE
bird = lambda x, y, up: (f"M{x} {y}.5h1m3 0h1m-4 1h3" if up else f"M{x + 1} {y}.5h3m-4 1h1m3 0h1")
FLOCK = [(900, 60), (909, 64), (917, 58), (926, 65), (934, 61)]

SPRITES = (
    # clouds, a flock of birds, lake glints
    # the cumulus billow: two sets of 1px caps on their lit tops and left flanks swell out and sink back on long,
    # unequal periods (each cap sits just outside a flat run of the cloud's edge in the PNG)
    "<path class='hw-o' style='--t:13s' fill='#fff' d='M150 9h4v1h-4zM163 15h6v1h-6zM93 52h1v3h-1zM280 17h4v1h-4zM18 39h4v1h-4z'/>"
    "<path class='hw-o' style='--t:19s;--d:-7s' fill='#fff' d='M135 14h6v1h-6zM189 28h6v1h-6zM273 24h1v4h-1zM274 37h1v5h-1zM305 35h6v1h-6z'/>"
    # three small clouds drifting across, one after another
    "<path class='hw-d' fill='#fff' d='M-80 20h34v-1h-6v-1h-5v-1h-7v-1h-8v1h-4v1h-4zm-560 9h24v-1h-5v-1h-5v-1h-7v1h-4v1h-3zm280-5h20v-1h-3v-2h-4v-1h-6v1h-4v2h-3z'/>"
    f"<g class='hw-v' stroke='#346'><path class='hw-o' style='--t:.6s' d='{''.join(bird(x, y, 1) for x, y in FLOCK)}'/>"
    f"<path class='hw-o' style='--t:.6s;--d:-.3s' d='{''.join(bird(x, y, 0) for x, y in FLOCK)}'/></g>"
    "<path class='hw-g' stroke='#fff' d='M96 101.5h8m90 6h10m72 5h7m-262-9h7'/>"
    "<path class='hw-g' style='--d:-2.5s' stroke='#fff' d='M40 109.5h9m180-7h8m44 13h8m-150-12h6'/>"
    # the castle: its shadow, the atlas, the smoke (which sinks with the stacks), then the parts back to front
    # with the legs and fins slipped in behind the stern, and last the eyelids that half-close its eye-ports
    # while it rests. --k is a part's place in the ripple, bow (0) to stacks; --a how far it dips on a footfall,
    # --s how far it sways back. The legs stay on the ground, so when the parts sink the hull settles over them
    # and only the feet stick out. Each fin is a drooped frame with a raised frame flickering over it.
    f"<g class='hw-go'><path fill='#6b5' d='M{CX0 + 8} 120h58v1h3v1h-64v-1h3z'/><defs>{SHEET}</defs>"
    f"<g class='hw-k' style='--k:6;--a:0'>{puff(CX0 + 33, CY + 3)}{puff(CX0 + 22, CY + 12, -1.8)}</g>"
    + "".join(
        (f"<path class='hw-l' d='{leg(26)}{leg(49)}'/><path class='hw-l hw-m' d='{leg(35)}{leg(58)}'/>"
         + "".join(part(f, "--k:4;--a:0", (CX0 + FINAT[0] + dx + CELL[f][0], CY + FINAT[1] + dy + CELL[f][1]), a)
                   for f, a, dx, dy in (("fin2", "", 4, 12), ("fin2", "", 0, 0), ("fin1", " class='hw-f'", 0, 0)))
         if n == "rear" else "") + part(n, st)
        for n, _, st in PARTS)
    + "".join(f"<g class='hw-k' style='--k:{k};opacity:calc(1 - var(--w))'><path fill='{FAM['d'][2]}' "
              f"d='M{CX0 + x + 1} {CY + y + 1}h3v2h-3zm7 1h3v2h-3z'/></g>" for k, x, y in ((3, 43, 28), (2, 50, 47)))
    + "</g>"
    # Turnip Head hops through behind the others
    f"<g class='hw-t'><g class='hw-j'>{img(art(TURNIP, TPAL), TX, TY)}</g></g>"
    # the tall flowers are rooted nearer than Turnip Head: their heads are sprites further down, and the part of
    # each PNG stem that his pole can reach is redrawn here so it stays in front of him too
    + f"<path fill='{G3}' d='{''.join(f'M{x} {y + 2}h1v{TBASE - y - 1}h-1z' for x, y in WIND if y + 2 <= TBASE)}'/>"
      f"<path fill='{G2}' d='{''.join(f'M{x + 1} {y + 4}h1v1h-1z' for x, y in WIND if y + 4 <= TBASE)}'/>"
    # Heen, Sophie and Howl, then their idle life: ribbon, hem, hair, jacket, tail, blinks
    + img(cast(), CHX - 20, CHY)
    + f"<path class='hw-z' style='--t:5.7s;--d:-3s' stroke='#f8d3b0' d='M{CHX - 15} {CHY + 21}.5h1m1 0h1'/>"   # Markl blinks
    + f"<path stroke='#f8d3b0' d='M{CHX + 82} {CHY + 19}.5h1m3 0h1'/>"   # the Witch dozes, eyes shut
    # the household greets the castle as it arrives and sits, and sees it off when it stands (the hw-r windows):
    # Sophie waves (a sleeve, then two hand frames), Markl throws his arms up, the Witch opens her eyes
    + f"<g class='hw-r'><path fill='#365aa6' d='M{SX + 12} {SY + 20}h1v1h-1zm1-7h1v1h-1z'/>"
      f"<path class='hw-o' style='--t:.6s' fill='#f8d3b0' d='M{SX + 14} {SY + 11}h1v2h-1zm1-2h1v2h-1z'/>"
      f"<path class='hw-o' style='--t:.6s;--d:-.3s' fill='#f8d3b0' d='M{SX + 14} {SY + 9}h1v4h-1z'/>"
      f"<path fill='#3d7f6c' d='M{CHX - 20} {CHY + 22}h1v3h-1zm13 0h1v3h-1z'/>"
      f"<path fill='#f8d3b0' d='M{CHX - 20} {CHY + 20}h1v2h-1zm13 0h1v2h-1z'/>"
      f"<path stroke='#33304a' d='M{CHX + 82} {CHY + 19}.5h1m3 0h1'/></g>"
    + f"<path class='hw-o' style='--t:.8s' stroke='#e8607a' d='M{SX + 13} {SY + 3}.5h4'/>"
      f"<path class='hw-o' style='--t:.8s;--d:-.4s' stroke='#e8607a' d='M{SX + 13} {SY + 3}.5h2m0-1h2'/>"
      f"<path class='hw-o' style='--t:1.4s' fill='#365aa6' d='M{SX + 16} {SY + 27}h1v3h-1z'/>"
      f"<path class='hw-o' style='--t:1.1s;--d:-.3s' fill='#cfa64e' d='M{HX + 13} {HY + 6}h1v3h-1z'/>"
      f"<path class='hw-o' style='--t:1.6s;--d:-.7s' fill='#ee9bb8' d='M{HX + 14} {HY + 18}h1v4h-1z'/>"
      f"<path class='hw-o' style='--t:.5s' fill='#ecd6ac' d='M{CHX - 1} {CHY + 29}h1v2h-1z'/>"
      f"<path class='hw-o' style='--t:.5s;--d:-.25s' fill='#ecd6ac' d='M{CHX - 1} {CHY + 31}h1v2h-1z'/>"
      f"<path class='hw-z' style='--t:3.7s' fill='#8a5a3c' d='M{CHX + 8} {CHY + 30}h1v1h1v1h-1v-1h-1z'/>"   # ear twitch
      f"<path class='hw-z' stroke='#f8d3b0' d='M{SX + 6} {SY + 9}.5h1m2 0h1'/>"
      f"<path class='hw-z' style='--t:6.3s;--d:-2s' stroke='#f8d3b0' d='M{HX + 5} {HY + 5}.5h1m2 0h1'/>"
      f"<path class='hw-z' style='--t:4.1s;--d:-1s' stroke='#ecd6ac' d='M{CHX + 12} {CHY + 27}.5h1'/>"
    # Calcifer: glow, body, two flame-tip frames, and a flare-up now and then
    + f"<g class='hw-c'>{img(art(FIRE, FPAL), FX, FY + 4)}"
      f"<g class='hw-o' style='--t:.5s'>{strokes(TIP_A, TPAL2, FX, FY)}</g>"
      f"<g class='hw-o' style='--t:.5s;--d:-.25s'>{strokes(TIP_B, TPAL2, FX, FY)}</g>"
      f"<g class='hw-r'>{strokes(FLARE, TPAL2, FX, FY - 4)}</g></g>"
    # tall flowers nodding in the wind: per colour, one path of petals and one of centres. (No markers,
    # gradients or anything else that needs url(#id): T3's theme validator rejects those.)
    + "".join(
        f"<g class='hw-w' style='--t:{t}s;--d:-{i}s'>"
        f"<path fill='{c}' d='{''.join(f'M{x - 1} {y - 2}h2v1h1v2h-1v1h-2v-1h-1v-2h1z' for x, y in WIND[i * 3:i * 3 + 3])}'/>"
        f"<path fill='{m}' d='{''.join(f'M{x - 1} {y - 1}h2v2h-2z' for x, y in WIND[i * 3:i * 3 + 3])}'/></g>"
        for i, (c, m, t) in enumerate([('#fff', '#fd5', 2.6), ('#f7a8c8', '#fff', 3.4), ('#fd5', '#f64', 3)]))
)
CSS = (
    # generic: hw-o two-frame toggle, hw-z brief flash (6% of its period), both steered by --t / --d
    ".hw-o{animation:hw-o var(--t,1s) steps(1) var(--d,0s) infinite}@keyframes hw-o{50%{opacity:0}}"
    ".hw-z{opacity:0;animation:hw-z var(--t,5s) steps(1) var(--d,0s) infinite}@keyframes hw-z{94%{opacity:1}}"
    ".hw-g{animation:hw-o 5s steps(4) var(--d,0s) infinite}"
    # The castle's three-minute loop, in % of 180s: it strides in from the left (0-20%: 60 footfalls of 4px, one
    # every 0.6s), stops by the water's edge, sits (20-22%), rests (to 62%), stands (62-64%), and from 65% ambles
    # off to the right at half the pace (90 footfalls of 2px); from 70%, when its leading foot reaches the brow of
    # the hill, hw-h adds 1px of descent every third footfall, so that foot follows the 1-in-6 slope down and out
    # of the frame (the feet behind it land a little lower on the hillside, never above the crest).
    # --w is 1 while it walks and 0 while it sits: it scales the legs' steps, the ripple and the fins' flapping,
    # and opens or half-closes the eyelids; --q halves the legs' reach for the slow walk off.
    # The whole loop is started 45s in, so the theme opens on the castle already resting by the lake.
    ".hw-go{--w:1;--q:1;animation:hw-go 180s steps(1) -45s infinite,hw-y 180s steps(1) -45s infinite,"
    "hw-h 180s steps(1) -45s infinite;animation-composition:add}"
    "@keyframes hw-go{from{translate:-240px;animation-timing-function:steps(60)}20%{translate:none}"
    "65%{translate:none;animation-timing-function:steps(90)}95%,to{translate:180px}}"
    "@keyframes hw-y{20%{--w:0}65%{--w:1;--q:.5}to{--w:1;--q:1}}"
    "@keyframes hw-h{70%{translate:0 0;animation-timing-function:steps(25)}95%,to{translate:0 25px}}"
    f".hw-l{{fill:none;stroke:{K};stroke-width:2;animation:hw-l 1.2s steps(1) infinite}}.hw-m{{animation-delay:-.6s}}"
    "@keyframes hw-l{from{translate:calc(var(--w)*var(--q)*2px) calc(var(--w)*-3px)}"
    "25%{translate:calc(var(--w)*var(--q)*4px) calc(var(--w)*-1px)}50%,to{translate:none}}"
    # every part runs two animations that add up: the ripple on each footfall (dip, settle, rise, each part a
    # beat after the one in front) and the sit, which lowers it SIT px in five steps, lets it breathe 1px up
    # and down while it rests, and raises it again, likewise bow first
    ".hw-k,svg svg use{animation:hw-k .6s steps(1) calc(var(--k)*.07s - .6s) infinite,hw-n 180s steps(1) calc(var(--k)*.15s - 45s) infinite;"
    "animation-composition:add}"
    "@keyframes hw-k{from{translate:calc(var(--s,0)*var(--w)*-1px) calc(var(--a,1)*var(--w)*1px)}30%{translate:none}"
    "65%{translate:0 calc(var(--w)*-1px)}}"
    f"@keyframes hw-n{{20%{{translate:0 0;animation-timing-function:steps(5)}}22%,34%,46%,58%{{translate:0 {SIT}px}}"
    f"28%,40%,52%{{translate:0 {SIT - 1}px}}62%{{translate:0 {SIT}px;animation-timing-function:steps(5)}}64%,to{{translate:0 0}}}}"
    ".hw-f{animation:hw-f .6s steps(1) infinite}@keyframes hw-f{from{opacity:var(--w)}50%,to{opacity:0}}"
    ".hw-s{fill:#667;animation:hw-s 3.6s steps(4) var(--d,0s) infinite}@keyframes hw-s{to{translate:-4px -8px}}"
    ".hw-s path{animation:hw-p 3.6s steps(1) calc(var(--d,0s) - var(--e,0s)) infinite}@keyframes hw-p{33.3%,to{opacity:0}}"
    # moments
    ".hw-t{animation:hw-t 80s steps(1120) infinite}.hw-d{animation:hw-t 320s steps(1120) infinite}@keyframes hw-t{to{translate:1120px}}"
    ".hw-j{animation:hw-j .5s steps(3) infinite alternate}@keyframes hw-j{to{translate:0 -6px}}"
    ".hw-v{animation:hw-v 67s steps(670) infinite}@keyframes hw-v{to{translate:-1340px -40px}}"
    ".hw-c{animation:hw-c 1.6s steps(1) infinite}@keyframes hw-c{25%{translate:1px -1px}50%{translate:0 -3px}75%{translate:-1px -1px}}"
    ".hw-r{opacity:0;animation:hw-r 180s steps(1) -45s infinite}@keyframes hw-r{18%,62.5%{opacity:1}23%,68%{opacity:0}}"
    ".hw-w{animation:hw-w var(--t) steps(1) var(--d) infinite}@keyframes hw-w{50%{translate:1px}}"
)
THEME = {"position": "center 50%",  # wide panes crop vertically; see build wide.png
         "canvas": "#10203a", "accent": "#ffb454", "overlay": "#0e1c33",
         "colors": {"sidebar": "#0d1a30", "sidebarRowSelected": "#1c3559", "sidebarBorder": "#1f3a61",
                    "surface": "#162a4a", "border": "#27446e", "text": "#eef4fb", "textMuted": "#a8bbd6"}}
