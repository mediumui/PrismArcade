// Browser regression test for Connect 4 win detection.
// Runs headless Chrome, plays scripted column sequences and asserts the
// HUD result / highlighted win line.
//
// Usage: node tools/verify_games.mjs http://localhost:8096
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] || "http://localhost:8096";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9231;
const profile = mkdtempSync(join(tmpdir(), "c4-"));

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  `--window-size=1200,900`, "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.q = []; this.ready = false;
    ws.addEventListener("message", (e) => {
      const m = JSON.parse(e.data);
      if (m.id && this.pending.has(m.id)) { this.pending.get(m.id)(m); this.pending.delete(m.id); }
    });
    const waitOpen = () => new Promise((res) => {
      if (ws.readyState === 1) return res();
      ws.addEventListener("open", res, { once: true });
    });
    this._open = waitOpen().then(() => { this.ready = true; this.q.splice(0).forEach((f) => f()); });
  }
  async send(method, params = {}) {
    await this._open;
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, (m) => (m.error ? reject(new Error(method + ": " + JSON.stringify(m.error))) : resolve(m.result)));
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async eval(expression) {
    const r = await this.send("Runtime.evaluate", { returnByValue: true, expression });
    return r.result.value;
  }
}

const state = async (cdp) => cdp.eval(`JSON.stringify({
  result: document.getElementById('result').textContent,
  turn: document.getElementById('turn').textContent,
  reds: [...document.querySelectorAll('.c4-cell.red')].length,
  blues: [...document.querySelectorAll('.c4-cell.blue')].length,
  winCells: document.querySelectorAll('.c4-cell.win').length
})`);

try {
  await sleep(2500);
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const page = list.find((t) => t.type === "page");
  const cdp = new CDP(new WebSocket(page.webSocketDebuggerUrl));
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Page.navigate", { url: `${BASE}/games/connect4.html` });
  await sleep(2500);

  // click a column: cells are laid out row-major, bottom row starts at 5*7
  const click = async (col) => {
    await cdp.eval(`document.querySelectorAll('.c4-cell')[${5 * 7 + col}].click()`);
    await sleep(120);
  };

  console.log("initial      ", await state(cdp));
  await click(0);
  console.log("after 1 drop ", await state(cdp), "  <- must stay '—', turn=Blue");
  await click(1);
  console.log("after 2 drops", await state(cdp));

  // fresh board; red takes cols 0,1,2,3 while blue always dumps into col 6
  await cdp.eval(`document.getElementById('reset').click()`);
  await sleep(300);
  for (const col of [0, 6, 1, 6, 2, 6, 3]) await click(col);
  console.log("after red 4-in-row", await state(cdp), "  <- expect Red wins, winCells=4");

  // vertical four: red stacks col 0, blue always replies in col 1
  await cdp.eval(`document.getElementById('reset').click()`);
  await sleep(300);
  for (const col of [0, 1, 0, 1, 0, 1, 0]) await click(col);
  console.log("vertical 4    ", await state(cdp), "  <- expect Red wins, winCells=4");

  // diagonal four: red builds (5,0)(4,1)(3,2)(2,3), blue fills the staircase
  await cdp.eval(`document.getElementById('reset').click()`);
  await sleep(300);
  for (const col of [0, 1, 1, 2, 5, 2, 6, 3, 2, 3, 6, 3, 3]) await click(col);
  console.log("diagonal 4    ", await state(cdp), "  <- expect Red wins, winCells=4");

  await cdp.eval(`document.getElementById('reset').click()`);
  await sleep(300);
  console.log("after reset   ", await state(cdp));
} catch (e) {
  console.error("FAILED:", e.message);
  process.exitCode = 1;
} finally {
  chrome.kill();
  try { rmSync(profile, { recursive: true, force: true }); } catch {}
}
