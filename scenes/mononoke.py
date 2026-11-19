"""Princess Mononoke: a day and a night at the Forest Spirit's pool, deep in the ancient cedar forest.

The chat column covers the middle of the picture (about x 122-198), so the cast stands to the sides:
San sits astride Moro under the left cedar, Ashitaka waits on Yakul under the right one with one
of Moro's children lying at his feet and the other sitting behind her, and the middle holds the pool and the deeper forest. By day the Forest Spirit walks out
onto the water and stands just right of the column. At dusk the light warms and fails, he fades,
and the Nightwalker rises behind him where he stood and wades slowly left across the pool under the
stars. At dawn the giant sinks beside the moon and the Forest Spirit is standing on the pool again.

Everything static is painted once, in daylight colours. Night is two multiply layers that step in
at dusk: a rect over the sky, and NIGHT, a flat image the exact shape of the land, drawn over the
land. Whatever sits between them (stars, moon, Nightwalker) or above them (kodama, the apes' eyes,
fireflies) keeps its own light.

Layers, back to front (320x180):
  base PNG   day sky, clouds, far mountains, haze
  sprites    night sky tint, stars and the rising moon, the Nightwalker (alpha PNG)
  mid PNG    conifer ridges, far trunks, the pool and its reflections   (transparent above the trees)
  sprites    water glints, the Forest Spirit and his reflection
  fg PNG     canopy, the great cedars, moss, roots, ferns, near bank, Ashitaka on Yakul, Moro's children,
             the apes' shapes, Moro's legs
  sprites    Moro (tails, breathing body, two heads) and San (blink, cape hem, mask), sun shafts, NIGHT, the warm dusk/dawn
             wash, then what the night does not dim: kodama, Ashitaka's cursed arm, the apes' eyes
             and fireflies after dark
Depth rule: water effects come straight after the pool, and anything nearer than a moving sprite is
in a later layer than that sprite.

One 220 s cycle (1% = 2.2 s):
   0- 7%  day: the Forest Spirit walks out from behind the right cedar
   7-26%  he stands on the water, sprouts at his hooves
  22-32%  dusk: a warm wash peaks at 26%, night steps in from 25%; he fades 26-29% while the
          Nightwalker rises behind him 26-33% and the moon climbs out of the trees; San pulls her
          mask down over her face (26-40%)
  33-68%  night: the Nightwalker wades left across the pool, a pixel a step
  68-79%  dawn: he sinks with his head beside the moon, night steps out 71-78%, the warm wash peaks at 76%,
          and the Forest Spirit fades back in 76-79%, standing where he stood
  82-89%  he turns and walks off behind the cedar; midday is quiet until the loop restarts
Ambient loops on their own periods: breathing 5 s, Moro's head turn 29 s, kodama rattles 11 s.
"""
import base64, math, random, struct, zlib
from PIL import Image, ImageDraw
from lib import Canvas, UNPAINTED, sprite

NAME = "Princess Mononoke"
SIZE = W, H = 320, 180
COLORS = 16

# daylight palette
S = ["#4f9ad8", "#73b4e4", "#9ccdec", "#c4e2ee"]   # sky, top -> low
HAZE, FOG = "#dcecdc", "#c4dcd8"                 # cloud streaks; the softer haze behind the tree line
MT1, MT2 = "#a4c8dc", "#8ab4cc"                 # far mountains
R1, R2, R3 = "#6aa690", "#44826a", "#285844"    # conifer ridges, far -> near
WA = ["#2f6e5c", "#b4dccc", "#7cbcd0", "#4a94b4"]  # pool: tree reflection, bright horizon, sky, deep
B0, B1, B2, B3 = "#2c2a24", "#484032", "#6a5a40", "#9c8854"   # bark, shadow -> sunlit
M0, M1, M2, M3 = "#1e4a2a", "#34742e", "#5ea636", "#b4e45c"   # moss, shadow -> sunlit
# night: what the daylight colours are multiplied by, in the sky and on the land
NIGHT_SKY, NIGHT = "#334d9e", "#7394d9"

GROUND = 146


def png(cv):
    """Canvas -> base64 palette PNG. UNPAINTED is transparent; 4-tuples carry their own alpha.
    Tries a few bit depths / deflate settings and keeps the smallest."""
    cnt = {}
    for row in cv.px:
        for p in row:
            cnt[p] = cnt.get(p, 0) + 1
    alpha = lambda c: 0 if c == UNPAINTED else (c[3] if len(c) == 4 else 255)
    cols = sorted(cnt, key=lambda c: (alpha(c) == 255, -cnt[c]))
    idx = {c: i for i, c in enumerate(cols)}
    trns = bytes(alpha(c) for c in cols if alpha(c) < 255)
    n = len(cols)
    best = None
    for bits in (1, 2, 4, 8):
        if n > 1 << bits:
            continue
        raw = bytearray()
        for row in cv.px:
            raw.append(0)
            acc = nb = 0
            for p in row:
                acc = acc << bits | idx[p]
                nb += bits
                if nb == 8:
                    raw.append(acc)
                    acc = nb = 0
            if nb:
                raw.append(acc << (8 - nb))
        for wb in (15, 12, 10):
            for st in (0, 1):
                c = zlib.compressobj(9, 8, wb, 9, st)
                d = c.compress(bytes(raw)) + c.flush()
                if best is None or len(d) < len(best[1]):
                    best = bits, d
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return base64.b64encode(
        b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, best[0], 3, 0, 0, 0))
        + ch(b"PLTE", bytes(x for c in cols for x in c[:3])) + (ch(b"tRNS", trns) if trns else b"")
        + ch(b"IDAT", best[1]) + ch(b"IEND", b"")).decode()


def img(cv, x=0, y=0, extra=""):
    pos = (f" x='{x}'" if x else "") + (f" y='{y}'" if y else "")
    return f"<image{pos} width='{cv.w}' height='{cv.h}'{extra} href='data:image/png;base64,{png(cv)}'/>"


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


def firs(cv, base, col, seed, wr, hr, bottom):
    """A conifer tree line: overlapping pointed crowns standing on base(x)."""
    r = random.Random(seed)
    base0, base = base, lambda x: int(round(base0(x)))
    top = [base(x) for x in range(cv.w)]
    x = -r.randrange(wr[1])
    while x < cv.w:
        w, h = r.randrange(*wr), r.randrange(*hr)
        for i in range(w):
            if 0 <= x + i < cv.w:
                t = 1 - abs((i + .5) / w * 2 - 1)
                top[x + i] = min(top[x + i], base(x + i) - int(round(h * t ** .8)))
        x += r.randrange(w // 2, w)
    for x, yt in enumerate(top):
        cv.rect(x, yt, 1, bottom - yt, col)
    return top


# ---------------------------------------------------------------- base: the day sky
def draw():
    cv = Canvas(W, H)
    # sky bands: each edge is long horizontal brush streaks at slightly different heights, riding a slow
    # swell, with a few one-row wisps of the paler colour above it (a dithered seam read as a stitched line)
    cv.rect(0, 0, W, H, S[3])
    r = random.Random(12)
    for y0, up in ((58, S[2]), (38, S[1]), (16, S[0])):
        x = 0
        while x < W:
            n = r.randrange(8, 26)
            e = y0 + int(round(1.6 * math.sin(x * .021 + y0))) + r.randrange(-1, 2)
            cv.rect(x, 0, n, e, up)
            if r.random() < .35:
                cv.rect(x + r.randrange(n // 2), e - 2 - r.randrange(2), r.randrange(3, 9), 1, cv.get(min(x + n, W - 1), e))
            x += n
    # high clouds: flat-bottomed streaks
    for x, y, n in [(98, 22, 30), (104, 21, 16), (108, 23, 26), (168, 34, 44), (178, 33, 24), (186, 35, 34),
                    (140, 50, 30), (146, 49, 14), (206, 56, 30), (96, 62, 24)]:
        cv.rect(x, y, n, 1, HAZE)
    # far mountains, then haze pooling at their feet (the tree line stands against it; a mid tone, so the
    # gaps between the crowns don't read as a row of white teeth)
    for x in range(W):
        a = int(round(69 + 4 * math.sin(x * .031 + 1.9) + 2 * math.sin(x * .09)))
        b = int(round(77 + 3 * math.sin(x * .043 + 4.4) + 2 * math.sin(x * .12 + 1)))
        cv.rect(x, a, 1, H, MT1)
        cv.rect(x, b, 1, H, MT2)
    for x in range(W):          # its top is a soft wavy bank of mist, not a dithered seam (that read as a stitched line)
        cv.rect(x, 85 + int(round(1.3 * math.sin(x * .08) + .8 * math.sin(x * .21 + 1))), 1, H, FOG)
    return cv


# ---------------------------------------------------------------- mid: forest ridges and the pool
SHORE = 101
FAR = [(19, 5), (158, 6), (300, 5)]     # far trunks standing on the far shore


def mid():
    cv = Canvas(W, H)
    firs(cv, lambda x: 90 + 3 * math.sin(x * .04 + 1), R1, 3, (6, 11), (4, 10), H)
    top = firs(cv, lambda x: 96 + 2 * math.sin(x * .05 + 3), R2, 8, (8, 15), (6, 14), H)
    for x, w in FAR:
        cv.rect(x, 0, w, SHORE, R2)
        cv.rect(x, 0, 1, SHORE, R1)
    # low mist along the far shore
    for x in range(W):
        if x % 4 == (0 if x // 40 % 2 else 2):
            cv.set(x, SHORE - 5, R1)
        if x % 2:
            cv.set(x, SHORE - 4, R1)
    cv.rect(0, SHORE - 3, W, 2, R1)
    cv.rect(0, SHORE - 1, W, 1, R3)
    # the pool mirrors the sky upside down: bright near the far shore, deeper at our feet
    bands(cv, SHORE, [(112, WA[1]), (124, WA[2]), (H, WA[3])])
    # the band edges as ripples (runs at slightly different heights) rather than dithered seams
    r = random.Random(6)
    for y0, up, lo in ((112, WA[1], WA[2]), (124, WA[2], WA[3])):
        x = 0
        while x < W:
            n, d = r.randrange(4, 12), r.randrange(-1, 3)
            for xx in range(x, x + n):
                for y in range(y0 - 1, y0 + 3):
                    cv.set(xx, y, up if y < y0 + d else lo)
            x += n
    # ... and the tree line and far trunks: each crown's reflection runs a different length, and its
    # tip breaks up into horizontal ripple streaks of random lengths
    r = random.Random(4)
    rip = []
    for k in range(40):
        row, on = [], r.random() < .5
        while len(row) < W:
            row += [on] * r.randrange(3, 10 if on else 5)
            on = not on
        rip.append(row)
    for x in range(W):
        n = int((SHORE - top[x]) * (.8 + .3 * math.sin(x * .19) * math.sin(x * .061 + 2))) + 3
        for k in range(n + 1):
            if k < max(n - 2, 4) or rip[k][x]:
                cv.set(x, SHORE + k, WA[0])
    for x, w in FAR:            # the far trunks' reflections waver and thin out instead of breaking into a ladder
        for k in range(26):
            if k < 12 or r.random() < 1 - (k - 10) / 16:
                cv.rect(x + (r.randrange(-1, 2) if k > 8 else 0), SHORE + k, w - (k > 18), 1, WA[0])
    for x, y, n in [(130, 115, 14), (226, 118, 10), (60, 121, 12), (176, 129, 12), (20, 131, 8), (286, 127, 9),
                    (96, 135, 10), (206, 137, 14)]:
        cv.rect(x, y, n, 1, WA[1] if y < 124 else WA[2])
    return cv


# ---------------------------------------------------------------- pixel art
MORO = [
    "...............................................W....w.................",
    "..............................................WWW..wWw................",
    "..............................................WgWW.wgWw...............",
    ".............................................WWgWWWwgWWw..............",
    ".............................................WWWWWWWWWWWWw............",
    "............................................WWWWWWWWWWWWWWWw..........",
    "............................................WWWWWWWWWWkkkkWWWWw.......",
    "...........................................WWWWWWWWWWWWeekWWWWWWWWw...",
    "..........................................WWWWWWWWWWWWWWwWWWWWWWWWWkk.",
    "........................................WWwWWWWWWWWWWWWWWWWWWWWWWWWwkk",
    "..WW..................................WWWWWwWWWWWWWWWWwkWWWWWWWWWWwww.",
    ".WWWWW..............................WWWWWWWwWWWWWWWWwwwkkkkkkWWkkkw...",
    "WWWWWWW..........................WWWWWWWWWWWWwWWWWWWwwgg.wwwwWWwww....",
    "WWWWWWWW.....WWWWWWWWWW........WWWWWWWWWWWWWWWwWWWWwwgw....gggg.......",
    ".WWWWWWWW..WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWwWwwwg.w..............",
    "..wWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWwWWwwgg................",
    "...wwWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWwwwwgw................",
    ".....wwWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWwWWwwg..................",
    "......ggWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWwWWWWWwwwwgw.................",
    "....WWWgWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWwWWWwwwwg...................",
    "...WWWWWgWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWwWWWWwwgw...................",
    "..WWWWWWwWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWwWWWWwwwg....................",
    ".WWWWWWw.WWWWWWWWWWWWWWWWWWWWWwwwWWWWWWWWwWWWWwwgw....................",
    ".WWWWWw..WWWWWWWWWWWWWWWWwwwwwwwwwwwwWWWWwWWWWwwg.....................",
    "WWWWWww..WWWWWWWWWWWWWWwwwwwwwwwwwwwwwwwWWWWWWwwg.....................",
    "WWWWww...WWWWWWWWWWWWWwwwwggggggggwwwwwwWWWWWWwggd....................",
    "WWWww....WWWWWWWWWWWWwwwggggg..g.gggwwwwWWWWWWwdggd...................",
    ".Www.....wWWWWWWWWWWwwggggggd.......ggwwWWWWWWwdggd...................",
    ".ww.......wWWWWWWWWwwg..ggggd........gwWWWWWWwgdggd...................",
    "..w........wWWWWWWwwg...gggd..........WWWWWWWwdggd....................",
    "............wWWWWWwg....gggd..........WWWWWWwgdggd....................",
    ".............wWWWWwg.....ggd..........WWWWWWwgdggd....................",
    ".............WWWWWwg.....ggd..........wWWWWWwgdggd....................",
    ".............WWWWwg......ggd...........WWWWWwgdggd....................",
    "............WWWWwg.......ggd...........WWWWWwgdggd....................",
    "............WWWWwg.......ggd...........WWWWWwgdggd....................",
    "............WWWWwg.......ggd...........WWWWWwgdggd....................",
    "............WWWWwg......gggd...........WWWWWwgdggd....................",
    "...........WWWWWWwg....ggggd..........WWWWWWWwgdgggd..................",
    "..........WWgWWgWwg...dggggd.........WWWgWWgWwdggggd..................",
]
SAN = [
    ".......R.......R........w...",
    "......RhR.....RhR......wW...",
    "......RhR.....RhR......wW...",
    "......RRR.....RRR......wW...",
    "......WWWWDDDDDDDWW....ww...",
    ".....WWWWDwwwRwwwDWW...o....",
    ".....WWWDwoooRooowDW...o....",
    "....WWWWDRokoRokoRDW...o....",
    "...WWwWWDRoooRoooRDW...o....",
    "...WWWWWWDRwwowwRDWW...o....",
    "...WWWWWWWDRokoRDWWW...o....",
    "...WwWWWhhhhhRhhhhwW...o....",
    "...WWWWWhhsssRsssswW...o....",
    "...WWWWWhhskkssskkwW...o....",
    "...wWWWWhhsRRsssRRwW...o....",
    "...WWWWWhhssRsssRswW...o....",
    "...WWwWWhhWsssDssswW...o....",
    "...WWWWWhhWssssssswW..o.....",
    "...WWWWWWhhssssssswW..o.....",
    "..WWWWWWWWWwsssssWW...o.....",
    "..WwWWWWWWWwssswwW....o.....",
    "..WWWWWWWWWwsswwWw....o.....",
    ".WWWWWWWWnWnWnWnWn....o.....",
    ".WwWWWWWWnNnWnWnnns...o.....",
    ".WWWWWWWWnNnnnnnnns...o.....",
    ".WWWwWWWWnNnnnnnnns...o.....",
    ".wWWWWWWWnNnnnnnnns...o.....",
    ".WWWWWWWWnNnnnnnnns...o.....",
    "wWWWWWWWWnNnnnnnnnsssso.....",
    "wWWWWWWWWWnNnnnnnnsssso.....",
    "gwWWWWWWWWnnnnssssssso......",
    ".gwWWWWWWwnnnnssssssso......",
    "..ggwwWWw......sssssso......",
    "...ggwww.......Sssssso......",
    "...............Sssss.o......",
    "...............Ssss..o......",
    "..............Ssss...o......",
    "..............Ssss..........",
    ".............Ssss...........",
    ".............Ssss...........",
    ".............bbbb...........",
    "............bbhhhb..........",
]
YAKUL = [
    "..........................................................",
    "......................QqqQqq....ZZ........................",
    "...........................qQqqQ..QZZ.....................",
    "............................QqqQqq...Q....................",
    "................................qqQq..ZZ..................",
    "..................................QqqQ..QZ................",
    "....................R..............qqQq..ZZ...............",
    ".................o.RRRR.............qQqqQ.ZQ..............",
    "................o.RRRRRRR.............qqQq.QZZ............",
    "...............o..DRRRRRRRRR...........qQqq.ZZQ...........",
    "..............o...DRRRssssss.............qqQ..QZ..........",
    ".............o....DRRshhshhs..............qQq..ZZ.........",
    "............o.....DRRsksskss........u......Qqq.ZZ.........",
    "............o.....DRRsssssss........ucu....uqquZZ.........",
    "...........o......DRRRsssss.........uccu..uRRqucc.........",
    "...........o.......RRRRRRRRR..........uuuuuRuuuuccc.......",
    "..........o....yyyyyDRRRRRD..............uuRuWkuuuccc.....",
    "..........o..yyyyyyyyyyyyynn.............uuuRkkuuuRuccc...",
    "..........o.ayyayyayyayyaynNn............uuuuRuuuuRucccc..",
    "...........yayyayyayyayyaynNnn............uuuuRRuuRcccccp.",
    "...........ayyayyayyayyaynnNnnn.........uuuuuuuuRRRcccccp.",
    "..........yayyayyayyayyaynnNn.nns.......uuuuuuuuucRccbcc..",
    ".........yyayyayyayyayyannnNn...sDs....uuuuuuucccRccc.....",
    ".........yyayyayyayyayyannnNn....sss...uuuuuuccRRc........",
    ".........yayyayyayyayyaynnnnn.........uuuuuuRcRccc........",
    ".........yayyayyayyayyaynnnnn.....RRR.uuuuRRRcccc.........",
    "........yyayyayyayyayyahhhhhhh.......RRRRRccccccc.........",
    "....u...yyayyayyayyayyahhhhhhhh.....uuuuuucccccc..........",
    "...uu...yayyayyayyayyahhhhhhhhh....uuuuuuccccccc..........",
    "...ucc...ayyayyayyayyabbbbbhhhh...uuuuuuucccccc...........",
    "....uccu.yuyauyuayuyuabbbbbbhhhhuuuuuuuuccccccc...........",
    ".....uuuuauuyuuuuauuyubbbbbhhhhuuuuuuuuucccccc............",
    ".....uuuuuouuuuuuuuuuuubbbbhqqhuuuuuuuuucccccc............",
    "....uuuuuuuouuuuuuuuuuuubbbhhhhuuuuuuuuuuccccc............",
    "....uuuuuuuuouuuuuuuuuuuuubhqqhuuuuuuuuucccccc............",
    "....uuuuuuuuuuuuuuuuuuuuuuuhqqhuuuuuuuuuuc.c.c............",
    "....uuuuuuuuuuuuuuuuuuuuuuuhhhhhuuuuuuuuuc...c............",
    "....uuuuuuuuuuuuuuuuuuuuuuuhhhhhhuuuuuuuuuuc..............",
    ".....Uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu................",
    ".....UUuuuuuuuuuuccccccccccccccuuuuuuuuuu.................",
    "......UUuuuuuccccccccccccccccccccuuuuuuu..................",
    ".......UuuuuuccccccccccccccccccccuuuuuUU..................",
    ".......Uuuuu.UUUU................Uuu..UUU.................",
    ".......Uuuuu.UUUU................Uuu..UUU.................",
    "......Uuuuu..UUU.................Uuu..UUU.................",
    "......Uuuu..UUU...................Uuu..UU.................",
    "......Uuuu.UUU....................Uuu..UU.................",
    "......Uuu..UUU....................Uuu..UU.................",
    ".......Uu...UU.....................Uu...UU................",
    ".......Uu...UU.....................Uu...UU................",
    "........Uu...UU....................Uu...UU................",
    "........Uu...UU....................Uu...UU................",
    "........Uu...UU....................Uu...UU................",
    "........Uu...UU....................Uu...UU................",
    "........Uu...UU....................Uu...UU................",
    "........hhh..hhh...................hhh..hhh...............",
]
PUP = [
    ".........W...W...........",
    "........WW..WW...........",
    "........WgW.WgW..........",
    ".......WWgWWWgW..........",
    ".......WWWWWWWWW.........",
    "......WWWWWWWWWWW........",
    "......WWWWWWkkkWWW.......",
    ".....wWWWWWWWekWWWWW.....",
    ".....wWWWWWWWWWWWWWWWk...",
    ".....wwWWWWWWWWwkkkkkw...",
    "......wwWWWWWWwwwwww.....",
    "......wWWWWWWWgg.........",
    ".....wWWWWWWWWg..........",
    ".....WWWWWWWWWW..........",
    "....WWWWWWWWWWWW.........",
    "...WWWWWWWWWWWWW.........",
    "..WWWWWWWWWWWWWW.........",
    "..WWWWWWWWWWWWWw.........",
    ".WWWWWWWWWWWWWWw.........",
    ".WWWWWWWWwWWWWWw.........",
    "WWWWWWWWwWWWWWWw.........",
    "WWWWWWWwWWWWwWW..........",
    "WWWWWWWwWWWWwWW..........",
    "WWWWWWwWWWWWwWW..........",
    "WWWWWwWWWWWWwWW..........",
    "WWWWwWWWWWWWgWW..........",
    "WWWWwWWWWWWgwWWg.........",
    "wWWWwWWWWWWgwWWg......W..",
    "wWWWwWWWWWWgwWWg.....WWw.",
    "wggggggggWWgwWWg....WWWw.",
    "WWWWWWWWWgggggggg.WWWWw..",
    "WWWWWWWWWWWWWWWWWWWWWg...",
    "wWWWWWWWWWWWWWWWWwwgg....",
    "gwwwwwwwwwgggggggg.......",
]
PUP_B = [
    "............W...W...................................",
    "...........WW..WW...................................",
    "...........WgW.WgW..................................",
    "..........WWgWWWgWW.................................",
    ".........WWWWWWWWWWW................................",
    ".......WWWWWWWWWWWWWW...............................",
    ".....WWWkkkWWWWWWWWWWWWWWWWWW.......................",
    "..WWWWWWWekWWWWWWWWWWWWWWWWWWWWWW...................",
    "kWWWWWWWWWWWWWWWWWwWWWWWWWWWWWWWWWWW.............WWW",
    "wkkkkkWWWWWWWWWWWwwWWWWWWWWWWWWWWWWWWW........W.WWWW",
    ".wwwwwwgWWWWWWWWwwWWWWWWWWWWWWWWWwWWWWW....W.WWWWWWW",
    ".......ggwWWWWWWwWWWWWWWWWWWWWWWwwWWWWWW...WWWWWWWW.",
    "........ggwWWWWWWWWWWWWWWWWWWWWwwWWWWWWWggWWWWWWWWW.",
    "....WWWWWWgwWWWWWWWWWWWWWWWWWWwwWWWWWWWWggWWWWWWWw..",
    "..WWWWWWWWWwwWWWWWWWWWWWWWWWWwwgwwWWWWWWggWWWWWww...",
    "WWWWWWWWWWWWwwWWWWWWWWWWWWWWwwggwwwwWWWWWgwwwww.....",
    "WWWWWWwwwwwwgwwwwwwwwwwwwwwwwgggwwwwwwWW............",
]
MORO_B = [
    ".....W.........W..............",
    "....WWW.......WWW.............",
    "....WgWW.....WWgW.............",
    "....WgWWWWWWWWWgW.............",
    "...WWWWWWWWWWWWWWW............",
    "...WWWWWWWWWWWWWWWW...........",
    "..WWWkkkWWWWWWkkkWW...........",
    "..WWWWeekWWWWWeekWWw..........",
    ".WWWWWWWWwWWWwWWWWWw..........",
    ".WWwWWWWWwWWWWwWWWww..........",
    "WWWWwWWWWwWkkkWwWWw...........",
    "WWWWWwWWWWwWkWwWwww...........",
    "WWWWWWwWWWwkkkkkwg............",
    "WWWWWWWwWWWwwwwwg.............",
]
DEER = [
    ".............V...V...V.............V...V...V",
    ".............V...V...V.............V...V...V",
    ".............v.V.v...v.V.........V.v...v.V.v",
    ".............v.VVv.V.v.V.........V.v.V.vVV.v",
    "..............vvVv.V.v.v.........v.v.V.vVvv.",
    "...............vvv.v.v.v.V.....V.v.v.v.vvv..",
    "................vv.v.vVv.V.....V.vVv.v.vv...",
    ".................vvv.vVv.v.....v.vVv.vvv....",
    "...................vvvvv.v.V.V.v.vvvvv......",
    "...................vvvvv.v.V.V.v.vvvvv......",
    ".....................vvvvv.v.v.vvvvv........",
    ".......................vvvvfffvvvv..........",
    ".........................vfffffv............",
    "..................ff....ffWWfWWff....ff.....",
    "..................fFFffffWWWWWWWffffFFf.....",
    "...................ffFFffkRWWWRkffFFff......",
    "...................fffWWpggpWpggpWWfff......",
    ".......................WppppWppppW..........",
    ".......................WWpgpkpgpWW..........",
    ".......................WWWpppppWWW..........",
    ".......................WWWWpppWWWW..........",
    ".......................WWWWWWWWWWW..........",
    "......................WWWWWWWWWWWWW.........",
    ".....................WWWWWWWwWWWWWW.........",
    "........FFFFFFFFFFFFWWWWwWWWwWWwWW..........",
    "......FFfffffffffffffWWWwWWWwWWwWW..........",
    "....FFfffcfffffcfffWWWWWwWWWwWWwW...........",
    "..cFffcffffffffffffffWwWwWWWWWWwW...........",
    ".ccffffffffffcfffcffWWwWwWwWWWWW............",
    ".ccfffffcfffffffffffffwWWWwWWWWW............",
    "..cffcffffffffffcffffWWWWWwWWWW.............",
    "...ffffffffcffffffffffWWfWwW.WW.............",
    "...ffffffffffffffffFffWffWWf.W..............",
    "....ffffffccccccccFfffffffW.................",
    "....fffffcccccccccFfffffff..................",
]
DEER_A = [
    ".....fffFF..........fffFFF..",
    "....ffFFFF..........ffFFFF..",
    "....ffF..FF..........ffFF...",
    "....fLL..ll..........fLLl...",
    "..LLLL....ll..........LLLL..",
    "..LcL.....ll..........LcL...",
    "..LLL.....ll..........LLL...",
    "..LcL......ll........llLcL..",
    ".LLL.......ll........llLLL..",
    "qqqQ.......QQQ.......QqqqQ..",
    "qQqQ.......QQQ.......QqQqQ..",
]
DEER_B = [
    "....fffFFFF.........fffFFF..",
    "....ffF..FF.........ffFFFF..",
    "....ffF..FF.........ffFFFF..",
    "....fLL..ll.........fLLlll..",
    "....LLLL.ll.........LLLLll..",
    "....LcL..ll.........LcL.ll..",
    "....LLL..ll.........LLL.ll..",
    "....LcL..ll.........LcL.ll..",
    "....LLL..ll.........LLL.ll..",
    "...qqqQ..QQQ.......qqqQ.QQQ.",
    "...qQqQ..QQQ.......qQqQ.QQQ.",
]
# her mask pulled down over her face (with a patch of hood fur above it, to cover the folded-up one)
MASK = [
    ".WWWWWWWWWWW.",
    ".WWWWWWWWWWW.",
    ".WWWWWWWWWWW.",
    ".WWWWWWWWWWW.",
    ".WWWDDDDDWWW.",
    ".WDDRRRRRDDW.",
    ".DRRRRRRRRRD.",
    "DRwwwwRwwwwRD",
    "DwRooRwRooRwD",
    "DRokkoRokkoRD",
    "DRokkoRokkoRD",
    "DRRooRRRooRRD",
    "DRwRRRRRRRwRD",
    "DRRwwRRRwwRRD",
    ".DRRRwwwRRRD.",
    ".DRRRoooRRRD.",
    "..DRRokoRRD..",
    "...DRoooRD...",
    "....DDDDD....",
]
# Ashitaka's curse flares as the Nightwalker rises: the mark darkens his forearm and worm-like tendrils
# writhe off it, thick at the root and tapering to a curled tip, a wave travelling down each one (two
# frames, half a wave apart). Drawn at (250, 100); his forearm runs from (266, 111) to the hand at (259, 115)
TENDRILS = [   # root x, y; heading (radians, 0 = right, up positive); how far it curls; length
    (12.5, 12, 2.1, 2.4, 10), (15, 11, 1.35, 1.9, 8), (10, 14, 3.4, -2.2, 9), (9, 15.5, 4.3, 1.8, 6)]


def curse(phase):
    k = 4
    im = Image.new("L", (24 * k, 22 * k), 0)
    d = ImageDraw.Draw(im)
    for x, y, a0, curl, n in TENDRILS:
        for i in range(n * k):
            t = i / (n * k)
            a = a0 + curl * t * t + .7 * math.sin(6.3 * t * 1.2 - phase) * t
            x, y = x + math.cos(a) / k, y - math.sin(a) / k
            rad = (2.1 * (1 - t) + .7) / 2
            d.ellipse([(x - rad) * k, (y - rad) * k, (x + rad) * k, (y + rad) * k], fill=255)
    px = im.resize((24, 22), Image.BOX).load()
    on = lambda x, y: 0 <= x < 24 and 0 <= y < 22 and px[x, y] > 100
    return ["".join(("v" if not on(x, y - 1) or not on(x - 1, y) else "p") if on(x, y) else "." for x in range(24))
            for y in range(22)]


# Moro howling to the moon, in profile pointed at the sky: long muzzle, jaw open, ears pinned back, eye shut,
# a chin notch and a shaded throat edge. Rows 17+ line up
# with HEAD_A's rows 0+, and it covers the head underlay kept in TORSO
MORO_H = [
    ".....................WWk......",
    "...................WWWWkk.....",
    "..................WWWWWWWw....",
    "WWW.............WWWWWWWWwk....",
    ".WggWWW........WWWWWWWWwkk....",
    "..WgggggWWWWWgWWWWWWWWwkkk....",
    "...WgggWWWWWWWWWWWWWWwkkk.....",
    "....WWWWWWWWWWWWWWWWwkkwww....",
    ".....WWWWWWWWkkWWWWwkwwwwg....",
    ".....WWWWWWWWWwwwwwwwwwgg.....",
    "....WWWWWWWWWWWWWwwwwwg.......",
    "....WWWWWWWWWWWWWwwwwg........",
    "...WWWWWWWWWWWWWWWwgg.........",
    "...WWWWWWWWWWWWWWWg...........",
    "...WWWWWWWWWWWWWWwg...........",
    "...WWWWWWWWWWWWWWWwg..........",
    "..WWWWWWWWWWWWWWWWwg..........",
    "..WWWWWWWWWWWWWWWWwg..........",
    "..WWWWWWWWWWWWWWWWWwg.........",
    "..WWWWWWwWWWWWWWWWWwg.........",
    ".WWWWWWWWwWWWWWWWWWwg.........",
    ".WWWWWWWWwWWWWWWWWWwg.........",
    ".WWWWWWWWWwWWWWWWWWwg.........",
    "WWWWWwWWWWWWWWWWWWWwg.........",
    "WWWWWWwWWWWWWWWWWWWWwg........",
    "WWWWWWWWWWWWwWWWWWWWwg........",
    "WWWWWWWWWWWWWwWWWWWWwg........",
    "WWWWWWWWWWWWWwWWWWWWwg........",
    "WWWWWWWWWWWWWWWWWWWWwg........",
    "WWWWWWWWWWWWWWWWWWWwg.........",
    "WWWWWWWWWWWWWWWWWWWwg.........",
]
# ... and her sitting child joins in (its head and neck redrawn; five new rows above its old head)
PUP_H = [
    "...............kk........",
    "..............Wkkw.......",
    ".............WWWkw.......",
    "............WWWWkw.......",
    "...........WWWWWww.......",
    "..........WWWWWwwg.......",
    "......W..WWWWWWwg........",
    ".....WgWWWWkkWwwg........",
    ".....WggWWWWWWwg.........",
    "......WWWWWWWWwg.........",
    "......WWWWWWWWwg.........",
    "......WWWWWWWWwg.........",
    ".....wWWWWWWWWwg.........",
    ".....wWWWWWWWWwg.........",
    ".....wwWWWWWWWwg.........",
    "......wwWWWWWWwg.........",
] + PUP[11:]
PAL = {
    "W": "#f2f6ee", "w": "#c6d6de", "g": "#8faac4", "d": "#5c7c9e", "k": "#101c24", "e": "#f0b030",
    "R": "#e03a34", "D": "#a82430", "s": "#eab890", "S": "#c98a68", "h": "#3a2418", "n": "#1c2c64", "N": "#2c4490",
    "o": "#c89a58", "c": "#f0e6c4", "b": "#8c6444", "a": "#d8b868",
    "p": "#e86a50", "u": "#e8a26a", "U": "#c07840", "q": "#b6b6ac", "Q": "#84847c", "y": "#ecdf9c",
    "f": "#dcbca6", "F": "#b8927c", "v": "#6c7450", "V": "#9aa472", "L": "#77724a", "l": "#565334", "Z": "#5e5e58",
}
MX, MY = 40, 108           # Moro's art origin, under the left cedar; her feet land on GROUND + 1
SPLIT = 24                 # Moro rows above this breathe; rows from here down are static legs
SX, SY = MX + 22, MY - 25  # San
YX, YY = 236, GROUND - 54  # Ashitaka on Yakul, under the right cedar, painted mirrored so they face the pool
PX, PY = 13, GROUND - 33   # Moro's two children, young wolves about Yakul's size: one sits behind her tail ...
LX, LY = 199, GROUND - 16  # ... and one lies in the grass in front of Yakul
APES = [(38, 34), (41, 80), (286, 28)]   # the apes: only a hunched shape, and red eyes after dark
VIGIL = [(50, 100, 0), (76, 62, 1), (258, 28, 2), (280, 84, 3)]   # kodama that gather on the cedars to watch the Nightwalker


def spr(rows, x, y, extra="", flip=False):
    """ASCII art as a nested PNG at (x, y). The image carries a 1px transparent border: a sprite's
    own bounds are anti-aliased at fractional zoom, so art that touched them would get a soft edge."""
    cv = Canvas(len(rows[0]) + 2, len(rows) + 2)
    cv.paint(rows, PAL, 1, 1, flip)
    return img(cv, x - 1, y - 1, extra)


# ---------------------------------------------------------------- foreground
def trunk(cv, x0, x1, lit, seed):
    """A great cedar: a bark cylinder shaded towards its sunlit side, long fibrous strips of bark,
    and a foot that flares out towards the light."""
    r = random.Random(seed)
    for y in range(H):
        f = int(max(0, y - 112) ** 2 / 110)                    # flare of the foot
        a, b = (x0, x1 + f) if lit > 0 else (x0 - f, x1)
        w = b - a
        for x in range(a, b):
            t = (x - a + .5) / w if lit > 0 else 1 - (x - a + .5) / w      # 1 = sunlit edge
            j = t + ((.03 if (x + y) % 2 else -.03) if x1 - x0 > 30 else 0)   # checker softens each seam on the big two
            cv.set(x, y, B3 if t > 1 - 1.2 / w else B2 if j > .74 else B1 if j > .36 or t < 2.5 / w else B0)
    x = x0 + 3
    while x < x1 - 3:
        if 0 <= x < cv.w:
            t = (x - x0 + .5) / (x1 - x0) if lit > 0 else 1 - (x - x0 + .5) / (x1 - x0)
            c = B1 if t > .77 else B0 if t > .39 else B1
            y = -r.randrange(40)
            while y < H:
                n = r.randrange(40, 110)
                cv.rect(x, y, 1, n, c)
                y += n + r.randrange(4, 12)
        x += r.randrange(5, 9)


def moss(cv, cx, cy, rx, ry):
    """One moss cushion, lit from the upper left."""
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            u, v = (x + .5 - cx) / (rx + .5), (y + .5 - cy) / (ry + .5)
            if u * u + v * v <= 1:
                k = -u * .45 - v * .9
                cv.set(x, y, M3 if k > .72 and (x + y) % 2 == 0 else M2 if k > .38 else M1 if k > -.3 else M0)


def mossy(cv, patches, seed):
    """Moss growing in drifts: each patch is a loose cluster of small cushions."""
    r = random.Random(seed)
    cs = []
    for cx, cy, sx, sy, n in patches:
        cs += [(cy + r.randrange(-sy, sy + 1), cx + r.randrange(-sx, sx + 1), r.randrange(2, 5), r.randrange(1, 4))
               for _ in range(n)]
    for cy, cx, rx, ry in sorted(cs):
        moss(cv, cx, cy, rx, ry)


def root(cv, x0, y0, n, side):
    """A buttress root sweeping from the trunk down to the bank, mossy along its top."""
    for i in range(n):
        x = x0 + side * i
        y = y0 + int((GROUND - y0) * (1 - (1 - i / n) ** 2.2))
        cv.rect(x, y, 1, GROUND - y + 3, B1 if i % 5 == 4 else B2)
        cv.set(x, y, M3 if i % 3 == 0 else M2)
        cv.set(x, y + 1, M2 if i % 2 else M1)
        cv.set(x, y + 2, M1)


def fern(cv, x0, y0, size, lean=0):
    """A fern: fronds rise from one crown and arch over, pale at the tips."""
    for k, a in enumerate((-1.15, -.65, -.2, .25, .7, 1.2)):
        n = int(size * (1 - abs(k - 2.5) * .08))
        x, y = x0 + .5, y0 + .5
        for i in range(n):
            t = i / n
            th = (a + lean) * (.35 + 1.75 * t)
            x, y = x + math.sin(th), y - math.cos(th)
            cv.set(int(x), int(y), M3 if t > .7 else M2)
            if i > 2 and i % 2 == 0:
                cv.set(int(x - math.cos(th) * 1.5), int(y - math.sin(th) * 1.5 + 1), M1)
                cv.set(int(x + math.cos(th) * 1.5), int(y + math.sin(th) * 1.5 + 1), M1)


def fg(yakul=YAKUL, pup_b=PUP_B, pup=PUP):
    cv = Canvas(W, H)
    trunk(cv, -10, 12, 1, 3)
    trunk(cv, 306, 332, -1, 4)
    trunk(cv, 28, 92, 1, 1)
    trunk(cv, 244, 296, -1, 2)
    # roots
    root(cv, 100, 124, 22, 1)
    root(cv, 236, 126, 18, -1)
    # the near bank
    bands(cv, GROUND, [(GROUND + 4, M1), (GROUND + 10, M0), (H, B1)])
    mossy(cv, [(x, GROUND + 1, 5, 1, 3) for x in range(4, W, 12)], 9)
    r = random.Random(11)
    for x in range(4, W, 9):                       # grass tufts
        x += r.randrange(5)
        n = r.randrange(2, 5)
        cv.rect(x, GROUND - n, 1, n + 1, M1)
        cv.set(x, GROUND - n, M2)
        cv.rect(x + 2, GROUND - n + 2, 1, n, M1)
        cv.rect(x - 1, GROUND - 1, 1, 2, M2)
    # moss: drifts up the trunks' sunlit edges, skirts at their feet, cushions on burls
    mossy(cv, [(91, 26, 2, 12, 7), (91, 66, 2, 9, 5), (93, 100, 3, 10, 7), (98, 126, 6, 6, 8),
               (245, 20, 2, 10, 6), (245, 52, 2, 6, 4), (244, 92, 2, 12, 7), (239, 128, 5, 5, 7),
               (12, 60, 1, 14, 5), (13, 118, 3, 8, 5), (306, 44, 1, 10, 4), (305, 110, 3, 9, 5),
               (268, 134, 9, 3, 6), (284, 140, 6, 2, 4)], 7)
    for cx, cy, rx, ry in [(44, 58, 6, 2), (272, 66, 7, 2)] + [(x, y + 13, 4, 2) for x, y, _ in VIGIL]:
        moss(cv, cx, cy, rx, ry)
    for x, y, n, lean in [(24, 148, 13, .2), (6, 148, 14, .25), (314, 148, 14, -.25)]:
        fern(cv, x, y, n, lean)
    # canopy
    r = random.Random(5)
    for cx in range(-6, W + 8, 9):
        d = abs(cx - 168) / 168
        cy, rad = -7 + r.randrange(5) + int(9 * d), r.randrange(8, 13)
        for y in range(0, cy + rad + 1):
            for x in range(cx - rad, cx + rad + 1):
                if (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= rad * rad:
                    cv.set(x, y, M0)
        for dx in (-5, 0, 4):                                   # leaf sprays along the underside
            y = cy + int(math.sqrt(max(0, rad * rad - dx * dx))) - 2
            cv.rect(cx + dx - 1, y, 3, 1, M1)
            cv.set(cx + dx, y + 1, M1)
        if r.random() < .6:
            n = r.randrange(3, 9)
            cv.rect(cx + 2, cy + rad - 1, 1, n, M1)
            cv.set(cx + 2, cy + rad - 1 + n, M2)
    # the apes, barely there
    for x, y in APES:
        for i, n in enumerate((3, 5, 7, 9, 9, 9)):
            cv.rect(x - n // 2, y - 2 + i, n, 1, B0)
    # Ashitaka on Yakul, and the young wolves, each with a shadow on the moss
    cv.rect(YX + 15, GROUND, 36, 2, M0)
    cv.paint(yakul, PAL, YX, YY, True)
    cv.rect(LX + 1, GROUND, 48, 2, M0)
    cv.rect(PX + 1, GROUND, 24, 2, M0)
    cv.paint(pup, PAL, PX, PY + len(PUP) - len(pup))
    cv.paint(pup_b, PAL, LX, LY)
    # Moro's legs (her body breathes in a sprite above) and her shadow on the moss
    cv.rect(MX + 9, GROUND, 46, 1, M1)
    cv.rect(MX + 12, GROUND + 1, 40, 1, M0)
    cv.paint([row[10:] for row in MORO[SPLIT:]], PAL, MX + 10, MY + SPLIT)
    return cv


def night():
    """The land's silhouette in one flat colour: multiplied over the daylight land, it is the night.
    The sky gaps stay open, so the moon and the Nightwalker shine through them untouched."""
    cv = Canvas(W, H)
    flat = dict.fromkeys(PAL, NIGHT)
    for layer in (mid(), fg()):
        for y, row in enumerate(layer.px):
            for x, p in enumerate(row):
                if p != UNPAINTED:
                    cv.set(x, y, NIGHT)
    cv.paint(MORO, flat, MX, MY)
    cv.paint(MORO_B, flat, MX + 40, MY)
    cv.paint(SAN, flat, SX, SY)
    return cv


# ---------------------------------------------------------------- the Nightwalker
NW_W, NW_H = 84, 80           # only what can show above the trees; the rest of him is never seen


def nightwalker(flat=False):
    """The Nightwalker, drawn facing left (the way he wades): a tall, upright, broad-shouldered giant.
    Built silhouette first: shoulders as the widest line, a long ape-like arm hanging down each side clear
    of the torso (elbows at hip height, forearms drooping away behind the trees),
    a chest tapering to the waist, a thick neck curving forward to a small bowed head with a
    blunt muzzle and fangs, a crest of long spines from crown to shoulder. Then broad value planes
    (lit from the upper left, where the moon is), one rim round the outside, three separation lines
    (near arm over torso, neck over shoulders, head over neck) and a few chunky navy markings.
    flat=True returns the bare silhouette, for judging the form alone."""
    def mask(draw):
        im = Image.new("L", (NW_W, NW_H), 0)
        draw(ImageDraw.Draw(im))
        return im.load()
    def blob(d, x, y, r):
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    def limb(d, pts, w0, w1, n=40):
        for i in range(n + 1):
            t = i / n * (len(pts) - 1)
            k = min(int(t), len(pts) - 2)
            f = t - k
            blob(d, pts[k][0] + (pts[k + 1][0] - pts[k][0]) * f, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * f, (w0 + (w1 - w0) * i / n) / 2)
    def arm(d, pts, w0, w1, sx, sy, sr):
        blob(d, sx, sy, sr)                                          # deltoid cap
        limb(d, pts, w0, w1)                                         # upper arm, elbow, forearm; the hand is below the trees
    def spines(d):
        for x0, y0, a, n in [(30, 11, 115, 10), (34, 10, 96, 15), (38, 12, 77, 19), (42, 16, 60, 21), (46, 21, 46, 21), (50, 26, 34, 19),
                             (55, 30, 23, 16), (62, 31, 14, 13), (71, 36, 6, 10), (75, 46, 0, 7), (76, 57, -4, 5)]:
            for i in range(n + 1):                                   # each curls upwards a little and tapers to a round tip
                t = i / n
                blob(d, x0 + i * math.cos(math.radians(a + 18 * t)), y0 - i * math.sin(math.radians(a + 18 * t)), 1.8 - 1.1 * t)
    # masses, back to front, each with the centre and radii its value planes are measured from
    parts = [
        (mask(spines), None),
        (mask(lambda d: arm(d, [(28, 41), (22, 54), (21, 66), (26, 84)], 8.5, 5.5, 30, 39, 6.5)), (25, 52, 6, 16)),            # far arm
        (mask(lambda d: d.polygon([(33, 35), (59, 33), (63, 40), (62, 54), (58, 66), (58, 80), (38, 80), (37, 66), (32, 54), (31, 42)], fill=255)),
         (46, 54, 17, 26)),                                                                                                     # chest and waist
        (mask(lambda d: arm(d, [(67, 41), (73, 54), (74, 66), (69, 84)], 10.5, 7, 64, 38, 8)), (69, 50, 8, 18)),               # near arm
        (mask(lambda d: (limb(d, [(47, 37), (44, 27), (37, 19)], 15, 15), blob(d, 32, 31, 3.5))), (43, 27, 10, 12)),   # neck: broad all the way up, full at the throat
        (mask(lambda d: (blob(d, 33, 17, 8), limb(d, [(31, 18), (24, 24), (19, 30)], 14, 10), blob(d, 27, 31, 3.5),
                         d.polygon([(14, 33), (15, 38), (17, 34), (19, 38), (21, 34)], fill=255))), (27, 22, 12, 12)),
        # ^ head: skull, a deep blunt muzzle, a small chin where the jaw ends above the throat, fangs
    ]
    # close any background boxed in between the masses: it joins the chest
    seen, todo = set(), [(-1, -1)]
    while todo:
        x, y = todo.pop()
        if ((x, y) not in seen and -1 <= x <= NW_W and -1 <= y <= NW_H
                and not (0 <= x < NW_W and 0 <= y < NW_H and any(m[x, y] for m, _ in parts))):
            seen.add((x, y))
            todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    for y in range(NW_H):
        for x in range(NW_W):
            if (x, y) not in seen and not any(m[x, y] for m, _ in parts):
                parts[2][0][x, y] = 255
    own = lambda x, y: max((i for i, (m, _) in enumerate(parts) if 0 <= x < NW_W and 0 <= y < NW_H and m[x, y]), default=-1)
    # markings: chunky navy shapes, each belonging to one mass (the value drawn is that mass's index)
    pat = Image.new("L", (NW_W, NW_H), 0)
    dp = ImageDraw.Draw(pat)
    dp.arc([59, 33, 69, 43], 30, 330, fill=3, width=2)               # spiral on the near shoulder
    dp.rectangle([63, 37, 65, 39], fill=3)
    for y in (49, 57, 72):
        dp.rectangle([62, y, 80, y + 1], fill=3)                     # bands round the near arm
    for y in (48, 56, 71):
        dp.rectangle([16, y, 30, y + 1], fill=1)                     # ... and the far one
    dp.arc([36, 42, 56, 62], 150, 400, fill=2, width=2)              # a sweep across the chest
    dp.arc([42, 48, 50, 56], 0, 250, fill=2, width=2)
    dp.arc([42, 64, 54, 76], 200, 480, fill=2, width=2)              # spiral above the waist
    dp.arc([37, 20, 49, 32], 190, 330, fill=4, width=2)              # a band round the neck
    dp.rectangle([28, 17, 30, 18], fill=5)                           # the eye
    pp = pat.load()
    RIM, GLOW, PALE = (220, 255, 248, 240), (120, 214, 236, 228), (160, 236, 244, 226)
    LITE, MID, DARK, NAVY = (112, 186, 232, 216), (70, 132, 208, 214), (44, 88, 170, 214), (18, 32, 100, 228)
    cv = Canvas(NW_W, NW_H)
    for y in range(NW_H):
        for x in range(NW_W):
            o = own(x, y)
            if o < 0:
                continue
            nb = [own(x - 1, y), own(x, y - 1), own(x + 1, y), own(x, y + 1)]
            if flat:
                c = MID
            elif o == 0:
                c = PALE
            elif min(nb) < 0:
                c = RIM if min(nb[:2]) < 0 else GLOW                 # one rim, brightest up and to the left
            elif o < 5 and max(nb) > max(o, 2):
                c = NAVY                                             # the form behind, where arm, neck or head crosses it
            elif pp[x, y] == o:
                c = NAVY
            else:
                cx, cy, rx, ry = parts[o][1]
                if o in (1, 3) and y > 66:                           # forearms: their own planes, below a crease at the elbow
                    cx, cy, ry = (23 if o == 1 else 72), 76, 12
                k = -(x - cx) / rx * .7 - (y - cy) / ry * .45 - (o in (1, 3) and y == 66)
                c = (LITE, MID, DARK, DARK)[(0 if k > .3 else 1 if k > -.3 else 2) + (o == 1)]
            cv.set(x, y, c)
    if not flat:
        for x, y in [(29, 18), (41, 25), (36, 46), (50, 40), (44, 60), (55, 68), (41, 72), (66, 47), (70, 60), (25, 44), (22, 26), (50, 52)]:
            if own(x, y) > 0:
                cv.set(x, y, (255, 255, 255, 255))                   # a few stars
    return cv


def smoke():
    """Irontown's smoke, far beyond the trees: a column rising from behind the ridges that leans and
    spreads downwind, lit on its sunward side. Drawn at (90, 40)."""
    cv = Canvas(36, 50)
    # distinct billows, each bigger than the last, bending over downwind; the top ones thin out to a dither
    for x, y, r, thin in [(6, 46, 2.2, 0), (7, 42, 2.7, 0), (6, 37, 3, 0), (8, 32, 3.3, 0), (9, 27, 3.6, 0),
                          (10, 21, 4, 0), (15, 16, 4.3, 0), (21, 12, 4.4, 0), (28, 11, 4, 1), (33, 12, 3, 2)]:
        for yy in range(int(y - r) - 1, int(y + r) + 2):
            for xx in range(int(x - r) - 1, int(x + r) + 2):
                d = math.hypot(xx + .5 - x, yy + .5 - y)
                if d <= r and 0 <= xx < cv.w and 0 <= yy < cv.h and not (thin and (xx + yy) % (thin + 1)):
                    lit = (xx + .5 - x) * -.6 + (yy + .5 - y) * -.8 > r * .2
                    cv.set(xx, yy, "#d6cec2" if lit else "#aaa298")
    return cv


NX, NY = 174, 14                  # where he has risen to: his head just behind where the Forest Spirit's was
HX, HY = 250, SHORE + 10 - 46      # Forest Spirit, parked behind the right-hand trunk
LEGS_A, LEGS_B = [[DEER[34][:28]] + f for f in (DEER_A, DEER_B)]


def deer(first):
    """The Forest Spirit's markup: body, crown and face in one image, then two walking leg frames or
    the standing legs. The second copy (his reflection) reuses the images by id."""
    def part(k, rows, x, y):
        return spr(rows, HX + x, HY + y, f" id='pm-d{k}'", True) if first else f"<use href='#pm-d{k}'/>"
    return (f"<g class='pm-z'><g class='pm-x'><g class='pm-t'>{part(0, DEER, 0, 0)}"
            f"<g class='pm-w'><g class='pm-l'>{part(2, LEGS_A, 16, 34)}</g>"
            f"<g class='pm-l pm-e'>{part(3, LEGS_B, 16, 34)}"
            + (f"<path stroke='#cfe' d='M{HX + 16} {HY + 46}.5h8m10 0h9'/>" if first else "") + "</g></g>"
            "<g class='pm-s'><use href='#pm-d3'/>"
            # where he stands, lilies open on the water round his hooves: pads, then blossoms on them
            + (f"<path stroke='#5a4' d='M{HX + 11} {HY + 46}.5h5m8 0h5m9 0h6m-29 1h7m7 0h6m10 0h5'/>"
               f"<path stroke='#9d5' d='M{HX + 12} {HY + 46}.5h2m11 0h2m11 0h2'/>"
               f"<path stroke='#f8b' d='M{HX + 12} {HY + 45}.5h2m26 0h2m-27-1h1m26 0h1'/>"
               f"<path stroke='#fff' d='M{HX + 25} {HY + 45}.5h3m-2-1h1'/>" if first else "")
            + "</g></g></g></g>")


def put(rows, *edits):
    """A copy of some art with runs of pixels replaced: (row, column, new pixels)."""
    rows = list(rows)
    for y, x, s in edits:
        rows[y] = rows[y][:x] + s + rows[y][x + len(s):]
    return rows


def patch(cls, **art):
    """A flick frame for the foreground: only the pixels that change when a piece of its art is redrawn
    (what is uncovered shows the pool or bark behind), as a small image to switch on and off."""
    m, a, b = mid(), fg(), fg(**art)
    d = [(x, y) for y in range(H) for x in range(W) if a.px[y][x] != b.px[y][x]]
    x0, y0 = min(x for x, _ in d), min(y for _, y in d)
    cv = Canvas(max(x for x, _ in d) - x0 + 3, max(y for _, y in d) - y0 + 3)
    for x, y in d:
        cv.set(x - x0 + 1, y - y0 + 1, m.px[y][x] if b.px[y][x] == UNPAINTED else b.px[y][x])
    return img(cv, x0 - 1, y0 - 1, f" class='{cls}'")


def oval(rx, ry, cy):
    """A pixel-stepped ellipse centred on x 0, as one path."""
    hw = [int(rx * math.sqrt(1 - ((y + .5 - ry) / ry) ** 2) + .5) for y in range(2 * ry)]
    d = f"M{-hw[0]} {cy - ry}h{2 * hw[0]}"
    for a, b in zip(hw, hw[1:]):
        d += "v1" + (f"h{b - a}" if b != a else "")
    d += f"v1h{-2 * hw[-1]}"
    for a, b in zip(hw[::-1], hw[-2::-1]):
        d += "v-1" + (f"h{a - b}" if b != a else "")
    return d + "z"


# Ashitaka's straw cape lifts in a breath of wind; Yakul flicks an ear and his tail; the lying wolf flicks an ear
FLICKS = [("pm-F",dict(yakul=put(YAKUL, (12, 36, "."), (13, 36, ".uu"), (14, 34, "uu")))),
          ("pm-F pm-2", dict(yakul=put(YAKUL, (26, 3, "u"), (27, 2, "uu."), (28, 2, "uuc")))),
          ("pm-F pm-3", dict(pup_b=put(PUP_B, (0, 16, "."), (1, 15, "."), (1, 17, "WW")))),
          ("pm-C", dict(yakul=put(YAKUL, (23, 8, "y"), (24, 8, "y"), (25, 7, "yy"), (26, 7, "y"), (27, 7, "a"),
                                  (28, 7, "y"), (29, 8, "y")))),
          ("pm-Y pm-j", dict(pup=PUP_H))]


# Moro's two heads (profile; turned to look at you) swap over an underlay kept in the torso image
HEAD_A = [row[40:] for row in MORO[:14]]
TORSO = [(row[10:40] + "".join("W" if p in PAL and q in PAL else "." for p, q in zip(HEAD_A[i], MORO_B[i])) if i < 14 else row[10:])
         for i, row in enumerate(MORO[:SPLIT + 1])]
CLS_H, CLS_Y = " class='pm-h'", " class='pm-Y'"
KOD = [(112, 131, 0), (136, 136, 2), (272, 53, 4), (44, 45, 1), (170, 137, 5)]
MOON = "h10v1h3v2h2v3h1v8h-1v3h-2v2h-3v1h-10v-1h-3v-2h-2v-3h-1v-8h1v-3h2v-2h3z"

SPRITES = (
    # night falls on the sky; then its lights: stars, and the moon climbing out of the trees
    f"<rect class='pm-N pm-b' width='{W}' height='96' fill='{NIGHT_SKY}'/>"
    "<g class='pm-N'><path stroke='#fff' d='M104 8.5h1m67 9h1m18-12h1m31 17h1m-41 18h1m-75 4h1'/>"
    "<path class='pm-a' stroke='#fff' d='M236 9.5h1m-22 26h1m-55 25h1m-30-34h1m54 0h1'/>"
    f"<g class='pm-u'><path fill='#8ad' opacity='.3' d='M98 17{MOON.replace('10', '16', 1).replace('-10', '-16', 1)}'/>"
    f"<path fill='#ffe' d='M103 21{MOON}'/><path stroke='#cdd' d='M103 25.5h3m-2 1h2m5 7h3m-2 1h2m-7 1h2'/></g></g>"
    # the Nightwalker, between sky and forest
    + f"<g class='pm-n'><g class='pm-q'>{img(nightwalker(), NX, NY)}</g></g>"
    # Irontown's smoke beyond the trees, while the Forest Spirit stands on the pool
    + img(smoke(), 90, 40, " class='pm-I'")
    + img(mid())
    # glints on the pool
    + "<path class='pm-a' stroke='#efe' d='M98 116.5h5m96 6h7m-30 9h4m52 2h6m-222-6h5'/>"
      "<path class='pm-a pm-e' stroke='#efe' d='M180 119.5h6m30 8h5m-118 4h4m128-12h4m-230 12h6'/>"
    # the Forest Spirit, and his reflection
    + deer(True) + f"<g transform='matrix(1 0 0 -.6 0 {1.6 * (SHORE + 10):g})' opacity='.25'>{deer(False)}</g>"
    # a kodama peeks round the right cedar at the Forest Spirit, twice by day (only its head clears the bark)
    + "<use class='pm-p' href='#pm-K' x='249' y='72' style='--d:3'/>"
    + img(fg())
    + "".join(patch(c, **a) for c, a in FLICKS)
    + "<path class='pm-c' style='animation-duration:7s' stroke='#eb9' d='M268 104.5h1m2 0h1'/>"   # Ashitaka blinks
    # Moro's tails, then the breathing group: her body and head, San
    + f"<g class='pm-q'>{spr([row[:12] for row in MORO[10:30]], MX, MY + 10)}</g>"
    + f"<g class='pm-r'>{spr(TORSO, MX + 10, MY)}"
      f"<g class='pm-y'><g class='pm-g'>{spr(HEAD_A, MX + 40, MY)}<path class='pm-c' stroke='#eff' d='M{MX + 55} {MY + 7}.5h2'/></g>"
      f"{spr(MORO_B, MX + 40, MY, CLS_H)}</g>{spr(MORO_H, MX + 40, MY - 17, CLS_Y)}{spr(SAN, SX, SY)}"
      f"<path class='pm-c' style='animation-delay:-2s' stroke='#eb9' d='M{SX + 11} {SY + 13}.5h2m3 0h2'/>"
      f"<path class='pm-c' style='animation-delay:-4s' stroke='#eff' d='M{SX - 1} {SY + 29}.5h1m-2 1h2m-1 1h1'/>"
      f"<g class='pm-M'>{spr(MASK, SX + 7, SY + 4)}</g></g>"
    + f"<path class='pm-c' style='animation-delay:-3s' stroke='#eff' d='M{PX + 13} {PY + 7}.5h2m{LX - PX - 6} {LY - PY}h2'/>"
    # sun shafts, by day only
    + "<g class='pm-z'><path fill='#ffd' opacity='.1' d='M92 0h30l42 147h-30zm8 0h14l42 147h-14zM180 0h16l34 120h-16zM256 0h16l30 105h-16z'/></g>"
    # night falls on the land; a warm wash at dusk and dawn
    + img(night(), extra=" class='pm-N pm-b'")
    + f"<rect class='pm-W pm-b' width='{W}' height='{H}' fill='#fa6'/>"
    # lights that the night does not dim. The Nightwalker's glow lies on the water in broken streaks and
    # wades with him; these and the moon's path are placed only where nothing nearer stands (checked against
    # the foreground, Moro and San, breathing included), so they need no occluder over them
    + "<g class='pm-L'><path class='pm-a' stroke='#7de' d='M211 103.5h6m5 2h8m-16 3h5m6 3h6m-19 3h4m4 4h7m-11 5h3'/>"
      "<path class='pm-a pm-e' stroke='#5bd' d='M216 104.5h4m-12 2h5m13 2h4m-13 2h7m-1 5h5m-15 5h4'/></g>"
    # as the Forest Spirit fades at dusk, motes of his light lift off him towards the giant rising behind
    # (nothing nearer stands there, so they too sit above the night)
    + "<path class='pm-S' stroke='#dff' d='M206 72.5h1m14 6h2m-11 7h1m16-2h1m-24 11h2m14 1h1m-6-18h1m-14 24h1m22-8h1'/>"
    # kodama (glowing faintly after dark), Ashitaka's cursed arm, and after dark the apes' eyes and fireflies
    + f"<defs><path id='pm-O' fill='#cfe' fill-opacity='.11' d='{oval(7, 9, 2)}'/>"
      "<g id='pm-o'><path fill='#bdc' d='M-1 4h2v1h1v1h-1v3h-2v-3h-1v-1h1zm-2 2h1v1h-1zm5 0h1v1h-1zm-4 3h1v2h-1zm3 0h1v2h-1z'/>"
      "<g id='pm-K' class='pm-k'><path fill='#efe' d='M-3-4h5v1h1v1h1v4h-1v1h-1v1h-5v-1h-1v-6h1z'/>"
      "<path fill='#123' d='M-3-1h2v2h-2zm4 0h1v1h-1zm-1 2h1v1h-1z'/></g></g>"
      "<g id='pm-V'><use href='#pm-O'/><use href='#pm-o'/></g></defs>"
    + "<g class='pm-N'>" + "".join(f"<use href='#pm-O' x='{x}' y='{y}'/>" for x, y, _ in KOD) + "</g>"
    + "".join(f"<use href='#pm-o' x='{x}' y='{y}' style='--d:{d}'/>" for x, y, d in KOD)
    + "".join(f"<use class='pm-v' href='#pm-V' x='{x}' y='{y}' style='--d:{d}'/>" for x, y, d in VIGIL)
    + f"<path stroke='#c5f' d='M{YX + 24} {YY + 22}.5h1m-2 1h1'/>"
    + "<g class='pm-X'>" + "".join(f"<g class='pm-l{e}'>{sprite(c, {'v': '#c8f', 'p': '#529'}, 250, 100)}</g>"
                                   for c, e in zip((curse(0), curse(math.pi)), ("", " pm-e"))) + "</g>"
    # the apes' eyes blink, each in its own time; deep in the night a fourth pair opens on the far-right trunk
    + "<g class='pm-N'>" + "".join(f"<path class='pm-B' style='animation-delay:-{2.3 * i:g}s' stroke='#e33' d='M{x - 2} {y}.5h1m2 0h1'/>"
                                   for i, (x, y) in enumerate(APES))
    + "<g class='pm-A'><path class='pm-B' stroke='#e33' d='M311 62.5h1m2 0h1'/></g>"
      # the moon's path on the pool, under the moon, cut where Moro's head is nearer
      "<path class='pm-a' stroke='#eec' d='M104 104.5h3m3 0h3m-10 5h5m1 6h4m-3 5h6'/>"
      "<path class='pm-a pm-e' stroke='#eec' d='M106 102.5h4m-3 5h5m-10 5h3m3 0h5m-2 5h4m-8 6h5'/>"
      "<path class='pm-f' stroke='#fd6' d='M118 96.5h1m64-30h1m40 62h1m-140 12h1m90-60h1m68 14h1m-216 20h1'/>"
      "<path class='pm-f pm-e' stroke='#fd6' d='M150 84.5h1m60-14h1m-110 50h1m120 24h1m-50-88h1m90 60h1m-240-30h1'/></g>"
)
CSS = (
    # night: both multiply layers and every night-only light share one stepped fade
    ".pm-b{mix-blend-mode:multiply}"
    ".pm-N{opacity:0;animation:pm-N 220s steps(8) infinite}@keyframes pm-N{25%{opacity:0}32%,71%{opacity:1}78%{opacity:0}}"
    # the warm wash runs twice a cycle, so one keyframe set serves dusk and dawn
    ".pm-W{opacity:0;animation:pm-W 110s steps(5) infinite}@keyframes pm-W{42%{opacity:0}52%{opacity:.7}62%{opacity:0}}"
    # the moon climbs while it fades in
    ".pm-u{animation:pm-u 220s steps(20) infinite}@keyframes pm-u{from,26%{translate:0 40px}35%,to{translate:0}}"
    # Nightwalker: rises 96px behind the Forest Spirit's spot, then wades 96px left across the pool
    # through the night, a pixel a step, bobbing as he goes (his wrapper borrows the tail rule, pm-q),
    # and sinks at dawn with his head beside the moon; both ends of the loop are below the trees
    ".pm-n{animation:pm-n 220s steps(96) infinite}"
    "@keyframes pm-n{from,26%{translate:0 96px}33%{translate:0}68%{translate:-96px}75%,to{translate:-96px 96px}}"
    # ... and his light on the water fades in as he clears the trees, wades with him step for step, and goes as he sinks
    ".pm-L{opacity:0;animation:pm-L 220s steps(96) infinite}"
    "@keyframes pm-L{from,30%{translate:0;opacity:0}33%{translate:0;opacity:1}68%{translate:-96px;opacity:1}71%,to{translate:-96px;opacity:0}}"
    # shared on/off blink; pm-e is the opposite phase
    ".pm-a{animation:pm-a 5s steps(1) infinite}.pm-a.pm-e{animation-delay:-2.5s}@keyframes pm-a{50%{opacity:0}}"
    # Forest Spirit: walk out, stand, (fade at dusk, return at dawn,) turn, walk off; sun shafts fade with him
    ".pm-z{animation:pm-z 220s steps(4) infinite}@keyframes pm-z{26%{opacity:1}29%,76%{opacity:0}79%{opacity:1}}"
    ".pm-x{animation:pm-x 220s steps(30) infinite}@keyframes pm-x{7%,82%{translate:-60px}89%,to{translate:0}}"
    f".pm-t,.pm-w,.pm-s,.pm-M{{animation:pm-t 220s steps(1) infinite}}.pm-t{{transform-origin:{HX + 22}px 0}}"
    "@keyframes pm-t{82%{scale:-1 1}}.pm-w{animation-name:pm-w}@keyframes pm-w{7%{opacity:0}82%{opacity:1}}"
    ".pm-s{opacity:0;animation-name:pm-s}@keyframes pm-s{7%{opacity:1}82%{opacity:0}}"
    ".pm-l{animation:pm-a .9s steps(1) infinite}.pm-l.pm-e{animation-delay:-.45s}"
    # Moro breathes, her tails stir, she blinks, and now and then she turns to look at you
    ".pm-g,.pm-h{animation:pm-g 29s steps(1) infinite}@keyframes pm-g{62%{opacity:0}78%{opacity:1}}"
    ".pm-h{opacity:0;animation-name:pm-h}@keyframes pm-h{62%{opacity:1}78%{opacity:0}}"
    ".pm-r{animation:pm-r 5s steps(1) infinite}@keyframes pm-r{45%{translate:0 -1px}}"
    ".pm-q{animation:pm-r 7s -3s steps(1) infinite}"
    ".pm-c{opacity:0;animation:pm-c 6s steps(1) infinite}@keyframes pm-c{96%{opacity:1}}"
    # San's mask comes down while the Nightwalker rises
    ".pm-M{opacity:0;animation-name:pm-M}@keyframes pm-M{26%{opacity:1}40%{opacity:0}}"
    # kodama heads click round and rattle
    ".pm-k{animation:pm-k 11s calc(var(--d)*-1.7s) steps(1) infinite}"
    "@keyframes pm-k{80%{rotate:90deg}84%{rotate:0deg}87%{rotate:90deg}91%{rotate:-90deg}95%{rotate:0deg}}"
    # one peeks out from behind the right cedar at 11% (the Forest Spirit is on the water) and at 91% (quiet midday)
    ".pm-p{animation:pm-p 220s steps(1) infinite}@keyframes pm-p{11%,15%{translate:-3px}11.4%,14.6%{translate:-6px}"
    "15.4%{translate:0}91%,95%{translate:-3px}91.4%,94.6%{translate:-6px}95.4%{translate:0}}"
    # ear and tail flicks on their own periods (none shares a period with Moro's 29 s head turn); the cape lifts
    ".pm-F{opacity:0;animation:pm-F 13s steps(1) infinite}.pm-2{animation-duration:17s}.pm-3{animation-duration:23s}"
    "@keyframes pm-F{90%,95%{opacity:1}93%,97%{opacity:0}}"
    ".pm-C{opacity:0;animation:pm-C 11s steps(1) infinite}@keyframes pm-C{70%{opacity:1}88%{opacity:0}}"
    # apes: blinks, and the fourth pair's eyes open 40-62%
    ".pm-B{animation:pm-B 7s steps(1) infinite}@keyframes pm-B{92%{opacity:0}96%{opacity:1}}"
    ".pm-A{opacity:0;animation:pm-A 220s steps(1) infinite}@keyframes pm-A{40%{opacity:1}62%{opacity:0}}"
    # Irontown's smoke climbs into the day sky 9-24%; the Forest Spirit's motes lift off him 25-31%
    ".pm-I{opacity:0;animation:pm-I 220s steps(10) infinite}@keyframes pm-I{9%{opacity:0;translate:0 6px}12%,21%{opacity:.8}24%,to{opacity:0;translate:0}}"
    ".pm-S{opacity:0;animation:pm-S 220s steps(4) infinite}@keyframes pm-S{25%{opacity:0;translate:0}26%{opacity:1}31%,to{opacity:0;translate:0 -16px}}"
    # Ashitaka's curse flares as the Nightwalker rises, writhing (its two frames alternate on the pm-l walk beat)
    ".pm-X{opacity:0;animation:pm-X 220s steps(1) infinite}@keyframes pm-X{27%{opacity:1}35%{opacity:0}}"
    # kodama gather on the cedars one by one to watch the Nightwalker wade, and slip away before dawn
    ".pm-v{opacity:0;animation:pm-v 220s calc(var(--d)*-4.4s) steps(1) infinite}@keyframes pm-v{39%,68%{opacity:1}69%{opacity:0}}"
    # deep in the night Moro throws back her head and howls at the moon; her sitting child joins in a beat later
    ".pm-y{animation:pm-y 220s steps(1) infinite}@keyframes pm-y{45%{opacity:0}49%{opacity:1}}"
    ".pm-Y{opacity:0;animation:pm-Y 220s steps(1) infinite}.pm-Y.pm-j{animation-delay:-217.8s}@keyframes pm-Y{45%{opacity:1}49%{opacity:0}}"
    # fireflies
    ".pm-f{animation:pm-f 14s steps(9) infinite alternate,pm-a 4s steps(1) infinite}.pm-f.pm-e{animation-delay:-14s,-2s}"
    "@keyframes pm-f{to{translate:9px -9px}}"
)
THEME = {"position": "center 55%",  # wide panes crop vertically; see build wide.png
    "canvas": "#0b1a20", "accent": "#8cd058", "overlay": "#081418",
    "colors": {"sidebar": "#0c1e24", "sidebarRowSelected": "#17383c", "sidebarBorder": "#1c4046",
               "surface": "#10272e", "border": "#235058", "text": "#eaf4ea", "textMuted": "#93b4b0"},
}
