// Rough cost check for a whole theme: load a built theme JSON into a page shaped
// like T3's layout (sidebar, glass, chat, composer) and play it in headless Chrome.
// Usage: node perf_theme.mjs <theme.json> [seconds=8] [width=2752] [height=1152] [dpr=1.25]
// Prints the page's rAF rate and worst frame, CPU per Chrome process type, and
// GPU engine utilization of Chrome's GPU process (Windows perf counters). Compare
// the GPU process and renderer CPU between builds; the utilization figure moves
// with the iGPU's clock, and other apps animating on the same GPU skew it.
import { spawn, execFile } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, basename } from "node:path";

const [themePath, secArg = "8", wArg = "2752", hArg = "1152", dprArg = "1.25"] = process.argv.slice(2);
const seconds = Number(secArg);
const theme = JSON.parse(readFileSync(themePath, "utf8"));
const css = theme.css ?? "";

const lorem = "The quick brown fox jumps over the lazy dog while the build runs and the tests pass. ";
const msgs = Array.from({ length: 8 }, (_, i) =>
  `<div data-timeline-row-kind="message" data-message-role="${i % 2 ? "assistant" : "user"}" style="margin:18px 0">
     ${i % 2 ? `<div class="chat-markdown">${lorem.repeat(4)}</div>` : `<div data-user-message-bubble style="padding:10px 14px;margin-left:30%">${lorem}</div>`}
   </div>`).join("");
const threads = Array.from({ length: 24 }, (_, i) =>
  `<div data-thread-item style="padding:6px 12px"><a ${i === 3 ? 'aria-current="page"' : ""} style="display:block;padding:4px 8px">Thread number ${i} about something</a></div>`).join("");

const html = `<!doctype html><html class="dark" data-theme-id="x"><head><style>
:root{--glass-blur:16px;--glass-saturation:1.14;--glass-opacity:80%;--font-sans:system-ui}
body{margin:0;background:#000;color:#e6e2ff;font:14px/1.5 system-ui;overflow:hidden}
.surface-glass{backdrop-filter:blur(var(--glass-blur)) saturate(var(--glass-saturation))}
</style><style>${css}</style></head><body>
<div data-slot="sidebar-wrapper" style="display:flex;min-height:100vh;width:100%">
  <div data-slot="sidebar" data-side="left" style="width:300px;flex:none">
    <div data-slot="sidebar-gap" style="width:300px;height:100%"></div>
    <div data-slot="sidebar-container" style="position:fixed;inset:0 auto 0 0;width:300px;z-index:10;border-right:1px solid">
      <div data-slot="sidebar-inner" style="height:100%;overflow:hidden">${threads}</div>
    </div>
  </div>
  <main data-slot="sidebar-inset" style="flex:1;position:relative;display:flex;flex-direction:column;height:100vh">
    <div data-chat-canvas style="flex:1;display:flex;flex-direction:column;min-height:0">
      <div data-chat-column style="flex:1;display:flex;flex-direction:column;min-height:0">
        <header data-chat-header style="height:48px;padding:0 16px;display:flex;align-items:center">Chat title</header>
        <div data-workspace-area="conversation" style="flex:1;min-height:0;position:relative">
          <div class="messages-timeline-scroll" style="height:100%;overflow:auto;padding:0 12%">${msgs}</div>
        </div>
        <form data-chat-composer-form style="padding:12px 12% 18px">
          <div data-chat-composer-stack style="position:relative">
            <div data-slot="composer-host" class="surface-glass" style="position:relative;height:110px;border-radius:18px;border:1px solid #ffffff1a">
              <div data-slot="composer-shell" style="position:absolute;inset:0;border-radius:18px"></div>
            </div>
          </div>
        </form>
      </div>
    </div>
  </main>
</div></body></html>`;

const dir = mkdtempSync(join(tmpdir(), "nyx-perf-"));
const page = join(dir, "page.html");
writeFileSync(page, html);

const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
  "--headless=new", `--user-data-dir=${join(dir, "profile")}`, `--remote-debugging-port=${port}`,
  `--window-size=${wArg},${hArg}`, `--force-device-scale-factor=${dprArg}`, "--hide-scrollbars",
  "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
  "file:///" + page.replaceAll("\\", "/"),
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function json(path) {
  for (let i = 0; i < 60; i++) {
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

// Sum of GPU engine utilization (all engines, 3D mostly) for one pid, sampled once a second.
function gpuCounter(pid, n) {
  return new Promise((resolve) => {
    const ps = `$s = Get-Counter -Counter '\\GPU Engine(pid_${pid}_*)\\Utilization Percentage' -SampleInterval 1 -MaxSamples ${n} -ErrorAction SilentlyContinue;` +
      `($s | % { ($_.CounterSamples | Measure-Object CookedValue -Sum).Sum } | Measure-Object -Average).Average`;
    execFile("powershell", ["-NoProfile", "-Command", ps], (err, out) => resolve(err ? NaN : Number(String(out).trim())));
  });
}

try {
  const version = await json("/json/version");
  const targets = await json("/json/list");
  const browser = await connect(version.webSocketDebuggerUrl);
  const tab = await connect(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
  await sleep(3000);
  const info = await browser.send("SystemInfo.getProcessInfo");
  const gpuPid = info.processInfo.find((p) => p.type === "GPU")?.id;
  const cpu = async () => Object.fromEntries((await browser.send("SystemInfo.getProcessInfo")).processInfo.map((p) => [`${p.type}:${p.id}`, p.cpuTime]));
  const before = await cpu();
  const gpuP = gpuPid ? gpuCounter(gpuPid, Math.max(1, seconds - 1)) : Promise.resolve(NaN);
  const r = await tab.send("Runtime.evaluate", {
    awaitPromise: true, returnByValue: true,
    expression: `new Promise((done) => { const t0 = performance.now(); let n = 0, worst = 0, last = t0;
      const tick = (t) => { n++; worst = Math.max(worst, t - last); last = t;
        if (t - t0 < ${seconds * 1000}) requestAnimationFrame(tick); else done({ fps: n / ((t - t0) / 1000), worst }); };
      requestAnimationFrame(tick); })`,
  });
  const after = await cpu();
  const gpuUtil = await gpuP;
  const per = {};
  for (const [k, v] of Object.entries(after)) {
    const t = k.split(":")[0];
    per[t] = (per[t] ?? 0) + (v - (before[k] ?? 0)) / seconds;
  }
  const cpuStr = Object.entries(per).filter(([, v]) => v > 0.005).map(([k, v]) => `${k} ${(v * 100).toFixed(0)}%`).join(", ");
  const total = Object.values(per).reduce((a, b) => a + b, 0);
  console.log(`${basename(themePath).padEnd(34)} fps ${r.result.value.fps.toFixed(1).padStart(5)}  worst ${r.result.value.worst.toFixed(0).padStart(4)}ms  CPU total ${(total * 100).toFixed(0).padStart(3)}% (${cpuStr})  GPU ${isNaN(gpuUtil) ? "n/a" : gpuUtil.toFixed(1) + "%"}`);
  tab.close(); browser.close();
} finally {
  const exited = chrome.exitCode !== null ? Promise.resolve() : new Promise((r) => chrome.once("exit", r));
  chrome.kill();
  await exited;
  rmSync(dir, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
