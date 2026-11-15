"""Shared pixel-art helpers for scene files. Canvas is 240x135 (16:9)."""
import base64, io, math, random
from PIL import Image

W, H = 240, 135
UNPAINTED = (255, 0, 255)  # canvas starts magenta; build_scene warns about any pixel left this colour


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) if isinstance(c, str) else c


class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.px = [[UNPAINTED] * w for _ in range(h)]

    def get(self, x, y):
        return self.px[y][x]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = hx(c)

    def rect(self, x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.set(x, y, c)

    def bands(self, y0, y1, cols):
        """Vertical gradient as flat colour bands with checker-dithered seams."""
        n, span = len(cols), (y1 - y0) / len(cols)
        for y in range(y0, y1):
            t = (y - y0) / span
            i = min(int(t), n - 1)
            f = t - i
            for x in range(self.w):
                c = cols[i]
                if i + 1 < n and f > 0.75 and (x + y) % 2 == 0:
                    c = cols[i + 1]
                if i > 0 and f < 0.2 and (x + y) % 2 == 0:
                    c = cols[i - 1]
                self.set(x, y, c)

    def ridge(self, base, waves, c, seed, rough=1, top=None):
        """Fill below a wavy profile y = base + sum(a*sin(x*f+p)). Returns the profile list."""
        r = random.Random(seed)
        prof, j = [], 0
        for x in range(self.w):
            y = base + sum(a * math.sin(x * f + p) for a, f, p in waves)
            if rough:
                j = max(-rough, min(rough, j + r.choice((-1, 0, 0, 1))))
            prof.append(int(round(y + j)))
        for x, yt in enumerate(prof):
            for y in range(yt, self.h):
                self.set(x, y, c)
            if top:
                self.set(x, yt, top)
        return prof

    def blob(self, circles, hi, mid, lo, light=(-0.55, -0.83)):
        """Union of circles, each shaded in 3 tones by a light direction (clouds, canopies)."""
        for cx, cy, r in circles:
            for y in range(int(cy - r) - 1, int(cy + r) + 2):
                for x in range(int(cx - r) - 1, int(cx + r) + 2):
                    dx, dy = x + 0.5 - cx, y + 0.5 - cy
                    if math.hypot(dx, dy) <= r:
                        k = (dx * light[0] + dy * light[1]) / r
                        self.set(x, y, hi if k > 0.3 else (mid if k > -0.35 else lo))

    def paint(self, rows, palette, x0, y0, flip=False):
        """Stamp ASCII pixel art. rows: list of equal-length strings; palette: {char: '#rrggbb'};
        any char not in palette (e.g. '.') is transparent."""
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row[::-1] if flip else row):
                if ch in palette:
                    self.set(x0 + dx, y0 + dy, palette[ch])

    def image(self):
        img = Image.new("RGB", (self.w, self.h))
        img.putdata([p for row in self.px for p in row])
        return img


def sprite(rows, palette, x0=0, y0=0, flip=False):
    """ASCII pixel art -> compact SVG (one <path> per colour, horizontal runs).
    Use it to build SPRITES in Python: SPRITES = f"<g class='xx-walk'>{sprite(ART, PAL, 40, 90)}</g>"."""
    runs = {}
    for dy, row in enumerate(rows):
        row = row[::-1] if flip else row
        x = 0
        while x < len(row):
            ch = row[x]
            n = 1
            while x + n < len(row) and row[x + n] == ch:
                n += 1
            if ch in palette:
                runs.setdefault(ch, []).append(f"M{x0 + x} {y0 + dy}h{n}v1h-{n}z")
            x += n
    return "".join(f"<path fill='{palette[c]}' d='{''.join(d)}'/>" for c, d in runs.items())


def encode_png(img, colors=32):
    """Quantize to a palette PNG and return base64 text."""
    q = img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    buf = io.BytesIO()
    q.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode(), q.convert("RGB")


def svg_escape(s):
    """Make raw SVG text safe inside a CSS url("data:image/svg+xml,...").
    '</style' is escaped so the CSS also survives being pasted into an HTML <style> tag."""
    return (s.replace("%", "%25").replace("#", "%23").replace('"', "'")
            .replace("</style", "%3C/style").replace("\n", ""))


THEME_CSS_LIMIT = 20000  # T3 Code's cap on a theme's `css` field


def theme_css(svg, theme):
    """The full `css` for a one-scene T3 theme: the scene as the chat background plus glassy chat chrome.
    theme: {'canvas': '#hex', 'accent': '#hex', 'overlay': '#hex' (optional, defaults to canvas),
            'position': CSS background-position (optional, default 'center bottom'). In windows wider than 16:9
            the image is cropped vertically; e.g. 'center 30%' takes 30% of that crop from the top instead of all of it}."""
    o = ",".join(map(str, hx(theme.get("overlay", theme["canvas"]))))
    a = ",".join(map(str, hx(theme["accent"])))
    pos = theme.get("position", "center bottom")
    return (
        f"[data-workspace-area=\"conversation\"]{{background:linear-gradient(rgba({o},.42),rgba({o},.55)),"
        f"url(\"data:image/svg+xml,{svg_escape(svg)}\") {pos}/cover no-repeat {theme['canvas']}!important}}\n"
        "[data-workspace-area=\"conversation\"] .messages-timeline-scroll,[data-chat-header]{background:transparent!important}\n"
        "[data-chat-header]{backdrop-filter:blur(6px)}\n"
        f"[data-user-message-bubble]{{background:rgba({o},.8)!important;border:1px solid rgba({a},.35)!important;backdrop-filter:blur(4px)}}\n"
        ".chat-markdown{text-shadow:0 1px 2px rgba(0,0,0,.95),0 0 6px rgba(0,0,0,.6)}\n"
        f".chat-markdown-codeblock{{background:rgba({o},.88)!important}}\n"
        f"[data-slot=\"composer-host\"]{{background:rgba({o},.82)!important;backdrop-filter:blur(8px);border-color:rgba({a},.4)!important}}")


def scene_svg(png_b64, sprites, css, w=W, h=H):
    """One scene as raw SVG: the pixel PNG plus animated vector sprites on top."""
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' preserveAspectRatio='xMidYMax slice' "
            f"shape-rendering='crispEdges'><style>image{{image-rendering:pixelated}}{css}</style>"
            f"<image width='{w}' height='{h}' href='data:image/png;base64,{png_b64}'/>{sprites}</svg>")
