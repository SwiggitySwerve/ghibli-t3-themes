// Bake the purple aurora glow for Nyx · Aurora Ocean into nyx/glow.css.
// Usage: node nyx/tools/bake_glow.mjs
//
// The glow is the stock sky art (the --a image in base/nyx.json) blurred,
// brightened and saturated, screen-blended over the sky. Applying that blur as
// a live CSS filter means the GPU re-blurs a layer larger than the window on
// every frame, which was the single largest cost in the theme. This tool does
// the blur, brightness and saturation once on a canvas and writes the result
// as a WebP; the theme keeps only a hue-rotate filter for the colour drift.
//
// The blur radius is in art pixels: the CSS blur was 14px on art drawn about
// 5.7 CSS px per art pixel (an ultrawide window), so about 2.4 art pixels.
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
  const W = img.width, H = img.height;
  const c = document.createElement("canvas");
  c.width = W; c.height = H;
  const ctx = c.getContext("2d");
  ctx.filter = "blur(2.4px) brightness(1.45) saturate(1.6)";
  ctx.drawImage(img, 0, 0);
  // the CSS layer was transparent outside the art; keep the alpha the blur makes
  return c.toDataURL("image/webp", 0.8);
})()`);
if (!url?.startsWith("data:image/webp")) throw new Error("bake failed");
const out = join(NYX, "glow.css");
writeFileSync(out, `\n/* purple aurora glow image, baked by tools/bake_glow.mjs */\n.dark [data-slot="sidebar"][data-side="left"]::before { background-image: url(${url}); }\n`);
console.log(`wrote ${out}: image ${url.length} chars`);
