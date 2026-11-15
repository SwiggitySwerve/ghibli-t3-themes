"""Howl's Moving Castle: the castle treads on its chicken legs at the edge of the alpine lake,
chimney puffing, while Sophie and Calcifer watch from the flower meadow and Turnip Head hops past.

Static layer (PNG, 19 colours): sky, cumulus, snowy peaks, lake, meadow + flower carpet, Sophie, Calcifer.
Sprites (SVG), back to front: two drifting cloud wisps, chimney smoke, legs, the castle body (a second
small transparent PNG, so the whole heap can dip with each footfall and hide the smoke and leg tops),
Calcifer's flickering flame tongue, lake glints, Turnip Head.

Keyframes use the individual `translate` / `scale` properties (same compositor path as `transform`,
about 60 characters shorter over the scene).
"""
import base64, math, struct, zlib
from lib import Canvas, W, H, UNPAINTED

NAME = "Howl's Moving Castle"
COLORS = 32   # 19 are used. Past 16 Pillow writes 8-bit indices, which deflate far better than 4-bit packing

SK = ["#3f7fd0", "#5f9fe2", "#8cc2ef", "#bfe2f6"]
WHT, CLM, CLS = "#ffffff", "#e3edf8", "#b4c8e6"
MT1, MT2, LAK, LK2 = "#7d9bcb", "#4f6fae", "#4fb9c4", "#3ea3b9"
G1, G2, G3, PNK = "#8fd062", "#58ad48", "#2f7d3e", "#f7a1c4"
RED, YEL, SKN, DRK = "#f96a4c", "#ffd85e", "#f7cfa6", "#2a2740"   # RED: poppies, hat ribbon, Calcifer
HZ = 70            # far shore row
CX, CY = 60, 24    # castle image top-left
SX, SY = 145, 90   # Sophie top-left


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


def cloud(cv, circles, base):
    """Daylight cumulus: white lumps painted back to front, each with a pale crescent of shade on its
    lower right, over a flat two-tone base."""
    for cx, cy, r in circles:
        for y in range(int(cy - r), min(base, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + .5 - cx, y + .5 - cy
                d = math.hypot(dx, dy)
                if d <= r:
                    shade = d > r - 4 and .6 * dx + .8 * dy > .45 * r
                    cv.set(x, y, CLS if base - y <= 2 else CLM if shade or base - y <= 5 else WHT)


def ell(cv, cx, cy, rx, ry, shade):
    """Filled ellipse; shade(dx/rx, dy/ry) -> colour."""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            u, v = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            if u * u + v * v <= 1:
                cv.set(x, y, shade(u, v))


def peak(cv, cx, top, sl, sr, lit, shade, snow):
    """Peak with a lit left face, shaded right face and a zigzag snow cap. Rows come in identical
    pairs (k is even), which halves what the slopes cost."""
    for y in range(top, HZ):
        k = (y - top) // 2 * 2
        mid = cx + k // 4
        for x in range(int(cx - k * sl), int(cx + k * sr) + 1):
            cap = k < snow + (2 if (x // 2) % 2 else 0)
            cv.set(x, y, (WHT if x < mid else CLM) if cap else (lit if x < mid else shade))


def ground(x):
    """Top row of the meadow: a hillock under the castle that dips to the lakeshore on the right."""
    if x < 126:
        return 88 - (x < 40) - (x < 18)
    return min(100, 88 + (x - 126) * 3 // 8) + (x > 200)


SOPHIE = [
    "....yyyyy....",
    "...yyyyyyy...",
    "...ppppppp...",
    "yyyyyyyyyyyyy",
    "..hhssssshh..",
    "..hskssksh...",
    "..hhsssssh...",
    "...hhssshh...",
    "...hwwwwwh...",
    "...bbbbbbb...",
    "..bbbbbbbbb..",
    "..sbbbbbbbs..",
    "..sbbbbbbbs..",
    "...bbbbbbd...",
    "...bbbbbbd...",
    "..bbbbbbbdd..",
    "..bbbbbbbdd..",
    "..bbbbbbbdd..",
    ".bbbbbbbbbdd.",
    ".bbbbbbbbbdd.",
    ".bbbbbbbbbdd.",
    "bbbbbbbbbbbdd",
    "....k...k....",
]
SPAL = {"y": YEL, "p": RED, "h": CLM, "s": SKN, "b": SK[0], "d": MT2, "w": WHT, "k": DRK}
FIRE = ["....o....", "...oo....", "..ooo.o..", "..ooooo..", ".ooyyyoo.", ".oyyyyyo.", "oowwywwoo", "oodwydwoo",
        ".oyyyyyo.", ".ooydyoo.", "..ooooo.."]
FPAL = {"o": RED, "y": YEL, "w": WHT, "d": DRK}
FX, FY = 133, 91   # Calcifer top-left


def draw():
    cv = Canvas()
    bands(cv, 0, [(14, SK[0]), (34, SK[1]), (54, SK[2]), (HZ, SK[3])])
    # cumulus: a big tower behind the castle, a smaller one boiling up behind the right-hand peaks
    cloud(cv, [(100, 46, 24), (104, 25, 14), (86, 34, 13), (122, 35, 13), (68, 48, 14), (140, 50, 14),
               (52, 60, 9), (157, 61, 8)], HZ - 1)
    cloud(cv, [(206, 31, 10), (222, 40, 13), (192, 45, 8)], HZ - 1)
    # snowy peaks: a hazy far one, then the near range
    peak(cv, 170, 46, 1.5, 1.3, CLS, MT1, 4)
    peak(cv, 22, 48, 1.4, 1.5, CLS, MT1, 4)
    peak(cv, 198, 36, 1.1, 1.2, MT1, MT2, 8)
    peak(cv, 228, 46, 1.2, 1.0, MT1, MT2, 6)
    # far shore, lake with a pale band and a few glints
    cv.rect(0, HZ - 1, W, 2, G3)
    cv.rect(0, HZ + 1, W, 40, LAK)
    for y in range(86, 104):       # deeper water toward the near shore, one dithered row between
        for x in range(W):
            if y > 86 or (x + y) % 2:
                cv.set(x, y, LK2)
    for x in range(0, W, 4):
        cv.rect(x, HZ + 2, 3, 1, SK[3])
        cv.rect(x + 2, HZ + 4, 2, 1, SK[3])
    cv.rect(186, 74, 22, 1, MT1)
    cv.rect(190, 76, 14, 1, MT1)
    cv.rect(146, 79, 9, 1, SK[3])
    # meadow: light crest, mid green, and a flower carpet. Flowers sit only on every third row, each
    # row the same 36px motif at a different even offset: periodic rows cost ~6 chars each, however dense
    motif = {0: RED, 7: WHT, 13: G3, 18: YEL, 26: WHT, 31: PNK}
    for x in range(W):
        g = ground(x)
        cv.rect(x, g, 1, 2, G1)
        for y in range(g + 2, H):
            cv.set(x, y, motif.get((x + y // 3 * 10 + y // 9 * 4) % 36, G2) if y % 3 == 0 and y > g + 3 else G2)
    # a few bigger blooms up front for depth
    for x, y, c in [(20, 107, WHT), (88, 110, PNK), (119, 104, WHT), (186, 108, PNK), (216, 111, WHT)]:
        cv.paint([".p.", "pyp", ".p.", ".g."], {"p": c, "y": YEL, "g": G3}, x, y)
    cv.paint(SOPHIE, SPAL, SX, SY)
    cv.paint(FIRE, FPAL, FX, FY)
    return cv


# ---- the castle body: its own small PNG so it can bob as one piece ----
K, D, B, L = "#2e2836", "#54464a", "#7b6657", "#a48d70"
M, N, T, T2 = "#8794a0", "#b9c4cc", "#4f9a8c", "#2f6e68"
R, C, P, U = "#b8553f", "#ecdcb4", "#e8707a", "#9c6a42"
CW, CH = 70, 56


def castle():
    cv = Canvas(CW, CH)
    hull = lambda u, v: L if v < -.55 and u < .4 else (D if v > .5 or (v > .15 and u < -.7) else B)
    # chimneys
    for x, y, w in [(9, 9, 3), (33, 0, 4), (48, 11, 3)]:
        cv.rect(x, y, w, 20, K)
        cv.rect(x - 1, y, w + 2, 2, D)
    # rear house on a strut
    cv.rect(1, 30, 9, 8, C)
    cv.rect(1, 36, 9, 2, L)
    for i in range(4):
        cv.rect(i, 29 - i, 12 - 2 * i, 1, T if i else T2)
    cv.rect(4, 32, 2, 3, K)
    cv.rect(3, 38, 1, 4, K)
    # cottage, copper dome, tower
    cv.rect(14, 15, 10, 11, C)
    cv.rect(22, 15, 2, 11, L)
    for i in range(6):
        cv.rect(12 + i, 14 - i, 14 - 2 * i, 1, R)
    cv.rect(16, 17, 2, 3, YEL)
    cv.rect(20, 17, 2, 3, K)
    ell(cv, 31, 21, 9, 9, lambda u, v: N if -.7 < u < -.4 and v < .1 else (T if u < .3 else T2))
    cv.rect(41, 11, 5, 16, N)
    cv.rect(44, 11, 2, 16, M)
    for i in range(7):
        cv.rect(39 + (i + 1) // 2, 10 - i, 9 - 2 * ((i + 1) // 2), 1, T if i < 6 else T2)
    cv.rect(42, 14, 2, 2, K)
    cv.rect(50, 20, 7, 8, C)       # a hut wedged between the eye turrets
    for i in range(4):
        cv.rect(49 + i, 19 - i, 9 - 2 * i, 1, R)
    cv.rect(52, 22, 2, 2, K)
    # hull and head
    ell(cv, 32, 38, 25, 16, hull)
    ell(cv, 51, 37, 15, 13, hull)
    # plating seams, patches, portholes, door, fin
    for x, y, n in [(11, 31, 22), (8, 39, 28), (14, 46, 26)]:
        cv.rect(x, y, n, 1, D)
    cv.rect(22, 31, 1, 8, D)
    cv.rect(30, 39, 1, 7, D)
    cv.rect(13, 33, 7, 4, L)
    cv.rect(23, 41, 6, 4, U)
    cv.rect(32, 31, 5, 5, M)
    cv.rect(33, 32, 3, 3, YEL)
    cv.rect(10, 41, 2, 2, YEL)
    cv.rect(18, 41, 3, 5, K)
    for i in range(5):
        cv.rect(3 + i, 42 + i, 9 - i, 1, N if i < 2 else M)
    # jaw, mouth with grille, tongue
    ell(cv, 54, 46, 13, 6, lambda u, v: N if v < -.1 else M)
    cv.rect(43, 40, 24, 4, K)
    for x in range(44, 66, 3):
        cv.rect(x, 40, 1, 3, N)
    cv.rect(55, 42, 5, 8, P)
    cv.rect(56, 50, 3, 1, P)
    cv.rect(57, 43, 1, 5, R)
    # eyes: domed turrets with cannons
    for ex, ey in [(45, 29), (59, 31)]:
        ell(cv, ex, ey, 5, 5, lambda u, v: N if u + v < -.3 else M)
        cv.rect(ex - 1, ey - 1, 3, 3, K)
        cv.rect(ex + 2, ey - 1, 6, 2, K)
    return cv


def png(cv):
    """Canvas -> base64 8-bit palette PNG, unpainted key colour transparent (index 0). One byte per
    pixel deflates ~15% smaller than 4-bit packing here, and Pillow can't write the 1-byte tRNS."""
    cols = [UNPAINTED] + sorted({p for row in cv.px for p in row if p != UNPAINTED})
    raw = b"".join(b"\0" + bytes(cols.index(p) for p in row) for row in cv.px)
    idat = min((c.compress(raw) + c.flush() for c in
                (zlib.compressobj(9, 8, wb, 9, st) for wb in (15, 12, 10, 9) for st in (0, 1))), key=len)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return base64.b64encode(
        b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 3, 0, 0, 0))
        + ch(b"PLTE", bytes(x for c in cols for x in c)) + ch(b"tRNS", b"\0") + ch(b"IDAT", idat) + ch(b"IEND", b"")).decode()


LEG = "v10h-1v2h-1v3h1v3h1v3h1v3h4m-7 0h3"   # hip, hock bent back, shin, toes: stroked 2px wide
leg = lambda x: f"M{CX + x} {CY + 44}{LEG}"
PUFF = "h2v1h1v2h-1v1h-2v-1h-1v-2h1z"   # 4x4, starts fully hidden behind the 4px stack
TX, TY = -300, 96  # Turnip Head, parked off-canvas to the left

SPRITES = (
    # two cloud wisps drifting through (parked off-canvas; they borrow Turnip Head's keyframes)
    "<path class='hw-d' fill='snow' d='M-60 21h26v-1h-5v-1h-4v-1h-5v-1h-6v1h-3v1h-3zm-420 8h18v-1h-4v-1h-4v-1h-5v1h-3v1h-2z'/>"
    # chimney smoke (starts hidden behind the stack, one puff per footfall), legs, then the castle body over both
    f"<path class='hw-s' d='M{CX + 34} {CY + 2}{PUFF}'/><path class='hw-s hw-m' d='M{CX + 34} {CY + 2}{PUFF}'/>"
    f"<path class='hw-l' d='{leg(19)}{leg(53)}'/><path class='hw-l hw-m' d='{leg(28)}{leg(44)}'/>"
    f"<image class='hw-b' x='{CX}' y='{CY}' width='{CW}' height='{CH}' href='data:image/png;base64,{png(castle())}'/>"
    # Calcifer's body is in the PNG; a second flame tongue flickers over it
    f"<path class='hw-o' stroke='#f96a4c' d='M{FX + 6} {FY}.5h1m-2 1h2'/>"
    # lake glints that fade in and out
    "<path class='hw-g' stroke='snow' d='M158 82.5h7m22 5h9m18 5h5m-189-8h6'/>"
    # Turnip Head: crossbar + pole, turnip with its nose, bow tie, then hat + eye + coat as one dark path
    f"<g class='hw-t'><g class='hw-j'><path fill='peru' d='M{TX - 1} {TY + 9}h15v1h-15zm7 5h1v7h-1z'/>"
    f"<path fill='snow' d='M{TX + 4} {TY + 4}h5v2h2v1h-3v1h-3v-1h-1z'/><path fill='red' d='M{TX + 5} {TY + 8}h3v1h-3z'/>"
    f"<path fill='#234' d='M{TX + 4} {TY}h5v3h2v1h-9v-1h2zm3 5h1v1h-1z"
    f"M{TX + 1} {TY + 9}h11v3h-1v-1h-1v5h-2v-1h-1v-1h-1v1h-1v1h-2v-5h-1v1h-1z'/></g></g>"
)
CSS = (
    # the body dips 1px as each pair of feet lands; legs lift in four phases (0, -2, -4, -2 px)
    ".hw-b{animation:hw-b .9s -.45s steps(1) infinite}@keyframes hw-b{50%{translate:0 1px}}"
    ".hw-l{fill:none;stroke:#223;stroke-width:2;animation:hw-l 1.8s steps(2) infinite}"
    "@keyframes hw-l{25%{translate:0 -4px}50%,to{translate:0}}"
    f".hw-s{{fill:#889;transform-origin:{CX + 35}px {CY + 4}px;animation:hw-s 1.8s steps(7) infinite}}"
    "@keyframes hw-s{to{translate:-7px -14px;scale:2;opacity:0}}.hw-m{animation-delay:-.9s}"
    ".hw-o{animation:hw-o .4s steps(1) infinite}.hw-g{animation:hw-o 5s infinite}@keyframes hw-o{50%{opacity:0}}"
    ".hw-t{animation:hw-t 60s linear infinite}.hw-d{animation:hw-t 240s linear infinite}@keyframes hw-t{to{translate:900px}}"
    ".hw-j{animation:hw-j .45s ease-out infinite alternate}@keyframes hw-j{to{translate:0 -5px}}"
)
