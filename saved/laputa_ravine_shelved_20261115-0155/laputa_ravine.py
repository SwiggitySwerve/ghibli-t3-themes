"""Castle in the Sky, second view: Slag Ravine and the whole road home, a day and a night.

One wide, map-like view from high over the near rim of the ravine. The map is the film's: the miners' terrace
low on the green dome; the path that leaves the head of its street, climbs round a hairpin, passes the old
mill's roofless gables and rusty pipe on one side and the cottage and the pink-brick ruin on the other, and
ends at the door of Pazu's house on the crown of the hill; the ravine falling away to the west, the old town
set into its far wall.

A chat column covers the middle of the pane (about 38-62% of the width, x 122-198), so that band gets only
the depths of the gorge, mist, the grass of the dome and the hairpin of the path. What matters stands in the
outer thirds:

  left    the ravine: its far wall running away north, carved rock - masses that jut and recede, lit faces,
          shadowed sides, deep cracks, ledges and rims that catch the light - with three small clusters of
          old house fronts on it, two bridges far below, Uncle Pom on the plank ledge of his mine; on the
          near rim the tall wooden house hung off the rock and two rusty pipes; Laputa floating large over
          the ravine, Fortress Tedis small on the skyline beside it
  right   top to bottom: Pazu's house on the skyline (the brick block, the round kiln turret with doves on
          its rim, the slate-roofed shack and its white stovepipe); the mill ruins, the brick ruin and the
          cottage beside the path; the terrace (two rows of joined houses in a crescent round the hill: cream
          stone, orange tiles, a chimney each, walled back gardens with outbuildings and washing, a redder cross-wing
          across the uphill end); the road on down the hill

Perspective: the ravine and the terrace are solids in one 3D space (metres; see "the map" below), drawn
through one camera (eye at the origin looking along +Y, verticals upright, horizon on row HZ). The far wall
is one plane and the fronts set into it are placed in metres along it; the terrace is gabled boxes laid along
a curving path, 90-140 m off and some 60 m below the eye. Up the hill beyond it, where a house is a dozen pixels,
the ruins and Pazu's house are pixel art set on the path (drawn straight on the screen), smaller with distance
except that his house is drawn large enough to read as the landmark it is.

Layers, back to front (320x180):
  draw()      the base PNG: sky, clouds, Tedis, the far wall with its town, bridges and Pom, the dome with its
              shade, rock, shrubs and flowers, the path, the ruins, the terrace, Pazu's house, the hanging house
  sky         Laputa (bobbing), the Goliath, the Tiger Moth
  town        chimney smoke, Dola's sons on two flaptters, Pazu's doves, Pazu and Sheeta on the path, Pazu
              on his roof with the trumpet
  light       night (one multiply wash), the warm wash of dusk and dawn, then what the night does not dim:
              stars and moon, lit windows, Pom's lantern, the Goliath's lights and searchlights, the crystal
              veins, and Sheeta drifting down

One 240 s cycle (1% = 2.4 s). The loop point is just after sunrise, so the theme opens on a bright morning:
   0-  8%  sunrise: the last warm light fades; Pazu stands on his roof and plays his trumpet (1-7%); his
           doves rise from the turret and fly off over the gorge towards Laputa (1.5-8%)
   8- 44%  day: the Tiger Moth crosses the sky (8-42%); two flaptters climb out of the gorge past the hanging
           house (16-24%); Pazu and Sheeta run up the path from the terrace to the house (25-35%); the doves
           come home (29-35.5%)
  44- 51%  dusk: the Goliath comes over (44-84%), searchlights swinging across the hill; the warm wash peaks
           at 48%; night steps in (45-51%) and the terrace windows light in three lots
  51- 94%  night: Sheeta drifts down the ravine to Pom's ledge (62-84%); Laputa's core answers her stone and
           crystal veins in the far wall wake in three bands as she passes
  94-100%  dawn: night steps out under the warm wash

Motion is CSS transform/opacity only, in whole-pixel steps(). Every moment is parked (off-canvas or at
opacity 0) and its keyframes hold outside its slot, so nothing is redrawn for it then. The only things
that never rest are Laputa's slow bob and the wisps of chimney smoke.
"""
import base64, math, random, struct, zlib
from lib import Canvas, UNPAINTED, hx

NAME = "Castle in the Sky: Slag Ravine"
SIZE = W, H = 320, 180
COLORS = 200         # more than the base layer uses, so its colours stay exact
F, CX, HZ = 170, 160, 34             # the camera: focal length in px (a wide lens), centre column, horizon row
SUN = (-.45, -.5, .74)               # direction to the sun: upper left, a little towards us


def mix(a, b, t):
    a, b = hx(a), hx(b)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


S = ["#3564b4", "#4a7fc8", "#6a9ad8", "#8db6e4", "#b3d1ee", "#d3e5f5"]              # sky top -> horizon
C = ["#fffaf0", "#eee8ea", "#d0d4ea", "#b2bade"]                                     # cumulus
MIST = "#dfe9f4"
ROCK = ["#bfb0b6", "#9d8fa8", "#6a5e8c", "#4a4170", "#ddd0cc"]   # the far wall: lit face, half-light, shadowed side, crack, lit edge
GRASS = ["#b4d862", "#8ec65a", "#5ba558", "#418a56"]
PLASTER = [["#f2e8cc", "#d2c8b4", "#aaa09c"], ["#ebdcb8", "#c8baa4", "#a09690"], ["#e6e0d0", "#c4beb8", "#9c98a0"]]
ROOFS = [["#dc8c4c", "#b86c3c", "#8e5236"], ["#cf7a44", "#ac5e38", "#844834"], ["#e09a58", "#bc7844", "#925a3a"]]
BRICK = ["#c8765c", "#a85e4c", "#804842"]
WOOD = ["#a8644e", "#8a4e42", "#6a3c3a"]
PLANK = ["#cfa868", "#ad8850", "#8a6a44"]
SLATE = ["#93a0be", "#7482a4", "#586688"]
ST = ["#f6ecd0", "#dccdaa", "#b0a29c", "#807a98", "#514c70", "#353150", "#23213a"]   # Laputa's stone
GR = ["#c4e070", "#8cc458", "#56984f", "#2f6c50", "#1e4b47"]                         # leaves
WD = ["#8a6450", "#5e4640"]
SK = ["#f8cfa0", "#d8996c"]
INK, GOLD, DARK = "#2a2438", "#ffd75e", "#4a4670"


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
                m = prev and ((k == 0 and (x % 4 != (yy % 2) * 2)) or (k == 1 and (x + yy) % 2)
                              or (k == 2 and x % 4 == (yy % 2) * 2))
                cv.set(x, yy, prev if m else c)
        prev, y = c, y1


def blur(a, r):
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
    r = random.Random(seed)
    out = list(lumps)
    for cx, cy, rad in lumps:
        for _ in range(n):
            a = math.radians(r.uniform(-175, -5))
            q = rad * r.uniform(lo, hi)
            out.append((cx + math.cos(a) * rad * .85, cy + math.sin(a) * rad * .85, q))
    return out


LEAF = (-.52, -.66, .54)
CUTS = (.45, .30, .12, -.05)


def volume(cv, lumps, tones, cuts, soft=4, sharp=.6, sink=.25, base=None, light=(-.45, -.60, .66)):
    """Painterly lumpy volume (cumulus, tree crown): a union of spheres lit by a mix of its own normal
    and that of a blurred copy, darkened towards the bottom by `sink`, cut into flat tones."""
    w, h = cv.w, cv.h
    hg = [[0.0] * w for _ in range(h)]
    for cx, cy, r in lumps:
        for y in range(max(0, int(cy - r) - 1), min(h, int(cy + r) + 2)):
            for x in range(max(0, int(cx - r) - 1), min(w, int(cx + r) + 2)):
                d2 = (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2
                if d2 < r * r:
                    hg[y][x] = max(hg[y][x], math.sqrt(r * r - d2))
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


def rnd(i):
    return (i * 2654435761 % 2 ** 32) / 2 ** 32


# ------------------------------------------------------------------ one camera for everything
def pr(p):
    """World point (X right, Y away, Z up, eye at the origin) -> screen."""
    return CX + F * p[0] / p[1], HZ - F * p[2] / p[1]


def poly(cv, pts, c):
    """Fill a polygon given in screen coordinates (pixel centres, even-odd)."""
    ys = [p[1] for p in pts]
    for y in range(max(0, math.floor(min(ys))), min(cv.h, math.ceil(max(ys)) + 1)):
        yc, xs = y + .5, []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            if (y0 <= yc) != (y1 <= yc):
                xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            for x in range(max(0, math.ceil(a - .5)), min(cv.w, math.ceil(b - .5))):
                cv.set(x, y, c)


def line(cv, a, b, c):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
    for i in range(n + 1):
        cv.set(int(a[0] + (b[0] - a[0]) * i / n), int(a[1] + (b[1] - a[1]) * i / n), c)


def tone(n):
    """Which of a material's three tones a face with outward normal n gets: lit, mid or shade."""
    d = (n[0] * SUN[0] + n[1] * SUN[1] + n[2] * SUN[2]) / math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
    return 0 if d > .42 else 1 if d > -.05 else 2


def face(cv, pts, n, mat, hz=0, ox=0, oy=0):
    """Fill a planar face if its outward normal n looks at the eye. Returns its screen points, or None."""
    p = pts[0]
    if n[0] * p[0] + n[1] * p[1] + n[2] * p[2] >= 0:
        return None
    sp = [(x - ox, y - oy) for x, y in map(pr, pts)]
    poly(cv, sp, mix(mat[tone(n)], MIST, hz))
    return sp


def house(cv, o, a, w, d, h, rh, wall, roof, hz=0, wins=None, ox=0, oy=0, chim=True, fitted=True):
    """A gabled house. o: the ground corner where its front wall starts; a: the heading of its ridge;
    w along the ridge, d deep (to the left of the heading), walls h high, roof rising rh more.
    The front wall gets windows and a door, the back wall windows; the ridge gets a chimney at its start."""
    ex, ey = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
    P = lambda u, v, z: (o[0] + u * ex[0] + v * ey[0], o[1] + u * ex[1] + v * ey[1], o[2] + z)
    S_ = lambda p: (pr(p)[0] - ox, pr(p)[1] - oy)
    k = dict(hz=hz, ox=ox, oy=oy)
    back = face(cv, [P(0, d, 0), P(w, d, 0), P(w, d, h), P(0, d, h)], (ey[0], ey[1], 0), wall, **k)
    g0 = face(cv, [P(0, 0, 0), P(0, d, 0), P(0, d, h), P(0, d / 2, h + rh), P(0, 0, h)], (-ex[0], -ex[1], 0), wall, **k)
    g1 = face(cv, [P(w, 0, 0), P(w, d, 0), P(w, d, h), P(w, d / 2, h + rh), P(w, 0, h)], (ex[0], ex[1], 0), wall, **k)
    front = face(cv, [P(0, 0, 0), P(w, 0, 0), P(w, 0, h), P(0, 0, h)], (-ey[0], -ey[1], 0), wall, **k)
    face(cv, [P(0, d, h), P(w, d, h), P(w, d / 2, h + rh), P(0, d / 2, h + rh)], (ey[0] * rh, ey[1] * rh, d / 2), roof, **k)
    face(cv, [P(0, 0, h), P(w, 0, h), P(w, d / 2, h + rh), P(0, d / 2, h + rh)], (-ey[0] * rh, -ey[1] * rh, d / 2), roof, **k)
    sz = F / P(w / 2, 0, 0)[1]                       # px per metre here
    if fitted:
        line(cv, S_(P(0, d / 2, h + rh)), S_(P(w, d / 2, h + rh)), mix(mix(roof[0], "#ffffff", .3), MIST, hz))
    ww, wh = max(1, round(.8 * sz)), max(1, round(1.1 * sz))
    spots = [(u, d / 2, .7, 0) for u, f in ((0, g0), (w, g1)) if f]         # a window in a gable end that shows
    for v in [0] * bool(front) + [d] * bool(back):                           # and the long wall that faces the eye
        spots += [(.27 * w, v, .66, 0), (.73 * w, v, .66, 0), (.73 * w, v, .22, 0), (.27 * w, v, .2, not v)]
    for u, v, z, door in spots if fitted else ():
        x, y = S_(P(u, v, z * h))
        x, y = int(x - ww / 2), int(y - wh / 2)
        for yy in range(wh + (door and sz > 1.8)):
            for xx in range(ww):
                cv.set(x + xx, y + yy, mix(WD[1] if door else DARK, MIST, hz))
        if wins is not None and not door:
            wins.append((x + ox, y + oy, ww, wh))
    if chim:
        x, y = S_(P(0, d / 2, h + rh))
        cw, ch = max(1, round(.8 * sz)), max(2, round(1.5 * sz))
        for yy in range(ch):
            for xx in range(cw):
                cv.set(int(x) + xx, int(y) - yy, mix("#a8645a" if xx < cw - 1 or cw == 1 else "#7c4c50", MIST, hz))
        return int(x) + ox, int(y) - ch + oy


# ------------------------------------------------------------------ the map (metres; the eye is at the origin, looking north)
#
#                      N
#    far wall |                                        [#] Pazu's house on the crown of the hill
#    of the   |   g o r g e        mill ruins        .'    (the top of the path, ~195 m off)
#    ravine,  |   (bridges)        and pipe  mm    .'  ::  the brick ruin and the cottage
#    the old  |                  . - ~ ~ - .     .'
#    town set |   Pom's mine   '    the      `<'           the path: up from the terrace, one hairpin,
#    into it  |   on a ledge  /     dome       `.          past the ruins, to the house door
#             |              |                   ||        the terrace: two rows either side of its
#             | hanging      |                   ||        street, a crescent 90-140 m off, 60 m below the eye,
#             | house  []     \                   \\       a cross-wing at its uphill end
#             | on the rim     ` - .                `.     the road on down the hill
#                                    eye o
#
# The gorge runs north; its far wall is one plane (WA to WB and on). The dome's edge above the gorge is EDGE.
WA, WB = (-75, 60), (-60, 360)
WLEN = math.hypot(WB[0] - WA[0], WB[1] - WA[1])
EDGE = [(-14, 14, -13), (-13, 18, -14), (-12, 24, -16), (-11, 34, -20), (-8, 50, -25), (-3, 75, -29), (4, 105, -30),
        (14, 140, -30), (28, 180, -32), (48, 230, -36), (80, 300, -42)]
STREET = [(76, 92, -64.5), (61.2, 99.9, -64.5), (49.1, 111.6, -64), (40.7, 126.1, -62.5),
          (36.6, 142.4, -60.5)]       # the terrace's street, downhill end first: a crescent bending round the hill
PATH = [(204, 106), (196, 100), (188, 94), (186, 91), (190, 88), (204, 78), (222, 64), (238, 52),
        (246, 46)]                    # on screen: from the top of the street, round the hairpin, up to Pazu's door
HOME_AT = 233, 17                    # the top-left of Pazu's house on the crown
MX, MY = 30, 96                      # Uncle Pom's mine mouth, in the far wall
HWINS = []                           # windows that light at night: the hanging house, Pazu's shack
SMOKES = []                          # chimney tops that smoke


def wall_at(sx, sy):
    """Screen pixel -> (u, Y, Z) on the far wall, or None to the right of where it vanishes."""
    k, dx, dy = (sx + .5 - CX) / F, WB[0] - WA[0], WB[1] - WA[1]
    if k * dy - dx >= -1:
        return None
    t = (WA[0] - k * WA[1]) / (k * dy - dx)
    y = WA[1] + dy * t
    return t * WLEN, y, (HZ - sy - .5) * y / F


def wall_pt(u, z):
    t = u / WLEN
    return WA[0] + (WB[0] - WA[0]) * t, WA[1] + (WB[1] - WA[1]) * t, z


def misted(c, y, z):
    """A colour of the gorge as the mist takes it: more the deeper and the farther. Six flat steps."""
    return mix(c, MIST, int(min(1, max(0, (-z - 40) / 130) + max(0, y - 200) / 800) * 5.99) * .19)


# the old town set into the far wall: three small clusters of narrow fronts (u along the wall, top z, width, floors)
FACADES = [(u0 + 8.5 * i, z0 - 6 * rnd(int(u0) + i), 8, 3 + int(2 * rnd(int(u0) + i + 9)))
           for u0, z0, n in ((30, -24, 3), (118, -16, 4), (182, -50, 3)) for i in range(n)]
# the wall itself: big irregular masses of rock (where each begins along the wall; its top; its two ledges)
MASS = [(-8, -4, -30, -80)]
for _k in range(40):
    MASS.append((MASS[-1][0] + (7 + 13 * rnd(_k + 20)) * (1 + max(0, MASS[-1][0]) / 70), -2.5 - 11 * rnd(_k + 50), -18 - 36 * rnd(_k + 70), -66 - 44 * rnd(_k + 90)))


def far_wall(cv):
    """The far wall of the ravine as carved rock: masses that jut and recede, each with a lit face, a shadowed
    side and a deep crack before the next, ledges and a top rim that catch the light, mist taking it lower down
    and farther off; a little of the old town on it (fronts, windows, chimneys, balconies, ladders); Pom's mine;
    two bridges."""
    cv.rect(0, HZ, 216, H - HZ, mix(ROCK[0], MIST, .76))           # the far depths of the gorge
    k = 0
    for sx in range(172):
        w = wall_at(sx, HZ)
        if not w:
            break
        u, y = w[:2]
        while k + 2 < len(MASS) and MASS[k + 1][0] <= u:
            k += 1
        u0, top, l1, l2 = MASS[k]
        ps = F / y                                                 # px per metre here
        rock = ROCK[3] if (u - u0) * ps < 1.7 else ROCK[2] if u > u0 + .76 * (MASS[k + 1][0] - u0) else ROCK[k % 2]
        for sy in range(HZ, H):
            z = (HZ - sy - .5) * y / F
            c = "#a8cf8a" if z > -2 else mix(ROCK[1], MIST, .3) if z > top else rock
            for zl in (-2, top, l1, l2):
                d = (zl - z) * ps                                  # rows below this edge
                if 0 <= d < 1:
                    c = ROCK[4]
                elif zl < top and 1 <= d < 1 + ps:
                    c = ROCK[2]
            for fu, fz, fw, fl in FACADES:
                if fu <= u < fu + fw and fz - fl * 3.2 <= z < fz + 1.4:
                    c = "#9a6a50" if z >= fz else "#c4b6ae" if int(fu) % 2 else "#b3a49c"
            cv.set(sx, sy, misted(c, y, z))
    for fu, fz, fw, fl in FACADES:
        px = F / wall_pt(fu, 0)[1]                               # px per metre at this front
        step = max(1, math.ceil(2.4 / (3.2 * px)))
        for f in range(0, fl, step):
            for i in range(0, 2, step):
                p = wall_pt(fu + 2.2 + 3.6 * i, fz - 1.7 - 3.2 * f)
                x, y = map(int, pr(p))
                cv.set(x, y, misted(DARK, p[1], p[2]))
        p = wall_pt(fu + 6, fz + 1.4)                            # a chimney
        x, y = map(int, pr(p))
        cv.rect(x, y - max(1, round(3 * px)), 1, max(1, round(3 * px)), misted("#7c4c50", p[1], p[2]))
        if px > 1.2:                                             # a plank balcony under the top floor, a ladder below
            line(cv, pr(wall_pt(fu, fz - 3.4)), pr(wall_pt(fu + fw, fz - 3.4)), misted(WD[0], p[1], p[2]))
            x, y = map(int, pr(wall_pt(fu + 1, fz - fl * 3.2)))
            cv.rect(x, y, 1, round(5 * px), misted(WD[1], p[1], p[2]))
    for by, x0, x1, hz in ((102, 78, 154, .3), (86, 116, 170, .55)):        # bridges across the gorge, far below
        c = mix("#7d7490", MIST, hz)
        cv.rect(x0, by, x1 - x0, 2, c)
        for x in range(x0 + 5, x1, 12):
            cv.rect(x, by + 2, 2, 7, c)
            cv.rect(x - 2, by + 2, 6, 1, c)
    cv.rect(MX, MY, 10, 11, "#3a3550")                             # Uncle Pom's mine: a timbered mouth, a plank ledge
    cv.rect(MX - 1, MY - 1, 1, 12, WD[0])
    cv.rect(MX + 10, MY - 1, 1, 12, WD[1])
    cv.rect(MX - 1, MY - 2, 12, 1, WD[0])
    cv.rect(MX - 14, MY + 11, 30, 1, WD[0])
    cv.rect(MX - 14, MY + 12, 30, 1, WD[1])
    for x in (MX - 12, MX + 1, MX + 13):
        cv.rect(x, MY + 13, 1, 4, WD[1])
    cv.paint(POM, PPAL, MX - 10, MY - 1)


TEDIS = [                   # Fortress Tedis: pale stone, domed bastions, the stepped keep and its spire
    "..................s",
    "..................s",
    ".................ddd",
    "................wwwww",
    "................wwWww",
    "..........ddd...wwwww...ddd",
    ".........wwwww.wwwwwww.wwwww",
    ".....ddd.wwWww.wwwwWww.wwwww.ddd",
    "....wwwwwwwwwwwwwwwwwwwwwwwwwwwww",
    "....wWwwwwwwWwwwwwwwwwwwWwwwwwwWw",
    "..b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b",
    "..wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww",
    "..wwWwwwwwwwwWwwwwwwwwwWwwwwwwwwWww",
]
TPAL = {"s": "#8c94b0", "d": "#8088a8", "w": "#dfe0e8", "W": "#c2c2a8", "b": "#c4c8dc"}
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
MILL = [                    # the old mill: a long front wall with window holes, three roofless gables, the rusty pipe
    "....r",
    "....r",
    "....r",
    "....r",
    "....r...m......m.....m",
    "....r...mM.....mM....mM",
    "....r..mmmM...mmmM..mmmM",
    "....r..mhmM...mhmM..mhmM",
    "....r.mmmmmM.mmmmmMmmmmmM",
    "mmmmmmmmmmmmmmmmmmmmmmmmM",
    "mhmmhmmmhmmhmmmhmmhmmmhmM",
    "mmmmmmmmmmmmmmmmmmmmmmmmM",
]
RUIN = [                    # the pink-brick ruin: a roofless shell, ragged at the top, arched holes
    "P....PP.....P",
    "PP..PPPP...PPQ",
    "PPPPPhPPP.PPPQQ",
    "PhhPPhPPPPPhPQQ",
    "PPPPPPPPPPPPPQQ",
    "PhhPPhPPhPPhPQQ",
    "PPPPPPPPPPPPPQQ",
]
COT = [                     # the cottage below it: a tiled roof, a white chimney, shrubs
    "...w",
    "...w.tttttt",
    "..tttttttttt",
    ".ttttttttttttgg",
    "TTTTTTTTTTTTTggg",
    ".cchccchcchc.gggg",
]
TURRET = [                  # on the roof of Pazu's brick block: the round kiln turret, doves on its rim, a doorway
    "..w.....w",
    "..ooooooooo",
    "..BBBBbbbdd",
    "..BBBBbbbdd",
    "..bbbbddddd",
    "..BBBBbbbdd",
    ".BBBBBbbbbdd",
    ".bbbbbdddddd",
    ".BBBBBbbbbdd",
    ".BBBBBbbbbdd",
    "bbbbbbddddddd",
    "BBBBBBbbbbddd",
    "BBBBBBKbbbddd",
    "bbbbbKKKddddd",
    "BBBBBKKKbbddd",
    "BBBBBKKKbbddd",
]
SHACK = [                   # and the slate-roofed plank shack with its white stovepipe
    "....w",
    "....w",
    "....w",
    "....w",
    "...sssssss",
    "..sssssssss",
    ".sssssssssss",
    "SSSSSSSSSSSSS",
    ".ppPppPppPpp",
    ".pyyypPqqPpp",
    ".pyyypPqqPpp",
    ".ppPppPqqPpp",
    ".ppPppPqqPpp",
]
RPAL = {"r": "#b8703c", "m": "#eee4c8", "M": "#b9ae9c", "h": "#6a6278", "Q": "#b47870", "t": "#c8843c",
        "T": "#96582e", "w": "#ffffff", "c": "#e6dcc0", "g": "#2f7048", "o": "#de9a7c", "B": BRICK[0], "b": BRICK[1],
        "d": BRICK[2], "s": SLATE[0], "S": SLATE[2], "p": PLANK[0], "P": PLANK[1], "q": PLANK[2], "y": DARK, "K": INK}


def strip(pts, half):
    """A ribbon of ground `half` metres either side of a path, as a screen polygon."""
    a, b = [], []
    for i, p in enumerate(pts):
        q, r = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dy = r[0] - q[0], r[1] - q[1]
        n = math.hypot(dx, dy)
        a.append(pr((p[0] - dy / n * half, p[1] + dx / n * half, p[2])))
        b.append(pr((p[0] + dy / n * half, p[1] - dx / n * half, p[2])))
    return a + b[::-1]


def dome(cv, wins):
    """The grass hill, seen whole: far land beyond it, its sunlit crown and swathes, the shade that wraps its curve
    (every seam between two tones dithered), tufts, rock, shrubs, the path and its flowers, a mine trolley, the
    ruins beside the path, the terrace, and Pazu's house on the crown."""
    edge = [pr(p) for p in EDGE]
    sky = [(218, 53), (230, 46), (282, 46), (300, 50), (321, 57)]
    poly(cv, [(168, HZ), edge[-1]] + sky + [(321, HZ)], "#b4d2cc")                    # far land
    poly(cv, [(190, HZ + 5), (236, HZ + 2), (290, HZ + 5), (321, HZ + 3), (321, 58), (240, 58)], "#9cc4c0")
    poly(cv, edge + sky + [(321, 181), (-10, 181)], GRASS[1])
    for c, pts in (
            (0, edge[7:] + sky + [(321, 72), (296, 68), (268, 74), (240, 80), (214, 78), (192, 82), (180, 86)]),   # the sunlit crown
            (2, [(170, 86), (200, 80), (238, 84), (268, 78), (300, 72), (321, 76), (321, 82), (300, 79), (268, 85),
                 (238, 91), (200, 87), (172, 93)]),                                    # bands of shade round the dome
            (2, [(144, 114), (174, 98), (206, 92), (224, 98), (214, 114), (206, 132), (188, 144), (162, 138), (142, 128)]),
            (3, [(160, 124), (184, 116), (200, 122), (194, 134), (172, 136)]),         # the dark of the hollow
            (0, [(321, 90), (300, 92), (286, 106), (294, 126), (321, 132)]),           # sunlit swathes
            (0, [(236, 100), (262, 96), (284, 104), (270, 112), (246, 110)]),
            (2, [(210, 152), (246, 150), (272, 164), (300, 166), (321, 160), (321, 181), (200, 181)]),
            (1, [(226, 170), (260, 173), (296, 172), (321, 168), (321, 172), (296, 177), (260, 178), (228, 175)]),
            (2, [(-10, 181), (44, 166), (92, 150), (136, 142), (176, 152), (204, 181)]),
            (3, [(-10, 181), (34, 176), (104, 164), (156, 181)])):
        poly(cv, pts, GRASS[c])
    tones = [tuple(hx(c)) for c in GRASS]
    snap = [row[:] for row in cv.px]
    for y in range(47, H - 1):                                # dither each seam between two tones: a two-row checker
        for x in range(120, W):
            a, b = tuple(snap[y][x]), tuple(snap[y + 1][x])
            if a != b and a in tones and b in tones:
                cv.set(x, y + (x + y) % 2, b if (x + y) % 2 == 0 else a)
    for i in range(60):                                       # tufts: short strokes one tone darker than the grass they are in
        x, y = 150 + int(rnd(i + 300) * 168), 62 + int(rnd(i + 400) * 116)
        for xx in range(3):
            c = tuple(cv.px[y - xx % 2][x + xx])
            if c in tones[:3]:
                cv.set(x + xx, y - xx % 2, GRASS[tones.index(c) + 1])
    for x, y, w in ((170, 106, 5), (188, 124, 6), (150, 144, 7), (118, 154, 6), (304, 120, 5), (256, 112, 4), (238, 92, 4),
                    (226, 162, 6), (284, 62, 4), (306, 96, 5), (262, 170, 6), (296, 80, 5)):              # pale rock
        cv.rect(x, y, w, 2, "#dadec4")
        cv.rect(x + 1, y - 1, w - 2, 1, "#eef0dc")
        cv.rect(x + 1, y + 2, w - 1, 1, GRASS[3])
    for x, y in ((300, 62), (308, 64), (278, 43), (262, 96), (180, 104), (290, 104)):                    # shrubs
        cv.rect(x, y, 6, 3, GRASS[3])
        cv.rect(x + 1, y - 2, 4, 2, "#2f7048")
    for pts in (PATH, [(300, 156), (308, 168), (316, 181)]):                                              # the path
        for a, b in zip(pts, pts[1:]):
            for d in (0, 1):
                line(cv, (a[0], a[1] + d), (b[0], b[1] + d), "#e8dfc2")
            for k, (dx, dy) in enumerate(((-3, -2), (3, 4), (-5, 1), (5, -1))):       # yellow flowers beside it
                cv.set((a[0] * (3 - k % 2 * 2) + b[0] * (1 + k % 2 * 2)) // 4 + dx, (a[1] + b[1]) // 2 + dy, "#f6dc4a")
    cv.rect(207, 72, 4, 2, WD[0])                             # a mine trolley left on the path
    cv.rect(207, 74, 4, 1, INK)
    cv.paint(MILL, RPAL, 196, 49)
    cv.paint(RUIN, dict(RPAL, P="#dc9c8e"), 240, 64)
    cv.paint(COT, RPAL, 220, 76)
    poly(cv, strip(STREET, 2.6), "#d9d0b8")
    # the terrace: joined houses down both sides of the street, each row's fronts to it
    A, B = STREET[-2:]
    a = math.atan2(B[1] - A[1], B[0] - A[0])                  # the cross-wing across the uphill end of the street
    o = (B[0] + .5 * math.cos(a) - 2.6 * math.sin(a), B[1] + .5 * math.sin(a) + 2.6 * math.cos(a), B[2])
    todo = [(math.hypot(o[0], o[1]) + 3, o, a - math.pi / 2, 11.6, 1, 1)]
    for i in range(len(STREET) - 1):
        for g, (A, B) in enumerate(((STREET[i], STREET[i + 1]), (STREET[i + 1], STREET[i]))):
            ln = math.hypot(B[0] - A[0], B[1] - A[1])
            n = round(ln / 5.6)
            a = math.atan2(B[1] - A[1], B[0] - A[0])
            for k in range(n):
                o = tuple(A[j] + (B[j] - A[j]) * k / n for j in range(3))
                o = (o[0] - 3 * math.sin(a), o[1] + 3 * math.cos(a), o[2])
                todo.append((math.hypot(o[0] - 6 * math.sin(a), o[1] + 6 * math.cos(a)), o, a, ln / n, len(todo), g))
    for dist, o, a, w, j, g in sorted(todo, reverse=True):    # far to near, so each hides what is behind it
        top = house(cv, o, a, w, 6, 5.0, 2.4, PLASTER[j % 3], ["#c8603c", "#a84c34", "#803c30"] if w > 9 else ROOFS[j % 3], 0, wins)
        if j % 7 == 3:
            SMOKES.append(top)
        if not g:                                             # the near row's walled back garden and its outbuilding
            q = [pr((o[0] + u * math.cos(a) - v * math.sin(a), o[1] + u * math.sin(a) + v * math.cos(a), o[2] + .5))
                 for u, v in ((0, 6), (0, 10.5), (w, 10.5), (w, 6))]
            poly(cv, q, GRASS[2])
            for p0, p1 in zip(q, q[1:]):
                line(cv, p0, p1, "#e4dcc0")
            cv.set(int(q[1][0]) + 1, int(q[1][1]) - 1, ROOFS[1][1])
            mx, my = int((q[0][0] + q[2][0]) / 2), int((q[0][1] + q[2][1]) / 2)
            if j % 3 == 0:                                    # washing on a line
                cv.rect(mx - 1, my, 3, 1, "#ffffff")
                cv.set(mx, my, GRASS[2])
            elif j % 4 == 1:                                  # someone out in the garden
                cv.set(mx, my - 1, "#5a3a2c")
                cv.set(mx, my, "#c8563a")
    # Pazu's house on the crown: the brick block, the arched door the path comes to, ivy, the shack and the turret
    x, y = HOME_AT
    cv.rect(x, y + 17, 6, 13, BRICK[2])
    cv.rect(x + 6, y + 17, 36, 13, BRICK[0])
    for yy in range(13):
        for xx in range(36):
            if yy % 3 == 0 or (xx + (yy // 3 % 2) * 3) % 6 == 5:
                cv.set(x + 6 + xx, y + 17 + yy, BRICK[1])
    cv.rect(x, y + 16, 6, 1, "#bfae88")
    cv.rect(x + 6, y + 16, 36, 1, "#efe2c0")
    for dx, dy, w, h in ((12, 24, 4, 6), (23, 20, 3, 4), (31, 20, 3, 4)):      # the arched door the path comes to, window holes
        cv.rect(x + dx, y + dy, w, h, INK)
        cv.rect(x + dx + 1, y + dy - 1, w - 2, 1, INK)
    for i in range(30):
        cv.set(x + 29 + int(rnd(i) * 12), y + 18 + int(rnd(i + 40) * 12), GR[1 + i % 2])
    cv.paint(SHACK, RPAL, x + 14, y + 3)
    cv.paint(TURRET, RPAL, x + 28, y)
    HWINS.append((x + 16, y + 12, 3, 2))
    SMOKES.append((x + 17, y + 3))


def hanging_house(cv):
    """On the dome's edge above the gorge: a tall wooden house hung off the rock, and the old mill's rusty pipes."""
    for x, top in ((80, 60), (113, 78)):
        cv.rect(x, top, 2, 136 - top, "#b8703c")
        cv.rect(x + 1, top, 1, 136 - top, "#8a4e30")
        cv.rect(x - 1, top, 4, 1, "#8a4e30")
    xa, xb, ya, yb, zt, zb = -14.5, -11.2, 34, 37.5, -10, -42
    face(cv, [(xb, ya, zb), (xb, yb, zb), (xb, yb, zt + 1), (xb, ya, zt)], (1, 0, 0), WOOD)
    face(cv, [(xa, ya, zb), (xb, ya, zb), (xb, ya, zt), (xa, ya, zt)], (0, -1, 0), WOOD)
    face(cv, [(xa - .4, ya - .6, zt), (xb + .4, ya - .6, zt), (xb + .4, yb, zt + 1), (xa - .4, yb, zt + 1)], (0, -1, 4), SLATE)
    x0, y0 = map(int, pr((xa, ya, zt)))
    x1 = int(pr((xb, ya, zt))[0])
    for x in range(x0 + 2, x1, 3):
        cv.rect(x, y0 + 1, 1, H - y0, WOOD[1])
    for y in (y0 + 18, y0 + 38):
        cv.rect(x0, y, x1 - x0, 1, WOOD[2])
    for x, y in ((x0 + 3, y0 + 6), (x0 + 10, y0 + 6), (x0 + 6, y0 + 24), (x0 + 3, y0 + 43), (x0 + 10, y0 + 43)):
        cv.rect(x, y, 4, 5, "#f2e6c4")
        cv.rect(x + 1, y + 1, 2, 3, DARK)
        HWINS.append((x + 1, y + 1, 2, 3))


def base():
    cv = Canvas(W, H)
    bands(cv, 0, [(6, S[0]), (12, S[1]), (19, S[2]), (25, S[3]), (30, S[4]), (HZ + 1, S[5])])
    volume(cv, puffs([(150, 31, 4), (180, 32, 4), (214, 30, 5), (286, 30, 5), (308, 32, 4), (6, 31, 4)], 11, 2),
           C, CUTS[:3], soft=3, sink=.3, base=HZ + 1)
    cv.paint(TEDIS, TPAL, 2, 21)
    far_wall(cv)
    wins = []
    dome(cv, wins)
    hanging_house(cv)
    return cv, [w for w in wins if tuple(cv.px[w[1]][w[0]]) == tuple(hx(DARK))]   # only the windows that still show


BASE, WINS = base()


def draw():
    return BASE


# ------------------------------------------------------------------ Laputa, small and far, in the sky over the ravine
IX, IY, IK = 40, 0, 1
FARC = lambda c: mix(c, "#8fc0ea", .18)


def cyl(u):
    return 1 if u < -.84 else 0 if u < -.05 else 1 if u < .4 else 2 if u < .76 else 3


def island(k=IK):
    q = lambda v: round(v * k)
    cv = Canvas(q(64), q(56))
    cx, uy, r = q(32), q(43), q(30)
    st, gr = [FARC(c) for c in ST], [FARC(c) for c in GR]
    for d in range(q(11)):                                # the dark underside
        hw = int(r * math.sqrt(1 - (d / (q(11) + .2)) ** 2))
        for x in range(cx - hw, cx + hw):
            u = (x + .5 - cx) / r
            cv.set(x, uy + d, st[4] if u < -.6 else st[5] if u < .3 else st[6])
    cv.rect(cx - 2, uy + q(11), 4, 1, st[6])
    for x, y in ((6, 46), (17, 52), (46, 52), (57, 46)):
        cv.rect(q(x), q(y), 1, 2, st[6] if x > 32 else st[5])
    prev = 0
    for hw, y0, y1 in [(8, 24, 28), (15, 28, 32), (22, 32, 36), (28, 36, 41), (31, 41, 43)]:
        hw, y0, y1 = q(hw), q(y0), q(y1)
        for x in range(cx - hw, cx + hw):
            t = cyl((x + .5 - cx) / hw)
            cv.rect(x, y0, 1, y1 - y0, st[t])
            cv.set(x, y1 - 1, st[t + 1])
            if y1 - y0 > 2 and (x - cx) % 3 == 1:
                cv.set(x, y0 + 1, st[min(6, t + 3)])
            if abs(x + .5 - cx) > prev - 1:
                cv.set(x, y0, gr[2] if x < cx else gr[3])
        prev = hw
    for y in range(q(16), q(26)):                         # trunk
        hw = max(1, q(3 + max(0, y / k - 22)))
        cv.rect(cx - hw, y, 2 * hw, 1, FARC(WD[0]))
        cv.rect(cx + hw - 1, y, 1, 1, FARC(WD[1]))
    crown = [(32, 6, 5), (32, 14, 8), (23, 16, 7), (41, 16, 7), (15, 18, 6), (49, 18, 6), (8, 20, 4), (56, 20, 4), (4, 21, 3),
             (60, 21, 3), (20, 11, 5), (44, 11, 5), (27, 9, 5), (37, 9, 5), (12, 22, 3), (52, 22, 3)]
    volume(cv, puffs([(x * k, y * k, rr * k) for x, y, rr in crown], 2, 2, .3, .45), gr, (.56, .40, .22, .04),
           soft=2, sharp=.7, sink=.3, light=LEAF)
    return cv


# ------------------------------------------------------------------ people
RUN = [                     # Pazu and Sheeta running up the path (their legs are sprites): his cap, white sleeves, red-brown
    ".ccc...kkk.",          # waistcoat and satchel; her dark hair, braids tied with red, and dark dress
    "cccc..kkkk.",
    ".sch..skkk.",
    ".shh..skkr.",
    "wvvvw.nnnk.",
    "svvvg.nnnnk",
    ".vvvg.nnnnr",
    ".uuu..nnnnn",
]
TRUMP = [                   # Pazu on his roof, trumpet raised
    ".....ccc",
    "tt..cccc",
    "ttt..ssh",
    "..ttwssh",
    "....wvvw",
    ".....vvw",
    ".....vvs",
    ".....uu",
    ".....bb",
]
UPAL = {"c": "#d8b060", "h": "#5a3a2c", "w": "#fffaf0", "v": "#c8563a", "g": "#7a8a5a", "u": "#6f88ac", "n": "#33447e",
        "k": "#3a2c34", "r": "#d83848", "s": SK[0], "b": "#6a4230", "t": GOLD}
FALL = [                    # Sheeta asleep on the air, braids streaming up, lit by the stone at her throat
    "................k..k",
    "...............r..r",
    "...............k.k",
    ".nn..ddddddddppsskk",
    "nnn.dddddddddpppsssk",
    "..n..dddddddd.ppssk",
    ".........dd",
]
FPAL = {"k": "#4a5a9c", "r": "#e86070", "n": "#c06070", "d": "#5870c8", "p": "#e4eefc", "s": "#fbe6d0"}

# ------------------------------------------------------------------ things that fly
MOTH = [                    # the Tiger Moth: a fat ochre hull mottled with brown, propellers on booms, the lookout kite
    "......l........l" + "." * 14 + "aa",
    ".....pl...hhh..lp" + "." * 11 + "l.a",
    "...l..hhhhhhhhhh..l" + "." * 7 + "l",
    "..pl.hhHHmHHHHHHh.lp...l",
    ".....hHHHHHmmHHHHtt.l",
    "..l..HHmHHHHHHHmHttt",
    ".pl..DHHHHmHHHHHDtt",
    "......DDDmDDDDDD",
    ".......kkokokokk",
]
MPAL = {"h": "#ecd070", "H": "#d4ac4c", "D": "#a8843c", "m": "#8a5a34", "l": "#5e5670", "p": "#e4eefa", "t": "#c89840",
        "k": WD[1], "o": GOLD, "a": "#eee2c6"}
GOLIATH = [                 # the Goliath, bow to the right
    "....f" + "." * 21 + "t" + "." * 9 + "tt" + "." * 9 + "t",
    "...ff" + "." * 20 + "ttt" + "." * 7 + "tttt" + "." * 7 + "ttt",
    "..fff" + "h" * 54,
    ".ffff" + "h" * 62,
    "pffff" + "H" * 70,
    "pffff" + "H" * 76,
    "pffff" + "H" * 79,
    "pffff" + "D" * 75,
    ".ffff" + "D" * 68,
    "..fff" + "D" * 56,
    "...ff" + "." * 29 + "b" * 12,
    "....f" + "." * 30 + "b" * 10,
]
OPAL = {"h": "#8196c6", "H": "#6b80b4", "D": "#566a9e", "f": "#566a9e", "t": "#6b80b4", "b": "#48598c", "p": "#a9bbe0"}
FLAP = [                    # a flaptter: a rust-orange pod with a dark intake, two of Dola's sons aboard
    "....hh.hh",
    "....ss.ss",
    "..oooooooooo",
    ".oooooooOOOOo",
    "ooooooooOkkOoo",
    "oOoooooooOOOoo",
    ".ooooooooooo",
    "..d......d",
]
LPAL = {"h": "#c0403a", "s": SK[0], "o": "#d86a38", "O": "#a84a2c", "k": "#3a2a30", "d": WD[1]}


def flock(pts):
    """Birds, wings up, placed point-symmetrically about the image centre. Turning the image half a turn
    about that centre gives the same flock with wings down, so one PNG is both frames of the flap."""
    mx, my = max(abs(x) for x, y in pts), max(abs(y) for x, y in pts)
    cv = Canvas(2 * mx + 3, 2 * my + 2)
    for x, y in pts + [(-x, -y) for x, y in pts if (x, y) != (0, 0)]:
        cv.paint(["w.w", ".w."], {"w": "#ffffff"}, mx + x, my + y)
    return cv


def runs(pts, n=1):
    """Dashes n px long as one stroked path."""
    d, cx, cy = "", None, None
    for x, y in pts:
        d += f"M{x} {y}.5h{n}" if cx is None else f"m{x - cx} {y - cy}h{n}"
        cx, cy = x + n, y
    return d


def boxes(ws):
    """Small filled rects (x, y, w, h) as one path."""
    return "".join(f"M{x} {y}h{w}v{h}h-{w}z" for x, y, w, h in ws)


def diamond(cx, cy, r):
    """A filled pixel diamond of radius r round the pixel (cx, cy)."""
    return f"M{cx} {cy - r}h1" + "v1h1" * r + "v1" + "h-1v1" * r + "h-1" + "v-1h-1" * r + "v-1" + "h1v-1" * r + "z"


def smoke(x, y, delay):
    return (f"<path class='lr-s' style='animation-delay:-{delay}s' fill='#eef' "
            f"d='M{x} {y - 3}h2v2h-2zm2-4h3v3h-3z'/>")


def wings(x, y):
    """A flaptter's four wings raised, for the craft whose image is at (x, y). A half turn about the
    bottom of this shape (the wing roots) swings them down behind the pod."""
    return f"<path class='lr-w' d='M{x + 2} {y - 3}.5h3m-2 1h4m-2 1h3m3 0h2m-1-1h3m-2-1h4'/>"


SX, SY = 36, -14                     # Sheeta, parked above the frame
GX, GY = SX + 13, SY + 5             # the stone
NX, NY = IX + round(32 * IK), IY + round(54 * IK)                # Laputa's lowest point
LIT = sorted(w for i, w in enumerate(WINS) if i % 5 in (0, 2))                                # the terrace windows that light
VEINS = [                            # crystal veins in the far wall, lit in three bands as she passes
    [(6, 62), (18, 70), (50, 66), (92, 62), (30, 74), (108, 48), (112, 58)],
    [(6, 80), (54, 84), (62, 94), (16, 90), (70, 76), (96, 72)],
    [(8, 116), (22, 124), (50, 118), (62, 128), (40, 134), (12, 138)],
]
GOX, GOY = -90, 2                    # the Goliath, parked
FLX, FLY = 124, 186                  # the leading flaptter, parked

LAYERS = [
    # --- sky: Laputa, the Goliath passing in front of it, the Tiger Moth
    ("laputa", "<g class='lr-i'>" + img(island(), IX, IY)
     + f"<path class='lr-v' style='--d:152s' stroke='#aff' d='M{NX - 2} {NY}.5h4m-3 1h2'/></g>"),
    ("goliath", img(art(GOLIATH, OPAL), GOX, GOY, " class='lr-go'")),
    ("moth", img(art(MOTH, MPAL), 330, 5, " class='lr-t'")),
    # --- smoke: chimneys on the terrace, Pazu's stovepipe, the pipe by the hanging house
    ("smoke", "".join(smoke(x, y, d) for (x, y), d in zip(SMOKES + [(80, 59)], (0, 3, 5, 2, 6)))),
    # --- Dola's sons on their flaptters, climbing out of the gorge
    ("flaptters", "<g class='lr-f' stroke='#bde'>" + wings(FLX, FLY) + wings(FLX + 22, FLY + 12)
     + img(art([r.ljust(14, ".")[::-1] for r in FLAP], LPAL), FLX, FLY, " id='lr-fl'") + "<use href='#lr-fl' x='22' y='12'/></g>"),
    # --- Pazu's doves, hidden at the turret until he plays, then off over the gorge and home again
    ("doves", "<g class='lr-px'><g class='lr-py'>" + img(flock([(0, 0), (4, -2), (7, 1)]), HOME_AT[0] + 26, HOME_AT[1] - 5, " class='lr-pf'")
     + "</g></g>"),
    # --- Pazu and Sheeta running up the path to the house: each has one leg down and one tucked up behind, swapping
    ("runners", "<g class='lr-rx'><g class='lr-ry'>"
     + "".join(f"<path class='lr-g'{o} stroke='{c}' d='M{PATH[0][0] - 5 + dx}.5 {PATH[0][1] - 2 - up}v3'/>"
               for dx, c, up, o in ((1, "#6f88ac", 0, ""), (7, "#33447e", 0, ""), (3, "#6f88ac", 3, " style='transform-origin:bottom'"),
                                    (9, "#33447e", 3, " style='transform-origin:bottom'")))
     + img(art(RUN, UPAL), PATH[0][0] - 5, PATH[0][1] - 10, " class='lr-m'") + "</g></g>"),
    # --- Pazu on his roof with the trumpet, parked 400 px off to the right until dawn
    ("pazu", "<g class='lr-tp'>" + img(art(TRUMP, UPAL), HOME_AT[0] + 402, HOME_AT[1] + 7) + "</g>"),
    # --- light: night, the warm wash, and what the night does not dim
    ("night", f"<rect class='lr-N lr-b' width='{W}' height='{H}' fill='#3f5098'/>"
     f"<rect class='lr-W lr-b' width='{W}' height='{H}' fill='#fa6'/>"),
    ("lights", "<g class='lr-N'>"
     + f"<path stroke='#fff' d='{runs([(14, 17), (72, 1), (100, 15), (128, 0), (150, 18), (176, 1), (200, 21), (232, 16), (262, 20), (300, 0), (312, 23)])}'/>"
     + "<path fill='#ffe' d='M212 10h3v1h-2v1h-1v4h1v1h2v1h-3v-1h-1v-1h-1v-4h1v-1h1z'/>"
     + f"<path fill='#fd7' d='{boxes(HWINS + [(10, 30, 1, 1), (18, 28, 1, 1), (28, 30, 1, 1)])}M{MX - 10} {MY + 6}h1v3h-1z'/>"
     + f"<path fill='#fd7' opacity='.3' d='M{MX - 11} {MY + 3}h3v2h2v5h-2v2h-3v-2h-2v-5h2z'/>"
     + "".join(f"<path class='lr-N' style='animation-delay:{d}s' fill='#fd7' d='{boxes(LIT[i::3])}'/>" for i, d in ((0, -4), (1, 0), (2, 4)))
     + "<path stroke='#fd7' opacity='.45' stroke-dasharray='1 3' d='"
     + "".join("M%d %dL%d %d" % (*map(round, pr(wall_pt(fu + 1, fz - 1.7 - 6.4 * f))), *map(round, pr(wall_pt(fu + fw - 1, fz - 1.7 - 6.4 * f))))
               for fu, fz, fw, fl in FACADES for f in range(fl // 2)) + "'/>"
     + "</g>"),
    ("goliath lights", f"<g class='lr-go'><path stroke='#fd7' stroke-dasharray='1 1' d='M{GOX + 9} {GOY + 6}.5h62'/>"
     f"<path class='lr-bm' fill='#fd6' opacity='.6' d='M{GOX + 22} {GOY + 12}l-7 24h2l7-24z'/>"
     f"<path class='lr-bm' fill='#fd6' opacity='.6' d='M{GOX + 50} {GOY + 12}l6 22h2l-6-22z'/></g>"),
    ("veins", "".join(f"<path class='lr-v' style='--d:{d}s' stroke='#6ef' d='{runs(pts, 2)}'/>"
                      for pts, d in zip(VEINS, (163, 171, 179)))),
    ("falling", "<g class='lr-sh'>" + f"<path fill='#8ef' opacity='.25' d='M{GX - 2} {GY - 6}h5v3h3v7h-3v3h-5v-3h-3v-7h3z'/>"
     + img(art(FALL, FPAL), SX, SY)
     + f"<path fill='#8ef' d='{diamond(GX, GY, 2)}'/><path fill='#fff' d='M{GX} {GY}h1v1h-1z'/></g>"),
]
SPRITES = "".join(chunk for _, chunk in LAYERS)
CSS = (
    # ambient loops
    ".lr-i{animation:lr-i 16s steps(2) infinite alternate}@keyframes lr-i{to{transform:translateY(2px)}}"
    ".lr-s{animation:lr-s 8s steps(8) infinite}@keyframes lr-s{from{opacity:0}25%{opacity:.8}to{opacity:0;transform:translateY(-8px)}}"
    # night and the warm wash (which peaks twice a cycle: one keyframe set serves dusk and dawn)
    ".lr-b{mix-blend-mode:multiply}"
    ".lr-N{opacity:0;animation:lr-N 240s steps(8) infinite}@keyframes lr-N{45%{opacity:0}51%,94.5%{opacity:1}99.5%{opacity:0}}"
    ".lr-W{animation:lr-W 120s steps(6) infinite}@keyframes lr-W{from,to{opacity:.24}5%,88%{opacity:0}96%{opacity:.6}}"
    # the day's moments
    ".lr-tp{animation:lr-tp 240s steps(1) infinite}@keyframes lr-tp{1%{transform:translateX(-400px)}7%{transform:none}}"
    ".lr-px{animation:lr-px 240s steps(120) infinite,lr-o 240s steps(1) infinite}.lr-py{animation:lr-py 240s steps(30) infinite}"
    "@keyframes lr-o{from,35.5%{opacity:0}1.5%{opacity:1}}"
    ".lr-pf,.lr-w,.lr-g,.lr-m{transform-box:fill-box;transform-origin:center;animation:lr-pf 240s steps(45) infinite}"
    "@keyframes lr-px{1.5%{transform:none}8%,29%{transform:translateX(-240px)}35.5%,to{transform:none}}"
    "@keyframes lr-py{1.5%{transform:none}8%,29%{transform:translateY(-30px)}35.5%,to{transform:none}}"
    "@keyframes lr-pf{1.5%{transform:none}8%,29%{transform:rotate(8100deg)}35.5%,to{transform:none}}"
    # the run up the path: one pixel at a time, left to the hairpin and then right, climbing all the way
    ".lr-rx{animation:lr-rx 240s infinite,lr-q 240s steps(1) infinite}.lr-ry{animation:lr-ry 240s steps(60) infinite}"
    ".lr-g{transform-origin:top;animation:lr-g 240s steps(60) infinite}.lr-m{animation:lr-m 240s steps(1) infinite}"
    "@keyframes lr-q{from,35%{opacity:0}25%{opacity:1}}"
    "@keyframes lr-rx{25%{transform:none;animation-timing-function:steps(18)}27.31%{transform:translateX(-18px);"
    "animation-timing-function:steps(60)}35%,to{transform:translateX(42px)}}"
    "@keyframes lr-ry{25%{transform:none}35%,to{transform:translateY(-60px)}}"
    "@keyframes lr-g{25%{transform:none}35%,to{transform:rotate(10800deg)}}"
    "@keyframes lr-m{27.31%{transform:scaleX(-1)}}"
    ".lr-t{animation:lr-t 240s steps(185) infinite}@keyframes lr-t{8%{transform:none}42%,to{transform:translateX(-370px)}}"
    ".lr-f{animation:lr-f 240s steps(82) infinite}@keyframes lr-f{16%{transform:none}24%,to{transform:translate(-164px,-82px)}}"
    ".lr-w{transform-origin:bottom;animation:lr-w 240s steps(82) infinite}@keyframes lr-w{16%{transform:none}24%,to{transform:rotate(14760deg)}}"
    # dusk: the Goliath crosses the sky, its searchlights swinging once as it goes
    ".lr-go{animation:lr-go 240s steps(210) infinite}@keyframes lr-go{44%{transform:none}84%,to{transform:translateX(420px)}}"
    ".lr-bm{transform-box:fill-box;transform-origin:top;animation:lr-bm 240s steps(16) infinite}"
    "@keyframes lr-bm{44%{transform:rotate(-12deg)}84%,to{transform:rotate(12deg)}}"
    # the night's moment
    ".lr-sh{animation:lr-sh 240s steps(212) infinite}@keyframes lr-sh{62%{transform:none}84%,to{transform:translateY(212px)}}"
    ".lr-v{opacity:0;animation:lr-v 240s var(--d) steps(3) infinite}@keyframes lr-v{1%,4%{opacity:1}6%{opacity:0}}"
)
THEME = {
    "position": "center 5%",
    "canvas": "#101a36", "accent": "#f6c56a", "overlay": "#0e1834",
    "colors": {"sidebar": "#0d1630", "sidebarRowSelected": "#22305a", "sidebarBorder": "#1d2a50",
               "surface": "#152044", "border": "#27366a", "text": "#f1f4ff", "textMuted": "#a9b6d6"},
}
