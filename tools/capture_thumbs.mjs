#!/usr/bin/env node
/**
 * capture_thumbs.mjs — real gameplay screenshots for all game pages.
 *
 * Zero-dependency: uses Node 22's built-in WebSocket + fetch to talk to
 * Chrome's DevTools Protocol. Spawns local headless Chrome itself.
 *
 * What it does per game page:
 *   1. navigate (local http server or live site)
 *   2. locate the game surface (largest <canvas>, else #grid, else .board-grid)
 *   3. try clicking a start/restart control so the scene is "alive"
 *   4. wait for animation frames, then screenshot the surface (2x, JPEG)
 *
 * Usage:
 *   node tools/capture_thumbs.mjs [baseUrl]
 *   baseUrl default: http://localhost:8097
 * Output: thumbs/<slug>.jpg
 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(ROOT, "thumbs");
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9223;
const BASE = process.argv[2] || "http://localhost:8097";

const SLUGS = [
  "2048", "block-slide", "color-sort", "connect4", "flappy", "hangman",
  "maze", "memory", "number-merge", "quick-tap", "quiz", "reaction-test",
  "reflex-relay", "runner", "sequence", "sliding-number", "snake",
  "stack-tower", "sudoku", "tic-tac-toe", "whack", "word-merge",
];

/**
 * Every game page tags its playable surface with `data-board`
 * (see tools/tag_board.py). New games must do the same — that is the only
 * contract this tool relies on.
 */
const RECT_JS = `(() => {
  let el = document.querySelector('canvas[data-board]') || document.querySelector('[data-board]');
  if (!el) return JSON.stringify(null);
  // Some boards are a thin strip (hangman word row, word-merge letter pool).
  // Climb to a squarer ancestor so the crop still reads as a game thumbnail.
  const vw = document.documentElement.clientWidth;
  let r = el.getBoundingClientRect(), hops = 0;
  const tooFlat = (b) => b.height / b.width < 0.45;
  while (hops < 3 && el.tagName !== 'CANVAS' && el.parentElement && tooFlat(r)) {
    const p = el.parentElement.getBoundingClientRect();
    if (p.width > vw || p.width > 1200 || p.height > 800) break;
    el = el.parentElement; r = p; hops++;
    if (!tooFlat(r)) break;
  }
  el.scrollIntoView({ block: 'center' });
  r = el.getBoundingClientRect();
  return JSON.stringify({ x: r.x, y: r.y + window.scrollY, w: r.width, h: r.height });
})()`;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitPort() {
  for (let i = 0; i < 40; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (r.ok) return true;
    } catch {}
    await sleep(250);
  }
  throw new Error("chrome devtools port never came up");
}

class CDP {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    ws.addEventListener("message", (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
      }
    });
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  const profile = join(OUT, ".chrome-profile");
  const chrome = spawn(CHROME, [
    "--headless=new", "--disable-gpu", "--no-first-run", "--no-sandbox",
    "--hide-scrollbars", "--window-size=1280,1000",
    `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
    "about:blank",
  ], { stdio: "ignore" });
  process.on("exit", () => { try { chrome.kill(); } catch {} });

  await waitPort();
  const tabs = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  const page = tabs.find((t) => t.type === "page");
  const cdp = new CDP(new WebSocket(page.webSocketDebuggerUrl));
  await sleep(500);

  const results = [];
  for (const slug of SLUGS) {
    const url = `${BASE}/games/${slug}.html`;
    try {
      await cdp.send("Page.navigate", { url });
      await sleep(1800);

      // try to start the game first (some boards only render after start)
      await cdp.send("Runtime.evaluate", { expression: `(() => {
        const btn = document.querySelector('#start, #startBtn, #restart, #reset, #new') ||
                    [...document.querySelectorAll('button')].find(b => /^(start|play|restart|new game)$/i.test(b.textContent.trim()));
        if (btn) { btn.click(); }
      })()` });
      await sleep(400);

      // activate the scene: tap the canvas twice (starts tap-to-play games,
      // second tap acts as a jump/flap), then arrow keys (fills merge/slide
      // boards, steers the snake)
      await cdp.send("Runtime.evaluate", { expression: `(() => {
        const cv = document.querySelector('canvas[data-board]');
        const tap = () => {
          if (!cv) return;
          const r = cv.getBoundingClientRect();
          const opts = { bubbles: true, cancelable: true, clientX: r.x + r.width/2, clientY: r.y + r.height/2 };
          cv.dispatchEvent(new PointerEvent('pointerdown', opts));
          cv.dispatchEvent(new PointerEvent('pointerup', opts));
          cv.dispatchEvent(new MouseEvent('click', opts));
        };
        tap(); setTimeout(tap, 180);
        const key = (k) => {
          const ev = new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true });
          window.dispatchEvent(ev); document.dispatchEvent(ev);
          if (cv) cv.dispatchEvent(ev);
        };
        ['ArrowLeft','ArrowUp','ArrowLeft','ArrowUp','ArrowLeft','ArrowUp','ArrowRight','ArrowUp']
          .forEach((k, i) => setTimeout(() => key(k), 120 + i * 90));
      })()` });
      await sleep(1100);

      const rectStr = await cdp.send("Runtime.evaluate", {
        returnByValue: true,
        expression: RECT_JS,
      });
      const rect = JSON.parse(rectStr.result.value);
      if (!rect || rect.h < 10 || rect.w < 10) { results.push([slug, "NO-SURFACE"]); console.error(`${slug}: NO-SURFACE`); continue; }

      const shot = await cdp.send("Page.captureScreenshot", {
        format: "jpeg", quality: 88,
        captureBeyondViewport: true,
        clip: { x: rect.x, y: rect.y, width: rect.w, height: rect.h, scale: 2 },
      });
      const file = join(OUT, `${slug}.jpg`);
      writeFileSync(file, Buffer.from(shot.data, "base64"));
      const kb = Math.round(Number(shot.data.length) * 3 / 4 / 1024);
      results.push([slug, `OK ${rect.w}x${rect.h} ${kb}KB`]);
      console.log(`${slug}: OK (${rect.w}x${rect.h}, ${kb}KB)`);
    } catch (e) {
      results.push([slug, `FAIL ${e.message}`]);
      console.error(`${slug}: FAIL ${e.message}`);
    }
  }

  try { chrome.kill(); } catch {}
  const fails = results.filter(([, s]) => !s.startsWith("OK"));
  console.log(`\nDone: ${results.length - fails.length}/${results.length} OK`);
  if (fails.length) { console.log("Failed:", fails.map(([s]) => s).join(", ")); process.exitCode = 1; }
}

main().catch((e) => { console.error(e); process.exit(1); });
