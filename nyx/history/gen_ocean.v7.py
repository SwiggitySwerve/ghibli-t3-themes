"""Generate variant-ocean.css: an animated SVG particle-wave ocean along the bottom.

One coherent height field h(x, z, t) = A(z) sin(k x - w t + phi(z)) seen in
perspective (scale s = 1/z, so rows bunch up toward the horizon).
- Particle rows (fixed depth): sines drawn as solid strokes painted with a
  stripe pattern (so they read as chains of dots) that slide sideways rigidly; screen wavelength and speed both
  scale with s, so every row shares one period T. Animated with CSS inside
  the SVG (translate by var(--l)).
- Cross-hatch columns (fixed world x) converge on the vanishing point; their
  vertices rise and fall as the wave passes. Columns are 1/8 wavelength apart,
  so 8 SMIL-morphing template paths (8 frames, every 2nd row) serve every
  column through <use> with an x-scale.
- Impulses: real bumps. A displacement filter lifts everything on the surface
  (dots, cross-hatch, light) by a height map that is drawn as ordinary SVG:
  a hump that swells at a point, then spreads as a ring wave and settles.
  Particle rings ride the crest.

Usage: python -I gen_ocean.py <out.css>
"""
import math
import sys
import urllib.parse

W, H = 1600, 400          # viewBox
Y_H, Y_NEAR = 40, 372     # horizon and nearest row baseline
CX = 800                  # vanishing point x
ROWS = 24                 # depth slices, z = 1 + DZ i
DZ = 0.32
LAM = 800                 # world wavelength (= screen wavelength at s = 1)
DX = LAM / 8              # column spacing: 8 phase classes
COLS = range(-13, 13)     # column j sits at world x = CX + (j + .5) DX
FRAMES = 8
T = 14                    # seconds per wave period
A0 = 56                   # peak wave height at s = 1
FILL = (1.1, 1.21)        # extra copies of the rows, scaled about the vanishing
                          # point: the same surface seen from closer, which
                          # lands their rows between the originals (3x density)
FAR, NEAR = (0x6A, 0x4C, 0xFF), (0x5F, 0xE6, 0xFF)
ACCENT_FAR, ACCENT_NEAR = (0xB0, 0x5C, 0xFF), (0xFF, 0x5F, 0xDC)
TAU = 2 * math.pi
RIPPLES = [(560, 3, 0), (1180, 6, -2.4), (300, 9, -4.7)]  # (x, row index, delay)
RING_R = 1300             # final ring radius, world units (screen = world * s)
FLAT = 0.22               # a circle on the surface is this flat on screen
BUMP = 700                # a full-strength (opaque) map shape lifts by BUMP / 2 ...
BUMP_FULL_Y = 250         # ... from this y down; above it the lift shrinks with s
BUMP_GAIN = 4             # map contrast boost; lifts clip at BUMP / 2 / BUMP_GAIN
BUMP_W = 380              # crest width (stroke), world units
BUMP_BLUR = "150 680"     # crest softness across and along the view, world units
                          # (long along the view keeps the near slope ~ -0.7 at
                          # ~83 units of lift; proto/sim.py models it)
BUMP_RING = 0.8           # ring strength right after the hump collapses into it
MAP_DY = 420              # the height map is drawn this far below the surface


def mix(a, b, t):
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def depth(i):
    s = 1 / (1 + DZ * i)
    return s, Y_H + (Y_NEAR - Y_H) * s


# Phase and hill height depend on ln z, so a FILL copy (the surface scaled
# by f about the vanishing point, i.e. rows moved to depth z/f) is off by the
# same phase PHI_K*ln f at every depth. That constant phase is an x-shift
# proportional to s, i.e. to (y - Y_H): a shear cancels it exactly.
PHI_K = 2.2               # diagonal crests: phase = PHI_K * ln z
rows = []  # far to near, so near rows paint on top
for i in reversed(range(ROWS)):
    s, yb = depth(i)
    lz = math.log(1 + DZ * i)
    rows.append({
        "i": i, "s": s, "yb": yb,
        "amp": A0 * (0.6 + 0.4 * math.sin(2.4 * lz + 0.6)),  # hills vary with depth
        "phi": PHI_K * lz,
    })


def fill_transform(f):
    g = PHI_K * math.log(f) * LAM / (TAU * (Y_NEAR - Y_H))  # shear per unit of (y - Y_H)
    return (f"matrix(1 0 {g:.4f} 1 {-g * Y_H:.2f} 0) "
            f"translate({CX} {Y_H}) scale({f}) translate(-{CX} -{Y_H})")
S_FAR = rows[0]["s"]


def row_path(r):
    """Row as an absolute-baseline sine using relative smooth quadratics."""
    lam = LAM * r["s"]
    amp = r["amp"] * r["s"]
    half = lam / 2
    x = CX - r["phi"] / TAU * lam          # a zero-crossing going up
    while x > -lam:
        x -= lam
    n = math.ceil((W + lam - x) / half)
    return f"M{x:.0f} {r['yb']:.0f}q{half / 2:.1f} {-2 * amp:.1f} {half:.1f} 0" + f"t{half:.1f} 0" * n


hatch = [r for k, r in enumerate(rows) if (len(rows) - 1 - k) % 2 == 0]  # every 2nd, incl. nearest


def column_frame(m, k):
    """Template column for phase class m at frame k; x is 100*s, scaled per use."""
    theta = TAU * (m + 0.5) / 8
    pts = []
    for r in hatch:
        h = r["amp"] * math.sin(theta + r["phi"] - TAU * k / FRAMES)
        pts.append(f"{100 * r['s']:.0f} {r['yb'] - h * r['s']:.0f}")
    return "M" + " ".join(pts)


style = (
    "<style>"
    f".r{{animation:m {T}s linear infinite}}"
    "@keyframes m{to{transform:translate(var(--l),0)}}"
    # ring p and bump crest b share one timeline: hold while the hump swells
    # (0-9%), then burst outward with the same easing, so the ring of light
    # stays on the crest of the real wave
    ".p{transform-box:fill-box;transform-origin:center;opacity:0;animation:p 7s cubic-bezier(.2,.6,.3,1) infinite}"
    "@keyframes p{0%,9%{transform:scale(.04);opacity:0}15%{opacity:1}100%{transform:scale(1);opacity:0}}"
    ".b{animation:b 7s cubic-bezier(.2,.6,.3,1) var(--d) infinite}"
    f"@keyframes b{{0%{{r:{RING_R * 0.04:.0f}px;opacity:0}}9%{{r:{RING_R * 0.04:.0f}px;opacity:1}}"
    f"17%{{opacity:{BUMP_RING}}}70%{{opacity:0}}100%{{r:{RING_R}px;opacity:0}}}}"
    "filter{color-interpolation-filters:sRGB}"
    ".f{transform-box:fill-box;transform-origin:center;opacity:0;animation:f 7s ease-out infinite;mix-blend-mode:plus-lighter}"
    "@keyframes f{0%{transform:scale(.2);opacity:0}5%{opacity:.9}40%,100%{transform:scale(1);opacity:0}}"
    "</style>"
)

defs = [
    "<linearGradient id='w' x1='0' y1='0' x2='0' y2='1'>"
    "<stop offset='0' stop-color='#000' stop-opacity='0'/>"
    "<stop offset='.15' stop-color='#04031a' stop-opacity='.55'/>"
    "<stop offset='1' stop-color='#020208' stop-opacity='.9'/></linearGradient>",
    f"<linearGradient id='cg' gradientUnits='userSpaceOnUse' x1='0' y1='{Y_H}' x2='0' y2='{H}'>"
    "<stop offset='0' stop-color='#6a4cff' stop-opacity='0'/>"
    "<stop offset='.25' stop-color='#6a4cff' stop-opacity='.4'/>"
    "<stop offset='1' stop-color='#5fe6ff' stop-opacity='.8'/></linearGradient>",
    "<radialGradient id='fg'><stop offset='0' stop-color='#9ff0ff' stop-opacity='.55'/>"
    "<stop offset='.5' stop-color='#6a4cff' stop-opacity='.18'/>"
    "<stop offset='1' stop-color='#6a4cff' stop-opacity='0'/></radialGradient>",
]
# Height map pieces. Green channel = lift: #808080 is level, #80ff80 up,
# #800080 down. One impulse (in world units, instanced per ripple) is a crest
# ring and a trough ring 0.75 s behind it; while the radius is still smaller
# than the stroke the ring is a solid disc, which is the hump (then the dip)
# at the centre. The blur gives the crest a smooth cross-section; it is
# longer along the view than across because the lift is a vertical pixel
# shift: where the near slope of a bump gets steeper than about 0.7 px per
# px the dots smear into streaks, and past 1 the image folds over.
# feImage(#element) cannot feed a displacement map (Chrome treats it as
# tainted and the filter becomes a no-op), so the map is drawn in the filtered
# group itself, MAP_DY below the surface, and feOffset moves it into place.
# After blur and ramp the shapes use well under half the map's range, so
# feColorMatrix stretches green about level by BUMP_GAIN and the displacement
# scale shrinks to match. Same lift, but the filter's cost grows with its
# scale (headless Chrome at 1920x1080: 60, 69, 74, 85 ms per frame at scale
# 10, 79, 190, 400, against 57 ms without the filter).
MAP_Y, MAP_H = Y_H - 10, H - Y_H + 50
defs += [
    f"<filter id='b' filterUnits='userSpaceOnUse' x='-1800' y='-1800' width='3600' height='3600'>"
    f"<feGaussianBlur stdDeviation='{BUMP_BLUR}'/></filter>",
    f"<g id='I' filter='url(#b)' stroke-width='{BUMP_W}'><circle class='b' stroke='#80ff80'/>"
    "<circle class='b' stroke='#800080' stroke-opacity='.5' style='animation-delay:calc(var(--d) + .75s)'/></g>",
    # level grey that fades out toward the viewer: drawn over the bumps it
    # scales their height by s (taller near, smaller far). Stopping the ramp
    # just below the nearest impulse spends the map's 8 bits where the bumps
    # are (one grey level is BUMP / 255 px of lift).
    f"<linearGradient id='u' gradientUnits='userSpaceOnUse' x2='0' y1='{Y_H}' y2='{BUMP_FULL_Y}'>"
    "<stop stop-color='#808080'/><stop offset='1' stop-color='#808080' stop-opacity='0'/></linearGradient>",
    f"<filter id='D' filterUnits='userSpaceOnUse' x='0' y='{MAP_Y}' width='{W}' height='{MAP_DY + MAP_H}'>"
    f"<feOffset dy='-{MAP_DY}'/><feColorMatrix values='1 0 0 0 0 0 {BUMP_GAIN:g} 0 0 "
    f"{128 / 255 * (1 - BUMP_GAIN):.4f} 0 0 1 0 0 0 0 0 1 0' result='m'/>"
    f"<feDisplacementMap in='SourceGraphic' in2='m' scale='{BUMP / BUMP_GAIN:.0f}' "
    "xChannelSelector='R' yChannelSelector='G'/></filter>",
]
for m in range(8):
    frames = [column_frame(m, k) for k in range(FRAMES)]
    defs.append(
        f"<path id='c{m}' vector-effect='non-scaling-stroke' d='{frames[0]}'>"
        f"<animate attributeName='d' dur='{T}s' repeatCount='indefinite' "
        f"values='{';'.join(frames + frames[:1])}'/></path>"
    )

backdrop = [
    f"<rect y='{Y_H - 8}' width='{W}' height='{H}' fill='url(#w)'/>",
    f"<path d='M0 {Y_H}H{W}' stroke='#9a7bff' stroke-width='10' stroke-opacity='.14'/>",
    f"<path d='M0 {Y_H}H{W}' stroke='#b9a6ff' stroke-width='1' stroke-opacity='.6'/>",
]
body = [  # everything here is lifted by the bumps
    # cross-hatch columns
    "<g stroke='url(#cg)' stroke-width='1'>"
    + "".join(f"<use href='#c{j % 8}' transform='translate({CX} 0) scale({j + 0.5:g} 1)'/>" for j in COLS)
    + "</g>",
]

# particle rows (in one group so the FILL copies can reuse them)
# Each row is one solid stroke painted with a stripe pattern, so the dots come
# from the paint instead of from geometry. Dotted strokes (dasharray 0 + round
# caps) made Chrome re-rasterize ~10k tiny caps per copy every frame: 19 fps
# at 1920x1080 against 125 fps for the same surface striped. The pattern is in
# the row's user space, so its dots slide with the row and shrink with the
# FILL copies. Colour comes from a y gradient (depth is linear in y).
row_svg = []
pats = {}
for r in rows:
    s, i = r["s"], r["i"]
    t = (s - S_FAR) / (1 - S_FAR)  # 0 far .. 1 near
    dot = 0.9 + 2.4 * s
    gap = round(max(3, 8 * s) * 2) / 2
    op = 0.45 + 0.55 * t
    pid = pats.setdefault((int(i % 5 == 4), gap), f"q{len(pats)}")
    row_svg.append(
        f"<g class='r' style='--l:{LAM * s:.1f}px'><path d='{row_path(r)}' stroke='url(#{pid})' "
        f"stroke-width='{dot:.1f}' stroke-opacity='{op:.2f}'/></g>"
    )
body.append(f"<g id='R'>{''.join(row_svg)}</g>")
for acc, (a, b) in enumerate(((FAR, NEAR), (ACCENT_FAR, ACCENT_NEAR))):
    defs.append(f"<linearGradient id='y{acc}' gradientUnits='userSpaceOnUse' x2='0' y1='{rows[0]['yb']:.0f}' "
                f"y2='{Y_NEAR}'><stop stop-color='{mix(a, b, 0)}'/><stop offset='1' stop-color='{mix(a, b, 1)}'/>"
                "</linearGradient>")
for (acc, gap), pid in pats.items():
    defs.append(f"<pattern id='{pid}' patternUnits='userSpaceOnUse' width='{gap:g}' height='{H}'>"
                f"<rect width='{max(1.4, 0.42 * gap):.1f}' height='{H}' fill='url(#y{acc})'/></pattern>")
for f in FILL:
    body.append(f"<use href='#R' opacity='.75' transform='{fill_transform(f)}'/>")

# impulses: a flash of light as the hump peaks, plus two particle rings
# bursting from the same point. They sit in the displaced group, so the flash
# rises with the hump and the rings ride the real ring wave.
for x, i, delay in RIPPLES:
    s, yb = depth(i)
    rx = RING_R * s
    body.append(
        f"<ellipse class='f' style='animation-delay:{delay + 0.3:.1f}s' cx='{x}' cy='{yb:.0f}' "
        f"rx='{rx * 0.7:.0f}' ry='{rx * 0.7 * FLAT:.0f}' fill='url(#fg)'/>"
    )
    for ring, lag in ((1, 0), (0.62, 0.45)):
        body.append(
            f"<ellipse class='p' style='animation-delay:{delay - lag:.1f}s' cx='{x}' cy='{yb:.0f}' "
            f"rx='{rx * ring:.0f}' ry='{rx * ring * FLAT:.0f}' stroke='#bff6ff' stroke-width='{1.6 + 3 * s:.1f}' "
            f"stroke-dasharray='0 {4 + 7 * s:.1f}'/>"
        )

# the height map itself (see the defs above), out of sight below the viewBox
body.append(
    f"<g transform='translate(0 {MAP_DY})'><rect y='{MAP_Y}' width='{W}' height='{MAP_H}' fill='#808080'/>"
    + "".join(
        f"<use href='#I' style='--d:{delay:g}s' transform='translate({x} {depth(i)[1]:.0f}) "
        f"scale({depth(i)[0]:.3g} {depth(i)[0] * FLAT:.3g})'/>"
        for x, i, delay in RIPPLES
    )
    + f"<rect y='{MAP_Y}' width='{W}' height='{MAP_H}' fill='url(#u)'/></g>"
)

svg = (
    f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' preserveAspectRatio='none' "
    f"fill='none' stroke-linecap='round'>{style}<defs>{''.join(defs)}</defs>{''.join(backdrop)}"
    f"<g filter='url(#D)'>{''.join(body)}</g></svg>"
)
uri = urllib.parse.quote(svg, safe=" =:/'.,-;()")

css = f"""
/* Particle-wave ocean (generated by gen_ocean.py). All motion runs inside the
   SVG; the CSS animation is a slow camera bob from the bottom edge. */
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
print(f"wrote {sys.argv[1]}: svg {len(svg)} chars, encoded {len(uri)} chars")
