"""Castle in the Sky: Laputa adrift in a blue noon sky, rising out of towering cumulus. On a grassy
knoll among mossy ruins the garden robot offers a flower to Sheeta while Pazu looks on.

A 320x180 canvas. Nearly everything is a small palette PNG nested in the SVG (a PNG is far cheaper per
pixel than paths, and each layer can move or be passed behind). Back to front:

  draw()      sky bands, a hazed cloud bank and the Dragon's Nest storm far off (the build encodes this one)
  far         the Goliath, lightning in the storm, a high cloud streak
  middle()    cumulus towers, the cloud sea, the knoll with its ruins, a fallen robot, a nest, flowers
  island()    Laputa: crown, trunk and roots, ring walls with arcades, towers and gardens, the dark underside
  near        a wisp lapping the island, two drifting clouds, gulls, the Tiger Moth with its lookout kite,
              Dola's flaptters, Pazu's pigeons
  figures     Pazu (who plays his trumpet now and then) and Sheeta, the robot with its head as a separate
              piece so it can nod, the fox-squirrel

Motion is CSS transform/opacity only, in whole-pixel steps().
- Ambient loops change on a shared half-second grid, so the image is redrawn about twice a second.
- A "moment" is parked off-canvas (or at opacity 0) and its keyframes hold for most of the cycle, e.g.
  `15%,to{...}`: nothing changes, so nothing is redrawn, until its turn comes round. The flapping of
  wings is a half-turn per step driven by the same held keyframes, so it stops while parked too.
- Moments share a 120 s cycle (the two airships 240 s) and each has its own slot; see CSS.
"""
import base64, math, random, struct, zlib
from lib import Canvas, UNPAINTED

NAME = "Castle in the Sky"
SIZE = W, H = 320, 180
COLORS = 16

S = ["#1f4a9c", "#2a5fb4", "#3a78c8", "#5494d8", "#74b0e4", "#9acbee", "#bfe0f4"]   # sky top -> horizon
HAZE = ["#d6e6f7", "#bcd6f1", "#a3c5ea"]                         # far cloud, hazed towards the sky
STORM = ["#b4c0e2", "#97a5d0", "#7f8dbe"]                        # the Dragon's Nest
C = ["#fffaf0", "#f1e9e6", "#d3d3e8", "#b3b6d8", "#989cc8"]       # cumulus: sunlit -> deep shade
G = ["#b6dc62", "#7cba4c", "#4f9648", "#2f7048", "#1f5244"]       # meadow: lit edge -> deep
ST = ["#f6ecd0", "#dccdaa", "#b0a29c", "#807a98", "#514c70", "#353150", "#23213a"]   # stone: lit -> black
GR = ["#c4e070", "#8cc458", "#56984f", "#2f6c50", "#1e4b47"]      # leaves and moss
WD = ["#8a6450", "#5e4640"]                                       # wood: trunk, roots, hulls
RB = ["#d2a66c", "#a07a50", "#8a6848", "#70563e", "#2b2438"]      # robot: lit, body, groove, shade, joints
SK = ["#f8cfa0", "#d8996c"]                                       # skin
INK, PINK, GOLD = "#2a2438", "#f08aa0", "#ffd75e"
GY = 152             # ground line under the figures


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
                mix = prev and ((k == 0 and (x % 4 != (yy % 2) * 2)) or (k == 1 and (x + yy) % 2)
                                or (k == 2 and x % 4 == (yy % 2) * 2))
                cv.set(x, yy, prev if mix else c)
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


SUN = (-.45, -.60, .66)      # light for the clouds: upper left, fairly frontal
LEAF = (-.52, -.66, .54)     # the crown gets a lower sun so its underside goes properly dark
CUTS = (.45, .30, .12, -.05)


def volume(cv, lumps, tones, cuts, soft=4, sharp=.6, sink=.25, base=None, light=SUN):
    """Painterly lumpy volume (cumulus, tree crown). The lumps are spheres and their union is a height
    field. Each pixel is lit by a mix of that field's normal (crisp billows, each with a sunlit crown
    and a shaded underside) and the normal of a blurred copy (the mass as a whole turning away from
    the sun), darkened towards the bottom by `sink`, then cut into flat tones. Sky pockets enclosed
    by lumps are filled. Rows from `base` down are not painted."""
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


# ------------------------------------------------------------------ sky and far clouds
def draw():
    """Base layer: the sky, a hazed cloud bank, and the Dragon's Nest brooding on the horizon."""
    cv = Canvas(W, H)
    bands(cv, 0, [(16, S[0]), (38, S[1]), (62, S[2]), (86, S[3]), (108, S[4]), (128, S[5]), (H, S[6])])
    volume(cv, puffs([(112, 118, 8), (100, 126, 10), (124, 128, 10), (138, 134, 9), (88, 134, 10), (170, 137, 8),
                      (186, 139, 8), (204, 137, 9)], 9, 2), HAZE, (.45, .22), soft=3, sink=.3, base=146)
    volume(cv, puffs([(224, 88, 6), (236, 85, 8), (249, 85, 8), (261, 89, 6), (230, 99, 11), (254, 100, 12),
                      (242, 112, 14), (222, 118, 10), (262, 118, 12), (244, 130, 16)], 4, 2),
           STORM, (.45, .22), soft=3, sink=.35, base=146)
    return cv


# ------------------------------------------------------------------ cumulus and the knoll
LEFT = [(38, 44, 10), (50, 52, 10), (26, 54, 11), (58, 66, 12), (14, 68, 13), (38, 70, 15), (70, 84, 12),
        (26, 88, 17), (2, 90, 14), (54, 96, 16), (84, 106, 12), (22, 116, 20), (60, 120, 20), (92, 128, 13),
        (-2, 122, 16), (20, 150, 24), (60, 152, 24), (96, 150, 16), (-6, 150, 16)]
RIGHT = [(298, 72, 10), (310, 84, 12), (284, 86, 11), (322, 102, 14), (268, 102, 12), (294, 104, 15),
         (270, 124, 16), (302, 126, 18), (326, 130, 12), (246, 130, 11), (250, 154, 16), (284, 156, 22), (316, 154, 18)]
SEA = [(108, 151, 10), (128, 154, 13), (150, 150, 8), (166, 155, 13), (188, 152, 9), (204, 154, 12),
       (226, 151, 11), (240, 154, 10)]
RUIN = {"o": ST[0], "a": ST[1], "b": ST[2], "d": ST[3], "g": GR[2], "G": GR[1], "m": GR[3],
        "n": WD[0], "e": C[0], "R": RB[1], "D": RB[3], "k": RB[4], "p": PINK}
COLUMN = [                  # a broken column with a nest and two eggs on top
    "..ee......",
    ".nnnnnn...",
    "..gGGg....",
    ".GGgggmm..",
    ".oogabbdd.",
    ".ooabbbdd.",
    ".ooabbbdd.",
    ".gGabbbdd.",
    ".ogGbbbdd.",
    ".ooagbbdd.",
    ".ooabbbdd.",
    ".ooabbmdd.",
    "oooabbbmdd",
    "oooabbbddd",
]
BLOCK = [
    "..gGg...",
    ".ooaabd.",
    "oooaabdd",
    "oooaabdd",
]
FALLEN = [                  # a robot long dead, sunk into the grass, with a flower laid on it
    ".....p.........",
    "....gGGGg......",
    "..gGGmRRRRD....",
    ".gGRRRRRRRDD...",
    ".GRkkRRRkRRD.gG",
    "gGRkkRRRRRRDgGm",
    "GgRRRRRRRRDDGgm",
]


def knoll(x):
    return GY + int(.0005 * (x - 178) ** 2)


def middle():
    """Cumulus towers, the cloud sea on the horizon and the grassy knoll the figures stand on."""
    cv = Canvas(W, H)
    volume(cv, SEA, C[:3], (.45, .30), soft=3, sink=.2)
    volume(cv, puffs(LEFT, 3), C, CUTS)
    volume(cv, puffs(RIGHT, 5), C, CUTS)
    for x in range(W):
        y0 = knoll(x)
        for y in range(y0, H):
            d = y - y0
            cv.set(x, y, G[1] if d < 2 else G[2] if d < 9 or (d < 11 and (x + y) % 2) else
                   G[3] if d < 19 or (d < 21 and (x + y) % 2) else G[4])
        cv.set(x, y0, G[0])
        if (x * 7) % 13 < 3:                      # tufts
            cv.set(x, y0 - 1, G[0] if x % 2 else G[1])
        if (x * 5) % 31 == 0:
            cv.set(x, y0 - 2, G[1])
    for x, d, c in [(118, 7, PINK), (146, 6, GOLD), (183, 3, PINK), (228, 3, GOLD), (88, 7, GOLD), (262, 5, PINK)]:
        cv.set(x, knoll(x) + d, c)
    for x, d in [(96, 3), (124, 8), (138, 4), (172, 5), (196, 8), (222, 4), (246, 9), (268, 6), (70, 6)]:
        cv.paint([".w.", "wyw", ".w."], {"w": C[0], "y": GOLD}, x, knoll(x) + d)
    cv.paint(COLUMN, RUIN, 112, knoll(117) - 13)
    cv.paint(BLOCK, RUIN, 126, knoll(130) - 3)
    cv.paint(FALLEN, RUIN, 234, knoll(241) - 6)
    return cv


# ------------------------------------------------------------------ the island
IW, IH = 104, 84
IX, IY = 96, 32


def tone(u):
    """Tone index across a cylinder seen from the side, lit from the upper left (u = -1..1)."""
    return 1 if u < -.84 else 0 if u < -.05 else 1 if u < .4 else 2 if u < .76 else 3


def island():
    cv = Canvas(IW, IH)
    cx = IW // 2
    # underside: a dark hemisphere with ring grooves, a nub at the bottom and hanging roots
    uy = 63
    for d in range(17):
        hw = int(49 * math.sqrt(1 - (d / 17.2) ** 2))
        for x in range(cx - hw, cx + hw):
            u = (x + .5 - cx) / 49
            cv.set(x, uy + d, ST[4] if u < -.62 + d * .012 else ST[5] if u < .3 + d * .01 else ST[6])
        if d in (3, 9):
            for x in range(cx - hw + 2, cx + hw - 2):
                if x % 2:
                    cv.set(x, uy + d, ST[3] if x < cx - 26 else ST[4] if x < cx + 16 else ST[5])
    cv.rect(cx - 5, uy + 17, 9, 1, ST[5])
    cv.rect(cx - 3, uy + 18, 6, 1, ST[6])
    for x, y, n in [(9, 68, 4), (15, 71, 5), (22, 75, 3), (29, 77, 5), (36, 79, 3), (68, 79, 4), (74, 78, 3),
                    (81, 75, 5), (88, 71, 4), (94, 67, 3)]:
        cv.rect(x, y, 1, n, ST[6] if x > cx else ST[5])
    # ring walls, widest at the bottom: arcades, cornice, shadowed foot
    prev = 0
    for hw, y0, y1 in [(13, 32, 38), (25, 38, 45), (37, 45, 52), (47, 52, 60), (52, 60, 63)]:
        for x in range(cx - hw, cx + hw):
            t = tone((x + .5 - cx) / hw)
            cv.rect(x, y0, 1, y1 - y0, ST[t])
            cv.set(x, y1 - 1, ST[t + 1])
        if y1 - y0 > 3:
            for k in range(-8, 9):
                x = cx + hw * math.sin(math.radians(k * 10.5))
                n = 2 if abs(k) < 5 else 1
                cv.rect(int(round(x - n / 2)), y0 + 3, n, y1 - y0 - 4, ST[min(6, tone((x - cx) / hw) + 3)])
        # terrace garden on the ledge this tier adds
        for x in range(cx - hw, cx + hw):
            if abs(x + .5 - cx) > prev - 1:
                left = x < cx
                g = (x * 7 + hw) % 5
                cv.set(x, y0, GR[2] if left else GR[3])
                if g < 3:
                    cv.set(x, y0 - 1, GR[1 if g else 0] if left else GR[2 if g else 3])
                if g == 1 and abs(x - cx) < hw - 3:
                    cv.set(x, y0 - 2, GR[1] if left else GR[3])
        # a domed tower at each end of the ledge
        if 13 < hw < 52:
            for sx, t in ((cx - hw + 1, 0), (cx + hw - 5, 3)):
                cv.rect(sx, y0 - 5, 4, 6, ST[t])
                cv.rect(sx + 3, y0 - 5, 1, 6, ST[t + 1])
                cv.rect(sx, y0 - 6, 4, 1, GR[3])
                cv.rect(sx + 1, y0 - 7, 2, 1, GR[3])
                cv.set(sx + 1, y0 - 3, ST[t + 3])
        prev = hw
    # trunk, with roots spilling down over the citadel and the upper wall
    for y in range(20, 35):
        hw = 5 + max(0, y - 29)
        cv.rect(cx - hw, y, 2 * hw, 1, WD[0])
        cv.rect(cx + hw - 4 - (y > 30), y, 4 + (y > 30), 1, WD[1])
    for x, y, dx, n in [(cx - 10, 33, -1, 10), (cx - 5, 35, -1, 7), (cx + 9, 33, 1, 11), (cx + 4, 35, 1, 6),
                        (cx - 13, 35, -2, 6), (cx + 12, 35, 2, 6)]:
        for i in range(n):
            cv.rect(x + dx * (i // 2), y + i, 2, 1, WD[0] if dx < 0 else WD[1])
    # little trees in the terrace gardens
    for x, y in [(cx - 20, 38), (cx - 33, 45), (cx - 29, 45), (cx - 43, 52), (cx + 17, 38), (cx + 28, 45),
                 (cx + 40, 52), (cx + 32, 45)]:
        lit = x < cx
        cv.rect(x, y - 3, 3, 2, GR[1] if lit else GR[3])
        cv.set(x + 1, y - 4, GR[0] if lit else GR[2])
        cv.set(x, y - 3, GR[0] if lit else GR[2])
        cv.set(x + 2, y - 2, GR[2] if lit else GR[4])
    # vines trailing down the walls from each terrace
    for x, y, n in [(8, 61, 3), (17, 53, 4), (24, 53, 2), (31, 46, 3), (38, 46, 2), (22, 61, 2), (44, 39, 2),
                    (66, 39, 3), (73, 46, 3), (82, 53, 4), (90, 53, 2), (97, 61, 3), (60, 46, 2), (35, 53, 2)]:
        cv.rect(x, y, 1, n, GR[2] if x < cx else GR[3])
    # the crown: a broad dome of leaf clumps, hanging lower at the sides so the trunk shows under its middle
    crown = [(52, 16, 13), (38, 19, 11), (66, 19, 11), (25, 22, 10), (79, 22, 10), (13, 25, 7), (91, 25, 7),
             (7, 27, 4), (97, 27, 4), (32, 12, 9), (72, 12, 9), (44, 8, 9), (60, 8, 9), (52, 5, 6),
             (20, 16, 6), (84, 16, 6), (18, 28, 5), (86, 28, 5), (33, 28, 5), (71, 28, 5)]
    volume(cv, puffs(crown, 2, 2, .3, .45), GR, (.56, .40, .22, .04), soft=3, sharp=.7, sink=.3, light=LEAF)
    # boughs showing in the shade under the crown
    for x, y, dx, n in [(cx - 6, 27, -1, 7), (cx + 5, 27, 1, 7), (cx - 3, 24, -1, 4), (cx + 2, 24, 1, 4)]:
        for i in range(n):
            cv.set(x + dx * i, y - i // 2, WD[1])
    return cv


# ------------------------------------------------------------------ the robot
RPAL = {"o": RB[0], "b": RB[1], "c": RB[2], "d": RB[3], "k": RB[4], "g": GR[2], "G": GR[1], "m": GR[3],
        "y": GOLD, "f": C[0], "p": PINK, "s": GR[2]}
HEAD = [
    "....GGobbb...",
    "..gGGGbbbbbd.",
    ".ogGgbbbbbbbd",
    "ooobbbbbbbbdd",
    "oobkkbbbbbbdd",
    "ookyykbbkbbdd",
    "ookyykbkykbdd",
    "oobkkbbbkbbdd",
    ".oobbbbbbbdd.",
    "...obbbbdd...",
]
TORSO = [
    "......GGGoobbbbbbbbdd....",
    "....gGGGgoobbbbbbbbbbdd..",
    "..oGGggmoobbbbbbbbbbbbddd",
    ".oogggmoobbbbbbbbbbbbbbdd",
    "oobgmooobbbbooobbbbbbbbdd",
    "oobbbobbbbbbobobbbbbbbddd",
    "obbbdoobbbbbooobbbbbbdbdd",
    ".bbd.oobbbbbbbbbbbbbd.bdd",
    ".....oobbbbbbbbbbGgbd....",
    "......obbbbbbbbbbggmd....",
    "......oobbbbbbbbbbmdd....",
    ".......obbbbbbbbbbdd.....",
    ".......oobbbbbbbbddd.....",
    "........obbbbbbbbdd......",
    "........oobbbbbbdd.......",
    ".........obbbbbdd........",
    ".........kkkkkkkk........",
    ".........oobbbbdd........",
    "........oobbbbbbdd.......",
    "........obbbbbbbbd.......",
]
LEGS = [                    # two separate legs: ringed thighs, shins flaring outwards, flat feet
    "........obd....obd",
    "........obd....obd",
    "........ccd....ccd",
    "........obd....obd",
    "........obd....obd",
    "........ccd....ccd",
    "........obd....obd",
    "........obd....obd",
    ".......kkkk....kkkk",
    ".......obbd....obbd",
    ".......obGd....obbd",
    ".......ccmg....cccd",
    "......oobbd....obbbd",
    "......oobbd....obbbd",
    "......ccccd....ccccd",
    ".....oobbbd....obbbd",
    ".....oobbbd....obbGd",
    ".....cccccd....cccmd",
    ".....oobbbd....obbbd",
    ".....oobbbd....obbbd",
    "....kkkkkkk....kkkkkk",
    "..gGoobbbbd....obbbbd",
    ".mgGoobbbbd....obbbbbdd",
    ".obbbbbbbbd....obbbbbbbd",
]
HAND = [
    "obbbd",
    "obbbd",
    "b.b.d",
    "b.b.d",
    "b...d",
]
RW, RH = 40, 56      # robot canvas; the head is a separate piece so it can nod
RX, RY = 180, GY - RH
HXA, HYA = RX + 17, RY                  # the head, absolute


def limb(cv, x, y, n, w0, w1):
    """A ringed limb running down from (x, y), centred on column x, width w0 -> w1, a soft groove every 3rd row."""
    for i in range(n):
        w = round(w0 + (w1 - w0) * i / max(1, n - 1))
        for j in range(w):
            cv.set(x - w // 2 + j, y + i, RB[3] if j == w - 1 else RB[2] if i % 3 == 2 else RB[0] if j == 0 else RB[1])


def robot():
    cv = Canvas(RW, RH)
    tx = 12                                   # torso left edge
    cv.paint(LEGS, RPAL, tx, 32)
    # far arm, hanging: upper arm, forearm flaring to the wrist, three long fingers
    ax = tx + 23
    limb(cv, ax, 20, 12, 3, 3)
    cv.rect(ax - 1, 32, 3, 1, RB[4])
    limb(cv, ax, 33, 11, 3, 5)
    cv.paint(HAND, RPAL, ax - 2, 44)
    # near arm: down to the elbow, then the forearm held out level with the flower
    ax = tx + 2
    limb(cv, ax, 20, 9, 3, 3)
    cv.rect(ax - 1, 29, 3, 1, RB[4])
    cv.rect(ax - 1, 30, 3, 3, RB[1])
    cv.rect(ax + 1, 30, 1, 3, RB[3])
    for i in range(10):
        w = 3 + (i > 4)
        for j in range(w):
            cv.set(ax - 2 - i, 30 + j - (w > 3), RB[3] if j == w - 1 else RB[2] if i % 3 == 2 else RB[0] if j == 0 else RB[1])
    cv.paint(["Gg", "gm"], RPAL, ax - 8, 28)
    cv.paint([".f.", "fpf", ".f.", ".s.", ".s.", "oo.", "obb", "obd", ".dd"], RPAL, 1, 21)
    cv.paint(TORSO, RPAL, tx, 12)
    cv.rect(tx + 10, 10, 5, 2, RB[3])         # neck
    cv.rect(tx + 10, 10, 5, 1, RB[4])
    return cv


# ------------------------------------------------------------------ Sheeta and Pazu
SHEETA = [
    ".....kkkkkk....",
    "...kkKKkkkkkk..",
    "..kkKkkkkkkkkk.",
    "..kkkkkkkkkkkk.",
    "..kkkkkkskksk..",
    "..kkkkssssssss.",
    "..kkkksssesses.",
    "..kkkksssesses.",
    "..kkk.dssssss..",
    ".kkk...dssds...",
    ".kk.....ss.....",
    ".rr...pppppp...",
    ".kk..pppppppp..",
    ".kk..pPpppppps.",
    ".kk..pPpcppp.ss",
    ".k...pPppppp...",
    ".k...pPppppp...",
    ".....PPppppp...",
    ".....yyyyyyy...",
    "....yyyyyyyyy..",
    "....yYyyyyyyy..",
    "....yYyyy.yyy..",
    "....yYyy..yyy..",
    "....yYyy..yyy..",
    "....yyyy..yyy..",
    ".....YY....YY..",
    ".....ss....ss..",
    ".....nn....nnn.",
]
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
KPAL = {"k": INK, "K": "#4a4468", "s": SK[0], "d": SK[1], "e": INK, "p": "#e8708c", "P": "#b84c70",
        "y": "#e8b450", "Y": "#b88438", "n": WD[1], "r": "#d83848", "c": "#7fe8ff",
        "t": "#c9955a", "T": WD[0], "h": WD[1], "w": C[0], "v": "#a8552e", "b": WD[1],
        "u": "#4f7f78", "U": "#35605e"}
SX, PX = 159, 141
KY = GY - 28
CX, CY = SX + 8, KY + 14             # Sheeta's crystal


def kids():
    cv = Canvas(SX - PX + 15, 28)
    cv.paint(SHEETA, KPAL, SX - PX, 0)
    cv.paint(PAZU, KPAL, 0, 0)
    return cv


# ------------------------------------------------------------------ things that fly
RIB = "HHHHHr" * 4
MOTH = [                    # the Tiger Moth, bow to the left: pirate flag, washing line, lookout kite on its tether
    "." * 62 + "aaaaaa",
    "." * 36 + "lfffff" + "." * 21 + "aAAa",
    "." * 36 + "lfwfwf" + "." * 19 + "l..aa",
    "." * 17 + "l" * 19 + "lfffff" + "." * 17 + "l",
    "." * 17 + "l..ww..p..cc..ww..." + "l" + "." * 19 + "l",
    "." * 17 + "l..ww..p..c...w...." + "l" + "." * 17 + "l",
    "." * 15 + "h" * 20 + ".l" + "." * 15 + "t",
    "." * 9 + "h" * 30 + "." * 12 + "tt",
    "." * 6 + "h" * 5 + "hhhhhr" * 4 + "h" * 8 + "." * 6 + "tttt",
    "." * 4 + "H" * 7 + RIB + "H" * 6 + "hhhh" + "." + "t" * 7,
    ".." + "HkHkHkHHH" + RIB + "H" * 8 + "hhhh" + "t" * 6,
    "." + "H" * 10 + RIB + "H" * 10 + "hhhhTTTT",
    "." + "D" * 10 + "DDDDDR" * 4 + "D" * 11 + "dddTTTT",
    ".." + "n" * 9 + "DDDDDR" * 4 + "D" * 9 + "ddd" + ".." + "TTTT",
    "." * 4 + "n" * 6 + "k" * 30 + "ddd" + "." * 6 + "TTT",
    "." * 6 + "kkkk" + "okk" * 9 + "k" + "." * 12 + "T",
    "." * 9 + "k" * 24,
    "",
    "",
]
MPAL = {"h": "#eee2c6", "H": "#cfbb94", "D": "#a8967e", "d": "#8a7a70", "r": "#b8a480", "R": "#917f6c",
        "n": WD[0], "k": WD[1], "f": INK, "w": C[0], "o": GOLD, "p": PINK, "c": "#7fd0e8", "l": "#6a6680",
        "t": "#d8c8a4", "T": "#a8967e", "a": "#eee2c6", "A": "#c0504a"}
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
FLAP = [                    # a flaptter, Dola's pink braids streaming
    "...........pp...........",
    ".........ppsss.w........",
    "t.......hhhhhhhww.......",
    "tt....hhhhhHHHHHHHh.....",
    "ttthhhhhhHHHHHHHHHHkh...",
    ".tt.rrrrrrrrrrrrrrrhh...",
    "........dddddddddddd....",
    "..........d......d......",
    ".........ddd....ddd.....",
]
FPAL = {"h": "#c89858", "H": "#a87040", "r": "#b8423a", "d": WD[1], "t": "#a87040", "p": PINK,
        "s": SK[0], "w": "#cfe8f4", "k": GOLD}
FOX = [
    ".e.e....",
    ".ooo..tt",
    "okoo.tTt",
    ".wooooTt",
    "..o.o...",
]
XPAL = {"o": "#f0a850", "e": "#c87830", "t": "#f0a850", "T": "#c87830", "k": INK, "w": C[0]}
BPAL = {"w": "#ffffff", "k": "#3c4a78"}


def moth():
    cv = art(MOTH, MPAL)
    for x in (13, 30):      # two engines on outriggers, their propellers a pale blur seen edge-on
        cv.rect(x, 9, 1, 10, "#e4eefa")
        cv.rect(x + 1, 13, 5, 2, WD[1])
    return cv


def flock(pts):
    """Birds, wings up, placed point-symmetrically about the image centre. Turning the image half a turn
    about that centre gives the same flock with wings down, so one PNG is both frames of the flap. Each
    bird carries a dark edge, so it reads over white cloud as well as over sky."""
    mx, my = max(abs(x) for x, y in pts), max(abs(y) for x, y in pts)
    cv = Canvas(2 * mx + 5, 2 * my + 3)
    for x, y in pts + [(-x, -y) for x, y in pts if (x, y) != (0, 0)]:
        cv.paint(["w...w", "kwwwk", ".kkk."], BPAL, mx + x, my + y)
    return cv


def wings(x, y):
    """A flaptter's four wings raised, for the craft whose image is at (x, y). A half turn about the
    bottom of this shape (the wing roots) swings them down behind the hull."""
    return f"<path class='lp-w' d='M{x + 4} {y - 4}.5h3m-2 1h4m-2 1h4m-2 1h3m4 0h2m-1-1h3m-2-1h4m-3-1h3'/>"


NX, NY = IX + IW // 2, IY + 80       # the island's lowest point
FX, FY = -34, 130                    # the leading flaptter, parked
TX = PX + 400                        # Pazu's trumpet pose is parked 400 px to the right of his arm

LAYERS = [
    # --- far, behind the cumulus: the Goliath, lightning in the Dragon's Nest, a cloud streak
    ("goliath", img(art(GOLIATH, OPAL), -90, 64, " class='lp-go'")),
    ("lightning", "<path class='lp-bo' stroke='#fff' d='M243 93.5h2m-2 1h2m-3 1h2m-3 1h2m-3 1h4m-2 1h2m-3 1h2m-3 1h2m-2 1h1m-2 1h1"
                  "m13-11h2m-3 1h2m-3 1h3m-2 1h1m-2 1h1'/>"),
    ("cloud_a", img(cloud([(5, 8, 3), (11, 7, 4), (18, 7, 5), (26, 6, 5), (34, 7, 6), (43, 6, 5), (51, 7, 5),
                           (58, 8, 4), (64, 9, 3)], 70, 14, C[:3], 4), -90, 66, " class='lp-a'")),
    ("middle", img(middle(), 0, 0)),
    # --- the island, bobbing; its core answers Sheeta's crystal
    ("island", "<g class='lp-i'>" + img(island(), IX, IY)
     + f"<path class='lp-z' stroke='#aff' d='M{NX - 3} {NY}.5h6m-4 1h2m-2 1h2M{NX - 6} {NY - 2}.5h1m10 0h1'/></g>"),
    # --- cloud lapping the island's lower left (Laputa is rising out of the cumulus), and a flat-based puff
    ("wisp", img(cloud([(9, 16, 7), (21, 12, 9), (35, 15, 8), (47, 18, 6), (28, 21, 8), (14, 23, 7), (41, 24, 7)],
                       56, 24, C[:4], 7, base=22), 76, 98)),
    ("cloud_b", img(cloud([(9, 14, 7), (20, 10, 9), (33, 12, 8), (44, 15, 6), (27, 16, 8)], 52, 20, C[:4], 6, base=18),
                    -90, 96, " class='lp-b'")),
    # --- gulls wheeling round the crown: two groups on one eight-point orbit, half a lap apart
    ("gulls", "<g class='lp-e'>" + img(flock([(0, 0), (9, -4)]), 137, 30, " class='lp-q'") + "</g>"
     "<g class='lp-e' style='animation-delay:-9.5s'>" + img(flock([(6, -2)]), 150, 44, " class='lp-q'") + "</g>"),
    # --- the Tiger Moth, small and near, crossing in front of the crown
    ("moth", img(moth(), 330, 30, " class='lp-t'")),
    # --- moments: Dola's flaptters climbing past, then Pazu's pigeons
    ("flaptters", f"<g class='lp-mx' style='--x:400px;--y:-40px;--r:36000deg;--d:44s'><g class='lp-my' stroke='#bde'>"
     + wings(FX, FY) + wings(FX - 34, FY - 9) + img(art(FLAP, FPAL), FX, FY, " id='lp-fl'")
     + "<use href='#lp-fl' x='-34' y='-9'/></g></g>"),
    ("pigeons", "<g class='lp-mx' style='--x:-400px;--y:-40px;--r:7200deg;--d:8s'><g class='lp-my'>"
     + img(flock([(0, 0), (9, -4), (17, 3), (25, -6)]), 330, 120, " class='lp-pf'") + "</g></g>"),
    ("cloud_c", img(cloud([(10, 15, 8), (24, 12, 11), (40, 14, 10), (56, 12, 12), (72, 16, 8), (48, 20, 9),
                           (30, 21, 9)], 82, 30, C[:4], 8), -90, 104, " class='lp-c'")),
    # --- Pazu and Sheeta: her braid tip sways, both blink, he glances up at the island
    ("kids", img(kids(), PX, KY)
     + f"<path class='lp-s' fill='#2a2438' d='M{SX} {KY + 14}h1v2h-1z'/>"
     + f"<path class='lp-k' fill='#fca' d='M{PX + 8} {KY + 5}h1v2h-1zm3 0h1v2h-1z'/>"
       f"<path class='lp-k' style='animation-delay:-2s' fill='#fca' d='M{SX + 9} {KY + 6}h1v2h-1zm3 0h1v2h-1z'/>"
     + f"<g class='lp-l'><path fill='#fca' d='M{PX + 8} {KY + 6}h1v1h-1zm3 0h1v1h-1z'/>"
       f"<path fill='#2a2438' d='M{PX + 8} {KY + 4}h1v1h-1zm3 0h1v1h-1z'/></g>"),
    # --- Pazu's near arm, hanging; and, parked off-canvas until its turn, the same arm lifting his trumpet
    ("trumpet", f"<g class='lp-tp'><path fill='#fffaf0' d='M{PX + 2} {KY + 12}h2v3h-2zM{TX + 2} {KY + 9}h1v1h1v2h-2z'/>"
     f"<path fill='#f8cfa0' d='M{PX + 2} {KY + 15}h2v1h-2zM{TX + 1} {KY + 8}h2v1h-2z'/>"
     f"<path fill='gold' d='M{TX - 5} {KY + 5}h1v1h1v1h10v1h-12z'/>"
     f"<path fill='peru' d='M{TX - 5} {KY + 8}h2v1h-2zm5-2h1v1h-1zm2 0h1v1h-1z'/></g>"),
    # --- the crystal: a steady glint, and now and then a glow that the island's core answers
    ("crystal", f"<path class='lp-z' fill='#8ef' d='M{CX} {CY - 2}h1v1h1v1h1v1h-1v1h-1v1h-1v-1h-1v-1h-1v-1h1v-1h1z'/>"
     f"<path class='lp-g' fill='#fff' d='M{CX} {CY}h1v1h-1z'/>"),
    # --- the robot: its eyes pulse, its head nods to her, the fox-squirrel runs from shoulder to head
    ("robot", img(robot(), RX, RY) + "<g class='lp-h'>" + img(art(HEAD, RPAL), HXA, HYA)
     + f"<path class='lp-g' fill='#c63' d='M{HXA + 3} {HYA + 5}h2v2h-2zm5 1h1v1h-1z'/></g>"
     + img(art(FOX, XPAL), RX + 31, RY + 9, " class='lp-u'")),
    # --- small life on the knoll: the nest's bird hops, two butterflies, petals on a breeze
    ("knoll life", "<g class='lp-j'><path fill='#fff' d='M117 138h2v1h2v2h-3v-1h-1z'/><path fill='#fc4' d='M116 139h1v1h-1z'/></g>"
     + "".join(f"<g class='lp-m'{d}><path class='lp-n' fill='{c}' d='M{x} {y}h1v1h1v1h-1v-1h-1z'/></g>"
               for x, y, c, d in ((98, 146, "#fff", ""), (226, 147, "#fc4", " style='animation-delay:-2s'")))
     + "<g class='lp-mx' style='--x:400px;--y:40px;--d:70s'><path class='lp-my' fill='#f58' "
       "d='M-30 98h2v1h-2zm9 6h1v1h-1zm-16 4h2v1h-2zm8 7h1v1h-1zm-13-2h2v1h-2z'/></g>"),
]
SPRITES = "".join(chunk for _, chunk in LAYERS)

CSS = (
    # ambient loops, on a half-second grid
    ".lp-i{animation:lp-i 12s steps(3) infinite alternate}@keyframes lp-i{to{transform:translateY(3px)}}"
    ".lp-a{animation:lp-d 840s -610s steps(420) infinite}.lp-b{animation:lp-d 630s -166s steps(420) infinite}"
    ".lp-c{animation:lp-d 420s -325s steps(420) infinite}@keyframes lp-d{to{transform:translateX(420px)}}"
    ".lp-e{animation:lp-e 24s steps(6) infinite}@keyframes lp-e{from,to{transform:translate(44px,0)}"
    "12.5%{transform:translate(31px,4px)}25%{transform:translate(0,6px)}37.5%{transform:translate(-31px,4px)}"
    "50%{transform:translate(-44px,0)}62.5%{transform:translate(-31px,-4px)}75%{transform:translate(0,-6px)}"
    "87.5%{transform:translate(31px,-4px)}}"
    ".lp-q{animation:lp-q 1s steps(2,jump-none) infinite}@keyframes lp-q{to{transform:rotate(180deg)}}"
    ".lp-g{animation:lp-g 3s steps(3) infinite alternate}.lp-s{animation:lp-g 3s steps(2,jump-none) infinite}"
    "@keyframes lp-g{to{opacity:0}}"
    ".lp-k{opacity:0;animation:lp-k 6s steps(1) infinite}@keyframes lp-k{96%{opacity:1}}"
    ".lp-l{opacity:0;animation:lp-l 14s steps(1) infinite}@keyframes lp-l{50%{opacity:1}75%{opacity:0}}"
    ".lp-h{animation:lp-h 17s steps(1) infinite}@keyframes lp-h{55%{transform:translate(-1px,1px)}70%{transform:none}}"
    ".lp-u{animation:lp-u 23s steps(4) infinite}@keyframes lp-u{60%,94%{transform:none}64%,90%{transform:translate(-7px,-14px)}}"
    ".lp-j{animation:lp-j 4s steps(1) infinite}@keyframes lp-j{75%{transform:translateY(-1px)}}"
    ".lp-m{animation:lp-m 6s steps(6) infinite alternate}.lp-n{animation:lp-n 4s steps(4) infinite alternate}"
    "@keyframes lp-m{to{transform:translateX(12px)}}@keyframes lp-n{to{transform:translateY(-6px)}}"
    # moments on a 120 s cycle, each parked and unchanging outside its slot (--d = when it starts):
    #   6 Pazu's trumpet . 8 pigeons . 30 and 90 crystal . 44 flaptters . 70 petals . 104 lightning
    ".lp-mx{animation:lp-x 120s var(--d) steps(200) infinite}.lp-my{animation:lp-y 120s var(--d) steps(40) infinite}"
    ".lp-w{animation:lp-r 120s var(--d) steps(200) infinite}.lp-pf{animation:lp-r 120s var(--d) steps(40) infinite}"
    "@keyframes lp-x{15%,to{transform:translateX(var(--x))}}@keyframes lp-y{15%,to{transform:translateY(var(--y))}}"
    "@keyframes lp-r{15%,to{transform:rotate(var(--r))}}"
    ".lp-w,.lp-pf,.lp-q{transform-box:fill-box;transform-origin:center}.lp-w{transform-origin:bottom}"
    ".lp-tp{animation:lp-tp 120s steps(1) infinite}@keyframes lp-tp{5%{transform:translateX(-400px)}15%{transform:none}}"
    ".lp-z{opacity:0;animation:lp-z 60s 30s steps(4) infinite}@keyframes lp-z{5%,14%{opacity:1}19%{opacity:0}}"
    ".lp-bo{opacity:0;animation:lp-bo 120s 104s steps(1) infinite}"
    "@keyframes lp-bo{.3%{opacity:1}.5%{opacity:0}.9%{opacity:1}1.4%{opacity:0}}"
    # the airships, 240 s: the Tiger Moth from 60 s, the Goliath from 170 s
    ".lp-t{animation:lp-t 240s 60s steps(200) infinite}@keyframes lp-t{40%,to{transform:translateX(-400px)}}"
    ".lp-go{animation:lp-go 240s 170s steps(210) infinite}@keyframes lp-go{50%,to{transform:translateX(420px)}}"
)
THEME = {
    "position": "center 75%",   # wide panes crop vertically: keep the crown in view (see wide.png)
    "canvas": "#0e1a38", "accent": "#7fe0ff", "overlay": "#0c1a3a",
    "colors": {"sidebar": "#0c1733", "sidebarRowSelected": "#1c3160", "sidebarBorder": "#1b2c52",
               "surface": "#132348", "border": "#22386a", "text": "#eef4ff", "textMuted": "#a6b8d8"},
}
