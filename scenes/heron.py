"""The Boy and the Heron: the overgrown tower by the pond at night. Mahito stands on the bank with
his bow, the grey heron looms in the shallows opposite him, and between them the warawara rise in a
loose, weaving column towards the moon.

Stacked pixel layers, so anything can pass behind anything without clip paths:
  base PNG (draw)   sky, moon, clouds, far mountains, pond, lily pads, frogs
  LAND PNG          two tree lines with mist between, framing cedars, the tower   (pelicans pass behind)
  NEAR-PADS PNG     the lily pads and frogs just nearer than the boat's lane, again (the boat passes behind)
  FRONT PNG         near bank, the seven granny dolls, Mahito with bow and feather arrow, the heron's body
                    (boat and warawara pass behind)
Sprites (SVG) are in depth order, back to front; sprites always draw over the PNG beneath them, so a
moving thing must come after everything farther than it and before everything nearer:
  behind the land   twinkling stars, a falling star (71 s), a cloud wisp crossing the moon (300 s),
                    four pelicans with pouches (100 s, wings 1 s, each bird out of phase)
  on the far shore  window flicker (9 s), stirring vine runners, the Parakeet King in the doorway with
                    a pink and a blue parakeet joining him (53 s), one more at a window (37 s)
  water surface     glints, lane shimmer, ripple rings at the heron's legs: first on the water
  on the water      Himi in her fire, throwing fireballs (5 s) while the pelicans cross; Kiriko's
                    sailing boat (160 s); NEAR-PADS; carp heads (47 s); warawara
  in front          FRONT, then the heron's head: closed beak / toothy grin with the nose (27 s), a
                    mirrored <use> copy for the head turn (43 s), blink, plume; its rear leg, standing or
                    tucked up (31 s); Mahito's blink and hair; reeds last, nearest of all
Timeline of the first two minutes: window parakeet 1-7 s, carp 9-17, parakeet trio 14-27, Himi and
the pelicans 21-60 (grin 23, leg 26, head turn 36, falling star 49), boat 62-107 (trio again 67-78).
Warawara are three ball sizes in <defs>, stamped with <use> (T3's validator rejects url(#id), so no
markers, clips or masks). The main stream is eight groups, one per sway phase: every ball sits in the
group matching its height along the helix, so the groups swaying out of phase weave a slowly turning
double strand while the parent group rises. Each group holds one rise period plus a <use> copy of it.
"""
import base64, io, math, random
from PIL import Image
from lib import Canvas, UNPAINTED

NAME = "The Boy and the Heron"
SIZE = W, H = 320, 180
COLORS = 16
THEME = {"position": "center 55%",  # wide panes crop vertically; see build wide.png
         
    "canvas": "#0a1230",
    "accent": "#f6b84a",
    "overlay": "#080e26",
    "colors": {
        "sidebar": "#0a182c",
        "sidebarRowSelected": "#17414a",
        "sidebarBorder": "#1c3350",
        "surface": "#0f1d3c",
        "border": "#24406a",
        "text": "#eef0e2",
        "textMuted": "#9fb3c8",
    },
}

N = ["#070c26", "#0b1438", "#122159", "#1a3a80", "#2a5ca0", "#4f8cba", "#9ccbd6"]   # sky top -> horizon, mist
INK = N[0]
CREAM, WARM, SKIN, PINK = "#f6f1da", "#f6b84a", "#f0c49a", "#ee88aa"
TF, T1, T2, T3 = "#123a5e", "#0e2c3e", "#143f49", "#2c6f6e"   # far trees, near trees, bushes, moonlit rim
G0, G1, G2 = "#1b5346", "#2a7a55", "#6cc070"          # vines and lily pads
P0, P1, P2 = "#0d3f4b", "#165a5e", "#2a8c80"          # pond
S1, S2, S3 = "#9aa5ba", "#667291", "#414b6e"          # stone: moonlit, mid, shadow
BANK, NAVY, NAVY2, OCHRE, SHADE = "#0a2231", "#2a4a96", "#1a2f6a", "#c08a3a", "#b8c4d8"
SHORE = 110          # far waterline
TX = 100             # tower centre column
MX, MY = 118, 115    # Mahito top-left (feet on the bank at y=144)
HX, HY = 178, 95     # heron top-left (beak tip); feet in the water at y=148
CX = 160             # warawara column
IX = 229             # Himi, left edge; she stands in her fire on the water at y=122


def art(s):
    rows = s.strip("\n").split("\n")
    w = max(map(len, rows))
    return [r.ljust(w, ".") for r in rows]


def bands(cv, y, rows, soft=True):
    """rows: [(y_end, colour)]. Flat bands with an ordered-dither seam (same helper as spirited_away)."""
    prev = None
    for y1, c in rows:
        for yy in range(y, y1):
            k = yy - y + (0 if soft else 1)
            for x in range(cv.w):
                mix = prev and ((k == 0 and (x % 4 != (yy % 2) * 2)) or (k == 1 and (x + yy) % 2)
                                or (k == 2 and soft and x % 4 == (yy % 2) * 2))
                cv.set(x, yy, prev if mix else c)
        prev, y = c, y1


def disc(cv, cx, cy, r, c):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            if math.hypot(x + .5 - cx, y + .5 - cy) <= r:
                cv.set(x, y, c)


def puff(cv, circles, base, hi, mid, lo, lx=-.6):
    """Circles painted back to front, each with a lit rim on the side facing the moon; flat base."""
    for cx, cy, r in circles:
        for y in range(int(cy - r), min(base, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + .5 - cx, y + .5 - cy
                d = math.hypot(dx, dy)
                if d <= r:
                    rim = d > r - 1.6 and (lx * dx - .8 * dy) > .25 * r
                    cv.set(x, y, hi if rim else (lo if base - y <= 2 else mid))


def spire(cv, cx, top, base, c):
    """A conifer: 1px tip widening one pixel per side every two rows."""
    for y in range(top, base):
        hw = (y - top) // 2
        cv.rect(cx - hw, y, 2 * hw + 1, 1, c)


def cedar(cv, cx, top, base, c, rim, side):
    """A big tiered cedar: each tier widens a pixel per row, then steps back in. The lowest row of
    each tier catches the moon on the side facing it."""
    hw = 0
    for y in range(top, base):
        hw = hw - 4 if (y - top) % 7 == 6 else hw + 1
        cv.rect(cx - hw, y, 2 * hw + 1, 1, c)
        if (y - top) % 7 == 5 and hw > 4:
            cv.rect(cx + side * hw - (side > 0) * 3, y, 4, 1, rim)


# ---------------------------------------------------------------- base layer: sky and pond
def draw():
    cv = Canvas(W, H)
    bands(cv, 0, [(10, N[0]), (26, N[1]), (44, N[2]), (60, N[3]), (76, N[4]), (SHORE, N[5])])
    for x, y in [(22, 8), (58, 5), (104, 13), (131, 6), (238, 16), (264, 4), (226, 30), (46, 24), (150, 21),
                 (74, 31), (288, 12), (12, 34), (214, 9)]:
        cv.set(x, y, CREAM)
    for x, y in [(34, 14), (92, 22), (118, 3), (142, 15), (176, 6), (250, 9), (276, 26), (300, 6), (66, 18), (202, 3),
                 (228, 38), (122, 27), (84, 40), (20, 22)]:
        cv.set(x, y, N[4])
    # moon with a soft halo (each sky band lifted one step) and pale maria
    mx, my = 186, 36
    idx = {tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)): i for i, c in enumerate(N)}
    for y in range(my - 21, my + 22):
        for x in range(mx - 21, mx + 22):
            d = math.hypot(x + .5 - mx, y + .5 - my)
            if d < 19:
                cv.set(x, y, N[idx[cv.get(x, y)] + 1] if cv.get(x, y) in idx else cv.get(x, y))
    disc(cv, mx, my, 13, CREAM)
    for cx, cy, r in [(mx - 4, my - 4, 2.6), (mx + 4, my + 1, 3.2), (mx - 3, my + 6, 1.8), (mx + 6, my - 7, 1.4)]:
        disc(cv, cx, cy, r, N[6])
    for x, y, n, c in [(164, 43, 40, N[4]), (150, 45, 34, N[3]), (204, 52, 44, N[4]), (40, 28, 40, N[2]),
                       (236, 21, 34, N[2]), (108, 36, 26, N[3])]:
        cv.rect(x, y, n, 1, c)                      # thin cloud streaks, one across the moon
    # moonlit clouds: body one band lighter than the sky behind, base fading into it
    puff(cv, [(236, 57, 5), (247, 52, 8), (261, 55, 7), (273, 58, 4)], 61, N[5], N[4], N[3])
    puff(cv, [(46, 58, 4), (56, 54, 6), (66, 58, 4)], 61, N[5], N[4], N[3], lx=.6)
    # two far mountain ranges
    for x in range(W):
        y = 80 + round(4 * math.sin(x * .028 + 2) + 2 * math.sin(x * .09))
        cv.rect(x, y, 1, SHORE - y, N[4])
    for x in range(W):
        y = 87 + round(4 * math.sin(x * .035 + 1) + 1.5 * math.sin(x * .11))
        cv.rect(x, y, 1, SHORE - y, N[3])
    # pond: dark reflection under the far shore, then green water
    bands(cv, SHORE, [(117, P0), (H, P1)], soft=False)
    for x, y, n in [(24, 121, 12), (60, 126, 9), (226, 119, 11), (262, 128, 14), (238, 140, 12), (286, 146, 11),
                    (36, 133, 8), (140, 122, 9), (214, 152, 12), (8, 140, 10), (296, 121, 9)]:
        cv.rect(x, y, n, 1, P2)
    # the tower's reflection as broken streaks, with a warm one under the lit window
    for y, n, j in [(111, 52, 0), (113, 44, 2), (115, 46, -2), (117, 34, 1), (119, 26, -3), (121, 18, 2), (124, 10, -1)]:
        cv.rect(TX - n // 2 + j, y, n, 1, S2)
    cv.rect(TX + 1, 113, 5, 1, WARM)
    cv.rect(TX, 116, 4, 1, WARM)
    # moonlit lane
    for i, y in enumerate(range(113, 157, 2)):
        n = 5 + (i * 5) % 9 + i // 2
        cv.rect(mx - n + (i % 3) * 2, y, 2 * n, 1, P2)
        if i % 2 == 0:
            cv.rect(mx - 3 - (i % 3), y, 5 + i % 4, 1, CREAM)
    pads(cv, 0)
    return cv


BOAT_Y = 126         # waterline of the boat's lane; lily pads are either wholly beyond it or wholly nearer
PADS = [(286, 120, 0), (250, 131, 1), (268, 122, 0), (242, 144, 0), (282, 137, 1), (300, 128, 0),
        (84, 121, 0), (62, 131, 1), (38, 122, 0), (98, 130, 0), (20, 134, 0), (170, 152, 0)]   # x, y, in flower


def pads(cv, near):
    """Lily pads and frogs. near=0 paints them all into the base; near=1 repaints only those just
    nearer than the boat's lane, where its wake reaches (notch left transparent), for the occluder
    layer drawn over the boat."""
    for x, y, f in PADS:
        if near and not BOAT_Y < y <= BOAT_Y + 6:
            continue
        cv.rect(x + 1, y, 6, 1, G2)
        cv.rect(x, y + 1, 3, 1, G2)
        cv.rect(x + 5, y + 1, 3, 1, G2)
        if not near:
            cv.rect(x + 3, y + 1, 2, 1, P1)
        cv.rect(x + 1, y + 2, 6, 1, G1)
        if f:
            cv.rect(x + 2, y - 2, 3, 2, PINK)
            cv.set(x + 3, y - 1, CREAM)
    for x, y in [(99, 128), (251, 129)]:
        frog(cv, x, y)


def near_pads():
    cv = Canvas(W, H)
    pads(cv, 1)
    return cv


def frog(cv, x, y):
    cv.rect(x, y + 1, 5, 1, G1)
    cv.rect(x + 1, y, 2, 1, G1)
    cv.set(x, y, WARM)
    cv.set(x + 3, y, WARM)


# ---------------------------------------------------------------- land layer: trees and tower
def tower(cv):
    cx = TX

    def tone(u):          # u = -1..1 across the drum; moonlight from the right
        return S1 if u > .25 else S2 if u > -.45 else S3

    def drum(y0, y1, hw0, hw1):
        for y in range(y0, y1):
            hw = hw0 + (hw1 - hw0) * (y - y0) // max(1, y1 - y0 - 1)
            for x in range(cx - hw, cx + hw):
                t = tone((x + .5 - cx) / hw)
                if y % 6 == 3 and (x + (y // 6) * 5) % 9 < 4 and t != S3:     # broken mortar courses
                    t = S2 if t == S1 else S3
                cv.set(x, y, t)

    drum(82, SHORE, 26, 28)
    drum(58, 80, 21, 22)
    drum(46, 56, 16, 16)
    for y, hw in [(80, 29), (56, 24)]:              # ledges
        for x in range(cx - hw, cx + hw):
            cv.set(x, y, S1 if x > cx - hw // 2 else S2)
        cv.rect(cx - hw + 1, y + 1, 2 * hw - 2, 1, S3)
    for i, hw in enumerate([3, 6, 9, 11, 13, 15, 16, 17, 18, 18]):      # low slate dome
        for x in range(cx - hw, cx + hw):
            cv.set(x, 36 + i, S2 if x > cx + hw // 3 else S3)
    cv.rect(cx, 31, 1, 5, S3)
    cv.rect(cx - 1, 33, 3, 1, S3)
    cv.rect(cx + 6, 40, 4, 2, INK)                  # hole in the roof
    # arched windows: one lit, the rest dark; slits above; the great doorway below
    for i, x in enumerate([cx - 18, cx - 9, cx + 1, cx + 11]):
        c = WARM if i == 2 else INK
        cv.rect(x, 64, 5, 11, c)
        cv.rect(x + 1, 63, 3, 1, c)
    for x in [cx - 9, cx - 1, cx + 7]:
        cv.rect(x, 48, 2, 5, INK)
    cv.rect(cx - 6, 91, 14, 19, S3)
    cv.rect(cx - 5, 93, 12, 17, INK)
    cv.rect(cx - 4, 92, 10, 1, INK)
    cv.rect(cx - 2, 91, 6, 1, INK)
    cv.rect(cx - 9, 108, 20, 1, S1)
    cv.rect(cx - 11, 109, 24, 1, S2)
    # missing stones along the silhouette, and a crack down the lit face
    for x, y in [(cx + 20, 58), (cx + 20, 59), (cx + 19, 58), (cx + 23, 56), (cx + 22, 56), (cx + 23, 57),
                 (cx + 28, 80), (cx + 27, 80), (cx + 28, 81), (cx + 17, 44), (cx + 17, 45), (cx + 16, 44),
                 (cx + 15, 46), (cx + 15, 47), (cx + 14, 46), (cx + 25, 82), (cx + 25, 83)]:
        cv.px[y][x] = UNPAINTED
    for i, dx in enumerate([16, 16, 15, 15, 16, 16, 17, 17, 17, 18, 18, 19]):
        cv.set(cx + dx, 84 + i, S3)
    # vines: leafy clumps with hanging runners, heaviest on the shadowed left
    r = random.Random(7)
    for bx, by, br in [(cx - 8, 38, 5), (cx - 17, 43, 7), (cx - 23, 56, 6), (cx - 14, 60, 6), (cx - 25, 72, 6),
                       (cx - 18, 80, 5), (cx - 28, 92, 6), (cx - 21, 99, 5), (cx + 20, 57, 4), (cx + 26, 82, 4),
                       (cx + 4, 36, 3)]:
        for x in range(bx - br + 1, bx + br, 2):
            n = r.randrange(4, 14)
            y0 = by + int(math.sqrt(br * br - (x - bx) ** 2))
            cv.rect(x, y0, 1, n, G1)
            cv.set(x, y0 + n, G0)
        for y in range(by - br, by + br + 1):
            for x in range(bx - br, bx + br + 1):
                dx, dy = x + .5 - bx, y + .5 - by
                if math.hypot(dx, dy) <= br:
                    k = (.6 * dx - .8 * dy) / br
                    cv.set(x, y, G2 if k > .62 else G1 if k > -.25 else G0)
    for x, y, n in [(cx + 9, 58, 7), (cx + 15, 58, 10), (cx + 13, 82, 9), (cx + 22, 86, 12), (cx - 3, 82, 6)]:
        cv.rect(x, y, 1, n, G0)


def land():
    cv = Canvas(W, H)
    for x in range(W):                              # far tree line, bluer with distance
        t = min(1, max(0, (x - 140) / 24))
        y = round(78 + 5 * t + 2 * math.sin(x * .37 + 2) + 1.5 * math.sin(x * .13))
        cv.rect(x, y, 1, SHORE - y, TF)
    for cx, top in [(52, 60), (72, 66), (132, 62), (152, 70), (168, 76), (198, 72), (214, 78), (244, 74), (262, 80)]:
        spire(cv, cx, top, SHORE, TF)
    for x in range(W):                              # near tree line: taller behind the tower
        t = min(1, max(0, (x - 140) / 24))
        y = round(86 + 4 * t + 1.5 * math.sin(x * .5) + 1.5 * math.sin(x * .19 + 1))
        cv.rect(x, y, 1, SHORE - y, T1)
    for cx, top in [(60, 68), (44, 76), (140, 70), (124, 78), (160, 82), (182, 84), (192, 80),
                    (208, 85), (226, 81), (238, 86), (254, 82)]:
        spire(cv, cx, top, SHORE, T1)
    for x, y, n in [(140, 104, 34), (196, 106, 44), (128, 107, 58), (226, 104, 30), (40, 106, 26), (252, 107, 24)]:
        cv.rect(x, y, n, 1, T3)                     # mist lying on the far shore
    cv.rect(0, SHORE - 1, W, 1, INK)
    tower(cv)
    # bushes swallowing the tower's foot
    puff(cv, [(TX - 34, 102, 9), (TX - 24, 106, 6), (TX + 33, 101, 9), (TX + 43, 105, 7), (TX + 25, 107, 4)],
         SHORE, T3, T2, T1, lx=.6)
    for cx, top in [(4, 16), (27, 44), (316, 22), (296, 50), (279, 74)]:
        cedar(cv, cx, top, SHORE, INK, N[2], 1 if cx < 160 else -1)
    return cv


# ---------------------------------------------------------------- front layer: bank, Mahito, heron
MAHITO = art("""
....kkkkkk
...kkkkkkkk
..kkkkkkkkkk
..kkkkkkkssk
..kkkbbsssss
..kkkssskss
..kksssssssss
...kssssssss
....sssssss
.....sss
....jwwwwj
...jjjjjjjl
..jjjjjjyjjl
..jjjjjjjjjjl
..jjdjjjyjjjjjjlss
..jjdjjjjjjl
..jjdjjjyjjl
..jjdjjjjjjl
..jsdjjjyjjl
...jjjjjjjj
...tttttttt
...tttttttt
...tttt.tttt
...sss...sss
...sss...sss
...sss...sss
...www...www
...www...www
...kkkk..kkkk
""")
BOW = [14, 15, 16, 16, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 17, 17, 17, 16, 16, 15, 14]   # from row 3
HERON = art("""
..............swwwwww
...............swwwww
................swwwww
.................swwwww
..................swwwww
..................sswwww
..................sswwww
..................swwwww
.................swwwww
................swwwww
...............swwwwww
..............swwkwwwgggg
.............swwwkwwgggggggl
.............swwwwwwgggggggggll
............swwwkwwkkggggggggggggl
............swwwkwkkkgggggggggggggll
............swwwwwwkkgggddddgggggggggl
............swwkwwggggggggggdddddgggggggl
.............swwkwggggggggggggdddddddggg
.............swwwwwgggggggggggggggddddddddg
..............swwwggggggggggggggggggdddddddd
..............sswwwgggggggggggggggg...ddddddd
...............sswwwggggggggggggg.......ddddd
................ssswwggggggggg............ddd
..................sssgggggg
....................sgggg
.....................yy..oo
.....................y....o
.....................y....o
.....................y....o
.....................y....o
.....................y....o
.....................y....o
.....................y....o
....................yy....o
....................y....oo
....................y....o
....................y....o
....................y....o
....................y....o
....................y....o
....................y....o
....................y....o
....................y....o
....................y....o
..................yyy..ooo
""")   # painted from row 7; rows 0-6 are the animated head


def front():
    cv = Canvas(W, H)
    for x in range(0, 172):
        y = 144 + (0 if x < 140 else (x - 139) // 2)
        cv.rect(x, y, 1, H - y, BANK)
        cv.set(x, y, G1)
    for x in [9, 23, 24, 41, 60, 143, 150]:
        cv.rect(x, 142 + (x > 140) * (x - 139) // 2, 1, 2, G1)
    # the seven old maids as the little dolls that guard Mahito, lined up on the bank behind him
    for i, c in enumerate([OCHRE, S2, PINK, G1, "#5578c8", WARM, S2]):
        x, y = 71 + 6 * i, 138 + (i % 3 == 1)      # grey bun and hair, face, robe widening to the hem
        cv.set(x + 2, y - 1, S1)
        cv.rect(x + 1, y, 3, 1, S1)
        cv.rect(x + 1, y + 1, 3, 1, SKIN)
        cv.rect(x + 1, y + 2, 3, 1, c)
        cv.rect(x, y + 3, 5, 141 - y, c)
    cv.paint(MAHITO, {"k": INK, "s": SKIN, "j": NAVY, "d": NAVY2, "t": NAVY2, "l": "#5578c8", "w": CREAM, "y": WARM, "b": CREAM},
             MX, MY)
    for i, dx in enumerate(BOW):
        if 0 < i < 23 and i != 11:
            cv.set(MX + 14, MY + 3 + i, S2)         # bowstring
        cv.set(MX + dx, MY + 3 + i, OCHRE)
    cv.rect(MX + 12, MY + 13, 10, 1, WARM)          # the arrow, fletched with the heron's feather
    cv.rect(MX + 22, MY + 13, 2, 1, SHADE)
    cv.rect(MX + 9, MY + 13, 3, 1, CREAM)
    cv.rect(MX + 9, MY + 12, 2, 1, SHADE)
    # 'o', the rear leg, is left out: it is a sprite so the heron can tuck it up
    cv.paint(HERON, {"k": INK, "w": CREAM, "s": SHADE, "g": S1, "d": S2, "l": SHADE, "y": WARM}, HX, HY + 7)
    return cv


# ---------------------------------------------------------------- SVG helpers
def layer(cv, dx=0, dy=0):
    """A canvas as a cropped palette PNG <image>; unpainted pixels are transparent."""
    ys = [y for y, row in enumerate(cv.px) if any(p != UNPAINTED for p in row)]
    xs = [x for row in cv.px for x, p in enumerate(row) if p != UNPAINTED]
    x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
    cols = [UNPAINTED] + sorted({p for row in cv.px[y0:y1] for p in row[x0:x1]} - {UNPAINTED})
    img = Image.new("P", (x1 - x0, y1 - y0))
    img.putpalette([v for c in cols for v in c])
    img.putdata([cols.index(p) for row in cv.px[y0:y1] for p in row[x0:x1]])
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True, transparency=0)
    return (f"<image x='{x0 + dx}' y='{y0 + dy}' width='{x1 - x0}' "
            f"height='{y1 - y0}' href='data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}'/>")


def px(rows, pal, x0=0, y0=0):
    """ASCII art -> one stroked path per colour: 1px runs at y+.5 joined by relative moves. A colour
    of None leaves the stroke to be inherited, so a <use> copy can recolour that part."""
    runs = {}
    for dy, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch, n = row[x], 1
            while x + n < len(row) and row[x + n] == ch:
                n += 1
            if ch in pal:
                runs.setdefault(ch, []).append((x0 + x, y0 + dy, n))
            x += n
    out = ""
    for ch, rs in runs.items():
        d, ex, ey = "", 0, 0
        for i, (x, y, n) in enumerate(rs):
            d += f"M{x} {y + .5:g}h{n}" if i == 0 else f"m{x - ex}{'' if y < ey else ' '}{y - ey}h{n}"
            ex, ey = x + n, y
        out += f"<path{pal[ch] and f' stroke={chr(39)}{pal[ch]}{chr(39)}' or ''} d='{d}'/>"
    return out


# ---------------------------------------------------------------- warawara
WPAL = {"w": "#fff", "s": "#abd", "k": "#124"}
MARKS = {   # id suffix -> art, centred on the vertex
    "l": art("""
..wwwww
.wwwwwww
wwwwwwwww
wwkwwwkww
wwwwwwwww
.swwwwws
..sssss
"""),
    "m": art("""
.wwwww
wwwwwww
wkwwwkw
swwwwws
.sssss
"""),
    "s": art("""
.www
wkwkw
wwwww
.sss
"""),
}
RISE, LAM, GROUPS = 240, 80, 8     # one rise loop in px, helix pitch, sway phase groups


def balls():
    """The three ball sizes as <defs> groups, centred on (0,0), to be stamped with <use>."""
    return "<defs>" + "".join(f"<g id='bh-{k}'>{px(a, WPAL, -(len(a[0]) // 2), -(len(a) // 2))}</g>"
                              for k, a in MARKS.items()) + "</defs>"


def stamp(k, pts):
    return "".join(f"<use href='#bh-{k}' x='{x}' y='{y - 12}'/>" for x, y in sorted(pts, key=lambda q: -q[1]))


def twice(i, body, period):
    """One rise period plus a <use> copy of it a period lower, so translateY(-period) loops seamlessly.
    Only static content is copied: the swaying group wraps both, because animations inside a <use>
    copy are not guaranteed to stay in phase with the original."""
    return f"<g id='bh-{i}'>{body}</g><use href='#bh-{i}' y='{period}'/>"


def column():
    """The main stream. Each ball belongs to the sway group matching its height along the helix, so the
    eight groups (each swaying with its own delay) weave a slowly turning double strand."""
    r = random.Random(11)
    groups = [[] for _ in range(GROUPS)]
    for s in (0, 1):
        for i in range(RISE // 10):
            if r.random() < .3:
                continue
            y = i * 10 + r.randrange(-3, 4)
            groups[round((y / LAM + s / 2) * GROUPS) % GROUPS].append((CX + r.randrange(-3, 4), y))
    return "".join(f"<g style='--d:{g}'>{twice(f'c{g}', stamp('l' if g % 3 == 2 else 'm', q), RISE)}</g>"
                   for g, q in enumerate(groups))


def strays(seed, n, x0, x1, period):
    r = random.Random(seed)
    return [(r.randrange(x0, x1), i * period // n + r.randrange(-6, 7)) for i in range(n)]


def specks(pts):
    """The smallest strays: 2x2 dots, white over pale blue, as two stroked paths."""
    pts = sorted(pts, key=lambda q: -q[1])
    return "".join(f"<path stroke='{c}' d='" + "".join(f"M{x - 1} {y - 13 + o}.5h2" for x, y in pts) + "'/>"
                   for c, o in (("#fff", 0), ("#abd", 1)))


# ---------------------------------------------------------------- characters that move
HEAD = art("""
...............wwwww
.............wwwwwwwww
............wwwwwkkkkkkk
...........wwwyywwkkkkkkk
...........wwwkywwwwwww
...........wwwwwwwwwww
............swwwwwwwww
""")
BEAK = art("""
.
.
.
.........yy
....yyyyyyy
yyyyyyyyyyy
....oooooooo
""")
GRIN = art("""
.
.
yyyy
..yyyyyyyyy
......yyyynn
.....twtwtwnn
.....rrrrrrr
....oooooooo
""")
HPAL = {"w": "#f6f1da", "k": "#070c26", "y": "#f6b84a", "o": "#c08a3a", "s": "#b8c4d8", "t": "#fff", "r": "#a23",
        "n": "#e9a"}

PELICAN = art("""
...........www
yyyyyyyyy.wwwww
.ooooooooowwwwwwwwwwwww
..ooooooo.wwwwwwwwwwwwwww
....ooo....gwwwwwwwwwwggk
.............ggggggg
""")
WING_UP = art("""
.................kk
................wwkk
...............wwwwk
..............wwwww
.............wwwwww
""")
WING_DN = art("""
.............gwwwww
..............gwwwwk
...............gwwkk
................gkk
""")
BPAL = {"w": "#fff", "g": "#9ab", "k": "#124", "y": "#fb4", "o": "#e83"}

PARAKEET = art("""
..gggg
.gggggg
gwkggkwg
gwkggkwg
gggooggg
.ggooggg
gggggggg
gglllggg
glllllgg
glllllgg
.gllllg
..gggg
..o..o
""")
QPAL = {"g": None, "l": "#ffd", "w": "#fff", "k": "#124", "o": "#f83"}   # body colour comes from the <use>
PEEK = art("""
.ppp
ppppp
wkpkw
ppopp
ppppp
""")
CARP = art("""
...ll
..lkkl
..lkkl
.ggllgg
gwggggwg
gkggggkg
tggggggt
.tttttt
""")   # a golden carp gulping at the surface: round lips up, eyes out to the sides
FPAL = {"g": "#d94", "l": "#fdb", "k": "#124", "w": "#fff", "t": "#4ba"}

BOAT = art("""
............m
....ssssssssm
...sssssssssm
...sssspssssm
...sssspssssm
..ssssspssssm
..sppppppppsm
..ssssspssssm
..ssssspssssm
.sssssspssssm.....kkk
.sssssspssssm....kkkkk.e
.sppppppppppm....fffk..e
.sssssspssssm....fffk..e
.sssssspssssm.....ff...e
ssssssspssssm....jjjj..e
ssssssspssssm...jjjjjj.e
mmmmmmmmmmmmm...frrrrffe
............m....jjjj..e....c
............m....wwww..eccccc
bb..........m....ww.ww.eciibb
.bbbbbbbbbbbbbbbbbbbbbbbbbbbb
..dddddddddddddddddddddddddd
...dddddddddddddddddddddddd
.....gg.ggggg..gggg.ggg....g.gg
........ggg...ggggg...g
""")   # Kiriko: hair tied back, blue jacket, red sash, pale trousers, a pole in hand and her catch astern

HIMI = art("""
f.....f
p.hhh.p
phhhhhp
.hfffh.
.hfffh.
..ppp..
..ppp..
.rrrrr.
.rrrrr.
rrrrrrr
..f.f..
""")
IPAL = {"h": "#742", "f": "#fc9", "p": "#f8a", "r": "#d44"}
FIRE = [art(a) for a in ("""
.
.
.
...y.....y
..yyyy.yyyy
..yyyyyyyyy
""", """
..o.......o
.oo......oo
.ooo....ooo.o
ooo.o..o.ooo
.o........o
""", """
...o.....o
..oo.....oo
o.ooo...ooo
.oo.o..o.ooo
..o........o
""")]


def himi():
    """Himi, wreathed in her own fire on the water, throwing fireballs up at the pelicans. She is only
    there while they cross (bh-hi shares the flock's period and delay)."""
    flames = "".join(f"<g{c}>{px(a, {'y': '#fd6', 'o': '#f83'}, IX - 3, 117)}</g>"
                     for c, a in zip(("", " class='bh-u'", " class='bh-d'"), FIRE))
    ball = (f"<g class='bh-fw'><path stroke='#f83' d='M{IX + 3} 105.5h1m-2 1h3m-2 1h1'/>"
            f"<path stroke='#ffd' d='M{IX + 3} 106.5h1'/></g>")
    return (f"<g class='bh-hi'><path stroke='#c73' d='M{IX - 2} 124.5h10m-8 2h7'/>"
            f"{px(HIMI, IPAL, IX, 111)}{flames}{ball}</g>")


def boat():
    cv = Canvas(40, 30)
    cv.paint(BOAT, {"m": "#5a3a22", "s": CREAM, "p": OCHRE, "k": INK, "w": CREAM, "f": SKIN, "r": "#c23b3b",
                    "j": "#4a7fc0", "b": "#8a5a30", "d": "#5a3a22", "e": "#8a5a30", "c": SHADE, "i": PINK, "g": P2}, 0, 0)
    return layer(cv, 380, 104)


def heron_head():
    plume = f"<path class='bh-p' stroke='#070c26' fill='none' d='M{HX + 24} {HY + 2.5}h4l5 3m-8-2h4l5 4'/>"
    lid = f"<path class='bh-e' stroke='#f6f1da' d='M{HX + 14} {HY + 3.5}h2m-2 1h2'/>"
    return (f"<g class='bh-ha'><g id='bh-h'>{px(HEAD, HPAL, HX, HY)}{lid}"
            f"<g class='bh-c'>{px(BEAK, HPAL, HX, HY)}</g><g class='bh-o'>{px(GRIN, HPAL, HX, HY)}</g>{plume}</g></g>"
            f"<use class='bh-hb' href='#bh-h' transform='matrix(-1 0 0 1 {2 * HX + 37} 0)'/>")


def pelicans():
    bird = (f"<g id='bh-b'>{px(PELICAN, BPAL, 340, 61)}<g class='bh-u'>{px(WING_UP, BPAL, 340, 57)}</g>"
            f"<g class='bh-d'>{px(WING_DN, BPAL, 340, 65)}</g></g>")
    return (f"<g class='bh-fl'><g class='bh-fb'>{bird}<use href='#bh-b' x='30' y='-8' style='--d:2'/>"
            "<use href='#bh-b' x='58' y='3' style='--d:1'/><use href='#bh-b' x='84' y='-12' style='--d:3'/></g></g>")


def rings(cx, cy):
    out = ""
    for a, d in [(3, 0), (6, 2), (9, 1)]:
        out += (f"<path style='--d:{d}' d='M{cx - a + 1} {cy - .5}h{2 * a - 2}m-{2 * a - 1} 1h1m{2 * a - 2} 0h1"
                f"m-{2 * a - 1} 1h{2 * a - 2}'/>")
    return f"<g class='bh-q' stroke='#4ba'>{out}</g>"


def reed(x, top):
    return f"M{x} 180v-{177 - top}h-1v-7h3v7h-1v{177 - top}z"


SPRITES = (
    balls()
    # --- behind the land: twinkling stars, a falling star, pelicans
    + "<path class='bh-ta' stroke='#fea' d='M88 17.5h1m118 6h1m-176 13h1m252-22h1'/>"
      "<path class='bh-tb' stroke='#fea' d='M166 9.5h1m-118 31h1m200-12h1m-136 2h1'/>"
      "<path class='bh-z' stroke='#fff' d='M250 6l8-3'/>"
    + "<path class='bh-cl' fill='#2a5ca0' d='M-90 33h46v1h-46zm14 2h50v1h-50zm-210 22h40v1h-40zm8-2h22v1h-22z'/>"
    + pelicans()
    + layer(land())
    # --- on the far shore: the lit window flickering, vine runners, parakeets
    + f"<path class='bh-f' fill='#c73' d='M{TX + 1} 64h5v11h-5z'/>"
    + "".join(f"<path class='bh-v' style='--d:{i}' stroke='#2a7a55' d='M{TX + x}.5 {y}v{n}'/>"
              for i, (x, y, n) in enumerate([(-22, 86, 8), (22, 62, 8), (28, 87, 9)]))
    # the Parakeet King (crowned) in the doorway, then a pink and a blue one flanking it
    + f"<g class='bh-k' style='--d:30' stroke='#4b4'><g id='bh-pk'>{px(PARAKEET, QPAL, TX - 3, 96)}</g>"
      f"<path stroke='#fc4' d='M{TX - 2} 94.5h1m1 0h1m1 0h1m-5 1h5'/></g>"
      "<use class='bh-k' style='--d:28' href='#bh-pk' x='-12' stroke='#e8a'/>"
      "<use class='bh-k' style='--d:26' href='#bh-pk' x='12' stroke='#5ad'/>"
    + f"<g class='bh-k bh-k2' style='--d:30'>{px(PEEK, {'p': '#fd5', 'w': '#fff', 'k': '#124', 'o': '#f83'}, TX + 11, 70)}</g>"
    # --- water surface: glints, lane shimmer, ripple rings. First on the water, so everything that
    #     moves or stands on the pond draws over them.
    + "<path class='bh-ta' stroke='#4ba' d='M70 116.5h8m150 5h7m-200 13h6m252-9h8'/>"
      "<path class='bh-tb' stroke='#4ba' d='M124 113.5h7m128 3h8m-222 18h6m160 10h7'/>"
      "<path class='bh-ta' stroke='#f6f1da' d='M181 118.5h6m-9 12h5m3 12h7'/>"
    + rings(HX + 23, 149)
    # --- on the water, far to near: Kiriko's boat, the lily pads and frogs nearer than its lane
    #     (redrawn from the base so the boat passes behind them), fish heads
    + himi()
    + f"<g class='bh-bo'><g class='bh-bb'>{boat()}</g></g>"
    + layer(near_pads())
    + f"<g class='bh-fi' style='--d:30'><g id='bh-fs'>{px(CARP, FPAL, 148, 129)}</g>"
      "<use href='#bh-fs' x='84' y='6'/><use href='#bh-fs' x='-108' y='7'/></g>"
    # --- warawara, over the pond but behind the bank, Mahito, the heron and the reeds
    + f"<g class='bh-w3'>{twice('e0', specks(strays(5, 9, 62, 240, 200)), 200)}</g>"
      f"<g class='bh-s'><g class='bh-w2'><g style='--d:0'>{twice('d0', stamp('s', strays(8, 6, 120, 215, 200)), 200)}</g>"
      f"<g style='--d:3'>{twice('d1', stamp('s', strays(9, 6, 110, 205, 200)), 200)}</g></g>"
    + f"<g class='bh-w1'>{column()}</g></g>"
    + layer(front())
    # --- in front: heron head, Mahito's blink and hair, reeds
    + heron_head()
    # the heron's rear leg: standing, or tucked up for a few seconds
    + f"<g stroke='#c08a3a'><path class='bh-ld' d='M{HX + 25} {HY + 33}.5h2M{HX + 26}.5 {HY + 34}v8M{HX + 25} {HY + 42}.5h2"
      f"M{HX + 25}.5 {HY + 43}v9M{HX + 23} {HY + 52}.5h3'/><path class='bh-lu' d='M{HX + 25} {HY + 33}.5h2"
      f"M{HX + 26}.5 {HY + 34}v4M{HX + 27} {HY + 37}.5h3M{HX + 29}.5 {HY + 38}v2'/></g>"
    + f"<path class='bh-e' stroke='#f0c49a' d='M{MX + 8} {MY + 5.5}h1'/>"
      f"<path class='bh-hr' stroke='#070c26' d='M{MX + 1} {MY + 3.5}h1m-2 1h2'/>"
    + f"<path class='bh-s' fill='#070c26' d='{reed(60, 118)}{reed(67, 128)}{reed(52, 132)}'/>"
      f"<path class='bh-s bh-s2' fill='#070c26' d='{reed(248, 124)}{reed(256, 112)}{reed(263, 130)}'/>"
)
CSS = (
    # warawara: rise (parent) + sway (each group, phase from --d)
    ".bh-w1{animation:bh-r 64s linear infinite}@keyframes bh-r{to{transform:translateY(-240px)}}"
    ".bh-w2,.bh-w3{animation:bh-r2 90s linear infinite}.bh-w3{animation-duration:130s}"
    "@keyframes bh-r2{to{transform:translateY(-200px)}}"
    ".bh-w1 [style],.bh-w2 [style]{animation:bh-x 7s calc(var(--d)*-1.75s) ease-in-out infinite alternate}"
    ".bh-w2 [style]{animation-duration:11s}"
    "@keyframes bh-x{from{transform:translateX(-10px)}to{transform:translateX(10px)}}"
    # twinkles, falling star, window flicker
    ".bh-ta,.bh-tb{animation:bh-t 5s infinite}.bh-tb{animation-delay:-2.5s}@keyframes bh-t{50%{opacity:0}}"
    ".bh-z{opacity:0;animation:bh-z 71s -20s linear infinite}"
    "@keyframes bh-z{96%{opacity:0;transform:none}97%{opacity:1}to{opacity:0;transform:translate(-50px,19px)}}"
    ".bh-f{opacity:0;animation:bh-f 9s infinite}@keyframes bh-f{8%,30%,62%{opacity:0}12%,34%,70%{opacity:.6}}"
    # pelicans: the flock crosses right to left; wings alternate, each bird out of phase
    ".bh-fl{animation:bh-fl 100s -75s linear infinite}@keyframes bh-fl{to{transform:translateX(-1500px)}}"
    ".bh-u,.bh-d{animation:bh-t 1s calc(var(--d,0)*-.23s) steps(1) infinite}"
    ".bh-d{animation-delay:calc(var(--d,0)*-.23s - .5s)}"
    ".bh-fb{animation:bh-fb 3.1s ease-in-out infinite alternate}@keyframes bh-fb{to{transform:translateY(4px)}}"
    # Kiriko's boat: glides right to left, bobbing a pixel
    ".bh-bb{animation:bh-bb 2.6s steps(1) infinite}@keyframes bh-bb{50%{transform:translateY(1px)}}"
    ".bh-bo{animation:bh-bo 160s -105s linear infinite}@keyframes bh-bo{to{transform:translateX(-1280px)}}"
    # pop-ins: hidden until the last 16% of their period (bh-on); their counterparts hide then (bh-off)
    ".bh-k,.bh-fi,.bh-hb,.bh-o,.bh-lu{opacity:0;animation:bh-on 53s calc(var(--d,0)*-1s) steps(1) infinite}"
    ".bh-ha,.bh-c,.bh-ld{animation:bh-off 43s steps(1) infinite}"
    "@keyframes bh-on{84%{opacity:1}}@keyframes bh-off{84%{opacity:0}}"
    ".bh-k2{animation-duration:37s}.bh-fi{animation-duration:47s}.bh-hb{animation-duration:43s}"
    ".bh-c,.bh-o{animation-duration:27s}.bh-ld,.bh-lu{animation-duration:31s}"
    # Himi: fades in and out with the flock; a fireball rises from her hands every 5 s
    ".bh-hi{animation:bh-hi 100s -75s infinite}@keyframes bh-hi{32%{opacity:1}35%,96%{opacity:0}99%{opacity:1}}"
    ".bh-fw{animation:bh-fw 5s steps(25) infinite}"
    "@keyframes bh-fw{from{opacity:0}20%,70%{opacity:1}to{opacity:0;transform:translateY(-50px)}}"
    ".bh-cl{animation:bh-cl 300s -80s linear infinite}@keyframes bh-cl{to{transform:translateX(700px)}}"
    # heron: blink, plume
    ".bh-e{opacity:0;animation:bh-e 6s steps(1) infinite}@keyframes bh-e{96%{opacity:1}}"
    f".bh-p{{transform-origin:{HX + 24}px {HY + 3}px;animation:bh-p 3.4s ease-in-out infinite alternate}}"
    "@keyframes bh-p{to{transform:rotate(12deg)}}"
    ".bh-hr{animation:bh-t 2.6s steps(1) infinite}"
    # ripple rings and reeds
    ".bh-q path{opacity:0;animation:bh-q 3.6s calc(var(--d)*-1.2s) steps(1) infinite}"
    "@keyframes bh-q{from{opacity:1}33%{opacity:0}}"
    ".bh-v{transform-box:fill-box;transform-origin:top;animation:bh-v 5s calc(var(--d)*-1.3s) ease-in-out infinite alternate}"
    "@keyframes bh-v{to{transform:rotate(9deg)}}"
    ".bh-s{transform-origin:0 180px;animation:bh-s 4.5s ease-in-out infinite alternate}.bh-s2{animation-delay:-2s}"
    "@keyframes bh-s{from{transform:skewX(-2deg)}to{transform:skewX(3deg)}}"
)
