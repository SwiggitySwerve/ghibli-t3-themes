"""Make a theme's CSS animations advance in steps at a fixed frame rate.

Chromium redraws an animated page at the display rate. For the Nyx layers that
means compositing several full-window blended layers (one with a live blur)
60 times a second, which keeps an iGPU busy even though the motion is slow.
A steps() timing function only changes the value FPS times a second, and
when nothing changes between display frames Chromium skips the redraw.

steps() replaces the easing, though, so each eased stretch of an animation is
split into shorter linear pieces (about SAMPLE seconds each) that follow the
original curve, and every piece is stepped. All step boundaries sit on one
grid of 1/FPS seconds from the start of the animation, shifted half a step so
they land between display frames rather than on them: a boundary landing
exactly on a frame tick can round into either neighbouring frame, and the page
is redrawn twice.

Only the CSS outside url(...) is touched, so the ocean SVG's own stepped
animations are left alone.

    from step_motion import step_motion
    css = step_motion(css, fps=20)
"""
import math
import re

KEYWORDS = {
    "linear": None,
    "ease": (0.25, 0.1, 0.25, 1),
    "ease-in": (0.42, 0, 1, 1),
    "ease-out": (0, 0, 0.58, 1),
    "ease-in-out": (0.42, 0, 0.58, 1),
}
NUM = re.compile(r"-?(?:\d+\.?\d*|\.\d+)([a-z%]*)")


def bezier(p1x, p1y, p2x, p2y):
    """Return y(x) for a CSS cubic-bezier."""
    def coord(t, a, b):
        return 3 * a * t * (1 - t) ** 2 + 3 * b * t * t * (1 - t) + t ** 3

    def y_at(x):
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if coord(mid, p1x, p2x) < x:
                lo = mid
            else:
                hi = mid
        return coord((lo + hi) / 2, p1y, p2y)
    return y_at


def easing(tf):
    tf = tf.strip()
    if tf in KEYWORDS:
        pts = KEYWORDS[tf]
        return (lambda u: u) if pts is None else bezier(*pts)
    m = re.fullmatch(r"cubic-bezier\(([^)]*)\)", tf)
    if not m:
        raise ValueError(f"unsupported timing function {tf!r}")
    return bezier(*(float(v) for v in m.group(1).split(",")))


def split_top(s, sep):
    """Split on sep outside parentheses."""
    out, depth, cur = [], 0, ""
    for ch in s:
        depth += (ch == "(") - (ch == ")")
        if ch == sep and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [p.strip() for p in out if p.strip()]


def normalize(value):
    # scale(a) and scale(a, b) must share one shape to be interpolated
    return re.sub(r"scale\(\s*([^,()]+?)\s*\)", r"scale(\1, \1)", value)


def lerp_value(a, b, f):
    a, b = normalize(a), normalize(b)
    ta, tb = NUM.sub("#", a), NUM.sub("#", b)
    if ta != tb:
        raise ValueError(f"cannot interpolate {a!r} and {b!r}")
    na, nb = list(NUM.finditer(a)), list(NUM.finditer(b))
    parts, last = [], 0
    for ma, mb in zip(na, nb):
        unit = ma.group(1) or mb.group(1)
        if ma.group(1) and mb.group(1) and ma.group(1) != mb.group(1):
            raise ValueError(f"unit mismatch in {a!r} and {b!r}")
        va = float(ma.group(0)[: len(ma.group(0)) - len(ma.group(1))])
        vb = float(mb.group(0)[: len(mb.group(0)) - len(mb.group(1))])
        v = va + (vb - va) * f
        parts.append(a[last:ma.start()])
        parts.append(f"{round(v, 4):g}{unit if v != 0 or unit in ('deg', '%') else ''}")
        last = ma.end()
    parts.append(a[last:])
    return "".join(parts)


def parse_keyframes(body):
    """{property: [(offset, value)]} from a keyframes body."""
    props = {}
    for sel, decls in re.findall(r"([^{}]+)\{([^{}]*)\}", body):
        offsets = [0.0 if s.strip() == "from" else 1.0 if s.strip() == "to" else float(s.strip().rstrip("%")) / 100
                   for s in sel.split(",")]
        for decl in split_top(decls, ";"):
            prop, val = (x.strip() for x in decl.split(":", 1))
            for o in offsets:
                props.setdefault(prop, []).append((o, val))
    for prop, frames in props.items():
        frames.sort()
        if frames[0][0] != 0 or frames[-1][0] != 1:
            raise ValueError(f"{prop} needs values at 0% and 100%")
    return props


def sample(frames, t, ease):
    for (o0, v0), (o1, v1) in zip(frames, frames[1:]):
        if o0 <= t <= o1 and o1 > o0:
            return lerp_value(v0, v1, ease((t - o0) / (o1 - o0)))
    return frames[-1][1]


def stepped_keyframes(props, duration, tf, fps, sample_s):
    ease = easing(tf)
    total = round(duration * fps)  # frames in one iteration
    marks = sorted({round(o * total) for frames in props.values() for o, _ in frames})
    grid = []
    for a, b in zip(marks, marks[1:]):
        pieces = 1 if tf == "linear" else max(1, math.ceil((b - a) / (sample_s * fps)))
        grid += [a + round((b - a) * k / pieces) for k in range(pieces)]
    grid = sorted(set(grid + [total]))
    out = []
    for i, f in enumerate(grid):
        t = f / total
        decls = [f"{p}:{sample(frames, t, ease)}" for p, frames in props.items()]
        if i + 1 < len(grid):
            decls.append(f"animation-timing-function:steps({grid[i + 1] - f})")
        out.append(f"{round(100 * t, 3):g}%{{{';'.join(decls)}}}")
    return "".join(out)


def step_motion(css, fps=20, sample_s=3):
    urls = []

    def stash(m):
        urls.append(m.group(0))
        return f"url(\0{len(urls) - 1}\0)"
    css = re.sub(r"""url\((?:"[^"]*"|'[^']*'|[^)"']*)\)""", stash, css)

    keyframes = {m.group(1): m.group(2) for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", css)}
    made = {}

    def convert(entry):
        words = split_top(entry, " ")
        name = next(w for w in words if w in keyframes)
        times = [float(w[:-2]) / 1000 if w.endswith("ms") else float(w[:-1])
                 for w in words if re.fullmatch(r"-?[\d.]+m?s", w)]
        duration, delay = times[0], (times[1] if len(times) > 1 else 0.0)
        tf = next((w for w in words if w in KEYWORDS or w.startswith("cubic-bezier(") or w.startswith("steps(")), "ease")
        if tf.startswith("steps("):
            return entry
        rest = [w for w in words if w in ("infinite", "alternate", "reverse", "alternate-reverse", "both", "forwards", "backwards")
                or re.fullmatch(r"\d+", w)]
        if abs(duration * fps - round(duration * fps)) > 1e-6 or abs(delay * fps - round(delay * fps)) > 1e-6:
            raise ValueError(f"{entry!r}: duration and delay must be whole frames at {fps} fps")
        key = (name, duration, tf)
        if key not in made:
            new = f"{name}-s{len(made)}"
            made[key] = new
            keyframes_out.append(f"@keyframes {new}{{{stepped_keyframes(parse_keyframes(keyframes[name]), duration, tf, fps, sample_s)}}}")
        return " ".join([made[key], f"{duration:g}s", "linear", f"{delay - 0.5 / fps:g}s", *rest])

    keyframes_out = []

    def rewrite(m):
        return m.group(1) + ", ".join(convert(e) for e in split_top(m.group(2), ","))
    css = re.sub(r"(\banimation\s*:\s*)([^;}]*?(?=\s*!important|\s*[;}]))",
                 lambda m: m.group(0) if m.group(2).strip() in ("none",) else rewrite(m), css)
    # the stepped copies replace the originals
    for name in {k[0] for k in made}:
        css = re.sub(r"@keyframes\s+" + re.escape(name) + r"\s*\{(?:[^{}]*\{[^{}]*\})*\s*\}", "", css)
    css += "".join(keyframes_out)
    return re.sub("url\\(\0(\\d+)\0\\)", lambda m: urls[int(m.group(1))], css)
