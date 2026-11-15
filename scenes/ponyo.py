"""Ponyo: the storm chase, as a side-scroller tracking shot. Ponyo sprints along the backs of the
wave-fish toward Sosuke's house on its cliff, her little sisters leaping beside her; Sosuke stands
behind the fence beside the green bucket, flashing the signal lamp out to his father's ship, the
Koganei Maru, which answers from the open water; Lisa's car races home along the cliff road, and
the ladies of the Himawari house watch it all from their window.

Static layer (PNG): storm sky, cloud banks, far sea, headland + road + tunnel, house, fence, bucket,
the care home with its sunflower sign and the three ladies.
Sprites, back to front: lightning, scud, the ship (pitching, with Koichi's lamp and beam) and the
strip of sea in front of its hull, car (clipped at the tunnel by a nested <svg>), flag, the ladies'
idle bits, Sosuke + lamp, the fence rail redrawn over him, Fujimoto riding a swell in, back wave
row (Sosuke's toy boat adrift in one of its troughs), main wave row (blinking eyes, Granmamare gliding on her back inside its water, the
sisters swimming and riding in it, three more leaping beside Ponyo, Ponyo on top), front wave row
(a Devonian fish and three jellyfish in its water).
Each wave row is a transparent PNG strip drawn twice and scrolled by one period.

Ponyo stays at one screen x while the main row scrolls under her, so her height is a keyframe track
sampled from that strip's top envelope every STEP px (see track()); fish noses sit on that grid so
she tops each brow, leaps (second row of her sprite sheet), and lands on the next back.

Timing: every stepped animation changes on a 1/16 s grid (TICK) and moves in whole canvas pixels, so
the scene repaints at most 16 times a second however many things are moving.
"""
import base64, math, struct, zlib
from lib import Canvas, UNPAINTED, hx

NAME = "Ponyo"
SIZE = W, H = 320, 180
COLORS = 32
THEME = {
    "canvas": "#0d1630", "accent": "#ff8a5c", "overlay": "#0a1330",
    "colors": {"sidebar": "#0c1530", "sidebarRowSelected": "#1f4596", "sidebarBorder": "#1c2f5c",
               "surface": "#14224a", "border": "#263c70", "text": "#e9f2f2", "textMuted": "#9db6cc"},
}

S = ["#141b3a", "#1d2b50", "#284166", "#375e7e", "#568796", "#96bcab", "#dde5b4"]   # sky top -> horizon
SEA = ["#3f7590", "#2f5f86"]
ROCK, ROCKD, ROCKB = "#655a80", "#3c345e", "#28264a"
GRASS, GRASSD, PINE = "#5aa24c", "#3b7f4a", "#245a48"
WALL, WALLD, ROOF, ROOFD = "#ece8c6", "#a7c0b2", "#cf4a3a", "#8c2c34"
LAMP, DARK, BUCKET, CEIL, SKIN = "#ffd24a", "#141a36", "#3fc864", "#0d1330", "#ffd2aa"
HZ = 96            # horizon row
GY = 72            # plateau the house stands on
TUN = 160          # tunnel mouth (left edge); the car is clipped just inside it
P = 360            # wave strip period
STEP = 9           # Ponyo's track is sampled every STEP px of strip
PX = 198           # Ponyo's feet centre on screen (a multiple of STEP)
V = 16             # main row scroll, px/s: one pixel per TICK
T = P / V          # seconds per pass of the main row
TICK = 1 / 16


# ------------------------------------------------------------------ helpers
def png(cv, alpha=255):
    """A Canvas (magenta = transparent) as a base64 palette PNG, hand-encoded so the bit depth and the
    deflate strategy can be whichever comes out smallest. (Same encoder as scenes/laputa.py.)
    alpha makes colours translucent through the palette's tRNS chunk: one value for every colour,
    or {colour: value} with the rest opaque."""
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
    al = alpha if isinstance(alpha, dict) else dict.fromkeys(cols, alpha)
    trns = bytes([0] + [al.get(c, 255) for c in cols[1:]]).rstrip(b"\xff")
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, bits, 3, 0, 0, 0))
            + chunk(b"PLTE", bytes(v for c in cols for v in c)) + (chunk(b"tRNS", trns) if trans else b"")
            + chunk(b"IDAT", z) + chunk(b"IEND", b""))
    return base64.b64encode(data).decode()


def img(cv, x=0, y=0, attr="", alpha=255):
    pos = (f" x='{x}'" if x else "") + (f" y='{y}'" if y else "")
    return f"<image{attr}{pos} width='{cv.w}' height='{cv.h}' href='data:image/png;base64,{png(cv, alpha)}'/>"


def cls(name):
    return f" class='{name}'"


def art(rows, pal):
    """ASCII art -> Canvas ('.' or any char not in pal stays transparent). Short rows are padded."""
    cv = Canvas(max(map(len, rows)), len(rows))
    cv.paint(rows, pal, 0, 0)
    return cv


def bands(cv, y, rows, soft=True):
    """rows: [(y_end, colour)]. Flat bands with an ordered-dither seam (3 rows when soft, else 1)."""
    prev = None
    for y1, c in rows:
        for yy in range(y, y1):
            k = yy - y + (0 if soft else 1)
            for x in range(cv.w):
                mix = prev and ((k == 0 and (x % 4 != (yy % 2) * 2)) or (k == 1 and (x + yy) % 2)
                                or (k == 2 and soft and x % 4 == (yy % 2) * 2))
                cv.set(x, yy, prev if mix else c)
        prev, y = c, y1


def cloud(cv, circles, base, hi, mid, lo, dither=True):
    """Circles painted back to front, each with a lit upper-left rim; flat shadowed base, with a
    dithered row above it unless dither is off."""
    for cx, cy, r in circles:
        for y in range(int(cy - r), min(base, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + .5 - cx, y + .5 - cy
                d = math.hypot(dx, dy)
                if d <= r:
                    rim = d > r - 1.7 and (-.6 * dx - .8 * dy) > .2 * r
                    cv.set(x, y, hi if rim else (lo if base - y <= 2 or (dither and base - y == 3 and x % 2) else mid))


def hang(cv, circles, hi, mid, lo):
    """Storm cloud hanging from the canvas top: the union of the circles (plus everything above
    row 0), one flat mass whose underside alone catches the light from the horizon."""
    inside = lambda x, y: y < 0 or any(math.hypot(x + .5 - cx, y + .5 - cy) <= r for cx, cy, r in circles)
    for y in range(max(int(cy + r) + 1 for cx, cy, r in circles)):
        for x in range(cv.w):
            if inside(x, y):
                edge = not inside(x, y + 1)
                cv.set(x, y, hi if edge and not inside(x + 3, y + 1) else lo if edge or not inside(x + 1, y + 3) else mid)


# ------------------------------------------------------------------ static layer
def cliff_top(x):
    pts = [(0, 80), (34, 77), (72, 74), (100, GY), (168, GY), (173, 75), (177, 83), (180, 98), (184, 124), (188, H)]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if xa <= x <= xb:
            return round(ya + (yb - ya) * (x - xa) / (xb - xa))


def pine(cv, x, base, h):
    for i in range(h):
        w = 1 + (i % 4) + i // 3
        cv.rect(x - w // 2, base - h + i, w, 1, PINE)
    cv.rect(x, base, 1, 2, ROCKB)


def house(cv, x0):
    y = GY
    cv.rect(x0 + 2, y - 14, 38, 14, WALL)             # ground floor
    cv.rect(x0 + 31, y - 14, 9, 14, WALLD)            # its shaded sea side
    cv.rect(x0 + 8, y - 26, 22, 9, WALL)              # upper floor
    cv.rect(x0 + 24, y - 26, 6, 9, WALLD)
    cv.rect(x0 - 1, y - 17, 44, 3, ROOF)              # skirt roof
    cv.rect(x0 - 1, y - 15, 44, 1, ROOFD)
    for i in range(6):                                # hipped top roof
        cv.rect(x0 + 15 - 2 * i - (i > 3), y - 32 + i, 8 + 4 * i + 2 * (i > 3), 1, ROOF if i < 5 else ROOFD)
    cv.rect(x0 + 11, y - 31, 3, 5, WALLD)             # chimney
    for x, yy, w, h in [(5, 11, 5, 6), (13, 11, 5, 6), (11, 24, 4, 5), (18, 24, 4, 5)]:   # lit windows
        cv.rect(x0 + x, y - yy, w, h, LAMP)
        cv.rect(x0 + x + w // 2, y - yy, 1, h, WALL)
    cv.rect(x0 + 23, y - 11, 5, 11, ROCKD)            # door
    cv.rect(x0 + 34, y - 10, 3, 4, LAMP)
    cv.rect(x0 + 30, y - 21, 14, 1, DARK)             # balcony rail over the skirt roof
    for x in range(31, 45, 3):
        cv.rect(x0 + x, y - 20, 1, 3, DARK)
    cv.rect(x0 + 47, y - 40, 1, 40, DARK)             # signal mast with a yard and its flag
    cv.rect(x0 + 44, y - 34, 7, 1, DARK)
    cv.rect(x0 + 48, y - 38, 4, 2, ROOF)
    cv.rect(x0 + 48, y - 36, 4, 2, LAMP)


# The Himawari house: three ladies at its window. The first waves (her raised hand is a sprite),
# Toki in the middle keeps her arms crossed (her glasses are a sprite, so she can look about), the
# third points out at Ponyo.
HX, HY = 46, 61        # left edge and roof row
LADIES = [
    "..cc.....cccc.....ccc...",
    ".cccc...cccccc...ccccc..",
    ".cssc...cssssc...csss...",
    ".ssss....ssss....ssss...",
    ".rrrr....vvvv....bbbbsss",
    "rrrrrr..vsssvv..bbbbbb..",
    "rrrrrr..vvvvvv..bbbbbb..",
]
SUNFLOWER = [".y.y.", "yyyyy", "yynyy", "yyyyy", ".y.y."]
LX, LY = HX + 6, HY + 6    # top-left of the ladies


def home(cv):
    x, y = HX, HY
    cv.rect(x + 2, y - 1, 38, 16, WALL)
    cv.rect(x + 33, y - 1, 7, 16, WALLD)               # shaded sea side, with the door
    cv.rect(x + 35, y + 6, 3, 9, ROCKD)
    cv.rect(x, y - 4, 42, 2, S[4])                     # flat roof, shadow under its eaves
    cv.rect(x + 1, y - 2, 40, 1, S[3])
    cv.rect(x + 4, y + 3, 27, 1, LAMP)                 # the window: a lit lintel over a dim room
    cv.rect(x + 4, y + 4, 27, 9, ROCKD)
    cv.paint(LADIES, {"c": WALL, "s": SKIN, "r": ROOF, "v": S[5], "b": LAMP}, LX, LY)
    cv.paint(SUNFLOWER, {"y": LAMP, "n": ROOFD}, x + 16, y - 11)  # sunflower sign on the roof
    cv.rect(x + 18, y - 6, 1, 2, GRASSD)


THUNDER = [(252, 60, 15), (274, 48, 19), (300, 54, 17), (322, 44, 16), (234, 70, 10)]
BANK = [(222, 78, 8), (240, 70, 13), (262, 75, 12), (284, 67, 15), (306, 73, 13), (322, 80, 9), (206, 85, 5)]


def draw():
    cv = Canvas(W, H)
    bands(cv, 0, [(15, S[0]), (36, S[1]), (55, S[2]), (70, S[3]), (83, S[4]), (91, S[5]), (HZ, S[6])])
    for y in (91, 92, 93):                            # the horizon band gets a one-row seam: three rows read as a fence
        for x in range(W):
            cv.set(x, y, S[5] if y == 91 and (x + y) % 2 else S[6])
    # storm ceiling hanging from the top edge, lit from below
    hang(cv, [(10, -3, 14), (38, -12, 27), (72, -2, 11), (96, -10, 26), (128, -1, 9), (150, -8, 19), (178, -14, 30),
              (212, -2, 10), (236, -9, 22), (262, -3, 11), (286, -12, 28), (316, -4, 14)], S[2], CEIL, S[0])
    # long stratus streaks through the middle of the sky
    for x, y, n, c in [(40, 26, 70, 0), (52, 28, 40, 0), (196, 30, 84, 0), (214, 32, 48, 0), (120, 41, 60, 1),
                       (132, 43, 30, 1), (-10, 46, 58, 1), (250, 48, 80, 1), (268, 50, 44, 1), (150, 60, 50, 2),
                       (60, 58, 36, 2)]:
        cv.rect(x + 5, y, n - 12, 1, S[c])
        cv.rect(x, y + 1, n, 1, S[c])
    # a dark thunderhead standing behind the lit bank
    cloud(cv, THUNDER, HZ - 5, S[4], S[3], S[3])
    mask = Canvas(W, H)                               # the bank's lower part as one mass with a flat shadow:
    cloud(mask, BANK, HZ - 5, S[5], S[5], S[5], False)       # no notches or seams behind the ship's masts
    x0 = W
    for y in range(77, HZ - 5):
        x0 = min([x for x in range(W) if mask.get(x, y) != UNPAINTED] + [x0])
        cv.rect(x0, y, W - x0, 1, S[4] if HZ - 5 - y <= 2 else S[5])
    cloud(cv, BANK, HZ - 5, S[6], S[5], S[4], False)
    cloud(cv, [(10, 66, 12), (30, 70, 9), (-6, 72, 8)], 78, S[5], S[4], S[3])
    # far sea (the rows under the ship's hull stay flat: a sprite redraws them in front of it)
    bands(cv, HZ, [(99, SEA[0]), (H, SEA[1])], soft=False)
    for x, y, n in [(196, 104, 10), (290, 98, 9), (282, 103, 7), (228, 106, 8), (300, 105, 12)]:
        cv.rect(x, y, n, 1, S[4])
    # headland: lit rock above the road, darker below, darkest at the foot; grass cap
    for x in range(189):
        yt = cliff_top(x)
        for y in range(yt, H):
            k = y - 90
            sea_end = x > 168 and y > yt + 2
            cv.set(x, y, ROCKB if k > 26 or (k > 22 and (x + y) % 2) else
                   ROCKD if k > 0 or sea_end else ROCK)
        if x < 174:
            for y in range(yt, yt + 3):
                cv.set(x, y, GRASS if y < yt + 2 or x % 3 else GRASSD)
            if x % 2:
                cv.set(x, yt + 3, GRASSD)
    for x, y, n in [(8, 84, 12), (40, 82, 16), (28, 86, 8), (70, 79, 12), (96, 83, 18), (128, 80, 10),
                    (62, 85, 6), (140, 85, 9)]:
        cv.rect(x, y, n, 1, ROCKD)
    for x, y, n in [(12, 98, 18), (52, 101, 24), (104, 97, 16), (136, 102, 14), (160, 108, 12), (30, 106, 10),
                    (20, 114, 16), (70, 111, 20), (118, 116, 14), (150, 120, 10)]:
        cv.rect(x, y, n, 1, ROCK)
    # road ledge with a low wall; tunnel through the point
    cv.rect(0, 88, TUN + 4, 2, S[5])
    for x in range(0, TUN + 2, 4):
        cv.rect(x, 90, 2, 1, S[6])
    cv.rect(TUN, 80, 7, 10, DARK)
    cv.rect(TUN + 1, 79, 5, 1, DARK)
    cv.rect(TUN - 1, 79, 1, 9, ROCKD)
    # trees, the care home, the house, the fence with the green bucket hung on the gatepost
    for x, h in [(14, 10), (24, 15), (35, 11)]:
        pine(cv, x, cliff_top(x), h)
    home(cv)
    cv.blob([(101, 61, 8), (93, 66, 6), (107, 67, 5)], GRASS, GRASSD, PINE)
    house(cv, 106)
    cv.rect(156, GY - 4, 17, 1, WALL)
    for x in range(156, 174, 4):
        cv.rect(x, GY - 5, 1, 5, WALL)
    cv.rect(167, GY - 5, 5, 1, BUCKET)
    cv.rect(168, GY - 4, 3, 4, BUCKET)
    cv.rect(167, GY - 4, 1, 2, BUCKET)
    cv.rect(171, GY - 4, 1, 2, BUCKET)
    cv.rect(168, GY - 5, 3, 1, GRASSD)
    return cv


# ------------------------------------------------------------------ wave-fish strips
# Three poses, all facing left. Top profile as (distance from nose / length, height / brow height):
# 'rear' lifts its head clear of the water (Ponyo leaps off the brow); 'dive' arches over and noses
# back in (she runs down its head onto the next tail); 'breach' is the head Fujimoto stands on.
# eye = (d/L, h/H); slope tilts the mouth line; mouth is its length in head-lengths.
KIND = {
    "rear": dict(top=[(0, .42), (.115, 1), (.24, .93), (.36, .95), (.6, .7), (.82, .36), (1, 0)], eye=(.075, .63), slope=-.1, mouth=1.5),
    "breach": dict(top=[(0, .4), (.3, 1), (.5, .97), (.78, .7), (1, 0)], eye=(.2, .6), slope=-.06, mouth=.9),
    "dive": dict(top=[(0, .16), (.12, .7), (.32, 1), (.48, .93), (.7, .6), (.87, .27), (1, 0)], eye=(.1, .4), slope=.3, mouth=.5),
}


def curve(pts, u):
    """Height at u: a quarter-ellipse for the nose (first segment), a Hermite spline for the back."""
    for i in range(len(pts) - 1):
        (ua, ha), (ub, hb) = pts[i], pts[i + 1]
        if u <= ub:
            t = (u - ua) / (ub - ua)
            if i == 0:
                return ha + (hb - ha) * math.sqrt(max(0, 1 - (1 - t) ** 2))
            sl = lambda j: 0 if j <= 1 else (pts[j + 1][1] - pts[j - 1][1]) / (pts[j + 1][0] - pts[j - 1][0]) \
                if j + 1 < len(pts) else (pts[j][1] - pts[j - 1][1]) / (pts[j][0] - pts[j - 1][0])
            ma, mb = sl(i) * (ub - ua), sl(i + 1) * (ub - ua)
            return ((2 * t ** 3 - 3 * t * t + 1) * ha + (t ** 3 - 2 * t * t + t) * ma
                    + (3 * t * t - 2 * t ** 3) * hb + (t ** 3 - t * t) * mb)
    return 0


MANE = [1, 2, 1, 0, 1, 3, 1, 0, 2, 1, 0, 1]      # foam comb heights along a crest


def strip(fishes, pal, wy, h):
    """A P-wide transparent strip of overlapping wave-fish.
    fishes: [(nose x, length, brow height above the waterline row wy, kind, pupil dx, pupil dy)].
    Each fish's tail lies over the chin of the fish behind it (to its right), wrapping round the
    period. Returns (canvas, env, eyes): env[x] is the height of the top surface above wy."""
    body, rim, mid, deep, foam, foam2, eyec, dark, shade = pal
    cv = Canvas(P, h)
    for y in range(wy, h):
        k = y - wy
        for x in range(P):
            cv.set(x, y, body if k < 5 or (k < 8 and (x + y) % 2) else deep)
    for i, x in enumerate(range(8, P, 37)):
        cv.rect(x, wy + 11 + 6 * (i % 3), 10 + 4 * (i % 2), 1, body)
    env, eyes = [0.0] * P, []
    order = sorted(fishes, key=lambda f: -f[0])

    def one(f, froth, lo=0):
        x0, L, Hh, kind, pdx, pdy = f
        K = KIND[kind]
        pts = K["top"]
        big = Hh > 24
        a, hn = pts[1][0] * L, pts[0][1] * Hh
        ac, ml = a * 1.5, a * K["mouth"]
        top = lambda d: Hh * curve(pts, d / L)
        for x in range(max(x0, lo), x0 + L):
            d = x - x0 + .5
            t = top(d)
            chin = hn * (1 - math.sqrt(1 - (1 - d / ac) ** 2)) if d < ac else 0
            yt, yc = wy - round(t), wy - round(chin)
            X = x % P
            env[X] = max(env[X], t)
            # mouth: a long line that turns down at the corner, with a thin lit lower lip
            jaw = hn - 1 + K["slope"] * d - .22 * hn * (max(0, d - .8 * a) / a) ** 2
            lip = 1 + 2 * math.sin(math.pi * d / ml) if d < ml else 0
            for y in range(yt, max(yc, yt + 1)):
                c = body
                if y == yt:
                    c = rim
                elif y == yt + 1 or jaw - lip < wy - y < jaw:
                    c = mid
                elif t > 12 and y - yt > .58 * t:
                    c = shade                                # underside in shadow
                cv.set(X, y, c)
            if d < ml:
                cv.set(X, wy - round(jaw), dark)
                if d < ml * .3:
                    cv.set(X, wy - round(jaw) + 1, dark)
            # foam: a curl spilling over the brow, a combed mane behind it that thins out toward the
            # tail, and froth where this tail runs up against the face of the fish behind
            m0 = a * .6
            crest, thin = m0 < d < m0 + L * .2, m0 + L * .2 <= d < m0 + L * .5
            curl = kind != "dive" and a * .15 < d <= m0
            fr = froth[0] <= x < froth[1]
            if crest or fr or curl or (thin and X % 3):
                cv.set(X, yt, foam)
                for k in range(MANE[X % 12] if crest else MANE[X % 12] > 1 if fr else 0):
                    cv.set(X, yt - 1 - k, foam)
                if crest:
                    cv.set(X, yt + 1, foam2 if X % 4 else foam)
                if curl and big:
                    for k in range(1, 1 + MANE[X * 5 % 12]):
                        cv.set(X, yt + k, foam if k == 1 else foam2)
            elif d >= m0 + L * .5 and x * 7 % 13 < 4:
                cv.set(X, yt, foam2)
            if big and m0 + L * .1 < d < L * .78 and x * 3 % 23 < 7 and t > 9:   # water streaming off the back
                cv.set(X, yt + 3, foam2)
            for k in (6, 12):                                # contour lines following the back
                if a + 14 + 3 * k < d < L - 14 - 3 * k and (x + 5 * k) % 19 < 11 and t - k > 4:
                    cv.set(X, yt + k, mid)
        if x0 < lo:
            return
        ex, ey = x0 + round(K["eye"][0] * L), wy - round(K["eye"][1] * Hh)   # eye: ring, disc, pupil, glint
        re = 4.2 if Hh > 28 else 3.2 if Hh > 17 else 2.4
        n = int(re) + 2
        eyes.append((ex % P, ey, re))
        for y in range(-n, n + 1):
            for x in range(-n, n + 1):
                r = math.hypot(x, y)
                if r <= re + 1:
                    cv.set((ex + x) % P, ey + y, eyec if r <= re else deep)
        ps = max(1, int(re * .62))
        cv.rect((ex + pdx - ps // 2) % P, ey + pdy - ps // 2, ps, ps, dark)
        if ps > 1:
            cv.set((ex + pdx - ps // 2 + ps - 1) % P, ey + pdy - ps // 2, foam)
        gx, g = ex + n + 2, round(re) + 2                                     # gill arc and fin
        for j in range(-g, g + 1):
            cv.set((gx + round(2.4 * (1 - (j / g) ** 2))) % P, ey + 1 + j, deep)
        if re > 3:
            for i in range(5):
                cv.rect((gx + 5 + i) % P, ey + g - 1 + i, 9 - 2 * i, 1, deep if i else mid)
        for dx, dy in [(-4, 2), (2, 5), (9, 4), (16, 7), (23, 4), (31, 6)]:    # spray off the brow
            dd = a + dx
            if big or dx in (2, 16):
                cv.set((x0 + round(dd)) % P, wy - round(top(dd)) - dy, foam)

    edge = lambda b: round(b[2] * (.4 if b[3] == "rear" else .15))
    for i, f in enumerate(order):
        back = order[i - 1]                       # the fish behind this one (wraps)
        bx = back[0] + (P if i == 0 else 0)
        one(f, (bx - 5, bx + edge(back)))
    b = order[-1]
    one(order[0], (b[0] + P - 5, b[0] + P + edge(b)), lo=P)
    return cv, env, eyes


MAIN_PAL = ["#1f4596", "#5a92dc", "#2f60ba", "#173474", "#eef6f0", "#9fcbe0", "#f6f0c4", "#0c1230", "#1a3b84"]
BACK_PAL = ["#31609f", "#74a8d2", "#4278b4", "#284f8a", "#e4f0ea", "#a4cad8", "#eef0cc", "#16224a", "#2b5694"]
FRONT_PAL = ["#132c68", "#3a66ba", "#1d3f8c", "#0e2050", "#dcebee", "#7fb0d0", "#e8e6c0", "#080c24", "#10255a"]
MAIN_FISH = [(27, 138, 38, "rear", -1, 0), (153, 144, 26, "dive", -1, 1), (261, 162, 32, "rear", 0, -1)]
# strip-local waterline row and the strip's top row on screen (waterlines at 118, 136 and 162). Each
# strip only reaches down to where the next row's water (plus its heave) takes over. The back row's
# crests stop at the ship's waterline, so only the main row's biggest fish ever crosses its hull.
MAIN_WY, MAIN_Y = 46, 90
BACK_WY, BACK_Y = 26, 92
FRONT_WY, FRONT_Y = 30, 132
MAIN, ENV, EYES = strip(MAIN_FISH, MAIN_PAL, MAIN_WY, FRONT_Y + FRONT_WY + 4 - MAIN_Y)
BACK, BENV, _ = strip([(6, 96, 16, "rear", 0, 0), (82, 92, 12, "dive", 0, 0), (160, 118, 18, "rear", -1, 0),
                  (254, 80, 11, "dive", 0, 0), (322, 80, 14, "rear", 0, 0)], BACK_PAL, BACK_WY, MAIN_Y + MAIN_WY + 4 - BACK_Y)
FRONT, FENV, _ = strip([(40, 176, 20, "dive", -1, -1), (204, 232, 22, "rear", -1, -1)], FRONT_PAL, FRONT_WY, H - FRONT_Y)


def swell():
    """The fish Fujimoto rides: a single 'breach' head cut out of its strip above the waterline."""
    L, Hh = 60, 30
    cv, *_ = strip([(2, L, Hh, "breach", -1, 1)], BACK_PAL, Hh + 6, Hh + 7)
    out = Canvas(L + 4, Hh + 6)
    out.px = [row[:L + 4] for row in cv.px[:Hh + 6]]
    return out


def surf(x, w=1):
    """Screen row of the main row's surface at strip x (the highest point over w px)."""
    return MAIN_Y + MAIN_WY - round(max(ENV[(x + i) % P] for i in range(w)))


def track():
    """Ponyo's feet height above the main waterline at each STEP of scroll, starting at strip x = PX
    and moving left through the strip: the envelope, with a hop off each rearing brow. Heights are
    multiples of 3 so that the track's steps(3) between samples lands on whole pixels."""
    n = P // STEP
    hs = [ENV[(PX - STEP * i) % P] for i in range(n)]
    for x0, L, Hh, kind, *_ in MAIN_FISH:
        i = ((PX - x0) // STEP) % n
        # airborne past the nose: up off a rearing brow, or a skip over the gap below a diving one
        hs[i] = hs[i - 1] + 4 if kind == "rear" else (hs[i - 1] + hs[(i + 1) % n]) / 2 + 2
    return [3 * int((v + 1) // 3) for v in hs]


# ------------------------------------------------------------------ characters
# Ponyo, running left. She is assembled per frame from a head (two hair states, for the flutter),
# a dress (two flare states), a pair of arms and a pair of legs, then given a dark outline.
# H o O: hair highlight, mid, shadow; s S: skin, skin in shadow; b: blush and tongue; k w: eye and
# its highlight; m: inside of her mouth; e r R: dress collar, red, shadow; x: the outline.
PPAL = {"H": "#ff9a4a", "o": "#f8692c", "O": "#c43d20", "s": SKIN, "S": "#e8a482", "b": "#ff9a8a", "k": "#3a1422",
        "w": "#fff6ea", "m": "#8a1c2a", "e": "#ff6a5a", "r": "#e22a38", "R": "#a81c30", "x": "#6a1e22"}
HEAD_A = [
    ".....HHHHH",
    "...HHHHHHHHo...o",
    "..HHHooooooooooo",
    ".HHoooooooooooOooo",
    ".HoosoosoooooOOo",
    ".oosssssooooOOooo",
    ".skwsskwsoooOO.o",
    ".skksskksooOOo",
    ".sbssssbssoOO",
    "..smmmmssSO..O",
    "..ssbbssSS",
    "...sssSS",
]
HEAD_B = [HEAD_A[0], "...HHHHHHHHo..o", HEAD_A[2], ".HHoooooooooooOoo.o", HEAD_A[4], ".oosssssooooOOoo", ".skwsskwsoooOOoo",
          HEAD_A[7], HEAD_A[8], "..smmmmssSO.O", HEAD_A[10], HEAD_A[11]]
BODY_A = [
    ".....sS",
    "...eeeee",
    "...rrrrrr",
    "..rrrrrrrR",
    "..rrrrrrrrR",
    ".rrrrrrrrrRR",
    ".rrrrrrrrrrRR",
    "rrrrrrrrrrrrRR",
    "rrrrrrrrrrrrrRR.R",
    ".wwwwwwwwwwwww",
]
BODY_B = BODY_A[:7] + ["rrrrrrrrrrrrRRR", "rrrrrrrrrrrrrRR", ".wwwwwwwwwwwww"]
LEGY = 7                    # the legs hang from this row of the body; the skirt covers their top three rows
# arms as (x, y) pixels from the body's top-left, each two pixels thick: reaching ahead, swung back,
# bent at her side, flung up and out for the leap
AHEAD = [(3, 2), (2, 2), (1, 1), (0, 1), (0, 0)]
ABACK = [(9, 2), (10, 3), (11, 3), (12, 4), (13, 4)]
ABENT_L, ABENT_R = [(3, 3), (2, 4), (3, 5)], [(9, 3), (10, 4), (9, 5)]
AUP_L, AUP_R = [(3, 2), (2, 1), (1, 0), (0, -1)], [(9, 1), (10, 0), (11, -1), (12, -2)]
# one leg through the run cycle (hip at columns 5-6, the ground under the eighth row): planted ahead,
# under her, pushing off, kicked up behind, swinging through, reaching ahead
LEGS = [
    [".....ss", "....sss", "...sss", "..sss", ".sss", ".ss", ".ss", "sss"],
    [".....ss", ".....ss", ".....ss", "....sss", "....ss", "....ss", "....ss", "..ssss"],
    [".....ss", "......ss", ".......ss", "........ss", ".........ss", ".........ss", "........sss"],
    [".....ss", "......ss", ".......sss", ".........sss", "..........sss", "...........ss"],
    [".....ss", "....sss", "...sss", "..ssss", "...ssss", ".....sss"],
    [".....ss", "....sss", "..ssss", ".sss", ".ss", "sss"],
]
FW, FH, NF = 22, 30, 6      # frame cell; her feet stand on row FH - 2. She is 27 px tall, 29 with her outline
HEADH, BODYH = len(HEAD_A), len(BODY_A)


def ponyo():
    """Sprite sheet: row 0 is the six-frame run (frames 2 and 5 are the airborne beats, a pixel
    higher), row 1 the leap repeated six times so the run's frame stepping passes over it unseen."""
    sheet = Canvas(FW * NF, 2 * FH)

    def girl(col, row, head, body, near, far, legs, lift):
        cell = Canvas(FW, FH)
        y0 = 2 - lift
        yb = y0 + HEADH                                                       # top row of the body
        far_pal = dict(PPAL, s=PPAL["S"])
        cell.paint(LEGS[legs[1]], far_pal, 4, yb + LEGY)                      # far leg, far arm
        for x, y in far:
            cell.rect(1 + x, yb + y, 1, 2, PPAL["S"])
        cell.paint(LEGS[legs[0]], PPAL, 2, yb + LEGY)                         # near leg
        cell.paint(body, PPAL, 1, yb)
        cell.paint(head, PPAL, 1, y0)
        for x, y in near:                                                     # near arm, drawn over the dress
            cell.rect(1 + x, yb + y, 1, 2, PPAL["s"])
        edge = [(x, y) for y in range(FH) for x in range(FW) if cell.get(x, y) == UNPAINTED and any(
            0 <= x + dx < FW and 0 <= y + dy < FH and cell.get(x + dx, y + dy) != UNPAINTED
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        for x, y in edge:
            cell.set(x, y, PPAL["x"])
        for y in range(FH):
            sheet.px[row * FH + y][col * FW:(col + 1) * FW] = cell.px[y]

    arms = [(ABACK, AHEAD), (ABACK, AHEAD), (ABENT_R, ABENT_L), (AHEAD, ABACK), (AHEAD, ABACK), (ABENT_L, ABENT_R)]
    for i in range(NF):
        girl(i, 0, HEAD_B if i % 2 else HEAD_A, BODY_B if i % 2 else BODY_A, *arms[i], (i, (i + 3) % NF), i % 3 == 2)
        girl(i, 1, HEAD_A, BODY_A, AUP_L, AUP_R, (3, 5), 1)
    return sheet


SOSUKE = [
    "..kkkk..y",
    ".kkkkkk.s",
    ".kkssks.s",
    ".kssssss.",
    "..ssss.y.",
    ".yyyyyy..",
    "syyyyy...",
    "s.bbbb...",
    "..bbbb...",
    "...s.s...",
    "...k.k...",
]
SPAL = {"k": "#2a1c2c", "s": SKIN, "y": LAMP, "b": "#31508c"}
CAR = [
    ".........yyyyyyy....",
    "........ybkybbbby...",
    "........ybsybbbbyy..",
    ".......yyyyyyyyyyyy.",
    "h.h.hhwyyyyyyyyyyyyr",
    ".h.hhhyyyyyyyyyyyyyy",
    ".......ykkyyyyyykky.",
    "........kk......kk..",
]
CPAL = {"y": LAMP, "b": "#cfe9f2", "w": "#fff6ea", "r": "#e22a38", "k": DARK, "h": "#fff0a0", "s": SKIN}
# Fujimoto: long red hair streaming back, gaunt face, striped blazer, arms out for balance
FUJI = [
    "....hhhhhh.......",
    "...hhhhhhhhhh.h..",
    "..hhhhhhhhhhhhh..",
    "..sshhhhhhhhhhhhh",
    "..skshhhhhhh.hh..",
    "..ssshhhhhh.h....",
    "...sshhhhh.......",
    "...wjwjwwh.......",
    "..wjwjwjwj.......",
    ".wwjwjwjwjw......",
    "swwjwjwjwjww.....",
    "s.wjwjwjwj.ws....",
    "...wjwjwjw..s....",
    "...wjwjwjw.......",
    "...jjjjjjj.......",
    "...jjj.jjj.......",
    "...jjj.jjj.......",
    "...jj...jj.......",
    "...jj...jj.......",
    "...jj...jj.......",
    "..kkk..kkk.......",
]
FPAL = {"h": "#9c2c30", "s": "#f2d6c0", "j": "#22306a", "w": "#e8eef4", "k": DARK}
# The Koganei Maru, bow to the left: a dusk silhouette with lit bridge windows and portholes, a mast
# light, and Koichi on the bridge roof with his signal lamp. The last four rows ride below the water.
SHIP = [
    "..............................k...............",
    "..............................ky..............",
    "..............................k...............",
    "...........k..............s...k....kk.........",
    "...........k..............c...k....kk.........",
    "...........k.............uuuuuuuu..rr.........",
    "..........kkk............uyuyuyuu..kk.........",
    "...........k.............uuuuuuuuuuuuu........",
    "...........k.............uyuyuyuuyuyuu........",
    "....k......k......k......uuuuuuuuuuuuu....k...",
    "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk.",
    ".kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk..",
    ".kkykkkykkkykkkykkkykkkykkkykkkykkkykkkykkkk..",
    "..kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk...",
    "..rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr...",
    "...rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr....",
    "...rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr....",
    "...rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr....",
    "....rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr.....",
    "....rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr.....",
]
SHPAL = {"k": DARK, "u": S[2], "y": LAMP, "r": ROOFD, "s": SKIN, "c": "#e8eef4"}
SHX, SHWL, DRAFT = 226, 100, 4      # ship's left edge, the row of its waterline, rows kept under water


GM = 8                    # width of the clear, lit water baked around her
# Her hair: locks that stream out behind her, each a wavy ribbon with a rounded end and a lighter
# strand along it, painted back to front. The first six leave the back of her head and spread
# beneath her; the last four come out from behind her neck and fan up behind her shoulders, clear
# of her face. All of them run on past her feet. OVER are two more that lie across her gown.
# (start x, start row, length, fall per px, rise, wave height, wave length, phase, half-width, tone)
LOCKS = [(6, 22, 152, .02, 0, 2.0, 22, 0.0, 6.0, "D"), (6, 30, 158, 0, 0, 2.2, 26, 2.0, 5.5, "D"),
         (6, 26, 154, .01, 0, 2.2, 21, 1.0, 7.0, "h"), (6, 21, 114, .03, 0, 1.8, 17, 3.0, 4.5, "L"),
         (6, 32, 116, 0, 0, 2.0, 18, 4.2, 4.0, "h"), (6, 25, 80, .01, 0, 1.5, 14, 5.0, 4.5, "L"),
         (28, 14, 134, .03, 10, 1.6, 19, 1.0, 4.5, "D"), (28, 14, 150, .05, 8, 2.0, 23, 0.0, 3.5, "h"),
         (28, 15, 112, .03, 8.5, 1.5, 16, 2.5, 4.0, "h"), (30, 15, 86, .04, 6.5, 1.3, 13, 4.0, 3.2, "L")]
OVER = [(37, 11, 52, .2, 0, 1.0, 9, 0.0, 2.0, "h"), (76, 10, 58, .17, 0, 1.0, 10, 2.0, 1.8, "L")]


def goddess():
    """Granmamare gliding under the surface on her back, head first, looking up through the water:
    her face turned up and three-quarters toward us (two lowered lids, a small mouth, a soft jaw),
    the circlet arcing across her forehead with its jewel, a necklace at her throat, strands of hair
    rippling across her temple and ear; head, shoulders and a slim pale gown in one level line, an
    arm along her side; and her coral-red hair streaming out around and behind her like a cloak,
    far longer than she is, two locks of it lying across the gown. The water around her is lit
    clear in two steps of turquoise. Drawn from curves because she is 160 px long.
    Returns (canvas, alphas): the lit water is translucent through the PNG palette."""
    pal = {"p": "#fff0e2", "S": "#f6c4b0", "k": "#4a1c2c", "r": "#e2364a", "h": "#f25a44", "L": "#ff9072",
           "D": "#cc3a30", "w": "#bfe9e4", "c": "#8fcfd0", "g": "#ffe27a", "A": "#9eeaf0", "a": "#62cfe8"}
    lighter = {"D": "h", "h": "L", "L": "S"}
    darker = {"L": "h", "h": "D", "D": "D"}
    fw, fh = 166, 40
    cv = Canvas(fw + 2 * GM, fh + 2 * GM)

    def put(x, y, ch):
        if 0 <= x < fw and 0 <= y < fh:
            cv.set(int(x) + GM, int(y) + GM, pal[ch])

    def lock(xs, y0, ln, fall, rise, amp, per, ph, th, tone):
        for x in range(xs, xs + ln):
            u = (x - xs) / ln
            yc = y0 + fall * (x - xs) - rise * (1 - math.exp((xs - x) / 12)) + amp * math.sin(x / per * 2 + ph) * min(1, u * 4)
            ht = th * math.sqrt(1 - u * u)
            lo, hi = round(yc - ht), round(yc + ht)
            for y in range(lo, hi + 1):
                put(x, y, darker[tone] if y == hi and ht > 1.5 else tone)          # shaded underside
            if .06 < u < .82 and x // 11 % 4 and ht > 2.5:                         # a lighter strand running along it
                put(x, round(yc - ht * .35), lighter[tone])

    for lk in LOCKS:
        lock(*lk)
    for y in range(3, 26):                                    # her head: hair, and her face turned up and toward us
        for x in range(1, 32):
            f = ((x - 18) / 11) ** 2 + ((y - 11) / 7.5) ** 2
            if f <= 1:
                put(x, y, "S" if f > .8 and x > 22 and y > 12 else "p")            # a soft jaw
            elif ((x - 16) / 15) ** 2 + ((y - 15) / 10.5) ** 2 <= 1:
                put(x, y, "L" if y < 7 else "h")
    for x in range(27, 36):                                   # throat
        for y in range(9, 18):
            put(x, y, "S" if y == 17 else "p")
    for x in range(8, 35):                                    # hair rippling over her temple, ear and jaw:
        ya = 15.5 + math.sin(x / 3.4) + (x - 8) * .03         # a light strand across the side of her face,
        yb = 19 + math.sin(x / 3.4 + 2) + (x - 8) * .03       # the mass under it, and a dark strand through that
        for y in range(int(ya), 22):
            put(x, y, "L" if y < int(ya) + 2 else "D" if y == int(yb) else "h")
    for x in range(35, 131):                                  # the gown: slim, breast and knees a little raised
        sway = 1.2 * math.sin((x - 35) / 22)
        yt = round(13.5 + sway - 2 * math.exp(-((x - 44) / 8) ** 2) - math.exp(-((x - 105) / 9) ** 2))
        yb = round(19 + sway - max(0, x - 95) * .06)
        for y in range(yt, yb + 1):
            put(x, y, "c" if y == yb else "w")
    for x in range(131, 151):                                 # its hem fluttering out past her feet
        ht = 2.6 * (1 - (x - 131) / 20) ** .7
        yc = 16 + 1.5 * math.sin(x / 3.5)
        for y in range(round(yc - ht), round(yc + ht) + 1):
            put(x, y, "c" if y == round(yc + ht) else "w")
    for x in range(127, 131):                                 # toes
        put(x, 12, "p")
        put(x, 11, "p" if x > 128 else "w")
    for x in range(39, 77):                                   # the arm along her side
        y0 = 16.5 + (x - 39) * .03
        put(x, y0, "p")
        put(x, y0 + 1, "p" if x > 71 else "S")
    for lk in OVER:
        lock(*lk)
    face = ([(12, 5, "g"), (11, 6, "g"), (11, 7, "g"), (10, 8, "g"), (10, 9, "g"), (10, 10, "g"), (10, 11, "g"), (10, 12, "g"),
             (11, 13, "g"), (11, 14, "g"), (11, 10, "r")]                                               # circlet arcing over her forehead, its jewel
            + [(35, 10, "g"), (36, 11, "g"), (36, 12, "g"), (36, 13, "g"), (35, 14, "g")]               # necklace
            + [(17, 6, "k"), (18, 7, "k"), (17, 11, "k"), (18, 12, "k"), (18, 13, "k"), (17, 14, "k"),  # two lowered lids,
               (16, 12, "S"), (16, 13, "S")]                                                            # the nearer one shaded
            + [(22, 8, "S"), (22, 9, "S"), (21, 13, "S"), (22, 13, "S"),                                # nose, cheek
               (25, 10, "r"), (25, 11, "S")])                                                           # a small mouth
    for x, y, ch in face:
        put(x, y, ch)
    ring = [(x, y) for y in range(cv.h) for x in range(cv.w) if cv.get(x, y) != UNPAINTED]
    for d in range(1, GM + 1):                                # the lit water, growing outward
        grown = []
        for x, y in ring:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (-1, -1), (1, -1), (-1, 1)) if d % 2 else ()):
                q = (x + dx, y + dy)
                if 0 <= q[0] < cv.w and 0 <= q[1] < cv.h and cv.get(*q) == UNPAINTED:
                    cv.set(*q, pal["A" if d < 5 else "a"])
                    grown.append(q)
        ring = grown
    return cv, {hx(pal["A"]): 190, hx(pal["a"]): 95}


def scud():
    """A period of low ragged cloud, lit from below."""
    cv = Canvas(P, 20)
    for cx, n in [(40, 5), (150, 7), (268, 4)]:
        hang(cv, [(cx + 13 * i - 6 * n, 1 - (i * 5) % 4, 7 + (i * 3) % 5) for i in range(n)], S[3], CEIL, S[1])
    for y in range(2):                          # hang() also fills what lies above the circles: clear it
        for x in range(P):
            if cv.get(x, y) != UNPAINTED and cv.get(x, 2) == UNPAINTED:
                cv.px[y][x] = UNPAINTED
    return cv


# ------------------------------------------------------------------ sprites
def twice(body, pid):
    """A strip-wide thing and its copy one period to the left, so scrolling by P is seamless."""
    return f"<g id='{pid}'>{body}</g><use href='#{pid}' x='-{P}'/>"


def lids():
    """Eyelids for the main row's fish: a body-coloured disc and a lash line over each eye, shown for
    a blink. The blink runs on a group holding the lid and its <use> copy for the strip's second copy
    (an animation inside a <use> would not run)."""
    out = ""
    for i, (ex, ey, re) in enumerate(EYES):
        y, r = MAIN_Y + ey, round(re)
        out += (f"<g class='po-e' style='animation-delay:-{3 * i + 1}s'><g id='po-{7 + i}'>"
                f"<circle cx='{ex + .5}' cy='{y + .5}' r='{re + .4:g}'/>"
                f"<path stroke='#113' d='M{ex - r} {y + 1.5}h{2 * r + 1}'/></g><use href='#po-{7 + i}' x='-{P}'/></g>")
    return f"<g fill='{MAIN_PAL[0]}'>{out}</g>"


# Sosuke's candle-driven toy boat, adrift in the lowest trough of the back row (below the ship's
# waterline, so it never sits on top of her hull)
BOAT = [
    "......y......",
    "......y......",
    "...wwwwww....",
    "...wkwwkw....",
    ".ggggggggggg.",
    "ggggggggggggg",
    ".wwwwwwwwwww.",
    "..rrrrrrrrr..",
]
BOATPAL = {"y": LAMP, "w": "#fff6ea", "k": DARK, "g": "#2f9a5c", "r": ROOFD}
# In the front row's water: one of the Devonian fish (an armoured head-shield with its jointed arm,
# a scaly tail) and three jellyfish
DEVON = [
    "..aaaaaaaaaaaa....................",
    ".aaaaaaaaaaaaaa.....bb............",
    "aakaadaaaadaaaabbbbbbbbbbb......b.",
    "aaaaadaaaadaaaabbbbbbbbbbbbbb..bb.",
    "aaaaadaaaadaaaabbbbbbbbbbbbbbbbbb.",
    "aaaaadaaaadaaaabbbbbbbbbbbbbbbbb..",
    ".aaaadaaaadaaabbbbbbbbbbbbb.......",
    "..aaaaaaaaaaaa...bbbbb............",
    "...daaaaaa........................",
    "....ddaaaaa.......................",
    "......dddaa.......................",
]
JELLY = ["..ppp..", ".ppppp.", "ppppppp", "p.p.p.p", ".t.t.t.", "..t.t.."]
DEVX, JELX = 254, 94   # their places in front-strip coords


def creatures():
    """One image for the front row's swimmers, each a few rows under its own stretch of surface.
    Returns (canvas, top row on screen)."""
    under = lambda x, w: FRONT_Y + FRONT_WY - round(min(FENV[(x + i) % P] for i in range(w))) + 3
    dy, jy = under(DEVX, len(DEVON[0])), under(JELX, 32)
    top = min(dy, jy)
    cv = Canvas(DEVX + len(DEVON[0]) - JELX, max(dy + len(DEVON), jy + 11) - top)
    cv.paint(DEVON, {"a": "#b89a5a", "d": "#5a4628", "k": DARK, "b": "#7a8a5a"}, DEVX - JELX, dy - top)
    for x, y in ((0, 3), (11, 0), (23, 5)):
        cv.paint(JELLY, {"p": "#f0c8e0", "t": "#c898d0"}, x, jy - top + y)
    return cv, top


def sis(x, y, attr=""):
    return f"<use{attr} href='#po-4' x='{x}' y='{y}'/>"


def sisters():
    """The little sisters that travel with the main row (so they sit in its water or on its backs,
    behind Ponyo): a school in the third fish's flank, two riding on backs and two wriggling in the
    foam of a crest. Their bob runs on a parent of the strip's two copies."""
    cx = 302
    cy = surf(cx, 38) + 6
    school = "".join(sis(cx + dx, cy + dy) for dx, dy in [(0, 3), (9, 9), (18, 1), (22, 12), (31, 6)])
    rest = "".join(sis(x, surf(x, 7) - 3 + dip) for x, dip in [(116, 0), (214, 0), (48, 2), (284, 2)])
    return f"<g class='po-o'>{twice(school + rest, 'po-6')}</g>"


def leaper(dx):
    """A sister dx px ahead of Ponyo (negative) or behind her (positive), riding Ponyo's own height
    track: the wave under her is the wave that was, or will be, under Ponyo dx / V seconds away, so
    she runs the same keyframes with that delay. She tops the same brows and leaps off them before
    or after Ponyo does; spray marks each landing; a one-pixel wiggle keeps her swimming."""
    x, y = PX + dx - 3, FEET0 - 2
    return (f"<g class='po-j' style='animation-delay:{dx / V - (T if dx > 0 else 0):g}s'>{sis(x, y, cls('po-A'))}"
            f"<path class='po-S' stroke='#eef' d='M{x - 2} {y + 1}.5h1m9 0h1M{x} {y - 1}.5h1m5 0h1'/></g>")


TR = track()
FEET0 = MAIN_Y + MAIN_WY - TR[0]                 # feet row on screen at t=0
SWELL, RIDE = swell(), 108                       # Fujimoto's fish; how far it carries him in, and sinks
GOD, GODA = goddess()
GODY = 108                                       # her image's top row: face and glow in the main sea band
SHY = SHWL + DRAFT - len(SHIP)                   # ship image's top row
BOATX = min(range(P - len(BOAT[0])), key=lambda x: max(BENV[x:x + len(BOAT[0])]))        # its place in back-strip coords
BOATY = BACK_Y + BACK_WY - round(max(BENV[BOATX:BOATX + len(BOAT[0])])) - len(BOAT) + 1   # keel a pixel into the water
CREA, CREAY = creatures()
SPRITES = (
    # one little sister, stamped wherever one is needed
    "<defs><g id='po-4' stroke='#d43'><path d='M1 .5h4m1 0h1M2 1.5h5M1 2.5h4m1 0h1'/><path stroke='#fec' d='M0 1.5h2'/></g></defs>"
    # a bolt between the storm ceiling and the far cloud bank; scud racing under the ceiling
    "<path class='po-t' fill='none' stroke='#ffe' d='M296.5 13.5v7h-3v6h4v8h-3v7h-3v8M297.5 34.5h3v5h2v4'/>"
    f"<g class='po-c'>{twice(img(scud(), 0, 17), 'po-k')}</g>"
    # the Koganei Maru pitching in open water, Koichi's lamp and its beam; then the sea in front of
    # her hull (redrawn from the PNG) with the wash at her bow
    f"<g class='po-s'>{img(art(SHIP, SHPAL), SHX, SHY)}"
    f"<path class='po-m' stroke='#ffc' d='M{SHX + 8} {SHY + 2}.5h17M{SHX + 8} {SHY + 1}.5h11m-11 2h11"
    f"M{SHX + 8} {SHY}.5h5m-5 4h5'/></g>"
    f"<path fill='{SEA[1]}' d='M{SHX - 4} {SHWL}h{len(SHIP[0]) + 8}v{DRAFT}h-{len(SHIP[0]) + 8}z'/>"
    f"<path stroke='#eef' stroke-dasharray='3 2' d='M{SHX - 3} {SHWL}.5h13'/>"
    # Lisa's car comes out of the tunnel and runs down the cliff road
    # (Lisa at the wheel, a hand out of the window waving)
    f"<svg width='{TUN + 1}' height='99'><g class='po-v'>{img(art(CAR, CPAL), TUN + 1, 80)}"
    f"<path class='po-A' fill='{SKIN}' d='M{TUN + 10} 79h1v2h-1z'/></g></svg>"
    # the flag's fly end snapping in the wind
    f"<path class='po-3' fill='{ROOF}' d='M156 {GY - 36}h2v1h-2z'/>"
    # the ladies: a waving hand, and Toki's glasses as she looks about
    f"<path class='po-A' fill='{SKIN}' d='M{LX + 6} {LY + 3}h1v2h-1z'/>"
    f"<path class='po-A' style='animation-duration:2.5s' stroke='#113' d='M{LX + 9} {LY + 2}.5h1m1 0h1'/>"
    # Sosuke behind the fence, the lamp in his raised hand; then the fence rail and post he stands
    # behind, redrawn from the PNG because sprites always draw over it
    f"<g class='po-h'>{img(art(SOSUKE, SPAL), 158, GY - len(SOSUKE))}"
    f"<path class='po-l' fill='#ffb' d='M165 {GY - len(SOSUKE) - 2}h3v3h-3z'/></g>"
    f"<path fill='{WALL}' d='M157 {GY - 4}h3v-1h1v1h3v1h-3v3h-1v-3h-3z'/>"
    # Fujimoto rides a fish in after her from the right, then goes under
    f"<g class='po-2'>{img(SWELL, 256, 97 - 6)}{img(art(FUJI, FPAL), 270, 97 - len(FUJI))}</g>"
    # back row
    f"<g class='po-u'><g class='po-b'>{twice(img(BACK, 0, BACK_Y) + img(art(BOAT, BOATPAL), BOATX, BOATY), 'po-q')}</g></g>"
    # main row and the sisters that travel with it
    f"<g class='po-u po-n'><g class='po-w'>{twice(img(MAIN, 0, MAIN_Y), 'po-f')}{lids()}{sisters()}</g>"
    # Granmamare gliding inside that water, parked just off the right edge until her pass. The sisters
    # pass behind her (so nothing crosses her face) and show through the lit water around her; the
    # front row will pass in front of her lower hair
    f"<g class='po-G'>{img(GOD, W, GODY, alpha=GODA)}</g>"
    # one sister ahead of Ponyo and two behind, each on her path; then Ponyo herself: a nested svg
    # windows one frame of her sheet
    f"{leaper(-22)}{leaper(18)}{leaper(36)}<g class='po-j'>"
    f"<svg x='{PX - 8}' y='{FEET0 - FH + 2}' width='{FW}' height='{FH}'>"
    f"<g class='po-L'>{img(ponyo(), attr=cls('po-r'))}</g></svg></g></g>"
    # front row
    f"<g class='po-u po-g'><g class='po-x'>{twice(img(FRONT, 0, FRONT_Y) + img(CREA, JELX, CREAY), 'po-z')}</g></g>"
)


def pcs(vals):
    return ",".join(f"{v:g}%" for v in vals)


def jump_css():
    """Ponyo's height track: one keyframe per sample, samples of equal height sharing a rule."""
    n, at = len(TR), {}
    for i in range(1, n):
        at.setdefault(TR[0] - TR[i], []).append(100 * i / n)
    ks = "".join(f"{pcs(v)}{{translate:0 {dy}{'px' * (dy != 0)}}}" for dy, v in at.items())
    return f".po-j{{animation:po-j {T:g}s steps(3) infinite}}@keyframes po-j{{{ks}}}"


def splash_css():
    """Spray under a sister for the sample after each leap."""
    n = len(TR)
    hops = sorted(((PX - f[0]) // STEP) % n for f in MAIN_FISH)
    return (f".po-S{{opacity:0;animation:po-S {T:g}s steps(1) infinite;animation-delay:inherit}}"
            f"@keyframes po-S{{{pcs(100 * (i + 1) / n for i in hops)}{{opacity:1}}{pcs(100 * (i + 2) / n for i in hops)}{{opacity:0}}}}")


def leap_css():
    """Show the sheet's leap row from the sample before each nose to the sample after it."""
    n = len(TR)
    hops = sorted(((PX - f[0]) // STEP) % n for f in MAIN_FISH)
    return (f".po-L{{animation:po-L {T:g}s steps(1) infinite}}@keyframes po-L{{{pcs(100 * (i - 1) / n for i in hops)}"
            f"{{translate:0 -{FH}px}}{pcs(100 * (i + 1) / n for i in hops)}{{translate:0 0}}}}")


MORSE = {"A": ".-", "B": "-...", "E": ".", "K": "-.-", "L": ".-..", "O": "---", "V": "...-"}


def morse_css(name, word, start):
    """Keyframes that flash `word` in Morse, one percent of the period per unit, from unit `start`."""
    on, off, t = [], [], start
    for ch in word:
        for s in MORSE[ch]:
            on.append(t)
            t += 1 if s == "." else 3
            off.append(t)
            t += 1
        t += 2
    assert t < 100
    return f"@keyframes {name}{{{pcs(on)}{{opacity:1}}{pcs(off)}{{opacity:0}}}}"


GODRUN = 200                                     # seconds between Granmamare's passes, at half a pixel a tick
CSS = (
    # wave rows and scud scroll right by one period: 1 px a tick, 1 px every other tick, 2 px a tick
    f".po-w{{animation:po-w {T:g}s steps({P}) infinite}}@keyframes po-w{{to{{translate:{P}px}}}}"
    f".po-b{{animation:po-w {2 * T:g}s steps({P}) infinite}}.po-x{{animation:po-w {T / 2:g}s steps({P // 2}) infinite}}"
    f".po-c{{animation:po-w {5 * T:g}s steps({P}) infinite}}"
    # heave: 0-2 px and back
    ".po-u{animation:po-u 3s steps(3) infinite alternate}.po-n{animation-duration:3.75s;animation-delay:-2s}"
    ".po-g{animation-duration:2.25s}@keyframes po-u{to{translate:0 3px}}"
    + jump_css() + leap_css() +
    f".po-r{{animation:po-r .375s steps({NF}) infinite}}@keyframes po-r{{to{{translate:-{FW * NF}px}}}}"
    ".po-e{opacity:0;animation:po-e 10s steps(1) infinite}@keyframes po-e{97.5%{opacity:1}}"
    ".po-v{animation:po-v 40s -35s steps(640) infinite}@keyframes po-v{to{translate:-640px}}"
    # sisters: the ones in the wave bob with it; the three beside Ponyo run her track with their own
    # delay (set inline), and their landing spray inherits that delay
    ".po-o{animation:po-u 1.5s steps(3) infinite alternate}"
    + splash_css() +
    # Granmamare glides right to left through the main row's water, then stays parked far off-canvas
    f".po-G{{animation:po-G {GODRUN}s 75s steps({GODRUN * 8}) infinite}}@keyframes po-G{{to{{translate:-{GODRUN * 8}px}}}}"
    # Fujimoto: in from off-canvas right at 1 px every other tick, a pause, straight down at 1 px a tick
    # (a 100 s loop, so each leg starts on a whole tick: 1 s, 14.5 s, 17.5 s. He is on screen from 40 s
    # to 63 s of every 100; Granmamare, every 200 s from 75 s to 138 s, always falls between his visits)
    f".po-2{{translate:{RIDE}px {RIDE}px;animation:po-2 100s -61s steps({RIDE}) infinite}}"
    f"@keyframes po-2{{1%{{translate:{RIDE}px 0}}14.5%,17.5%{{translate:0 0}}24.25%{{translate:0 {RIDE}px}}"
    f"24.35%{{translate:{RIDE}px {RIDE}px}}}}"
    ".po-t{opacity:0;animation:po-t 25s steps(1) infinite}@keyframes po-t{40%,41.5%{opacity:1}40.5%,42%{opacity:0}}"
    ".po-3{animation:po-3 .5s steps(1) infinite}@keyframes po-3{50%{opacity:0}}"
    # the ship climbs a swell and settles: a pixel every half second, three at most
    ".po-s{animation:po-s 20s steps(1) infinite}@keyframes po-s{40%,55%{translate:0 -1px}42.5%,52.5%{translate:0 -2px}"
    "45%{translate:0 -3px}57.5%{translate:0 0}}"
    ".po-h{animation:po-h 10s steps(1) infinite}@keyframes po-h{90%,95%{translate:0 -1px}92.5%{translate:0 0}}"
    ".po-A{animation:po-A 1.5s -.5s steps(1) infinite}@keyframes po-A{50%{translate:1px}}"
    # the lamps talk in Morse, one unit = 5 ticks: the house sends BAKA, the ship answers LOVE
    ".po-l,.po-m{opacity:0;filter:drop-shadow(0 0 2px #fe6);animation:po-l 31.25s steps(1) infinite}"
    ".po-m{animation-name:po-m}" + morse_css("po-l", "BAKA", 0) + morse_css("po-m", "LOVE", 50)
)
