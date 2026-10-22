#!/usr/bin/env node
/**
 * render_thumbs.mjs — render thumbs_svg/*.svg to thumbs/<slug>.jpg (640x360).
 *
 * Pairs with tools/gen_thumbs.py, which writes the SVGs. Uses headless Chrome
 * via CDP (same zero-dependency approach as capture_thumbs.mjs).
 *
 * Usage: node tools/render_thumbs.mjs
 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { tmpdir } from "node:os";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SRC = join(ROOT, "thumbs_svg");
const OUT = join(ROOT, "thumbs");
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9224;
const PROFILE = join(tmpdir(), "pa-render-profile"); // never inside thumbs/ (it ships)

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitPort() {
  for (let i = 0; i < 40; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      if (r.ok) return;
    } catch {}
    await sleep(250);
  }
  throw new Error("chrome devtools port never came up");
}

class CDP {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.pending = new Map();
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
  const svgs = readdirSync(SRC).filter((f) => f.endsWith(".svg"));
  if (!svgs.length) { console.error("no SVGs in thumbs_svg/ — run gen_thumbs.py first"); process.exit(1); }

  const profile = PROFILE;
  const chrome = spawn(CHROME, [
    "--headless=new", "--disable-gpu", "--no-first-run", "--no-sandbox",
    "--hide-scrollbars", "--window-size=660,400",
    `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank",
  ], { stdio: "ignore" });
  process.on("exit", () => { try { chrome.kill(); } catch {} });

  await waitPort();
  const tabs = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  const page = tabs.find((t) => t.type === "page");
  const cdp = new CDP(new WebSocket(page.webSocketDebuggerUrl));
  await new Promise((res) => { if (cdp.ws.readyState === 1) res(); else cdp.ws.addEventListener("open", res, { once: true }); });
  await cdp.send("Page.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride", { width: 640, height: 360, deviceScaleFactor: 2, mobile: false });
  await sleep(400);

  let ok = 0;
  for (const f of svgs) {
    const slug = f.replace(/\.svg$/, "");
    const html = `<!doctype html><html><body style="margin:0;padding:0;overflow:hidden">${readFileSync(join(SRC, f), "utf8")}</body></html>`;
    await cdp.send("Page.navigate", { url: "data:text/html;charset=utf-8," + encodeURIComponent(html) });
    await sleep(450);
    const shot = await cdp.send("Page.captureScreenshot", {
      format: "jpeg", quality: 90,
      clip: { x: 0, y: 0, width: 640, height: 360, scale: 2 },
    });
    writeFileSync(join(OUT, `${slug}.jpg`), Buffer.from(shot.data, "base64"));
    ok++;
    console.log(`${slug}.jpg`);
  }
  try { chrome.kill(); } catch {}
  console.log(`\nRendered ${ok}/${svgs.length} -> thumbs/`);
}

main().catch((e) => { console.error(e); process.exit(1); });
