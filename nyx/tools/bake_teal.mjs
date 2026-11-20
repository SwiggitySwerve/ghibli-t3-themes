// Bake the teal aurora stream for Nyx · Aurora Ocean into nyx/teal-stream.css.
// Usage: node nyx/tools/bake_teal.mjs
//
// The stream is the stock Nyx sky art (the --a image in base/nyx.json) turned
// 90 degrees clockwise, blurred, and recoloured from purple to teal. Doing that
// live in CSS needs a blur and hue filter on a large layer, which the GPU has to
// redo every frame while the layer moves. Baking it here into a small WebP
// leaves the theme only a transform and opacity animation to run.
//
// Recolouring maps each pixel's brightness through a teal palette, greener
// toward the streak tips on the left and bluer toward the band on the right,
// so the stream has more colour depth than a flat hue shift.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromeEval } from "./chrome_eval.mjs";

const NYX = join(dirname(fileURLToPath(import.meta.url)), "..");

const baseCss = JSON.parse(readFileSync(join(NYX, "base", "nyx.json"), "utf8")).css;
const art = baseCss.match(/--a:\s*url\((data:image\/png;base64,[A-Za-z0-9+/=]+)\)/)[1];

const bake = `(async () => {
  const img = new Image();
  img.src = ${JSON.stringify(art)};
  await img.decode();
  // portrait canvas at a quarter of the art's size: the blur hides the low
  // resolution once the browser scales it up
  const W = 135, H = 240;
  const c = document.createElement("canvas");
  c.width = W; c.height = H;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, W, H);
  ctx.filter = "blur(2px)";
  ctx.setTransform(0, 1, -1, 0, W, 0); // 90 degrees clockwise: art (x, y) lands at (W - y, x)
  ctx.drawImage(img, 0, 0, H, W);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.filter = "none";

  const d = ctx.getImageData(0, 0, W, H);
  const px = d.data;
  const lum = new Float32Array(W * H);
  for (let i = 0; i < W * H; i++) lum[i] = Math.max(px[i * 4], px[i * 4 + 1], px[i * 4 + 2]) / 255;
  const peak = Float32Array.from(lum).sort()[Math.floor(W * H * 0.995)] || 1;

  // brightness stops 0, 0.2, 0.45, 0.7, 1
  const green = [[0, 0, 0], [2, 40, 34], [10, 122, 92], [46, 224, 168], [200, 255, 236]];
  const cyan = [[0, 0, 0], [4, 33, 63], [10, 106, 138], [36, 208, 214], [216, 255, 250]];
  const stops = [0, 0.2, 0.45, 0.7, 1];
  const ramp = (pal, t) => {
    let k = 0;
    while (k < stops.length - 2 && t > stops[k + 1]) k++;
    const f = (t - stops[k]) / (stops[k + 1] - stops[k]);
    return pal[k].map((v, j) => v + (pal[k + 1][j] - v) * f);
  };
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = y * W + x;
      // drop the faint sky floor so the dark sky stays black under screen blending
      // the 0.7 power lifts the dim streaks under the band more than the band itself
      const t = Math.min(1, Math.max(0, (lum[i] / peak - 0.08) / 0.92)) ** 0.7;
      const mix = x / (W - 1);
      const a = ramp(green, t), b = ramp(cyan, t);
      for (let j = 0; j < 3; j++) px[i * 4 + j] = Math.round(a[j] + (b[j] - a[j]) * mix);
      px[i * 4 + 3] = 255;
    }
  }
  ctx.putImageData(d, 0, 0);
  return c.toDataURL("image/webp", 0.75);
})()`;

const url = await chromeEval(bake);
if (!url?.startsWith("data:image/webp")) throw new Error("bake failed");
const out = join(NYX, "teal-stream.css");
writeFileSync(out, `
/* teal aurora stream image, baked by tools/bake_teal.mjs */
.dark [data-slot="sidebar-inset"]::before { background-image: url(${url}); }
`);
console.log(`wrote ${out}: image ${url.length} chars`);
