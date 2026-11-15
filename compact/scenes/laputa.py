"""Castle in the Sky: Laputa adrift in a blue noon sky, rising out of towering cumulus. On a meadow
in the foreground the moss-covered robot offers a flower to Sheeta while Pazu looks on.

Static layer (PNG, 16 colours): sky, cumulus, far cloud deck, meadow, robot, Sheeta, Pazu.
Sprites (SVG), back to front: far cloud, the island, near cloud + a still wisp across the island's
base, a flock circling the tree, the robot's eye and Sheeta's crystal glowing, a flaptter crossing.

The island is a second, tiny palette PNG inside the SVG rather than vector paths: a PNG is far
cheaper per pixel than paths (~890 characters for 76x58 px of detail), and as its own element it can
bob in one piece with clouds passing both behind and in front of it.
"""
import base64, io, math
from PIL import Image
from lib import Canvas, W, H, UNPAINTED

NAME = "Castle in the Sky"
COLORS = 16

S = ["#2b56a6", "#3a71c0", "#528fd6", "#73ade4", "#9ccbee"]      # sky top -> horizon
HI, MID, LO = "#faf0e6", "#ccccdd", "#99aadd"                    # cloud: sunlit ('linen'), shade (#ccd), deep (#9ad)
G1, G2, G3 = "#a5d45c", "#5d9e45", "#2c6a48"                     # grass / moss
DARK, BR, TAN, SKIN, PINK = "#22223a", "#8a5638", "#c9955a", "#f6c999", "#e0607c"
GY = 108             # meadow top row
IX, IY = 70, 19      # island sprite top-left


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


def disc(cx, cy, r):
    return [(x, y) for y in range(int(cy - r) - 1, int(cy + r) + 2) for x in range(int(cx - r) - 1, int(cx + r) + 2)
            if math.hypot(x + .5 - cx, y + .5 - cy) <= r]


def cumulus(cv, back, shade, front):
    """Cumulus in three passes of lumps (cx, cy, r): sunlit silhouette, then shaded lumps clipped to
    it (the lower-right body in shadow), then sunlit lumps billowing in front of the shadow."""
    mask = {p for l in back + front for p in disc(*l)}
    # fill sky pockets enclosed by the lumps (or by lumps and the meadow): flood the open sky from above
    sky, todo = set(), [(x, -1) for x in range(-30, W + 30)]
    while todo:
        x, y = todo.pop()
        if -30 <= x < W + 30 and -1 <= y < GY and (x, y) not in sky and (x, y) not in mask:
            sky.add((x, y))
            todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    mask = {(x, y) for x in range(W) for y in range(GY) if (x, y) not in sky}
    dark = {p for l in shade for p in disc(*l)} & mask
    lit = {p for l in front for p in disc(*l)}
    for x, y in mask:
        if (x, y) in dark and (x, y) not in lit:   # deepest where the shadow meets the lumps in front
            cv.set(x, y, LO if (x, y + 1) in lit or (x, y + 2) in lit else MID)
        else:
            cv.set(x, y, HI)


# ---------------------------------------------------------------- the island (its own little PNG)
IW, IH = 76, 58
ST1, ST2, ST3, IDK = "#efe2c4", "#b7a99c", "#7c7790", "#35304c"   # stone light / mid / shade, underside
T1, T2, T3, TRK = "#9fcc62", "#5c9a52", "#2f6652", "#7a5648"      # canopy, trunk


def island():
    cv = Canvas(IW, IH)
    cx = IW // 2
    # underside: a dark shallow bowl with hanging roots
    for d in range(9):
        hw = int(34 * math.sqrt(1 - (d / 9) ** 2))
        cv.rect(cx - hw, 47 + d, 2 * hw, 1, IDK)
        cv.rect(cx - hw, 47 + d, max(2, hw // 5), 1, ST3)
    for x, y, n in [(13, 51, 3), (20, 53, 3), (27, 55, 2), (33, 55, 3), (39, 56, 2), (44, 55, 3), (51, 54, 2),
                    (58, 52, 3)]:
        cv.rect(x, y, 1, n, IDK)
    # stone tiers: lit left, shaded right, a colonnade of dark arches, a grassy ledge where each steps out
    prev = 0
    for hw, y, h in [(12, 26, 6), (20, 32, 6), (28, 38, 6), (34, 44, 3)]:
        cv.rect(cx - hw, y, 2 * hw, h, ST2)
        cv.rect(cx - hw, y, hw * 2 // 3, h, ST1)
        cv.rect(cx + hw - hw // 2, y, hw // 2, h, ST3)
        if h > 3:
            for x in range(cx - hw + 2, cx + hw - 1, 3):
                cv.rect(x, y + 2, 1, 3, IDK if x > cx - hw // 3 else ST3)
            cv.rect(cx - hw, y, hw - prev, 1, T2)
            cv.rect(cx + prev, y, hw - prev, 1, T3)
            if prev:     # a domed turret at each end of the ledge
                for x, c in ((cx - hw, ST1), (cx + hw - 3, ST3)):
                    cv.rect(x, y - 2, 3, 2, c)
                    cv.rect(x, y - 3, 3, 1, T3)
        prev = hw
    # trunk with roots spilling over the keep
    cv.rect(cx - 3, 19, 7, 8, TRK)
    cv.rect(cx + 2, 19, 2, 8, IDK)
    cv.rect(cx - 8, 25, 17, 1, TRK)
    for x, n in [(cx - 6, 3), (cx - 10, 2), (cx + 5, 4), (cx + 9, 2)]:
        cv.rect(x, 25, 2, n, TRK)
    # the colossal canopy
    for ccx, ccy, r in [(13, 17, 5), (63, 17, 5), (53, 13, 9), (23, 13, 9), (46, 8, 7), (38, 11, 11), (30, 7, 6)]:
        for y in range(int(ccy - r), min(22, int(ccy + r) + 1)):
            for x in range(int(ccx - r), int(ccx + r) + 1):
                dx, dy = x + .5 - ccx, y + .5 - ccy
                if math.hypot(dx, dy) <= r:
                    k = (-.55 * dx - .83 * dy) / r
                    cv.set(x, y, T3 if 22 - y <= 2 or k < -.45 else (T1 if k > .35 else T2))
    return cv


def png_sprite(cv):
    """A Canvas (magenta = transparent) as a base64 palette PNG."""
    cols = [UNPAINTED] + sorted({p for row in cv.px for p in row if p != UNPAINTED})
    im = Image.new("P", (cv.w, cv.h))
    im.putpalette([v for c in cols for v in c])
    im.putdata([cols.index(p) for row in cv.px for p in row])
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True, transparency=0)
    return base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------- foreground figures (static)
ROBOT = [
    "................tbbbbbb........",
    "..............GGtbbbbbbbb......",
    "..............gttbbbbbbbb......",
    "..............tkEEkkkekbb......",
    "..............ttbbbbbbbbb......",
    "...............tbbbbbbbb.......",
    ".................kkkkk.........",
    "............GGtttbbbbbbbbbb....",
    "..........gGGgttbbbbbbbbbbbbb..",
    "..........gggtttbbbbbbbbbbbbb..",
    "..........tbgtttbbbbbbbbbkbbb..",
    "..........tb.tttbbbbbbgGbb.bb..",
    "..........kk.ttbbbbbbbbgbb.kk..",
    "..........tb..tbbbbbbbbbb..bb..",
    ".f........tb..tbbbbbbbbbb..bb..",
    "fpf.......kk...tbbbbbbbb...kk..",
    ".f........tb...tbbbbbbbb...bb..",
    ".G.....ttttb....kkkkkk.....bb..",
    ".tttkttkbbk....tbbbbbbbb...kk..",
    ".bbbkbbkb......tbbbbbbbb...bb..",
    "...............tbbb..tbbb..bb..",
    "...............tbbb..tbbb..kk..",
    "...............kkkk..kkkk.bbbb.",
    "...............tbbb..tbbb.bbbb.",
    "...............tbbb..tbbb.b.bb.",
    "...............kkkk..kkkk......",
    "...............Gbbb..tbbb......",
    "...............gbbb..tbbg......",
    "...............kkkk..kkkk......",
    "...............tbbb..tbbb......",
    "...............tbbb..tbbb......",
    "..............ttbbb..tbbbb.....",
    ".............tbbbbb..tbbbbb....",
]
RPAL = {"b": BR, "t": TAN, "g": G2, "G": G1, "k": DARK, "e": TAN, "E": TAN, "f": HI, "p": PINK}
RX, RY = 131, GY - 33

SHEETA = [
    "..kkkk..",
    ".kkkkkk.",
    ".kkssss.",
    ".kkssks.",
    ".k.sss..",
    ".kppppk.",
    ".kppppps",
    ".kpppp..",
    ".k.pp...",
    "..yyyy..",
    "..yyyy..",
    "..y..y..",
    "..y..y..",
    "..k..k..",
]
PAZU = [
    "..ttttt.",
    ".ttttttt",
    "..kssss.",
    "..kssks.",
    "...sss..",
    "..rwwr..",
    ".wrwwrw.",
    ".wrwwrw.",
    ".s.rr.s.",
    "..gggg..",
    "..gggg..",
    "..g..g..",
    "..g..g..",
    "..g..g..",
    "..k..k..",
]
KPAL = {"k": DARK, "s": SKIN, "p": PINK, "y": TAN, "t": TAN, "r": BR, "w": HI, "g": G3}
SX, PX = 119, 107


def draw():
    cv = Canvas()
    bands(cv, 0, [(13, S[0]), (33, S[1]), (56, S[2]), (80, S[3]), (H, S[4])])
    # towering cumulus on the left, a lower bank on the right, a far cloud deck between them
    cumulus(cv, [(36, 47, 8), (26, 54, 8), (46, 56, 8), (14, 66, 11), (36, 66, 12), (56, 70, 10), (24, 78, 12),
                 (66, 86, 10), (2, 82, 12), (46, 84, 10)],
            [(48, 70, 11), (60, 84, 12), (34, 82, 9)],
            [(20, 94, 15), (46, 100, 13), (68, 104, 9), (-2, 100, 12)])
    cumulus(cv, [(218, 66, 8), (229, 74, 9), (207, 75, 9), (240, 86, 10), (194, 87, 9), (218, 82, 8)],
            [(232, 84, 12), (214, 88, 8)],
            [(200, 100, 12), (226, 102, 13), (246, 104, 8), (180, 104, 7)])
    for x, r in [(92, 3), (99, 5), (108, 4), (116, 3), (140, 3), (147, 4), (160, 3)]:
        for px, py in disc(x, 103, r):
            if py < 104:
                cv.set(px, py, HI)
    cv.rect(86, 102, 80, 2, HI)
    # meadow: lit top edge, tufts, a few flowers
    cv.rect(0, GY, W, H - GY, G2)
    cv.rect(0, GY, W, 1, G1)
    for y in range(120, H):
        for x in range(W):
            if y > 121 or (x + y) % 2:
                cv.set(x, y, G3)
    for x in range(W):
        if (x * 7) % 13 < 3:
            cv.set(x, GY - 1, G1 if x % 2 else G2)
    for x, y, c in [(84, 112, HI), (98, 115, PINK), (114, 113, HI), (136, 115, HI), (152, 112, PINK), (170, 114, HI)]:
        cv.set(x, y, c)
    cv.paint(ROBOT, RPAL, RX, GY - len(ROBOT))
    cv.paint(SHEETA, KPAL, SX, GY - len(SHEETA))
    cv.paint(PAZU, KPAL, PX, GY - len(PAZU))
    return cv


def runs(rows, x0, y0):
    """One horizontal run per row [(x, n)] -> a stroked path of 1px rows with relative moves."""
    d, px = "", None
    for i, (x, n) in enumerate(rows):
        d += f"M{x0 + x} {y0}.5h{n}" if px is None else f"m{x - px} 1h{n}"
        px = x + n
    return d


def puff(circles, base, x0, y0, shade=2):
    """A small drifting cloud as two stroked paths (sunlit body, shaded base)."""
    rows = []
    for y in range(base):
        xs = [x for x in range(80) if any(math.hypot(x + .5 - cx, y + .5 - cy) <= r for cx, cy, r in circles)]
        if xs:
            rows.append((y, min(xs), max(xs) - min(xs) + 1))
    top = rows[0][0]
    body = [(x, n) for y, x, n in rows[:-shade]]
    foot = [(x, n) for y, x, n in rows[-shade:]]
    return (f"<path stroke='linen' d='{runs(body, x0, y0 + top)}'/>"
            f"<path stroke='#ccd' d='{runs(foot, x0, y0 + top + len(body))}'/>")


SPRITES = (
    # far cloud: the near cloud's shape again, higher and slower, drawn behind the island
    "<use class='lp-d' href='#lp-p' y='-27'/>"
    f"<image class='lp-i' x='{IX}' y='{IY}' width='{IW}' height='{IH}' href='data:image/png;base64,{png_sprite(island())}'/>"
    f"<g class='lp-c'><g id='lp-p'>{puff([(7, 8, 5), (17, 6, 6), (28, 7, 7), (40, 9, 5), (48, 10, 3)], 12, -70, 64)}</g></g>"
    # the same shape once more, standing still across the island's lower left: Laputa rising out of the cloud
    "<use href='#lp-p' x='121' y='5'/>"
    # a little flock wheeling round the tree (x and y swing a quarter period apart = an ellipse)
    + "<g class='lp-x'><path class='lp-y' stroke='#223' d='M64 22.5h1m1 0h1m-2 1h1m6 3h1m1 0h1m-2 1h1m-12 2h1m1 0h1m-2 1h1'/></g>"
    # robot eye and Sheeta's crystal
    + f"<path class='lp-e' fill='#fd5' d='M{RX + 16} {RY + 3}h2v1h-2z'/>"
    + f"<path class='lp-e' stroke='#5ef' d='M{SX + 5} {GY - 9}.5h1m-2 1h3m-2 1h1'/>"
    # flaptter: hull + tail fin, Dola's pink braids, faces, dragonfly wings in two alternating frames
    + "<g class='lp-f'><path fill='#532' d='M-600 34h6v-1h14v1h1v1h-1v1h-3v1h-7v-1h-3v-1h-7zm0-2h1v2h-1z'/>"
      "<path stroke='#e68' d='M-586 31.5h2m1 0h1'/><path stroke='#fc9' d='M-585 32.5h1m2 0h1'/>"
      "<g stroke='#cde'><path class='lp-w' d='M-592 31.5h4m-7-1h4m-7-1h4m-6-1h3m8 2h3m-4-1h3m-4-1h3m-4-1h3m-3-1h2'/>"
      "<path class='lp-w' style='animation-delay:-.1s' d='M-601 32.5h11m-9-1h7'/></g></g>"
)
CSS = (
    ".lp-i,.lp-x,.lp-y{animation:lp-i 9s ease-in-out infinite alternate}@keyframes lp-i{to{transform:translateY(2px)}}"
    ".lp-x{animation-name:lp-x}.lp-y{animation-name:lp-y;animation-delay:-4.5s}"
    "@keyframes lp-x{to{transform:translateX(88px)}}@keyframes lp-y{to{transform:translateY(12px)}}"
    ".lp-c{animation:lp-c 260s -150s linear infinite}.lp-d{animation:lp-c 420s -60s linear infinite}"
    "@keyframes lp-c{to{transform:translateX(380px)}}"
    ".lp-e{animation:lp-o 4s infinite}.lp-w{animation:lp-o .2s steps(1) infinite}@keyframes lp-o{50%{opacity:0}}"
    ".lp-f{animation:lp-f 80s linear infinite}@keyframes lp-f{to{transform:translateX(1200px)}}"
)
