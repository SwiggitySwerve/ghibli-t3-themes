"""Nausicaa of the Valley of the Wind: the valley seen from the edge of the Sea of Corruption.
An Ohmu crawls across the jungle floor, its legs stepping in a wave and its armour plates rippling
with them, a young one at its tail; Nausicaa escorts it on her Mehve with Teto on her shoulder; Lord
Yupa watches from Kai, his horseclaw, with Kui behind under a pack, beside a shed Ohmu shell; the castle with its great wind wheel and the windmills stand on golden hills behind, where three Valley girls wave; a fossil God Warrior stands in the far haze.

320x180. Static layers, so things can pass between them:
  draw()    sky gradient (the base PNG)
  mid()     God Warrior, cumulus, snow range, hills, castle, mills, the girls  (nested PNG)
  jungle()  far fungi, the jungle floor, mid fungi                     (nested PNG)
  near()    the giant framing fungi, pods, foreground ferns            (nested PNG)
Sprites, back to front: cirrus streaks, Tolmekian fleet | mid | wind wheel and windmill
sails (stepped sprite sheets), streamer, the waving hands of the girls, wind gusts, Valley gunship +
shadow | jungle | the Ohmu (shadows, the young one and its legs, 9 leg pairs, 7 shell segments cut
from one image, eye glow), Yupa on Kai, Mehve with Nausicaa and Teto | near | spore-pod glints,
drifting spores, a royal yanma.

The Ohmu walks 1px per 0.125s. A stride is 12 of those ticks: each leg pair stays planted for 9
(sliding back under the body exactly as fast as the body advances), then lifts and swings forward
for 3. Each pair runs one tick behind the pair in front, so the wave travels from head to tail. The
shell undulates along its length with it: as a segment's legs swing, that segment slides 1px forward
and stays there for half the stride, so plates telescope into the one ahead and draw out again in
turn. Strips overlap by 1px, and offsets are only ever 0 or 1, so no gap can open. The young one
at its tail is rigid and takes quick short steps: its six legs are planted for 3 ticks and lifted
for 1, each one tick behind the leg in front.

The Ohmu and Nausicaa repeat every 60s, the story every 120s, and three later moments every 240s, so the
two halves of the loop differ. t = 0 is the still the build
tools show and where the scene opens, so it is a quiet moment: she is drifting back and nothing else is
under way. (Every story animation is delayed -105s from where it was first written: a whole number of
the Ohmu's 1.5s strides and of the 15s wind cycle, so legs and rotor stills stay in step.)
  50.6s, 110.6s   the Ohmu's head comes in from the left, fully in view 10.5s later; it crosses and leaves
                  to the right by 50.5s / 110.5s, the young one last
  14.25-21.25s,   Nausicaa, hovering right of the castle, turns as its head passes under her and, with a
  74.25-81.25s    puff from her jet, glides along just behind its head at its pace; in clear sky short of the
                  right windmill she turns and drifts back, facing the next crossing. The three girls wave
                  her off (for 4.8s), and now and then she blinks
  21-32s          a yanma flies across
  42-84s          the Tolmekian fleet crosses behind the castle; the Ohmu's eyes flush red (55-73.5s) as it
                  comes in, the young one's with them, and calm to blue as it reaches Nausicaa; the wind dies
                  with the rage (57.3-72.3s: rotors, streamer and gusts stop, and Kai and Kui rear up, heads
                  high and beaks open, as it rages past behind them), and as the eyes calm four golden feelers
                  rise from its head towards her (71-84s). The young one stays red until it is out from behind
                  the birds, and calms last (by 84s)
  44.4-48.6s      a spore pod by the right-hand fungus bursts in a puff of spores (240s loop)
  94.8s, 154.8s   the last lens left in the shed shell glints (240s loop)
  103-112s        the Valley gunship skims the fields
  204-234s        spores fall like snow around Yupa (240s loop)
Everything that travels moves in whole-pixel steps.
"""
import base64, math, random, struct, zlib
from lib import Canvas, UNPAINTED

NAME = "Nausicaa of the Valley of the Wind"
SIZE = W, H = 320, 180
COLORS = 16
THEME = {"position": "center 60%",  # wide panes crop vertically; see build wide.png
         
    "canvas": "#12112a", "accent": "#7fd0ff", "overlay": "#10132c",
    "colors": {"sidebar": "#161432", "sidebarRowSelected": "#2c2860", "sidebarBorder": "#2a2654",
               "surface": "#1b1940", "border": "#353070", "text": "#eef0fa", "textMuted": "#a9a8cc"},
}

S = ["#2857a4", "#3a74c0", "#5a98d6", "#86bbe6", "#b6dbee", "#f1e6c0"]     # sky top -> horizon haze
WHITE = "#ffffff"
C1, C2, C3 = "#e4eff8", "#bdd6ec", "#98bbdc"                               # cloud shade tones
M0, M1, N1 = "#a9c6e4", "#7fa5d0", "#cfe0f0"                               # range: lit, shadow, snow shadow
G0, G1, G2 = "#f0cc62", "#d6a23c", "#ad7a2c"                               # golden fields
V0, V1, V2 = "#b9c468", "#7fa450", "#4c7846"                               # meadow, field green, trees
ST0, ST1, ROOF, BRN = "#f2e6c0", "#b9a47e", "#8c5a48", "#4a3432"           # stone lit/shade, roof, dark wood
CLOTH = "#e9d6a4"                                                          # windmill sails
J0, J1, J2, J3, J4 = "#110f28", "#1e1a46", "#322a68", "#463a86", "#6a5aa8"  # jungle indigo -> lavender
T0, T1, T2 = "#256f84", "#3aa6a8", "#7ee6dc"                               # teal shade, teal, glow
P0, P1 = "#9488cc", "#d6cef6"                                              # pale spore blooms
O0, O1, O2, O3, O4 = "#232f58", "#3a5282", "#55749e", "#7c9cc0", "#b6cee2"  # Ohmu shell dark -> highlight
E0, E1, E2 = "#17306e", "#2c68c8", "#4c9cf0"                               # Ohmu eye: socket, dome shade, dome

OL, OH, OB = 126, 40, 149             # Ohmu: length, height, base row. It is drawn with its tail at x = 0.
PW, HEAD, LEAN = 14, 42, 9            # plate width; head shield (the front 42px, with the eyes); seam lean
# Ohmu eyes: (centre x, centre y, radius). Half-pixel radii give odd diameters (2.5 -> 5px, 3.5 -> 7px).
EYES = [(x, OB + y, r) for x, y, r in [(93, -31, 2.5), (102, -32, 3.5), (112, -26, 3.5), (98, -22, 3.5),
                                       (106, -18, 2.5), (117, -17, 2.5), (112, -10, 2.5), (102, -10, 2.5)]]
GLOWS = []                            # (x, y) of every glow point painted by jungle() and near(), for the glints


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
    """Separable box blur of a 2D list, radius r."""
    for _ in range(2):
        a = [[sum(row[max(0, x - r):x + r + 1]) / (2 * r + 1) for x in range(len(row))] for row in a]
        a = [list(col) for col in zip(*a)]
    return a


def cumulus(cv, lumps, base, tones=(WHITE, C1, C2, C3), cuts=(.62, .47, .3)):
    """Painterly cumulus. The lumps are spheres whose union is a height field; shading comes from the
    normal of a blurred copy (broad lit and shadowed masses rather than a pile of shaded balls) plus a
    little of the sharp one for puff edges, cut into flat tones. Flat base at row `base`."""
    xs = [v for cx, cy, r in lumps for v in (cx - r, cx + r)]
    x0, x1 = max(0, int(min(xs)) - 1), min(cv.w, int(max(xs)) + 2)
    y0 = max(0, int(min(cy - r for cx, cy, r in lumps)) - 1)
    w, h = x1 - x0, base - y0
    hg = [[0.0] * w for _ in range(h)]
    for cx, cy, r in lumps:
        for y in range(max(y0, int(cy - r) - 1), min(base, int(cy + r) + 2)):
            for x in range(max(x0, int(cx - r) - 1), min(x1, int(cx + r) + 2)):
                d2 = (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2
                if d2 < r * r:
                    hg[y - y0][x - x0] = max(hg[y - y0][x - x0], math.sqrt(r * r - d2))
    hb = blur(hg, 4)

    def lum(a, x, y):
        gx = a[y][min(w - 1, x + 1)] - a[y][max(0, x - 1)]
        gy = a[min(h - 1, y + 1)][x] - a[max(0, y - 1)][x]
        nx, ny = -gx / 2, -gy / 2
        return (-.5 * nx - .72 * ny + .48) / math.sqrt(nx * nx + ny * ny + 1)

    for y in range(h):
        for x in range(w):
            if hg[y][x] > 0:
                i = .7 * lum(hb, x, y) + .3 * lum(hg, x, y) - .2 * y / h
                k = sum(i < c for c in cuts)
                if h - y <= 2:
                    k = max(k, 2)
                cv.set(x + x0, y + y0, tones[k])


def poly(cv, pts, c):
    """Fill a polygon (pixel centres inside)."""
    ys = [p[1] for p in pts]
    for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
        yc, xs = y + .5, []
        for (xa, ya), (xb, yb) in zip(pts, pts[1:] + pts[:1]):
            if (ya <= yc) != (yb <= yc):
                xs.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            for x in range(int(math.ceil(a - .5)), int(math.floor(b - .5)) + 1):
                cv.set(x, y, c)


def hill(cv, f, c, top=None):
    for x in range(W):
        y = int(round(f(x)))
        cv.rect(x, y, 1, H - y, c)
        if top:
            cv.set(x, y, top)


# ------------------------------------------------------------------ base layer: sky
def draw():
    cv = Canvas(W, H)
    bands(cv, 0, [(13, S[0]), (33, S[1]), (52, S[2]), (69, S[3]), (84, S[4]), (H, S[5])])
    return cv


# ------------------------------------------------------------------ mid layer: clouds, range, valley
def far_hill(x):
    return 96 + 2 * math.sin(x * .021 + 1) + 1.2 * math.sin(x * .05 + 2)


def castle_hill(x):
    return 101 + 2.5 * math.sin(x * .026 + 1) + 1.5 * math.sin(x * .06) - 10 * math.exp(-((x - 120) / 27) ** 2)


def mid_hill(x):
    return 112 + 3 * math.sin(x * .022 + 4) + 1.5 * math.sin(x * .07 + 1)


def mountains(cv):
    """Snow range: each peak has a lit left face and a shadowed right face, split by a ridge that
    wanders down and to the right from the summit; snow above a wavy line."""
    peaks = [(8, 17), (40, 22), (68, 15), (100, 19), (150, 23), (184, 17), (214, 21), (248, 16), (282, 23), (316, 18)]
    for x in range(W):
        v, px, ph = max((ph - abs(x - px) * (.62 if x < px else .5), px, ph) for px, ph in peaks)
        t = int(round(v + .8 * math.sin(x * .9) + .6 * math.sin(x * .37 + 1)))
        for y in range(96 - t, 97):
            lit = x < px + (y - 96 + ph) * .4 + 1.3 * math.sin(y * .8 + px)
            snow = 96 - y > 11 + 2 * math.sin(x * .5) + (0 if lit else 3)
            cv.set(x, y, (WHITE if lit else N1) if snow else (M0 if lit else M1))


MILLS = [(84, 80, 8), (198, 85, 6), (246, 80, 8)]     # small windmills: tower x, hub y, sail radius (the middle one
                                                    # smaller, so its sails stay clear of her bob on a full-height tower)


def tower(cv, x, base, hub):
    """Slender tapering windmill tower; the sails are a sprite centred on (x, hub)."""
    for y in range(hub - 3, base + 2):
        hw = 1 + (y - hub) // 12
        cv.rect(x - hw, y, 2 * hw + 1, 1, ST1)
        cv.rect(x - hw, y, hw, 1, ST0)
    cv.rect(x - 2, hub - 4, 5, 2, ROOF)
    cv.rect(x - 1, hub - 5, 3, 1, ROOF)
    cv.rect(x, base - 2, 1, 3, BRN)


def house(cv, x, y, w=5):
    cv.rect(x, y - 3, w, 3, ST0)
    cv.rect(x + w - 2, y - 3, 2, 3, ST1)
    cv.rect(x - 1, y - 5, w + 2, 2, ROOF)
    cv.rect(x, y - 6, w, 1, ROOF)
    cv.set(x + 1, y - 2, BRN)


def trees(cv, x, y, n):
    for i in range(n):
        cx, r = x + 4 * i, 3 if i % 2 else 2
        for dy in range(-r, 1):
            ww = int(round(math.sqrt(r * r - dy * dy))) + 1
            cv.rect(cx - ww, y + dy - (i % 2), 2 * ww, 1, V2)
            if dy < -r + 2:
                cv.rect(cx - ww, y + dy - (i % 2), ww, 1, V1)


CX, CY = 116, 58      # hub of the castle's great wind wheel


def castle(cv):
    """The Valley's castle: an irregular cluster on a rock. A tall tapering keep carries the great
    wind wheel (sprite); a hall with a pitched roof and a watchtower with a streamer stand to its
    right, a low gatehouse to its left, and a stair runs down the hill."""
    by = 91
    for x in range(95, 151):                           # rock outcrop
        t = int(round(3 + 1.5 * math.sin(x * .7) + (x % 7 == 3)))
        cv.rect(x, by - t, 1, t + 3, ST1)
        cv.set(x, by - t, ROOF if x % 5 < 2 else ST1)
    cv.rect(98, 77, 12, 12, ST0)                       # gatehouse, flat roof with a parapet
    cv.rect(106, 77, 4, 12, ST1)
    cv.rect(97, 75, 14, 2, ST1)
    for x in (97, 101, 105, 109):
        cv.rect(x, 73, 2, 2, ST1)
    cv.rect(101, 82, 3, 7, BRN)
    cv.rect(102, 81, 1, 1, BRN)
    for y in range(47, by - 1):                        # the keep: tall, tapering, lit from the left
        hw = 5 + (y - 47) // 14
        cv.rect(CX - hw, y, 2 * hw + 1, 1, ST0)
        cv.rect(CX + 1, y, hw, 1, ST1)
    cv.rect(CX - 7, 45, 15, 2, BRN)                    # wooden gallery under the cap
    for i in range(4):
        cv.rect(CX - 5 + i, 44 - i * 2, 11 - 2 * i, 2, ROOF)
    cv.rect(CX, 35, 1, 3, BRN)
    for x, y in [(CX - 3, 72), (CX - 3, 79), (CX + 3, 76), (CX + 3, 84)]:
        cv.rect(x, y, 1, 3, BRN)
    cv.rect(124, 71, 17, by - 71, ST0)                 # hall with a pitched roof
    cv.rect(135, 71, 6, by - 71, ST1)
    for i in range(5):
        cv.rect(123 + i, 70 - i, 19 - 2 * i, 1, ROOF)
    for x in (127, 131):
        cv.rect(x, 76, 1, 3, BRN)
    cv.rect(128, 83, 4, 6, BRN)                        # hall door and the stair down the hill
    for i in range(6):
        cv.rect(131 + 3 * i, 89 + i * 2 // 3, 4, 1, ST0)
    cv.rect(141, 63, 7, by - 63, ST0)                  # watchtower with a cone roof and a flagpole
    cv.rect(145, 63, 3, by - 63, ST1)
    for i in range(4):
        cv.rect(140 + i, 62 - 2 * i, 9 - 2 * i, 2, ROOF)
    cv.rect(144, 47, 1, 9, BRN)
    cv.rect(143, 68, 1, 3, BRN)


# A fossil God Warrior, far off in the haze: the same tone as the range's shadow, standing behind it.
GIANT = [
    ".......#####.........",
    "......#######........",
    "......##.#.##........",
    "......#######........",
    ".......#.#.#.........",
    "........###..........",
    ".#...#########...#...",
    "###.###########.###..",
    "#####.#######.#####..",
    "###..#.#####.#..###..",
    "##...#########...##..",
    "##...#.#####.#...##..",
    "##....#######....##..",
    "##....#.###.#....##..",
    "#......#####......#..",
    "#.......###.......#..",
    "........###..........",
    ".......#####.........",
    "......#######........",
] + ["......##...##........"] * 11
KIDS = [(152, 106, ROOF), (157, 107, WHITE), (162, 105, M1)]      # Valley girls on the hill: x, feet row, dress


def mid():
    cv = Canvas(W, H)
    cv.paint(GIANT, {"#": M1}, 205, 47)
    cumulus(cv, [(34, 52, 15), (58, 60, 14), (16, 66, 15), (80, 72, 12), (44, 76, 18), (100, 82, 9), (0, 80, 14),
                 (70, 86, 14)], 97)
    cumulus(cv, [(286, 46, 16), (262, 60, 13), (308, 60, 16), (244, 74, 11), (276, 76, 18), (226, 84, 8),
                 (318, 82, 14), (252, 88, 12)], 97)
    cumulus(cv, [(172, 82, 7), (160, 87, 6), (186, 88, 7), (148, 91, 5), (198, 92, 5)], 97)
    mountains(cv)
    # the valley, back to front: hazy meadow, the castle's golden hill, a nearer darker field
    hill(cv, far_hill, V0)
    for x in range(W):                                 # hedgerow dashes on the far meadow
        if x % 12 < 5:
            cv.set(x, int(round(far_hill(x))) + 2, V1)
    hill(cv, castle_hill, G0)
    for x0, x1, c, d in [(30, 74, V1, V2), (166, 190, V1, V2), (214, 262, G1, G2)]:   # field patches
        for x in range(x0, x1):
            y = int(round(castle_hill(x))) + 3
            for dy in range(0, 7):
                if abs(x - (x0 + x1) / 2) < (x1 - x0) / 2 - dy * .2:
                    cv.set(x + dy, y + dy, d if dy % 2 else c)
    castle(cv)
    trees(cv, 66, 96, 3)
    trees(cv, 156, 95, 4)
    trees(cv, 226, 100, 2)
    house(cv, 60, 100)
    house(cv, 170, 99, 6)
    house(cv, 181, 101)
    house(cv, 262, 103, 6)
    for x, hub, _ in MILLS:
        tower(cv, x, int(castle_hill(x)) + 2, hub)
    hill(cv, mid_hill, G1, G0)
    for dy in (4, 8, 12, 16):                          # furrows following the slope
        for x in range(W):
            if (x + dy * 3) % 16 < 11:
                cv.set(x, int(round(mid_hill(x))) + dy, G2)
    for i, (x, y, c) in enumerate(KIDS):               # hair, face, a dress that flares
        cv.rect(x, y - 5, 2, 1, BRN)
        cv.rect(x, y - 4, 2, 1, ST0)
        cv.rect(x, y - 3, 2, 1, c)
        cv.rect(x - i % 2, y - 2, 3, 2, c)
    return cv


# ------------------------------------------------------------------ front layer: Sea of Corruption
def floor(x):
    return 130 + 2 * math.sin(x * .045) + 1.2 * math.sin(x * .11 + 1)


def glow(cv, x, y, w=1):
    cv.rect(x, y, w, 1, T2)
    GLOWS.append((x, y))


def cap(cv, x, top, hw, body, lit, under, lights=True):
    """Mould-tree cap: a dome lit from the upper left, a gilled and scalloped underside, hanging
    filaments with the odd glowing tip. Returns the row of its underside."""
    ch = max(3, int(hw * .62))
    for i, dx in enumerate(range(-hw + 2, hw - 1, 3)):         # filaments
        n = 3 + (i * 7 + hw) % 7
        cv.rect(x + dx, top + ch, 1, n, body)
        if lights and i % 3 == 1:
            glow(cv, x + dx, top + ch + n)
    for dy in range(ch + 1):
        w = int(round(hw * math.sqrt(1 - ((ch - 1 - min(dy, ch - 1)) / ch) ** 2)))
        for dx in range(-w, w + 1):
            edge = w - abs(dx)
            c = body
            if dy == ch:                                       # scalloped lip
                if (dx + hw) % 6 > 2 or edge < 1:
                    continue
            elif dx < w * .3 and (edge < 2 or dy < 2) and dy < ch - 2:
                c = lit
            elif dy == ch - 2:
                c = under                                      # shaded band above the lip
            cv.set(x + dx, top + dy, c)
    if lights:
        for i in range(hw // 5):
            glow(cv, x - hw // 2 + i * 7 + (i % 2), top + ch // 2 + (i * 3) % 4, 2)
    return top + ch


def fungus(cv, x, base, top, hw, body, lit, under, sw=1, lights=True, shelves=()):
    """Giant mould tree: a flared stalk, a main cap, and smaller shelf caps on short branches.
    shelves: [(dx from the stalk, top row, half width)]."""
    for y in range(top + 2, base):
        k = sw + (2 if y > base - 4 else 1 if y > base - 12 else 0)
        cv.rect(x - k, y, 2 * k + 1, 1, body)
        cv.set(x - k, y, under)
    for dx, st, shw in shelves:
        yb = cap(cv, x + dx, st, shw, body, lit, under, lights)
        for i in range(abs(dx) + 1):                           # branch rising from the stalk
            cv.rect(x + (i if dx > 0 else -i), yb + (abs(dx) - i) * 2 // 3, 1, 2, body)
    yb = cap(cv, x, top, hw, body, lit, under, lights)
    cv.rect(x - sw - 1, yb, 2 * sw + 3, 3, body)               # flare under the cap


def puff(cv, x, base, h, body, lit):
    """Spore bloom: a thin stalk carrying a cluster of puffballs."""
    cv.rect(x, base - h, 1, h, body)
    for cx, cy, r in [(x - 3, base - h + 1, 2.6), (x + 3, base - h, 2.6), (x, base - h - 2, 3.6)]:
        for yy in range(int(cy - r), int(cy + r) + 2):
            for xx in range(int(cx - r), int(cx + r) + 2):
                d = math.hypot(xx - cx, yy - cy)
                if d <= r:
                    cv.set(xx, yy, lit if (xx - cx) + (yy - cy) < -r * .5 else body)


def tubes(cv, x, base, hs, c, mouth):
    """Organ-pipe fungi with glowing mouths."""
    for i, h in enumerate(hs):
        cv.rect(x + 4 * i, base - h, 3, h, c)
        cv.rect(x + 4 * i, base - h, 3, 1, mouth)
        glow(cv, x + 4 * i + 1, base - h)


def pod(cv, cx, cy, r, c, hi):
    """Spore pod: a ball on a short stem with a lit shoulder and a glow point."""
    cv.rect(cx, cy, 1, r + 3, c)
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if math.hypot(x - cx, y - cy) <= r + .3:
                cv.set(x, y, hi if (x - cx) + (y - cy) < -r * .6 else c)
    glow(cv, cx - r // 2, cy - r // 2)


def frond(cv, x, base, h, lean, c):
    """Curling fern-like silhouette."""
    for i in range(h):
        t = i / h
        fx = x + int(round(lean * t * t))
        cv.rect(fx, base - i, 2 if t < .6 else 1, 1, c)
        if i % 3 == 1 and .15 < t < .95:
            n = int(4 * (1 - t)) + 1
            cv.rect(fx - n, base - i + 1, n, 1, c)
            cv.rect(fx + 1, base - i, n, 1, c)
    cv.rect(x + int(round(lean)) + (1 if lean > 0 else -2), base - h + 1, 2, 2, c)


def eye(cv, cx, cy, r, tones, rings=()):
    """Dome eye: a disc of diameter 2r with a darker lower-right crescent and a highlight.
    rings: [(extra radius, colour)] painted outside the disc, nearest first (socket, halo)."""
    R = int(r + 4)
    for y in range(-R, R + 1):
        for x in range(-R, R + 1):
            d = math.hypot(x, y)
            if d <= r + .1:
                cv.set(cx + x, cy + y, tones[1] if (x + y) > r * .75 else tones[0])
            else:
                for extra, c in rings:
                    if d <= r + extra:
                        cv.set(cx + x, cy + y, c)
                        break
    k = 1 if r < 3 else 2
    cv.rect(cx - k, cy - k, k, 1, tones[2])
    if k == 2:
        cv.set(cx - 2, cy - 1, tones[2])


def ohmu_top(x):
    pts = [(0, 5), (.05, 11), (.16, 21), (.34, 31), (.54, 37), (.70, 40), (.82, 38), (.90, 33), (.96, 24), (1, 12)]
    t = x / OL
    for (t0, h0), (t1, h1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            return h0 + (h1 - h0) * (t - t0) / (t1 - t0)


def ohmu():
    """The Ohmu's body, tail at x = 0, head to the right, no legs. Six armour plates and a head shield
    that carries the dome eyes. A plate's rear lip is raised and lit; its front sits in the shadow of
    the plate ahead. The shell is cut into vertical strips that move on their own, so every seam
    starts on a strip boundary at the top of the shell and only sweeps forward as it descends."""
    cv = Canvas(W, H)
    edges = [OL - HEAD - PW * j for j in range(6)]

    def seam(b, y):
        return b + LEAN * max(0, (y - OB + ohmu_top(b)) / OH) ** 1.3

    for x in range(OL + 1):
        kt = (OL - HEAD - 1 - x) % PW             # px back from the strip's front edge
        h = int(round(ohmu_top(x))) + (0 if x >= OL - HEAD else 2 if kt >= PW - 2 else 1 if kt >= PW - 4 else 0)
        top = OB - h

        def where(y):
            """(px back from the seam ahead, px forward of the seam behind); 99 where there is none."""
            xs = [seam(b, y) for b in edges]
            return min([v - x for v in xs if v > x] or [99]), min([x - v for v in xs if v <= x] or [99])

        k, r = where(OB - 5)
        bot = OB - 4 + (1 if k > 3 and r > 2 else 0) - (1 if k <= 1 or r < 1 else 0)      # scalloped skirt
        for y in range(top, bot):
            k, r = where(y)
            d = y - top
            c = O2
            if d < 1:
                c = O4
            elif d < 4 + (2 if x < OL * .6 else 0):
                c = O3
            elif y > OB - 13 or x > OL * .94:
                c = O1                            # belly shade
            if k <= 1:
                c = O0                            # seam
            elif k <= 2.5:
                c = O1 if c != O1 else O0         # in the shadow of the plate ahead
            elif r < 1 and d > 0:
                c = O4 if y < OB - 14 else O3     # raised rear lip
            elif r < 2 and 4 <= d < 12 and c == O2:
                c = O3                            # sheen on the swell behind the lip
            cv.set(x, y, c)
        cv.rect(x, bot, 1, OB - 2 - bot, O0)      # underside
    for dx, n in [(0, 5), (-3, 3), (3, 2)]:       # mouthparts under the head
        cv.rect(OL - 3 + dx, OB - 7, 1, n + 2, O0)
    for cx, cy, r in EYES:
        eye(cv, cx, cy, r, (E2, E1, WHITE), [(1.2, E0)])
    return cv


def baby():
    """The young Ohmu that trails the big one: 30px long, the same armour in miniature, three eyes."""
    hs = [2, 3, 4, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 10, 11, 11, 11, 11, 11, 11, 11, 10, 10, 9, 8, 7, 6, 4, 3]
    cv = Canvas(30, 11)
    for x, h in enumerate(hs):
        for y in range(11 - h, 11):
            d = y - 11 + h
            seam, lip = x < 20 and x % 5 == 4, x <= 20 and x % 5 == 0 and y < 7
            cv.set(x, y, O0 if y == 10 or seam else O4 if d == 0 or lip else O3 if d == 1 else O1 if y > 7 else O2)
    for x, y in [(22, 2), (22, 6), (25, 5)]:
        cv.rect(x, y, 2, 2, E2)
        cv.set(x, y, WHITE)
    return cv


BABY_EYES = [(-10, 139), (-10, 143), (-7, 142)]   # the young one's eyes on the canvas, as img(baby(), -32, OB - 12) places them


SHELL_X, SHELL_B = 92, 133         # the shed shell's left end and base row; its last lens at (SHELL_X + 5, SHELL_B - 9)


def shell(cv):
    """A shed Ohmu shell lying on the jungle floor, head to the left: bleached pale, the plates the same as
    the live one's, the eye sockets empty and dark but for one lens, and the hollow underside open."""
    hs = [6, 8, 10, 11, 12, 13, 13, 13, 13, 12, 12, 12, 11, 11, 11, 10, 10, 9, 9, 8, 8, 7, 7, 6, 5, 5, 4, 3, 2, 2]
    for x, h in enumerate(hs):
        for y in range(SHELL_B - h, SHELL_B):
            d = y - SHELL_B + h
            seam = x > 9 and x % 4 == 1
            cv.set(SHELL_X + x, y, "#3e4660" if seam or x == 9 else "#d0d8e2" if d == 0 or (x > 9 and x % 4 == 2 and d < 5)
                   else "#a8b4c6" if d < 3 else "#5e6a84" if y > SHELL_B - 4 else "#8492aa")
        if 2 < x < 27:                                  # the hollow, open along the bottom
            cv.rect(SHELL_X + x, SHELL_B - 2 - (x % 3 == 0), 1, 3, J1)
    for x, y in [(2, -7), (6, -6), (3, -4)]:            # empty sockets
        cv.rect(SHELL_X + x, SHELL_B + y, 2, 2, J1)
    cv.rect(SHELL_X + 4, SHELL_B - 10, 3, 3, "#9fd8f6")  # the one lens left in it
    cv.set(SHELL_X + 4, SHELL_B - 10, WHITE)


def tendrils():
    """The golden feelers the Ohmu raise when they calm, drawn behind the shell and risen 24px through it.
    Drawn as they stand at the peak: k px above the shell top, each bows outward from its root, then curves in
    so its tip reaches towards Nausicaa (above x ~102), with a gentle sway all of them share. A pale luminous
    core with a 1px deep-gold edge on its shaded (right) side, so it holds against the golden field, tapers
    from 2px at the root to 1px, then loses its edge for the last few px up to a bright tip."""
    cv = Canvas(W, H)
    for bx, h, out, tip in [(86, 14, -2, 92), (95, 19, -1, 99), (104, 22, 0, 104), (113, 16, 1, 109)]:
        y0, px = OB - round(ohmu_top(bx)) + 24, None
        for k in range(-4, h + 1):
            u = max(0, k) / h
            x = bx + round(out * math.sin(math.pi * u) + (tip - bx) * u * u + .8 * math.sin(k * .22))
            w = 2 if k < h * .4 else 1
            for xx in range(min(x, px if px is not None else x), max(x, px if px is not None else x) + w):
                cv.set(xx, y0 - k, "#fff2b0" if k > h - 2 or xx < x + w - 1 or w == 1 and k < h * .7 else "#ffe27a")
            if k < h * .75:
                cv.set(x + w, y0 - k, "#b8780e")
            px = x
    return cv


def jungle():
    """Behind the Ohmu: hazy fungi on the last of the fields, the jungle floor, mid-distance fungi."""
    cv = Canvas(W, H)
    GLOWS.clear()
    for x, top, hw in [(22, 112, 9), (128, 116, 8), (178, 119, 6), (236, 116, 8), (292, 109, 10), (306, 118, 6)]:
        fungus(cv, x, 133, top, hw, J4, T1, J3, lights=False)
    for x, h in [(38, 12), (154, 12), (204, 9), (224, 9)]:
        puff(cv, x, 133, h, P0, P1)
    for x in range(W):
        y = int(round(floor(x)))
        cv.rect(x, y, 1, H - y, J3)
        cv.set(x, y, T1 if (x // 5) % 3 else J4)
    for y0, c in [(137, J2), (146, J1)]:           # floor darkens towards us, dithered seams
        for y in range(y0, H):
            for x in range(W):
                k = y - y0
                if k > 1 or (k == 0 and (x + y) % 4 == 0) or (k == 1 and (x + y) % 2):
                    cv.set(x, y, c)
    fungus(cv, 254, 142, 109, 13, J2, T1, J3)
    tubes(cv, 262, 141, (6, 10, 13, 7), J2, T1)
    shell(cv)
    return cv


def near():
    """In front of the Ohmu: the giant framing fungi, spore pods and the foreground ferns."""
    cv = Canvas(W, H)
    fungus(cv, 48, H, 54, 27, J1, T0, J2, 2, shelves=[(-15, 86, 10)])
    fungus(cv, 274, H, 44, 30, J1, T0, J2, 2, shelves=[(16, 80, 10), (-12, 118, 7)])
    pod(cv, 234, 150, 4, J1, T0)
    pod(cv, 243, 154, 2, J1, T0)
    for x in range(W):
        y = int(round(161 + 2 * math.sin(x * .06 + 2) + 1.5 * math.sin(x * .17)))
        cv.rect(x, y, 1, H - y, J0)
    for x, h, lean in [(20, 26, 7), (34, 17, -5), (256, 18, -6), (298, 24, 6), (310, 15, -5)]:
        frond(cv, x, 163, h, lean, J0)
    return cv


# ------------------------------------------------------------------ sprite builders
def png(cv):
    """Canvas (magenta = transparent) -> base64 palette PNG, hand-encoded so the bit depth and the deflate
    strategy, memory level and window can be whichever comes out smallest."""
    cols = [UNPAINTED] + sorted({p for row in cv.px for p in row if p != UNPAINTED})
    idx = {c: i for i, c in enumerate(cols)}
    n, best = len(cols), None
    for bits in {1 if n <= 2 else 2 if n <= 4 else 4 if n <= 16 else 8, 8}:
        raw = bytearray()
        for row in cv.px:
            v = [idx[p] for p in row]
            raw.append(0)
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
        for strat, mem, wbits in ((a, b, c) for a in range(4) for b in range(1, 10) for c in range(9, 16)):
            co = zlib.compressobj(9, zlib.DEFLATED, wbits, mem, strat)
            z = co.compress(bytes(raw)) + co.flush()
            if best is None or len(z) < len(best[1]):
                best = bits, z
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return base64.b64encode(
        b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, best[0], 3, 0, 0, 0))
        + ch(b"PLTE", bytes(v for c in cols for v in c))
        + ch(b"tRNS", b"\0")
        + ch(b"IDAT", best[1]) + ch(b"IEND", b"")).decode()


def crop(cv):
    """(canvas trimmed to its painted bounding box, x, y)."""
    ys = [y for y, row in enumerate(cv.px) if any(p != UNPAINTED for p in row)]
    xs = [x for row in cv.px for x, p in enumerate(row) if p != UNPAINTED]
    x0, x1, y0, y1 = min(xs), max(xs) + 1, ys[0], ys[-1] + 1
    out = Canvas(x1 - x0, y1 - y0)
    out.px = [row[x0:x1] for row in cv.px[y0:y1]]
    return out, x0, y0


def img(cv, x=0, y=0, cls=""):
    """A canvas as a nested <image>, trimmed, placed so canvas (0,0) lands on (x, y)."""
    cv, dx, dy = crop(cv)
    c = f" class='{cls}'" if cls else ""
    return (f"<image{c} x='{x + dx}' y='{y + dy}' width='{cv.w}' height='{cv.h}' "
            f"href='data:image/png;base64,{png(cv)}'/>")


def sheet(frames, attrs):
    """Classic sprite sheet: the frames side by side in one PNG. Returns (frame size, <image>). Frames are
    padded to squares, and the image is n x 1 units, so inside a window() whose viewBox makes one frame
    one unit, 'translateX(-Npx)' with steps(N) plays any sheet whatever its pixel size."""
    n, d = len(frames), max(frames[0].w, frames[0].h)
    cv = Canvas(d * n, d)
    for i, f in enumerate(frames):
        for r, row in enumerate(f.px):
            cv.px[r][i * d:i * d + f.w] = row
    return d, f"<image {attrs} width='{n}' height='1' href='data:image/png;base64,{png(cv)}'/>"


def window(x, y, d, inner):
    """A one-frame viewport onto a sheet (a nested <svg> clips to its box)."""
    return f"<svg x='{x}' y='{y}' width='{d}' height='{d}' viewBox='0 0 1 1'>{inner}</svg>"


def strip(frames, x, y, cls, style=""):
    d, im = sheet(frames, f"class='{cls}'" + (f" style='{style}'" if style else ""))
    return window(x, y, d, im)


def stamp(rows, pal, cv=None, x=0, y=0):
    cv = cv or Canvas(max(len(r) for r in rows), len(rows))
    cv.paint(rows, pal, x, y)
    return cv


def dots(pts, half=".5"):
    """[(x, y, w)] -> path data for a stroked path of 1px-high runs, relative moves. (For a 2px
    stroke pass half="" so the runs sit on whole rows.)"""
    d, cx, cy = "", 0, 0
    for x, y, w in pts:
        d += f"m{x - cx} {y - cy}h{w}" if d else f"M{x} {y}{half}h{w}"
        cx, cy = x + w, y
    return d


def rotor(r, a, n=4):
    """Windmill rotor with n sails at angle a, pixel-snapped: a dark spar with cloth on its trailing side."""
    cv = Canvas(2 * r + 1, 2 * r + 1)
    sw, inner = (max(2, round(r * .28)), .3) if n == 4 else (2, .42)
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            for q in range(n):
                th = a + q * 2 * math.pi / n
                u, v = x * math.cos(th) + y * math.sin(th), -x * math.sin(th) + y * math.cos(th)
                if inner * r <= u <= r + .2 and .5 < v <= .5 + sw:
                    cv.set(x + r, y + r, CLOTH)
                if 0 <= u <= r + .2 and abs(v) <= .5:
                    cv.set(x + r, y + r, BRN)
    cv.rect(r - 1, r - 1, 3, 3, BRN)
    return cv


def turn(r, n, frames):
    """The frames of one sail-to-sail step of an n-sail rotor (after which it looks the same again)."""
    return [rotor(r, i * 2 * math.pi / n / frames, n) for i in range(frames)]


# Nausicaa, 3/4 view facing right, leaning into the wind with both hands on the Mehve's bar. Her head
# is outlined in deep brown (o) so it holds against sky and cloud: auburn hair swept back with a lit
# crown (i) and a dark underside (h); set brows; two eyes, each a dark pixel with a highlight (x) beside
# it; a mouth (m); and a shadow tone (s) under the hair edge and along the jaw. Three frames differ only in
# the streaming hair tips and the tunic tail. Teto is his own sprite: he rides her far shoulder and now
# and then hops up onto the crown of her head, never over her face.
NPAL = {"H": "#b8552c", "h": "#7e3220", "i": "#e08a4c", "o": "#4a2218", "S": "#f8d2a6", "s": "#d99c78", "e": "#3a2a3a",
        "x": "#ffffff", "m": "#b4533f", "B": "#3a6cc8", "b": "#234590", "L": "#6a9cec", "W": "#f0dcaa", "w": "#bfa67a", "K": "#7a4a2c",
        "k": "#4a2c22", "T": "#f2b440", "t": "#a85e22"}
FIG = [
    ".........ooooooo....",
    ".......ooiiiHHHHo...",
    ".....oohHHiiHHHHHo..",
    "...oohhHHHHHHHHHHo..",
    "..oh..ohHHShhShhSo..",
    ".o....ohHHSxeSxeSo..",
    "......ohHhSSSSSSSo..",
    ".......ohhsSSmmSo...",
    "........oossSSSo....",
    "........BBBss.......",
    ".......BBBBBBB......",
    "......BBBLLBBBBB....",
    ".....bBBBBLLBBBBSK..",
    "....bBBBBBBBB.BBKK..",
    "...bbBBBBBBBB.......",
    "..bbbBBBBBBBB.......",
    ".bb.bbBBBBBBBB......",
    ".....bbBBBBBBB......",
    "......WWWw.WWWW.....",
    ".....wWWW...WWWW....",
    ".....WWW.....WWw....",
    "....wWW......WWW....",
    "....KKK......KKK....",
    "...kKKK.....kKKKK...",
]
FLUTTER = [   # per frame: {row: replacement}
    {},
    {3: "..oohhhHHHHHHHHHHo..", 4: ".oh...ohHHShhShhSo..", 5: "o.....ohHHSxeSxeSo..",
     15: ".bbbbBBBBBBBB.......", 16: "bb..bbBBBBBBBB......"},
    {2: "....oohhHHiiHHHHHo..", 3: "....ohhHHHHHHHHHHo..", 4: "...oh.ohHHShhShhSo..", 5: "..o...ohHHSxeSxeSo..",
     14: "..bbbBBBBBBBB.......", 15: ".bb.bBBBBBBBB.......", 16: "....bbBBBBBBBB......"},
]
TETO = ["..T.T.", "..TeTT", ".tTTTT", "tt.TT."]      # sits at figure column 2, row 7
MW, MH, MCX, MCY = 84, 46, 41, 31     # Mehve frame size and the craft's origin within it
MX, MY = 124, 38                      # where the frame sits at the start of her run (see .nc-n)
VIEW = 72, 27, -6                     # Mehve heading (0 = side-on, 90 = towards us), camera elevation, bank
WING = "#ffffff", "#e2edf8", "#c2d6ec", "#6f8ebc", "#3c4868"   # lit, half, shade, underside, engine


def world(X, Y, Z):
    """Mehve coordinates (X forward, Y span, Z up) -> (screen right, depth, up) for the VIEW angles."""
    psi, bank = math.radians(VIEW[0]), math.radians(VIEW[2])
    Y, Z = Y * math.cos(bank) - Z * math.sin(bank), Y * math.sin(bank) + Z * math.cos(bank)
    return X * math.cos(psi) - Y * math.sin(psi), X * math.sin(psi) + Y * math.cos(psi), Z


def P(X, Y, Z=0.0):
    """Mehve coordinates -> pixel in the Mehve frame."""
    x, d, z = world(X, Y, Z)
    phi = math.radians(VIEW[1])
    return MCX + x, MCY + d * math.sin(phi) - z * math.cos(phi)


FX, FY = (int(v) for v in P(-1, 0, 2))      # where she stands; her figure's top-left is (FX - 10, FY - 22)


def mehve(frame=0):
    """The Mehve: a white jet glider, modelled as a 3D planform and projected in 3/4 view. Broad chord,
    blunt tips, a thick slab edge and a dark engine pod keep it reading as a machine rather than a gull."""
    cv = Canvas(MW, MH)
    arch = lambda y: 5 * math.sin(math.pi * y / 42)           # gull: up from the root, level at the tip
    ST = [(0, 15, -10), (6, 14, -9), (16, 11, -9), (26, 7, -10), (33, 3, -11), (36, -3, -10)]
    for s in (-1, 1):                       # far wing first
        quads = [((l0, s * y0, arch(y0)), (l1, s * y1, arch(y1)), (t1, s * y1, arch(y1)), (t0, s * y0, arch(y0)))
                 for (y0, l0, t0), (y1, l1, t1) in zip(ST, ST[1:])]
        for q in quads:                     # slab thickness / underside
            for dz in (1, 2):
                poly(cv, [(x, y + dz) for x, y in (P(*p) for p in q)], WING[3])
        for q in quads:
            a, b, c = (world(*p) for p in q[:3])
            u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
            n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
            if n[2] < 0:
                n = [-k for k in n]
            lum = (-.45 * n[0] + .35 * n[1] + .82 * n[2]) / math.sqrt(sum(k * k for k in n))
            poly(cv, [P(*p) for p in q], WING[0] if lum > .8 else WING[1] if lum > .68 else WING[2])
    poly(cv, [P(17, -3, 0), P(17, 3, 0), P(-12, 4, 0), P(-12, -4, 0)], WING[4])           # engine pod
    poly(cv, [P(14, -3, 2), P(14, 3, 2), P(-12, 4, 2.5), P(-12, -4, 2.5)], WING[1])        # its white cowl
    rows = [FLUTTER[frame].get(i, r) for i, r in enumerate(FIG)]
    cv.rect(FX - 5, FY - 9, 1, 9, WING[4])                    # far handle post, behind her
    cv.paint(rows, NPAL, FX - 10, FY - 22)
    cv.rect(FX + 6, FY - 8, 1, 9, WING[4])                    # near post, under her glove
    return cv


# Lord Yupa on Kai, his horseclaw, on the jungle floor in front of the Ohmu's path. Frame 2: Kai dips
# his head and the cape lifts.
UPAL = {"h": "#6a4a34", "H": "#3c2a24", "s": "#e2a878", "g": "#ece8e0", "c": "#2f4f6f", "C": "#4f7a9a",
        "K": "#ead9b6", "k": "#a98c68", "r": "#a04838", "y": "#d2661e", "e": "#2a2030", "l": "#7a4c2c", "d": "#110f28"}
YUPA = [
    "........hhh.............",
    ".......hhhhh............",
    ".....HHHHHHHHH..........",
    "........sggg.....KKKK...",
    ".......ccgggc...KKKKKK..",
    "......ccccgcc...KKeKKyyy",
    ".....ccccccccc..KKKKKyyy",
    ".....ccCcccccc...KKKk.ye",
    "....cccCcccccc...KKk....",
    "....ccccccrrr....KKk....",
    "...ccccKcrrrr...KKKk....",
    "...cc.KKKcKKKKKKKKKk....",
    "..cc.KKKKcKKKKKKKKk.....",
    ".....KKKKHKKKKKKKKk.....",
    "...kkKKKKKKKKKKKKk......",
    "..kk..kKKKKKKKKkk.......",
    "........ll...ll.........",
    "........ll...ll.........",
    ".........l....l.........",
    ".........l....l.........",
    "........l....l..........",
    "........l....l..........",
    ".......lll..lll.........",
    ".....ddddddddddddd......",
]
YUPA2 = {3: "........sggg............", 4: ".......ccgggc....KKKK...", 5: "......ccccgcc...KKKKKK..",
         6: ".....ccccccccc..KKeKKyyy", 7: ".....ccCcccccc..KKKKKyyy", 8: "....cccCcccccc...KKKk.ye",
         11: "..ccc.KKKcKKKKKKKKKk....", 12: ".cc..KKKKcKKKKKKKKk.....", 15: ".kk...kKKKKKKKKkk......."}
UX, UY = 66, 131
# Kui, Yupa's second horseclaw, half a step behind Kai: the same bird with a pack lashed on instead of a rider.
KUI = ["." * 24] * 3 + [
    ".................KKKK...",
    "................KKKKKK..",
    "................KKeKKyyy",
    "................KKKKKyyy",
    ".......lll.......KKKk.ye",
    ".....llrrrll.....KKk....",
    "....lrrrrrrrl....KKk....",
    "....lrHrrrrHl...KKKk....",
    "....lkHkkkkHkKKKKKKk....",
    ".....KKHKKKKHKKKKKk.....",
    ".....KKKKKKKKKKKKKk.....",
] + YUPA[14:]
KUI2 = {**{i: KUI[i][:15] + YUPA2[i][15:] for i in range(3, 9)}, 15: YUPA2[15]}    # head dip, tail flick
# Both birds rear up while the raging Ohmu passes behind them: head thrown 2px higher on a stretched neck,
# beak agape (columns 15-23 of rows 0-10 replace the idle head).
ALARM = [".........", "..KKKK...", ".KKKKKK.y", ".KKeKKKyy", ".KKKKK...", "..KKKkyyy", "..KKk....",
         "..KKk....", "..KKk....", "..KKk....", ".KKKk...."]
YUPA_A, KUI_A = ([r[:15] + ALARM[i] if i < 11 else r for i, r in enumerate(f)] for f in (YUPA, KUI))


# Tolmekian warships, far off and hazy, heading left: a heavy transport and two corvettes.
TPAL = {"X": "#465a82", "B": "#5b7099", "h": "#8196bb"}
BIG = [
    "....................................hX............",
    "..........h......h......h..........hXX............",
    ".........hX.....hX.....hX.........hBXX............",
    "......hhhhhhhhhhhhhhhhhhhhhhhhhhhhhBBXXhh.........",
    "...hhhBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBhhh.....",
    ".hhBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBhh...",
    "hBBXBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBXX",
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBXXX.",
    ".BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBXX....",
    "..XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.......",
    "....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX..........",
    ".........XX.....XX.....XX.....XX..................",
    "........XXX....XXX....XXX....XXX..................",
    ".......XX.....XX.....XX.....XX....................",
]
SMALL = [
    "..................hX......",
    "....h.....h......hXX......",
    "..hhhhhhhhhhhhhhhhBXh.....",
    "hhBBBBBBBBBBBBBBBBBBBBhhXX",
    "BXBBBBBBBBBBBBBBBBBBBBBXX.",
    ".XXXXXXXXXXXXXXXXXXXXX....",
    ".....XX.....XX............",
    "....XX.....XX.............",
]
# The Valley's gunship, heading right, low over the fields.
GPAL = {"T": "#b8553a", "d": "#5a2c2a", "c": "#c8f0f4", "W": "#dc8a5c", "r": "#f0dcaa"}
GUN = [
    "..d.......................",
    ".dTd......................",
    ".dTT..........ccc.........",
    "dTTTTTTTTTTTTcccTTTTTT....",
    ".dTTTTrrTTTTTTTTTTTTTTTTd.",
    "...dddWWWWWWWWWWWdddddd...",
    ".......dWWWWWWWd..........",
    ".........dWWWd............",
]
# A royal yanma (the jungle's dragonfly-like scout); two wing frames. Drawn heading right, mirrored in build().
YPAL = {"B": "#c6ec6a", "t": "#4a8a4a", "e": "#f2b440", "w": "#eafffa"}
YAN = [[".....ww...ww......", ".....ww..ww.......", ".....ww.ww........", "tBtBBtBBtBBBBBBBe.", "..........BBBBBBee",
        "..................", ".................."],
       ["..................", "..................", "..................", "tBtBBtBBtBBBBBBBe.", "........wwBBBBBBee",
        ".......wwwww......", ".......www.www...."]]


def fleet():
    cv = Canvas(124, 14)
    stamp(SMALL, TPAL, cv, 0, 4)
    stamp(BIG, TPAL, cv, 34, 0)
    stamp(SMALL, TPAL, cv, 98, 5)
    for x in range(42, 76, 3):          # a row of portholes along the transport
        cv.set(x, 6, TPAL["h"])
    return cv


def burst():
    """A spore pod bursting, as sheet frames (frame 0 blank): a split and a flash, then a puff of spores that
    spreads, rises and thins on the wind. The pod sits at (24, 40) of each 48px frame."""
    r = random.Random(7)
    ps = [(math.radians(r.uniform(-175, -5)), r.uniform(.5, 1), r.random()) for _ in range(40)]
    frames = [Canvas(48, 48) for _ in range(8)]
    f = frames[1]
    for a in range(0, 360, 30):                         # the split pod and its flash
        f.set(24 + round(8 * math.cos(math.radians(a))), 39 + round(7 * math.sin(math.radians(a))), T2)
    f.rect(22, 35, 5, 1, "#eafffa")
    f.rect(24, 33, 1, 5, "#eafffa")
    f.rect(23, 34, 3, 3, WHITE)
    for k, (R, up, wind, keep) in enumerate([(6, 3, 0, 1), (11, 6, 1, 1), (16, 10, 3, .85), (19, 15, 5, .65), (21, 20, 8, .45),
                                             (22, 25, 11, .28)]):
        f = frames[k + 2]
        if k < 3:                                       # the dense heart of the puff, dithered, thinning
            for y in range(-4 - 2 * k, 5 + 2 * k):
                for x in range(-4 - 2 * k, 5 + 2 * k):
                    if x * x + y * y <= (4 + 2 * k) ** 2 and (x + y) % 2 == 0 and (k < 2 or (x * 3 + y) % 4 == 0):
                        f.set(24 + x + wind, 40 - up - 3 + y, P1)
        for th, sp, h in ps:
            if h < keep:
                x, y = round(24 + math.cos(th) * R * sp + wind * sp), round(40 + math.sin(th) * R * sp * .8 - up)
                n = 2 if k < 5 and h < .7 else 1
                f.rect(x, y, n, n, "#eafffa" if h < .5 else T2)
    return frames


def glint():
    """The lens catching the light: frame 0 blank, then a 4-point star that grows and shrinks."""
    frames = [Canvas(9, 9) for _ in range(4)]
    for f, n in zip(frames[1:], (2, 4, 2)):
        f.rect(4 - n, 4, 2 * n + 1, 1, "#eafffa")
        f.rect(4, 4 - n, 1, 2 * n + 1, "#eafffa")
        f.rect(3, 3, 3, 3, WHITE) if n > 2 else f.set(4, 4, WHITE)
    return frames


def discs(which):
    """Eyes as pixel-snapped circles (no fill of their own, so each <use> can colour them)."""
    return "".join(f"<circle cx='{x}.5' cy='{y}.5' r='{r + .1}'/>" for x, y, r in which)


_r = random.Random(11)
SNOW = [sorted((_r.randrange(18, 116), _r.randrange(62, 104), 2) for _ in range(20)) for _ in range(2)]   # two layers of falling motes


def spores(seed, n, w=1):
    r = random.Random(seed)
    return dots(sorted((r.randrange(46, 286), r.randrange(112, 156), w) for _ in range(n)), ".5" if w == 1 else "")


# ------------------------------------------------------------------ assemble
def build():
    back, far, fore = mid(), jungle(), near()
    glints = sorted(GLOWS)[::3]
    d8, small = sheet(turn(8, 4, 6), "id='nc-i'")
    d6, small6 = sheet(turn(6, 4, 6), "id='nc-i6'")
    d14, wheel = sheet(turn(14, 8, 4), "id='nc-wh'")
    # the wind dies while the herd rages: at T1 every rotor is swapped for a still of the frame it shows then, and
    # 15s later (a whole number of turns of each) the still is swapped back on that same frame, so neither swap
    # pops. Mill periods divide both 15 and 120.
    T1, mills = 57.3, list(zip(MILLS, ("2.142857", "2.5", "3")))
    still = lambda dur, n: int(T1 % float(dur) / float(dur) * n)
    play = lambda n, dur: f"style='--n:{n};animation-duration:{dur}s'"
    body, _, by = crop(ohmu())

    def seg(x, w, beat, extra=""):
        """One shell segment: a strip of the body image that slides forward on its own beat (--d) of the stride."""
        return (f"<g class='nc-j' style='--d:{beat}'><svg x='{x}' y='{by}' width='{w}' height='{body.h}' "
                f"viewBox='{x} 0 {w} {body.h}'><use href='#nc-om'/></svg>{extra}</g>")

    return [
        f"<defs>{small}{small6}{wheel}"
        f"<image id='nc-om' width='{body.w}' height='{body.h}' href='data:image/png;base64,{png(body)}'/>"
        f"<path id='nc-lg' stroke='#5a7aa6' stroke-width='2' d='M4 {OB - 4}v5m7-5v5'/>"
        f"<path id='nc-lb' stroke='#5a7aa6' d='M.5 {OB - 2}v3m-12-3v3'/>"
        f"<g id='nc-ea'>{discs(EYES[::2])}</g><g id='nc-eb'>{discs(EYES[1::2])}</g></defs>",
        # two cirrus streaks and the warships cross behind the big clouds and the mountains
        "<path class='nc-c' stroke='#fff' opacity='.85' d='M-70 21.5h30m-38 1h52m-40 1h30M-250 39.5h26m-34 1h44m-30 1h20'/>",
        f"<g class='nc-t'>{img(fleet(), 322, 55)}</g>",
        img(back),
        # the Valley girls on the hill wave her off, one after another, each time she sets out (.nc-w)
        "<g stroke='#f2e6c0'>" + "".join(f"<path class='nc-w' style='animation-delay:-{45.75 - .3 * i:g}s' "
                                         f"d='{dots([(x + 2, y - 5, 1)])}'/>" for i, (x, y, _) in enumerate(KIDS)) + "</g>",
        # the great wind wheel, the small mills (one shared sheet), the watchtower's streamer and the wind gusts
        # running across the fields (.nc-wa); then their stills and a limp streamer, shown while the wind is dead
        "<g class='nc-wa'>" + window(CX - 14, CY - 14, d14, "<use class='nc-x' style='--n:4' href='#nc-wh'/>")
        + "".join(window(x - r, hub - r, 2 * r + 1, f"<use class='nc-x' {play(6, dur)} href='#nc-i{'' if r > 6 else 6}'/>")
                  for (x, hub, r), dur in mills)
        + "<g stroke='#d43'><path class='nc-a' d='M145 47.5h7m-6 1h7'/>"
        "<path class='nc-a' style='animation-delay:-.45s' d='M145 47.5h5m-3 1h6m-3 1h4'/></g>"
        "<g stroke='#fffad0'>"
        f"<path class='nc-u' d='{dots([(66, 108, 10), (80, 116, 14), (58, 121, 9), (84, 109, 6)])}'/>"
        f"<path class='nc-u' style='animation-delay:2s' d='{dots([(216, 106, 12), (232, 112, 9), (222, 119, 10), (206, 113, 6)])}'/></g></g>"
        "<g class='nc-ws'>" + window(CX - 14, CY - 14, d14, f"<use href='#nc-wh' x='-{still(3, 4)}'/>")
        + "".join(window(x - r, hub - r, 2 * r + 1, f"<use href='#nc-i{'' if r > 6 else 6}' x='-{still(dur, 6)}'/>")
                  for (x, hub, r), dur in mills)
        + "<path stroke='#d43' d='M145.5 48v6m1-6v3'/></g>",
        # the gunship and its shadow on the fields, then the jungle behind the Ohmu
        f"<g class='nc-g'>{img(stamp(GUN, GPAL), -1145, 96)}<path stroke='#7d5628' opacity='.5' d='M-1139 114.5h16'/></g>",
        img(far),
        strip(glint(), SHELL_X + 1, SHELL_B - 13, "nc-gl"),
        # the Ohmu: ground shadows, the young one trailing at its tail (six legs on a quick 4-tick stride of
        # their own, see .nc-k), nine leg pairs (beat 0 at the head), six plates and the head shield, whose
        # group also carries the eye glow (circles): two blue sets pulsing out of phase, and the red set that
        # fades in over them while the fleet passes
        f"<g class='nc-h'><path fill='#110f28' d='M4 {OB}h{OL - 6}v2h-{OL - 6}zM-30 {OB}h26v1h-26z'/>"
        + "".join(f"<use class='nc-l nc-k' style='--d:{i}' href='#nc-lb' x='{-6 - 4 * i}'/>" for i in range(3))
        + img(baby(), -32, OB - 12)
        # the young one's eyes go red with the herd's, and stay red until it has come out from behind Kai (calm by 84s)
        + f"<g class='nc-r' style='animation-delay:-30s'><path stroke='#f2503c' stroke-width='2' "
          f"d='{dots([(x, y + 1, 2) for x, y in BABY_EYES], '')}'/><path stroke='#ffd8b8' d='{dots([(x, y, 1) for x, y in BABY_EYES])}'/></g>"
        + "".join(f"<use class='nc-l' style='--d:{d}' href='#nc-lg' x='{OL - PW * (d + 1)}'/>" for d in range(9))
        # the golden feelers, behind the shell, rise through it as the eyes calm (.nc-gt)
        + img(tendrils(), cls='nc-gt')
        # (tail first; each strip is 1px wider than its plate and tucked under the one ahead, so no hairline
        # of background can show between neighbours at fractional zoom)
        + "".join(seg(OL - HEAD - PW * (j + 1), PW + 1, j + 3) for j in reversed(range(6)))
        + seg(OL - HEAD, HEAD + 1, 1,
              "<g class='nc-q' fill='#b4ecff' fill-opacity='.8' stroke='#7fd8ff' stroke-opacity='.45'>"
              "<use class='nc-e' href='#nc-ea'/><use class='nc-e nc-e2' href='#nc-eb'/></g>"
              "<g class='nc-r' fill='#f2503c' stroke='#7a1c2a'><use href='#nc-ea'/><use href='#nc-eb'/>"
              f"<path stroke='#ffd8b8' d='{dots([(x - 1 - (r > 3), y - 1 - (r > 3), 1 + (r > 3)) for x, y, r in EYES])}'/></g>")
        + "</g>",
        # Kui and Yupa on Kai at their idle; while the wind is dead (the Ohmu raging past behind them) both birds rear up
        "<g class='nc-wa'>" + strip([stamp(KUI, UPAL), stamp([KUI2.get(i, r) for i, r in enumerate(KUI)], UPAL)], UX - 20, UY - 1,
                                    "nc-x", "--n:2;animation-duration:3.7s")
        + strip([stamp(YUPA, UPAL), stamp([YUPA2.get(i, r) for i, r in enumerate(YUPA)], UPAL)], UX, UY, "nc-x", "--n:2;animation-duration:2.8s")
        + "</g><g class='nc-ws'>" + "".join(
            f"<g class='nc-hp'{d}>{img(stamp(rows, UPAL), x, y)}</g><path class='nc-du' stroke='#9488cc'{d} "
            f"d='{dots([(x, y + 20, 2), (x + 16, y + 20, 2), (x - 2, y + 21, 5), (x + 15, y + 21, 5), (x - 3, y + 22, 6), (x + 15, y + 22, 7)])}'/>"
            for rows, x, y, d in [(KUI_A, UX - 22, UY - 1, " style='animation-delay:-.45s'"), (YUPA_A, UX - 2, UY, "")]) + "</g>",
        # Nausicaa: run (.nc-n) > sway > bob > facing (.nc-v) > flutter sheet and Teto
        f"<g class='nc-n'><g class='nc-m'><g class='nc-b'><g class='nc-v'>"
        f"{strip([mehve(i) for i in range(3)], MX, MY, 'nc-x', '--n:3;animation-duration:.75s')}"
        # a puff from the jet as she sets off, blown back from under the wing's trailing edge (.nc-jp)
        f"<g class='nc-jp'><path stroke='#fff' d='{dots([(MX + 24, MY + 38, 4), (MX + 20, MY + 39, 9), (MX + 12, MY + 39, 3), (MX + 19, MY + 40, 4), (MX + 11, MY + 40, 4), (MX + 3, MY + 39, 4), (MX + 2, MY + 40, 6)])}'/>"
        f"<path stroke='#98bbdc' d='{dots([(MX + 23, MY + 40, 6), (MX + 20, MY + 41, 7), (MX + 12, MY + 41, 2), (MX + 2, MY + 41, 6)])}'/></g>"
        f"{img(stamp(TETO, NPAL), MX + FX - 8, MY + FY - 15, cls='nc-o')}"
        # her blink: lids over both eyes for a moment
        f"<path class='nc-bl' stroke='#d99c78' d='M{MX + FX + 1} {MY + FY - 17}.5h2m1 0h2'/></g></g></g></g>",
        img(fore),
        # a spore pod bursts (44.4s); spores fall like snow around Yupa (204-234s)
        strip(burst(), 210, 110, "nc-pb"),
        "".join(f"<g class='nc-sn'{d}><path stroke='#eafffa' stroke-width='2' d='{dots(m, '')}'/>"
                f"<path stroke='#3aa6a8' d='{dots([(x + 1, y - 1, 1) for x, y, _ in m])}'/></g>"
                for d, m in [("", SNOW[0]), (" style='animation-delay:-234s'", SNOW[1])]),
        # glints on the spore pods and filament tips, then spores drifting up
        f"<path class='nc-p' stroke='#eafffa' d='{dots([(x, y, 1) for x, y in glints])}'/>",
        "<g stroke='#aef4e8'>" + "".join(
            f"<path class='nc-s' style='animation-delay:-{i * 8}s' d='{spores(i + 3, 6)}'/>" for i in range(2))
        + f"<path class='nc-s' stroke-width='2' style='animation-duration:23s' d='{spores(9, 5, 2)}'/></g>",
        # the yanma reuses the gunship's keyframes through a mirrored parent
        f"<g transform='matrix(-1 0 0 1 320 0)'><g class='nc-g'><g class='nc-b' style='animation-duration:1.9s'>"
        f"{strip([stamp(f, YPAL) for f in YAN], -2658, 131, 'nc-x', '--n:2;animation-duration:.3s')}</g></g></g>",
    ]


SPRITES = "".join(build())
CSS = (
    # sprite sheets: --n frames, stepped one frame (= one unit of the window) at a time
    ".nc-x{animation:nc-x 3s steps(var(--n)) infinite}@keyframes nc-x{to{transform:translateX(calc(var(--n)*-1px))}}"
    ".nc-c{animation:nc-c 400s steps(600) -150s infinite}@keyframes nc-c{to{transform:translateX(600px)}}"
    ".nc-t{animation:nc-t 120s steps(1280) -78s infinite}@keyframes nc-t{to{transform:translateX(-1280px)}}"
    ".nc-a{animation:nc-a .9s steps(1) infinite}@keyframes nc-a{50%{opacity:0}}"
    # the girls' wave: a hand up, rocking 1px every 0.6s for 4.8s after she sets out, then down
    ".nc-w{animation:nc-w 60s steps(1) infinite}@keyframes nc-w{1%,3%,5%,7%{transform:translateX(1px)}2%,4%,6%{transform:none}8%,to{opacity:0}}"
    # the wind dies at 57.3s (85.25% after the -45s delay) and returns at 72.3s; see T1 in build()
    ".nc-wa{animation:nc-wa 120s steps(1) -45s infinite}@keyframes nc-wa{85.25%{opacity:0}97.75%{opacity:1}}"
    ".nc-ws{opacity:0;animation:nc-ws 120s steps(1) -45s infinite}@keyframes nc-ws{85.25%{opacity:1}97.75%{opacity:0}}"
    ".nc-u{opacity:0;animation:nc-u 30s infinite}@keyframes nc-u{7%{opacity:1}14%,to{opacity:0;transform:translateX(14px)}}"
    ".nc-g{animation:nc-g 120s steps(4800) -45s infinite}@keyframes nc-g{to{transform:translateX(4800px)}}"
    # the Ohmu: 480px in 60s = 1px per 0.125s. Legs (.nc-l) and shell segments (.nc-j) share the 1.5s stride, each
    # --d ticks late; a segment slides forward as its legs start to swing (75%) and back a half stride later
    ".nc-h{animation:nc-h 60s steps(480) -9.375s infinite}@keyframes nc-h{from{transform:translateX(-127px)}to{transform:translateX(353px)}}"
    ".nc-j{animation:nc-j 1.5s steps(1) calc(var(--d)*.125s - 1.125s) infinite}@keyframes nc-j{50%{transform:translateX(1px)}}"
    ".nc-l{animation:nc-l 1.5s steps(3) calc(var(--d)*.125s - 1.5s) infinite}"
    # the young one's legs: a 4-tick stride (planted 3 ticks, sliding 1px a tick; lifted 1), so each foot steps
    # 4px, the spacing of its legs, instead of striding 12px past its neighbours
    ".nc-k{animation-name:nc-k;animation-duration:.5s}"
    "@keyframes nc-k{from{transform:translateX(1px)}74.9%{transform:translateX(-2px)}75%,to{transform:translateY(-1px)}}"
    "@keyframes nc-l{from{transform:translateX(4px);animation-timing-function:steps(9)}74.9%{transform:translateX(-5px)}"
    "75%{transform:translate(-2px,-1px)}to{transform:translate(4px,-1px)}}"
    # Nausicaa: 56px with the Ohmu in 7s (clear of the mill and the cap), then 53s drifting back the other way, facing left
    ".nc-n{animation:nc-n 60s steps(56) -45.75s infinite}@keyframes nc-n{11.667%{transform:translateX(56px)}}"
    f".nc-v{{transform-origin:{MX + FX}px 0;animation:nc-v 60s steps(1) -45.75s infinite}}@keyframes nc-v{{11.667%{{transform:scaleX(-1)}}}}"
    # the jet puff: 12px back from under the wing in 1.5s as it fades
    ".nc-jp{opacity:0;animation:nc-jp 60s -45.75s infinite}@keyframes nc-jp{from{opacity:1;animation-timing-function:steps(12)}2.5%,to{opacity:0;transform:translateX(-12px)}}"
    ".nc-m{animation:nc-m 9s steps(4) infinite alternate}@keyframes nc-m{to{transform:translateX(4px)}}"
    ".nc-b{animation:nc-b 5.2s steps(4) infinite alternate}@keyframes nc-b{to{transform:translateY(4px)}}"
    # the startled birds, stepped back 2px, hop 3px and land every 1.1s, kicking up dust as they land
    ".nc-hp{animation:nc-hp 1.1s steps(1) infinite}@keyframes nc-hp{from{transform:translateY(-3px)}30%,to{transform:none}}"
    ".nc-du{opacity:0;animation:nc-du 1.1s steps(1) infinite}@keyframes nc-du{30%{opacity:1}60%{opacity:0}}"
    ".nc-bl{opacity:0;animation:nc-bl 6.3s steps(1) infinite}@keyframes nc-bl{97%{opacity:1}}"
    ".nc-o{animation:nc-o 13s steps(1) infinite}@keyframes nc-o{82%{transform:translate(6px,-9px)}}"
    ".nc-e,.nc-p{animation:nc-e 3.6s infinite alternate}.nc-e2{animation-delay:-3.6s}.nc-p{animation-duration:5s}"
    "@keyframes nc-e{from{opacity:.1}}"
    ".nc-q{animation:nc-q 120s -45s infinite}@keyframes nc-q{83.3%,98.7%{opacity:1}86.7%,95.8%{opacity:0}}"
    ".nc-r{opacity:0;animation:nc-r 120s -45s infinite}@keyframes nc-r{83.3%,98.7%{opacity:0}86.7%,95.8%{opacity:1}}"
    # the feelers rise 24px over 4s from 71s, hold, and fade by 84s (-49s puts 71s at 0%)
    ".nc-gt{opacity:0;animation:nc-gt 120s -49s infinite}"
    "@keyframes nc-gt{from{animation-timing-function:steps(24)}3.33%,8.33%{opacity:1;transform:translateY(-24px)}10.83%,to{opacity:0;transform:translateY(-24px)}}"
    # new moments run on a 240s loop, so its two 120s halves differ. A spore pod bursts at 44.4s, when no Ohmu is near
    # it (one sheet frame per .6s)
    ".nc-pb{animation:nc-pb 240s steps(1) infinite}@keyframes nc-pb{18.5%{transform:translateX(-1px)}18.75%{transform:translateX(-2px)}"
    "19%{transform:translateX(-3px)}19.25%{transform:translateX(-4px)}19.5%{transform:translateX(-5px)}19.75%{transform:translateX(-6px)}"
    "20%{transform:translateX(-7px)}20.25%{transform:none}}"
    # the shed shell's lens glints at 94.8s and 154.8s, when no Ohmu is in front of it
    ".nc-gl{animation:nc-gl 240s steps(1) infinite}@keyframes nc-gl{39.5%,39.875%,64.5%,64.875%{transform:translateX(-1px)}"
    "39.625%,64.625%{transform:translateX(-2px)}39.75%,64.75%{transform:translateX(-3px)}40%,65%{transform:none}}"
    # spores fall like snow around Yupa, 2px a second: one layer 204-228s, the other 6s behind it
    ".nc-sn{opacity:0;animation:nc-sn 240s infinite}@keyframes nc-sn{85%{opacity:0;transform:none;animation-timing-function:steps(6)}"
    "86.25%{opacity:1;transform:translateY(6px);animation-timing-function:steps(34)}"
    "93.333%{opacity:1;transform:translateY(40px);animation-timing-function:steps(8)}95%,to{opacity:0;transform:translateY(48px)}}"
    ".nc-s{opacity:0;animation:nc-s 16s linear infinite}@keyframes nc-s{20%,70%{opacity:.9}to{transform:translate(8px,-42px)}}"
)
