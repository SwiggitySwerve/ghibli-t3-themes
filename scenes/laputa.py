"""Castle in the Sky: Laputa adrift in a blue noon sky, rising out of towering cumulus. On a grassy
knoll among mossy ruins the garden robot offers a flower to Sheeta while Pazu looks on.

A 320x180 canvas. Nearly everything is a small palette PNG nested in the SVG (a PNG is far cheaper per
pixel than paths, and each layer can move or be passed behind). Back to front:

  draw()      sky bands, a hazed cloud bank and the Dragon's Nest storm far off (the build encodes this one)
  far         the Goliath, lightning in the storm, a high cloud streak, and (in front of the cumulus, behind
              the island) a soldier robot flying home to Laputa
  middle()    cumulus towers, the cloud sea, the knoll with its ruins, a fallen robot, a nest, flowers
  island()    Laputa: crown, trunk and roots, ring walls with arcades, towers and gardens, the dark underside.
              It floats on a slow two-way drift, and its gulls and glowing core ride with it
  near        a wisp lapping the island, two drifting clouds, the Tiger Moth with its lookout kite,
              Dola's flaptters, Pazu's pigeons
  figures     Pazu (who plays his trumpet at dawn) and Sheeta, the robot with its head as a separate
              piece so it can nod, the fox-squirrel
  night       the two washes, then the lights

The chat column covers the middle of the pane (about x 122-198), so the figures stand in the left third
and the island floats in the right third; a small storm cloud hangs in the upper left, and the middle holds
only open sky, a low haze bank, cloud sea and grass.

Motion is CSS transform/opacity only, in whole-pixel steps().
- Ambient loops change on a shared half-second grid, so the image is redrawn about twice a second.
- A "moment" is parked off-canvas (or at opacity 0) and its keyframes hold for most of the cycle, e.g.
  `15%,to{...}`: nothing changes, so nothing is redrawn, until its turn comes round. The pigeons'
  flapping is a half-turn per step driven by the same held keyframes, so it stops while parked too.
- One day and night take 240 s. Everything is painted in daylight colours; night is a multiply wash laid
  over the whole picture (a warm one at dusk and dawn), with the lights that should keep their glow drawn
  above it: stars, moon, the island's windows and core, the crystal, the robot's eyes.
- Moments share that 240 s cycle and each has its own slot in the day or the night; see CSS.
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
RB = ["#9c9c62", "#72764a", "#575d3e", "#424832", "#2a2c2a"]      # robot: lit, body, shade, deep shade, seams
SK = ["#f8cfa0", "#d8996c"]                                       # skin
INK, PINK, GOLD = "#2a2438", "#f08aa0", "#ffd75e"
GY = 152             # ground line under the figures
NIGHT = "#56a"       # what the daylight colours are multiplied by after dark


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


def cloud(lumps, tones, seed, x, y, attrs=""):
    """A drifting cloud as an <image>, its lumps' own origin at (x, y). The bitmap is fitted to the lumps with
    their puffs, so nothing is cut off square by its edge (it shows when a cloud crosses the island's dark keel)."""
    ps = puffs(lumps, seed)
    x0, y0 = (math.floor(min(c[i] - c[2] for c in ps)) for i in (0, 1))
    x1, y1 = (math.ceil(max(c[i] + c[2] for c in ps)) for i in (0, 1))
    cv = Canvas(x1 - x0, y1 - y0)
    volume(cv, [(cx - x0, cy - y0, r) for cx, cy, r in ps], tones, CUTS[:len(tones) - 1], soft=3)
    return img(cv, x + x0, y + y0, attrs)


# ------------------------------------------------------------------ sky and far clouds
def draw():
    """Base layer: the sky, a hazed cloud bank low in the middle, and a compact storm cloud in the upper left,
    above the garden. It sits between the flight lines (Tiger Moth above, soldier and Goliath below)."""
    cv = Canvas(W, H)
    bands(cv, 0, [(16, S[0]), (38, S[1]), (62, S[2]), (86, S[3]), (108, S[4]), (128, S[5]), (H, S[6])])
    volume(cv, puffs([(196, 128, 10), (182, 134, 9), (150, 137, 8),
                      (134, 139, 8), (116, 137, 9)], 9, 2), HAZE, (.45, .22), soft=3, sink=.3, base=146)
    volume(cv, puffs([(48, 56, 8), (59, 50, 12), (72, 53, 10), (81, 58, 6)], 4, 2), STORM, (.45, .22), soft=3,
           sink=.35, base=63)
    return cv


# ------------------------------------------------------------------ cumulus and the knoll
LEFT = [(-12, 44, 10), (0, 52, 10), (8, 66, 12), (24, 62, 11), (34, 82, 10), (-12, 70, 15), (20, 84, 12), (-24, 88, 17), (4, 96, 16),
        (-28, 116, 20), (10, 120, 20), (-30, 150, 24), (10, 152, 24)]
RIGHT = [(224, 128, 11), (208, 133, 9), (322, 102, 14), (268, 102, 12), (294, 104, 15), (270, 124, 16), (302, 126, 18), (326, 130, 12),
         (246, 130, 11), (250, 154, 16), (284, 156, 22), (316, 154, 18)]
SEA = [(40, 156, 12), (62, 153, 9), (84, 157, 13), (108, 153, 10), (128, 156, 13), (150, 152, 8), (166, 157, 13),
       (188, 154, 9), (204, 157, 12), (226, 155, 11), (240, 158, 10)]
RUIN = {"o": ST[0], "a": ST[1], "b": ST[2], "d": ST[3], "g": GR[2], "G": GR[1], "m": GR[3],
        "n": WD[0], "e": C[0], "R": RB[1], "D": RB[3], "k": RB[4], "p": PINK,
        "L": RB[0], "c": RB[2], "t": "#e2c27c", "T": "#b89658"}
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
FALLEN = [                  # a robot long dead: its bullet head on its side, dome to the left, the visor turned up to
                            # the sky round an empty socket, a shoulder ball behind, moss over both, a flower laid on it
    "......p...........",
    "....gGGGg.........",
    "..LLgttttTk.......",
    ".LRttkkkktDk.gGgm.",
    "LRRtTkDDktDk.RRRDD",
    "LRRtTkkkktDkcRRRDD",
    "gRRRttttTDDkcRRDDm",
    "GgRRRRRRRDDgGgRDgm",
    "GgGgGGgggmmGgGgGgm",
]


HAND = [                    # beside it, a mechanical hand reaching up out of the grass: three jointed fingers splayed open,
    "o..o..c.",             # a palm, a ringed wrist and forearm, moss and grass climbing it
    "o..b..cd",
    "ob.b.ccd",
    ".obbbcd.",
    ".obgbcd.",
    ".okkkkd.",
    "..obcd..",
    "..obcm..",
    "..kkkk..",
    "..obcd..",
    ".gobcdm.",
    ".GgbcGgm",
    "gGgGgGgm",
]
CHIPS = [(17, 144, 2, 2), (21, 148, 2, 2), (25, 150, 3, 2), (8, 150, 2, 1)]   # volucite in the ruin and the block


def knoll(x):
    return GY + int(.0003 * (x - 72) ** 2)


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
    for x, d, c in [(118, 7, PINK), (146, 6, GOLD), (183, 3, PINK), (228, 3, GOLD), (88, 7, GOLD), (42, 6, PINK)]:
        cv.set(x, knoll(x) + d, c)
    for x, d in [(96, 3), (124, 8), (138, 4), (172, 5), (196, 8), (222, 4), (26, 5), (8, 8), (70, 6)]:
        cv.paint([".w.", "wyw", ".w."], {"w": C[0], "y": GOLD}, x, knoll(x) + d)
    cv.paint(COLUMN, RUIN, 15, knoll(20) - 13)
    cv.paint(BLOCK, RUIN, 4, knoll(8) - 3)
    cv.paint(FALLEN, RUIN, 211, knoll(219) - 7)
    cv.paint(HAND, RPAL, 230, knoll(234) - 12)
    for x, y, w, h in CHIPS:                      # volucite chips, pale by day (they glow after dark, see lights)
        cv.rect(x, y, w, h, "#a8dce8")
    return cv


# ------------------------------------------------------------------ the island
IW, IH = 104, 84
IX, IY = 202, 30        # top left of its float: it wanders 7 px right and 5 px down from here


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
    # bright lips where the two streams pour over the foot of the lowest ring (see stream())
    cv.paint(["lwwwwl", "wwwwww"], {"w": C[0], "l": S[6]}, 30, 61)
    cv.paint(["lwwl", "wwwl"], {"w": S[6], "l": S[5]}, 69, 61)
    return cv


# ------------------------------------------------------------------ the robot
RPAL = {"o": RB[0], "b": RB[1], "c": RB[2], "d": RB[3], "k": RB[4], "g": GR[2], "G": GR[1], "m": GR[3],
        "t": "#e2c27c", "T": "#b89658", "y": GOLD, "r": "#e8483c", "f": C[0], "p": PINK, "s": GR[2]}
HEAD = [                    # a small bullet helmet; a broad sand visor holds one big ringed eye and a small port
    "...obbc...",
    "..obbbbc..",
    ".oobbbbcd.",
    ".obbbbbcd.",
    "obttttttcd",
    "ottttkkktd",
    "otTttkyktd",
    "otkttkkktd",
    "obttttttcd",
    ".obbbbbcd.",
    "..cbbbcd..",
]
BODY = [                    # from the neck down: a great round torso capped with moss, ball shoulders, long
                            # segmented arms (the near one holds out a flower), hip block, short legs, flat feet
    "............................kkkkk",
    "............................obbcd",
    ".............gGGg.......gGGGGGGgggmmm.......Gggm",
    "............gGGggm...gGGGGGgGGGGggggmmmm...gGggmm",
    "............oGgbcd..bGGGgGGGGgGGgggggmmmc..ogmmcd",
    "............oobbcd.ooGGggGgGGgbgGggggmgmmc.obbccd",
    "............oobbcdoooogGgbbgGgbbbggggbmmgmdobbccd",
    ".............obcd.ooooogbbbbgbbbbbggbbbmmbd.bccd",
    "............ddddd.oooooobbbbbbbbbbgbbbbmbcd.ddddd",
    "............obbcd.oooooobbbbbbbbbbbbbbbbccd.obbcd",
    "............obbcd.oooocbbbbbbbbbbbrbbbdcccd.obbcd",
    "............obbcd.ooocbcbbbbbbbbbbbbbdcdccd.obbcd",
    "............ddddd.ooocbcbbbbbbbbbbbbbdcdccd.ddddd",
    "............obbcd.oobcbcbbbbbbbbbbbbcdcdccd.obbcd",
    "............obbcd..bbbcbbbbbbbbbbbbcccdccd..obbcd",
    "..f.........obbcd..bbbbbbbbbbbbbbbcccccccd..obbcd",
    ".fpf........ddddd...bbbbbbbbbbbbbcccccccd...ddddd",
    "..f.........obbcd...bbbbbbbbbbbbccccccccd...obbcd",
    "..s.........obbcd....bbbbbbbbbbccccccccd....obbcd",
    "..s.........obbcd....bbbbbbbbbcccccccccd....obbcd",
    "o.s.o...Gg..kkkkk.....bbbbbbbcccccccccd.....kkkkk",
    "o.s.ookogmdoooooo......bbbbbcccccccccd......obbcd",
    "obbbbbkbbbdbbbbbb.......bbbcccccccccd.......obbcd",
    "obdbbbkbbbdbbbbbb.........kkkkkkkkk.........obbcd",
    "cbdbbckcccdcccccc.......oobbbbbbccccd.......ddddd",
    ".cdccdkddddddddd........oobbbbbbccccd.......obbbcd",
    ".......................dddddbccccddddd......obbbcd",
    ".......................obbcd.....obbcd......obbbcd",
    ".......................obbcd.....obbcd......obbbcd",
    ".......................obbcd.....obbcd......dddddd",
    ".......................ddddd.....ddddd......obbbcd",
    ".......................obbcd.....obbcd......obbbcd",
    ".......................obbcd.....obbcd......obbbcd",
    ".......................obbcd.....obbcd......obbbcd",
    "......................kkkkkk.....kkkkkk.....kkkkkk",
    "......................obbbcd.....obbbcd....obbbbcd",
    "......................obbbcd.....obbbcd....obbbbcd",
    "......................obbbcd.....obbbcd....o.b.b.d",
    "......................obbbcd.....obbbcd....o.b.b.d",
    "......................dddddd.....dddddd....c.c.c.d",
    ".....................obbbbcd.....obbbbcd...o.b.b.d",
    ".....................obbbbcd.....obbbbcd.....b.b",
    ".....................obbbbcd.....obbbbcd",
    ".....................obbbbcd.....obbbbcd",
    ".....................obbbbcd.....obbbbcd",
    ".....................ddddddd.....ddddddd",
    "....................obbbbbcd.....obbbbbcd",
    "..................obbbbbbbcd.....obbbbbbbcd",
    ".................obbbbbbbbcd.....obbbbbbbbcd",
]
RX, RY = 67, GY - 60                    # the robot is 50 x 60; its head is a separate piece so it can nod
HXA, HYA = RX + 25, RY                  # the head, absolute


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
PAZU = [                    # his near arm is a sprite, so it can hang or lift the trumpet. Aviator goggles on his cap
    "....tttttt.....",
    "...tttttttttt..",
    "..tthhkGgkGgk..",
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
        "u": "#4f7f78", "U": "#35605e", "g": "#5f9fb0", "G": "#9cd0dc"}
SX, PX = 52, 36                      # Pazu close beside Sheeta, so narrow panes keep both (see THEME position)
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
FLAP = [                    # a flaptter, nose to the right. The tall bell-shaped rust engine pod is most of it: a
    "................hhhh......",    # rounded top, a nose sloping down to the keel's front, a dark porthole on the
    "..............hhhhhhhH....",    # nose, three vent slots in its side, a seam along its base and a knob at each
    ".............hhhhhhhhHH...",    # lower corner. Under it is a short, deep, angular red keel that runs back just
    "............hhhhhhhhkkH...",    # far enough to be a footboard, where Dola crouches at the handlebar with her
    "pp..ss.....hhhhhhhhhkkHH..",    # pink braids streaming behind
    ".pppsss....hhkhkhkhhhhHH..",
    "....bbbb...hhkhkhkhhhhHHH.",
    "....bbbbbHHhhkhkhkhhhhHHH.",
    "....bbbb...hhhhhhhhhhhHHHH",
    ".....bbb..oHHHHHHHHHHHHHHo",
    "...rrrrrrrrrrrrrrrrrrrrrr.",
    ".....RRRRRRRRRRRRRRRRRRR..",
    "........RRRRRRRRRRRRRR....",
]
FPAL = {"h": "#d47858", "H": "#a85440", "o": "#e89a78", "k": WD[1], "r": "#d03a3c", "R": "#a02c38", "p": PINK,
        "s": SK[0], "b": "#3a4a8a"}
FOX = [
    ".e.e....",
    ".ooo..tt",
    "okoo.tTt",
    ".wooooTt",
    "..o.o...",
]
XPAL = {"o": "#f0a850", "e": "#c87830", "t": "#f0a850", "T": "#c87830", "k": INK, "w": C[0]}
BPAL = {"w": "#ffffff", "k": "#3c4a78"}
PERCH = [                   # the nest's bird, a little bluebird, perched facing right
    "...bb.",
    "..bkbY",
    ".Bbbww",
    "BB.ww.",
]
GLIDE = [                   # the same bird gliding, wings raised
    "..B.....",
    "..BB....",
    "...BB.bb",
    "BBbbbbkY",
    "...www..",
]
DPAL = {"b": "#4a70c8", "B": "#2c3e7c", "w": "#ffffff", "Y": "#ffcc44", "k": INK}
BX, BY = 19, 136                     # the bird on its nest; on the robot's forearm it is 53 px right, 16 up


def stream(n):
    """Water spilling off the island's lowest ring, n px wide (lit left, shaded right): a broken 6 px pattern of
    streaks, with gaps so it reads as falling water rather than a cord."""
    pal = {"w": C[0], "l": S[6], "d": S[4]}
    return art([r[-n:] for r in ["wwl.", "wwld", "lw.d", "wl.l", ".wwl", "wlwd"]] * 5, pal)


# spray blooming where each stream meets the cloud: it fans out at the foot (the cloud in front hides its base)
MIST = art(["...w.w...", "..wlwlw..", ".wwlwwwl.", "wlwwwwlww", ".wwwwwww.", "lwwwlwwwl"],
           {"w": C[0], "l": C[1]})


def moth():
    cv = art(MOTH, MPAL)
    for x in (13, 30):      # two engines on outriggers, their propellers a pale blur seen edge-on across the keel
        cv.rect(x, 11, 1, 6, "#e4eefa")
        cv.rect(x + 1, 13, 5, 2, WD[1])
    return cv


def flock(pts):
    """Birds, wings up, placed point-symmetrically about the image centre. Turning the image half a turn
    about that centre gives the same flock with wings down, so one PNG is both frames of the flap. Each
    bird is a white M over a dark body pixel: it reads over sky and the crown, where the gulls circle."""
    mx, my = max(abs(x) for x, y in pts), max(abs(y) for x, y in pts)
    cv = Canvas(2 * mx + 7, 2 * my + 3)
    for x, y in pts + [(-x, -y) for x, y in pts if (x, y) != (0, 0)]:
        cv.paint([".ww.ww.", "w..w..w", "...k..."], BPAL, mx + x, my + y)
    return cv


def fan(x, y, far=False):
    """A flaptter's beating wings on one side, for the craft whose image is at (x, y): a fan of two pale streaks, one
    steep and one shallow, from the root, where the pod's base meets the keel at the middle of the hull. The far
    fan slants up and forward and is drawn behind the hull, fainter, so only what sticks out past the pod shows;
    the near one is its mirror image through the root, down and back, drawn over the keel and footboard. Their
    shape never changes: they only buzz a pixel to and fro (see lp-mw)."""
    if far:
        return f"M{x + 16} {y + 9}.5h1{'m0-1h1' * 8}m-8 8h3{'m0-1h3' * 3}"
    return f"M{x + 15} {y + 10}.5h1{'m-2 1h1' * 6}m2-6h3{'m-6 1h3' * 3}"


SOLDIER = [                 # a soldier robot in flight (drawn banking west, used mirrored): its arms are its wings, a row
    "........................bb.b",      # of lavender fins under each; egg body with the red chest dot, visor head,
    ".....................kbkbkb.",      # legs trailing
    "..........bbb.......bkbkvv..",
    "..........trtb....kbkbvvv...",
    "..........bttb.bbbkbvvv.....",
    "...........kbbbbbbbvv.......",
    "......bkbkbbbbbrbbbb........",
    "...bkbkbkvvbbbbbbbbk........",
    "bbkbkbvvvv.bbbbbbbkk........",
    "b.bb.vvvv...kbbbbkkbk.......",
    "..................kbkbkb....",
    "....................kkbkbb..",
    "......................bb.bb.",
]
VPAL = {"b": RB[1], "k": RB[3], "v": "#b4a4e6", "t": "#e2c27c", "r": "#ff4433"}     # the garden robot's body tones
VX, VY = -360, 0                     # parked off-canvas to the west; its flight ends at 240, 80, behind the island


def windows():
    """Some of the arcade openings on the island's sunlit side, as one stroked path: lit after dark."""
    d, px, py = "", 0, 0
    for hw, y0, n, ks in ((13, 32, 2, (-3, 0, 2)), (25, 38, 3, (-4, -2, -1, 1, 3)), (37, 45, 3, (-4, -3, -1, 0, 2, 4)),
                          (47, 52, 4, (-4, -2, -1, 1, 2, 4))):
        for k in ks:
            x = IX + int(round(IW // 2 + hw * math.sin(math.radians(k * 10.5)) - 1)) + 1
            y = IY + y0 + 3
            d += f"m{x - px} {y - py}v{n}" if d else f"M{x} {y}v{n}"
            px, py = x, y + n
    return d.replace(" -", "-")


def oval(cx, cy, rx, ry):
    """A pixel ellipse as one stroked path of row runs (stroke width 1, on the half-pixel)."""
    d, px, py = "", 0, 0
    for dy in range(-ry, ry + 1):
        hw = int(round(rx * math.sqrt(1 - (dy / (ry + .5)) ** 2)))
        x, y = cx - hw, cy + dy
        d += f"m{x - px} {y - py}h{2 * hw}" if d else f"M{x} {y}.5h{2 * hw}"
        px, py = x + 2 * hw, y
    return d.replace(" -", "-")


def beam():
    """The crystal's beam pointing to Laputa, rising 1 px every 7: solid out to the chat column, then dashed, stopping
    short of the island. It is drawn with the lights (above the night wash), so it leaves out the pixels the robot
    covers, which puts it behind him."""
    d, px, py = "", 0, 0
    for k in range(20):
        y = CY - 2 - k
        r = y - RY - 11
        xs = [x for x in range(CX + 4 + 7 * k, CX + 11 + 7 * k) if (k < 8 or k % 2 == 0) and not
              (0 <= r < len(BODY) and 0 <= x - RX < len(BODY[r]) and BODY[r][x - RX] != ".")]
        for x in xs:
            if x - 1 in xs:
                continue
            n = next(i for i in range(len(xs) + 1) if x + i not in xs)
            d += f"m{x - px} {y - py}h{n}" if d else f"M{x} {y}.5h{n}"
            px, py = x + n, y
    return d.replace(" -", "-")


NX, NY = IX + IW // 2, IY + 80       # the island's lowest point
FX, FY = -34, 70                     # the leading flaptter, parked; they glide down over the robot's head
TX = PX + 400                        # Pazu's trumpet pose is parked 400 px to the right of his arm

LAYERS = [
    # --- far, behind the cumulus: the Goliath (with searchlights after dark), lightning in the Dragon's Nest,
    #     a cloud streak
    ("goliath", "<g class='lp-go'>" + img(art(GOLIATH, OPAL), -90, 64)
     # its two searchlights sweep slowly to and fro, out of step
     + "<g class='lp-N' fill='#ffd' fill-opacity='.22'><path class='lp-sw' style='transform-origin:-62px 75px' d='M-63 75h2l3 22h-8z'/>"
       "<path class='lp-sw' style='transform-origin:-22px 75px;animation-delay:-11s' d='M-23 75h2l3 22h-8z'/></g></g>"),
    ("lightning", f"<path class='lp-bo' stroke='#dde' stroke-opacity='.5' d='{oval(68, 51, 10, 4)}'/>"
                  "<path class='lp-bo' stroke='#fff' d='M64 47.5h2m-2 1h2m-3 1h2m-3 1h2m-3 1h4m-2 1h2m-3 1h2m-3 1h2m-2 1h1m-2 1h1"
                  "m13-11h2m-3 1h2m-3 1h3m-2 1h1m-2 1h1'/>"),
    ("cloud_a", cloud([(5, 8, 3), (11, 7, 4), (18, 7, 5), (26, 6, 5), (34, 7, 6), (43, 6, 5), (51, 7, 5),
                       (58, 8, 4), (64, 9, 3)], C[:3], 4, -90, 66, " class='lp-a'")),
    ("middle", img(middle(), 0, 0)),
    # --- a soldier robot comes home at dusk, behind the island: in fast from the left, high over the garden, down
    #     across the sky and in behind Laputa's walls, where it stays hidden (at every point of the island's drift)
    #     until the loop comes round. 3 px a step; its fins flutter on Sheeta's braid beat
    ("soldier", "<g class='lp-mx' style='--x:600px;--y:80px;--d:46s'><g class='lp-my'>"
     + img(art([r[::-1] for r in SOLDIER], VPAL), VX, VY)
     + f"<path class='lp-s' fill='#b4a4e6' d='M{VX + 20} {VY + 10}h3v1h-3zm-15-5h3v1h-3z'/></g></g>"),
    # --- the island, adrift (lp-o sideways, lp-i up and down); its core answers Sheeta's crystal, and the
    #     gulls wheeling round the crown go with it: two groups on one eight-point orbit, half a lap apart.
    #     They roost after dark (lp-R) and stay down until Pazu's doves have crossed at dawn
    ("island", "<g class='lp-o'><g class='lp-i'>" + img(island(), IX, IY)
     # water spilling off the lowest ring, down past the dark underside into the cloud (a window onto a moving strip)
     + "".join(f"<svg x='{IX + x}' y='{IY + 63}' width='{w}' height='{n}'>{img(stream(w), 0, -6, cls)}</svg>"
               for x, w, n, cls in ((31, 4, 22, " class='lp-wf'"), (70, 3, 18, " class='lp-wf' style='animation-delay:-.5s'")))
     + f"<g class='lp-ms'>{img(MIST, IX + 29, IY + 74)}{img(MIST, IX + 67, IY + 71)}</g>"
     + "<g class='lp-R'><g class='lp-e'>" + img(flock([(0, 0), (9, -4)]), 243, 28, " class='lp-q'") + "</g>"
     "<g class='lp-e' style='animation-delay:-9.5s'>" + img(flock([(6, -2)]), 256, 42, " class='lp-q'") + "</g></g></g></g>"),
    # --- cloud lapping the island's lower left (Laputa is rising out of the cumulus), and a drifting puff
    ("wisp", cloud([(9, 16, 7), (21, 12, 9), (35, 15, 8), (47, 18, 6), (28, 19, 7)], C[:4], 7, 189, 98)),
    ("cloud_b", cloud([(9, 14, 7), (20, 10, 9), (33, 12, 8), (44, 15, 6), (27, 16, 8)], C[:4], 6, -90, 96,
                      " class='lp-b'")),
    # --- the Tiger Moth, small and near, crossing in front of the crown
    ("moth", img(moth(), 330, 30, " class='lp-t'")),
    # --- moments: Dola's flaptters gliding down past, then Pazu's pigeons
    ("flaptters", "<g class='lp-my' style='--x:400px;--y:40px;--d:10s' stroke='#bde'>"
     + f"<g class='lp-mw' opacity='.5'><path id='lp-ff' d='{fan(FX, FY - 8, True)}'/><use href='#lp-ff' x='-34' y='-9'/></g>"
     + "<g class='lp-mx'>" + img(art(FLAP, FPAL), FX, FY - 8, " id='lp-fl'") + "<use href='#lp-fl' x='-34' y='-9'/></g>"
     + f"<g class='lp-mw' opacity='.7'><path id='lp-fn' d='{fan(FX, FY - 8)}'/><use href='#lp-fn' x='-34' y='-9'/></g></g>"),
    ("pigeons", "<g class='lp-mx' style='--x:-400px;--y:-40px;--r:7200deg;--d:184s'><g class='lp-my'>"
     + img(flock([(0, 0), (9, -4), (17, 3), (25, -6)]), 330, 110, " class='lp-pf'") + "</g></g>"),
    ("cloud_c", cloud([(10, 15, 8), (24, 12, 11), (40, 14, 10), (56, 12, 12), (72, 16, 8), (48, 20, 9),
                       (30, 21, 9)], C[:4], 8, -90, 104, " class='lp-c'")),
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
     # the trumpet: a 3 px flared bell, a darker underside (broken by his hand) and a valve
     f"<path fill='gold' d='M{TX - 6} {KY + 5}h1v1h1v1h11v1h-13zm5-1h1v1h-1z'/>"
     f"<path fill='darkgoldenrod' d='M{TX - 6} {KY + 8}h7v1h-7zm9 0h3v1h-3zm-2-2h1v1h-1zM{TX - 6} {KY + 9}h1v1h-1z'/></g>"),
    # --- the robot: its head nods to her, the fox-squirrel runs from shoulder to head
    ("robot", img(art(BODY, RPAL), RX, RY + 11) + "<g class='lp-h'>" + img(art(HEAD, RPAL), HXA, HYA)
     + "</g>" + img(art(FOX, XPAL), RX + 43, RY + 8, " class='lp-u'")),
    # --- small life on the knoll: the nest's bird (it hops, and flies over to perch on the robot's arm until the
    #     fox-squirrel lands there), two butterflies
    ("knoll life", f"<g class='lp-bd' style='transform-origin:{BX + 3}px {BY + 2}px'><g class='lp-j'>"
     + img(art(PERCH, DPAL), BX, BY, " class='lp-bp'") + "</g>" + img(art(GLIDE, DPAL), BX - 1, BY - 2, " class='lp-bg'") + "</g>"
     + "".join(f"<g class='lp-m'{d}><path class='lp-n' fill='{c}' d='M{x} {y}h1v1h1v1h-1v-1h-1z'/></g>"
               for x, y, c, d in ((22, 146, "#fc4", ""), (204, 151, "#f8a", " style='animation-delay:-2s'")))),
    # --- night: a multiply wash over everything, and a warm one at dusk and dawn (both change only then)
    ("night", f"<rect class='lp-N lp-B' width='{W}' height='{H}' fill='{NIGHT}'/>"
              f"<rect class='lp-W lp-B' width='{W}' height='{H}' fill='#fa6'/>"),
    # --- what the night does not dim. After dark: stars and a moon in the open sky, the island's windows.
    #     Always: the island's core and Sheeta's crystal, the robot's eyes (so by night they glow)
    ("lights", "<g class='lp-N'><path stroke='#fff' d='M46 13.5h1m56 45h1m14-13h1m19-26h1m23 21h1m18-14h1m-45 31h1m34 23h1"
               "m17-22h1m23-46h1m45 4h1m36-8h1'/>"
               "<path fill='#ffe' d='M101 29h5v1h2v1h1v2h1v5h-1v2h-1v1h-2v1h-5v-1h-2v-1h-1v-2h-1v-5h1v-2h1v-1h2z'/>"
               # the moon's craters and its shaded lower limb
               "<path stroke='#dda' d='M102 33.5h2m1 3h1m-6 2h2M109.5 33v5m-1 0v2M106 40.5h2m-7 1h5'/>"
               # volucite in the ruin's stones, waking when the crystal glows by night (Uncle Pom's mine)
               # steady through the night, flaring with a halo when the crystal glows
               "<path fill='#6ce' d='" + "".join(f"M{x} {y}h{w}v{h}h-{w}z" for x, y, w, h in CHIPS) + "'/>"
               "<g class='lp-z'><path fill='#8ef' fill-opacity='.3' d='"
               + "".join(f"M{x - 1} {y - 1}h{w + 2}v{h + 2}h-{w + 2}z" for x, y, w, h in CHIPS) + "'/>"
               "<path fill='#cff' d='" + "".join(f"M{x} {y}h{w}v{h}h-{w}z" for x, y, w, h in CHIPS) + "'/></g>"
               # and the fallen robot's empty eye stirs with it
               "<path class='lp-z' stroke='#f53' d='M217 155.5h2'/>"
               # the crystal's beam pointing the way to Laputa: once a cycle, faint (see beam())
               f"<path class='lp-v' stroke='#aff' stroke-opacity='.35' d='{beam()}'/></g>"
               # a soft glow where the roots cradle the great crystal under the island: a static shape, lit with the
               # night (by day the cumulus rises over the dome's tip and it would tint the cloud)
               f"<g class='lp-o'><g class='lp-i'><g class='lp-N'><path stroke='#7df' stroke-opacity='.25' d='{oval(NX, NY - 5, 13, 3)}'/>"
               f"<path stroke='#7df' stroke-opacity='.3' d='{oval(NX, NY - 4, 7, 2)}'/></g>"
               f"<path class='lp-N' stroke='#fc6' stroke-width='2' d='{windows()}'/>"
               f"<path class='lp-N' stroke='#aff' d='M{NX - 2} {NY}.5h4'/>"
               f"<path class='lp-z' stroke='#aff' d='M{NX - 3} {NY}.5h6m-4 1h2m-2 1h2M{NX - 6} {NY - 2}.5h1m10 0h1'/></g></g>"
               f"<g class='lp-h'><path class='lp-g' fill='#f84' d='M{HXA + 6} {HYA + 6}h1v1h-1zm-4 1h1v1h-1z'/></g>"),
    # --- the crystal: a steady glint, and now and then a glow that the island's core answers
    ("crystal", f"<path class='lp-z' fill='#8ef' d='M{CX} {CY - 2}h1v1h1v1h1v1h-1v1h-1v1h-1v-1h-1v-1h-1v-1h1v-1h1z'/>"
     f"<path class='lp-g' fill='#fff' d='M{CX} {CY}h1v1h-1z'/>"),
]
SPRITES = "".join(chunk for _, chunk in LAYERS)


def keys(name, pts):
    """@keyframes on the 240 s cycle from (t seconds, x, y, mirrored, steps): each pose holds from t (the element runs
    steps(1)), unless `steps` is given, when it moves to the next pose in that many whole steps."""
    out = ""
    for t, x, y, m, n in pts:
        tr = f"translate({x}px,{y}px)" + ("scaleX(-1)" if m else "")
        out += f"{round(t / 2.4, 3):g}%{{transform:{tr}" + (f";animation-timing-function:steps({n})" if n else "") + "}"
    return f"@keyframes {name}{{{out}}}"


# the fox-squirrel: runs along the robot's shoulders, leaps to its forearm (scaring off the bird) and on to Sheeta's
# head, rides there through the night, comes home after dawn, and once pops up onto the robot's head
FOXK = keys("lp-u", [(0, 0, 0, 0, 0), (34, 0, 0, 0, 10), (36, -30, 0, 0, 0), (36.25, -35, 5, 0, 0), (36.5, -39, 19, 0, 0),
                     (38, -46, 14, 0, 0), (38.25, -54, 19, 0, 0), (198, -54, 19, 1, 0), (198.25, -46, 14, 1, 0),
                     (198.5, -39, 19, 1, 0), (200, -35, 5, 1, 0), (200.25, -30, 0, 1, 10), (202.25, 0, 0, 1, 0),
                     (203, 0, 0, 0, 0), (226, 0, 0, 0, 4), (227, -16, -12, 0, 0), (231, -16, -12, 0, 4), (232, 0, 0, 0, 0)])
# the nest's bird: on the robot's forearm at the start of the cycle; flies home when the fox lands there (36.5 s),
# and back out to the arm once the fox is home again (212 s)
BIRDK = keys("lp-bd", [(0, 53, -16, 0, 0), (36.5, 53, -16, 1, 10), (39, 26, -26, 1, 10), (41.5, 0, 0, 1, 0),
                       (212, 0, 0, 0, 10), (214.5, 26, -28, 0, 10), (217, 53, -16, 0, 0), (240, 53, -16, 0, 0)])

CSS = (
    # ambient loops, on a half-second grid
    # the island's float: 5 px down and back in 30 s, 7 px across and back in 48 s (a 5:8 figure that closes
    # every 4 min). steps(n) with `alternate` rests two beats at each end, which eases the turn.
    ".lp-i{animation:lp-i 15s -7.5s steps(6) infinite alternate}@keyframes lp-i{to{transform:translateY(6px)}}"
    ".lp-o{animation:lp-o 24s -12s steps(8) infinite alternate}@keyframes lp-o{to{transform:translateX(8px)}}"
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
    ".lp-u{transform-origin:114px 102.5px}.lp-u,.lp-bd{animation:lp-u 240s steps(1) infinite}.lp-bd{animation-name:lp-bd}"
    + FOXK + BIRDK +
    ".lp-bg{opacity:0;animation:lp-bg 240s steps(1) infinite}@keyframes lp-bg{15.208%{opacity:1}17.292%{opacity:0}88.333%{opacity:1}90.417%{opacity:0}}"
    ".lp-bp{animation:lp-bp 240s steps(1) infinite}@keyframes lp-bp{15.208%{opacity:0}17.292%{opacity:1}88.333%{opacity:0}90.417%{opacity:1}}"
    # the island's water, 2 px a half-second; the Goliath's searchlights sweep 28 degrees in 22 s
    ".lp-wf{animation:lp-wf 1.5s steps(3) infinite}@keyframes lp-wf{to{transform:translateY(6px)}}"
    ".lp-ms{animation:lp-ms 2s steps(2,jump-none) infinite alternate}@keyframes lp-ms{to{transform:translateY(-1px)}}"
    ".lp-sw{animation:lp-sw 22s steps(22) infinite alternate}@keyframes lp-sw{from{transform:rotate(-14deg)}to{transform:rotate(14deg)}}"
    ".lp-j{animation:lp-j 4s steps(1) infinite}@keyframes lp-j{75%{transform:translateY(-1px)}}"
    ".lp-m{animation:lp-m 6s steps(6) infinite alternate}.lp-n{animation:lp-n 4s steps(4) infinite alternate}"
    "@keyframes lp-m{to{transform:translateX(12px)}}@keyframes lp-n{to{transform:translateY(-6px)}}"
    # one day and night every 240 s. Night is a multiply wash stepping in 60-77 s and out 170-187 s, with the
    # night-only lights on the same fade; the warm wash runs twice a cycle, peaking at 62 s (dusk) and 182 s (dawn)
    ".lp-B{mix-blend-mode:multiply}"
    ".lp-N{opacity:0;animation:lp-N 240s steps(8) infinite}@keyframes lp-N{25%{opacity:0}32%,71%{opacity:1}78%{opacity:0}}"
    ".lp-W{opacity:0;animation:lp-W 120s steps(5) infinite}@keyframes lp-W{42%{opacity:0}52%{opacity:.7}62%{opacity:0}}"
    # the gulls roost with nightfall and come back once Pazu's doves have crossed (202 s)
    ".lp-R{animation:lp-R 240s steps(8) infinite}@keyframes lp-R{25%,87%{opacity:1}32%,84%{opacity:0}}"
    # moments on that cycle, each parked and unchanging outside its slot (--d = when it starts):
    #   day    0 the bird perched on the robot's arm . 10 flaptters . 33 crystal and core . 34 the fox-squirrel runs to
    #          Sheeta's head (36.5 the bird flies home to its nest)
    #   dusk   46 the soldier robot flies home, left to right (on screen from 56, gone behind Laputa by 64)
    #   night  74 Goliath, searchlights sweeping . 93 and 153 crystal, core, ruin stones and the fallen robot's eye
    #          (93 also the beam) . 104 lightning
    #   dawn   182 Pazu's trumpet . 184 pigeons (the gulls stay roosted until 202) . 198 the fox comes home
    #   day    190 Tiger Moth . 212 the bird flies back to the robot's arm . 213 crystal and core . 224 lightning
    #          . 226 the fox pops up on the robot's head
    ".lp-mx{animation:lp-x 240s var(--d) steps(200) infinite}.lp-mw{animation:lp-x 240s var(--d) steps(400) infinite}.lp-my{animation:lp-y 240s var(--d) steps(40) infinite}"
    ".lp-pf{animation:lp-r 240s var(--d) steps(40) infinite}"
    "@keyframes lp-x{7.5%,to{transform:translateX(var(--x))}}@keyframes lp-y{7.5%,to{transform:translateY(var(--y))}}"
    "@keyframes lp-r{7.5%,to{transform:rotate(var(--r))}}"
    ".lp-pf,.lp-q{transform-box:fill-box;transform-origin:center}"
    ".lp-tp{animation:lp-tp 240s 176s steps(1) infinite}@keyframes lp-tp{2.5%{transform:translateX(-400px)}7.5%{transform:none}}"
    ".lp-z{opacity:0;animation:lp-z 60s 30s steps(4) infinite}@keyframes lp-z{5%,14%{opacity:1}19%{opacity:0}}"
    # the crystal's beam: lp-z's 93 s glow (the first after dusk) stretched over the 240 s cycle
    ".lp-v{opacity:0;animation:lp-v 240s 90s steps(4) infinite}@keyframes lp-v{1.25%,3.5%{opacity:1}4.75%{opacity:0}}"
    ".lp-bo{opacity:0;animation:lp-bo 120s 104s steps(1) infinite}"
    "@keyframes lp-bo{.3%{opacity:1}.5%{opacity:0}.9%{opacity:1}1.4%{opacity:0}}"
    # the Tiger Moth's flyby: 30 s gliding in over the right third, 12 s across the middle,
    # 30 s gliding out over the left third, a whole pixel or two a step. The Goliath crosses by night
    ".lp-t{animation:lp-t 240s 190s steps(100) infinite}"
    "@keyframes lp-t{12.5%{translate:-100px}17.5%{translate:-300px}30%,to{translate:-400px}}"
    ".lp-go{animation:lp-go 240s 74s steps(210) infinite}@keyframes lp-go{50%,to{transform:translateX(420px)}}"
)
THEME = {
    "position": "35% 75%",      # wide panes crop vertically: keep the crown in view (see wide.png); narrow ones
                                # crop sideways, and 35% keeps Pazu and his trumpet's bell in an app-sized pane, at the cost
                                # of the island's shaded edge
    "canvas": "#0e1a38", "accent": "#7fe0ff", "overlay": "#0c1a3a",
    "colors": {"sidebar": "#0c1733", "sidebarRowSelected": "#1c3160", "sidebarBorder": "#1b2c52",
               "surface": "#132348", "border": "#22386a", "text": "#eef4ff", "textMuted": "#a6b8d8"},
}
