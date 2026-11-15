"""Ponyo: the storm chase. Ponyo runs along the backs of the giant wave-fish as they roll past
Sosuke's house on its cliff; Lisa's little car races along the cliff road and the house's signal
lamp blinks out to the fishing boat on the horizon.

Static layer (PNG): sky, far cloud bank, sea, boat, cliff + road + tunnel, house, trees.
Sprites (SVG), back to front: racing scud, car (clipped at the tunnel by a nested <svg>), lamp and
boat light, back wave-fish row, front wave-fish row, Ponyo.

Ponyo's feet stay on the fish because the fish back is generated from the same ease-in-out curve
her bob keyframes use (rise for RISE of the period, fall for the rest), and both run on T.
"""
import math
from lib import Canvas, W, H

NAME = "Ponyo"
COLORS = 16

S = ["#243a66", "#2f5685", "#3f7ba3", "#62a5b8", "#9ccdc4", "#e4eec2"]   # sky top -> horizon glow
ROCK, ROCKD, GRASS, PINE = "#6a5f85", "#3d3560", "#58a64e", "#2a6a4c"
ROOF, LAMP, DARK = "#cf4a3a", "#ffd24a", "#161c3a"
HZ = 72            # horizon row
P, AMP, RISE = 80, 16, .15  # wave-fish period (px), height, fraction of the period that is the head
JUMP = AMP + 3     # apex of Ponyo's hop
T = 5              # seconds per fish period (front row)
PX = 151           # Ponyo's feet centre; the front row origin is shifted so phase 0 sits here
FRONT, BACK = 108, 96       # trough rows of the two wave rows
TUN = 115          # left edge of the tunnel mouth; the car is clipped just inside it


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


def cloud(cv, circles, base, hi, mid, lo):
    """Circles painted back to front, each with a lit upper-left rim; flat shadowed base."""
    for cx, cy, r in circles:
        for y in range(int(cy - r), min(base, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + .5 - cx, y + .5 - cy
                d = math.hypot(dx, dy)
                if d <= r:
                    rim = d > r - 1.7 and (-.6 * dx - .8 * dy) > .2 * r
                    cv.set(x, y, hi if rim else (lo if base - y <= 2 or (base - y == 3 and x % 2) else mid))


def cliff_top(x):
    """Top row of the headland at column x."""
    pts = [(0, 54), (18, 51), (46, 49), (64, 46), (113, 46), (119, 49), (124, 56), (128, 66), (133, 80), (141, 110)]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if xa <= x <= xb:
            return round(ya + (yb - ya) * (x - xa) / (xb - xa))


def house(cv, x0):
    C = S[5]
    # ground floor, skirt roof, upper floor, gable roof
    cv.rect(x0 + 2, 38, 26, 8, C)
    cv.rect(x0, 36, 30, 2, ROOF)
    cv.rect(x0 + 7, 30, 14, 6, C)
    for i in range(4):
        cv.rect(x0 + 11 - 2 * i, 26 + i, 6 + 4 * i, 1, ROOF)
    # shaded right-hand walls
    cv.rect(x0 + 23, 38, 5, 8, S[4])
    cv.rect(x0 + 18, 30, 3, 6, S[4])
    # lit windows and door
    for x, y in [(5, 40), (10, 40), (9, 31), (14, 31)]:
        cv.rect(x0 + x, y, 3, 3, LAMP)
    cv.rect(x0 + 17, 40, 3, 6, ROCKD)
    # balcony for the signal lamp, flag mast
    cv.rect(x0 + 21, 35, 9, 1, DARK)
    for x in (23, 26, 29):
        cv.rect(x0 + x, 33, 1, 2, DARK)
    cv.rect(x0 + 33, 26, 1, 20, DARK)
    cv.rect(x0 + 34, 27, 3, 2, ROOF)
    cv.rect(x0 + 34, 30, 3, 2, LAMP)


def draw():
    cv = Canvas()
    bands(cv, 0, [(13, S[0]), (29, S[1]), (45, S[2]), (57, S[3]), (66, S[4]), (HZ, S[5])])
    # far storm cumulus, lit from the horizon glow
    cloud(cv, [(176, 50, 9), (190, 44, 12), (207, 50, 13), (224, 46, 11), (238, 54, 10), (160, 58, 7)],
          HZ - 6, S[5], S[4], S[3])
    cloud(cv, [(8, 44, 9), (24, 48, 7)], 52, S[5], S[4], S[3])
    # sea behind the wave rows
    bands(cv, HZ, [(74, S[3]), (H, S[2])], soft=False)
    for x, y, n in [(150, 77, 9), (176, 76, 12), (214, 78, 8), (196, 81, 6)]:
        cv.rect(x, y, n, 1, S[3])
    # fishing boat on the horizon
    cv.rect(186, 70, 16, 2, DARK)
    cv.rect(188, 72, 12, 1, DARK)
    cv.rect(190, 66, 6, 4, S[5])
    cv.rect(191, 67, 2, 1, DARK)
    cv.rect(197, 62, 1, 8, DARK)
    cv.rect(183, 69, 3, 1, DARK)
    # headland: rock face, darker below the road, grass cap
    for x in range(142):
        yt = cliff_top(x)
        for y in range(yt, H):
            cv.set(x, y, ROCKD if y > 64 or (x > TUN + 5 and y > yt + 2) else ROCK)
        for y in range(yt, yt + 3):
            if x < 123:
                cv.set(x, y, GRASS)
        if x < 123 and x % 2:
            cv.set(x, yt + 3, GRASS)
    # strata cracks
    for x, y, n in [(6, 58, 9), (30, 56, 12), (22, 60, 6), (56, 54, 10), (74, 58, 14), (98, 55, 8), (50, 60, 5),
                    (10, 70, 14), (44, 72, 18), (80, 69, 12), (106, 73, 10)]:
        cv.rect(x, y, n, 1, ROCKD if y < 64 else ROCK)
    # road ledge with a low wall, tunnel through the shoulder
    cv.rect(0, 63, TUN + 3, 2, S[4])
    for x in range(0, TUN + 2, 4):
        cv.rect(x, 65, 2, 1, S[5])
    cv.rect(TUN, 57, 6, 8, DARK)
    cv.rect(TUN + 1, 56, 4, 1, DARK)
    # trees left of the house
    cv.blob([(69, 38, 6), (62, 42, 5), (73, 43, 4)], GRASS, PINE, PINE)
    cv.rect(68, 44, 2, 3, ROCKD)
    for x, h in [(34, 6), (40, 9), (46, 6)]:
        for i in range(h):
            cv.rect(x - i // 2, cliff_top(x) - h + i, 1 + 2 * (i // 2), 1, PINE)
    house(cv, 77)
    return cv


# ---------------------------------------------------------------- sprites
def bez(t, a=.42, b=.58):
    """CSS ease-in-out, cubic-bezier(.42,0,.58,1): progress at time fraction t."""
    lo, hi = 0, 1
    for _ in range(40):
        u = (lo + hi) / 2
        if 3 * u * (1 - u) ** 2 * a + 3 * u * u * (1 - u) * b + u ** 3 < t:
            lo = u
        else:
            hi = u
    return 3 * u * u * (1 - u) + u ** 3


# Ponyo leaves a fish's tail NOSE px before the next nose reaches her, peaks at JUMP exactly as it
# arrives (RISE of the period), then eases down for the rest. The fish back is that descent curve,
# capped at AMP (so she lands on the flat of the head) with a blunt quarter-ellipse nose in front.
NOSE = round(P * RISE)
PROF = [round(min(AMP * math.sqrt(max(0, 1 - ((NOSE - 3 - x) / (NOSE - 3)) ** 2)) if x < NOSE - 3 else AMP,
                  JUMP * (1 - bez(((x + .5 + NOSE) / P - RISE) / (1 - RISE))))) if x < P - NOSE else 0
        for x in range(P)]


def runs(art, pal, x0, y0, attr=""):
    """ASCII art -> one stroked path per colour made of 1px runs with relative moves.
    An empty colour leaves the stroke to be inherited from the parent group."""
    out = ""
    for ch, col in pal.items():
        d, cx, cy = "", 0, 0
        for dy, row in enumerate(art):
            x = 0
            while x < len(row):
                n = 1
                while x + n < len(row) and row[x + n] == row[x]:
                    n += 1
                if row[x] == ch:
                    X, Y = x0 + x, y0 + dy
                    d += f"m{X - cx} {Y - cy}h{n}" if d else f"M{X} {Y}.5h{n}"
                    cx, cy = X + n, Y
                x += n
        if d:
            out += f"<path{attr}{' stroke=' + repr(col) if col else ''} d='{d}'/>"
    return out.replace(" -", "-")


def fish():
    """One wave-fish in local coords: trough at y=0, back rising to -AMP, filled down to y=40."""
    d, n = f"M0 40V{-PROF[0]}", 1
    for a, b in zip(PROF, PROF[1:]):
        if a == b:
            n += 1
        else:
            d += f"h{n}v{a - b}"
            n = 1
    d += f"h{n + 1}V40z"
    art = [["."] * P for _ in range(AMP + 12)]
    for x in list(range(3, 10)) + list(range(19, 46)):     # sheen just inside the top of the head
        art[AMP - PROF[x] + 1][x] = "h"
    for x, y, n in [(30, -5, 14), (50, 2, 12), (10, 5, 16), (36, 9, 9)]:   # streaks down the flank
        art[AMP + y][x:x + n] = "h" * n
    hi = runs(["".join(r) for r in art], {"h": "#48c"}, 0, -AMP)
    eye = ("<path fill='#ffd' d='M11-13h4v1h1v4h-1v1h-4v-1h-1v-4h1zm-14 8h2v1h-2zm-2-5h1v1h-1zm4-3h1v1h-1z'/>"
           "<path fill='#113' d='M11-11h3v3h-3zm-9 6h7v1h-7z'/>")
    return f"<path d='{d}'/>{hi}{eye}".replace(" -", "-")


# Hair is one filled outline; everything else on her is 1px runs drawn over it.
HAIR = "h7v1h2v1h1v1h1v4h-1v1h-2v2h-1v1h-8v-1h-1v-1h-1v-2h-1v-3h1v-2h1v-1h2v-1z"
PONYO = [
    "................",
    "................",
    "................",
    "................",
    "...sss.s........",
    "..sssssss.......",
    "..skssssks......",
    "..sssssssss.....",
    "..sskkkksss.....",
    "..ssskkssss.....",
    "...ssssssss.....",
    ".....rrrrr......",
    "ss..rrrrrrr..ss.",
    ".sssrrrrrrrsss..",
    "....rrrrrrr.....",
    "...rrrrrrrrr....",
    "..rrrrrrrrrrr...",
    "..rrrrrrrrrrr...",
    "...wwwwwwwww....",
]
LEG_A = ["...ss....ss.....", "..ss......ss....", ".ss.......sss..."]
LEG_B = [".....ss.ss......", ".....ss.ss......", "....sss.s......."]
PPAL = {"s": "", "r": "#d23", "k": "#312", "w": "#fff"}
N = len(PONYO)
PY = FRONT - N - 3              # her top row when standing on a tail (feet on the row above the water)
X0 = PX - 8
CX, CY = TUN + 4, 57            # car, parked just inside the tunnel
ROWX = PX + NOSE - 3 * P        # front row origin: at t=0 Ponyo stands NOSE px short of a tail's end

SPRITES = (
    # racing scud: one 300px strip of 2px-thick streaks, drawn twice so the loop is seamless
    "<g class='po-c'><path id='po-k' stroke='#1a2850' stroke-width='2' d='M6 22h70m-58-2h44m-36-2h22"
    "M112 12h56m-52-2h34m-28-2h16M196 20h80m-64-2h46m-40-2h26m-22-2h10'/><use href='#po-k' x='300'/></g>"
    # Lisa's car (body, windows + headlight, wheels); the nested svg clips it at the tunnel mouth
    f"<svg width='{TUN + 2}' height='99'><g class='po-c po-v'><path fill='#fc3' d='M{CX + 2} {CY}h8v3h1v3h-11v-3h1v-2h1z'/>"
    f"<path fill='#cef' d='M{CX + 2} {CY + 1}h2v2h-2zm3 0h4v2h-4zm-5 3h1v1h-1z'/>"
    f"<path fill='#113' d='M{CX + 1} {CY + 6}h2v1h-2zm6 0h2v1h-2z'/></g></svg>"
    # signal lamp on the balcony, answering light on the boat
    "<path class='po-l' fill='#fe6' d='M103 30h2v1h1v2h-1v1h-2v-1h-1v-2h1z'/>"
    "<path class='po-l po-m' fill='#fe6' d='M197 60h2v2h-2z'/>"
    # back row of wave-fish: the row is defined here and reused for the front row
    f"<g fill='#2a55a8' transform='translate(-50 {BACK})'><g class='po-w po-b'><g id='po-r'><g id='po-f'>{fish()}</g>"
    + "".join(f"<use href='#po-f' x='{P * i}'/>" for i in range(1, 5)) + "</g></g></g>"
    # front row, then Ponyo on top of it
    f"<g fill='#17307a' transform='translate({ROWX} {FRONT})'><use class='po-w' href='#po-r'/></g>"
    f"<g class='po-j' stroke='#fca'><path fill='#f63' stroke='none' d='M{X0 + 4} {PY}{HAIR}'/>{runs(PONYO, PPAL, X0, PY)}"
    + runs(LEG_A, {"s": ""}, X0, PY + N, " class='po-a'") + runs(LEG_B, {"s": ""}, X0, PY + N, " class='po-a po-z'") + "</g>"
)
CSS = (
    f".po-w{{animation:po-w {T}s linear infinite}}.po-b{{animation-duration:8s}}@keyframes po-w{{to{{transform:translateX(-{P}px)}}}}"
    ".po-c{animation:po-c 50s linear infinite}.po-v{animation-duration:20s}@keyframes po-c{to{transform:translateX(-300px)}}"
    f".po-j{{animation:po-j {T}s ease-in-out infinite}}@keyframes po-j{{{round(RISE * 100)}%{{transform:translateY(-{JUMP}px)}}}}"
    ".po-a{animation:po-o .5s steps(1) infinite}.po-z{animation-delay:-.25s}"
    "@keyframes po-o{50%{opacity:0}}.po-l{filter:drop-shadow(0 0 2px #fe6);animation:po-l 6s steps(1) infinite}.po-m{animation-delay:-3s}@keyframes po-l{8%,24%,48%{opacity:0}16%,32%{opacity:1}}"
)
