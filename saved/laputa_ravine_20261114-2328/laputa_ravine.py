"""Castle in the Sky, second view: Slag Ravine from high on its rim, a day and a night.

We stand above Pazu's house and look down the length of the ravine. Its walls run away to a vanishing
point on the horizon, terraced with brick houses; the railway trestle crosses between two tunnel mouths,
the mine headframe stands on the right-hand ledge with Uncle Pom's mine mouth below it, and the depths
are lost in haze. Straight ahead, over the far end of the ravine, Laputa floats in the clouds.

Layers, back to front (320x180):
  draw()      the base PNG: sky, cloud bank, far hills with Fortress Tedis, and the whole ravine
              (floor haze, both walls, plateaus, houses, trestle, headframe, Pom at his mine)
  sky         the Goliath, Laputa (bobbing) with a wisp of cloud across it, a drifting cloud, the Tiger Moth
  ravine      chimney smoke, the train with Dola's sons' car on its tail (in a nested viewport as wide
              as the trestle, so the tunnel mouths swallow it), the turning mine wheel, Pazu's pigeons
  near        the rim we stand on with Pazu's roof, chimney and dovecote; Pazu and his trumpet
  light       night (one multiply wash), the warm wash of dusk and dawn, then everything the night does
              not dim: stars, lit windows, Pom's lantern, the crystal veins, Sheeta drifting down

One 240 s cycle (1% = 2.4 s). The loop point is just after sunrise, so the theme opens on a bright morning:
   0-  8%  sunrise: the last of the warm wash fades (0-2.5%); Pazu plays his trumpet (1-7%) and the
           pigeons sweep out from behind the roof (1.5-8%)
   6- 44%  day: the mine wheel turns (6-44%), the Tiger Moth crosses (8-42%), the train comes over the
           trestle with the pirates' car behind it (16-27%), the pigeons come home (29-35.5%)
  44- 51%  dusk: the Goliath comes over (44-84%), the warm wash peaks at 48%, night steps in 45-51%
           and the windows light with it
  51- 94%  night: Sheeta drifts down past us into the ravine (62-84%); the crystal veins in the walls
           wake as she passes and Laputa's core answers
  94-100%  dawn: night steps out (94.5-99.5%) under the warm wash, which peaks at 98%

Motion is CSS transform/opacity only, in whole-pixel steps(). Every moment is parked (off-canvas, behind
a wall, or at opacity 0) and its keyframes hold outside its slot, so nothing is redrawn for it then.
"""
import base64, math, random, struct, zlib
from lib import Canvas, UNPAINTED, hx

NAME = "Castle in the Sky: Slag Ravine"
SIZE = W, H = 320, 180
COLORS = 128         # more than the base layer uses, so its colours stay exact


def mix(a, b, t):
    a, b = hx(a), hx(b)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


S = ["#2f5fb0", "#4079c6", "#5a95d6", "#7db2e2", "#a5cdee", "#cbe3f5"]              # sky top -> horizon
C = ["#fffaf0", "#eee8ea", "#d0d4ea", "#b2bade"]                                     # cumulus
HILL, FORT = "#9db3dc", "#6e80ba"
FL = ["#dce9f5", "#c3d6ee", "#a6bde2", "#869fd2"]                                    # haze in the depths
WALL = {-1: ["#bdb9d2", "#c8ab94", "#b98b64", "#a06e48"],                            # lit wall, far -> near
        1: ["#a8abd0", "#9c8fa6", "#86687e", "#6c4c60"]}                             # shaded wall
LEDGE = {-1: ["#cbd2dc", "#d6c9a2", "#cfb07e", "#bd965f"], 1: ["#b8c0da", "#b6a9b6", "#a08490", "#866672"]}
DEPTH = {sd: [[mix(c, "#56609c", d) for c in WALL[sd]] for d in (0, .22, .42)] for sd in (-1, 1)}
TOP = ["#bcd0a8", "#a6c484", "#8ab85c", "#74a84a"]                                   # plateau grass, far -> near
ROOF, ROOF_D, PLASTER, PLASTER_D = "#c8644c", "#9a4a42", "#eedfc4", "#b9a9aa"
ST = ["#f6ecd0", "#dccdaa", "#b0a29c", "#807a98", "#514c70", "#353150", "#23213a"]   # Laputa's stone
GR = ["#c4e070", "#8cc458", "#56984f", "#2f6c50", "#1e4b47"]                         # leaves
WD = ["#8a6450", "#5e4640"]                                                          # wood
SK = ["#f8cfa0", "#d8996c"]
INK, GOLD = "#2a2438", "#ffd75e"
HZ = 80                              # the horizon row
VP = (166, HZ)                       # where the ravine vanishes
AL, BL = (-196, 48), (-50, 135)      # left wall: from VP along its rim, and along its foot, to depth 1
AR, BR = (184, 42), (52, 135)        # right wall


# ------------------------------------------------------------------ helpers
def png(cv):
    """A Canvas (magenta = transparent) as a base64 palette PNG, hand-encoded so the bit depth and the
    deflate strategy can be whichever comes out smallest."""
    cols = sorted({p for row in cv.px for p in row})
    trans = UNPAINTED in cols
    if trans:
        cols.remove(UNPAINTED)
        cols.insert(0, UNPAINTED)
    idx = {c: i for i, c in enumerate(cols)}
    n = len(cols)
    best = None
    for bits in {1 if n <= 2 else 2 if n <= 4 else 4 if n <= 16 else 8, 8}:
        raw = bytearray()
        for row in cv.px:
            raw.append(0)
            v = [idx[p] for p in row]
            if bits == 8:
                raw += bytes(v)
            else:
                per = 8 // bits
                v += [0] * (-len(v) % per)
                for i in range(0, len(v), per):
                    b = 0
                    for k in v[i:i + per]:
                        b = b << bits | k
                    raw.append(b)
        for strat in (0, 1, 2, 3):
            co = zlib.compressobj(9, zlib.DEFLATED, 15, 9, strat)
            z = co.compress(bytes(raw)) + co.flush()
            if best is None or len(z) < len(best[1]):
                best = (bits, z)
    bits, z = best
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, bits, 3, 0, 0, 0))
            + chunk(b"PLTE", bytes(v for c in cols for v in c)) + (chunk(b"tRNS", b"\0") if trans else b"")
            + chunk(b"IDAT", z) + chunk(b"IEND", b""))
    return base64.b64encode(data).decode()


def img(cv, x, y, attrs=""):
    return f"<image{attrs} x='{x}' y='{y}' width='{cv.w}' height='{cv.h}' href='data:image/png;base64,{png(cv)}'/>"


def art(rows, pal):
    """ASCII rows (ragged right is fine) -> Canvas."""
    cv = Canvas(max(map(len, rows)), len(rows))
    cv.paint(rows, pal, 0, 0)
    return cv


def bands(cv, y, rows):
    """rows: [(y_end, colour)]. Flat bands with a 3-row ordered-dither seam (25/50/75%)."""
    prev = None
    for y1, c in rows:
        for yy in range(y, y1):
            k = yy - y
            for x in range(cv.w):
                mix_ = prev and ((k == 0 and (x % 4 != (yy % 2) * 2)) or (k == 1 and (x + yy) % 2)
                                 or (k == 2 and x % 4 == (yy % 2) * 2))
                cv.set(x, yy, prev if mix_ else c)
        prev, y = c, y1


def blur(a, r):
    """Box blur of a 2D float list, radius r, twice (close enough to a gaussian)."""
    h, w = len(a), len(a[0])
    for _ in range(2):
        for axis in (0, 1):
            b = [[0.0] * w for _ in range(h)]
            for y in range(h):
                for x in range(w):
                    s = n = 0
                    for k in range(-r, r + 1):
                        xx, yy = (x + k, y) if axis == 0 else (x, y + k)
                        if 0 <= xx < w and 0 <= yy < h:
                            s += a[yy][xx]
                            n += 1
                    b[y][x] = s / n
            a = b
    return a


def puffs(lumps, seed, n=3, lo=.3, hi=.5):
    """Add small lumps round the upper rim of each big one so the silhouette goes cauliflower."""
    r = random.Random(seed)
    out = list(lumps)
    for cx, cy, rad in lumps:
        for _ in range(n):
            a = math.radians(r.uniform(-175, -5))
            q = rad * r.uniform(lo, hi)
            out.append((cx + math.cos(a) * rad * .85, cy + math.sin(a) * rad * .85, q))
    return out


SUN = (-.45, -.60, .66)
LEAF = (-.52, -.66, .54)
CUTS = (.45, .30, .12, -.05)


def volume(cv, lumps, tones, cuts, soft=4, sharp=.6, sink=.25, base=None, light=SUN):
    """Painterly lumpy volume (cumulus, tree crown): a union of spheres lit by a mix of its own normal
    and that of a blurred copy, darkened towards the bottom by `sink`, cut into flat tones. Sky pockets
    enclosed by lumps are filled. Rows from `base` down are not painted."""
    w, h = cv.w, cv.h
    hg = [[0.0] * w for _ in range(h)]
    for cx, cy, r in lumps:
        for y in range(max(0, int(cy - r) - 1), min(h, int(cy + r) + 2)):
            for x in range(max(0, int(cx - r) - 1), min(w, int(cx + r) + 2)):
                d2 = (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2
                if d2 < r * r:
                    hg[y][x] = max(hg[y][x], math.sqrt(r * r - d2))
    open_sky = set()
    todo = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while todo:
        x, y = todo.pop()
        if 0 <= x < w and 0 <= y < h and hg[y][x] == 0 and (x, y) not in open_sky:
            open_sky.add((x, y))
            todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    for y in range(h):
        for x in range(w):
            if hg[y][x] == 0 and (x, y) not in open_sky:
                hg[y][x] = .5
    ys = [y for y in range(h) if any(hg[y])]
    top, bot = ys[0], ys[-1]
    hb = blur(hg, soft)

    def lum(a, x, y):
        gx = a[y][min(w - 1, x + 1)] - a[y][max(0, x - 1)]
        gy = a[min(h - 1, y + 1)][x] - a[max(0, y - 1)][x]
        nx, ny, nz = -gx / 2, -gy / 2, 1
        return (nx * light[0] + ny * light[1] + nz * light[2]) / math.sqrt(nx * nx + ny * ny + nz * nz)

    for y in range(h if base is None else min(h, base)):
        for x in range(w):
            if hg[y][x] > 0:
                i = (1 - sharp) * lum(hb, x, y) + sharp * lum(hg, x, y) - sink * (y - top) / max(1, bot - top)
                cv.set(x, y, tones[min(sum(i < c for c in cuts), len(tones) - 1)])


def cloud(lumps, w, h, tones, seed, base=None):
    cv = Canvas(w, h)
    volume(cv, puffs(lumps, seed), tones, CUTS[:len(tones) - 1], soft=3, base=base)
    return cv


# ------------------------------------------------------------------ the ravine, in one-point perspective
def at(side, s, f):
    """Screen point on a wall: depth s (0 at the vanishing point, 1 nearest), and f from the rim (0)
    down to the foot (1). Negative f is up on the plateau behind the rim."""
    a, b = (AL, BL) if side < 0 else (AR, BR)
    return VP[0] + s * ((1 - f) * a[0] + f * b[0]), VP[1] + s * ((1 - f) * a[1] + f * b[1])


def wall_coords(x, y, a, b):
    """Inverse of at(): (alpha, beta) with the pixel = VP + alpha*a + beta*b."""
    dx, dy = x + .5 - VP[0], y + .5 - VP[1]
    det = a[0] * b[1] - a[1] * b[0]
    return (dx * b[1] - dy * b[0]) / det, (a[0] * dy - a[1] * dx) / det


SPURS = (.24, .44, .68)              # depths at which a nearer spur of rock overlaps the one behind


def rnd(i):
    return (i * 2654435761 % 2 ** 32) / 2 ** 32


def face(side, s, f):
    """A cliff face: four depth bands that lean, so each ends in a slanted spur with a lit lip and a
    shadow on the band behind; two ledges; gullies running down the slope. The lower a face goes the
    deeper it sinks into the blue shade of the ravine. Beyond the first spur it is all haze."""
    se = s - .1 * f
    k = sum(se > e for e in SPURS)
    lv = 0 if f < .36 else 1 if f < .68 else 2
    if k == 0:
        return DEPTH[side][lv][0]
    if .30 <= f < .36 or .62 <= f < .68 or min(se - e for e in SPURS if se > e) < .01:
        return LEDGE[side][k]
    if min([e - se for e in SPURS if se <= e] or [1]) < .028 or .36 <= f < .40 or .68 <= f < .72:
        return DEPTH[side][lv][min(3, k + 1)]            # shadow of the next spur, or under a ledge
    g = int(s * 110)
    if rnd(g) < .22 and rnd(g + 500) * .8 < f < rnd(g + 500) * .8 + .2 + .3 * rnd(g + 900):
        return DEPTH[side][lv][min(3, k + 1)]            # a gully
    return DEPTH[side][lv][k]


def house(cv, wins, side, s, f):
    """A house seen from above: mostly roof, a strip of wall below it. Its windows are remembered for the night."""
    px, py = at(side, s, f)
    w, rh, wh = int(5 + 13 * s), int(2 + 5 * s), int(2 + 4 * s)
    x0, y0 = int(px - w / 2), int(py) - wh
    haze = .4 if s < .42 else 0
    lit = side < 0
    tint = lambda c: mix(c, FL[1], haze)
    cv.rect(x0, y0, w, wh, tint(PLASTER if lit else PLASTER_D))
    cv.rect(x0 + w - 1, y0, 1, wh, tint(PLASTER_D if lit else "#93868f"))
    for x in range(x0 + 1, x0 + w - 1, 3):
        cv.rect(x, y0 + (wh > 3), 1, 1 + (wh > 4), tint("#4a4468"))
        if 0 <= x < W:
            wins.append((x, y0 + (wh > 3)))
    cv.rect(x0 - 1, y0 - rh, w + 2, rh, tint(ROOF if lit else ROOF_D))
    cv.rect(x0 - 1, y0 - rh, w + 2, 1, tint("#e08a66" if lit else ROOF))
    if rh > 3:
        cv.rect(x0 - 1, y0 - rh + 2, w + 2, 1, tint(ROOF_D if lit else "#7a3c3c"))
    if s > .4:
        cv.rect(x0 + w - 4, y0 - rh - 2, 2, 2, tint("#8a5a4c"))
    return x0 + w - 4, y0 - rh - 2          # the chimney top


TEDIS = [                   # Fortress Tedis: the great round keep, corner towers, a battlemented wall
    "...............ttttt",
    "..............ttttttt",
    "..............ttttttt",
    "....tt........ttttttt........tt",
    "...tttt.......ttttttt.......tttt",
    "...tttt..t.t.ttttttttt.t.t..tttt",
    "...ttttttttttttttttttttttttttttt",
    "...ttttttttttttttttttttttttttttt",
    "..ttttttttttttttttttttttttttttttt",
    ".ttttttttttttttttttttttttttttttttt",
    "tttttttttttttttttttttttttttttttttttt",
]
POM = [
    "...hhh",
    "..hhhhh",
    ".hhhhhhh",
    "...sss",
    "..wsssw",
    "..wwwww",
    ".cwwwwwc",
    "Lccwwwcc",
    "Lccccccc",
    "Lccccccc",
    "..cc.cc",
    "..kk.kk",
]
PPAL = {"h": WD[1], "s": SK[0], "w": "#f4f1ea", "c": "#6f7f6a", "L": GOLD, "k": INK}
WX, WY = 250, 99                    # the mine wheel's hub
TY = 110                             # the trestle's rail row
MX, MY = 231, 130                    # Uncle Pom's mine mouth


def ravine(cv):
    """Everything below the horizon. Returns the window positions and the chimney tops."""
    wins = []
    bands(cv, HZ, [(96, FL[0]), (116, FL[1]), (140, FL[2]), (H, FL[3])])
    for y in range(HZ + 8, H):                            # a thread of river far below
        x = VP[0] + round(5 * math.sin((y - HZ) * .1))
        cv.rect(x, y, 1 + (y - HZ) // 34, 1, "#f2f8fd")
    for y in range(HZ, H):
        for x in range(W):
            for side, a, b in ((-1, AL, BL), (1, AR, BR)):
                al, be = wall_coords(x, y, a, b)
                rim = .02 * math.sin(al * 31) + .012 * math.sin(al * 83 + side)     # the rim wanders
                if al > 0 and be >= rim:
                    cv.set(x, y, face(side, al + be, max(0, be) / (al + be)))
                elif al > 0 and (x + .5 - VP[0]) * side > 0:            # up on the plateau
                    cv.set(x, y, LEDGE[side][sum(al > e for e in SPURS)] if be > rim - .03 else
                           TOP[sum(y - HZ > e for e in (4, 12, 26))])
    for side, s, f, r in [(-1, .34, -.5, 2), (-1, .46, -.22, 2), (-1, .56, -.55, 3), (-1, .66, -.2, 3), (-1, .45, -.75, 2),
                          (1, .34, -.45, 2), (1, .46, -.2, 2), (1, .58, -.5, 3), (1, .7, -.14, 3), (1, .46, -.8, 2),
                          (-1, .24, -.3, 1), (1, .22, -.3, 1), (-1, .7, -.42, 3), (1, .6, -.22, 3)]:
        px, py = at(side, s, f)                           # trees up on the plateau
        for yy in range(r + 1):                         # a little dome, lit on top
            for xx in range(-min(r, yy + 1), min(r, yy + 1) + 1):
                cv.set(int(px) + xx, int(py) - r + yy, mix("#4f9a4c" if yy < r else "#2f6c50", FL[1], .35 if s < .4 else .1))
    # the trestle: rails, deck, bents and ties fading into the haze; a tunnel mouth at each end
    for x in range(102, 229):
        cv.set(x, TY, "#e2d2b0")
        cv.rect(x, TY + 1, 1, 2, WD[1])
        if (x - 104) % 9 == 0:
            for y in range(TY + 3, 150):
                cv.set(x, y, mix(WD[1], FL[2], (0, .3, .55, .8)[min(3, (y - TY - 3) // 9)]))
    for y in (TY + 8, TY + 16, TY + 24):
        for x in range(104, 228):
            if (x - 104) % 9:
                cv.set(x, y, mix(WD[1], FL[2], (.3, .55, .8)[(y - TY - 8) // 8]))
    for x0 in (95, 229):
        side = 1 if x0 > 160 else -1
        cv.rect(x0, TY - 7, 7, 10, "#3a3550")
        cv.rect(x0 + 1, TY - 8, 5, 1, "#3a3550")
        cv.rect(x0 - 1, TY - 8, 1, 11, LEDGE[side][2])
        cv.rect(x0 + 7, TY - 8, 1, 11, LEDGE[side][2])
        cv.rect(x0, TY - 9, 7, 1, LEDGE[side][2])
    # houses stepping down both sides
    town = [(-1, .22, -.2), (-1, .26, -.36), (-1, .30, -.14), (-1, .34, -.24), (-1, .36, -.5), (-1, .40, -.30),
            (-1, .44, -.12), (-1, .50, -.13), (-1, .52, -.42), (-1, .58, -.14), (-1, .62, -.30), (-1, .66, -.52),
            (-1, .70, -.12), (-1, .58, .34), (-1, .76, .34), (-1, .52, .66), (-1, .72, .66),
            (1, .22, -.2), (1, .28, -.14), (1, .32, -.3), (1, .36, -.5), (1, .40, -.32), (1, .45, -.14), (1, .50, -.13),
            (1, .54, -.44), (1, .60, -.13), (1, .66, -.28), (1, .72, -.42), (1, .34, .34), (1, .76, .34), (1, .44, .66)]
    tops = {h[:2]: house(cv, wins, *h) for h in sorted(town, key=lambda h: h[1])}
    cv.rect(277, 77, 3, 17, "#a8645a")                    # the mine's brick stack
    cv.rect(279, 77, 1, 17, "#7c4c50")
    cv.rect(276, 76, 5, 1, "#7c4c50")
    # the mine headframe: a braced timber tower with the winding wheel on top, and its engine shed
    for i in range(22):
        y = WY + 1 + i
        e = 2 + i * 7 // 21
        cv.set(WX - e, y, WD[0])
        cv.set(WX + e, y, WD[1])
        if i % 7 == 6:
            cv.rect(WX - e, y, 2 * e + 1, 1, WD[1])
        elif i > 1:
            j = (i % 7) * (2 * e - 1) // 6
            cv.set(WX - e + 1 + j, y, WD[1])
            cv.set(WX + e - 1 - j, y, WD[0])
    for a in range(0, 360, 6):                            # the rim of the wheel
        cv.set(WX + round(5 * math.cos(math.radians(a))), WY + round(5 * math.sin(math.radians(a))), INK)
    cv.rect(WX + 10, WY + 15, 12, 8, "#93868f")
    cv.rect(WX + 9, WY + 11, 14, 4, ROOF_D)
    cv.rect(WX + 9, WY + 11, 14, 1, ROOF)
    for i in range(9):
        cv.set(WX + 5 + i, WY + 3 + i, INK)                # the winding cable down to the shed
    # Uncle Pom at his mine mouth, lantern in hand
    cv.rect(MX, MY, 11, 12, "#3a3550")
    cv.rect(MX + 1, MY - 1, 9, 1, "#3a3550")
    cv.rect(MX - 1, MY - 1, 1, 13, WD[0])
    cv.rect(MX + 11, MY - 1, 1, 13, WD[1])
    cv.rect(MX - 1, MY - 2, 13, 1, WD[0])
    cv.paint(POM, PPAL, MX - 10, MY)
    return wins, tops


def base():
    cv = Canvas(W, H)
    bands(cv, 0, [(14, S[0]), (30, S[1]), (46, S[2]), (60, S[3]), (72, S[4]), (HZ, S[5])])
    volume(cv, puffs([(66, 68, 10), (82, 60, 9), (98, 66, 11), (114, 58, 8), (124, 70, 10), (50, 74, 9), (30, 76, 8),
                      (208, 64, 9), (222, 56, 10), (238, 62, 11), (254, 68, 10), (270, 74, 9), (290, 76, 8),
                      (140, 76, 7), (194, 76, 7), (8, 78, 7), (312, 78, 7)], 11),
           C, CUTS[:3], soft=4, sink=.3, base=HZ)
    for x in range(W):                                    # far hills, and Fortress Tedis on its crag
        y = 75 + round(2 * math.sin(x * .045) + 1.5 * math.sin(x * .11 + 1) - 3 * math.exp(-((x - 68) / 22) ** 2))
        cv.rect(x, y, 1, HZ - y, HILL)
    cv.paint(TEDIS, {"t": FORT}, 50, 65)
    wins, tops = ravine(cv)
    return cv, wins, tops


BASE, WINS, CHIMNEYS = base()


def draw():
    return BASE


# ------------------------------------------------------------------ Laputa, small and far
IW, IH = 64, 56
IX, IY = 134, 18
FAR = lambda c: mix(c, "#8fc0ea", .16)


def tone(u):
    return 1 if u < -.84 else 0 if u < -.05 else 1 if u < .4 else 2 if u < .76 else 3


def island():
    cv = Canvas(IW, IH)
    cx, uy = IW // 2, 43
    st, gr = [FAR(c) for c in ST], [FAR(c) for c in GR]
    for d in range(11):                                   # the dark underside
        hw = int(30 * math.sqrt(1 - (d / 11.2) ** 2))
        for x in range(cx - hw, cx + hw):
            u = (x + .5 - cx) / 30
            cv.set(x, uy + d, st[4] if u < -.6 else st[5] if u < .3 else st[6])
        if d in (2, 6):
            for x in range(cx - hw + 2, cx + hw - 2, 2):
                cv.set(x, uy + d, st[3] if x < cx - 14 else st[4] if x < cx + 10 else st[5])
    cv.rect(cx - 3, uy + 11, 6, 1, st[6])
    for x, y, n in [(6, 46, 3), (11, 49, 3), (17, 52, 2), (46, 52, 3), (52, 49, 3), (57, 46, 2)]:
        cv.rect(x, y, 1, n, st[6] if x > cx else st[5])
    prev = 0
    for hw, y0, y1 in [(8, 24, 28), (15, 28, 32), (22, 32, 36), (28, 36, 41), (31, 41, 43)]:
        for x in range(cx - hw, cx + hw):
            t = tone((x + .5 - cx) / hw)
            cv.rect(x, y0, 1, y1 - y0, st[t])
            cv.set(x, y1 - 1, st[t + 1])
        if y1 - y0 > 2:
            for k in range(-7, 8):
                x = cx + hw * math.sin(math.radians(k * 12))
                cv.rect(int(x), y0 + 2, 1, y1 - y0 - 3, st[min(6, tone((x - cx) / hw) + 3)])
        for x in range(cx - hw, cx + hw):
            if abs(x + .5 - cx) > prev - 1:
                cv.set(x, y0, gr[2] if x < cx else gr[3])
                if (x * 7 + hw) % 5 < 2:
                    cv.set(x, y0 - 1, gr[1] if x < cx else gr[3])
        if 8 < hw < 31:
            for sx, t in ((cx - hw, 0), (cx + hw - 2, 3)):
                cv.rect(sx, y0 - 4, 2, 4, st[t])
                cv.rect(sx, y0 - 5, 2, 1, gr[3])
        prev = hw
    for y in range(16, 26):                               # trunk and roots
        hw = 3 + max(0, y - 22)
        cv.rect(cx - hw, y, 2 * hw, 1, FAR(WD[0]))
        cv.rect(cx + hw - 2, y, 2, 1, FAR(WD[1]))
    for x, y, dx, n in [(cx - 6, 25, -1, 6), (cx + 5, 25, 1, 6), (cx - 3, 26, -1, 4), (cx + 2, 26, 1, 4)]:
        for i in range(n):
            cv.set(x + dx * (i // 2), y + i, FAR(WD[0] if dx < 0 else WD[1]))
    crown = [(32, 6, 5), (32, 14, 8), (23, 16, 7), (41, 16, 7), (15, 18, 6), (49, 18, 6), (8, 20, 4), (56, 20, 4), (4, 21, 3),
             (60, 21, 3), (20, 11, 5), (44, 11, 5), (27, 9, 5), (37, 9, 5), (32, 7, 4), (12, 22, 3), (52, 22, 3)]
    volume(cv, puffs(crown, 2, 2, .3, .45), gr, (.56, .40, .22, .04), soft=2, sharp=.7, sink=.3, light=LEAF)
    return cv


# ------------------------------------------------------------------ the near rim: Pazu's roof
ROOF_Y = 129                         # the ridge Pazu stands on
DOVECOTE = [
    "........s",
    ".......sSS",
    "......ssSSS",
    ".....sssSSSS",
    "....ssssSSSSS",
    "...sssssSSSSSS",
    "..ssssssSSSSSSS",
    ".sssssssSSSSSSSS",
    "ssssssssSSSSSSSSS",
    ".wwwwwwwwwwwwwwd",
    ".wkkwwkkwwkkwwwd",
    ".wkkwwkkwwkkwwwd",
    "lllllllllllllllll",
    ".wwwwwwwwwwwwwwd",
    ".wkkwwkkwwkkwwwd",
    ".wkkwwkkwwkkwwwd",
    "lllllllllllllllll",
    ".wwwwwwwwwwwwwwd",
    "..w....dd....d",
    "..w....dd....d",
    "..w....dd....d",
    "..w....dd....d",
]
DPAL = {"s": "#8088a8", "S": "#5c6388", "w": "#c9a070", "d": "#96704e", "k": INK, "l": "#e4c896"}


def knoll(x):
    return 153 + int(.0006 * (x - 127) ** 2)


def near():
    cv = Canvas(W, H)
    for x in range(W):                                    # the grassy rim we stand on
        y0 = knoll(x)
        for y in range(y0, H):
            cv.set(x, y, "#4f9648" if y - y0 < 8 else "#2f7048")
        cv.set(x, y0, "#b6dc62")
        cv.set(x, y0 + 1, "#7cba4c")
        if (x * 7) % 13 < 3:
            cv.set(x, y0 - 1, "#7cba4c")
    cv.rect(87, 150, 84, 4, "#a8684e")                    # the top of the brick wall under the eaves
    for y in range(ROOF_Y, 150):                          # the roof, seen from above and behind
        e = (y - ROOF_Y) * 8 // 20
        for x in range(92 - e, 165 + e):
            cv.set(x, y, "#e08a66" if y == ROOF_Y else ROOF_D if (y - ROOF_Y) % 3 == 0 or x > 158 + e else ROOF)
        cv.set(92 - e, y, "#e08a66")
    cv.rect(84, 149, 90, 1, "#7a3c3c")
    cv.rect(100, 116, 8, 1, WD[1])                         # chimney
    cv.rect(101, 117, 6, 15, "#b26a54")
    cv.rect(105, 117, 2, 15, "#8a5046")
    cv.paint(DOVECOTE, DPAL, 145, 108)
    return cv


NEAR = near()
PAZU = [                    # his near arm is a sprite, so it can hang or lift the trumpet
    "....tttttt.....",
    "...tttttttttt..",
    "..ttttttttttt..",
    "..TTTTTTTTTTttt",
    "..hhhssssssss..",
    "..hhsssessess..",
    "..hhsssessess..",
    "..hh.sssssss...",
    "...h..dssds....",
    "........ss.....",
    "....vvwwwwvv...",
    "...wvvvwwvvvw..",
    "....vvvwwvvvww.",
    "....vvvvvvvvww.",
    ".....vvvvvv.ww.",
    ".....vvvvvv.ss.",
    ".....bbbbbb....",
    ".....uuuuuu....",
    "....uuuuuuuu...",
    "....uUuuuuuu...",
    "....uUu..uuu...",
    "....uUu..uuu...",
    "....uUu..uPu...",
    "....uUu..uuu...",
    "....uUu..uuu...",
    "....uuu..uuu...",
    "....uuu..uuu...",
    "....nnn..nnnn..",
]
KPAL = {"s": SK[0], "d": SK[1], "e": INK, "P": "#b84c70", "n": WD[1], "t": "#c9955a", "T": WD[0], "h": WD[1],
        "w": "#fffaf0", "v": "#a8552e", "b": WD[1], "u": "#4f7f78", "U": "#35605e"}
PX, KY = 122, ROOF_Y - 27
TX = PX + 400                        # his trumpet pose is parked 400 px to the right of his arm


# ------------------------------------------------------------------ things that move
MOTH = [                    # the Tiger Moth far off, bow to the left, its lookout kite streaming behind
    "." * 33 + "aaa",
    "." * 17 + "lff" + "." * 12 + "l.a",
    "." * 7 + "h" * 10 + "l" + "." * 11 + "l",
    "...." + "h" * 17 + "....t.l",
    ".." + "HkHkHH" + "rHHH" * 3 + "Hhh.ttt",
    "." + "H" * 7 + "rHHH" * 3 + "HHHhtt",
    "." + "D" * 7 + "RDDD" * 3 + "DDdTT",
    "..." + "nn" + "k" * 15 + "dd..T",
    "....." + "ko" * 6 + "k",
]
MPAL = {"h": "#e4dccb", "H": "#c6b9a2", "D": "#a2988f", "d": "#8a8088", "r": "#b0a490", "R": "#8c8482",
        "n": "#8a6c64", "k": "#66525a", "f": INK, "o": GOLD, "l": "#6a6680", "t": "#cdc3ad", "T": "#a2988f",
        "a": "#e4dccb"}
GOLIATH = [                 # the Goliath, bow to the right, hazed by distance
    "....f" + "." * 21 + "t" + "." * 9 + "tt" + "." * 9 + "t",
    "...ff" + "." * 20 + "ttt" + "." * 7 + "tttt" + "." * 7 + "ttt",
    "..fff" + "h" * 54,
    ".ffff" + "h" * 62,
    "pffff" + "H" * 70,
    "pffff" + "H" * 76,
    "pffff" + "HHHH" + "wH" * 6 + "H" * 12 + "wH" * 8 + "H" * 12 + "wH" * 5 + "H" * 13,
    "pffff" + "D" * 75,
    ".ffff" + "D" * 68,
    "..fff" + "D" * 56,
    "...ff" + "." * 29 + "b" * 12,
    "....f" + "." * 30 + "bwbwbwbwbb",
]
OPAL = {"h": "#8196c6", "H": "#6b80b4", "D": "#566a9e", "f": "#566a9e", "t": "#6b80b4", "b": "#48598c",
        "w": "#c4d2ee", "p": "#a9bbe0"}
TRAIN = [                   # Dola's sons in their car, hard on the heels of the little mine train
    "." * 51 + "ff",
    "." * 40 + "cccc" + "." * 7 + "ff",
    "..hh.hh.h" + "." * 12 + "ooo" + "." * 6 + "ooo" + "." * 5 + "cRRc..bbbbbbbb",
    "..ss.ss.s" + "." * 10 + "ooooooo" + "..ooooooo" + "...cRRcbbbbbbbbbbb",
    ".yyyyyyyyy" + "." * 9 + "wwwwwww" + "..wwwwwww" + "...ccccbbbbbbbbbbbk",
    "yyyYyyyyYyy" + "." * 8 + "wwwwwww" + "kkwwwwwww" + "kkkkkkkkkkkkkkkkkkkkk",
    ".kk....kk" + "." * 10 + ".kk.kk.." + ".kk.kk.." + "..kk..kk...kk..kk",
]
TPAL = {"y": "#c89848", "Y": "#8a6450", "h": "#c0504a", "s": SK[0], "k": INK, "w": "#7a7f98", "o": WD[0],
        "c": "#2f4638", "R": "#f0a850", "b": "#3d5a4a", "f": "#3a3550"}
SHEETA = [                  # asleep on the air, braids streaming up, lit by the stone at her throat
    "................k..k",
    "...............k..k",
    "...............k.k",
    ".nn..ddddddddppsskk",
    "nnn.dddddddddpppsssk",
    "..n..dddddddd.ppssk",
    ".........dd",
]
HPAL = {"k": "#4a5a9c", "n": "#8a7a9a", "d": "#6f8fe0", "p": "#e4eefc", "s": "#fbe6d0"}
BPAL = {"w": "#ffffff", "k": "#3c4a78"}


def flock(pts):
    """Birds, wings up, placed point-symmetrically about the image centre. Turning the image half a turn
    about that centre gives the same flock with wings down, so one PNG is both frames of the flap."""
    mx, my = max(abs(x) for x, y in pts), max(abs(y) for x, y in pts)
    cv = Canvas(2 * mx + 5, 2 * my + 3)
    for x, y in pts + [(-x, -y) for x, y in pts if (x, y) != (0, 0)]:
        cv.paint(["w...w", "kwwwk", ".kkk."], BPAL, mx + x, my + y)
    return cv


def runs(pts, n=1):
    """Dashes n px long as one stroked path."""
    d, cx, cy = "", None, None
    for x, y in pts:
        d += f"M{x} {y}.5h{n}" if cx is None else f"m{x - cx} {y - cy}h{n}"
        cx, cy = x + n, y
    return d


def diamond(cx, cy, r):
    """A filled pixel diamond of radius r round the pixel (cx, cy)."""
    return f"M{cx} {cy - r}h1" + "v1h1" * r + "v1" + "h-1v1" * r + "h-1" + "v-1h-1" * r + "v-1" + "h1v-1" * r + "z"


def smoke(x, y, delay):
    return (f"<path class='lr-s' style='animation-delay:-{delay}s' fill='#eef' "
            f"d='M{x} {y - 3}h2v2h-2zm2-4h3v3h-3z'/>")


SX, SY = 199, -14                    # Sheeta, parked above the frame
GX, GY = SX + 13, SY + 5             # the stone
NX, NY = IX + IW // 2, IY + 54       # Laputa's lowest point
VEINS = [                            # crystal veins: three bands down the walls, lit in turn as she passes
    [(236, 98), (241, 100), (246, 96), (262, 104), (268, 106), (228, 94), (112, 101), (106, 103), (84, 100), (78, 102), (120, 97)],
    [(222, 117), (228, 120), (234, 116), (252, 124), (258, 127), (270, 130), (124, 118), (118, 121), (98, 116), (92, 118), (70, 124)],
    [(206, 137), (212, 141), (220, 139), (244, 146), (250, 148), (184, 134), (150, 131), (178, 142), (190, 147), (268, 150)],
]

LAYERS = [
    # --- sky: the Goliath far off, Laputa with a wisp of cloud across it, a drifting cloud, the Tiger Moth
    ("goliath", img(art(GOLIATH, OPAL), -90, 30, " class='lr-go'")),
    ("laputa", "<g class='lr-i'>" + img(island(), IX, IY)
     + f"<path class='lr-v' style='--d:160s' stroke='#aff' d='M{NX - 2} {NY}.5h4m-3 1h2'/></g>"
     + img(cloud([(7, 11, 5), (16, 8, 7), (27, 10, 6), (36, 13, 4), (22, 14, 6), (11, 15, 5)], 42, 17, C, 7, base=15),
           118, 60)),
    ("cloud", img(cloud([(8, 12, 6), (18, 9, 8), (30, 11, 7), (40, 13, 5), (24, 14, 7)], 48, 18, C, 6, base=16),
                  -70, 40, " class='lr-a'")),
    ("moth", img(art(MOTH, MPAL), 330, 22, " class='lr-t'")),
    # --- down in the ravine: chimney smoke, the train and the pirates' car, the mine wheel, the pigeons
    ("smoke", "".join(smoke(x, y, d) for (x, y), d in zip([CHIMNEYS[k] for k in ((-1, .62), (-1, .76), (1, .76))] + [(277, 75)], (0, 3, 5, 2)))),
    ("train", f"<svg x='102' y='{TY - 7}' width='127' height='7'>" + img(art(TRAIN, TPAL), -56, 0, " class='lr-tr'") + "</svg>"),
    ("wheel", f"<path class='lr-wh' stroke='#2a2438' d='M{WX}.5 {WY - 4}v9M{WX + 1} {WY}.5h4'/>"),
    ("pigeons", "<g class='lr-px'><g class='lr-py'>"
     + img(flock([(0, 0), (9, -4), (17, 3), (25, -6)]), 102, 133, " class='lr-pf'") + "</g></g>"),
    # --- the rim: Pazu's roof, his chimney smoke, Pazu, and the arm that hangs or lifts the trumpet
    ("near", img(NEAR, 0, 0) + smoke(103, 116, 1)),
    ("pazu", img(art(PAZU, KPAL), PX, KY)
     + f"<path class='lr-k' fill='#fca' d='M{PX + 8} {KY + 5}h1v2h-1zm3 0h1v2h-1z'/>"
     + f"<g class='lr-tp'><path fill='#fffaf0' d='M{PX + 2} {KY + 12}h2v3h-2zM{TX + 2} {KY + 9}h1v1h1v2h-2z'/>"
       f"<path fill='#f8cfa0' d='M{PX + 2} {KY + 15}h2v1h-2zM{TX + 1} {KY + 8}h2v1h-2z'/>"
       f"<path fill='gold' d='M{TX - 5} {KY + 5}h1v1h1v1h10v1h-12z'/>"
       f"<path fill='peru' d='M{TX - 5} {KY + 8}h2v1h-2zm5-2h1v1h-1zm2 0h1v1h-1z'/></g>"),
    ("pigeon", "<g class='lr-j'><path fill='#fff' d='M150 105h2v1h2v2h-3v-1h-1z'/><path fill='#fc4' d='M149 106h1v1h-1z'/></g>"),
    # --- light: night, the warm wash, and what the night does not dim
    ("night", f"<rect class='lr-N lr-b' width='{W}' height='{H}' fill='#4a5ca4'/>"
     f"<rect class='lr-W lr-b' width='{W}' height='{H}' fill='#fa6'/>"),
    ("lights", "<g class='lr-N'>"
     + f"<path stroke='#fff' d='{runs([(18, 16), (86, 26), (96, 8), (118, 21), (214, 15), (246, 24), (282, 8), (300, 19), (160, 6), (228, 27), (30, 25)])}'/>"
     + f"<path stroke='#fd7' d='{runs(sorted((p for p in WINS if NEAR.px[p[1]][p[0]] == UNPAINTED and not (PX <= p[0] < PX + 15 and p[1] >= KY)), key=lambda p: (p[1], p[0])) + [(66, 68), (57, 72), (63, 73), (70, 72), (80, 70)])}'/>"
     + f"<path fill='#fd7' d='M{MX - 10} {MY + 7}h1v3h-1z'/><path fill='#fd7' opacity='.3' d='{diamond(MX - 10, MY + 8, 4)}'/><path fill='#ffe' d='M52 20h3v1h-2v1h-1v4h1v1h2v1h-3v-1h-1v-1h-1v-4h1v-1h1z'/></g>"),
    ("veins", "".join(f"<path class='lr-v' style='--d:{d}s' stroke='#6ef' d='{runs(pts, 2)}'/>"
                      for pts, d in zip(VEINS, (170, 176, 182)))),
    ("sheeta", "<g class='lr-sh'>" + f"<path fill='#8ef' opacity='.22' d='{diamond(GX, GY, 8)}'/>"
     f"<path fill='#8ef' opacity='.3' d='{diamond(GX, GY, 5)}'/>" + img(art(SHEETA, HPAL), SX, SY)
     + f"<path fill='#8ef' d='{diamond(GX, GY, 2)}'/><path fill='#fff' d='M{GX} {GY}h1v1h-1z'/></g>"),
]
SPRITES = "".join(chunk for _, chunk in LAYERS)

CSS = (
    # ambient loops
    ".lr-i{animation:lr-i 16s steps(2) infinite alternate}@keyframes lr-i{to{transform:translateY(2px)}}"
    ".lr-a{animation:lr-a 780s -300s steps(390) infinite}@keyframes lr-a{to{transform:translateX(390px)}}"
    ".lr-s{animation:lr-s 8s steps(8) infinite}@keyframes lr-s{from{opacity:0}25%{opacity:.8}to{opacity:0;transform:translateY(-8px)}}"
    ".lr-k{opacity:0;animation:lr-k 6s steps(1) infinite}@keyframes lr-k{96%{opacity:1}}"
    ".lr-j{animation:lr-j 8s steps(1) infinite}@keyframes lr-j{75%{transform:translateX(3px)}}"
    # night and the warm wash (which peaks twice a cycle: one keyframe set serves dusk and dawn)
    ".lr-b{mix-blend-mode:multiply}"
    ".lr-N{opacity:0;animation:lr-N 240s steps(8) infinite}@keyframes lr-N{45%{opacity:0}51%,94.5%{opacity:1}99.5%{opacity:0}}"
    ".lr-W{animation:lr-W 120s steps(6) infinite}@keyframes lr-W{from,to{opacity:.24}5%,88%{opacity:0}96%{opacity:.6}}"
    # the day's moments
    ".lr-tp{animation:lr-tp 240s steps(1) infinite}@keyframes lr-tp{1%{transform:translateX(-400px)}7%{transform:none}}"
    ".lr-px{animation:lr-px 240s steps(135) infinite}.lr-py{animation:lr-py 240s steps(45) infinite}"
    ".lr-pf{transform-box:fill-box;transform-origin:center;animation:lr-pf 240s steps(45) infinite}"
    "@keyframes lr-px{1.5%{transform:none}8%,29%{transform:translateX(270px)}35.5%,to{transform:none}}"
    "@keyframes lr-py{1.5%{transform:none}8%,29%{transform:translateY(-90px)}35.5%,to{transform:none}}"
    "@keyframes lr-pf{1.5%{transform:none}8%,29%{transform:rotate(8100deg)}35.5%,to{transform:none}}"
    ".lr-t{animation:lr-t 240s steps(190) infinite}@keyframes lr-t{8%{transform:none}42%,to{transform:translateX(-380px)}}"
    f".lr-wh{{transform-origin:{WX}.5px {WY}.5px;animation:lr-wh 240s steps(96) infinite}}"
    "@keyframes lr-wh{6%{transform:none}44%,to{transform:rotate(8640deg)}}"
    ".lr-tr{animation:lr-tr 240s steps(92) infinite}@keyframes lr-tr{16%{transform:none}27%,to{transform:translateX(184px)}}"
    ".lr-go{animation:lr-go 240s steps(210) infinite}@keyframes lr-go{44%{transform:none}84%,to{transform:translateX(420px)}}"
    # the night's moment
    ".lr-sh{animation:lr-sh 240s steps(212) infinite}@keyframes lr-sh{62%{transform:none}84%,to{transform:translateY(212px)}}"
    ".lr-v{opacity:0;animation:lr-v 240s var(--d) steps(3) infinite}@keyframes lr-v{1%,4%{opacity:1}6%{opacity:0}}"
)
THEME = {
    "position": "center 45%",
    "canvas": "#101a36", "accent": "#f6c56a", "overlay": "#0e1834",
    "colors": {"sidebar": "#0d1630", "sidebarRowSelected": "#22305a", "sidebarBorder": "#1d2a50",
               "surface": "#152044", "border": "#27366a", "text": "#f1f4ff", "textMuted": "#a9b6d6"},
}
