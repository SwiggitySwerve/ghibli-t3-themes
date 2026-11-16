"""Spirited Away: the sea railway at dusk (full-budget version, 320x180).

No-Face and Chihiro wait on the little platform with Boh, the Yu-bird and three soot sprites while Lin
waves from her tub; the bathhouse glows on its rock across the water with its bridge, chimney, lanterns
and the boiler-room fire under it; on its terrace the three Kashira hop and Chihiro's parents, as pigs,
gorge at a food stall. The train glides past behind the travellers, the River Spirit rises out of the
sea, spirits cross the bridge, Haku flies across in front of the bathhouse, Yubaba follows in her bird
form and the spirit ferry comes in along the horizon to dock behind the island.

Layers, back to front:
  PNG (draw)   sky, clouds, far islands, bathhouse + bridge + rock, reflections, sea, rail, poles
  SPRITES      water glints first (so every moving thing is drawn over the water surface), stars, cloud
               wisps, smoke, steam, furnace fire, frog, bridge procession + railing, ferry, the island's right
               end again (nested PNG, so the ferry docks BEHIND it), window flicker, Kashira, the pigs' stall,
               the River Spirit (in a nested svg viewport), Lin's tub, Yubaba,
               Haku (in front of the bathhouse), train (nested PNG), foreground (nested PNG: platform +
               travellers, so the train passes BEHIND them), idle overlays (mask, ponytail, blink,
               glance, Boh, soot sprites, lamp)
Moments on a 120 s cycle: train 5-29 s, River Spirit 29-38 s, bridge procession 36-80 s, Haku 75-105 s,
Yubaba 106-119 s.
The ferry is on 240 s: in 110-168 s, docked out of sight, out again 182-239 s. Every moving sprite steps
in whole pixels and holds still while off-canvas.
"""
import base64, math, random, struct, zlib
from lib import Canvas, UNPAINTED

NAME = "Spirited Away"
SIZE = (320, 180)
COLORS = 32
W, H = SIZE
THEME = {"canvas": "#15132e", "accent": "#ff8a5c", "overlay": "#17143a",
         # wide panes crop vertically: take most of it from the empty sea at the bottom, not the bathhouse roof
         "position": "center 30%",
         "colors": {"sidebar": "#131129", "sidebarRowSelected": "#2c2658", "sidebarBorder": "#2a2552",
                    "surface": "#1c1940", "border": "#373066", "text": "#f6efe6", "textMuted": "#aa9fc6"}}

# sky, zenith -> horizon
S = ["#1f1d4a", "#2a2859", "#3a316b", "#4f3c7e", "#6c4a8c", "#8f5591", "#b0608f", "#cf6f86", "#e8897c",
     "#f6a878", "#fcc784", "#ffe2a0"]
DARK, RED, RED_D, LANT = "#1b1830", "#bb3333", "#7a2237", "#ff7847"
ROOF, ROOF_HI, ROOF_D = "#2c6e6a", "#58a892", "#1d4650"
STONE, STONE_HI, STONE_D, PUFF, PUFF_HI = "#5d5082", "#8474a6", "#463a68", "#f2a596", "#f9c3a6"
D1, D2 = "#2b2f66", "#222558"
HZ, RAIL, G = 106, 136, 90      # horizon row, rail row, bathhouse ground-floor / bridge deck row
BX = 132                        # bathhouse centre
CHM = BX - 34                   # chimney left edge
KX = CHM - 4                    # boiler-room furnace grate, inner left edge
BR0, BR1 = BX - 77, BX - 43     # bridge span
PX, PT = 174, 134               # platform left edge and top row
# storeys, bottom to top: half-width, wall top, wall bottom (exclusive), window rows as (dy, height)
TIERS = [(42, 77, 90, [(2, 4), (7, 4)]), (34, 63, 73, [(2, 3), (6, 3)]), (27, 50, 59, [(2, 2), (5, 2)]),
         (19, 39, 46, [(2, 3)]), (12, 30, 35, [(2, 2)])]


def windows():
    """[(x, y, h, colour)] for every bathhouse window; shared by draw() and the flicker sprites."""
    r, out = random.Random(11), []
    for i, (hw, y0, y1, rows) in enumerate(TIERS):
        for dy, h in rows:
            for x in range(BX - hw + 2, BX + hw - 3, 4):
                if i > 1 or abs(x + 1 - BX) > 17 or (i == 1 and dy == 2):
                    out.append((x, y0 + dy, h, r.choice([S[11]] * 5 + [S[10]] * 3 + [RED_D] * 2)))
    return out


def bands(cv, y, rows, soft=True):
    """rows: [(y_end, colour)]. Flat bands with an ordered-dither seam: 3 rows (25/50/75%) when
    soft, else one checker row. Regular patterns like these cost very little in the PNG."""
    prev = None
    for y1, c in rows:
        for yy in range(y, y1):
            k = yy - y + (0 if soft else 1)
            for x in range(cv.w):
                mix = prev and ((k == 0 and (x % 4 != (yy % 2) * 2)) or (k == 1 and (x + yy) % 2)
                                or (k == 2 and soft and x % 4 == (yy % 2) * 2))
                cv.set(x, yy, prev if mix else c)
        prev, y = c, y1


def cloud(cv, circles, base):
    """Cumulus as a union of circles painted back to front. Cream rim where the silhouette faces the
    light (up and left), a soft highlight crescent and a shadow crescent on each lobe, and a dithered
    shadow towards the flat base."""
    own = {}
    for i, (cx, cy, r) in enumerate(circles):
        for y in range(int(cy - r), min(base, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                if math.hypot(x + .5 - cx, y + .5 - cy) <= r:
                    own[x, y] = i
    for (x, y), i in own.items():
        cx, cy, r = circles[i]
        dx, dy = x + .5 - cx, y + .5 - cy
        k, d, e = (-.6 * dx - .8 * dy) / r, base - y, math.hypot(dx, dy)
        if (x, y - 1) not in own or (x, y - 2) not in own or ((x - 1, y) not in own and dy < r * .3):
            c = S[11]
        elif d <= 2:
            c = S[6]
        elif d <= 6 or (d <= 8 and (x + y) % 2) or (d <= 10 and x % 4 == (y % 2) * 2):
            c = S[7]
        elif k > .45 and e > r - 3.2:
            c = PUFF_HI
        elif k < -.62 and d > 12:
            c = S[8]
        else:
            c = PUFF
        cv.set(x, y, c)


def roof(cv, x0, x1, y):
    """A four-row tiled eave from x0 to x1 (exclusive), concave, with upturned tips."""
    cv.rect(x0 + 4, y, x1 - x0 - 8, 1, ROOF_HI)
    cv.rect(x0 + 2, y + 1, x1 - x0 - 4, 1, ROOF)
    cv.rect(x0, y + 2, x1 - x0, 1, ROOF)
    cv.rect(x0 + 2, y + 3, x1 - x0 - 4, 1, ROOF_D)
    for sx, x in ((-1, x0), (1, x1 - 1)):
        cv.set(x + sx, y + 1, ROOF)
        cv.set(x + 2 * sx, y, ROOF)
        cv.set(x - 2 * sx, y + 1, ROOF_HI)
        cv.set(x - 3 * sx, y + 1, ROOF_HI)


def bathhouse(cv):
    # battered stone base
    for j in range(10):
        hw = 44 + j // 3
        cv.rect(BX - hw, G + j, 2 * hw, 1, STONE_HI if j == 0 else STONE_D if j % 3 == 0 else STONE)
    for j in range(1, 10):
        if j % 3:
            for x in range(BX - 43 + (j // 3) * 4, BX + 43, 8):
                cv.set(x, G + j, STONE_D)
    cv.rect(KX - 1, 92, 11, 6, DARK)             # Kamaji's boiler room: a furnace grate under the chimney
    cv.rect(KX, 93, 9, 4, LANT)
    for x in range(KX + 1, KX + 9, 2):
        cv.rect(x, 93, 1, 4, DARK)
    for i, (hw, y0, y1, _) in enumerate(TIERS):
        cv.rect(BX - hw, y0, 2 * hw, y1 - y0, RED)
        cv.rect(BX - hw, y0, 2 * hw, 1, RED_D)
        cv.rect(BX - hw - 1, y1 - 1, 2 * hw + 2, 1, RED_D)
        if i:
            roof(cv, BX - hw - 5, BX + hw + 5, y1)
    for x, y, h, c in windows():
        cv.rect(x, y, 2, h, c)
    for x in range(BX - 40, BX + 41, 5):         # lantern row under the first eave
        cv.set(x, 78, LANT)
    # front bay: entrance under a blue noren, and a big curved gable with a gold crest
    cv.rect(BX - 12, 76, 24, 14, RED)
    cv.rect(BX - 12, 76, 1, 14, RED_D)
    cv.rect(BX + 11, 76, 1, 14, RED_D)
    cv.rect(BX - 7, 80, 14, 10, S[11])
    cv.rect(BX - 7, 80, 14, 3, "#3d5fa8")
    for x in (BX - 5, BX - 1, BX + 3):
        cv.rect(x, 81, 2, 1, S[11])
    cv.rect(BX - 1, 84, 2, 6, S[10])
    for x in (BX - 10, BX + 8):
        cv.rect(x, 80, 2, 4, LANT)
        cv.rect(x, 81, 2, 2, S[11])
    prof = [0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 6, 6, 7, 7, 7, 7, 8]
    for dx in range(-17, 17):
        t = 67 + prof[dx if dx >= 0 else -dx - 1]
        cv.set(BX + dx, t, ROOF_HI)
        cv.set(BX + dx, t + 1, ROOF)
        cv.set(BX + dx, t + 2, ROOF_D if abs(dx + .5) > 12 else ROOF)
        if abs(dx + .5) < 12:
            cv.rect(BX + dx, t + 3, 1, 76 - t - 3, RED)
    cv.rect(BX - 2, 71, 4, 4, S[10])
    cv.rect(BX - 1, 72, 2, 2, LANT)
    # top roof: concave hipped roof with a gold finial
    for i, hw in enumerate([2, 3, 4, 6, 8, 10, 12, 14, 15, 16, 18]):
        y = 19 + i
        cv.rect(BX - hw, y, 2 * hw, 1, ROOF)
        cv.rect(BX - hw, y, 2 if i < 8 else 3, 1, ROOF_HI)
        cv.rect(BX + hw - 2, y, 2, 1, ROOF_D)
        if i == 10:
            cv.rect(BX - hw + 2, y, 2 * hw - 4, 1, ROOF_D)
            cv.set(BX - hw - 1, y - 1, ROOF)
            cv.set(BX + hw, y - 1, ROOF)
    cv.rect(BX - 1, 15, 2, 4, S[10])
    cv.set(BX - 1, 14, S[11])


def chimney(cv):
    cv.rect(CHM, 14, 5, 50, "#3b2a4d")
    cv.rect(CHM, 14, 1, 50, STONE)
    for y in (24, 36, 48):
        cv.rect(CHM, y, 5, 1, DARK)
    cv.rect(CHM - 1, 13, 7, 2, DARK)


POLES = (34, 104, 276)           # telegraph poles standing in the water along the far side of the track
MX = 63.5                        # moon centre column


def draw():
    cv = Canvas(W, H)
    bands(cv, 0, [(10, S[0]), (22, S[1]), (34, S[2]), (46, S[3]), (57, S[4]), (67, S[5]), (76, S[6]), (84, S[7]),
                  (91, S[8]), (97, S[9]), (102, S[10]), (HZ, S[11])])
    bands(cv, HZ, [(108, S[10]), (111, S[9]), (115, S[8]), (120, S[7]), (126, S[6]), (133, S[5]), (RAIL, S[4])], soft=False)
    bands(cv, RAIL, [(143, S[4]), (152, S[3]), (163, D1), (H, D2)])
    # stars, high streak clouds
    for x, y in [(14, 5), (41, 14), (109, 17), (181, 26), (238, 13), (262, 24), (310, 18), (58, 27), (168, 12)]:
        cv.set(x, y, S[11] if y < 20 else S[8])
    # a pale, dim moon rising in the east, lit on the side facing the sunset
    for y in range(13, 22):
        for x in range(59, 68):
            if math.hypot(x + .5 - MX, y + .5 - 17.5) <= 3.6:
                cv.set(x, y, "#7f6fa3" if math.hypot(x + .5 - MX + 2.4, y + .5 - 17) <= 3.2 else "#b3a3c6")
    for x, y, n, c in [(170, 44, 56, S[5]), (186, 45, 26, S[5]), (10, 52, 46, S[6]), (20, 53, 20, S[6]),
                       (190, 66, 44, S[7]), (204, 67, 18, S[7]), (236, 30, 40, S[4]), (4, 30, 26, S[4])]:
        cv.rect(x, y, n, 1, c)
    # low cloud bank along the horizon, the big cumulus, far islets with the lonely house
    for x, y, n in [(0, 99, 34), (6, 98, 18), (186, 100, 50), (196, 99, 24), (246, 101, 40)]:
        cv.rect(x, y, n, 1, S[8])
    cloud(cv, [(274, 72, 12), (256, 90, 10), (280, 53, 13), (263, 72, 15), (298, 68, 20), (278, 86, 17), (316, 88, 14),
               (246, 93, 9), (236, 98, 6), (300, 92, 12)], HZ - 4)
    cloud(cv, [(-6, 84, 14), (10, 91, 10), (24, 97, 6)], HZ - 4)
    for x, n, h in [(252, 26, 1), (256, 14, 2), (300, 20, 1)]:
        cv.rect(x, HZ - h, n, h, S[6])
    cv.rect(260, HZ - 5, 5, 3, S[6])
    cv.rect(259, HZ - 6, 7, 1, S[5])
    cv.rect(266, HZ - 8, 3, 6, S[5])
    cv.rect(265, HZ - 7, 5, 3, S[5])
    # bathhouse rock (lumpy, flat waterline) and the bridge's far bank
    x = BX - 58
    for n, h in [(2, 1), (2, 2), (3, 4), (3, 5), (96, 6), (4, 7), (3, 5), (4, 4), (2, 5), (3, 3), (3, 2), (3, 1)]:
        cv.rect(x, HZ - h, n, h, DARK)
        x += n
    x = BR0 - 29
    for n, h in [(2, 1), (2, 3), (3, 6), (3, 9), (3, 12), (3, 14), (18, 16), (2, 10), (2, 5), (2, 2)]:
        cv.rect(x, HZ - h, n, h, DARK)
        x += n
    # Kamaji's chimney, rising behind the left wing, with a smoke trail
    chimney(cv)
    for x, y, n in [(4, 10, 5), (7, 8, 7), (11, 6, 9), (17, 4, 11), (25, 3, 10), (22, 2, 5)]:
        cv.rect(CHM + x, y, n, 2, S[1])
    bathhouse(cv)
    # pines at the foot of the walls
    for cx, cy, r in [(BX - 48, 97, 4), (BX - 52, 100, 3), (BX + 48, 98, 4), (BX + 53, 101, 3),
                      (BR0 - 19, 88, 4), (BR0 - 23, 92, 3)]:
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if math.hypot(x + .5 - cx, y + .5 - cy) <= r:
                    cv.set(x, y, ROOF if (x - cx) + (y - cy) < -1 else ROOF_D)
    # gatehouse on the far bank, then the bridge: deck and trestle piers (the railing is a sprite)
    cv.rect(BR0 - 12, 76, 12, 14, RED)
    cv.rect(BR0 - 12, 76, 12, 1, RED_D)
    cv.rect(BR0 - 9, 80, 6, 10, S[10])
    cv.rect(BR0 - 9, 80, 6, 2, "#3d5fa8")       # a blue noren and a lit door slit, like the main entrance
    cv.rect(BR0 - 7, 80, 2, 1, S[11])
    cv.rect(BR0 - 7, 83, 2, 7, S[11])
    roof(cv, BR0 - 16, BR0 + 4, 72)
    cv.rect(BR0, G, BR1 - BR0, 1, RED)
    cv.rect(BR0, G + 1, BR1 - BR0, 1, RED_D)
    for x in (7, 17, 27):
        cv.rect(BR0 + x, G + 2, 2, HZ - G - 2, RED_D)
    cv.rect(BR0 + 3, G + 8, 30, 1, RED_D)
    # reflections: a soft shadow under the rock, then the lit storeys as shrinking streaks
    for y, x0, x1, c in [(106, -60, 66, S[4]), (107, -56, 62, S[4]), (108, -50, 54, S[4]), (106, -104, -68, S[4]),
                         (107, -100, -72, S[4]), (109, -94, -78, RED_D),
                         (110, -42, 42, RED_D), (112, -40, 40, RED_D), (114, -34, 34, RED_D), (117, -27, 27, RED_D),
                         (120, -19, 19, S[4]), (123, -12, 12, S[4]), (126, -6, 6, S[4]), (129, -2, 2, S[4]),
                         (110, -34, -29, S[4]), (113, -34, -29, S[4]), (116, -34, -29, S[4]), (119, -34, -29, S[4])]:
        cv.rect(BX + x0, y, x1 - x0, 1, c)
    for y, hw in [(111, 38), (113, 32), (115, 26), (118, 18)]:
        for x in range(BX - hw + (y % 2) * 5, BX + hw, 10):
            cv.rect(x, y, 3, 1, S[11])
    # overhead-wire poles along the far side of the track (their tops, arms and the wire are a sprite, drawn
    # over the ferry)
    for x in POLES:
        cv.rect(x, 113, 1, 23, DARK)
    # the track: two rails just under the surface, sleepers between them
    cv.rect(0, RAIL, W, 1, DARK)
    for x in range(1, W, 7):
        cv.rect(x, RAIL + 1, 3, 1, S[3])
    cv.rect(0, RAIL + 2, W, 1, S[3])
    for x in POLES:
        for y, dx in [(139, 0), (141, 1), (144, 0), (147, -1)]:
            cv.rect(x + dx, y, 2, 1, S[2])
    # water: sun glitter near the horizon, ripples in the neighbouring band colour, long swells below the rail
    r = random.Random(5)
    for y in range(108, 134, 2):
        for _ in range(3):
            x, n = r.randrange(196, W), r.randrange(4, 12)
            if y < 118 or not PX + 30 < x + n and x < PX + 66 or x > LX + 4:   # keep clear of the soot sprites
                cv.rect(x, y, n, 1, S[11] if y < 116 else S[9] if y < 124 else S[7])
    for y in range(110, 134, 3):
        for _ in range(2):
            x, n = r.randrange(-5, W), r.randrange(6, 14)
            if not 20 < x < 200 or y > 130:
                cv.rect(x, y, n, 1, S[11] if y < 112 else S[8] if y < 121 else S[6] if y < 127 else S[4])
    for y, c in [(140, S[6]), (142, S[7]), (144, S[6]), (147, S[6]), (150, S[5]), (154, S[5]), (158, S[4]), (164, S[3])]:
        for _ in range(3):
            x, n = r.randrange(200, W), r.randrange(6, 16)
            cv.rect(x, y, n, 1, c)
    for y, c in [(142, S[5]), (146, S[4]), (151, S[4]), (156, S[3]), (163, D1), (170, D1)]:
        for x in range((y * 37) % 50 - 20, W, 50 + y % 7 * 6):
            cv.rect(x, y, 14 + y % 5 * 4, 1, c)
            cv.rect(x + 6, y + 1, 10 + y % 3 * 4, 1, c)
    return cv


IX, IY, IW, IH = 144, HZ - 13, 72, 16     # the island's right end, redrawn over the ferry


def island_end():
    """Everything in that box that is land or the island's shadow on the water, cut out of draw() by keying
    out the sky and open-water colours there. Drawn over the ferry, so it slides in behind the rock and the
    stone base (and its reflection behind their shadow) and is hidden completely while docked at x=144."""
    full, cv = draw(), Canvas(IW, IH)
    key = {tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in S[8:]}
    cv.px = [[UNPAINTED if q in key else q for q in row[IX:IX + IW]] for row in full.px[IY:IY + IH]]
    return cv


def png(cv):
    """Canvas -> base64 8-bit palette PNG with the unpainted key colour transparent (index 0)."""
    cols = [UNPAINTED] + sorted({p for row in cv.px for p in row if p != UNPAINTED})
    raw = b"".join(b"\0" + bytes(cols.index(p) for p in row) for row in cv.px)
    idat = min((c.compress(raw) + c.flush() for c in
                (zlib.compressobj(9, 8, wb, 9, st) for wb in (15, 12, 10, 9) for st in (0, 1))), key=len)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return base64.b64encode(
        b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 3, 0, 0, 0))
        + ch(b"PLTE", bytes(x for c in cols for x in c)) + ch(b"tRNS", b"\0") + ch(b"IDAT", idat) + ch(b"IEND", b"")).decode()


def img(cv, x, y, attrs=""):
    return f"<image{attrs} x='{x}' y='{y}' width='{cv.w}' height='{cv.h}' href='data:image/png;base64,{png(cv)}'/>"


def art(rows, pal):
    assert len({len(r) for r in rows}) == 1, [len(r) for r in rows]
    cv = Canvas(len(rows[0]), len(rows))
    cv.paint(rows, pal, 0, 0)
    return cv


def runs(rows, pal, x0, y0):
    """ASCII art -> one stroked <path> per colour made of 1px runs at y+.5 with relative moves."""
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
                    ax, ay = x0 + x, y0 + dy
                    d += f"M{ax} {ay}.5h{n}" if not d else f"m{ax - px} {ay - py}h{n}"
                    px, py = ax + n, ay
                x += n
        if d:
            out += f"<path stroke='{col}' d='{d.replace(' -', '-')}'/>"
    return out


# ---- foreground layer: platform, No-Face (body only; the mask is a sprite), Chihiro ----
FX, FY, FW, FH = PX - 4, 94, 80, 60
NOFACE = ["......kkkkkkkk......",
          ".....kkkkkkkkkk.....",
          "....vkkkkkkkkkkk....",
          "....vkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkk...",
          "...vkkkkkkkkkkkkkk..",
          "..vkkkkkkkkkkkkkkk..",
          "..vkkkkkkkkkkkkkkk..",
          "..vkkkkkkkkkkkkkkk..",
          "..vkkkkkkkkkkkkkkk..",
          "..vkkkkkkkkkkkkkkk..",
          "..vkkkkkkkkkkkkkkk..",
          "..vkkkkkkkkkkkkkkk..",
          "..vkkkkkkkkkkkkkkk..",
          ".vkkkkkkkkkkkkkkkk..",
          ".vkkkkkkkkkkkkkkkkk.",
          ".vkkkkkkkkkkkkkkkkk.",
          ".vkkkkkkkkkkkkkkkkk.",
          ".vkkkkkkkkkkkkkkkkk.",
          ".vkkkkkkkkkkkkkkkkk.",
          ".vkkkkkkkkkkkkkkkkk.",
          ".vkkkkkkkkkkkkkkkkk.",
          "vkkkkkkkkkkkkkkkkkk.",
          "vkkkkkkkkkkkkkkkkkkk",
          "vkkkkkkkkkkkkkkkkkkk",
          "vkkkkkkkkkkkkkkkkkkk",
          ".vkkkkkkkkkkkkkkkkk."]
MASK = ["..wwwwww..",
        ".wwwwwwww.",
        "wwpwwwwpws",
        "wwpwwwwpws",
        "wppwwwwpps",
        "wkkkwwkkks",
        "wwwwwwwwws",
        "wppwwwwpps",
        "wppwwwwpps",
        "wwpwwwwpws",
        "wwpwwwwpws",
        "wwwwwwwwws",
        "wwwwkkwwws",
        "wwwwwwwwws",
        ".wwggggws.",
        "..wwwwss.."]
MASK_PAL = {"s": "#c9bfd6", "p": "#96c", "g": "#a9a", "k": "#213"}   # the white base is one filled outline
CHIHIRO = ["..hhhhh..",
           ".hhhhhhh.",
           ".hhhhhhhu",
           ".hhsshsh.",
           ".hsssssh.",
           ".hskssks.",
           "..sssss..",
           "...sss...",
           "..wwwww..",
           ".wwgggww.",
           ".wwwwwww.",
           "swwwwwwws",
           "s.wwwww.s",
           "..ppppp..",
           "..ppppp..",
           "..pp.pp..",
           "..s...s..",
           "..s...s..",
           "..s...s..",
           "..s...s..",
           ".yy..yy.."]
CHI_PAL = {"h": "#5a3324", "s": "#ffcc99", "k": "#3a2218", "w": "#f6f0e8", "g": "#3f9a6a", "p": "#e8777c",
           "y": "#f2c84b", "u": "#9966cc"}
NX, CHX, LX = PX + 22, PX + 6, PX + 65      # No-Face and Chihiro left edges, lamp post
NY, CHY = PT - len(NOFACE), PT - len(CHIHIRO)


def foreground():
    cv = Canvas(FW, FH)
    o = lambda x, y: (x - FX, y - FY)
    # platform slab on posts, with broken reflections of the posts and the travellers
    cv.rect(*o(PX, PT), 70, 1, "#c9bfd6")
    cv.rect(*o(PX, PT + 1), 70, 2, "#7d7198")
    cv.rect(*o(PX, PT + 3), 70, 1, DARK)
    for x in (PX + 4, PX + 34, PX + 64):
        cv.rect(*o(x, PT + 4), 2, 7, DARK)
        cv.rect(*o(x, PT + 12), 2, 1, DARK)
        cv.rect(*o(x + 1, PT + 14), 2, 1, DARK)
    cv.rect(*o(CHX + 2, PT + 6), 5, 1, S[7])
    cv.rect(*o(CHX + 3, PT + 8), 4, 1, "#c9bfd6")
    for y, n in [(6, 5), (8, 3), (11, 4), (14, 2)]:
        cv.rect(*o(LX - 2 + y % 2, PT + y), n, 1, S[11])
    cv.paint(CHIHIRO, CHI_PAL, *o(CHX, CHY))
    return cv


def noface():
    """No-Face's body (the mask is a sprite) as its own nested PNG, so he can fade."""
    cv = art(NOFACE, {"k": "#14111f", "v": "#322a4e"})
    for dy in range(5, 31):                       # warm rim light from the lamp
        cv.set(NOFACE[dy].rindex("k"), dy, "#553044")
    return cv


# ---- train (nested PNG): two cars, lit windows with shadow passengers ----
TW, TH, CAR = 156, 32, 76
PANTO = ["kkkkkkk",       # a diamond pantograph on each car roof, its bar pressed up against the wire
         "..k.k..",
         ".k...k.",
         "..k.k.."]
PAX = [["..kkk..",      # upright, facing out
        "..kkk..",
        "...k...",
        ".ekkke.",
        ".kkkkk.",
        "kkkkkkk"],
       [".......",      # head bowed
        ".kkk...",
        ".kkke..",
        "..kk...",
        ".kkkke.",
        "ekkkkkk"],
       [".......",      # small, sitting low, turned away
        "...kk..",
        "...kk..",
        "...k...",
        "..ekkk.",
        ".ekkkkk"]]


def train():
    cv = Canvas(TW, TH)
    cream, lo, roofc = "#f0dcae", "#a03c36", "#4b4668"
    for x0 in (0, CAR + 4):
        cv.rect(x0 + 3, 2, CAR - 6, 1, "#6d6890")
        cv.rect(x0 + 1, 3, CAR - 2, 2, roofc)
        for vx in (12, 34, 56):
            cv.rect(x0 + vx, 0, 6, 2, roofc)
        cv.rect(x0, 5, CAR, 14, cream)
        cv.rect(x0, 19, CAR, 1, RED_D)
        cv.rect(x0, 20, CAR, 8, lo)
        cv.rect(x0, 27, CAR, 1, RED_D)
        cv.rect(x0 + 2, 28, CAR - 4, 4, DARK)
        for i, x in enumerate(range(x0 + 4, x0 + CAR - 8, 9)):
            if i in (0, 7):                       # doors
                cv.rect(x, 7, 6, 20, "#c9ad86")
                cv.rect(x + 1, 9, 4, 7, "#ffc95e")
                continue
            cv.rect(x, 8, 7, 8, "#ffc95e")
            cv.rect(x, 8, 7, 1, S[11])
            if (i * 5 + x0) % 3 == 0:             # a shadow passenger: dark, see-through at the edges, still
                cv.paint(PAX[(i + x0) % 3], {"k": "#2a2034", "e": "#8a5a52"}, x, 10)
    cv.rect(CAR, 4, 4, 24, DARK)                  # the bellows between the cars
    for y in range(6, 27, 3):
        cv.rect(CAR, y, 4, 1, "#3b2a4d")
    cv.rect(TW - 3, 5, 3, 23, "#c9ad86")          # cab front, windscreen, headlight
    cv.rect(TW - 3, 8, 2, 8, "#ffc95e")
    cv.rect(TW - 2, 22, 2, 3, S[11])
    cv.rect(TW - 1, 5, 1, 2, UNPAINTED)
    return cv


# ---- Haku: detailed head (nested PNG) + body slices that ripple ----
HAKU = [".................b........",     # 26x19 (was 28x21). At the back edge the mane is rows 3-6, the neck
        "................bb...b....",     # is white on rows 7-12 and shaded on row 13: exactly the first body slice
        "..............bbt...bbt...",
        "...........wwwbbttttbttttt",
        ".........wwwwwwwtttttTtttt",
        "...ww..wwwwwkkkwwwtttttTtt",
        "..wwwwwwwwwwwgkwwwwwwtttTt",
        ".wwwwwwwwwwwwwwwwwwwwwwwww",
        "pwwwwwwwwwwwwwwwwwwwwwwwww",
        "kssssssssssswwwwwwwwwwwwww",     # underside of the upper jaw
        ".w..w..w..w.kwwwwwwwwwwwww",     # upper fangs hanging into the open mouth (the sky shows through between them)
        ".....nnn..kwwwwwwwwwwwwwww",     # mouth and tongue; lower jaw drops from the hinge at the back
        "...nnn..kwwwwwwwswwwwwwwww",
        "...wrwrwwwwwwwwswwwwssssss",     # lower fangs point up along the jaw's front edge
        "....wwwwwwwwwwwwssss......",     # the jaw line steps up towards the back to meet the neck's shaded underside
        ".....sssssssssss..........",     # shaded underside of the lower jaw
        "..........................",     # (the whisker that trails back under the chin is two sprite frames)
        "..........................",
        ".........................."]
HAKU_PAL = {"w": "#ffffff", "s": "#c4d6e4", "t": "#3bb5a0", "T": "#1f7a75", "b": "#d9b77a", "k": "#221133",
            "g": "#2e8b57", "p": "#ee8888", "r": "#5a1630", "n": "#e0607a"}
PAPER = [["..w..",                # a hitogata paper doll, arms out / arms up
          "wwwww",
          "..s..",
          ".s.s."],
         ["w.w.w",
          ".www.",
          "..s..",
          ".s.s."]]
DY = 40                          # dragon top row in his own coordinates (the flight path adds to it)


def haku():
    """Head as a nested PNG; the body is 6px-long slices, each bobbing one step behind the last (--d)
    so a wave runs down it without opening gaps. The first slice moves with the head (--d:0) and starts on
    the head's neck rows, so the join never steps. The mane line and belly shade come from two static
    drop-shadows (see CSS). Paper birds chase his tail."""
    body = ""
    x = len(HAKU[0])
    for i, t in enumerate([6] * 17 + [5, 4, 2], 1):   # as thick as the neck all the way; only the tail tip tapers
        y = DY + 7 + (6 - t) // 2
        # a leg, then a little clawed foot: a pad row reaching forward and three toe pixels under it
        leg = (f"m{1 + i % 2} {t}h2v3h1v1h-5v-1h2zm-2 4h1v1h-1zm2 0h1v1h-1zm2 0h1v1h-1z"
               if i in (3, 4, 12, 13) else "")
        h = (3, 2, 3, 1, 2, 1, 1, 1)[i - 1] if i < 9 else 0
        o = i % 2 * (i > 1)                         # the first tuft is full width, flush against the head's mane
        tuft = (f"M{x + o} {y - h}h{4 - o}v1h2v{h - 1}h-{6 - o}z" if h else
                f"M{x + 4} {y - 1}h5v1h2v1h-2v1h-5z" if i == 20 else "")
        seg = f"d='M{x} {y}h6v{t}h-6z{leg}'/>"
        body += f"<g style='--d:{i - 1}'><path {seg}<path fill='#3ba' d='{tuft}'/></g>" if tuft else f"<path style='--d:{i - 1}' {seg}"
        x += 6
    birds = ""
    for k in (0, 1):                                # the paper shikigami chasing him, two flutter frames
        g = [["."] * 50 for _ in range(21)]
        for j, (bx, by) in enumerate([(0, 4), (11, 13), (21, 1), (32, 10), (44, 3)]):
            for dy, row in enumerate(PAPER[(j + k) % 2]):
                for dx, c in enumerate(row):
                    if c != ".":
                        g[by + dy][bx + dx] = c
        birds += f"<g class='sa-q{k}'>" + runs(["".join(r) for r in g], {"w": "#fff", "s": "#bcd"}, 166, DY - 3) + "</g>"
    whisker = "".join(f"<path class='sa-{c}' stroke='#f6f0e8' d='M6 {DY + 16}.5h2{d}'/>" for c, d in
                      (("a", "m0 1h4m0 1h5"), ("b", "m0 1h5m0-1h4")))
    return (f"<g class='sa-fy'><g class='sa-f'><g class='sa-hb' fill='#fff'>{body}</g>"
            f"<g class='sa-hd'>" + img(art(HAKU, HAKU_PAL), 0, DY) + whisker + "</g>" + birds + "</g></g>")


# ---- small vector sprites ----
RADISH = ["..rrrrr..",
          ".rrrrrrr.",
          "..wwwww..",
          ".wwkwkww.",
          ".wwwwwww.",
          "wwwwwwwww",
          "wwwwwwwww",
          "wwwwwwwws",
          ".wwrrrws.",
          ".ww...ws.",
          ".ww...ws."]
SOOT = [".k.k.",
        "kkkkk",
        "kwkwk",
        "kkkkk",
        ".k.k."]
KASUGA = ["..k..",
          ".kkk.",
          "wwwww",
          "wkwkw",
          "wwwww",
          "ooooo",
          "ooooo",
          "ooooo",
          "ooooo",
          "ooooo",
          "o...o"]
FROG = [".gg.",
        "gkgk",
        "gggg",
        "bbbb",
        "bbbb",
        "g..g"]
OOTORI = ["..gg..",        # the duck spirits
          ".yyyy.",
          "yykyyo",
          "yyyyyo",
          "yyyyyy",
          "yyyyyy",
          ".yyyy.",
          ".o..o."]
LIN = ["....hhh....",         # Lin in the tub she rowed Chihiro out in
       "...hhhh....",
       "...hhss....",
       "..hhhss....",
       "..h.ppp....",
       "....ppp....",
       "twwwwwwwwwt",
       "ttttttttttt",
       ".ttttttttt."]
YUBABA = [".....................hh.......",      # Yubaba's bird form: her huge head, tall grey bun on top, on a dark
          "....................hhhh......",      # bird with a pale rim along its back (wings are sprites)
          "....................hggh......",
          "....................hhhh......",
          "...................hhhhhh.....",
          "...................hhhhhh.....",
          "..................hhhhhhhh....",
          ".................hhhhhssss....",
          ".................hhhssrsss....",
          ".................hhsskksssss..",
          "......ee.........hhssssssssss",
          "..eeeekkee....eeeehsssssssss.",
          "eekkkkkkkkeeeekkkkkssmmss....",
          ".kkkkkkkkkkkkkkkkkkbbsss.....",
          "...kkkkkkkkkkkkkkkkbb........",
          "......kkkkkkkkkkkk..........."]
WING_UP = ["..e.ee....",
           "..ekkkee..",
           ".ekkkkkke.",
           ".kkkkkkkke",
           "ekkkkkkkkk",
           "kkkkkkkkkk",
           "kkkkkkkkkk"]
WING_DN = ["kkkkkkkkkk",      # primaries sweep down and back, notched along the trailing edge
           "kkkkkkkkkk",
           ".kkkkkkkkk",
           "k.kkkkkkk.",
           ".k.kkkkk..",
           "..k.kk...."]
KASHIRA = ["..ggg..",       # one of the three bouncing green heads
           ".ggggg.",
           "gkkgkkg",
           "gwkgwkg",
           "ggggggg",
           "gkkkkkg",
           ".ggggg."]
PIG = ["......e..",          # Chihiro's father (her mother is the same pig, mirrored)
       ".ppppppp.",
       "tpppppkpo",
       ".pppppppo",
       ".pppppp..",
       ".p.p.p.p."]
STALL = ["cocc.c",           # the food they are gorging on
         "bbbbbb",
         "b....b",
         "b....b"]
RIVER = ["...ttttt...",      # the River Spirit: the old man's mask on a body of water
         "..ttttttt..",
         ".wwwtttwww.",
         ".tkkktkkkt.",
         ".ttttttttt.",
         ".ttkkkkktt.",
         ".wttkkkttw.",
         ".wwtttttww.",
         "..wwwwwww..",
         "...wwwww...",
         "....www...."]
RIVER_BODY = ["..bbbbbbbbb..",   # a body of flowing water behind the beard, lit on the left, streaming down
              "..hbbbbbbbd..",
              "..hbbbbbbbd..",
              ".hbbbbbbbbdd.",
              ".hbbhbbbbbbd.",
              ".hbbbhbbbbdd.",
              "hbbbbhbbbbbdd",
              "hbbbbbhbbbbdd",
              "bhbbbbbhbbbbd",
              "hbbbbbbhbbbdd",
              "hbbbbbbbhbbbd"]
FOAM = [[".ff..........ff..",       # the foam collar where he breaks the surface, and spray in two frames
         "mmmmf.......fmmmm"],
        ["m...m.......m...m",
         ".................",
         ".m.............m."],
        [".m...........m...",
         "m..m.........m..m",
         "................."]]
RX, RY = 69, 128             # River Spirit, parked just under the surface line he rises through
BOH = [".mm.mm.",      # round ears, a dark underside edge against the pink sea
       ".mmmmm.",
       "mmmmkmn",
       "mmmmmm.",
       "dmmmmd.",
       ".dddd.."]
TX, TY, YX, YY = 146, 121, -30, 42        # Lin's tub; Yubaba's parked position
WIN = windows()


def flicker(idx, col):
    return "".join(f"M{x} {y}h2v{h}h-2z" for x, y, h, c in (WIN[i % len(WIN)] for i in idx)), col


def pig(x0, flip, d):
    """One parent at the stall: the body stays put and the head dips into the food (--d puts the two out of phase)."""
    rows = [r[::-1] if flip else r for r in PIG]
    hc = range(0, 4) if flip else range(5, 9)
    part = lambda head: ["".join(c if (i in hc and y < 4) == head else "." for i, c in enumerate(r)) for y, r in enumerate(rows)]
    pal = {"p": "#f9a", "e": "#d67", "t": "#d67", "o": "#d67", "k": "#213"}
    return runs(part(False), pal, x0, G - 6) + f"<g class='sa-gz' style='--d:{d}'>" + runs(part(True), pal, x0, G - 6) + "</g>"


def soot(i, x, candy):
    return (f"<g class='sa-j' style='--d:{i}'><use href='#sa-s' x='{x}'/>"
            f"<path fill='{candy}' d='M{x + 2} {PT - 9}h1v1h1v1h-1v1h-1v-1h-1v-1h1z'/></g>")


EY = CHY + 5                     # Chihiro's eye row
SPRITES = (
    # water glints, the shimmer in the bathhouse reflection and on the swells below the rail. First, so every
    # moving thing (ferry, train, Haku) is drawn over the water surface rather than under its sparkle.
    "<path class='sa-a' stroke='#fea' d='M200 110.5h7m40 3h5m-234 0h6m262 9h6m-180 8h5'/>"
    "<path class='sa-b' stroke='#fea' d='M218 112.5h6m52-3h8M8 118.5h7m234 6h6m-90 16h9'/>"
    f"<path class='sa-g' stroke='#fea' d='M{BX - 30} 111.5h4m14 0h5m20 0h4m-36 2h5m18 0h4m-20 2h5m6 3h4'/>"
    "<path class='sa-g sa-g2' stroke='#8f5591' d='M24 143.5h12m50 4h10m46-5h9m96 3h12m30-4h10'/>"
    # stars that twinkle, two cloud wisps that form and drift, chimney smoke puffs, bath steam
    "<path class='sa-a' stroke='#fea' d='M77 4.5h1M203 4.5h1M291 6.5h1M151 22.5h1'/>"
    "<path class='sa-b' stroke='#fea' d='M176 7.5h1M30 19.5h1M225 21.5h1M305 30.5h1'/>"
    # a light comes on in the lonely house on the islet as the train leaves, and its glint on the water
    "<path class='sa-h' stroke='#fc6' d='M262 102.5h1m-2 7h2'/>"
    "<path class='sa-c' fill='#6c4a8c' d='M174 27h44v1h-44zm8-1h22v1h-22z'/>"
    "<path class='sa-c sa-c2' fill='#8f5591' d='M196 35h30v1h-30zm10 1h34v1h-34z'/>"
    + "".join(f"<path class='sa-p' style='--d:{i}' fill='#2a2859' d='M{CHM + 4} 9h4v-1h3v1h1v2h-2v1h-5v-1h-1z'/>" for i in range(3))
    + "".join(f"<path class='sa-p' style='--d:{d}' fill='#fde' fill-opacity='.5' d='M{BX + 29} 55h3v-1h2v1h1v2h-6z'/>" for d in (.5, 2))
    # the boiler-room fire flaring behind its grate, the frog greeter in the doorway
    + f"<path class='sa-l' stroke='#fea' stroke-width='2' stroke-dasharray='1 1' d='M{KX} 95h9'/>"
    + "<g class='sa-j' style='--d:2'>" + runs(FROG, {"g": "#6a4", "b": "#36a", "k": "#213"}, BX + 2, G - 6) + "</g>"
    # the Radish Spirit, two Kasuga spirits and two duck spirits crossing the bridge behind the railing (a nested
    # svg viewport clips them to its span)
    + f"<svg x='{BR0}' y='70' width='{BR1 - BR0}' height='22' viewBox='{BR0} 70 {BR1 - BR0} 22'><g class='sa-r'><g class='sa-rb'>"
    + runs(RADISH, {"w": "#f6f0e8", "s": "#c9bfd6", "r": "#c33", "k": "#213"}, BR0 - 9, G - len(RADISH))
    + "<g id='sa-ks'>" + runs(KASUGA, {"w": "#f6f0e8", "o": "#e74", "k": "#213"}, BR0 - 19, G - len(KASUGA)) + "</g>"
      "<use href='#sa-ks' x='-9'/><g id='sa-ot'>"
    + runs(OOTORI, {"y": "#fd5", "o": "#f83", "g": "#6a4", "k": "#213"}, BR0 - 36, G - len(OOTORI))
    + "</g><use href='#sa-ot' x='-8'/></g></g></svg>"
    + f"<path stroke='#b33' d='M{BR0} {G - 5}.5h{BR1 - BR0}m-{BR1 - BR0} 2h{BR1 - BR0}'/>"
      f"<path stroke='#7a2237' stroke-width='6' stroke-dasharray='1 5' d='M{BR0 + 1} {G - 3}h{BR1 - BR0 - 1}'/>"
      f"<path stroke='#f74' stroke-dasharray='1 11' stroke-width='3' d='M{BR0 + 1} {G - 7.5}h{BR1 - BR0 - 1}'/>"
      f"<path class='sa-l' stroke='#fea' stroke-dasharray='1 11' d='M{BR0 + 1} {G - 7.5}h{BR1 - BR0 - 1}'/>"
    # the spirit ferry, far off on the horizon line; then the island's right end again so it docks behind it
    + f"<g class='sa-y'><path fill='#213' d='M0 {HZ - 3}h32v1h-1v1h-1v1h-28v-1h-1v-1h-1z'/>"
      f"<path fill='#b33' d='M4 {HZ - 8}h22v5h-22zM8 {HZ - 12}h14v3h-14z'/>"
      f"<path fill='#2c6e6a' d='M3 {HZ - 9}h24v1h-24zM7 {HZ - 13}h16v1h-16z'/>"
      f"<path stroke='#fea' stroke-width='3' stroke-dasharray='2 1' d='M5 {HZ - 5.5}h20'/>"
      f"<path stroke='#fea' stroke-dasharray='1 2' d='M9 {HZ - 10.5}h13'/>"
      f"<path class='sa-a' stroke='#f74' stroke-dasharray='1 3' d='M1 {HZ - 3.5}h30'/>"
      f"<path class='sa-b' stroke='#fea' stroke-dasharray='3 2' d='M3 {HZ + 1.5}h26m-22 1h18'/></g>"
    + img(island_end(), IX, IY)
    # the sea railway's poles rise above the train and carry its overhead wire (nearer than the ferry, so after it)
    + f"<path fill='{DARK}' d='" + "".join(f"M{x} 98h1v15h-1zM{x - 3} 99h7v1h-7zM{x - 2} 103h5v1h-5z" for x in POLES) + "'/>"
    + f"<path stroke='{DARK}' d='" + "".join(
        f"M{max(a, 0)} 101.5H{a + (b - a) // 4}m0 1H{b - (b - a) // 4}m0-1H{min(b, W)}"
        for a, b in [(-36, POLES[0]), POLES[:2], POLES[1:], (POLES[2], 346)]) + "'/>"
    # windows going dark / lighting up (before Haku, who flies in front of the building)
    + "".join(f"<path class='sa-m{k}' fill='{c}' d='{d}'/>" for k, (d, c) in enumerate(
        [flicker((3, 31, 58, 77), "#7a2237"), flicker((12, 40, 66), "#7a2237"), flicker((20, 47, 83, 8), "#ffe2a0")]))
    # Yubaba's penthouse windows flare just before she flies out
    + f"<path class='sa-x' stroke='#fff' stroke-width='2' stroke-dasharray='2 2' d='M{BX - 10} 33h18'/>"
    # the three Kashira hopping one after another on the terrace left of the entrance
    + "<defs><g id='sa-kh'>" + runs(KASHIRA, {"g": "#7b5", "k": "#213", "w": "#fff"}, 0, G - 7) + "</g></defs>"
    + "".join(f"<use class='sa-j' style='--d:{d}' href='#sa-kh' x='{BX - 38 + 8 * i}'/>" for i, d in enumerate((1, 1.6, 2.2)))
    # Chihiro's parents as pigs, gorging at a food stall on the terrace right of it
    + runs(STALL, {"c": "#fea", "o": "#f83", "b": "#a63"}, BX + 24, G - 4)
    + pig(BX + 14, False, 0) + pig(BX + 31, True, 1)
    # the River Spirit rising out of the sea under the bridge (a nested svg viewport is the waterline)
    + f"<svg x='{RX - 1}' y='{RY - 22}' width='13' height='22' viewBox='{RX - 1} {RY - 22} 13 22'><g class='sa-rs'>"
    + runs(RIVER_BODY, {"b": "#acf", "h": "#eff", "d": "#79c"}, RX - 1, RY + 7)
    + runs(RIVER, {"t": "#c85", "w": "#fff", "k": "#422"}, RX, RY) + "</g></svg>"
    + "<g class='sa-rf'>" + runs(FOAM[0], {"m": "#fff", "f": "#cdf"}, RX - 3, RY - 1)
    + "<g class='sa-a2'>" + runs(FOAM[1], {"m": "#fff"}, RX - 3, RY - 2) + "</g>"
      "<g class='sa-b2'>" + runs(FOAM[2], {"m": "#fff"}, RX - 3, RY - 2) + "</g></g>"
    # Lin waving from her tub (she bobs; the reflection stays put)
    + f"<path stroke='#6c4a8c' d='M{TX + 1} {TY + 9}.5h9'/><g class='sa-tb'>"
    + runs(LIN, {"h": "#422", "s": "#fc9", "p": "#fab", "w": "#db8", "t": "#a63"}, TX, TY)
    # she sculls: the oar sweeps between two strokes, with a ripple at its blade
    + f"<g class='sa-o1'><path stroke='#532' d='M{TX + 3} {TY + 5}.5h1m-2 1h1m-2 1h1m-2 1h1m-2 1h1'/>"
      f"<path stroke='#fdb' d='M{TX - 3} {TY + 10}.5h3'/></g>"
      f"<g class='sa-o2'><path stroke='#532' d='M{TX + 2} {TY + 5}.5h2m-4 1h2m-4 1h2m-4 1h2m-3 1h1'/>"
      f"<path stroke='#fdb' d='M{TX - 7} {TY + 10}.5h3'/></g>"
    + f"<path class='sa-a' stroke='#fc9' d='M{TX + 7} {TY + 3}.5h1m0-1h1'/>"
      f"<path class='sa-b' stroke='#fc9' d='M{TX + 7} {TY + 4}.5h2'/></g>"
    # Yubaba in her bird form
    + "<g class='sa-yb'>" + runs([r.ljust(30, ".") for r in YUBABA], {"k": "#213", "e": "#768", "h": "#dde", "g": "#99a",
                                                                         "s": "#ec9", "r": "#d33", "m": "#b33", "b": "#36a"}, YX, YY - 3)
    + "<g class='sa-q0'>" + runs(WING_UP, {"k": "#213", "e": "#768"}, YX + 8, YY + 2) + "</g>"
      "<g class='sa-q1'>" + runs(WING_DN, {"k": "#213"}, YX + 8, YY + 11) + "</g></g>"
    + haku()
    # the train, its reflection and wake
    + "<g class='sa-t'>" + img(train(), -158, RAIL - TH)
    + runs(PANTO, {"k": "#213"}, -136, 102) + runs(PANTO, {"k": "#213"}, -56, 102)
    + f"<path opacity='.3' fill='#213' d='M-158 {RAIL + 1}h{TW}v7h-{TW}z'/>"
      f"<path opacity='.5' stroke='#fc6' stroke-dasharray='7 2' d='M-152 {RAIL + 3}.5h64m16 0h64m-140 3h60m20 0h56'/>"
      f"<path class='sa-a' stroke='#fff' stroke-dasharray='3 4' d='M-158 {RAIL}.5h{TW}'/></g>"
    # foreground: platform and travellers, then their idle life
    + img(foreground(), FX, FY)
    + "<g class='sa-nf'>" + img(noface(), NX, NY)
    + f"<path fill='#2a2859' d='" + "".join(f"M{NX + 2 + k} {PT + 6 + 2 * k}h{16 - 2 * k}v1h-{16 - 2 * k}z" for k in range(5))
    + f"'/><path fill='#c9bfd6' d='M{NX + 7} {PT + 9}h5v1h-5z'/>"
    + f"<g class='sa-n'><path fill='#f6f0e8' d='M{NX + 6} {NY + 4}h6v1h1v1h1v12h-1v1h-1v1h-6v-1h-1v-1h-1v-12h1v-1h1z'/>"
    + runs(MASK, MASK_PAL, NX + 4, NY + 4) + "</g>"
      f"<g class='sa-e'><path fill='#14111f' d='M{NX - 4} {NY + 23}h1v-1h6v3h-6v-1h-1z'/><path fill='#fc3' d='M{NX - 4} {NY + 21}h2v1h-2zm3-2h1v2h-1z'/></g></g>"
    + f"<path class='sa-a2' fill='#5a3324' d='M{CHX + 8} {CHY}h2v-1h1v2h-1v1h-2z'/>"
      f"<path class='sa-b2' fill='#5a3324' d='M{CHX + 8} {CHY + 1}h3v1h1v1h-2v-1h-2z'/>"
      f"<path class='sa-k' stroke='#fc9' d='M{CHX + 3} {EY}.5h1m2 0h1'/>"
      f"<g class='sa-e'><path stroke='#fc9' d='M{CHX + 3} {EY}.5h1m2 0h1'/><path stroke='#3a2218' d='M{CHX + 4} {EY}.5h1m2 0h1'/></g>"
    # Boh the mouse carried by the Yu-bird, hovering by Chihiro
    + f"<g class='sa-v'><path class='sa-a2' stroke='#213' d='M{PX - 9} {CHY}.5h1m0 1h1'/>"
      f"<path class='sa-b2' stroke='#213' d='M{PX - 10} {CHY + 2}.5h2'/>"
      f"<path fill='#213' d='M{PX - 8} {CHY + 2}h3v2h-3z'/><path stroke='#fc3' d='M{PX - 5} {CHY + 2}.5h1'/>"
    + runs(BOH, {"m": "#cbd", "k": "#213", "n": "#f9a", "d": "#768"}, PX - 10, CHY + 4) + "</g>"
    # soot sprites with star candy
    + "<defs><g id='sa-s'>" + runs(SOOT, {"k": "#112", "w": "#fff"}, 0, PT - 5) + "</g></defs>"
    + soot(0, PX + 43, "#f9a") + soot(3, PX + 50, "#fe6") + soot(5, PX + 57, "#8ef")
    # the hopping lantern: post, cap, glowing lamp, and the white-gloved hand it stands on
    + f"<g class='sa-j' style='--d:6'><path fill='{DARK}' d='M{LX} 110h1v22h-1zm-3-8h7v1h-7zm1 7h5v1h-5z'/>"
      f"<path fill='#ffe2a0' d='M{LX - 2} 103h5v6h-5z'/><path class='sa-l' fill='#fff' d='M{LX - 1} 104h3v4h-3z'/>"
      f"<path fill='#fff' d='M{LX - 1} 132h3v2h-3zm3 0h1v1h-1z'/></g>"
)
CSS = (
    # twinkles / frame toggles (sa-o hides for half the cycle)
    ".sa-a,.sa-b,.sa-a2,.sa-b2,.sa-q0,.sa-q1{animation:sa-o 5s steps(1) infinite}.sa-b{animation-delay:-2.5s}"
    ".sa-a2,.sa-b2{animation-duration:1.4s}.sa-b2{animation-delay:-.7s}"
    ".sa-q0,.sa-q1{animation-duration:.6s}.sa-q1{animation-delay:-.3s}"
    "@keyframes sa-o{50%{opacity:0}}"
    ".sa-m0,.sa-m1,.sa-m2{opacity:0;animation:sa-m 23s steps(1) infinite}.sa-m1{animation-duration:31s}.sa-m2{animation-duration:41s}"
    "@keyframes sa-m{40%{opacity:1}70%{opacity:0}}"
    ".sa-l{animation:sa-l 3s steps(3) infinite alternate}@keyframes sa-l{from{opacity:.2}}"
    ".sa-c{opacity:0;animation:sa-c 110s steps(80) infinite}.sa-c2{animation-duration:170s;animation-delay:-60s}"
    "@keyframes sa-c{15%,85%{opacity:1}to{transform:translateX(80px);opacity:0}}"
    ".sa-p{opacity:0;animation:sa-p 12s calc(var(--d)*-4s) steps(12) infinite}"
    "@keyframes sa-p{20%{opacity:.9}to{transform:translate(24px,-12px);opacity:0}}"
    ".sa-g{animation:sa-g 2.4s steps(1) infinite}.sa-g2{animation-duration:3.6s}@keyframes sa-g{50%{transform:translateX(2px)}}"
    # moments
    ".sa-t{animation:sa-t 120s steps(480) infinite}@keyframes sa-t{0%,4%{transform:none}24%,to{transform:translateX(480px)}}"
    ".sa-r{animation:sa-r 120s steps(78) infinite}@keyframes sa-r{0%,30%{transform:none}66%,to{transform:translateX(78px)}}"
    ".sa-rb{animation:sa-rb .66s steps(1) infinite}.sa-tb{animation:sa-rb 4s steps(1) infinite}@keyframes sa-rb{50%{transform:translateY(-1px)}}"
    ".sa-rs{animation:sa-rs 120s steps(18) infinite}@keyframes sa-rs{0%,24.5%,32%,to{transform:none}26.5%,30%{transform:translateY(-18px)}}"
    ".sa-rf{opacity:0;animation:sa-rf 120s steps(1) infinite}@keyframes sa-rf{24.5%{opacity:1}32%{opacity:0}}"
    ".sa-yb{animation:sa-yb 120s steps(350) infinite}@keyframes sa-yb{0%,88%{transform:none}99.5%,to{transform:translateX(350px)}}"
    ".sa-y{animation:sa-y 240s steps(176) infinite}@keyframes sa-y{0%,46%,99.5%,to{transform:translateX(320px)}70%,76%{transform:translateX(144px)}}"
    ".sa-f{animation:sa-f 120s steps(540) infinite}@keyframes sa-f{0%,62.5%{transform:translateX(320px)}87.5%,to{transform:translateX(-220px)}}"
    ".sa-fy{animation:sa-fy 120s steps(16) infinite}@keyframes sa-fy{0%,62.5%{transform:none}87.5%,to{transform:translateY(-16px)}}"
    ".sa-hb{filter:drop-shadow(0 -1px #3ba) drop-shadow(0 1px #bcd)}"
    ".sa-hb>*,.sa-hd{animation:sa-w 2.4s calc(var(--d,0)*-.4s) steps(6) infinite alternate}@keyframes sa-w{to{transform:translateY(6px)}}"
    # idle life
    ".sa-n{animation:sa-n 17s steps(1) infinite}@keyframes sa-n{40%{transform:translateY(1px)}52%{transform:translate(-1px,1px)}66%{transform:none}}"
    ".sa-k{opacity:0;animation:sa-k 4.3s steps(1) infinite}@keyframes sa-k{96%{opacity:1}}"
    ".sa-e{opacity:0;animation:sa-e 17s steps(1) infinite}@keyframes sa-e{52%{opacity:1}66%{opacity:0}}"
    ".sa-v{animation:sa-v 1.8s steps(2) infinite alternate}@keyframes sa-v{to{transform:translateY(2px)}}"
    ".sa-j{animation:sa-j 7s calc(var(--d)*-1s) steps(2) infinite}@keyframes sa-j{3%{transform:translateY(-2px)}6%,to{transform:none}}"
    ".sa-nf{animation:sa-nf 120s steps(1) infinite}@keyframes sa-nf{34%{opacity:.7}35%,43%{opacity:.35}44%{opacity:.6}45%{opacity:.85}46%{opacity:1}}"
    ".sa-o1,.sa-o2{animation:sa-o 2.4s steps(1) infinite}.sa-o2{animation-delay:-1.2s}"
    ".sa-gz{animation:sa-gz 3s calc(var(--d)*-1.4s) steps(1) infinite}@keyframes sa-gz{45%{transform:translateY(1px)}}"
    ".sa-h,.sa-x{opacity:0;animation:sa-h 120s steps(1) infinite}@keyframes sa-h{4%{opacity:1}58%{opacity:0}}"
    ".sa-x{animation-name:sa-x}@keyframes sa-x{83%{opacity:.6}86%{opacity:1}99%{opacity:0}}"
)
