"""Render the generated ocean SVG at several animation times for inspection.

Writes one HTML page per time (the SVG as a CSS background, LED grid overlay
like the theme), screenshots each with headless Chrome at 1920x1080 after
letting it play for that long,
and stacks the bottom 45% of each into one contact sheet.

Usage: python -I render_ocean.py <variant-ocean.css> <out_dir> <t1> [t2 ...]
"""
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
css_path, out_dir, *times = sys.argv[1:]
os.makedirs(out_dir, exist_ok=True)
css = open(css_path, encoding="utf-8").read()
# Draw it the way the theme does, as a CSS background image. (In a minimal
# inline <svg> test Chrome did not update the bump filter as its height map
# animated; as a background image it does.)
uri = re.search(r'data:image/svg\+xml,[^"]+', css).group(0)
svg = (f"<div style=\"position:fixed;left:0;right:0;bottom:0;height:40vh;"
       f"background:url(&quot;{uri}&quot;) 0 0/100% 100% no-repeat\"></div>")

shots = []
profile = tempfile.mkdtemp(prefix="ocean-chrome-")
for t in times:
    html = f"""<!doctype html><html><body style="margin:0;background:#05040f;overflow:hidden">
{svg}
<div style="position:fixed;inset:0;background-image:linear-gradient(90deg,#000 1px,#0000 1px),linear-gradient(0deg,#000 1px,#0000 1px);background-size:4px 4px;background-position:right bottom"></div>
</body></html>"""
    # Let the page play for t seconds of virtual time instead of seeking:
    # seeking via getAnimations() misses CSS animations inside <use> clones.
    page = os.path.join(out_dir, f"t{t}.html")
    open(page, "w", encoding="utf-8").write(html)
    png = os.path.join(out_dir, f"t{t}.png")
    subprocess.run([CHROME, "--headless=new", f"--user-data-dir={profile}", "--hide-scrollbars",
                    "--window-size=1920,1080", f"--virtual-time-budget={int(float(t) * 1000)}",
                    f"--screenshot={png}", "file:///" + page.replace("\\", "/")],
                   check=True, capture_output=True, timeout=60)
    shots.append(png)

crops = [Image.open(p).crop((0, int(1080 * 0.55), 1920, 1080)) for p in shots]
sheet = Image.new("RGB", (1920, sum(c.height for c in crops) + 6 * (len(crops) - 1)), "#ff00ff")
y = 0
for c in crops:
    sheet.paste(c, (0, y))
    y += c.height + 6
sheet_path = os.path.join(out_dir, "sheet.png")
sheet.save(sheet_path)
print(sheet_path)
