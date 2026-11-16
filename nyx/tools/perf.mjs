// Rough cost check: play a variant-ocean.css as a full-width background in headless Chrome
// in real time and report requestAnimationFrame rate plus CPU time per Chrome process.
// Usage: node perf.mjs <variant-ocean.css> [seconds] [extra chrome flags...]
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [cssPath, secondsArg = "8", ...extra] = process.argv.slice(2);
const seconds = Number(secondsArg);
const css = readFileSync(cssPath, "utf8");
const uri = cssPath.endsWith(".svg") ? "data:image/svg+xml," + encodeURIComponent(css) : css.match(/data:image\/svg\+xml,[^"]+/)[0];
const dir = mkdtempSync(join(tmpdir(), "ocean-perf-"));
const page = join(dir, "page.html");
writeFileSync(page, `<!doctype html><html><body style="margin:0;background:#05040f;overflow:hidden">
<div style="position:fixed;left:0;right:0;bottom:0;height:40vh;background:url(&quot;${uri}&quot;) 0 0/100% 100% no-repeat"></div>
<div style="position:fixed;inset:0;background-image:linear-gradient(90deg,#000 1px,#0000 1px),linear-gradient(0deg,#000 1px,#0000 1px);background-size:4px 4px;background-position:right bottom"></div>
</body></html>`);

const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
  "--headless=new", `--user-data-dir=${join(dir, "profile")}`, `--remote-debugging-port=${port}`,
  "--window-size=1920,1080", "--hide-scrollbars", ...extra, "file:///" + page.replaceAll("\\", "/"),
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function json(path) {
  for (let i = 0; i < 50; i++) {
    try { return await (await fetch(`http://127.0.0.1:${port}${path}`)).json(); } catch { await sleep(200); }
  }
  throw new Error("chrome did not start");
}
function connect(url) {
  return new Promise((resolve) => {
    const ws = new WebSocket(url);
    let id = 0;
    const pending = new Map();
    ws.onmessage = (e) => {
      const m = JSON.parse(e.data);
      if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result ?? m.error); pending.delete(m.id); }
    };
    ws.onopen = () => resolve({
      send: (method, params = {}) => new Promise((r) => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); }),
      close: () => ws.close(),
    });
  });
}

try {
  const version = await json("/json/version");
  const targets = await json("/json/list");
  const browser = await connect(version.webSocketDebuggerUrl);
  const tab = await connect(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
  await sleep(2500);
  const gpu = await browser.send("SystemInfo.getInfo");
  const cpu = async () => Object.fromEntries((await browser.send("SystemInfo.getProcessInfo")).processInfo.map((p) => [`${p.type}:${p.id}`, p.cpuTime]));
  const before = await cpu();
  const r = await tab.send("Runtime.evaluate", {
    awaitPromise: true, returnByValue: true,
    expression: `new Promise((done) => { const t0 = performance.now(); let n = 0, worst = 0, last = t0;
      const tick = (t) => { n++; worst = Math.max(worst, t - last); last = t;
        if (t - t0 < ${seconds * 1000}) requestAnimationFrame(tick); else done({ fps: n / ((t - t0) / 1000), worst }); };
      requestAnimationFrame(tick); })`,
  });
  const after = await cpu();
  const use = Object.entries(after).map(([k, v]) => [k.split(":")[0], (v - (before[k] ?? 0)) / seconds])
    .filter(([, v]) => v > 0.005).map(([k, v]) => `${k} ${(v * 100).toFixed(0)}%`).join(", ");
  const d = gpu.gpu?.devices?.[0];
  console.log(`${cssPath.split(/[\\/]/).pop()}: rAF ${r.result.value.fps.toFixed(1)} fps, worst frame ${r.result.value.worst.toFixed(0)} ms; CPU per core: ${use}`);
  const aux = gpu.gpu?.auxAttributes ?? {};
  const fs = gpu.gpu?.featureStatus ?? {};
  console.log(`  gpu: ${d ? d.deviceString : "n/a"}; gl renderer: ${aux.glRenderer}; rasterization: ${fs.rasterization}; compositing: ${fs.gpu_compositing}; skia: ${aux.skiaBackendType}`);
  tab.close(); browser.close();
} finally {
  const exited = chrome.exitCode !== null ? Promise.resolve() : new Promise((r) => chrome.once("exit", r));
  chrome.kill();
  await exited;
  rmSync(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
