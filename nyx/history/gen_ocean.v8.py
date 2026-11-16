"""Generate variant-ocean.css: an animated SVG particle ocean along the bottom.

Crossing seas: several wave trains run through one another, each with its own
wavelength, height, heading and speed, seen in perspective (scale s = 1/z, so
rows bunch up toward the horizon).
- A row is a line of dots at one depth. It belongs to one train and carries
  that train's sine, which slides sideways rigidly. Trains take turns down the
  rows, so neighbouring rows wave out of step and their crests keep crossing.
- Each train is drawn once, in its own units, as a long sine. A row is a
  <use> of it, scaled by s and shifted to its depth and phase, so a row costs
  about 100 chars instead of a path of its own, and the one CSS animation on
  the sine (slide by a wavelength) moves every row of the train at the same
  world speed.
- Near rows are filled dark below their line and rows paint far to near, so a
  crest that rises over the rows behind it hides them: one wave in front of
  another instead of lines crossing.

The impulse version (bumps lifted by a displacement filter, cross-hatch
columns) is kept in gen_ocean.v7.py.

Usage: python -I gen_ocean.py <out.css>
"""
import math
import sys
import urllib.parse

W, H = 1600, 400          # viewBox
Y_H, Y_NEAR = 40, 372     # horizon and nearest row baseline
CX = 800                  # vanishing point x
ROWS = 72                 # depth slices over all trains, z = (1 + B i) ** GAMMA
Z_FAR = 8.36              # depth of the farthest row
GAMMA = 1.77              # how fast rows thin out toward the viewer: 1 would
                          # space them evenly in depth (few near, a crowd at the
                          # horizon); this leaves about 20 units between the
                          # nearest rows and under 1 at the horizon
T = 14                    # seconds per wave period at an 800-unit wavelength
HILL = 0.25               # rows of a train are 1 - 2 HILL .. 1 of its full height
FILL_S = 0.35             # rows at least this near are filled below their line
FILL = "#03030f", 0.6     # ... with this colour and opacity
TAU = 2 * math.pi

# One wave train per entry, in the order they take turns down the rows; the
# headings alternate so neighbouring rows run against each other.
#   lam   wavelength, world units (= screen units at s = 1)
#   amp   crest height, world units
#   slant phase = slant * ln z, so crests run diagonally into the distance;
#         opposite signs give the two diagonals, which is what makes two
#         trains read as crossing rather than as one train out of step
#   dir   +1 slides right, -1 left
#   hill  (rate, phase): row height = amp * (1 - HILL + HILL sin(rate ln z + phase)),
#         so every train has taller and lower rows, and now and then a tall
#         near row stands in front of low ones
#   far, near  dot colour at the horizon and at the viewer; one hue family per
#         train keeps them apart to the eye where they overlap
SEAS = [
    dict(id="a", lam=800, amp=56, slant=2.2, dir=1, hill=(2.4, 0.6), far=(0x6A, 0x4C, 0xFF), near=(0x5F, 0xE6, 0xFF)),
    dict(id="b", lam=1150, amp=48, slant=-2.8, dir=-1, hill=(3.1, 2.0), far=(0x8F, 0x5C, 0xFF), near=(0xD0, 0x8C, 0xFF)),
    dict(id="c", lam=430, amp=26, slant=5, dir=1, hill=(4.3, 4.0), far=(0x5C, 0x7C, 0xFF), near=(0x9F, 0xD0, 0xFF)),
    dict(id="d", lam=620, amp=34, slant=-6, dir=-1, hill=(3.7, 5.2), far=(0x4C, 0x8C, 0xFF), near=(0x7F, 0xFF, 0xE6)),
]
GAPS = [8, 13, 21, 34]    # dot pitch choices, in a train's own units
SHADES = 5                # colour steps from horizon to viewer per train


def mix(a, b, t):
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def wave(sea, s_min, closed):
    """The train's sine about y = 0, as relative smooth quadratics.

    Long enough to cover the view at scale s_min through any phase and a whole
    slide. It starts a whole number of wavelengths left of x = 0, so x = 0 is a
    zero crossing going up. A closed wave also runs down and back, far enough
    that the closing edges stay below the view; they are stroked like the rest.
    """
    lam, half = sea["lam"], sea["lam"] / 2
    n = math.ceil((W / s_min + 5 * lam) / lam) * 2
    x0 = -(n // 4) * lam
    drop = math.ceil((H - Y_H) / (FILL_S * (1 - 2 * HILL)) / 100) * 100
    return (f"M{x0:g} 0q{half / 2:g} {-2 * sea['amp']:g} {half:g} 0" + f"t{half:g} 0" * (n - 1)
            + (f"V{drop}H{x0:g}z" if closed else ""))


# Each train's sine twice: open and long for the far rows, closed and short for
# the near ones (a near row shows only a few wavelengths, and Chrome strokes the
# whole path, on screen or not). The slide is one wavelength per period, so it
# loops seamlessly, and the period follows deep-water waves: speed grows with
# the root of the wavelength, so the long trains overtake the short ones.
# `translate` (not `transform`) leaves the row's own scale alone. Only the
# position animates. Animating the height as well (a `scale` per row, so that
# sets of taller waves roll through) was tried: with all four trains doing it
# headless Chrome fell to a few frames a second. Why was not pinned down, so
# the heights stay fixed.
S_FAR = 1 / Z_FAR
style = "<style>.r{animation:m var(--t) linear infinite}@keyframes m{to{translate:var(--l)}}</style>"
defs = [
    "<linearGradient id='w' x1='0' y1='0' x2='0' y2='1'>"
    "<stop offset='0' stop-color='#000' stop-opacity='0'/>"
    "<stop offset='.15' stop-color='#04031a' stop-opacity='.55'/>"
    "<stop offset='1' stop-color='#020208' stop-opacity='.9'/></linearGradient>",
]
for sea in SEAS:
    slide = f"class='r' style='--l:{sea['dir'] * sea['lam']}px;--t:{T * math.sqrt(sea['lam'] / 800):.1f}s'"
    defs.append(f"<path id='{sea['id']}' {slide} d='{wave(sea, S_FAR, False)}'/>")
    defs.append(f"<path id='{sea['id'].upper()}' {slide} d='{wave(sea, FILL_S, True)}'/>")

# Rows, far to near so near rows paint on top. The dots come from the paint:
# a row is one solid stroke painted with a stripe pattern. (Dotted strokes,
# dasharray 0 + round caps, made Chrome re-rasterize thousands of tiny caps
# every frame: 19 fps against 125 for the same surface striped.) The pattern
# lives in the train's units, so its dots slide with the row and shrink with
# distance; a row picks the pitch that lands nearest 8 s px on screen (never
# under 3), and the stroke width is divided by the row's scale for the same
# reason. Colour and opacity are part of the pattern too, in SHADES steps.
B = (Z_FAR ** (1 / GAMMA) - 1) / (ROWS - 1)
pats, far_rows, near_rows = {}, [], []
for i in reversed(range(ROWS)):
    sea = SEAS[i % len(SEAS)]
    z = (1 + B * i) ** GAMMA
    s, lz = 1 / z, math.log(z)
    yb = Y_H + (Y_NEAR - Y_H) * s
    k = 1 - HILL + HILL * math.sin(sea["hill"][0] * lz + sea["hill"][1])
    t = max(0, (s - S_FAR) / (1 - S_FAR))  # 0 far .. 1 near
    gap = min(GAPS, key=lambda g: abs(g * s - max(3.2, 8 * s)) + (9 if g * s < 2.9 else 0))
    shade = round(math.sqrt(t) * SHADES)  # finer steps near the viewer, where rows are few and far apart
    pid = pats.setdefault((sea["id"], gap, shade), f"{sea['id']}{sum(1 for q in pats if q[0] == sea['id'])}")
    near = s >= FILL_S
    (near_rows if near else far_rows).append(
        f"<use href='#{sea['id'].upper() if near else sea['id']}' "
        f"transform='translate({CX - s * sea['lam'] * (sea['slant'] * lz / TAU % 1):.0f} {yb:.0f}) scale({s:.3g} {s * k:.3g})' "
        f"stroke='url(#{pid})' stroke-width='{(1 + 2.6 * s) / (s * k):.1f}'/>"
    )
for (sid, gap, shade), pid in pats.items():
    sea = next(x for x in SEAS if x["id"] == sid)
    t = (shade / SHADES) ** 2
    defs.append(f"<pattern id='{pid}' patternUnits='userSpaceOnUse' width='{gap}' height='9'>"
                f"<rect width='{0.44 * gap:.1f}' height='9' fill='{mix(sea['far'], sea['near'], t)}' "
                f"fill-opacity='{0.5 + 0.5 * t:.2f}'/></pattern>")

backdrop = [
    f"<rect y='{Y_H - 8}' width='{W}' height='{H}' fill='url(#w)'/>",
    f"<path d='M0 {Y_H}H{W}' stroke='#9a7bff' stroke-width='10' stroke-opacity='.14'/>",
    f"<path d='M0 {Y_H}H{W}' stroke='#b9a6ff' stroke-width='1' stroke-opacity='.6'/>",
]
# Only the near rows are filled. That is where a crest is tall enough to stand
# over the rows behind it, and their fills are small: a fill reaches from the
# row down to the bottom edge, so filling every row laid some 60 nearly
# full-size translucent layers over the view and more than halved the frame
# rate in a test.
# The fill is not opaque, so a wave that passes behind another dims instead
# of vanishing and both trains can still be followed through the crossing.
body = "".join(far_rows) + f"<g fill='{FILL[0]}' fill-opacity='{FILL[1]}'>{''.join(near_rows)}</g>"

svg = (
    f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' preserveAspectRatio='none' "
    f"fill='none'>{style}<defs>{''.join(defs)}</defs>{''.join(backdrop)}{body}</svg>"
)
uri = urllib.parse.quote(svg, safe=" =:/'.,-;()")

css = f"""
/* Particle ocean of crossing wave trains (generated by gen_ocean.py). All
   motion runs inside the SVG; the CSS animation is a slow camera bob from the
   bottom edge. */
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
print(f"wrote {sys.argv[1]}: svg {len(svg)} chars, encoded {len(uri)} chars, "
      f"{len(far_rows)} far rows + {len(near_rows)} near rows")
