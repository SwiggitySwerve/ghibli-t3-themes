// Bake the purple aurora glow for Nyx · Aurora Ocean into nyx/glow.css.
// Usage: node nyx/tools/bake_glow.mjs
//
// The glow is the stock sky art (the --a image in base/nyx.json) blurred,
// brightened and saturated, screen-blended over the sky. Applying that blur as
// a live CSS filter means the GPU re-blurs a layer larger than the window on
// every frame, which was the single largest cost in the theme. This tool does
// the blur, brightness and saturation once on a canvas and writes the result
// as a WebP.
//
// The glow was screen-blended, which needs an extra pass over a layer larger
// than the window on every step. Here each pixel's darkness becomes
// transparency instead (alpha = its brightest channel, colour scaled up to
// match), so normal blending lightens the sky by about as much.
//
// The image is half the art's size: it is a blur, and the half size keeps
// the alpha channel (stored losslessly) small. The blur radius is in those
// pixels: the CSS blur was 14px on art drawn about 5.7 CSS px per art pixel
// (an ultrawide window), so about 2.4 art pixels or 1.2 here.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromeEval } from "./chrome_eval.mjs";

const NYX = join(dirname(fileURLToPath(import.meta.url)), "..");
const baseCss = JSON.parse(readFileSync(join(NYX, "base", "nyx.json"), "utf8")).css;
const art = baseCss.match(/--a:\s*url\((data:image\/png;base64,[A-Za-z0-9+/=]+)\)/)[1];

const url = await chromeEval(`(async () => {
  const img = new Image();
  img.src = ${JSON.stringify(art)};
  await img.decode();
  const W = img.width / 2, H = img.height / 2;
  const c = document.createElement("canvas");
  c.width = W; c.height = H;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, W, H);
  ctx.filter = "blur(1.2px) brightness(1.45) saturate(1.6)";
  ctx.drawImage(img, 0, 0, W, H);
  ctx.filter = "none";
  const d = ctx.getImageData(0, 0, W, H), p = d.data;
  for (let i = 0; i < p.length; i += 4) {
    const a = Math.max(p[i], p[i + 1], p[i + 2]);
    for (let j = 0; j < 3; j++) p[i + j] = a ? Math.round(p[i + j] * 255 / a) : 0;
    p[i + 3] = a;
  }
  ctx.putImageData(d, 0, 0);
  return c.toDataURL("image/webp", 0.8);
})()`);
if (!url?.startsWith("data:image/webp")) throw new Error("bake failed");
const out = join(NYX, "glow.css");
writeFileSync(out, `\n/* purple aurora glow image, baked by tools/bake_glow.mjs */\n.dark [data-slot="sidebar"][data-side="left"]::before { background-image: url(${url}); }\n`);
console.log(`wrote ${out}: image ${url.length} chars`);
