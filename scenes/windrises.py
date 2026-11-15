"""The Wind Rises: the summer hillside (320x180).

Nahoko paints at her easel on the crest under the big white parasol; Jiro stands below on the slope holding
his hat against the wind, and bands of wind comb through the grass. One two-minute story loop:

   10 s  a paper plane glides down the wind into Jiro's raised hand
   19 s  the silver gull-winged prototype crosses the sky
   46 s  a gust takes the parasol; it tumbles down to Jiro, who catches it, carries it up and plants it
   56 s  Caproni's nine-winged dream plane lumbers across with Caproni waving from the top wing; Nahoko looks
         up and Jiro lifts his hat and waves back
   90 s  Jiro walks back down
   98 s  an ox cart hauls the prototype along the valley road towards the airfield
  100 s  Jiro throws the paper plane back up past Nahoko

Static layer (PNG): sky, cumulus, far country, the hill with grass texture and flowers, easel, Nahoko's body.
Sprites: nested palette PNGs for anything detailed that moves (aircraft, cloud puff, ox cart, Jiro's parts,
parasol canopy, Nahoko's three head frames) and small paths for flutter, legs and wind.
"""
import base64, io, math, random
from PIL import Image, ImageDraw
from lib import Canvas, hx

NAME = "The Wind Rises"
SIZE = W, H = 320, 180
COLORS = 256

SKY = ["#1f55b5", "#2a67c6", "#3a7dd6", "#4f93e2", "#69a9ea", "#8cc0f0", "#b4d9f5", "#d8edf8"]
CW, CM, CL, CD = "#ffffff", "#dfe6f7", "#b5c5e9", "#95aada"      # cloud: lit, half, shade, base
FAR, MID, NEAR, WOOD, DEEP = "#a3c6e6", "#7fb0c4", "#5f9f8c", "#3f8362", "#1f5a3a"
G = ["#ccee77", "#a3d858", "#7cc246", "#58a83e", "#3d8d3c", "#2b7038"]   # grass, light -> deep
SKIN, SKIND, HAIR, DARK, BROWN = "#f7cba3", "#dd9d7c", "#3b2a30", "#2b2640", "#885533"
LIL, LILM, LILD = "#e7e2f5", "#c2badf", "#998fc3"                # Jiro's lilac suit
RED, YEL, PINK, ROAD = "#ee5544", "#ffdd77", "#ff99bb", "#d9c9a3"

B4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def tone(x, y, t, cols, soft=.5):
    """Pick cols[t] with an ordered-dither seam of relative width `soft` between neighbours."""
    t = max(0, min(len(cols) - 1, t))
    i = int(t)
    f = (t - i - .5) / soft + .5
    if i + 1 < len(cols) and f > (B4[y % 4][x % 4] + .5) / 16:
        i += 1
    return cols[i]


def hill(x):
    """Skyline of the hill. Straight 1-in-3 between x=100 and 156, the stretch Jiro walks."""
    if x < 100:
        return 134.37 + (100 - x) / 3 + .012 * (100 - x) ** 2
    if x <= 156:
        return 115.7 + (156 - x) / 3
    if x <= 190:
        return 110 + .0049 * (190 - x) ** 2
    return 110 + .0011 * (x - 190) ** 2


def cloud(cv, lobes, base, flat=6):
    """Cumulus from circles painted back to front. sh=0 is plain sunlit white; otherwise the lobe turns to
    shade (two dithered tones) where its surface faces more than `sh` away from the light at upper left:
    about -.4 gives a thin crescent of shadow, +.35 a lobe in shade with only a lit cap. Flat dim base."""
    for cx, cy, r, sh in lobes:
        for y in range(int(cy - r), min(base, int(cy + r) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                dx, dy = x + .5 - cx, y + .5 - cy
                if math.hypot(dx, dy) > r:
                    continue
                c = CW
                if sh:
                    c = tone(x, y, (sh + (.5 * dx + .86 * dy) / r) / .5 + .5, [CW, CM, CL], .6)
                b = base - y
                if b <= flat:
                    c = tone(x, y, (flat - b) / flat * 2.2 + (.6 if c != CW else 0), [c, CL, CD], .8)
                cv.set(x, y, c)


def billow(forms, seed):
    """Break each shaded lobe's sunlit edge with three small plain bumps, so the cloud reads as billowing
    cauliflower rather than a pile of balls."""
    r, out = random.Random(seed), []
    for cx, cy, rad, sh in forms:
        out.append((cx, cy, rad, sh))
        for _ in range(3 if sh else 0):
            a = math.radians(r.uniform(175, 320))
            out.append((cx + math.cos(a) * rad * .92, cy + math.sin(a) * rad * .92, rad * r.uniform(.22, .42), 0))
    return out


PAL = {"W": CW, "h": CM, "u": CL, "K": DARK, "H": HAIR, "s": SKIN, "d": SKIND, "g": "#d9f1ff",
       "L": LIL, "l": LILM, "p": LILD, "b": BROWN, "R": RED, "c": SKY[3], "G": G[2], "y": YEL}

NAHOKO = [      # body only; the hat belongs to the head frames below
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".....WWWWWh.....",
    "....WWWWWWWh....",
    "....WWWWWWWWss..",
    "....WWWWWWh.....",
    "....hWWWWWh.....",
    ".....WWWWh......",
    ".....RRRRR......",
    "....WWWWWWh.....",
    "....WWWWWWWh....",
    "...WWWWhWWWh....",
    "...WWWWhWWWWh...",
    "...WWWhWWWWWh...",
    "..WWWWhWWWWWWh..",
    "..WWWWhWWWhWWh..",
    "..WWWhWWWWhWWh..",
    ".WWWWhWWWWhWWWh.",
    ".WWWWhWWWWhWWWh.",
    ".WWWhWWWWhWWWWh.",
    "WWWWhWWWWhWWWWh.",
    ".WWWWWWWWWWWWh..",
    "......ss.ss.....",
    "......ss.ss.....",
    "......WW.WW.....",
    "......bb.bbb....",
]
HAT = [
    ".....WWWWW......",
    "....WWWWWWW.....",
    "....WWWWWWWh....",
    "....RRRRRRRR....",
    "WWWWWWWWWWWWWWh.",
]
HEAD_A = HAT + [    # painting, facing the easel
    ".hhuHHHsssssuu..",
    "....HHHHssKss...",
    "....HHHHsssssd..",
    "....HHHHssss....",
    "....HHHHHsss....",
    ".....HHH.ss.....",
]
HEAD_B = HAT + [    # looking back down the hill
    "..uussssssHHuh..",
    "...ssKssKsHHH...",
    "..dsssssssHHH...",
    "....ssdsssHHH...",
    "....sssssHHHH...",
    ".....ss..HHH....",
]
HEAD_C = [          # looking up at the sky, hat tipped back
    ".....WWWWWW.....",
    ".....WWWWWWh....",
    "....WWWWWWRR....",
    "....WRRRRRWWWWh.",
    "....RWWWWWsss...",
    "WWWWWHHHssKssd..",
    "....HHHHssssss..",
    "....HHHHsssss...",
    "....HHHHHss.....",
    "....HHHH.ss.....",
    ".....HHH.ss.....",
]
EASEL = [
    "....b.....",
    ".WWWWWWWW.",
    ".WccccccW.",
    ".WcWWcccW.",
    ".WccccWcW.",
    ".WccccccW.",
    ".WcGGGccW.",
    ".WGGGGGGW.",
    ".WGGyGGGW.",
    ".WWWWWWWW.",
    "bbbbbbbbbb",
    ".b..b...b.",
    ".b..b...b.",
    ".b..b...b.",
    ".b...b..b.",
    ".b...b..b.",
    ".b...b..b.",
    "b....b...b",
    "b.....b..b",
    "b.....b..b",
]
JIRO = [        # head and torso; arms and legs are separate sprites
    "....WWWWWW....",
    "...WWWWWWWh...",
    "...WWWWWWWh...",
    "...KKKKKKKK...",
    ".hWWWWWWWWWWWh",
    "...KKsssssss..",
    "...KKKggsggs..",
    "...KssgKsgKss.",
    "....sssssss...",
    "....ssssdds...",
    ".....sssss....",
    "......sss.....",
    "....LLLWKWl...",
    "...LLLLlWKll..",
    "...LLLLLlKLl..",
    "...LLLLLlKLl..",
    "...LLLLLLlLl..",
    "...LLLLLLlLl..",
    "...LLLLLLlLl..",
    "...LLpLLLlLl..",
    "...LLLLLLlLl..",
    "...LLLLLLLLl..",
    "...lLLLLLLlp..",
]
LEGS_A = [
    "....LLLLllp...",
    "....LLLlllp...",
    "....LLL.llp...",
    "....LLL.llp...",
    "....LLL.llp...",
    "....LLL.llp...",
    "....LLL.llp...",
    "....LLL.llp...",
    "....LLL.llp...",
    "....LLL.llp...",
    "....LLL.llp...",
    "....LLL.llp...",
    "....LLL.llp...",
    "....bbb.bbb...",
    "....bbbbbbbb..",
]
LEGS_B = [
    "....LLLLllp...",
    "....LLLLllp...",
    "....LLLlllp...",
    "...LLLl.llp...",
    "...LLL..lllp..",
    "...LLL...llp..",
    "..LLLl...llp..",
    "..LLL....lllp.",
    "..LLL.....llp.",
    "..LLL.....llp.",
    "..LLL.....llp.",
    ".LLL......llp.",
    ".LLL......llp.",
    ".bbb......bbb.",
    ".bbbb.....bbbb",
]
LEGS_C = [r if i < 3 else r[:7].replace("l", "p").replace("L", "l") + r[7:].replace("l", "L").replace("p", "l")
          for i, r in enumerate(LEGS_B)]          # the other stride: near leg forward
ARMS_IDLE = [   # near hand holding the hat on, far hand at his side
    "..ss..........",
    "..ss..........",
    ".LL...........",
    ".LL...........",
    ".LL...........",
    "LL............",
    "LL............",
    "LL............",
    "LLp...........",
    "LLLp..........",
    ".LLLp.........",
    "..LLLp........",
    "...LLp.....p..",
    "...........lp.",
    "...........lp.",
    "...........lp.",
    "...........lp.",
    "...........lp.",
    "...........lp.",
    "...........lp.",
    "...........s..",
]
ARMS_WAVE = (["ss............"] * 2 + ["LL............"] * 10 +      # near arm straight up (the hat is a path)
             ARMS_IDLE[8:])
ARMS_HOLD = [   # both hands on the parasol pole (the pole is column 15)
    "..............ss",
    "...........LLLss",
    "........LLLLLp..",
    "......LLLLLp....",
    "......LLLp......",
    "..............ss",
    "..........llllss",
    "..........lpp...",
]


PAPER = [       # the paper plane, nose to the left
    ".........WWWW",
    "......WWWWWWh",
    "...WWWWWWWhh.",
    "WWWWWWWWhh...",
    "...uuuuuu....",
    ".....uuu.....",
]


CART = [        # the prototype on its way to the airfield: fuselage on a cart, two oxen, drover (legs are sprites)
    ".hh.............................................",
    ".hhu......gg..................W...........W..yyy",
    ".WWWWWWWWWWWWWWWWK...........HH..........bb...s.",
    "..hhhRRhhhhhhhhhhKK..bbbbbbbbHHH.ddddddddbbb.WWW",
    ".....uuuuhhhuuuu.....HHHHHHHHHHHbbbbbbbbbbbb.WWW",
    "..........hhu........HHHHHHHHH...bbbbbbbbb...WWW",
    "bbbbbbbbbbbbbbbbbbbbbHHHHHHHH....bbbbbbbb....HHH",
    "....HHH.......HHH...............................",
    "...HHbHH.....HHbHH..............................",
    "....HHH.......HHH...............................",
]


def stamp(cv, rows, x0, y0):
    assert len({len(r) for r in rows}) == 1, rows
    cv.paint(rows, PAL, x0, y0)


def tag(im, x, y, cls=""):
    """RGBA image -> small palette PNG with transparency -> an <image> element."""
    data = list(im.getdata())
    used = sorted({p[:3] for p in data if p[3]})
    q = Image.new("P", im.size, 0)
    q.putpalette([0, 0, 0] + [v for c in used for v in c])
    q.putdata([used.index(p[:3]) + 1 if p[3] else 0 for p in data])
    buf = io.BytesIO()
    q.save(buf, "PNG", optimize=True, transparency=0)
    c = f" class='{cls}'" if cls else ""
    return (f"<image{c} x='{x}' y='{y}' "
            f"href='data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}'/>")


def art(rows, x, y, cls=""):
    """ASCII art -> <image>."""
    assert len({len(r) for r in rows}) == 1, rows
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    im.putdata([hx(PAL[ch]) + (255,) if ch in PAL else (0, 0, 0, 0) for r in rows for ch in r])
    return tag(im, x, y, cls)


def puff(lobes, w, h, x, y, cls):
    """A small drifting cloud, drawn with the same cloud() as the static ones."""
    cv = Canvas(w, h)
    cloud(cv, lobes, h, 3)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    im.putdata([p + (255,) if p != (255, 0, 255) else (0, 0, 0, 0) for row in cv.px for p in row])
    return tag(im, x, y, cls)


# ---- aircraft: a tiny orthographic renderer (flat-shaded polygons, discs and lines, painter-sorted)
LIGHT = (-.35, -.3, .88)


def rgba(c):
    return hx(c) + (255,)


SIL = [rgba(c) for c in ("#f4f6fb", "#cdd6ea", "#98a8cc")]       # the prototype's bare aluminium
CRM = [rgba(c) for c in ("#fffaf0", "#fbf0d8", "#efdfc0")]       # Caproni's linen wings
HUL = [rgba(c) for c in (CW, CM, CL)]
INK, STRUT = rgba("#3a4160"), rgba("#8a7f96")


def view(az, el, pitch=0):
    """Camera at azimuth/elevation (degrees) round an aircraft with nose +x, right wing +y, up +z."""
    az, el, pitch = (math.radians(a) for a in (az, el, pitch))
    c = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
    r = (-math.sin(az), math.cos(az), 0)
    u = (c[1] * r[2] - c[2] * r[1], c[2] * r[0] - c[0] * r[2], c[0] * r[1] - c[1] * r[0])

    def att(p):
        return (p[0] * math.cos(pitch) - p[2] * math.sin(pitch), p[1], p[0] * math.sin(pitch) + p[2] * math.cos(pitch))

    def dot(a, b):
        return sum(i * j for i, j in zip(a, b))

    return (lambda p: (dot(att(p), r), -dot(att(p), u), -dot(att(p), c))), att, c


def render(parts, cam, s, size, org, outline, mark=(0, 0, 0)):
    """parts: ('poly', pts, tones, None, bias) | ('disc', p, r, colour, bias) | ('line', a, b, colour, bias)."""
    f, att, c = cam
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)

    def P(p):
        return org[0] + f(p)[0] * s, org[1] + f(p)[1] * s

    items = []
    for kind, a, b, col, bias in parts:
        if kind == "poly":
            p0, p1, p2 = (att(p) for p in a[:3])
            e1, e2 = [j - i for i, j in zip(p0, p1)], [j - i for i, j in zip(p0, p2)]
            n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
            ln = math.sqrt(sum(i * i for i in n)) or 1
            sg = -1 if sum(i * j for i, j in zip(n, c)) < 0 else 1
            k = sg * sum(i * j for i, j in zip(n, LIGHT)) / ln
            items.append((sum(f(p)[2] for p in a) / len(a) + bias, kind, [P(p) for p in a],
                          b[0] if k > .45 else b[1] if k > -.1 else b[2]))
        elif kind == "disc":
            items.append((f(a)[2] + bias, kind, P(a), b * s, col))
        else:
            items.append(((f(a)[2] + f(b)[2]) / 2 + bias, kind, P(a), P(b), col))
    for it in sorted(items, key=lambda i: -i[0]):
        if it[1] == "poly":
            dr.polygon(it[2], fill=it[3])
        elif it[1] == "disc":
            (x, y), r = it[2], it[3]
            dr.ellipse((x - r, y - r, x + r, y + r), fill=it[4])
        else:
            dr.line((it[2], it[3]), fill=it[4], width=1)
    px = im.load()
    w, h = size
    for x, y in [(x, y) for y in range(h) for x in range(w) if not px[x, y][3] and any(
            0 <= x + i < w and 0 <= y + j < h and px[x + i, y + j][3] for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))]:
        px[x, y] = outline
    box = im.getbbox()
    out = im.crop(box)
    out.info["mark"] = round(P(mark)[0]) - box[0], round(P(mark)[1]) - box[1]
    return out


def fighter():
    """The silver prototype: inverted gull wing, spatted wheels under the kink, radial cowl."""
    parts = []
    st = [(3.3, .66), (2.4, .7), (1.2, .64), (0, .56), (-1.2, .44), (-2.4, .32), (-3.4, .22), (-4.2, .12)]
    for (x0, r0), (x1, r1) in zip(st, st[1:]):
        for i in range(8):
            parts.append(("disc", (x0 + (x1 - x0) * i / 8, 0, 0), r0 + (r1 - r0) * i / 8, SIL[1], 0))
    parts += [("line", (2.4, 0, .62), (-3.6, 0, .2), SIL[0], -1), ("disc", (3.35, 0, 0), .62, INK, -.01),
              ("disc", (3.6, 0, 0), .2, SIL[0], -.3), ("disc", (.2, 0, .6), .32, INK, 0),
              ("poly", [(-3.0, 0, .2), (-3.7, 0, 1.4), (-4.25, 0, 1.35), (-4.35, 0, .1)], SIL, None, 0)]
    for sg in (1, -1):
        sec = [(.5, -.3, 1.4, -1.1), (1.7, -1.15, 1.35, -1.05), (3.6, -.3, 1.05, -.8), (5.0, .35, .6, -.5), (5.6, .6, .15, -.25)]
        for (y0, z0, a0, b0), (y1, z1, a1, b1) in zip(sec, sec[1:]):
            parts.append(("poly", [(a0, sg * y0, z0), (a1, sg * y1, z1), (b1, sg * y1, z1), (b0, sg * y0, z0)], SIL, None, 0))
        parts += [("disc", (.2, sg * 4.1, 0), .45, rgba(RED), -.5),
                  ("poly", [(1, sg * 1.7, -1.1), (.1, sg * 1.7, -1.1), (.2, sg * 1.7, -2), (.8, sg * 1.7, -2)],
                   [SIL[1], SIL[1], SIL[2]], None, 0),
                  ("disc", (.5, sg * 1.7, -2), .26, INK, 0),
                  ("poly", [(-3.3, 0, .25), (-3.5, sg * 1.8, .25), (-4, sg * 1.8, .25), (-4.15, 0, .25)], SIL, None, 0)]
    return render(parts, view(-33, 2, 7), 5.6, (90, 60), (45, 30), rgba("#46527a"))


def caproni():
    """Caproni's dream: a white boat hull under three stacks of three wings, seen from a little above so that
    every wing reads, with the man himself standing on the front top wing (his waving arm is a sprite).
    Returns the image and the position of his feet within it."""
    parts = []
    L, R, N, w, top, bot = -12, 9, 13.5, 1.5, 1.4, -1.6
    for sg in (1, -1):
        parts += [("poly", [(L, sg * w * .6, top), (R, sg * w, top), (N, 0, top + .6), (N, 0, bot + 1.2), (R, sg * w, bot),
                            (L, sg * w * .6, bot + .8)], HUL, None, 0),
                  ("poly", [(L, sg * w * .6, bot + .8), (R, sg * w, bot), (N, 0, bot + 1.2), (N, 0, bot + 1.9), (R, sg * w, bot + .8),
                            (L, sg * w * .6, bot + 1.5)], [rgba(RED)] * 3, None, -.3),
                  ("poly", [(3, sg * 10, -.2), (-3, sg * 10, -.2), (-3, sg * 10, -1.4), (2, sg * 10, -1.4)], HUL, None, 0),
                  ("line", (0, sg * 10, -.2), (0, sg * 10, 1.6), STRUT, 0)]
        for i in range(7):
            x = -7 + i * 2.2
            y = sg * w * (.6 + .4 * (x - L) / (R - L))
            parts.append(("line", (x, y, .6), (x + .5, y, .6), INK, -.5))
    parts += [("poly", [(L, -w * .6, top), (R, -w, top), (N, 0, top + .6), (R, w, top), (L, w * .6, top)], HUL, None, 0),
              ("poly", [(L, -w * .6, bot + .8), (R, -w, bot), (N, 0, bot + 1.2), (R, w, bot), (L, w * .6, bot + .8)], HUL, None, 0)]
    for x0 in (8.5, 0, -8.5):
        for z in (1.6, 4.8, 8):
            parts += [("poly", [(x0 + 1.5, -14, z), (x0 + 1.5, 14, z), (x0 - 1.5, 14, z), (x0 - 1.5, -14, z)], CRM, None, 0),
                      ("line", (x0 + 1.5, -14, z), (x0 + 1.5, 14, z), rgba("#c9b48c"), -.2)]
        for y in (-12, -4, 4, 12):
            parts.append(("line", (x0, y, 1.6), (x0, y, 8), STRUT, 0))
        for y in (-8, 8):
            parts.append(("disc", (x0 + .3, y, 4.8), .75, INK, -.3))
    plane = render(parts, view(75, 8), 3.1, (170, 100), (85, 60), rgba("#5a6490"), (8.5, 2, 8))
    im = Image.new("RGBA", (plane.width, plane.height + 8), (0, 0, 0, 0))
    im.paste(plane, (0, 8))
    mx, my = plane.info["mark"][0], plane.info["mark"][1] + 8
    ImageDraw.Draw(im).rectangle((mx, my - 5, mx + 1, my - 1), fill=INK)          # dark suit
    ImageDraw.Draw(im).rectangle((mx, my - 7, mx + 1, my - 6), fill=rgba(SKIN))
    return im, mx, my


GX = 300      # the wind group lives in coordinates shifted right by this, so nothing in it ever has a negative x


def gust():
    """One period (200px) of wind: a wide and a narrow ragged, slanted band, each a stack of 2px rows.
    Drawn twice: thick and faint as a lighter patch of grass, then thin and dashed as bent blades catching the light."""
    r, d = random.Random(3), ""
    for x0, k in [(GX, 1), (GX + 112, .45)]:
        px = None
        for i in range(25):
            y = 108 + 2 * i
            x = x0 + round(k * (.5 * (y - 108) + 5 * math.sin(y * .19) + r.uniform(-1.5, 1.5)))
            w = round(k * (21 + 8 * math.sin(y * .31 + 1) + r.uniform(-2, 2)))
            d += (f"M{x} {y + 1}" if px is None else f"m{x - px} 2") + f"h{w}"
            px = x + w
    return d


def hillclip():
    """The grass below the skyline as a CSS clip-path path() (T3 refuses any url(#id) in a theme, so no
    <clipPath>). The moving wind bands are clipped to it, so they never spill over the sky or the figures."""
    xs = [96, 100, 156, 164, 172, 181, 190, 216, 242, 268, 294, 320]
    return f"M{GX + 320} 157H{GX + 96}" + "".join(f"L{GX + x} {hill(x) + 2.5:.4g}" for x in xs) + "z"


def canopy():
    """The parasol canopy: a flattened dome of five panels with a scalloped edge, two rows of finial on top."""
    rows = ["." * 19 + "b" + "." * 18] * 2
    for y in range(11):
        row = ""
        for x in range(38):
            u = (x + .5 - 19) / 19
            ph = (x % 7.6) / 7.6
            inside = 9.6 * (1 - math.sqrt(1 - u * u)) <= y + .5 <= 10.9 - 2.2 * math.sin(math.pi * ph)
            panel = int(x / 7.6)
            row += ("u" if panel == 4 else "h" if panel == 3 or (ph < .14 and panel) else "W") if inside else "."
        rows.append(row)
    return rows


JX, JY = 118, 88          # Jiro's sprite origin at his spot on the slope (feet at x=125, y=126)
NX, NY = 175, 76          # Nahoko's sprite origin (feet at x=183, y=111)
EX, EY = 193, 91          # easel
OX, OY = -50, 139         # ox cart, parked off the left edge; its wheels run on the road at y=149
PX = 169                  # parasol pole column; it stands in rows 64..112


def larch(cv, x, base, h):
    for i in range(h):
        n = 1 + i * 4 // h + (i % 3 == 2)
        cv.rect(x - n, base - h + i, 2 * n + 1, 1, WOOD)
        cv.rect(x + 1, base - h + i, n, 1, DEEP)


def draw():
    cv = Canvas(W, H)
    r = random.Random(7)
    # sky: eight bands, deep cobalt down to a pale horizon
    for y in range(H):
        for x in range(W):
            cv.set(x, y, tone(x, y, (min(y, 139) / 140) ** 1.45 * 7.6, SKY, .3))
    # cumulus: the tower on the left, a broad cloud high in the middle, a bank behind the hill
    cloud(cv, billow([(58, 44, 17, 0), (48, 70, 28, 0), (40, 100, 40, 0), (82, 104, 26, 0),
                      (57, 33, 14, -.35), (78, 45, 10, -.2), (36, 47, 14, -.45), (88, 63, 13, -.2), (60, 58, 17, -.4),
                      (20, 68, 16, -.5), (102, 86, 13, .25), (76, 84, 18, -.35), (40, 82, 20, -.45),
                      (4, 92, 17, -.5), (108, 108, 11, .3), (86, 110, 15, -.2), (56, 108, 19, -.4),
                      (22, 110, 19, -.5)], 4), 132, 10)
    cloud(cv, billow([(150, 38, 12, 0), (170, 36, 14, 0), (136, 42, 8, 0), (160, 28, 10, -.4), (190, 40, 10, .3),
                      (178, 27, 8, -.25), (204, 43, 6, .3)], 5), 46, 5)
    cloud(cv, billow([(296, 100, 26, 0), (290, 68, 12, -.4), (306, 80, 14, -.25), (274, 82, 12, -.45),
                      (286, 93, 13, -.3), (318, 98, 12, -.2), (262, 102, 10, -.45)], 6), 124, 8)
    # far country on the left: two ranges, a lake, the road to the airfield
    cv.ridge(131, [(5, .028, 1), (2, .09, 0)], FAR, 3, 0)
    cv.ridge(138, [(4, .04, 2.5), (1.5, .13, 0)], MID, 5, 0)
    cv.rect(0, 144, 80, 2, SKY[6])
    cv.ridge(147, [(1, .05, .6), (.6, .17, 2)], NEAR, 7, 0)
    cv.rect(0, 149, 90, 1, ROAD)
    cv.ridge(158, [(3, .07, 1.2), (1.5, .3, 0)], WOOD, 9, 1)
    for x, base, h in [(279, 131, 15), (289, 131, 23), (299, 131, 18), (309, 131, 26), (318, 131, 20)]:
        larch(cv, x, base, h)                  # behind the right shoulder
    # the hill: lit rim, then tones deepening with depth and towards the right, tufts and flowers
    for x in range(W):
        y0 = int(round(hill(x)))
        for y in range(y0, H):
            cv.set(x, y, (G[0] if x < 215 else G[1]) if y - y0 < 2 else
                   tone(x, y, (y - y0) / 26 + max(0, x - 120) / 120 + .9, G, .7))
        if x > 52 and x * 7 % 5 < 2 and x % 11:
            cv.set(x, y0 - 1, G[0] if x < 215 else G[1])      # grass tips break the skyline
    for _ in range(170):                       # tufts: a light tick with a dark foot
        x, y = r.randrange(40, W - 1), r.randrange(112, 170)
        if y > hill(x) + 5:
            i = G.index("#%02x%02x%02x" % cv.get(x, y))
            cv.set(x, y - 1, G[max(0, i - 1)])
            cv.set(x + 1, y - 1, G[max(0, i - 1)])
            cv.set(x, y, G[min(5, i + 1)])
    for cx, cy, n in [(140, 132, 9), (206, 124, 7), (238, 138, 9), (112, 150, 8), (176, 146, 8), (282, 132, 6)]:
        for _ in range(n):                     # flower drifts
            x, y = cx + int(r.gauss(0, 9)), cy + int(r.gauss(0, 4))
            if y > hill(x) + 4:
                cv.set(x, y, r.choice([CW, CW, CW, YEL, PINK]))
    larch(cv, 81, 153, 25)                     # a stand at the hill's foot; the ox cart passes behind it
    larch(cv, 89, 150, 19)
    for x in range(W):                         # tall blades along the bottom edge
        top = 162 - (x * 5 % 7) - 3 * (x % 9 == 0) + int(2 * math.sin(x * .13))
        for y in range(max(top, round(hill(x)) + 6), H):
            cv.set(x, y, G[4] if x % 13 == 3 and y < top + 6 else DEEP)
    for x, y in [(96, 152), (131, 157), (150, 150), (187, 155), (214, 151), (243, 156), (262, 149), (301, 153)]:
        if y > hill(x) + 6:                    # a few near flowers
            cv.rect(x - 1, y, 3, 1, CW)
            cv.rect(x, y - 1, 1, 3, CW)
            cv.set(x, y, YEL)
    stamp(cv, EASEL, EX, EY)
    stamp(cv, NAHOKO, NX, NY)
    return cv


def build_sprites():
    s = ""
    cv = draw()
    # Caproni's plane, far and slow (parked off the right edge), then a cloud puff, then the fighter
    cap, mx, my = caproni()
    mx, my = mx + 330, my + 1
    s += (f"<g class='wr-c'><g class='wr-cb'>{tag(cap, 330, 1)}"
          f"<path class='wr-t' stroke='#346' d='M{mx - 1} {my - 5}.5h1m-2-1h1m-3-1h3'/>"
          f"<path class='wr-t wr-u' stroke='#346' d='M{mx + 2} {my - 5}.5h1m0-1h1m-1-1h3'/></g></g>")
    s += puff([(7, 7, 5, 0), (15, 6, 6, -.25), (23, 8, 4, .35)], 28, 10, 330, 22, "wr-d")
    s += f"<g class='wr-f'>{tag(fighter(), -80, 26, 'wr-fy')}</g>"
    # the ox cart on the valley road, inside a viewport that ends where the larches at the hill's foot begin
    legs = "<path class='wr-t wr-o'{} d='M{}.5 {}{}'/>"
    s += (f"<svg width='78' height='{H}'><g class='wr-ox' stroke='#323'>{art(CART, OX, OY)}"
          + legs.format("", OX + 21, OY + 7, "v3m2-3v3m3-3v3m2-3v3m5-3v3m2-3v3m3-3v3m2-3v3m5-3v3m2-3v3")
          + legs.format(" style='animation-delay:-.48s'", OX + 22, OY + 7, "v3m2-3v3m1-3v3m2-3v3m7-3v3m2-3v3m1-3v3m2-3v3m7-3v3")
          + "</g></svg>")
    # wind: ragged bands of lighter, combed grass sweeping left, clipped to the hill. The unpainted corner
    # path pins the clipped group's bounding box at 0,0, so the clip path means the same thing whichever
    # reference box the browser uses.
    s += (f"<g class='wr-h' transform='translate(-{GX})'><path fill='none' d='M0 0h1v1'/><g class='wr-w' stroke='#ce7'>"
          f"<g id='wr-g'><g stroke-width='2.2' opacity='.3'><path id='wr-q' d='{gust()}'/></g>"
          "<use href='#wr-q' y='-.5' stroke-dasharray='2 3 1 4' opacity='.85'/></g>"
          "<use href='#wr-g' x='200'/><use href='#wr-g' x='400'/></g></g>")
    # the paper plane, parked off the right edge. It glides down the wind and ends tucked behind Jiro's hat
    # and raised hand (it is drawn before him), where it is switched off; later he throws it back the same
    # way, mirrored, up past Nahoko and out of the picture.
    s += f"<g class='wr-pp'><g class='wr-py'>{art(PAPER, JX + 223, JY - 72, 'wr-pb')}</g></g>"
    # parasol: flight/carry > tumble > nested 1px sways
    s += (f"<g class='wr-pf'><g class='wr-pr' stroke='#853'><path d='M{PX}.5 96v17'/>"
          f"<g class='wr-s'><path d='M{PX}.5 80v16'/>"
          f"<g class='wr-s' style='animation-delay:-.48s'><path d='M{PX}.5 64v16'/>{art(canopy(), PX - 19, 53)}</g></g></g></g>")
    # Nahoko: three heads (painting, looking back, looking up), ribbon tails, hem, brush
    s += (f"<g class='wr-ha'>{art(HEAD_A, NX, NY)}<path class='wr-t' fill='#3b2a30' d='M{NX + 3} {NY + 8}h1v2h-1z'/>"
          f"<path class='wr-bl' fill='#f7cba3' d='M{NX + 10} {NY + 6}h1v1h-1z'/></g>"
          f"<g class='wr-hb'>{art(HEAD_B, NX, NY)}<path class='wr-bl' fill='#f7cba3' d='M{NX + 5} {NY + 6}h1v1h-1zm3 0h1v1h-1z'/></g>"
          f"<g class='wr-hc'>{art(HEAD_C, NX, NY)}<path class='wr-bl' fill='#f7cba3' d='M{NX + 10} {NY + 5}h1v1h-1z'/></g>"
          + f"<path stroke='#e54' d='M{NX + 1} {NY + 3}.5h3'/><path class='wr-t' stroke='#e54' d='M{NX - 3} {NY + 2}.5h4'/>"
          f"<path class='wr-t wr-u' stroke='#e54' d='M{NX - 3} {NY + 4}.5h3'/>"
          f"<path class='wr-t wr-u' fill='#fff' d='M{NX - 1} {NY + 28}h2v1h-2zm-1 1h1v1h-1z'/>"
          f"<path class='wr-b' stroke='#853' d='M{NX + 14} {NY + 13}.5h4'/>")
    # Jiro: walk > flip > torso, legs (standing / stride, passing, other stride, passing), arms (hat / pole / wave)
    legs = art(LEGS_A, JX, JY + 23).replace("<image", "<image id='wr-l'")
    # The patch is the hat's footprint grown by a pixel (and it repaints the row of face under the brim), so
    # that its own soft edge lies over matching colour and no fringe of the covered hat shows round it.
    bare = Image.new("RGBA", (15, 7), (0, 0, 0, 0))
    hat = {(x, y) for y in range(5) for x in range(14) if JIRO[y][x] != "."}
    for y in range(-1, 6):
        for x in range(-1, 14):              # (not past the brim on the right: the parasol pole sways there)
            if y > 2 and 6 - y <= x <= 4 + y:
                c = rgba(DARK)                                              # his hair
            elif y == 5 and 0 <= x < 14 and JIRO[5][x] in PAL:
                c = rgba(PAL[JIRO[5][x]])
            elif any((x + i, y + j) in hat for i in (-1, 0, 1) for j in (-1, 0, 1)):
                c = cv.get(JX + 36 + x, JY - 12 + y) + (255,)               # the sky where he stands to wave
            else:
                continue
            bare.putpixel((x + 1, y + 1), c)
    s += (f"<g class='wr-jw'><g class='wr-jf'>{art(JIRO, JX, JY)}<path class='wr-bl' fill='#d9f1ff' d='M{JX + 7} {JY + 7}h1v1h-1zm3 0h1v1h-1z'/>"
          f"<g class='wr-nw'>{legs}</g>"
          f"<g class='wr-wk'><use class='wr-la' href='#wr-l'/>{art(LEGS_B, JX, JY + 23, 'wr-lb')}"
          f"{art(LEGS_C, JX, JY + 23, 'wr-lb wr-lc')}</g>"
          f"<g class='wr-ai'>{art(ARMS_IDLE, JX, JY + 1)}<path class='wr-t' fill='#2b2640' d='M{JX + 7} {JY + 16}h1v1h-1z'/></g>"
          f"<path class='wr-t wr-u' fill='#c2badf' d='M{JX + 2} {JY + 21}h1v2h-1z'/>"
          f"{art(ARMS_HOLD, JX, JY + 9, 'wr-ah')}"
          # waving his hat at Caproni from under the parasol: a patch of the sky behind him there plus his
          # hair hides the hat on his head, the raised arm replaces the idle one, the hat sways in his hand
          f"<g class='wr-aw'>{tag(bare, JX - 1, JY - 1)}{art(ARMS_WAVE, JX, JY - 3)}"
          f"<g class='wr-hw'><path fill='#fff' d='M{JX - 2} {JY - 7}h5v1h1v1h-7v-1h1zm-3 3h12v1h-12z'/>"
          f"<path stroke='#224' d='M{JX - 3} {JY - 5}.5h7'/></g></g></g></g>")
    # a few blown leaves and petals (parked off the right edge)
    s += ("<g class='wr-lf'><g class='wr-ly'><path stroke='#ce7' d='M326 92.5h2m15-13h1m24 21h2m8-33h1m19 16h2'/>"
          "<path stroke='#fff' d='M335 104.5h1m32-28h1m25 14h1'/></g></g>")
    return s


SPRITES = build_sprites()
# Every style change below lands on one shared 0.12 s grid (step lengths, delays and keyframe times are all
# multiples of it; 0.1% of the 120 s story loop is one tick), so the image is re-rasterized at most about
# eight times a second however many things are moving.
ST = "animation-timing-function:steps"
CSS = (
    # ambient: wind bands, parasol sway, flutter, blinks, brush, cloud puff
    f".wr-h{{clip-path:path('{hillclip()}')}}"
    ".wr-w{animation:wr-w 12s -4.92s steps(100) infinite}@keyframes wr-w{to{translate:-200px}}"
    ".wr-s{animation:wr-s 3.36s steps(1) infinite}@keyframes wr-s{50%{translate:-1px}}"
    ".wr-t{animation:wr-t .72s steps(1) infinite}.wr-u{animation-delay:-.36s}@keyframes wr-t{50%{opacity:0}}"
    ".wr-bl{opacity:0;animation:wr-bl 6s steps(1) infinite}@keyframes wr-bl{96%{opacity:1}}"
    ".wr-b{animation:wr-b 2.4s steps(1) infinite}@keyframes wr-b{30%{translate:0 -1px}60%{translate:1px}}"
    ".wr-d{animation:wr-d 364.8s -149.76s steps(380) infinite}@keyframes wr-d{to{translate:-380px}}"
    # crossings: Caproni, the fighter, blown leaves, the paper plane, the ox cart
    ".wr-c{animation:wr-c 120s -63.96s steps(1000) infinite}@keyframes wr-c{to{translate:-1000px}}"
    ".wr-cb{animation:wr-cb 7.2s steps(1) infinite}"
    "@keyframes wr-cb{50%{translate:0 1px}}"
    # (x and y step separately, so every position is a whole pixel)
    ".wr-f{animation:wr-f 120s -101.4s steps(1000) infinite}@keyframes wr-f{to{translate:2000px}}"
    ".wr-fy{animation:wr-fy 120s -101.4s steps(50) infinite}@keyframes wr-fy{to{translate:0 -50px}}"
    ".wr-lf{animation:wr-lf 60s -23.76s steps(500) infinite}@keyframes wr-lf{to{translate:-1000px}}"
    ".wr-ly{animation:wr-ly 60s -23.76s steps(125) infinite}@keyframes wr-ly{to{translate:0 125px}}"
    # the paper plane: 6px along and 2px down every 0.36 s, the slope of the hill
    ".wr-pp{animation:wr-pp 120s -109.92s steps(111) infinite}"
    "@keyframes wr-pp{11.1%,75%{translate:-222px;opacity:1}11.2%,74.9%{translate:-222px;opacity:0}86.1%,to{translate:0}}"
    ".wr-py{animation:wr-py 120s -109.92s steps(37) infinite}@keyframes wr-py{11.1%,75%{translate:0 74px}86.1%,to{translate:0}}"
    f".wr-pb{{transform-origin:{JX + 229}.5px 0;animation:wr-cb 2.4s steps(1) infinite,wr-pm 120s -109.92s steps(1) infinite}}"
    "@keyframes wr-pm{50%{scale:-1 1}}"
    # the ox cart: 127px along the road in 0.48 s steps, then out of sight until the next loop
    ".wr-ox{animation:wr-ox 120s -22.08s steps(127) infinite}@keyframes wr-ox{50.8%,to{translate:127px}}"
    ".wr-o{animation-duration:.96s}"
    # Jiro's walk cycle: stride, passing, other stride, passing
    ".wr-la{animation:wr-t .48s -.24s steps(1) infinite}.wr-lb{animation:wr-lb .96s steps(1) infinite}"
    ".wr-lc{animation-delay:-.48s}@keyframes wr-lb{25%{opacity:0}}"
    # the story loop
    ".wr-pf,.wr-pr,.wr-jw,.wr-jf,.wr-nw,.wr-wk,.wr-ai,.wr-ah,.wr-ha,.wr-hb,.wr-hc,.wr-aw{animation:120s steps(1) infinite}"
    f".wr-pf{{animation-name:wr-pf}}.wr-pr{{animation-name:wr-pr;transform-origin:{PX}.5px 62.5px}}"
    f".wr-jw{{animation-name:wr-jw}}.wr-jf{{animation-name:wr-jf;transform-origin:{JX + 7}px 0}}"
    ".wr-nw{animation-name:wr-nw}.wr-wk{animation-name:wr-wk;opacity:0}"
    ".wr-ai{animation-name:wr-ai}.wr-ah{animation-name:wr-ah;opacity:0}.wr-aw{animation-name:wr-aw;opacity:0}"
    ".wr-hw{animation:wr-hw .96s steps(1) infinite}@keyframes wr-hw{50%{translate:2px}}"
    ".wr-ha{animation-name:wr-ha}.wr-hb{animation-name:wr-hb;opacity:0}.wr-hc{animation-name:wr-hc;opacity:0}"
    # parasol: lifts off, tumbles to Jiro (quarter turns), is carried up in step with his walk, planted
    f"@keyframes wr-pf{{38%{{translate:0;{ST}(4)}}38.8%{{translate:-8px -12px;{ST}(7)}}"
    f"40.2%,43%{{translate:-36px 9px;{ST}(12)}}47.8%{{translate:0 -3px}}48.3%{{translate:0}}}}"
    f"@keyframes wr-pr{{38.6%{{rotate:0deg;{ST}(8)}}40.2%,to{{rotate:-720deg}}}}"
    # Jiro: up the slope (3px along, 1px up per stride), wait under the parasol, turn, back down, turn
    f"@keyframes wr-jw{{43%{{translate:0;{ST}(12)}}47.8%{{translate:36px -12px}}"
    f"75%{{translate:36px -12px;{ST}(12)}}79.8%{{translate:0}}}}"
    "@keyframes wr-jf{75%{scale:-1 1}80.3%{scale:1}}"
    "@keyframes wr-nw{43%,75%{opacity:0}47.8%,79.8%{opacity:1}}@keyframes wr-wk{43%,75%{opacity:1}47.8%,79.8%{opacity:0}}"
    "@keyframes wr-ai{39.4%,56.7%{opacity:0}48.3%,68.3%{opacity:1}}@keyframes wr-ah{39.4%{opacity:1}48.3%{opacity:0}}"
    "@keyframes wr-aw{56.7%{opacity:1}68.3%{opacity:0}}"
    # Nahoko: looks back while he brings the parasol, up at Caproni's plane, up again at the paper plane
    "@keyframes wr-ha{38.6%,55%,87.5%{opacity:0}54%,70%,92.5%{opacity:1}}"
    "@keyframes wr-hb{38.6%{opacity:1}54%{opacity:0}}@keyframes wr-hc{55%,87.5%{opacity:1}70%,92.5%{opacity:0}}"
)
THEME = {"canvas": "#0d1b33", "accent": "#bfe86a",
         "position": "center 30%",   # wide panes crop vertically: keep Caproni's plane in at the top (see wide.png)
         "colors": {"sidebar": "#0b1830", "sidebarRowSelected": "#1c3a6b", "sidebarBorder": "#1e3560",
                    "surface": "#12264a", "border": "#27406e", "textMuted": "#b4c3de"}}
