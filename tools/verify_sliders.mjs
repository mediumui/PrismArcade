// Targeted interaction verification for the 4 games that the generic
// self-check flags as "no reaction" (its blind centre click misses the
// real hit targets: slider tiles, tubes, word tiles).
//
// Each case drives the game with rule-aware input and asserts state change.
//
// Usage: node tools/verify_sliders.mjs http://localhost:8096

import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = process.argv[2] || "http://localhost:8096";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9270;
const profile = mkdtempSync(join(tmpdir(), "vsl-"));
const chrome = spawn(
  CHROME,
  ["--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
   `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
   "--window-size=1280,900", "about:blank"],
  { stdio: "ignore" }
);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class CDP {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.p = new Map();
    ws.addEventListener("message", (e) => {
      const m = JSON.parse(e.data);
      if (m.id && this.p.has(m.id)) { this.p.get(m.id)(m); this.p.delete(m.id); }
    });
    this._o = new Promise((res) => (ws.readyState === 1 ? res() : ws.addEventListener("open", res, { once: true })));
  }
  async send(method, params = {}) {
    await this._o;
    const id = ++this.id;
    return new Promise((res, rej) => {
      this.p.set(id, (m) => (m.error ? rej(new Error(method)) : res(m.result)));
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async eval(expression) {
    const r = await this.send("Runtime.evaluate", { returnByValue: true, expression });
    return r.result.value;
  }
}

const results = [];
function check(name, pass, detail) {
  results.push({ name, pass, detail });
  console.log(`${pass ? "PASS" : "FAIL"}  ${name}  ${detail}`);
}

try {
  await sleep(2500);
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const cdp = new CDP(new WebSocket(list.find((t) => t.type === "page").webSocketDebuggerUrl));
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");

  // ---- block-slide: click a tile adjacent to the empty slot ----
  await cdp.send("Page.navigate", { url: `${BASE}/games/block-slide.html` });
  await sleep(2200);
  check("block-slide", JSON.parse(await cdp.eval(`(() => {
    const cells = [...document.querySelectorAll('#grid .bs-cell')];
    if (!cells.length) return JSON.stringify({ ok:false, why:'no cells' });
    // the empty slot is the only cell with no child elements
    const blank = cells.findIndex((e) => e.children.length === 0);
    if (blank < 0) return JSON.stringify({ ok:false, why:'no blank' });
    const moves = () => (document.getElementById('moves') || {}).textContent;
    const before = moves() + '|' + cells.map((e) => e.children.length).join('');
    const n = Math.round(Math.sqrt(cells.length));
    const r = Math.floor(blank / n), c = blank % n;
    const cand = [[r-1,c],[r+1,c],[r,c-1],[r,c+1]].filter(([a,b]) => a>=0 && a<n && b>=0 && b<n).map(([a,b]) => a*n+b);
    for (const i of cand) { if (cells[i].children.length) { cells[i].click(); break; } }
    const after = moves() + '|' + [...document.querySelectorAll('#grid .bs-cell')].map((e) => e.children.length).join('');
    return JSON.stringify({ ok: before !== after, blank, moves: moves() });
  })()`)).ok, "adjacent-tile click changes board/moves");

  // ---- sliding-number: click a number tile next to the blank ----
  await cdp.send("Page.navigate", { url: `${BASE}/games/sliding-number.html` });
  await sleep(2200);
  check("sliding-number", JSON.parse(await cdp.eval(`(() => {
    const cells = [...document.querySelectorAll('#board [class*="cell"], #board div')].filter((e) => e.children.length === 0);
    const real = [...document.querySelectorAll('#board > div')];
    const cs = real.length ? real : cells;
    const blank = cs.findIndex((e) => !e.textContent.trim());
    if (blank < 0) return JSON.stringify({ ok:false, why:'no blank' });
    const n = Math.round(Math.sqrt(cs.length));
    const r = Math.floor(blank / n), c = blank % n;
    const cand = [[r-1,c],[r+1,c],[r,c-1],[r,c+1]].filter(([a,b]) => a>=0 && a<n && b>=0 && b<n).map(([a,b]) => a*n+b);
    const before = cs.map((e) => e.textContent.trim()).join('|');
    if (cand.length) cs[cand[0]].click();
    const after = [...document.querySelectorAll('#board > div')].map((e) => e.textContent.trim()).join('|');
    return JSON.stringify({ ok: before !== after, blank, clicked: cand[0] });
  })()`)).ok, "adjacent-tile click swaps tiles");

  // ---- color-sort: pour needs a matching top colour, so try every
  //      destination tube after picking up a source, until #moves ticks ----
  await cdp.send("Page.navigate", { url: `${BASE}/games/color-sort.html` });
  await sleep(2200);
  check("color-sort", JSON.parse(await cdp.eval(`(() => {
    const tubes = () => [...document.querySelectorAll('#tubes .cs-tube')];
    if (tubes().length < 2) return JSON.stringify({ ok:false, why:'tubes=' + tubes().length });
    const moves = () => (document.getElementById('moves') || {}).textContent;
    const before = moves();
    for (let s = 0; s < tubes().length; s += 1) {
      tubes()[s].click();                       // pick up source
      for (let d = 0; d < tubes().length; d += 1) {
        if (d === s) continue;
        tubes()[d].click();                     // try to pour
        if (moves() !== before) {
          return JSON.stringify({ ok:true, from:s, to:d, moves:moves() });
        }
        tubes()[s].click();                     // re-pick source for next try
      }
      if (moves() !== before) break;
    }
    return JSON.stringify({ ok:false, why:'no valid pour found', moves:moves() });
  })()`)).ok, "valid tube pour increments moves");

  // ---- word-merge: click two pool tiles ----
  await cdp.send("Page.navigate", { url: `${BASE}/games/word-merge.html` });
  await sleep(2200);
  check("word-merge", JSON.parse(await cdp.eval(`(() => {
    const tiles = [...document.querySelectorAll('#pool > *, .pool > *, [class*="tile"], [class*="chip"]')].filter((e) => e.textContent.trim());
    if (!tiles.length) return JSON.stringify({ ok:false, why:'no tiles' });
    const before = tiles.map((e) => e.textContent.trim()).join(',') + '|' + tiles.map((e) => e.className).join(',');
    tiles[0].click();
    if (tiles[1]) tiles[1].click();
    const after = [...document.querySelectorAll('#pool > *, .pool > *, [class*="tile"], [class*="chip"]')].filter((e) => e.textContent.trim());
    const afterStr = after.map((e) => e.textContent.trim()).join(',') + '|' + after.map((e) => e.className).join(',');
    return JSON.stringify({ ok: before !== afterStr, before: before.slice(0, 80), after: afterStr.slice(0, 80) });
  })()`)).ok, "pool tile click changes selection/pool");

  const bad = results.filter((r) => !r.pass);
  console.log(`\n=== ${results.length - bad.length}/${results.length} PASS ===`);
  if (bad.length) process.exitCode = 1;
} catch (e) {
  console.error("ERR", e.message);
  process.exitCode = 1;
} finally {
  chrome.kill();
  try { rmSync(profile, { recursive: true, force: true }); } catch {}
}
