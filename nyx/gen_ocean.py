"""Generate variant-ocean.css: an animated SVG particle ocean along the bottom.

A woven swell with crossing seas, seen in perspective (scale s = 1/z, so rows
bunch up toward the horizon).
- The swell is one coherent height field h(x, z, t) = A(z) sin(k x - w t + phi(z)).
  It carries the mesh: dense rows of dots (fixed depth, sliding sideways) and
  cross-hatch columns (fixed world x, rising and falling as the wave passes).
- Crossing seas run through it on other headings. Their waves come in sets:
  a few tall ones, then a lull. The set is part of the wave's shape, so it
  travels with the waves and costs nothing per frame.
- Near rows of the crossing seas have a dark body under each crest, so a tall
  wave stands in front of what is behind it instead of being a line across it.

Every row is a <use> of its train's wave, drawn once in the train's own units
and scaled by s, so a row costs about 100 chars, and the one CSS animation on
the wave (slide by a whole pattern) moves every row at the same world speed.

Earlier versions, in history/: gen_ocean.v7.py (impulses lifted by a
displacement filter), gen_ocean.v8.py (four plain wave trains, no mesh).

Usage: python -I gen_ocean.py <out.css>
"""
import math
import sys
import urllib.parse

W, H = 1600, 400          # viewBox
Y_H, Y_NEAR = 40, 372     # horizon and nearest row baseline
CX = 800                  # vanishing point x
T = 14                    # seconds per wave period at an 800-unit wavelength
TAU = 2 * math.pi
NEAR_S = 0.35             # crossing rows at least this near get a body under their crests

# The swell
ROWS = 24                 # depth slices, z = 1 + DZ i
DZ = 0.32
LAM = 800                 # world wavelength (= screen wavelength at s = 1)
DX = LAM / 8              # column spacing: 8 phase classes
COLS = range(-13, 13)     # column j sits at world x = CX + (j + .5) DX
FRAMES = 8
A0 = 56          # peak wave height at s = 1
PHI_K = 2.2               # diagonal crests: phase = PHI_K * ln z
COPIES = (1.1, 1.21)      # extra copies of the rows, scaled about the vanishing
                          # point: the same surface seen from closer, which
                          # lands their rows between the originals (3x density)
FAR, NEAR = (0x6A, 0x4C, 0xFF), (0x5F, 0xE6, 0xFF)

# The crossing seas, one per entry.
#   lam    mean wavelength, world units
#   amp    crest height of the tallest wave in a set, world units
#   slant  phase = slant * ln z; the sign opposite to PHI_K puts the crests on
#          the other diagonal, which is what reads as crossing
#   dir    +1 slides right, -1 left
#   n      waves per set (the pattern that repeats along the row)
#   lull   height of the smallest wave, as a share of the tallest
#   rows, z  how many rows, and the depths of the nearest and farthest
#   far, near  dot colour at the horizon and at the viewer
SEAS = [
    dict(id="b", lam=1250, amp=80, slant=-2.8, dir=-1, n=3, lull=0.35,
         rows=15, z=(1.07, 7), far=(0x8F, 0x5C, 0xFF), near=(0xE8, 0x9C, 0xFF)),
    dict(id="c", lam=470, amp=26, slant=5, dir=1, n=7, lull=0.2,
         rows=12, z=(1.3, 5), far=(0x5C, 0x7C, 0xFF), near=(0xA8, 0xD8, 0xFF)),
]
BODY = "#03030f", 0.8   # colour and peak opacity of the body under a crest
GAPS = [8, 13, 21, 34]    # dot pitch choices, in a wave's own units
SHADES = 5                # colour steps from horizon to viewer per train
SET_SHARP = 1.2           # how peaked a set is: higher gives a longer lull
K = 4 / (3 * math.pi)     # cubic handle length that makes a half-wave a sine


def mix(a, b, t):
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def span(s_min, period, direction):
    """How far a wave must reach left and right of its origin to cover the
    view at scale s_min. A row's origin sits up to one period left of the
    vanishing point (its phase), and the slide carries it one more period."""
    return (CX / s_min + (period if direction > 0 else 0),
            (W - CX) / s_min + (period if direction > 0 else 2 * period))


def sine(s_min):
    """The swell's sine about y = 0: x = 0 is a zero crossing going up. The
    row copies reach about 60 units further (their shear), hence the margin."""
    left, right = (math.ceil((v + 80) / LAM) for v in span(s_min, LAM, 1))
    return f"M{-left * LAM} 0q{LAM / 4:g} {-2 * A0:g} {LAM / 2:g} 0" + f"t{LAM / 2:g} 0" * (2 * (left + right) - 1)


def set_wave(sea, s_min):
    """A crossing sea's wave about y = 0, and the x where it starts.

    One period is a set of n waves whose heights follow a raised-cosine
    envelope and whose lengths grow with their height (tall waves are long
    waves), so no two waves in a row are alike. Each half-wave is a smooth
    cubic: its handle mirrors the previous one, so the slope is continuous at
    the zero crossings even where the height changes. Zero crossings are
    rounded so that a period is exactly n * lam long and the slide loops.
    """
    n, lam, amp = sea["n"], sea["lam"], sea["amp"]
    env = lambda u: sea["lull"] + (1 - sea["lull"]) * (0.5 - 0.5 * math.cos(TAU * u)) ** SET_SHARP
    raw = [0.75 + 0.5 * env((j + 0.5) / (2 * n)) for j in range(2 * n)]
    cuts = [0]
    for w in raw:
        cuts.append(cuts[-1] + w)
    cuts = [round(c / cuts[-1] * n * lam) for c in cuts]
    halves = [b - a for a, b in zip(cuts, cuts[1:])]
    left, right = span(s_min, n * lam, sea["dir"])
    x_at = lambda j: j // (2 * n) * n * lam + cuts[j % (2 * n)]   # zero crossing j; even ones go up
    first = -2 * n * math.ceil(left / (n * lam))
    while x_at(first + 2) <= -left:
        first += 2
    last = first
    while x_at(last) < right:
        last += 1
    h = lambda j: halves[j % (2 * n)]
    # slope at zero crossing j: the handle height that gives the envelope's
    # height there, over the mean handle length of the half-waves on each side
    slope = lambda j: 4 / 3 * amp * env(cuts[j % (2 * n)] / (n * lam)) / (K * (h(j - 1) + h(j)) / 2)
    d = f"M{x_at(first)} 0c{K * h(first):.0f} {-slope(first) * K * h(first):.0f} "
    for j in range(first, last):
        up = 1 if j % 2 == 0 else -1
        d += ("s" if j > first else "") + f"{(1 - K) * h(j):.0f} {-up * slope(j + 1) * K * h(j):.0f} {h(j)} 0"
    return d, x_at(first)


style = "<style>.r{animation:m var(--t) linear infinite}@keyframes m{to{translate:var(--l)}}</style>"
defs = [
    "<linearGradient id='w' x1='0' y1='0' x2='0' y2='1'>"
    "<stop offset='0' stop-color='#000' stop-opacity='0'/>"
    "<stop offset='.15' stop-color='#04031a' stop-opacity='.55'/>"
    "<stop offset='1' stop-color='#020208' stop-opacity='.9'/></linearGradient>",
    f"<linearGradient id='cg' gradientUnits='userSpaceOnUse' x1='0' y1='{Y_H}' x2='0' y2='{H}'>"
    "<stop offset='0' stop-color='#6a4cff' stop-opacity='0'/>"
    "<stop offset='.25' stop-color='#6a4cff' stop-opacity='.4'/>"
    "<stop offset='1' stop-color='#5fe6ff' stop-opacity='.8'/></linearGradient>",
]
pats = {}


def dots(sid, colours, s):
    """Pattern id for a row of train sid at scale s. The dots come from the
    paint: a row is one solid stroke painted with a stripe pattern. (Dotted
    strokes, dasharray 0 + round caps, made Chrome re-rasterize thousands of
    tiny caps every frame: 19 fps against 125 for the same surface striped.)
    The pattern lives in the wave's units, so its dots slide with the row and
    shrink with distance; a row picks the pitch that lands nearest 8 s px on
    screen (never under 3). Colour and opacity are part of the pattern too,
    in SHADES steps from the horizon to the viewer."""
    t = max(0, (s - S_FAR) / (1 - S_FAR))  # 0 far .. 1 near
    gap = min(GAPS, key=lambda g: abs(g * s - max(3.2, 8 * s)) + (9 if g * s < 2.9 else 0))
    shade = round(math.sqrt(t) * SHADES)  # finer steps near the viewer, where rows are few and far apart
    key = (sid, gap, shade)
    if key not in pats:
        pats[key] = f"{sid}{sum(1 for q in pats if q[0] == sid)}"
        t = (shade / SHADES) ** 2
        defs.append(f"<pattern id='{pats[key]}' patternUnits='userSpaceOnUse' width='{gap}' height='9'>"
                    f"<rect width='{0.44 * gap:.1f}' height='9' fill='{mix(*colours, t)}' "
                    f"fill-opacity='{0.45 + 0.55 * t:.2f}'/></pattern>")
    return pats[key]


def row(href, pid, s, x, yb, ky=1):
    """A row: the wave href scaled to depth, its origin at screen x, baseline
    yb. The stroke width is divided by the scale so the dots stay the size
    they should be on screen."""
    return (f"<use href='#{href}' transform='translate({x:.0f} {yb:.0f}) scale({s:.3g} {s * ky:.3g})' "
            f"stroke='url(#{pid})' stroke-width='{(1 + 2.6 * s) / (s * ky):.1f}'/>")


def depth(z):
    return 1 / z, Y_H + (Y_NEAR - Y_H) / z


# ---- the swell: rows, their copies, and the cross-hatch
S_FAR = 1 / (1 + DZ * (ROWS - 1))
swell = []  # far to near
for i in reversed(range(ROWS)):
    s, yb = depth(1 + DZ * i)
    lz = math.log(1 + DZ * i)
    swell.append({"s": s, "yb": yb, "phi": PHI_K * lz,
                  "amp": A0 * (0.6 + 0.4 * math.sin(2.4 * lz + 0.6))})  # hills vary with depth
# The slide is one wavelength per period, so it loops seamlessly. `translate`
# (not `transform`) leaves the row's own scale alone.
defs.append(f"<path id='a' class='r' style='--l:{LAM}px;--t:{T}s' d='{sine(S_FAR)}'/>")
rows_svg = "".join(
    row("a", dots("a", (FAR, NEAR), r["s"]), r["s"],
        CX - r["s"] * LAM * (r["phi"] / TAU % 1), r["yb"], r["amp"] / A0)
    for r in swell
)


def copy_transform(f):
    """Phase and hill height depend on ln z, so a copy (the surface scaled by
    f about the vanishing point, i.e. rows moved to depth z/f) is off by the
    same phase PHI_K*ln f at every depth. That constant phase is an x-shift
    proportional to s, i.e. to (y - Y_H): a shear cancels it exactly."""
    g = PHI_K * math.log(f) * LAM / (TAU * (Y_NEAR - Y_H))  # shear per unit of (y - Y_H)
    return (f"matrix(1 0 {g:.4f} 1 {-g * Y_H:.2f} 0) "
            f"translate({CX} {Y_H}) scale({f}) translate(-{CX} -{Y_H})")


# Cross-hatch columns (fixed world x) converge on the vanishing point; their
# vertices rise and fall as the swell passes. Columns are 1/8 wavelength
# apart, so 8 SMIL-morphing template paths (8 frames, every 2nd row) serve
# every column through <use> with an x-scale.
hatch = [r for k, r in enumerate(swell) if (len(swell) - 1 - k) % 2 == 0]  # every 2nd, incl. nearest


def column_frame(m, k):
    """Template column for phase class m at frame k; x is 100*s, scaled per use."""
    theta = TAU * (m + 0.5) / 8
    pts = []
    for r in hatch:
        h = r["amp"] * math.sin(theta + r["phi"] - TAU * k / FRAMES)
        pts.append(f"{100 * r['s']:.0f} {r['yb'] - h * r['s']:.0f}")
    return "M" + " ".join(pts)


for m in range(8):
    frames = [column_frame(m, k) for k in range(FRAMES)]
    defs.append(
        f"<path id='h{m}' vector-effect='non-scaling-stroke' d='{frames[0]}'>"
        f"<animate attributeName='d' dur='{T}s' repeatCount='indefinite' "
        f"values='{';'.join(frames + frames[:1])}'/></path>"
    )
body = [
    f"<g stroke='url(#cg)' stroke-width='1'>"
    + "".join(f"<use href='#h{j % 8}' transform='translate({CX} 0) scale({j + 0.5:g} 1)'/>" for j in COLS)
    + "</g>",
    f"<g id='R'>{rows_svg}</g>",
] + [f"<use href='#R' opacity='.75' transform='{copy_transform(f)}'/>" for f in COPIES]

# ---- the crossing seas
# A sea's wave twice: the line, and a shorter closed copy for the body under a
# near row's crests. The closed one runs back along the level of the deepest
# trough, so the body is as tall as the wave: thick under a crest, nothing in
# a trough. It fades from the crest's height down to that level, which keeps
# it from showing as a band. Far rows use the sliding line, near rows the
# sliding group of body and line (the line itself is defined unanimated, or
# it would slide twice inside the group).
# The slide is one whole set per loop (n wavelengths in n periods), and the
# period follows deep-water waves: speed grows with the root of the
# wavelength, so the long sea overtakes the swell and the short one lags.
# Rows of all seas are painted together, far to near, on top of the swell, so
# a near body dims the swell and the far rows behind it. It is not opaque: a
# wave passing behind another dims instead of vanishing, and both can still
# be followed through the crossing.
crossing = []
for sea in SEAS:
    sid, n, lam = sea["id"], sea["n"], sea["lam"]
    slide = f"class='r' style='--l:{sea['dir'] * n * lam:g}px;--t:{n * T * math.sqrt(lam / 800):.0f}s'"
    line, _ = set_wave(sea, 1 / sea["z"][1])
    near_d, x0 = set_wave(sea, NEAR_S)
    defs.append(f"<path id='l{sid}' d='{line}'/><use id='{sid}' href='#l{sid}' {slide}/>")
    defs.append(f"<linearGradient id='g{sid}' gradientUnits='userSpaceOnUse' x2='0' y1='{-sea['amp']:g}' y2='{sea['amp']:g}'>"
                f"<stop stop-color='{BODY[0]}' stop-opacity='{BODY[1]:g}'/>"
                f"<stop offset='1' stop-color='{BODY[0]}' stop-opacity='0'/></linearGradient>")
    defs.append(f"<g id='{sid.upper()}' {slide}><path fill='url(#g{sid})' stroke='none' d='{near_d}V{sea['amp']:g}H{x0}z'/>"
                f"<use href='#l{sid}'/></g>")
    a, b = (v ** (1 / 1.8) for v in sea["z"])
    for i in range(sea["rows"]):
        # depths thin out toward the viewer, and wander a little so the rows are not evenly spaced
        z = (a + (b - a) * (i + 0.35 * math.sin(5 * i + ord(sid))) / (sea["rows"] - 1)) ** 1.8
        s, yb = depth(z)
        offset = s * n * lam * (sea["slant"] * math.log(z) / TAU / n % 1)
        crossing.append((z, row(sid.upper() if s >= NEAR_S else sid, dots(sid, (sea["far"], sea["near"]), s), s, CX - offset, yb)))
body.append("".join(r for _, r in sorted(crossing, reverse=True)))

backdrop = [
    f"<rect y='{Y_H - 8}' width='{W}' height='{H}' fill='url(#w)'/>",
    f"<path d='M0 {Y_H}H{W}' stroke='#9a7bff' stroke-width='10' stroke-opacity='.14'/>",
    f"<path d='M0 {Y_H}H{W}' stroke='#b9a6ff' stroke-width='1' stroke-opacity='.6'/>",
]

svg = (
    f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' preserveAspectRatio='none' "
    f"fill='none'>{style}<defs>{''.join(defs)}</defs>{''.join(backdrop)}{''.join(body)}</svg>"
)
uri = urllib.parse.quote(svg, safe=" =:/'.,-;()")

css = f"""
/* Particle ocean: a woven swell with crossing seas (generated by
   gen_ocean.py). All motion runs inside the SVG; the CSS animation is a slow
   camera bob from the bottom edge. */
.dark [data-slot="sidebar-inset"]::after {{
  inset: auto 0 0 0;
  height: 40vh;
  background: url("data:image/svg+xml,{uri}") 0 0 / 100% 100% no-repeat;
  mix-blend-mode: normal;
  transform-origin: 50% 100%;
  animation: nyx-bob 19s cubic-bezier(0.45, 0, 0.55, 1) infinite alternate;
}}

@keyframes nyx-bob {{
  from {{ transform: scaleY(1); }}
  to {{ transform: scaleY(1.07); }}
}}

@media (prefers-reduced-motion: reduce) {{
  /* animation inside the SVG ignores CSS animation:none, so hide the ocean */
  .dark [data-slot="sidebar-inset"]::after {{ display: none; }}
}}
"""
open(sys.argv[1], "w", encoding="utf-8").write(css)
print(f"wrote {sys.argv[1]}: svg {len(svg)} chars, encoded {len(uri)} chars, css {len(css)} chars, "
      f"{ROWS} swell rows x {1 + len(COPIES)}, {len(crossing)} crossing rows")
