"""Nausicaa of the Valley of the Wind: the valley seen from the edge of the Sea of Corruption.
An Ohmu rests among the fungi in the foreground, the castle and windmills stand on golden hills
behind it, and Nausicaa rides the wind on her Mehve overhead.

Static layer (PNG, 16 colours): sky, clouds, mountains, hills, castle, windmill towers, fungi, Ohmu.
Sprites (SVG), back to front: cloud streaks, windmill sails, Mehve + Nausicaa (she hovers in the safe
zone rather than crossing, so the film reads at any moment), Ohmu eye glow (blue pulse, plus a red
flush once per 67s), spores.
"""
import math
from lib import Canvas, W, H

NAME = "Nausicaa of the Valley of the Wind"
COLORS = 16

S = ["#2c5ea6", "#4684c6", "#7db2da", "#b8dbe6", "#f6e7b6"]     # sky top -> horizon haze
WHITE = "#ffffff"
G0, G1, G2, BRN = "#e6bb4e", "#c48f30", "#86672c", "#553a36"    # golden hills, brown stone/wood
J0, J1, J2, J3 = "#191634", "#3b2f6c", "#2a7f88", "#52bdfa"     # jungle: indigo, purple, teal, glow
O0, O1 = "#506c90", S[2]                                        # Ohmu shell
OX, OB, OL = 70, 110, 100   # Ohmu tail x, base row, length
EYE = [(OB - 23, OX + 64, 2), (OB - 18, OX + 69, 4), (OB - 13, OX + 79, 3)]   # rows of eyes: y, x, count


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


def cloud(cv, circles, base):
    """White cumulus: union of circles with a flat, shaded, dithered base."""
    for cx, cy, r in circles:
        for y in range(int(cy - r), min(base, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                if math.hypot(x + .5 - cx, y + .5 - cy) <= r:
                    cv.set(x, y, S[3] if base - y <= 2 or (base - y == 3 and x % 2) else WHITE)


def hill(cv, f, c, top=None):
    for x in range(W):
        y = int(round(f(x)))
        cv.rect(x, y, 1, H - y, c)
        if top:
            cv.set(x, y, top)


def tower(cv, x, base, hub):
    """Slender windmill tower; the sails are sprites centred on (x, hub)."""
    cv.rect(x - 1, hub + 6, 3, base - hub - 6, BRN)
    cv.rect(x - 1, hub - 2, 2, 8, BRN)
    cv.rect(x - 1, hub + 6, 1, base - hub - 6, G2)


def shroom(cv, x, base, top, hw, c, sw=1):
    """Giant fungus: flared stalk, tall dome cap with a teal-lit shoulder, hanging tendrils."""
    ch = int(hw * .65)
    cv.rect(x - sw, top + 2, 2 * sw + 1, base - top - 2, c)
    cv.rect(x - sw - 1, top + ch + (base - top) // 2, 2 * sw + 3, base, c)
    for dy in range(ch):
        w = int(round(hw * math.sqrt(1 - ((ch - 1 - dy) / ch) ** 2)))
        cv.rect(x - w, top + dy, 2 * w + 1, 1, c)
        if 0 < dy < 4:
            cv.rect(x - w + 1, top + dy, w - 1, 1, J2)
    for i, dx in enumerate(range(-hw + 1, hw, 4)):
        cv.rect(x + dx, top + ch, 1, 2 + (i * 5) % 4, c)
    cv.rect(x + hw // 3, top + ch - 2, 2, 1, J3)


def spore_stalks(cv, x, base, hs):
    """Thin stalks topped with teal spore balls."""
    for i, h in enumerate(hs):
        cv.rect(x + 4 * i, base - h, 1, h, J1)
        cv.rect(x + 4 * i - 1, base - h - 2, 3, 2, J2)
        cv.set(x + 4 * i - 1, base - h - 2, J3)


def ohmu(cv):
    """Side view, head to the right: overlapping armour plates, rows of eyes on the head, stub legs."""
    pts = [(0, 4), (.08, 11), (.22, 19), (.42, 26), (.62, 30), (.78, 29), (.88, 25), (.95, 18), (1, 9)]
    for i in range(OL + 1):
        t = i / OL
        for (t0, h0), (t1, h1) in zip(pts, pts[1:]):
            if t0 <= t <= t1:
                h = h0 + (h1 - h0) * (t - t0) / (t1 - t0)
        k = (OL - i) % 10           # plates are 10 wide, counted back from the head
        h = int(round(h)) - (2 if k == 9 else 1 if k == 8 else 0)
        x, top = OX + i, OB - h
        bot = OB - (1 if 2 <= k <= 7 else 2)          # each plate's lower edge bows down
        for y in range(top, bot):
            seam = (OL - i + (OB - y) // 7) % 10 == 9     # seams lean back towards the top
            cv.set(x, y, J1 if seam else O1 if y < top + 2 else O0)
        cv.rect(x, bot, 1, 3 if k == 9 else 1, J0)    # dark underside, a leg tip at every seam
    for y, x0, n in EYE:
        for x in range(x0, x0 + 5 * n, 5):
            cv.rect(x, y, 3, 3, J3)
            cv.rect(x, y + 3, 3, 1, J0)
            cv.set(x, y, WHITE)


def draw():
    cv = Canvas()
    bands(cv, 0, [(10, S[0]), (38, S[1]), (52, S[2]), (64, S[3]), (H, S[4])])
    cloud(cv, [(28, 48, 13), (48, 56, 10), (10, 57, 11), (63, 61, 6)], 68)
    cloud(cv, [(208, 46, 12), (226, 54, 12), (190, 58, 8), (238, 60, 8)], 68)
    # far mountains
    peaks = [(62, 9), (112, 15), (166, 11)]
    for x in range(W):
        h = max(ph - abs(x - px) * .45 for px, ph in peaks)
        if h > 0:
            cv.rect(x, 70 - int(round(h)), 1, int(round(h)), S[2])
        if h > 8:
            cv.rect(x, 70 - int(round(h)), 1, int(h - 7), WHITE)
    # golden hills; the castle sits on the bump at x=90
    hill(cv, lambda x: 71 + 2.5 * math.sin(x * .035 + 1) + 1.5 * math.sin(x * .08)
         - 6 * math.exp(-((x - 90) / 20) ** 2), G0)
    # castle: keep, shaded right side, central tower carrying the big windmill, two turrets
    cv.rect(80, 57, 20, 9, S[4])
    cv.rect(93, 57, 7, 9, G2)
    cv.rect(79, 56, 22, 1, BRN)
    cv.rect(88, 46, 4, 11, S[4])
    cv.rect(90, 46, 2, 11, G2)
    for x in (79, 98):
        cv.rect(x, 53, 3, 13, G2)
        cv.rect(x, 51, 3, 2, BRN)
        cv.set(x + 1, 50, BRN)
    for x in (83, 87):
        cv.rect(x, 60, 1, 2, BRN)
    cv.rect(89, 62, 3, 4, BRN)
    tower(cv, 150, 75, 54)
    tower(cv, 176, 74, 58)
    hill(cv, lambda x: 80 + 3 * math.sin(x * .03 + 4) + 1.5 * math.sin(x * .09 + 1), G1, G0)
    # Sea of Corruption: purple floor, fungi framing both sides, dark foreground
    hill(cv, lambda x: 96 + 2 * math.sin(x * .05), J1, J2)
    shroom(cv, 46, 100, 66, 12, J1)
    shroom(cv, 198, 100, 60, 13, J1)
    spore_stalks(cv, 56, 100, (9, 13, 7))
    spore_stalks(cv, 176, 100, (8, 12, 6))
    shroom(cv, 20, H, 38, 21, J0, 2)
    shroom(cv, 222, H, 30, 23, J0, 2)
    ohmu(cv)
    cv.rect(0, 116, W, H, J0)
    return cv


def runs(rows, pal, x0, y0, extra={}):
    """ASCII art -> one stroked <path> of 1px runs per colour (relative moves, y at .5).
    extra: {char: more path data} appended to that colour's path."""
    out = {}
    for dy, row in enumerate(rows):
        x = 0
        while x < len(row):
            n = 1
            while x + n < len(row) and row[x + n] == row[x]:
                n += 1
            if row[x] in pal:
                out.setdefault(row[x], []).append((x0 + x, y0 + dy, n))
            x += n
    s = ""
    for ch, rs in out.items():
        d, cx, cy = "", 0, 0
        for x, y, n in rs:
            d += f"m{x - cx} {y - cy}h{n}" if d else f"M{x} {y}.5h{n}"
            cx, cy = x + n, y
        s += f"<path stroke='{pal[ch]}' d='{d}{extra.get(ch, '')}'/>"
    return s


MEHVE = [
    "..........................HHHH............................",
    ".........................HHHHHH...........................",
    ".........................HHHSSS...........................",
    ".........................HHSSSS...........................",
    "........................BBBBSS............................",
    ".......................BBBBBBBB...........................",
    "......................BBBBBBBBBBS.........................",
    ".....................BB.BBBBB..BBS........................",
    "....................B...BBBBB.............................",
    "........................SSS.SS............................",
    "........................SS...SS...........................",
    "WWWWW...................HH...HH......................WWWWW",
    "WWWWWWWWWWWWWW........WWWWWWWWWWWWWWW.......WWWWWWWWWWWWWW",
    "..WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW..",
    ".......WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW.......",
    "..............wwwwwwwwwwwwwwwwwwwwwwwwwwwwww..............",
    "......................wwwwwwwwwwwwww......................",
]
MPAL = {"W": "white", "w": "#8ac", "B": "#25a", "H": "#a42", "S": "#fc9"}
MX, MY = 98, 20


def mill(x, y, r, diag=0):
    """Four triangular sails as one path; every 'z' returns to the hub. bbox is centred on the hub."""
    d = r * 2 // 3
    return (f"<path d='M{x} {y}l{d}-{d + 1} 2 2zl{d + 1} {d}-2 2zl-{d} {d + 1}-2-2zl-{d + 1}-{d} 2-2z'/>" if diag
            else f"<path d='M{x} {y}l{r}-2v3zl2 {r}h-3zl-{r} 2v-3zl-2-{r}h3z'/>")


EYES, _x = "d='", 0     # one run per row of EYE; the dash pattern cuts each run into 3px eyes
for _i, (y, x, n) in enumerate(EYE):
    EYES += (f"m{x - _x} 5" if _i else f"M{x} {y + 1}.5") + f"h{5 * n - 2}"
    _x = x + 5 * n - 2
EYES += "'"
# Mehve and figure come from runs(); the control bar is appended to the hair-coloured path.
# PARTS is a list only so each piece can be measured separately.
PARTS = [
    "<path class='nc-c' stroke='white' d='M-70 18.5h34m-26 1h40M-250 7.5h30m-40 1h44'/>",
    f"<g class='nc-w' fill='#432'>{mill(90, 47, 9)}{mill(150, 54, 8, 1)}{mill(176, 58, 6)}</g>",
    f"<g class='nc-m'><g class='nc-b'>{runs(MEHVE, MPAL, MX, MY, {'H': f'M{MX + 34}.5 {MY + 6}v6'})}</g></g>",
    f"<g stroke-width='3' stroke-dasharray='3 2'><path class='nc-e' stroke='#9ef' {EYES}/>"
    f"<path class='nc-r' stroke='red' {EYES}/></g>",
    "<g stroke='#aff' stroke-width='2'><path class='nc-s' d='M34 96h2m48 4h2m76-7h2m40-5h2'/>"
    "<path class='nc-s' style='animation-delay:-5s' d='M14 90h2m46 9h2m108 2h2m30-9h2'/></g>",
]
SPRITES = "".join(PARTS)
CSS = (
    ".nc-c{animation:nc-c 150s linear infinite}@keyframes nc-c{to{transform:translateX(520px)}}"
    ".nc-w path{transform-box:fill-box;transform-origin:center;animation:nc-w 9s linear infinite}"
    "@keyframes nc-w{to{transform:rotate(1turn)}}"
    ".nc-m{animation:nc-m 19s infinite alternate}@keyframes nc-m{to{transform:translateX(12px)}}"
    ".nc-b{animation:nc-b 3.4s infinite alternate}@keyframes nc-b{to{transform:translateY(3px)}}"
    ".nc-e{filter:drop-shadow(0 0 1px cyan);animation:nc-e 3.2s infinite alternate}@keyframes nc-e{to{opacity:0}}"
    ".nc-r{opacity:0;filter:drop-shadow(0 0 1px red);animation:nc-r 67s infinite}@keyframes nc-r{48%,56%{opacity:1}44%,60%{opacity:0}}"
    ".nc-s{opacity:0;animation:nc-s 10s linear infinite}@keyframes nc-s{50%{opacity:1}to{transform:translate(5px,-30px)}}"
)
