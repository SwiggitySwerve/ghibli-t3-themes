"""Kiki's Delivery Service: Kiki and Jiji fly a lazy circuit over Koriko on a bright sea-wind morning.

Full-budget version at 320x180 (the 4.5K compact one is in compact/scenes/kiki.py).

Static layer (PNG, ~56 colours): banded sky, cumulus, far headlands and lighthouse, the bay with three
far-off sails, the hill, Koriko as five hand-listed tiers of houses (gable-end, eaves-on and hipped
roofs, rationed chimneys and dormers, shutters, flower boxes, shop awnings; the top two tiers hazier),
the clock tower (the old janitor in its belfry) and a church, the quay, and the corner bakery with Lily
the white cat and a black kitten on its roof and the bread-wreath sign in its window. On the pavement:
Osono and her husband the baker beside the pretzel sign, a pecking crow. Ursula at her easel is a sprite.
Sprites (SVG), back to front: sea glints and sun sparkle (first, so everything else draws over the
water surface), the horizon steamer and the roof it sails behind, a cloud wisp, clock hands, the
janitor's deck brush, lighthouse and beacon lamps, the "FREEDOM" dirigible and the tower top it passes
behind, gulls, Tombo flying, the tacking dinghy, two moored boats, chimney
smoke, Lily's tail, the hanging pretzel sign, the pavement idles (Osono's wave and Ursula's brush arm,
the baker's loaf, the crows pecking and one hopping up with a flap), Tombo on the quay (with his
shadow), the quay-edge bollards he rides behind, and Kiki + Jiji + radio.
Depth by scale: Kiki is nearest, then flying Tombo and the gulls, then the town and tower, then the
dirigible and wisps, so each is drawn over everything farther; static things a farther sprite crosses
(tower top, bakery roof) are redrawn over it from the PNG itself (patch()).

The 120 s loop, in loop time (the scene opens 20 s in, see PH, so that Kiki starts mid-screen):
  Kiki       0-26 s climbs out of the harbour heading right, 26-43 s crosses the town above the clock
             face, 43-56 s hovers on the right, turns at 50 s and waves to Tombo below, 56-73 s flies
             back, 73-103 s dives to the harbour, 103-120 s hovers low over the bay and turns
  gulls      0-42 s, right to left, high
  Tombo      35 s rides in along the quay, 52-54 s stops and turns, 56 s the propeller lifts him off
             and he climbs away (gone by 70 s); 74-110 s he flies back across the sky behind Kiki
  dirigible  80-150 s, left to right behind the tower
  dinghy     sails in 60-108 s, goes about at 113 s, sails out by 180 s
The steamer keeps its own 150 s period; the clock hands tick once a minute. Kiki's idle life (bob,
bow / hair / hem / straw flutter, Jiji's tail, blinks, the radio swinging) runs throughout.

Big detailed sprites (Kiki, dirigible, boats, both Tombos) are small nested PNGs; their moving parts are
two-frame overlays of stroked 1px runs. One parametrised keyframe (kk-t, driven by --x/--y/--t/--n/--d)
serves every crossing, and one (kk-o) every two-frame flip.
"""
import base64, math, random, struct, zlib
from lib import Canvas, UNPAINTED, hx

NAME = "Kiki's Delivery Service"
SIZE = W, H = 320, 180
COLORS = 64
# Chrome colours: the night-blue of Kiki's dress for the panels, her bow for the accent, the warm cream
# of Koriko's walls for text.
THEME = {
    "canvas": "#141a33",
    "accent": "#f4606a",
    "overlay": "#0f1a36",
    "position": "center 80%",   # wide panes crop vertically: keep the quay above the composer, Kiki below the top
    "colors": {"sidebar": "#111730", "sidebarRowSelected": "#27325c", "sidebarBorder": "#2b3763",
               "surface": "#1b2342", "border": "#34406e", "text": "#f6ecd8", "textMuted": "#a9b6d6"},
}

S = ["#2e6cc4", "#3d7fd2", "#5694df", "#77ade9", "#9cc6f1", "#c4e0f7"]      # sky, top -> horizon
C0, C1, C2 = "#ffffff", "#dce9f8", "#b3cbea"                                  # cloud: lit, body shade, belly
FAR1, FAR2 = "#93b8de", "#739fca"                                             # headlands across the bay
SEA = ["#8cc3ea", "#5aa0dc", "#3f88cf", "#3175bf", "#2a64ad", "#25549a"]      # horizon -> foreground
GFAR, G1, G2, G3, G4 = "#86b39c", "#74b356", "#58994b", "#3b7742", "#2b5a3a"  # hills and trees
STONE, STONE_SH, STONE_DK = "#e3d5b8", "#bca88d", "#8a7767"
WALLS = {"c": ("#f8ecd2", "#d9bf9c"), "y": ("#f4d88e", "#d2ac64"), "p": ("#f3c7a9", "#cf9d85"),
         "w": ("#fffaf0", "#ddd3c4")}
ROOFS = {"o": ("#f7a05e", "#e9793f", "#b84d2c"), "r": ("#e9793f", "#c85a35", "#8e3b2f"),
         "t": ("#7cc4b4", "#4fa59b", "#357f7c")}
EAVE, BRICK, WIN, DARK = "#7a3226", "#a85a3c", "#33456b", "#1c2340"
WINF, SKIN, PINK = "#6a7fa8", "#f3c7a9", "#ee8888"                              # far windows; people
TEAL, SIGN, GOLD, RED = "#357f7c", "#2c5a4c", "#f2c14e", "#d62a3a"
HZ = 112         # horizon row
QUAY = 146       # quay surface row
TX = 200         # clock tower centre


def bands(cv, y, rows, soft=True):
    """rows: [(y_end, colour)]. Flat bands with ordered-dither seams (3 rows when soft, else 1)."""
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
    """Daylight cumulus: puffs painted back to front. Each is white where it faces the sun (upper left),
    shaded towards its lower right, so a puff in front cuts a bright edge into the shade of the one behind."""
    for cx, cy, r in circles:
        for y in range(int(cy - r), min(base, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + .5 - cx, y + .5 - cy
                if math.hypot(dx, dy) <= r:
                    lit = -(.5 * dx + .85 * dy) / r
                    c = C0 if lit > -.12 else C1 if lit > -.68 else C2
                    if base - y <= 2:
                        c = C2
                    elif base - y <= 5 and c == C0:
                        c = C1
                    cv.set(x, y, c)


def hill_y(x):
    t = min(1, max(0, (x - 84) / 130))
    return 112 - 33 * t * t * (3 - 2 * t) - (2.5 * math.sin((x - 214) * .045) if x > 214 else 0) \
        + max(0, 102 - x) * 1.5


def tier_base(x, f):
    """Ground line of a row of houses: f=0 on the quay, f=1 just under the hilltop."""
    return int(round(QUAY - f * (QUAY - (hill_y(x) + 14))))


def tree(cv, x, y, r):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + 1:
                cv.set(x + dx, y + dy, G2 if dx + 2 * dy < -r else G3 if dx + dy < r else G4)


def bld(cv, x, base, w, h, kind, wall, roof, o="", foot=5, far=False):
    """One house. kind: G gable end towards us, S roof slope towards us, H hipped.
    o flags: c/C chimney left/right (not on gables), d dormer(s), s shutters, 2..9 roof height, q quay
    front (door at street level), a shop awning, n no door or ground-floor windows (a plain wall behind
    the figures on the quay), x no windows at all (behind the easel). far: hazier windows and eaves for the upper tiers."""
    lit, sh = WALLS[wall]
    hi, mid, lo = ROOFS[roof]
    win, eave = (WINF, lo) if far else (WIN, EAVE)
    top = base - h
    cv.rect(x, top, w, h + foot, lit)
    cv.rect(x + w - 2, top, 2, h + foot, sh)
    cv.rect(x, top, w - 2, 1, sh)
    step = 5 if "s" in o else 4
    for fy in range(base - (12 if "q" in o else 5), top + 1, -6) if "x" not in o else ():
        for wx in range(x + 2, x + w - 4, step):
            cv.rect(wx, fy, 2, 3, win)
            if "s" in o:
                cv.rect(wx - 1, fy, 1, 3, TEAL)
                cv.rect(wx + 2, fy, 1, 3, TEAL)
                cv.rect(wx - 1, fy + 3, 4, 1, RED if (wx + fy) % 2 else GOLD)   # flower boxes
    if "n" in o:
        pass
    elif "a" in o:
        for i in range(w):
            cv.rect(x + i, base - 8, 1, 2, RED if i // 2 % 2 else C0)
        cv.rect(x + 1, base - 6, w - 7, 5, WALLS["y"][0])
        cv.rect(x + w - 5, base - 6, 3, 6, EAVE)
    elif "q" in o:
        cv.rect(x + w // 2 - 1, base - 6, 3, 6, EAVE)
        if w >= 11:
            cv.rect(x + 2, base - 6, 2, 3, WIN)
            cv.rect(x + w - 5, base - 6, 2, 3, WIN)
    rh = next((int(ch) for ch in o if ch.isdigit()), 5)
    if kind == "G":
        i = 0
        while True:
            x0, x1, y = x - 1 + i, x + w + 1 - i, top - 1 - i
            if x1 - x0 <= 0:
                break
            m = (x0 + x1) // 2
            cv.rect(x0, y, x1 - x0, 1, lit)
            cv.rect(x0, y, min(2, m - x0) or 1, 1, mid)
            cv.rect(max(m, x1 - 2), y, x1 - max(m, x1 - 2), 1, lo)
            i += 1
        if w >= 9:
            cv.rect(x + w // 2 - (w % 2 == 0), top - 3, 1 + (w % 2 == 0), 2, win)
        return
    for i in range(rh):
        ins = i if kind == "H" else (i + 1) // 3
        c = eave if i == 0 else hi if i == rh - 1 else mid
        cv.rect(x - 1 + ins, top - 1 - i, w + 2 - 2 * ins, 1, c)
    if "d" in o:
        for dx in ([w // 2 - 1] if w < 16 else [w // 4, 3 * w // 4 - 2]):
            cv.rect(x + dx, top - 4, 3, 3, lit)
            cv.rect(x + dx + 1, top - 3, 1, 2, win)
            cv.rect(x + dx - 1, top - 5, 5, 1, lo)
            cv.rect(x + dx, top - 6, 3, 1, lo)
    for ch, cx in (("c", x + w // 4), ("C", x + 3 * w // 4 - 1)):
        if ch in o:
            cv.rect(cx, top - rh - 2, 2, 4, BRICK)
            cv.rect(cx - 1, top - rh - 3, 4, 1, eave)


CLOCK = (TX, 77)  # clock centre; the hands are sprites


def tower(cv, cx):
    hi, mid, lo = ROOFS["t"]
    cv.rect(cx - 9, 88, 18, 30, STONE)                       # shaft
    cv.rect(cx + 5, 88, 4, 30, STONE_SH)
    cv.rect(cx - 9, 99, 14, 1, STONE_SH)
    for y in (91, 103):
        cv.rect(cx - 1, y, 2, 5, WIN)
    cv.rect(cx - 12, 67, 24, 20, STONE)                      # clock stage
    cv.rect(cx + 8, 67, 4, 20, STONE_SH)
    cv.rect(cx - 13, 87, 26, 1, STONE_DK)
    cv.rect(cx - 13, 66, 26, 1, STONE_DK)
    for dy in range(-8, 9):
        for dx in range(-8, 9):
            d = math.hypot(dx, dy)
            if d <= 7.7:
                cv.set(cx + dx, CLOCK[1] + dy, DARK if d > 6.4 else WALLS["w"][0])
    for k in range(12):
        a = k * math.pi / 6
        cv.set(cx + round(5 * math.sin(a)), CLOCK[1] - round(5 * math.cos(a)), DARK if k % 3 == 0 else STONE_SH)
    cv.rect(cx - 10, 57, 20, 9, STONE)                       # belfry: three arches, a bell in the middle one
    cv.rect(cx + 7, 57, 3, 9, STONE_SH)
    for ax in (cx - 8, cx - 2, cx + 4):
        cv.rect(ax, 60, 3, 6, WIN)
        cv.set(ax, 60, STONE)
        cv.set(ax + 2, 60, STONE_SH if ax > cx else STONE)
    cv.rect(cx - 11, 56, 22, 1, STONE_DK)                   # (the bell is a sprite: it swings as Kiki passes)
    for sx in (cx - 13, cx + 11):                            # corner pinnacles
        cv.rect(sx, 62, 2, 4, STONE if sx < cx else STONE_SH)
        cv.rect(sx, 60, 2, 2, mid if sx < cx else lo)
        cv.set(sx + (sx > cx), 59, mid if sx < cx else lo)
    for i in range(16):                                      # steep copper roof
        hw = 11 - (i * 10) // 15
        cv.rect(cx - hw, 55 - i, hw, 1, mid)
        cv.rect(cx, 55 - i, hw, 1, lo)
        cv.set(cx - hw, 55 - i, hi)
    cv.rect(cx - 5, 50, 3, 3, STONE)                         # lucarne
    cv.set(cx - 4, 51, WIN)
    cv.rect(cx - 5, 49, 3, 1, lo)
    cv.rect(cx, 33, 1, 7, DARK)                              # spire and ball
    cv.rect(cx, 35, 1, 2, GOLD)


def church(cv, x, base):
    hi, mid, lo = ROOFS["t"]
    bld(cv, x + 7, base, 19, 9, "S", "w", "r", "6")
    cv.rect(x, base - 28, 8, 30, STONE)
    cv.rect(x + 6, base - 28, 2, 30, STONE_SH)
    cv.rect(x + 3, base - 25, 2, 4, WIN)
    cv.rect(x + 3, base - 16, 2, 4, WIN)
    cv.rect(x - 1, base - 29, 10, 1, STONE_DK)
    for i in range(12):
        hw = 4 - i // 3
        cv.rect(x + 4 - hw, base - 30 - i, hw, 1, mid)
        cv.rect(x + 4, base - 30 - i, hw, 1, lo)
    cv.rect(x + 4, base - 46, 1, 5, DARK)
    cv.rect(x + 3, base - 45, 3, 1, DARK)


def poplar(cv, x, y, h):
    for i in range(h):
        hw = 0 if i < 2 else 1
        cv.rect(x - hw, y - h + i, 2 * hw + 1, 1, G3)
        cv.set(x + hw, y - h + i, G4)


FONT = {"B": "110101110101110", "A": "010101111101101", "K": "101101110101101",
        "E": "111100110100111", "R": "110101110101101", "Y": "101101010010010",
        "F": "111100110100100", "D": "110101101101110", "O": "111101101101111", "M": "101111111101101"}


def text(cv, s, x, y, c):
    for ch in s:
        for i, b in enumerate(FONT[ch]):
            if b == "1":
                cv.set(x + i % 3, y + i // 3, c)
        x += 4


def bakery(cv, x):
    """Guchokipanya: the corner bakery on the quay, with its sign board, awning and shop window."""
    lit, sh = WALLS["w"]
    hi, mid, lo = ROOFS["o"]
    w, top = 34, QUAY - 29
    cv.rect(x, top, w, 29, lit)
    cv.rect(x + w - 2, top, 2, 29, sh)
    cv.rect(x, top, w - 2, 1, sh)
    for wx in range(x + 4, x + w - 4, 8):                    # upstairs windows, shutters, flower boxes
        cv.rect(wx, top + 3, 2, 4, WIN)
        cv.rect(wx - 1, top + 3, 1, 4, TEAL)
        cv.rect(wx + 2, top + 3, 1, 4, TEAL)
        cv.rect(wx - 1, top + 7, 4, 1, RED)
    cv.rect(x, top + 10, w, 7, SIGN)                         # sign board
    text(cv, "BAKERY", x + 6, top + 11, WALLS["c"][0])
    for i in range(w + 2):                                   # awning
        cv.rect(x - 1 + i, top + 17, 1, 2, RED if i // 2 % 2 else C0)
    cv.rect(x + 2, top + 19, 19, 9, DARK)                    # shop window with loaves
    cv.rect(x + 3, top + 20, 17, 7, WALLS["y"][0])
    cv.rect(x + 11, top + 20, 1, 7, DARK)
    for bx, by in ((13, 22), (17, 22), (14, 25), (17, 25)):
        cv.rect(x + bx, top + by, 2, 1, BRICK)
    cv.rect(x + 12, top + 23, 8, 1, WALLS["y"][1])
    # the baker's bread wreath with the little witch in the middle, hung in the left pane
    cv.paint([".bbbbb.", "b.....b", "b..k..b", "b.kkk.b", "b.....b", ".bbbbb."], {"b": BRICK, "k": DARK}, x + 4, top + 20)
    cv.rect(x + 24, top + 19, 6, 10, TEAL)                   # door
    cv.rect(x + 25, top + 20, 4, 4, WALLS["y"][0])
    cv.rect(x - 9, top + 12, 9, 1, DARK)                     # bracket for the hanging pretzel sign
    for i in range(8):                                       # roof
        c = EAVE if i == 0 else hi if i == 7 else mid
        cv.rect(x - 1 + (i + 1) // 3, top - 1 - i, w + 2 - 2 * ((i + 1) // 3), 1, c)
    cv.rect(x + 15, top - 5, 5, 4, lit)                      # dormer
    cv.rect(x + 17, top - 4, 1, 3, WIN)
    cv.rect(x + 14, top - 6, 7, 1, lo)
    cv.rect(x + 15, top - 7, 5, 1, lo)
    cv.rect(x + 5, top - 13, 4, 9, BRICK)                    # oven chimney
    cv.rect(x + 4, top - 14, 6, 1, EAVE)
    # Lily, the white cat with the pink collar, sunning herself on the roof (her tail is a sprite)
    cv.paint(["w.w....", "www....", "www....", ".pwww..", ".wwwwS.", ".wwwwS."], {"w": C0, "S": C1, "p": PINK},
             x + LILY[0], top + LILY[1])
    cv.paint(["k.k", "kkk", "kkk"], {"k": DARK}, x + 10, top - 4)   # and a black kitten by the chimney


LILY = (23, -7)    # relative to the bakery's top-left wall corner


def mix(a, b, t=.5):
    return "#" + "".join(f"{round(p + (q - p) * t):02x}" for p, q in zip(hx(a), hx(b)))


SKY_ROWS = [(8, S[0]), (18, mix(S[0], S[1])), (28, S[1]), (39, mix(S[1], S[2])), (50, S[2]), (61, mix(S[2], S[3])),
            (72, S[3]), (82, mix(S[3], S[4])), (92, S[4]), (102, mix(S[4], S[5])), (HZ, S[5])]


def sky(cv):
    bands(cv, 0, SKY_ROWS)
    for x, y, n, c in [(20, 22, 46, S[2]), (34, 23, 22, S[2]), (232, 30, 40, S[2]), (250, 31, 30, S[2]),
                       (60, 8, 30, S[1])]:
        cv.rect(x, y, n, 1, c)


def clouds(cv):
    cloud(cv, [(262, 60, 11), (282, 52, 14), (303, 60, 13), (318, 56, 10), (290, 68, 14), (312, 72, 12),
               (270, 72, 9)], 90)
    cloud(cv, [(121, 45, 7), (156, 39, 8), (172, 51, 7), (103, 59, 8), (190, 73, 7),
               (130, 52, 13), (147, 46, 12), (161, 56, 12), (113, 68, 15), (138, 68, 18), (165, 72, 15),
               (181, 82, 11), (95, 86, 14), (121, 90, 17), (151, 92, 18), (177, 96, 13), (77, 98, 10),
               (196, 101, 8)], 109)
    cloud(cv, [(10, 93, 12), (-4, 100, 10), (28, 99, 10), (46, 103, 7)], 109)


def land(cv):
    for x in range(W):                                       # horizon haze and far headlands
        cv.rect(x, 109, 1, 3, S[5])
    x = 0
    for n, h in [(8, 9), (10, 10), (9, 9), (10, 8), (9, 7), (10, 6), (8, 5), (10, 4), (9, 3), (8, 2), (7, 1)]:
        cv.rect(x, HZ - h, n, h, FAR1)
        x += n
    x = 0
    for n, h in [(7, 5), (9, 6), (10, 5), (9, 4), (8, 3), (9, 2), (8, 1)]:
        cv.rect(x, HZ - h, n, h, FAR2)
        x += n
    # lighthouse: red cap, lantern (lit by a sprite), dark gallery, a white tower with a red band that
    # widens at its foot, and the keeper's cottage beside it
    cv.paint([".rr.", ".gg.", "gggg", ".wS.", ".wS.", ".rr.", ".wS.", "wwwS", "wwwS", "wwwS"],
             {"r": RED, "g": WINF, "w": C0, "S": C1}, 56, HZ - 15)
    cv.paint(["oooo", "wwwS", "wwwS"], {"o": ROOFS["r"][1], "w": C0, "S": C1}, 60, HZ - 8)
    bands(cv, HZ, [(114, SEA[0]), (120, SEA[1]), (130, SEA[2]), (143, SEA[3]), (158, SEA[4]), (H, SEA[5])],
          soft=False)
    for x in range(226, W):                                  # hazy far hill
        yt = int(round(84 - 12 * math.sin((x - 226) / 94 * 1.5)))
        cv.rect(x, yt, 1, H - yt, GFAR)
    for x in range(78, W):                                   # the town's hill
        yt = int(round(hill_y(x)))
        cv.rect(x, yt, 1, H - yt, G1)
        cv.rect(x, yt + 9 + int(2 * math.sin(x * .2)), 1, H, G2)
    for x, y, r in [(222, 88, 4), (230, 84, 5), (239, 88, 4), (247, 83, 4), (282, 86, 5), (291, 82, 4),
                    (300, 86, 5), (309, 81, 4), (317, 85, 5), (104, 112, 4), (112, 108, 5), (121, 111, 4),
                    (131, 105, 5), (141, 101, 4), (150, 97, 5), (160, 93, 4)]:
        tree(cv, x, y, r)
    for x, y, h in [(276, 90, 11), (254, 92, 9)]:
        poplar(cv, x, y, h)


TIERS = [
    # (f, x0, [(w, h, kind, wall, roof, flags)])   a gap is (n,)
    # Chimneys and dormers are rationed (about one house in three) so the upper tiers stay calm.
    (1.0, 164, [(9, 7, "G", "c", "o", ""), (12, 6, "S", "y", "r", "c"), (24,), (11, 7, "S", "w", "o", "4"),
                (9, 8, "G", "p", "r", ""), (14, 6, "S", "c", "o", "d")]),
    (.78, 148, [(11, 8, "G", "y", "o", ""), (15, 7, "S", "c", "o", "d"), (9, 9, "G", "w", "r", ""),
                (16, 7, "S", "p", "o", "C"), (5,), (13, 8, "S", "c", "r", ""), (11, 9, "G", "y", "o", ""),
                (17, 7, "H", "w", "t", "6"), (9, 9, "G", "c", "o", ""), (14, 7, "S", "p", "r", "d"),
                (11, 8, "G", "w", "o", ""), (16, 7, "S", "y", "o", "C")]),
    (.56, 131, [(13, 8, "S", "c", "o", "c"), (9, 10, "G", "p", "o", ""), (15, 8, "S", "w", "r", "d"),
                (11, 10, "G", "y", "o", ""), (17, 8, "S", "c", "o", ""), (9, 11, "G", "w", "o", ""),
                (14, 9, "S", "p", "o", "C"), (11, 10, "G", "c", "r", ""), (18, 8, "S", "y", "o", "d"),
                (9, 11, "G", "w", "o", ""), (15, 8, "S", "c", "t", ""), (11, 10, "G", "p", "o", ""),
                (16, 8, "S", "w", "o", "C"), (12, 9, "S", "y", "r", "")]),
    (.32, 116, [(12, 10, "S", "y", "o", ""), (9, 12, "G", "c", "o", ""), (16, 9, "S", "w", "o", "d"),
                (11, 12, "G", "p", "r", ""), (18, 10, "S", "c", "o", "C"), (9, 13, "G", "y", "o", ""),
                (15, 10, "S", "w", "t", ""), (11, 12, "G", "c", "o", ""), (17, 10, "S", "p", "o", "d"),
                (9, 13, "G", "w", "r", ""), (16, 10, "S", "y", "o", "c"), (11, 12, "G", "c", "o", ""),
                (18, 10, "S", "w", "o", "d"), (13, 11, "S", "p", "r", ""), (11, 12, "G", "y", "o", "")]),
    # quay front: plain walls (n, x) behind the crows at 244-258 and the painter,
    # who has one long white house (255-283) as her backdrop
    (0, 136, [(11, 22, "G", "y", "o", "qs"), (13, 18, "G", "p", "r", "q"), (9, 24, "G", "c", "o", "q"),
              (17, 17, "S", "w", "o", "qad6"), (11, 23, "G", "p", "o", "qs"), (13, 20, "G", "y", "r", "q"),
              (9, 25, "G", "w", "o", "q"), (16, 18, "S", "c", "t", "qd6"), (11, 22, "G", "y", "o", "qn"),
              (29, 19, "S", "w", "o", "qnxd6"), (13, 22, "G", "p", "o", "q"),
              (11, 22, "G", "y", "o", "q"), (13, 20, "G", "c", "o", "q")]),
]
FAR_FROM = .78   # tiers at or above this height factor get the hazy treatment


def town(cv):
    for f, x, row in TIERS:
        for b in row:
            if len(b) > 1:
                w, h, kind, wall, roof, o = b
                base = tier_base(x + w / 2, f)
                bld(cv, x, base, w, h, kind, wall, roof, o, QUAY - base if f == .32 else 5, f >= FAR_FROM)
            x += b[0] + (len(b) > 1)
        if f == 1:
            tower(cv, TX)
            # the old janitor in the belfry gallery, pushing his deck brush (the brush is a sprite)
            cv.paint(JANITOR, {"W": C0, "s": SKIN, "j": SEA[1], "e": DARK}, JX, 66 - len(JANITOR))
            church(cv, 258, tier_base(262, .78))
    # The plain gable behind the crows (243-253), which Tombo rides past: shutters and flower boxes on its
    # upper pair, its lower pair dropped (it sat behind his head), a shaded plinth, and the hill seam at
    # 242 closed by widening its neighbour.
    lit, sh = WALLS["y"]
    cv.rect(245, QUAY - 12, 6, 3, lit)
    for x in (244, 251):
        cv.rect(x, QUAY - 18, 1, 3, TEAL)
    cv.rect(245, QUAY - 15, 2, 1, RED)
    cv.rect(249, QUAY - 15, 2, 1, GOLD)
    cv.rect(243, QUAY - 7, 9, 7, sh)
    for y in range(QUAY - 22, QUAY):
        if cv.get(242, y) == hx(G2):
            cv.set(242, y, ROOFS["t"][1] if y < QUAY - 19 else WALLS["c"][1])


def front(cv):
    bakery(cv, 100)
    for y in range(QUAY + 8, H):                             # the bay wraps round under the quay
        for x in range(62, W):
            cv.set(x, y, SEA[5] if y < QUAY + 10 and (x + y) % 2 else cv.get(x % 60, y))
    cv.rect(62, QUAY, W - 62, 2, STONE)                      # quay and pier
    cv.rect(62, QUAY + 2, W - 62, 5, STONE_SH)
    # dressed stone: two courses with staggered joints in a soft mortar tone (not a ruler of dark ticks)
    mortar = mix(STONE_SH, STONE_DK, .45)
    cv.rect(62, QUAY + 4, W - 62, 1, mortar)
    for x in range(64, W, 12):
        cv.rect(x, QUAY + 2, 1, 2, mortar)
        cv.rect(x + 6, QUAY + 5, 1, 2, mortar)
    cv.rect(62, QUAY + 7, W - 62, 1, DARK)
    cv.rect(63, QUAY - 7, 3, 7, C0)                          # pier beacon
    cv.rect(63, QUAY - 5, 3, 2, RED)
    cv.rect(63, QUAY - 8, 3, 1, DARK)
    for x in (150, 214, 302):                                # lamp posts (none where the painter stands)
        cv.rect(x, QUAY - 10, 1, 10, DARK)
        cv.rect(x - 1, QUAY - 12, 3, 2, DARK)
        cv.set(x, QUAY - 11, GOLD)
    # washing strung below the upper windows of the pink house right of the painter
    cv.paint(["kkkkkkkkkk", ".wwS.rr.b.", ".wwS.rr.b.", ".wwS....b."],
             {"k": STONE_DK, "w": C0, "S": C1, "r": RED, "b": SEA[2]}, 285, QUAY - 15)
    # (the bollards on the quay edge are a sprite: Tombo rides behind them)
    # The bakers stand on the pier just left of the pretzel sign (x 72-89, sea and hillside behind them);
    # they and the pecking crow are on the house-front line (feet on row 145), behind Tombo's lane.
    # Ursula and her easel stand at the quay edge, nearer than him, so they are a sprite (painter()).
    for rows, x in ((OSONO, OX), (FUKUO, FX)):
        cv.paint(rows, PPAL, x, QUAY - len(rows))
    cv.paint(["kkk.", "kkkk", ".k.."], PPAL, CROWX + 1, QUAY - 3)
    for x, y in ((63, QUAY - 11), (149, QUAY - 15)):         # gulls perched on the beacon and a lamp post
        cv.rect(x, y, 3, 2, C0)
        cv.set(x + 2, y - 1, C0)
        cv.set(x, y + 1, G4)
        cv.set(x + 1, y + 2, GOLD)
    r = random.Random(4)                                     # wave dashes, longer and sparser towards us
    sea = [hx(c) for c in SEA]
    for i, y in enumerate((116, 118, 121, 124, 127, 131, 135, 139, 144, 149, 159, 165, 172)):
        for _ in range(DASHES):
            n = r.randrange(3 + i // 2, 6 + i)
            x = r.randrange(-4, W)
            if all(cv.get(min(W - 1, max(0, xx)), y) in sea for xx in (x - 2, x, x + n, x + n + 2)):
                k = sea.index(cv.get(max(0, x), y))
                cv.rect(x, y, n, 1, SEA[max(0, k - 1)])
    for x, y, rows in FAR_BOATS:                             # far-off sails, out by the headland
        cv.paint(rows, {"w": C0, "d": WIN}, x, y)


# (x, y, art): smaller the further out. They sit in rows 113-116: below the steamer on the horizon (which
# is further off and passes behind them), above the glints, and clear of the sun sparkle (x 20-36).
FAR_BOATS = [(4, 113, [".w", "ww", "dd"]), (43, 114, ["w.", "ww", "dd"]), (52, 113, ["w", "w", "d"])]


DASHES = 11
CROW = "#222233"
# Osono (h hair framing her face, e eyes, p mouth and dress, w apron over her bump) and her husband the
# baker (white cap and whites, m moustache), beside the pretzel sign; Ursula (H hair, e eye, r top, b trousers)
# a step back from her easel, a palette (T) in her far hand. Her brush arm is a sprite.
OSONO = [".hhhhh..", "hhhhhhh.", "hsssssh.", "hsesesh.", ".sspss..", "..pppp..", ".ppwwpp.", ".pwwwwp.", ".pwwwwwp",
         ".pwwwwwp", ".pwwwwp.", ".pppppp.", ".pppppp.", "..e..e.."]
FUKUO = ["...www...", "..wwwww..", "..wwwww..", "..sssss..", "..seses..", "..smmms..", "...sss...",   # 9 wide: barrel
         "wwwwwwwwS", "wwwwwwwwS", "wwwwwwwwS", "w.wwwwS.w", "s.wwwwS.s", "..wwwwS..", "..wwwwS..",   # chest, arms held
         "..bbbbb..", "..bb.bb..", "..ee.ee.."]                                                        # clear of a 5px waist
URSULA = [".HHHH....", "HHHHHH...", "HHsss....", "HHses....", ".Hss.....", ".rrrr....", ".rrrr....", ".rrrr....",
          ".rrrrs...", ".bbbb.TrT", ".bbbb.bTT", ".bbbb....", ".b..b....", ".b..b....", ".e..e...."]
# The easel, 9 wide and symmetrical: a mast, the framed canvas (T frame; n night sky, g stars, S the pale
# winged horse), a ledge under it, two front legs splaying evenly and a darker back leg (E) angling out behind.
EASEL = ["....L....", "....L....", ".TTTTTTT.", ".TngnnnT.", ".TnnnngT.", ".TnSSnnT.", ".TSSSSnT.", ".TnSnSnT.",
         ".TnnngnT.", ".TTTTTTT.", "LLLLLLLLL", "..L.E.L..", "..L.E.L..", ".L..E..L.", ".L...E.L.", "L....E..L"]
OX, FX, UX, EX = 72, 81, 266, 275
PPAL = {"h": BRICK, "H": EAVE, "s": SKIN, "p": PINK, "w": C0, "S": C1, "e": DARK, "m": EAVE, "b": WIN, "r": RED,
        "n": SEA[5], "g": GOLD, "L": BRICK, "E": EAVE, "T": WALLS["y"][1], "k": CROW}
PY = QUAY + 2      # the painter's ground line: the front edge of the pavement, level with the bollards' feet
# Ursula's crows, to her left: one pecking on the pavement (body in the PNG, head a sprite), one hopping
# (all sprite), and one perched on the bollard at 262 (a sprite, drawn over Tombo like the bollard itself).
CROWX, HOPX = 246, 253
# The janitor, 9px tall, facing right in the left arch of the belfry: W white hair, j overalls
JANITOR = ["..WW.", "..ss.", "..ss.", ".jjjj", ".jjjj", ".jjj.", ".jjj.", ".j.j.", ".e.e."]
JX = TX - 9


def draw():
    cv = Canvas(W, H)
    for part in (sky, clouds, land, town, front):
        part(cv)
    return cv


# ------------------------------------------------------------------ sprites
def art(rows, w, base=None):
    """Rows of 'x:chars' tokens -> equal-length strings ('.' transparent). Later tokens overwrite."""
    out = []
    for i, r in enumerate(rows):
        g = list(base[i]) if base else ["."] * w
        for tok in r.split():
            x, s = tok.split(":")
            g[int(x):int(x) + len(s)] = s
        out.append("".join(g))
    return out


def png(rows, pal):
    """ASCII art -> base64 palette PNG ('.' transparent), at whichever bit depth and zlib strategy
    comes out smallest."""
    keys = sorted({ch for r in rows for ch in r if ch in pal})
    idx = {k: i + 1 for i, k in enumerate(keys)}
    best = None
    for bits in ([4] if len(keys) < 16 else []) + [8]:
        raw = bytearray()
        for r in rows:
            v = [idx.get(ch, 0) for ch in r]
            raw.append(0)
            if bits == 8:
                raw += bytes(v)
            else:
                v += [0] * (len(v) % 2)
                raw += bytes(a << 4 | b for a, b in zip(v[::2], v[1::2]))
        for st in range(4):
            co = zlib.compressobj(9, 8, 15, 9, st)
            z = co.compress(bytes(raw)) + co.flush()
            if best is None or len(z) < len(best[1]):
                best = (bits, z)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return base64.b64encode(
        b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", len(rows[0]), len(rows), best[0], 3, 0, 0, 0))
        + ch(b"PLTE", b"\0\0\0" + bytes(v for k in keys for v in hx(pal[k]))) + ch(b"tRNS", b"\0")
        + ch(b"IDAT", best[1]) + ch(b"IEND", b"")).decode()


def img(rows, pal, x, y, cls=""):
    return (f"<image{cls and f' class={chr(39)}{cls}{chr(39)}'} x='{x}' y='{y}' width='{len(rows[0])}' "
            f"height='{len(rows)}' href='data:image/png;base64,{png(rows, pal)}'/>")


def short(c):
    """#aabbcc -> #abc when that is exact."""
    return "#" + c[1] + c[3] + c[5] if c[1] == c[2] and c[3] == c[4] and c[5] == c[6] else c


def runs(rows, pal, x0, y0):
    """ASCII art -> one stroked <path> per colour, 1px runs joined by relative moves. Horizontal or
    vertical runs, whichever is shorter for that colour."""
    out = ""
    for ch in sorted({c for r in rows for c in r if c in pal}):
        best = None
        for vert in (0, 1):
            g = [list(c) for c in zip(*rows)] if vert else rows
            d, px, py = "", 0, 0
            for j, row in enumerate(g):
                i = 0
                while i < len(row):
                    if row[i] != ch:
                        i += 1
                        continue
                    n = 1
                    while i + n < len(row) and row[i + n] == ch:
                        n += 1
                    if vert:
                        d += (f"M{x0 + j}.5 {y0 + i}" if not d else f"m{j - px} {i - py}") + f"v{n}"
                        px, py = j, i + n
                    else:
                        d += (f"M{x0 + i} {y0 + j}.5" if not d else f"m{i - px} {j - py}") + f"h{n}"
                        px, py = i + n, j
                    i += n
            d = d.replace(" -", "-")
            if d and (best is None or len(d) < len(best)):
                best = d
        out += f"<path stroke='{short(pal[ch])}' d='{best}'/>"
    return out


def flip(a, b, t=""):
    """Two alternating frames (period --t, default .6s). A frame that is a single path carries the class
    itself; a multi-colour frame gets a group."""
    cls = lambda s, c: (s.replace("<path ", f"<path class='{c}' ") if s.count("<path ") == 1 and s.startswith("<path ")
                        else f"<g class='{c}'>{s}</g>")
    return f"<g{t and f' style={chr(39)}--t:{t}{chr(39)}'}>{cls(a, 'kk-f')}{cls(b, 'kk-f kk-g')}</g>"


def airship():
    """The big dirigible: a long cigar envelope with panel ribs and its name on the side, tail fins,
    engine pod and a windowed gondola. 96x27, nose to the right."""
    w, h = 96, 27
    g = [["."] * w for _ in range(h)]
    for y in range(20):
        for x in range(6, w):
            u, v = (x + .5 - 51) / 45, (y + .5 - 10) / 10
            if abs(u) ** 2.4 + v * v <= 1:
                g[y][x] = "r" if y == 15 else "WLMM"[(0 if v < -.35 else 1 if v < .3 else 2) + (x % 15 == 6)]
    x = 37
    for ch in "FREEDOM":                                     # 3x5 lettering along the flank
        for i, b in enumerate(FONT[ch]):
            if b == "1":
                g[7 + i // 3][x + i % 3] = "D"
        x += 4
    return art(["3:MM", "2:MMMM", "2:LLLLLL", "3:LLLLLL", "4:LLLLLL", "5:LLLL", "", "", "", "0:rrrrrrr", "0:rrrrrrr",
                "", "", "", "5:MMMM", "4:MMMMMM", "3:MMMMMM", "2:MMMMMM", "2:MMMM", "3:MM 30:DDDDD",
                "30:DDDDDDD 52:D 68:D", "31:DDDDD 50:DDDDDDDDDDDDDDDDDDDDD", "49:DDDDDDDDDDDDDDDDDDDDDDD",
                "49:DDyyDyyDyyDyyDyyDyyDDDD", "49:DDyyDyyDyyDyyDyyDyyDDD", "50:DDDDDDDDDDDDDDDDDDDD", "52:DDDDDDDDDDDDDDDD"],
               w, ["".join(r) for r in g])


def patch(cv, x0, y0, x1, y1):
    """A region of a Canvas as a nested PNG (unpainted = transparent): used to redraw static things over a
    sprite that must pass behind them."""
    cols = sorted({p for row in cv.px[y0:y1] for p in row[x0:x1]} - {UNPAINTED})
    chars = "abcdefghijklmnop"
    rows = ["".join("." if p == UNPAINTED else chars[cols.index(p)] for p in row[x0:x1]) for row in cv.px[y0:y1]]
    return img(rows, {chars[i]: "#%02x%02x%02x" % c for i, c in enumerate(cols)}, x0, y0)


def painter():
    """Ursula and her easel on a clear background, to draw over Tombo as he rides past behind them."""
    cv = Canvas(W, H)
    for rows, x in ((URSULA, UX), (EASEL, EX)):
        cv.paint(rows, PPAL, x, PY - len(rows))
    return patch(cv, UX, PY - len(EASEL), EX + 9, PY)


def tower_top():
    """The spire and roof of the clock tower, alone, for the airship and its mooring line to pass behind."""
    cv = Canvas(W, H)
    tower(cv, TX)
    return patch(cv, TX - 13, 33, TX + 14, AY + 31)   # down to the eaves, below the mooring line


# Kiki: r/R bow, shoes, radio; h/H hair; s/S skin; e eye; k/K/d dress; o/O satchel; c/C Jiji; w white;
# y/Y/z straw; b/B broom handle; g radio grille
PAL = {"r": "#dd2233", "R": "#aa1122", "h": "#332211", "H": "#553322", "s": "#ffddaa", "S": "#dd9977",
       "e": "#221111", "k": "#332255", "K": "#554488", "d": "#221133", "o": "#ffaa33", "O": "#cc7722",
       "c": "#111122", "C": "#333344", "w": "#ffffff", "y": "#eecc66", "Y": "#cc9944", "z": "#996622",
       "b": "#996633", "B": "#664422", "g": "#ccddee"}
KW, KH = 64, 36
KIKI = art([
    "43:rrr",
    "30:rrrrrr 41:rrrrrr",
    "29:rrrrrrrR 37:rrr 40:Rrrrrrrr",
    "29:rrrrrrRR 37:rrr 40:RRrrrrrr",
    "30:rrrrRR 37:RrR 41:RRrrrr",
    "31:RRRR 42:RRRR 36:hhhhhhh",
    "35:hHHhhhhhh",
    "34:hhHHhhhhhhh",
    "34:hhhhhhhhhhh",
    "34:hhhhhhhssss",
    "34:hhhhhhssssss 14:c 19:c",
    "34:hhhhhhssshsss 14:cc 18:cc",
    "35:hhhhhSsssss 13:cccccccc",
    "35:hhhhhssssS 13:cccccccc",
    "34:hhhhh 40:Ssss 13:cccccccc",
    "34:hhh 39:SSs 13:cccccccc",
    "36:kkkkkk 14:cccccc",
    "35:Kkkkkkkk 39:O 14:ccccc",
    "34:Kkkkkkkkkk 38:O 13:Ccccccc",
    "34:Kkkkkkkk 37:O 13:Cccccccc",
    "33:Kkkkkkkk 35:OO 29:oooo 2:yyyyyyy 13:cccccccc",
    "33:kkkkkkk 34:O 28:oooooO 0:yyyyyyyyyyy 13:cccccccc",
    "27:Kkkkk 32:kkkkkkkk 28:oooooO 1:yyYyyyyyyyy 13:cccccccc",
    "25:KKkkkkkkkkkkkkkk 28:ooOooO 0:yyyyYYyyyyyy 12:cccccccccc",
    "24:Kkkkkkkkkkkkkkkkkk 29:OOOO 0:yyyyyyyyyyyy 12:cccccccccc",
    "0:yYYyyyyyyyyyzbbbbbbbbbb 43:bbbbbbbbbbbbbbbbbbbb 23:Kkkkkkkkkkkkkkkkkkkk",
    "0:YyyyyYYYyyyyzBBBBBBBBBB 43:BBBBBBBBBBBBBBBBBBBB 23:kkkkkkkkkkkkkkkkkkkk",
    "0:YYYYyyyyYYYYz 23:kkkkkdkkkkkkdkkkkkk",
    "1:YYYYYYYYYYY 24:kkkkdkkkkkkdkkkkk",
    "0:zzYYYYYzzYY 25:dkkdkkkkkkdkkd",
    "2:zzzzzzz 27:ddddddddddd 38:ss",
    "38:ss 34:SS",
    "39:ss 34:SS",
    "39:ss 33:RRRR",
    "39:rrrr",
    "39:RRRRR",
], KW)
RADIO = art(["3:B", "3:B", "0:RRRRRRR", "0:rrrrrrr", "0:rgggrwr", "0:rgggrrr", "0:rgggrrr", "0:RRRRRRR"], 7)
part = lambda **rows: art([rows.get(f"r{i}", "") for i in range(KH)], KW)   # sparse overlay frame
BOW = part(r0="31:rrrr"), part(r2="28:r", r3="28:r", r4="29:R")
HAIR = part(r14="32:hh", r15="32:hh"), part(r12="33:hh", r13="32:hhh")
HEM = part(r28="21:ddd", r29="20:ddddd", r30="22:ddddd"), part(r26="20:ddd", r27="19:dddd", r28="21:ddd")
TAIL = (part(r16="10:cc", r17="9:cc", r18="8:cc", r19="8:cc", r20="8:cc", r21="9:cc", r22="10:cc"),
        part(r16="6:c", r17="6:cc", r18="6:cc", r19="7:cc", r20="8:cc", r21="9:cc", r22="10:cc"))
STRAW = part(r22="0:y", r28="0:Y", r30="1:z"), part(r20="1:y", r24="12:y", r30="9:z")
EYE = part(r10="43:e", r11="43:e")
# Her near arm is an overlay so that it can leave the broom: ARMD rests on the handle, WAVE is two frames
# of a raised wave (shown while Tombo is stopped below her).
ARMD = part(r19="43:Kkk", r20="44:Kkk", r21="45:Kkk", r22="46:Kkk", r23="48:ss", r24="48:ss")
WAVE = (part(r17="43:Kkkk", r16="45:Kkk", r15="46:Kkk", r14="47:Kkk", r13="49:ss", r12="49:ss"),
        part(r17="43:Kkkkk", r16="46:Kkk", r15="48:Kkk", r14="51:ss", r13="51:ss"))
CATEYE = part(r13="14:ww 18:ww", r14="14:w 18:w")
# Jiji glancing back along the broom: his eyes slide a pixel to the tail end (black paints out where they
# were) and the near ear tilts out
GLANCE = part(r11="13:c", r13="13:ww 15:c 17:ww 19:c", r14="13:wc 17:wc")
# Kiki's sprite sits at her left-hand, high station; her flight path (CSS) offsets it by up to 180px
# right and 40px down. High, her feet clear the clock face; low, she is just above the bay.
KX, KY = 44, 27

# airship: W/L/M hull tones, D lettering, gondola and engine pod, r stripe and tail flash, y windows
APAL = {"W": "#ffffff", "L": "#dfe6f2", "M": "#b4c0d8", "D": "#55607a", "r": "#dd2233", "y": "#ffdd88"}
AX, AY = -100, 25   # parked off the left edge; low enough to show in wide panes (top 25px cropped)
# gull: w body, g wings, d wingtips, o beak. Body is shared; the wings are two frames.
GPAL = {"w": "#ffffff", "b": "#aabbcc", "g": "#667788", "d": "#333344", "o": "#ffaa33"}
GULL = (art(["", "", "", "5:wwwww 10:o", "5:bbbb"], 14), art(["0:dd 12:dd", "1:ggg 10:ggg", "3:ggg 8:ggg"], 14),
        art(["", "", "", "3:gg", "1:gggg 9:gggg", "0:dd 12:dd"], 14))
# moored boats: w white, b blue stripe, D dark, r red, t teal hull, y cabin light
BPAL = {"w": "#ffffff", "b": "#335577", "D": "#222233", "r": "#dd2233", "t": "#33aa99", "y": "#ffdd88",
        "s": "#bbccdd"}
SAIL = art(["10:Drr", "10:D", "10:D", "10:D", "10:D", "10:D", "10:D", "10:D", "10:D", "10:D", "10:D",
            "10:Dwwwwwwww", "10:DDDDDDDDD", "4:wwwww 10:D", "4:wbwbw 10:D", "0:wwwwwwwwwwwwwwwwwwwww",
            "1:wwwwwwwwwwwwwwwwwww", "2:bbbbbbbbbbbbbbbbb", "4:DDDDDDDDDDDDD"], 21)
TUG = art(["8:D", "8:D", "8:Drr", "6:rrrrrr", "6:wyDyDw", "6:wwwwww", "0:tt 16:ttt", "0:ttttttttttttttttttt",
           "1:wwwwwwwwwwwwwwwww", "2:ttttttttttttttt", "3:DDDDDDDDDDDDD"], 19)
# Tombo on the propeller bicycle, facing left: h hair, s skin, g glasses, e shoe, w/r striped shirt, b shorts,
# D bike
TPAL = {"h": "#332211", "s": "#ffddaa", "e": "#221111", "w": "#ffffff", "r": "#dd2233", "b": "#445588",
        "D": "#222233", "g": "#aaddff"}
# Both wheels are the same 7x7 ring with a hub (columns 1-7 and 13-19), joined by one bar at hub height;
# the handlebar and saddle are single pixels above each wheel's top, so nothing thickens either ring.
WHEEL = ["2:DDD", "1:D 5:D", "0:D 6:D", "0:D 3:D 6:D", "0:D 6:D", "1:D 5:D", "2:DDD"]
shift = lambda tok, dx: " ".join(f"{int(t.split(':')[0]) + dx}:{t.split(':')[1]}" for t in tok.split())
TOMBO = art([
    "9:hhhh",
    "8:hhhhh",
    "8:gDshh",
    "8:ssss",
    "8:wwwww",
    "5:sss 8:rrrrr",
    "4:D 8:wwwww 16:D",
] + [f"{shift(w, 1)} {shift(w, 13)} {mid}" for w, mid in zip(WHEEL, ["9:bbb", "10:bb", "10:s", "8:DDDDD 10:s", "10:s",
                                                                    "10:e", ""])], 20)
# He stops at x 190-209: clear of the lamp posts (150, 214) and the shop awnings (his shirt is striped
# too), with the bollard at 198 between his wheels. The wheels stand on quay row 146: in front of the
# house fronts and lamp posts (feet on 145), behind the edge bollards (down to 147).
TX0, TY0 = 190, QUAY - 13
# The janitor's deck brush, two positions of a slow push along the gallery
BRUSH = art(["0:x", "0:x", "1:x", "1:x", "0:xxx"], 4), art(["0:x", "1:x", "1:x", "2:x", "1:xxx"], 4)
# Lily's tail: lying along the roof, then curled up
LX, LY = 100 + LILY[0], QUAY - 29 + LILY[1]
LTAIL = art(["", "", "", "", "", "6:ww"], 9), art(["", "", "", "7:w", "7:w", "6:w"], 9)
# the bakery's hanging sign: a pretzel (g gold, b its baked-brown underside)
PRETZEL = art(["3:B", "1:gg 4:gg", "0:g 3:g 6:g", "0:g 2:g 4:g 6:g", "1:b 5:b", "2:bbb"], 7)
PUFF = "h2v1h1v1h-1v1h-2v-1h-1v-1h1z"   # a 4x3 puff, rounded
WISP = art(["10:wwwwww", "7:wwwwwwwwwwww 22:www", "4:wwwwwwwwwwwwwwwwwwwwwwwww", "2:wwwwwwwwwwwwwwwwwwwwwwwwwwwwwww",
            "0:wwwwwwww 8:sssssssssssssssssssssssssss", "3:sssssssssssssssssssssssssss", "8:ssssssssssssss"], 36)
CX, CY = CLOCK[0] + .5, CLOCK[1] + .5


def dashes(pts):
    """[(x, y, n)] -> path data for 1px-high dashes, relative moves after the first."""
    d, px, py = "", 0, 0
    for x, y, n in pts:
        d += (f"M{x} {y}.5" if not d else f"m{x - px} {y - py}") + f"h{n}"
        px, py = x + n, y
    return d.replace(" -", "-")


# Sea glints: three groups twinkling out of step. Every dash is on open water at least 2px clear of the
# boats' bob envelopes (sailboat x 8-28 y 122-141, tug x 40-58 y 135-146), the pier and the shore.
# (Two groups, not three: the third's dashes were shared out to pay for the new sprites.)
GLINTS = [("3.4s", "", [(12, 117, 4), (37, 118, 3), (66, 128, 4), (32, 135, 5), (3, 147, 6), (28, 148, 7), (116, 159, 8),
                        (213, 160, 8)]),
          ("5.8s", "-3s", [(3, 119, 3), (56, 117, 4), (48, 118, 4), (64, 123, 4), (2, 151, 6), (36, 152, 5), (131, 159, 8)])]
# Sun sparkle: two sets of dots in rows 115-118, below the steamer's lane and above the dinghy's
# (four short dashes per set rather than six dots: the dots read as a field of specks)
SPARKLE = ([(20, 115, 3), (31, 116, 2), (25, 117, 3), (33, 118, 2)],
           [(26, 115, 2), (21, 116, 2), (30, 117, 2), (24, 118, 3)])
# The steamer crawling along the horizon, bow to the right: s smoke, r funnel, w cabin, d hull. It ends
# its run hidden behind the tree and chimney at x 100-108, which are redrawn over it (STEAM_END).
STEAMER = art(["0:sss", "3:r", "2:wwww", "0:ddddddd"], 7)
STEAM_Y, STEAM_END = 109, 102
# The dinghy that tacks across the bay (w sail, D mast, r hull), bow to the right. Its lane is x<60, y 122-130.
DINGHY = art(["4:D", "3:wD", "2:wwDw", "2:wwDww", "1:wwwDww", "1:wwwDwww", "4:D", "0:rrrrrrrrr", "1:rrrrrrr"], 9)
DX, DY = 50, 122    # where it turns round
# Tombo in the air, further off and so smaller, bow to the right (the group is mirrored to fly left):
# h hair, s skin, g glasses, w/r striped shirt, b shorts, D bike
# Both wheels are the same 5x5 ring (columns 0-4 and 8-12), joined by one bar; nubs for saddle and handlebar.
SKYTOMBO = art(["4:hhh", "4:hhsg", "3:wwwws", "3:rrrr 8:s", "2:D 3:wwww 10:D", "1:DDD 5:bb 9:DDD", "0:D 4:D 6:s 8:D 12:D",
                "0:D 4:DDDDD 12:D", "0:D 4:D 8:D 12:D", "1:DDD 9:DDD"], 13)
SX, SY = -16, 36
# The pacifier mother (Kiki's first delivery) pushing her pram out of the bakery door and along the quay
# to her own door (the teal house, 233-235), facing right: h hair, s skin, c coat, l stockings, e shoes, H pram hood, P pram body, w trim, D frame
MPAL = {"h": "#553322", "s": "#f3c7a9", "c": "#7d6aa8", "l": "#ddccbb", "e": "#221111", "H": "#33456b",
        "P": "#4a5f8a", "w": "#ffffff", "D": "#222233"}
MOTHER = ["..hh...........", ".hhhh..........", ".hsss..........", ".hss...........", "..s............",
          ".cccc.D..HHH...", "cccccsDHHHHH...", ".cccc..HHHHPPPP", ".cccc..PPPPPPPP", ".cccc..wwwwwwww",
          "cccccc..PPPPPP.", "...l.....D...D.", "...e....DDD.DDD"]
MX = 121           # in front of the bakery door

k = lambda a: runs(a, PAL, KX, KY)
gull = lambda i, x, y, d: (f"<g id='kk-u'>{runs(GULL[0], GPAL, 0, 0)}"
                           f"{flip(runs(GULL[1], GPAL, 0, 0), runs(GULL[2], GPAL, 0, 0), '.5s')}</g>" if i == 0 else
                           f"<use href='#kk-u' x='{x}' y='{y}' style='--d:{d}s'/>")
# spinning propeller: the hub is static and the blade blinks over it (the same two frames as a flip, one
# animated element instead of two)
prop = lambda x, y: f"<path d='M{x}.5 {y + 3}v1'/><path class='kk-f' style='--t:.24s' d='M{x}.5 {y}v7'/>"
# Depth order, back to front. Water-surface effects come first so that everything else draws over them.
# Times in the comments are loop times; the 120 s rules all start 20 s in (PH) so that the scene opens
# with Kiki mid-screen rather than low on the left.
SPRITES = (
    # sea glints
    "<g stroke='#cef'>"
    + "".join(f"<path class='kk-f' style='--t:{t}{d and ';--d:' + d}' d='{dashes(pts)}'/>" for t, d, pts in GLINTS)
    # sun sparkle near the horizon
    + f"<path class='kk-f' style='--t:1.9s' stroke='#fff' d='{dashes(SPARKLE[0])}'/>"
      f"<path class='kk-f kk-g' style='--t:2.7s' stroke='#fff' d='{dashes(SPARKLE[1])}'/></g>"
    # the far steamer, then the tree and chimney it disappears behind
    + f"<g class='kk-t' style='--x:110px;--t:150s;--n:110'>{runs(STEAMER, {'s': '#bbccdd', 'r': '#dd2233', 'w': '#ffffff', 'd': '#334455'}, STEAM_END - 110, STEAM_Y)}</g>"
    + patch(draw(), 100, 108, 109, 113)
    # a cloud wisp drifting slowly across, high up
    + f"<g class='kk-t' style='--x:-420px;--t:520s;--n:420;--d:-150s'>{runs(WISP, {'w': '#ffffff', 's': '#ddeeff'}, 330, 4)}</g>"
    # clock hands: they start at ten past ten and then run at true speed, one tick a minute
    + f"<g stroke='#124'><path class='kk-c' d='M{CX} {CY}v-5'/>"
    f"<path class='kk-c' style='--t:43200s;--d:-36600s' d='M{CX} {CY}v-3'/></g>"
    # the belfry bell, swinging while Kiki passes over the tower (kk-i)
    + f"<path class='kk-i' stroke='{GOLD}' d='M{TX - 1}.5 62v2'/>"
    # the janitor's deck brush, pushed to and fro a pixel (one element, kk-r)
    + f"<g class='kk-r' style='--t:1.3s'>{runs(BRUSH[0], {'x': '#553322'}, JX + 6, 61)}</g>"
    # lighthouse and pier beacon, one path blinking together
    + f"<path class='kk-f' style='--t:4s' stroke='#ff8' d='M57 98.5h2M63 {QUAY - 8}.5h3'/>"
    # the dirigible crosses left to right, 80-150 s, behind the clock tower: its spire and roof are redrawn
    # over it
    + f"<g class='kk-t' style='--x:720px;--t:120s;--n:720;--d:-60s'>{img(airship(), APAL, AX, AY)}"
      # its mooring line trailing from under the nose
      f"<path stroke='#55607a' d='M{AX + 86}.5 {AY + 17}v2m-1 0v2m-1 0v2m-1 0v2m-1 0v1m-1 0v2m-1 0v1m-1 0v1m-1 0v1'/></g>"
    + tower_top()
    # gulls: a flock crossing right to left high up, 33-74 s, after the dirigible has gone (it used to fly
    # through its envelope)
    + "<g transform='matrix(-1 0 0 1 320 0)'><g class='kk-t' style='--x:1100px;--y:16px;--t:120s;--n:1100;--d:-110s'>"
      "<g transform='translate(-40 12)'>"
    + "".join(gull(i, x, y, d) for i, (x, y, d) in enumerate([(0, 0, 0), (-16, 6, -.2), (-9, 13, -.35), (-31, 9, -.1)]))
    + "</g></g>"
    # Tombo in the air, 74-110 s: once he has taken off from the quay he comes back across the sky behind
    # Kiki, further away and so smaller
      f"<g class='kk-t' style='--x:1130px;--t:120s;--n:1130;--d:-65.6s'>{img(SKYTOMBO, TPAL, SX, SY)}"
      f"<g stroke='#99a'>{prop(SX + 13, SY + 3)}</g></g></g>"
    # the dinghy tacking across the bay, behind the moored boats: in 60-108 s, about at 113 s, out again
    # Its wake trails off the stern, the outer dash coming and going. kk-v mirrors about the group's box, so
    # an unstroked point as far right of the hull's centre (54.5) as the wake reaches left keeps that centre.
    + f"<g class='kk-j' style='--p:-80s'><g class='kk-v'>{runs(DINGHY, {'w': '#ffffff', 'D': '#222233', 'r': '#dd2233'}, DX, DY)}"
      f"<path stroke='#def' d='M{DX - 4} {DY + 8}.5h3'/><path class='kk-f' style='--t:1.3s' stroke='#def' d='M{DX - 8} {DY + 9}.5h3'/>"
      f"<path d='M{DX + 16} {DY + 9}h1'/></g></g>"
    # moored boats, bobbing out of step
    + f"<g class='kk-b'>{img(SAIL, BPAL, 8, 122)}</g><g class='kk-b' style='--d:-1.3s'>{img(TUG, BPAL, 40, 135)}</g>"
    # chimney smoke over the bakery: two pale wisps that leave the chimney mouth small and swell as they fade
    + "".join(f"<path class='kk-p'{d and f' style={chr(39)}--d:{d}{chr(39)}'} fill='#b4bfd3' d='M106 100{PUFF}'/>"
              for d in ("", "-3.75s"))
    # Lily's tail
    + flip(runs(LTAIL[0], {"w": "#ffffff"}, LX, LY), runs(LTAIL[1], {"w": "#ffffff"}, LX, LY), "3.1s")
    # a glint sweeping across the right pane of the bakery's shop window now and then (kk-L)
    + "<path class='kk-L' stroke='#fff' d='M112 141.5h1m0-1h1m0-1h1m0 3h1m0-1h1m0-1h1'/>"
    # the pretzel sign, swaying on its bracket
    + f"<g class='kk-r'>{runs(PRETZEL, {'g': '#ffcc44', 'b': '#bb7733', 'B': '#112244'}, 92, QUAY - 16)}</g>"
    # the baker lifting a loaf to his chest and lowering it
    + "<g stroke='#c84'>" + flip(f"<path d='M{FX + 3} {QUAY - 7}.5h3m-3 1h3'/>", f"<path d='M{FX + 3} {QUAY - 10}.5h3m-3 1h3'/>", "5s") + "</g>"
    # Ursula's crows on the house side of the pavement: one pecks (head up, head down), one hops up with a
    # flap now and then and settles back
    + "<g stroke='#223'>"
    + flip(f"<path d='M{CROWX} {QUAY - 4}.5h2'/>", f"<path d='M{CROWX - 1} {QUAY - 2}.5h2'/>", "1.7s")
    + f"<g class='kk-n'><path d='M{HOPX} {QUAY - 4}.5h2m-1 1h3m-3 1h4m-3 1h1'/>"
      f"<path class='kk-z' style='animation-duration:11s;animation-delay:0s' d='M{HOPX - 2} {QUAY - 5}.5h3m2 0h3'/></g></g>"
    # the pacifier mother: out of the bakery door at 108 s, along the quay and in at her own door at 8.8 s
    # (kk-M), her trailing leg stepping (kk-f)
    + f"<g class='kk-M'>{img(MOTHER, MPAL, MX, QUAY - 13)}<g class='kk-f' style='--t:.5s'>"
      f"<path stroke='#dcb' d='M{MX + 1}.5 {QUAY - 2}v1'/><path stroke='#211' d='M{MX + 1}.5 {QUAY - 1}v1'/></g></g>"
    # Tombo on the quay: rides in from 35 s, stops and turns 52-54 s, and on the way out the propeller
    # lifts him off at 56 s; he climbs away and is gone by 70 s (kk-h; his shadow stays on the quay)
    + f"<g class='kk-q'><path stroke='#ba8' d='M{TX0 + 3} {QUAY}.5h14'/><g class='kk-h'><g class='kk-v'>{img(TOMBO, TPAL, TX0, TY0)}"
      f"<g stroke='#99a'>{prop(TX0, TY0 + 5)}</g></g></g></g>"
    # Nearer than Tombo, so drawn over him: the bollards on the quay edge with a crow perched on the one at
    # 262, then Ursula at her easel
    + f"<path stroke='#124' stroke-width='3' stroke-dasharray='2 30' d='M134 {QUAY}.5h188'/>"
    + f"<path stroke='#223' d='M260 {QUAY - 5}.5h2m-1 1h3m-3 1h4m-3 1h1'/>"
    + painter()
    # Ursula's brush arm dabbing at the canvas, plus her brush: the dab lifts the brush tip three rows up the
    # canvas edge.
    + f"<g stroke='{SKIN}'>"
    + flip(f"<path d='M{UX + 5} {PY - 9}.5h3'/><path stroke='#732' d='M{UX + 8} {PY - 9}.5h2'/>",
           f"<path d='M{UX + 5} {PY - 9}.5h1m0-1h1m0-1h1'/><path stroke='#732' d='M{UX + 8} {PY - 12}.5h2'/>", "1.2s")
    # Osono waves only while Kiki is low and near, 0-20 and 100-120 s (kk-W): a pink sleeve out from her
    # shoulder, then the forearm and a hand two pixels clear of her hair, the hand rocking a pixel (kk-r)
    + f"<g class='kk-W'><path stroke='{PINK}' d='M{OX - 1} {QUAY - 9}.5h2'/><path d='M{OX - 2}.5 {QUAY - 10}v1'/>"
      f"<path class='kk-r' style='--t:.6s' d='M{OX - 2}.5 {QUAY - 11}v1'/></g></g>"
    # Kiki: flight path across (kk-x) and up and down (kk-w), mirrored when she flies left (kk-m), bob (kk-y)
    + "<g class='kk-x'><g class='kk-w'><g class='kk-m'><g class='kk-y'>"
    + img(KIKI, PAL, KX, KY)
    + flip(k(BOW[0]), k(BOW[1]), ".5s") + flip(k(HAIR[0]), k(HAIR[1]), ".7s") + flip(k(HEM[0]), k(HEM[1]))
    + flip(k(TAIL[0]), k(TAIL[1]), "2.6s") + flip(k(STRAW[0]), k(STRAW[1]), ".4s")
    + f"<g class='kk-k'>{k(EYE)}</g><g class='kk-k' style='--t:3.7s'>{k(CATEYE)}</g>"
    + f"<g class='kk-l'>{k(GLANCE)}</g>"
    + f"<g class='kk-a'>{k(ARMD)}</g><g class='kk-z'>{flip(k(WAVE[0]), k(WAVE[1]), '.8s')}</g>"
    + f"<g class='kk-r'>{runs(RADIO, PAL, KX + 55, KY + 27)}</g>"
    + "</g></g></g></g>"
)
PH = "-20s"
CSS = (
    ".kk-t{animation:kk-t var(--t) var(--d,0s) steps(var(--n)) infinite}@keyframes kk-t{to{translate:var(--x) var(--y,0)}}"
    ".kk-c{transform-origin:" f"{CX}px {CY}px" ";animation:kk-c var(--t,3600s) var(--d,-600s) steps(60) infinite}@keyframes kk-c{to{rotate:1turn}}"
    # Kiki's flight path over the 120 s loop, in whole pixels (every moving leg is 60px across or 40px
    # up or down): 0-26 s she climbs out of the harbour heading right, 26-43 s crosses over the town above
    # the clock face, 43-56 s hovers on the right and turns (50 s), 56-73 s flies back, 73-103 s dives
    # to the harbour, 103-120 s hovers low and turns (112 s)
    f".kk-x{{animation:kk-x 120s {PH} steps(60) infinite}}"
    "@keyframes kk-x{22%,61%{translate:60px}29%,54%{translate:120px}36%,47%{translate:180px}86%{translate:0}}"
    f".kk-w{{animation:kk-w 120s {PH} steps(40) infinite}}"
    "@keyframes kk-w{0%,86%,to{translate:0 40px}22%,61%{translate:0 0}}"
    f".kk-m{{transform-origin:{KX + 32}px 0;animation:kk-m 120s {PH} steps(1) infinite}}"
    "@keyframes kk-m{42%{scale:-1 1}93%{scale:1}}"
    ".kk-y{animation:kk-y 2.8s steps(3) infinite alternate}@keyframes kk-y{to{translate:0 3px}}"
    ".kk-f{animation:kk-o var(--t,.6s) var(--d,0s) steps(1) infinite}.kk-g{animation-delay:calc(var(--d,0s) - var(--t,.6s)/2)}"
    "@keyframes kk-o{50%{opacity:0}}"
    # Kiki's wave to Tombo, 50-56 s: the resting arm hides and the waving one shows
    f".kk-a,.kk-z{{animation:kk-a 120s {PH} steps(1) infinite}}.kk-z{{opacity:0;animation-name:kk-z}}"
    "@keyframes kk-a{42%{opacity:0}47%{opacity:1}}@keyframes kk-z{42%{opacity:1}47%{opacity:0}}"
    ".kk-k{animation:kk-k var(--t,5.3s) steps(1) infinite}@keyframes kk-k{96%{opacity:0}}"
    # a two-position rock, a pixel to the left and back, each held for --t (pretzel sign, radio, brush, Osono's hand)
    ".kk-r{animation:kk-r var(--t,1.4s) steps(2) infinite alternate}@keyframes kk-r{from{translate:-1px}to{translate:1px}}"
    # smoke: each wisp leaves the chimney mouth small, then drifts up and left, swelling as it fades
    ".kk-p{opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:kk-p 7.5s var(--d,0s) steps(25) infinite}"
    "@keyframes kk-p{from{scale:.5}12%{opacity:.75}to{translate:-12px -22px;scale:2}}"
    # Jiji's glance: hidden, then shown for the last 15% of an 11 s cycle
    ".kk-l{opacity:0;animation:kk-l 11s 4s steps(1) infinite}@keyframes kk-l{85%{opacity:1}}"
    # the shop-window glint, every 19 s: three positions a pixel apart over about 0.8 s
    ".kk-L{opacity:0;animation:kk-L 19s 7s steps(1) infinite}@keyframes kk-L{96%{opacity:1}97.4%{translate:1px}98.7%{translate:2px}}"
    # the bell swings for about 7 s each time Kiki crosses the tower (33-40 s and 63-70 s): +1, 0, -1, 0 ...
    f".kk-i{{animation:kk-i 120s {PH} steps(1) infinite}}@keyframes kk-i{{"
    + "".join(",".join(f"{s + .5 * i:g}%" for s in (27.5, 52.5) for i in range(12) if i % m == j) + f"{{translate:{v}}}"
              for m, j, v in ((4, 0, "1px"), (4, 2, "-1px"), (2, 1, "0")))
    + "}"
    # the pram mother: 108 s out of the bakery door, 5px/s along the quay, 8.8 s in at her own door (104px on),
    # hidden in between
    f".kk-M{{animation:kk-M 120s {PH} infinite}}@keyframes kk-M{{from{{translate:60px;animation-timing-function:steps(44)}}"
    "7.32%{translate:104px;opacity:1;animation-timing-function:steps(1)}7.33%,90%{translate:104px;opacity:0;"
    "animation-timing-function:steps(1)}90.1%{translate:0;opacity:1;animation-timing-function:steps(60)}to{translate:60px}}"
    # Osono's wave: shown 0-20 s and 100-120 s, while Kiki is low over the harbour near her
    f".kk-W{{animation:kk-W 120s {PH} steps(1) infinite}}@keyframes kk-W{{16.7%{{opacity:0}}83.3%{{opacity:1}}}}"
    ".kk-b{animation:kk-b 3.2s var(--d,0s) steps(1) infinite}@keyframes kk-b{50%{translate:0 1px}}"
    # the hopping crow: up 8px, a beat at the top with wings out (kk-z on an 11 s period), down again
    ".kk-n{animation:kk-n 11s steps(8) infinite}@keyframes kk-n{39%,50%{translate:0}42%,47%{translate:0 -8px}}"
    f".kk-h{{animation:kk-h 120s {PH} steps(22) infinite}}@keyframes kk-h{{47%{{translate:0}}58%,to{{translate:0 -22px}}}}"
    f".kk-q{{animation:kk-q 120s {PH} steps(190) infinite}}@keyframes kk-q{{0%,23%,65%,to{{translate:190px}}43%,45%{{translate:0}}}}"
    # out-and-back for the dinghy; kk-v (shared with Tombo) mirrors whatever is turning round at 44%
    f".kk-j{{animation:kk-j 120s var(--p) steps(70) infinite}}@keyframes kk-j{{0%,to{{translate:-70px}}40%,48%{{translate:0}}}}"
    f".kk-v{{transform-box:fill-box;transform-origin:center;animation:kk-v 120s var(--p,{PH}) steps(1) infinite}}@keyframes kk-v{{44%,to{{scale:-1 1}}}}"
)
