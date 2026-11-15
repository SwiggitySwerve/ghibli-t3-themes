"""Build and preview one scene.

    python build_scene.py <slug> [t1 t2 t3 ...]

Imports scenes/<slug>.py, then writes to out/<slug>/:
  still.png    the static pixel layer at 5x (nearest-neighbour), after palette quantization
  sheet.png    2x2 contact sheet of the full animated scene at the given times (default 0 3 8 20 s)
  frame_<t>.png  each of those frames at full 1200x675, for judging small characters
  theme.png    the scene rendered through the real theme CSS (data: URL background + overlay) at t=0, 1200x800
  portrait.png same, in a narrow 600x900 window (shows what side-cropping leaves)
  wide.png     same, in a wide 1680x780 chat pane with the composer outlined (shows what top/bottom cropping leaves)
  app.png      a mock of the T3 Code window (sidebar, header, chat text, user bubble, composer) wearing the
               full theme: colours from THEME plus the theme CSS. Judge readability and chrome colours here.
  scene.svg    raw SVG
  theme.json   the publishable theme (name, colours, css)
Prints the size budget: the theme's whole css must stay within lib.THEME_CSS_LIMIT (20,000) characters.
Optional scene attributes: SIZE = (w, h) for a larger 16:9 canvas (default 240x135); THEME = {'canvas', 'accent',
'overlay'?, 'colors'?} (see BRIEF.md).
"""
import importlib.util, os, subprocess, sys, tempfile
from PIL import Image
import json, re
from lib import THEME_CSS_LIMIT, UNPAINTED, W, H, encode_png, scene_svg, svg_escape, theme_css

DEFAULT_THEME = {"canvas": "#0b1020", "accent": "#f4c66a"}
HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
VIEW_W, VIEW_H = 1200, 675


def load(slug):
    spec = importlib.util.spec_from_file_location(slug, os.path.join(HERE, "scenes", slug + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def shoot(html_path, png_path, w=VIEW_W, h=VIEW_H):
    url = "file:///" + html_path.replace("\\", "/")
    # own throwaway profile so parallel builds don't collide; ignore_cleanup_errors because Chrome can hold a file briefly
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={w},{h}",
                        f"--user-data-dir={profile}",
                        "--virtual-time-budget=1500", f"--screenshot={png_path}", url],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=60)


# Pause every CSS animation at time T so a headless screenshot shows that exact frame.
SEEK = ("<script>const T={t};addEventListener('load',()=>{{for(const a of document.getAnimations())"
        "{{a.pause();a.currentTime=T*1000}}}})</script>")


def frame_html(svg, t):
    return (f"<!doctype html><html><body style='margin:0;background:#000'>"
            f"<div style='width:{VIEW_W}px;height:{VIEW_H}px'>{svg.replace('<svg ', '<svg width=\"100%\" height=\"100%\" ', 1)}</div>"
            f"{SEEK.format(t=t)}</body></html>")


def app_html(css, theme):
    """Rough stand-in for the T3 Code window, using the same stable selectors the theme CSS targets."""
    c = theme.get("colors", {})
    side = c.get("sidebar", theme["canvas"])
    text = c.get("text", "#e8eefc")
    mut = c.get("textMuted", "#9aa6c0")
    para = ("Here's the plan: first fix the rendering pipeline, then pilot one scene, then fan out. "
            "The harness writes still.png, sheet.png and theme.png so each agent can check its own work.")
    rows = "".join(f"<div data-thread-item style='padding:7px 10px;border-radius:6px;color:{text if i == 1 else mut};"
                   f"background:{c.get('sidebarRowSelected', 'rgba(255,255,255,.08)') if i == 1 else 'transparent'}'>{t}</div>"
                   for i, t in enumerate(["Fix login redirect", "Ghibli theme scenes", "Refactor build script",
                                          "Investigate flaky test", "Release notes draft"]))
    return f"""<!doctype html><html><body style='margin:0;font:14px/1.5 system-ui,sans-serif;color:{text};background:{theme['canvas']}'>
<div style='display:flex;width:1400px;height:860px'>
<aside data-slot=sidebar style='width:260px;background:{side};border-right:1px solid {c.get("sidebarBorder", "rgba(255,255,255,.08)")};padding:14px;box-sizing:border-box'>
<div style='font-weight:600;margin:0 0 12px'>T3 Code</div>{rows}</aside>
<main data-workspace-area=conversation style='flex:1;display:flex;flex-direction:column;position:relative'>
<header data-chat-header style='height:46px;display:flex;align-items:center;padding:0 18px;border-bottom:1px solid rgba(255,255,255,.08)'>Ghibli theme scenes</header>
<div class=messages-timeline-scroll style='flex:1;padding:24px 60px;display:flex;flex-direction:column;gap:18px'>
<div data-message-role=user style='align-self:flex-end;max-width:60%'><div data-user-message-bubble style='padding:10px 14px;border-radius:14px'>Lets make each scene its own theme with the full budget</div></div>
<div data-message-role=assistant class=chat-markdown style='max-width:72%'><p style='margin:0 0 10px'>{para}</p><p style='margin:0;color:{mut}'>Muted secondary text sits here too.</p>
<pre class=chat-markdown-codeblock style='margin:10px 0 0;padding:10px 12px;border-radius:8px;font:12.5px ui-monospace,monospace'>python build_scene.py spirited_away 0 10 25 45</pre></div>
</div>
<form data-chat-composer-form style='padding:0 60px 18px'><div data-slot=composer-host style='border:1px solid rgba(255,255,255,.15);border-radius:16px;padding:14px 16px;height:64px;color:{mut}'>Ask anything…
<span style='float:right;background:{theme["accent"]};color:#111;border-radius:999px;padding:2px 10px'>Send</span></div></form>
</main></div><style>{css}</style></body></html>"""


def build(slug, times):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        _build(slug, times, tmp)


def _build(slug, times, tmp):
    m = load(slug)
    out = os.path.join(HERE, "out", slug)
    os.makedirs(out, exist_ok=True)
    cv = m.draw()
    holes = sum(p == UNPAINTED for row in cv.px for p in row)
    if holes:
        ys = [y for y, row in enumerate(cv.px) if UNPAINTED in row]
        print(f"WARNING: {holes} unpainted pixels (rows {ys[0]}..{ys[-1]}) - they show as magenta in still.png")
    b64, quant = encode_png(cv.image(), getattr(m, "COLORS", 32))
    w, h = getattr(m, "SIZE", (W, H))
    assert (cv.w, cv.h) == (w, h), f"draw() returned {cv.w}x{cv.h} but SIZE is {w}x{h}"
    k = max(1, 1200 // w)
    quant.resize((quant.width * k, quant.height * k), Image.NEAREST).save(os.path.join(out, "still.png"))
    svg = scene_svg(b64, m.SPRITES, m.CSS, w, h)
    theme = {**DEFAULT_THEME, **getattr(m, "THEME", {})}
    css = theme_css(svg, theme)
    open(os.path.join(out, "scene.svg"), "w", encoding="utf-8").write(svg)

    frames = []
    for i, t in enumerate(times):
        hp = os.path.join(tmp, f"f{i}.html")
        open(hp, "w", encoding="utf-8").write(frame_html(svg, t))
        pp = os.path.join(tmp, f"f{i}.png")
        shoot(hp, pp)
        frames.append(Image.open(pp).convert("RGB"))
        frames[-1].save(os.path.join(out, f"frame_{t:g}.png"))
    sheet = Image.new("RGB", (VIEW_W, VIEW_H), "black")
    for i, f in enumerate(frames[:4]):
        sheet.paste(f.resize((VIEW_W // 2, VIEW_H // 2)), ((i % 2) * VIEW_W // 2, (i // 2) * VIEW_H // 2))
    sheet.save(os.path.join(out, "sheet.png"))

    # theme: a typical window; portrait: a narrow one (sides cropped); wide: a wide, short chat pane like a
    # maximised window with the sidebar open (top/bottom cropped), with the composer's footprint outlined.
    composer = ("<div style='position:absolute;left:50%;bottom:16px;width:570px;height:86px;margin-left:-285px;"
                "border:2px dashed #f0f;border-radius:16px;background:rgba(10,10,20,.5)'></div>")
    for name, (vw, vh) in {"theme": (1200, 800), "portrait": (600, 900), "wide": (1680, 780)}.items():
        hp = os.path.join(tmp, name + ".html")
        open(hp, "w", encoding="utf-8").write(
            f"<!doctype html><html><body style='margin:0;background:#f0f'>"
            f"<div data-workspace-area=conversation style='position:relative;width:{vw}px;height:{vh}px'>"
            f"{composer if name == 'wide' else ''}</div>"
            f"<style>{css}</style></body></html>")
        shoot(hp, os.path.join(out, name + ".png"), vw, vh)
    hp = os.path.join(tmp, "app.html")
    open(hp, "w", encoding="utf-8").write(app_html(css, theme))
    shoot(hp, os.path.join(out, "app.png"), 1400, 860)

    json.dump({"version": 1, "name": "Ghibli · " + m.NAME, "appearance": "dark", "canvas": theme["canvas"],
               "accent": theme["accent"], **({"colors": theme["colors"]} if "colors" in theme else {}), "css": css},
              open(os.path.join(out, "theme.json"), "w", encoding="utf-8"), ensure_ascii=False)
    # T3 rejects theme CSS containing any url() that isn't data: or a literal #id, including url(%23id)
    # references inside the embedded SVG, plus @import and image-set().
    bad = sorted({u[:24] for u in re.findall(r"url\(\s*(?!['\"]?(?:data:|#))[^)]*\)", css, re.I)}
                 | set(re.findall(r"@import|image-set\(", css, re.I)))
    if bad:
        print(f"VALIDATOR FAIL: T3 will refuse this theme. Remove these (no clip-path/mask/fill/marker url(#id) "
              f"references inside the SVG; use nested <svg> viewports, <use>, or baked PNGs instead): {bad}")
    sprite_len = len(svg_escape(m.SPRITES + m.CSS))
    print(f"{slug}: png base64 {len(b64)} + sprites/css {sprite_len} -> theme css {len(css)} / {THEME_CSS_LIMIT}"
          f" {'OK' if len(css) <= THEME_CSS_LIMIT else 'OVER BUDGET'}")
    print(f"frames at t={times} -> {out}")


if __name__ == "__main__":
    build(sys.argv[1], [float(a) for a in sys.argv[2:]] or [0, 3, 8, 20])
