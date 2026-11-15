"""Spirited Away: the sea railway at dusk. No-Face and Chihiro wait on the little platform, the
bathhouse glows on its rock across the water, the train glides past behind them and Haku crosses
the sky once per cycle.

Static layer (PNG, 13 colours): sky, clouds, bathhouse + rock + reflection, bridge, sea, rail.
Sprites (SVG), back to front: dragon, train, dark-window overlay, platform + No-Face + Chihiro
(above the train so it passes BEHIND them), glints and stars.
"""
import math, random
from lib import Canvas, W, H

NAME = "Spirited Away"
COLORS = 16

# sky top -> horizon
S = ["#2a2859", "#473a7a", "#75508f", "#b0608f", "#e3837b", "#f9b577", "#ffdf9a"]
DARK, RED, ROOF, DEEP, PUFF = "#1b1830", "#bb3333", "#2c6e6a", "#232a5c", "#f2a596"
HZ = 80  # horizon row


def bands(cv, y, rows, soft=True):
    """rows: [(y_end, colour)]. Flat bands with an ordered-dither seam: 3 rows (25/50/75%) when
    soft, else one checker row. Regular patterns like these cost ~20 chars per row; noise costs far more."""
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


def bathhouse(cv, cx, by):
    y = by
    for hw, h in [(27, 9), (22, 8), (16, 7), (10, 6)]:
        cv.rect(cx - hw, y - h, 2 * hw, h, RED)
        cv.rect(cx - hw, y - 1, 2 * hw, 1, DARK)
        for x in range(cx - hw + 2, cx + hw - 2, 4):
            cv.rect(x, y - h + 2, 2, h - 4, S[6])
        cv.rect(cx - hw - 2, y - h - 2, 2 * hw + 4, 2, ROOF)
        cv.rect(cx - hw - 3, y - h - 3, 2, 1, ROOF)
        cv.rect(cx + hw + 1, y - h - 3, 2, 1, ROOF)
        y -= h + 2
    for i in range(5):  # top gable
        cv.rect(cx - 9 + 2 * i, y - 1 - i, 18 - 4 * i, 1, ROOF)
    cv.rect(cx - 1, y - 3, 2, 2, S[6])


def draw():
    cv = Canvas()
    bands(cv, 0, [(12, S[0]), (27, S[1]), (43, S[2]), (57, S[3]), (68, S[4]), (76, S[5]), (HZ, S[6])])
    # sea: mirrored sky, cooling to deep blue in the foreground
    bands(cv, HZ, [(83, S[5]), (88, S[4]), (95, S[3]), (104, S[2]), (116, S[1]), (H, DEEP)], soft=False)
    cv.rect(0, HZ, W, 1, S[5])
    # stars and a few thin streak clouds high up
    for x, y in [(30, 6), (128, 18), (183, 4), (228, 7), (12, 20), (76, 9)]:
        cv.set(x, y, S[6])
    for x, y, n, c in [(100, 33, 44, S[3]), (112, 34, 22, S[3]), (20, 47, 30, S[4]), (132, 50, 36, S[4]),
                       (146, 51, 14, S[4]), (176, 22, 30, S[2]), (40, 23, 20, S[2])]:
        cv.rect(x, y, n, 1, c)
    # clouds: a tall cumulus on the right, a low bank on the far left
    cloud(cv, [(207, 45, 11), (194, 60, 13), (222, 58, 15), (208, 68, 13), (238, 70, 10), (182, 71, 7)],
          HZ - 3, S[6], PUFF, S[3])
    cloud(cv, [(0, 66, 10), (14, 72, 7)], HZ - 3, S[6], PUFF, S[3])
    # rock island (lumpy, flat waterline), chimney with a smoke trail, bathhouse
    x = 34
    for n, h in [(2, 1), (1, 2), (2, 4), (2, 5), (65, 6), (6, 8), (2, 6), (3, 4), (2, 5), (2, 3), (2, 2), (2, 1),
                 (3, 0), (1, 1), (3, 2), (1, 1)]:
        cv.rect(x, HZ - h, n, h, DARK)
        x += n
    cv.rect(108, 36, 3, 40, DARK)
    cv.rect(107, 35, 5, 1, DARK)
    for x, y, n in [(110, 32, 4), (112, 31, 6), (115, 30, 7), (120, 29, 8), (126, 28, 9), (124, 27, 4)]:
        cv.rect(x, y, n, 1, S[0])
    bathhouse(cv, 74, 74)
    for x in range(40, 112, 6):     # lantern row along the foundation
        cv.set(x, 77, S[5])
    # red bridge leading off to the left
    cv.rect(4, 73, 30, 1, RED)
    cv.rect(4, 76, 30, 2, RED)
    for x in range(5, 34, 4):
        cv.rect(x, 72, 1, 4, RED)
        if x % 8 == 5:
            cv.rect(x, 78, 1, 2, DARK)
    # reflection: soft shadow under the rock, then the red tiers as broken streaks
    for y, x0, x1, c in [(80, 35, 124, S[2]), (81, 37, 121, S[2]), (82, 42, 112, S[2]), (84, 47, 101, RED),
                         (86, 52, 96, RED), (88, 58, 90, RED), (90, 64, 84, S[2]), (92, 70, 78, S[2]),
                         (84, 108, 111, S[2]), (86, 108, 111, S[2])]:
        cv.rect(x0, y, x1 - x0, 1, c)
    for x in range(46, 106, 8):
        cv.rect(x, 81, 2, 1, S[6])
    # the track: a rail just under the surface with sleeper ticks
    cv.rect(0, 101, W, 1, DARK)
    for x in range(1, W, 6):
        cv.rect(x, 102, 2, 1, S[1])
    # ripples: short streaks in the neighbouring band colour
    r = random.Random(5)
    for y in range(82, 118, 3):
        for _ in range(2):
            x, n = r.randrange(-5, W), r.randrange(5, 13)
            if y in (100, 103) or (30 < x < 118 and y < 96):
                continue
            c = S[6] if y < 88 else S[4] if y < 95 else S[3] if y < 104 else S[2] if y < 116 else S[1]
            cv.rect(x, y, n, 1, c)
    return cv


# Sprite paths are hand-written: filled outlines for big shapes, and for small details a stroked path
# of 1px runs at y+.5 with relative moves ("M139 85.5h2m1 0h1m-5 1h5"), about half the size of
# lib.sprite(). 3-digit and named colours keep the '#' -> '%23' escaping cost down.
NX, NY = 148, 73     # No-Face top-left; platform top is y=100
BODY = "h6v1h1v1h1v3h1v9h1v8h1v6h-16v-6h1v-8h1v-9h1v-3h1v-1h1z"
FACE = "h4v1h1v1h1v7h-1v1h-1v1h-4v-1h-1v-1h-1v-7h1v-1h1z"
TR = 87              # train roof row


def dragon():
    """Haku. Drawn facing right and mirrored by the outer matrix so he can reuse the train's keyframes
    and still fly right-to-left. Straight body segments each bob with a phase offset (--d) so a wave
    travels down the body; the teal mane is a 1px drop-shadow cast upwards (see CSS)."""
    seg = lambda i, x, leg=0: f"<path style='--d:{i}' d='M{x} 3.5h5{'m-4 3h2' if leg else ''}'/>"
    tail = "".join(seg(12 - i, 5 * i) for i in range(3))
    body = "".join(seg(9 - i, 15 + 5 * i, i in (2, 7)) for i in range(9))
    head = "<path stroke='none' d='M71 3h-2v-1h-2v-1h-2v-1h-2v-2h-1v1h-2v-2h-1v10h4v-1h6v-1h2z'/><path stroke='none' fill='#112' d='M65 2h1v1h-1z'/>"
    return (f"<g transform='matrix(-1 0 0 1 1200 22)'><g class='sa-t sa-h' fill='#fff' stroke='#fff' stroke-width='4'>"
            f"<g stroke-width='2'>{tail}</g>{body}{head}</g></g>")


SPRITES = (
    dragon()
    # train (parked 400px off to the left): cream cars, red-brown roof + skirt, lit windows as one
    # dashed stroke, soft reflection
    + f"<g class='sa-t'><path fill='#fec' d='M-400 {TR + 1}h37v9h-37zm38 0h37v9h-37z'/>"
      f"<path fill='#a43' d='M-399 {TR}h35v1h-35zm38 0h35v1h-35zm-39 10h75v4h-75z'/>"
      f"<path stroke='#fb4' stroke-width='4' stroke-dasharray='5 2' d='M-398 {TR + 5}h33m5 0h33'/>"
      f"<path opacity='.3' d='M-400 {TR + 14}h75v5h-75z'/></g>"
    # windows that go dark now and then
    + "<path class='sa-m' fill='#b33' d='M61 67h2v5h-2zm25-10h2v4h-2zm-6-9h2v3h-2z'/>"
    # platform, No-Face (body, mask, marks), Chihiro (hair, skin, shirt, stripe, shorts), then every dark detail in one path
    + "<path fill='#cba' d='M130 100h58v2h-58z'/>"
    + f"<path fill='#112' d='M{NX + 5} {NY}{BODY}'/><path fill='#fff' d='M{NX + 6} {NY + 3}{FACE}'/>"
    + f"<path stroke='#a5c' d='M{NX + 5} {NY + 5}.5h2m2 0h2m-6 2h2m2 0h2m-5 1h1m2 0h1'/>"
    + "<path stroke='#532' d='M139 85.5h2m1 0h1m-5 1h5m-6 1h5m-2 1h2m-2 1h1'/>"
      "<path fill='#fc9' d='M137 88h3v3h-3zm-1 4h6v2h-6zm1 5h1v3h-1zm3 0h1v3h-1z'/>"
      "<path fill='#fff' d='M137 91h4v4h-4z'/><path stroke='teal' d='M137 92.5h3'/><path fill='salmon' d='M137 95h4v2h-4z'/>"
    + f"<path fill='#112' d='M{NX + 5} {NY + 6}h2v1h-2zm4 0h2v1h-2zm-2 4h2v1h-2z"
      "M130 102h58v2h-58zm4 2h2v6h-2zm46 0h2v6h-2zm2-22h1v18h-1zm-2-2h5v3h-5z'/>"
      "<path class='sa-a' fill='red' d='M181 81h3v1h-3z'/>"
    # twinkling water glints and stars
    + "<path class='sa-a' stroke='#fea' d='M112 86.5h6m76 3h5m-166 5h5M97 4.5h1'/>"
      "<path class='sa-b' stroke='#fea' d='M24 90.5h6m170-5h6m-110 13h5M150 8.5h1'/>"
)
CSS = (
    ".sa-t{animation:sa-t 70s linear infinite}@keyframes sa-t{to{transform:translateX(1400px)}}"
    ".sa-h{filter:drop-shadow(0 -1px teal)}"
    ".sa-h path{animation:sa-w 1.2s calc(var(--d,0)*-.3s) ease-in-out infinite alternate}@keyframes sa-w{to{transform:translateY(5px)}}"
    ".sa-a,.sa-b{animation:sa-o 4s infinite}.sa-b{animation-delay:-2s}"
    ".sa-m{animation:sa-o 13s steps(1) infinite}@keyframes sa-o{50%{opacity:0}}"
)
