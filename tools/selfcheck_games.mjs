/**
 * Full self-check for every game page.
 *
 * Per game it loads the page in headless Chrome and reports:
 *   P0  uncaught JS exceptions, console errors, failed (4xx/5xx) requests
 *   P0  the [data-board] play surface exists and has a real size
 *   P1  the game actually reacts to input (start click, keys, board taps)
 *   P1  layout sanity at a mobile viewport (surface stays inside the screen)
 *
 * Usage: node tools/selfcheck_games.mjs http://localhost:8096
 */

import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BASE = (process.argv[2] || "http://localhost:8096").replace(/\/$/, "");
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9250;
const profile = mkdtempSync(join(tmpdir(), "selfcheck-"));

const SLUGS = [
  "2048", "block-slide", "color-sort", "connect4", "flappy", "hangman",
  "maze", "memory", "number-merge", "quick-tap", "quiz", "reaction-test",
  "reflex-relay", "runner", "sequence", "sliding-number", "snake",
  "stack-tower", "sudoku", "tic-tac-toe", "whack", "word-merge",
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  "--window-size=1280,900", "about:blank",
], { stdio: "ignore" });

class CDP {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.pending = new Map();
    ws.addEventListener("message", (e) => {
      const m = JSON.parse(e.data);
      if (m.id && this.pending.has(m.id)) { this.pending.get(m.id)(m); this.pending.delete(m.id); }
      else if (m.method === "Runtime.exceptionThrown") this.onExc?.(m.params);
      else if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") this.onConsole?.(m.params);
      else if (m.method === "Network.requestWillBeSent") this.onReq?.(m.params);
      else if (m.method === "Network.responseReceived") this.onResp?.(m.params);
      else if (m.method === "Network.loadingFailed") this.onFail?.(m.params);
    });
    this._open = new Promise((res) => (ws.readyState === 1 ? res() : ws.addEventListener("open", res, { once: true })));
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
    if (r.exceptionDetails) throw new Error("eval threw: " + JSON.stringify(r.exceptionDetails.exception?.description || ""));
    return r.result.value;
  }
  reset() { this.errors = []; this.failedReqs = []; this.excs = []; this.reqUrl = new Map(); }
  // third-party requests (AdSense, Google fonts) cannot resolve offline and
  // must not be reported as site faults — only same-origin failures count
  isOwn(url) { return typeof url === "string" && url.startsWith(BASE); }
}

// generic "play a bit" script; returns a fingerprint used to detect reaction
const PROBE = `(() => {
  const q = (s) => document.querySelector(s);
  const surface = q('[data-board]');
  const fp = () => {
    if (!surface) return 'none';
    // include class names: some games (memory flip, tic-tac-toe) only change
    // classes, so innerHTML length alone would miss the reaction
    let s = surface.innerHTML.length + '|' + (surface.textContent || '').length;
    s += '|' + [...surface.querySelectorAll('*')]
      .map((e) => (typeof e.className === 'string' ? e.className : (e.className.baseVal || '')))
      .join(',').length;
    if (surface.tagName === 'CANVAS') { try { s += '|' + surface.toDataURL().length; } catch(e) { s += '|c'; } }
    return s;
  };
  const before = fp();
  // press every obvious start control
  document.querySelectorAll('button').forEach((b) => {
    if (/^(start|play|new game|restart|retry|deal|roll|begin|tap to)\\b/i.test(b.textContent.trim()) || /^(start|play|restart)$/i.test(b.textContent.trim())) b.click();
  });
  ['#start','#restart','#reset','#new','#startBtn'].forEach((s) => { const el = q(s); if (el) el.click(); });
  return before;
})()`;

// real input through the browser, so clicks hit actual child elements
// (JS-dispatched events on the container never reach the tiles/cells)
async function realInput(cdp) {
  const rectStr = await cdp.eval(`(() => {
    const el = document.querySelector('[data-board]');
    if (!el) return JSON.stringify(null);
    el.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect();
    return JSON.stringify({ x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height });
  })()`);
  // prefer the centres of real child elements (tiles, cells, tubes, pads);
  // clicking the container centre can land on a gap and hit nothing
  const kidsStr = await cdp.eval(`(() => {
    const el = document.querySelector('[data-board]');
    if (!el || el.tagName === 'CANVAS') return JSON.stringify([]);
    const out = [];
    for (const k of el.children) {
      const r = k.getBoundingClientRect();
      if (r.width > 4 && r.height > 4 && r.y > 0 && r.y < window.innerHeight - 4) out.push([r.x + r.width / 2, r.y + r.height / 2]);
      if (out.length >= 12) break;
    }
    return JSON.stringify(out);
  })()`);
  const rect = JSON.parse(rectStr);
  const pts = [...JSON.parse(kidsStr)];
  if (rect) pts.push([rect.x, rect.y], [rect.x - rect.w * 0.3, rect.y], [rect.x + rect.w * 0.3, rect.y]);
  for (const [x, y] of pts) {
    if (x < 0 || y < 0) continue;
    await cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y, button: "none" });
    await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
    await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
    await sleep(170);
  }
  for (const [key, code, vk] of [["ArrowLeft", "ArrowLeft", 37], ["ArrowRight", "ArrowRight", 39],
                                 ["ArrowUp", "ArrowUp", 38], ["ArrowDown", "ArrowDown", 40],
                                 [" ", "Space", 32], ["a", "KeyA", 65]]) {
    await cdp.send("Input.dispatchKeyEvent", { type: "rawKeyDown", key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await cdp.send("Input.dispatchKeyEvent", { type: "keyUp", key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk });
    await sleep(90);
  }
}

const SURFACE = `(() => {
  const el = document.querySelector('[data-board]');
  if (!el) return JSON.stringify({ ok: false });
  const r = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  return JSON.stringify({ ok: true, tag: el.tagName, w: Math.round(r.width), h: Math.round(r.height),
    vis: cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity > 0 });
})()`;

async function checkDesktop(cdp, slug) {
  cdp.reset();
  await cdp.send("Page.navigate", { url: `${BASE}/games/${slug}.html` });
  await sleep(1800);
  const FP = `(() => {
    const s = document.querySelector('[data-board]');
    if (!s) return 'none';
    let v = s.innerHTML.length + '|' + (s.textContent || '').length;
    v += '|' + [...s.querySelectorAll('*')].map((e) => (typeof e.className === 'string' ? e.className : (e.className.baseVal || ''))).join(',').length;
    if (s.tagName === 'CANVAS') { try { v += '|' + s.toDataURL().length; } catch(e) { v += '|c'; } }
    return v;
  })()`;
  const before = await cdp.eval(PROBE);          // press start buttons
  // sample immediately: simon-style games light up while playing back, and
  // that flash is over before any click round finishes
  let reacted = false;
  for (let i = 0; i < 4 && !reacted; i += 1) {
    await sleep(400);
    if ((await cdp.eval(FP)) !== before) reacted = true;
  }
  await realInput(cdp);                          // real clicks + keys on the board
  await sleep(1200);
  // measure AFTER input: boards that render on start (number-merge) are empty
  // until the first interaction
  const surf = JSON.parse(await cdp.eval(SURFACE));
  for (let i = 0; i < 4 && !reacted; i += 1) {
    if ((await cdp.eval(FP)) !== before) reacted = true;
    else await sleep(450);
  }
  return { surf, reacted, errors: [...cdp.errors], excs: [...cdp.excs], failed: [...cdp.failedReqs] };
}

async function checkMobile(cdp, slug) {
  await cdp.send("Emulation.setDeviceMetricsOverride",
    { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  cdp.reset();
  await cdp.send("Page.navigate", { url: `${BASE}/games/${slug}.html` });
  await sleep(1800);
  const r = JSON.parse(await cdp.eval(`(() => {
    const el = document.querySelector('[data-board]');
    if (!el) return JSON.stringify({ ok: false });
    const b = el.getBoundingClientRect();
    return JSON.stringify({ w: Math.round(b.width), h: Math.round(b.height),
      overflowX: Math.round(b.right - document.documentElement.clientWidth),
      docW: document.documentElement.clientWidth, scrollW: document.documentElement.scrollWidth });
  })()`));
  await cdp.send("Emulation.clearDeviceMetricsOverride");
  return { ...r, errors: [...cdp.errors], excs: [...cdp.excs], failed: [...cdp.failedReqs] };
}

(async () => {
  try {
    await sleep(2500);
    const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
    const cdp = new CDP(new WebSocket(list.find((t) => t.type === "page").webSocketDebuggerUrl));
    cdp.onExc = (p) => cdp.excs?.push(p.exceptionDetails?.exception?.description || p.exceptionDetails?.text || "exception");
    cdp.onConsole = (p) => cdp.errors?.push((p.args || []).map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 160));
    cdp.onReq = (p) => cdp.reqUrl?.set(p.requestId, p.request.url);
    cdp.onResp = (p) => {
      if (p.response.status >= 400 && cdp.isOwn(p.response.url)) {
        cdp.failedReqs?.push(`${p.response.status} ${p.response.url.replace(BASE, "")}`);
      }
    };
    cdp.onFail = (p) => {
      const url = cdp.reqUrl?.get(p.requestId);
      if (cdp.isOwn(url)) cdp.failedReqs?.push(`FAILED ${p.errorText} ${String(url).replace(BASE, "")}`);
    };
    cdp.reset();
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Network.enable");
    await cdp.send("Log.enable");

    const rows = [];
    for (const slug of SLUGS) {
      const d = await checkDesktop(cdp, slug);
      const m = await checkMobile(cdp, slug);
      const allErr = [...new Set([...d.errors, ...d.excs, ...d.failed, ...m.errors, ...m.excs, ...m.failed])];
      const p0 = [];
      if (!d.surf.ok) p0.push("no [data-board]");
      else if (!d.surf.vis || d.surf.w < 40 || d.surf.h < 40) p0.push(`surface ${d.surf.w}x${d.surf.h} vis=${d.surf.vis}`);
      if (d.excs.length) p0.push(`JS exception x${d.excs.length}`);
      if (d.failed.length) p0.push(`bad request x${d.failed.length}`);
      if (d.errors.length) p0.push(`console error x${d.errors.length}`);
      const p1 = [];
      if (!d.reacted) p1.push("no reaction to input");
      if (m.ok === false) p1.push("mobile: no surface");
      else if (m.overflowX > 2) p1.push(`mobile overflow ${m.overflowX}px`);
      else if (m.scrollW > m.docW + 2) p1.push(`mobile h-scroll ${m.scrollW}>${m.docW}`);
      rows.push({ slug, p0, p1, size: d.surf.ok ? `${d.surf.w}x${d.surf.h}` : "-", err: allErr.slice(0, 3) });
      const flag = p0.length ? "FAIL" : p1.length ? "WARN" : "OK  ";
      console.log(`${flag} ${slug.padEnd(16)} ${String(rows.at(-1).size).padEnd(9)} ${[...p0, ...p1].join("; ") || ""}`);
      if (allErr.length) allErr.slice(0, 2).forEach((e) => console.log(`      ↳ ${String(e).slice(0, 120)}`));
    }

    const fails = rows.filter((r) => r.p0.length);
    const warns = rows.filter((r) => !r.p0.length && r.p1.length);
    console.log(`\n=== ${SLUGS.length} games: ${SLUGS.length - fails.length - warns.length} OK, ${warns.length} WARN, ${fails.length} FAIL ===`);
    if (fails.length) console.log("FAIL:", fails.map((r) => r.slug).join(", "));
    if (warns.length) console.log("WARN:", warns.map((r) => r.slug).join(", "));
  } catch (e) {
    console.error("HARNESS FAILED:", e.message);
    process.exitCode = 1;
  } finally {
    chrome.kill();
    try { rmSync(profile, { recursive: true, force: true }); } catch {}
  }
})();
