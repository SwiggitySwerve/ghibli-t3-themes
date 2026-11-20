// Run one async expression in headless Chrome and return its value. Used by the
// bake_*.mjs tools, which draw theme images on a canvas.
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = process.env.CHROME ?? "C:/Program Files/Google/Chrome/Application/chrome.exe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function chromeEval(expression) {
  const dir = mkdtempSync(join(tmpdir(), "nyx-bake-"));
  const port = 9500 + Math.floor(Math.random() * 400);
  const chrome = spawn(CHROME, ["--headless=new", `--user-data-dir=${join(dir, "profile")}`, `--remote-debugging-port=${port}`, "about:blank"], { stdio: "ignore" });
  try {
    let targets;
    for (let i = 0; i < 60 && !targets?.length; i++) {
      try { targets = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).filter((t) => t.type === "page"); } catch { await sleep(200); }
    }
    const ws = new WebSocket(targets[0].webSocketDebuggerUrl);
    await new Promise((r) => (ws.onopen = r));
    const reply = new Promise((r) => (ws.onmessage = (e) => r(JSON.parse(e.data))));
    ws.send(JSON.stringify({ id: 1, method: "Runtime.evaluate", params: { expression, awaitPromise: true, returnByValue: true } }));
    const m = await reply;
    ws.close();
    if (m.result?.exceptionDetails) throw new Error(JSON.stringify(m.result.exceptionDetails).slice(0, 400));
    return m.result?.result?.value;
  } finally {
    const exited = chrome.exitCode !== null ? Promise.resolve() : new Promise((r) => chrome.once("exit", r));
    chrome.kill();
    await exited;
    // Chrome's helper processes can hold the profile a moment after exit; a
    // leftover temp folder is harmless
    try { rmSync(dir, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 }); } catch {}
  }
}
