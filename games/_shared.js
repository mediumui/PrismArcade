/* Shared audio + toast feedback helpers for Prism Arcade games.
   No audio files: sounds are synthesized with the Web Audio API.
   Usage:
     PA.toast("Nice!", "good");
     PA.sfx.win(); PA.sfx.lose(); PA.sfx.click(); ...
   Include with: <script src="../games/_shared.js"></script>
*/
(function (window) {
  "use strict";

  let ctx = null;
  let muted = false;

  function audio() {
    if (!ctx) {
      try { ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { ctx = null; }
    }
    if (ctx && ctx.state === "suspended") ctx.resume();
    return ctx;
  }

  function tone(freq, dur, type, when, vol) {
    const ac = audio();
    if (!ac || muted) return;
    const t0 = ac.currentTime + (when || 0);
    const osc = ac.createOscillator();
    const gain = ac.createGain();
    osc.type = type || "sine";
    osc.frequency.setValueAtTime(freq, t0);
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(vol || 0.18, t0 + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    osc.connect(gain).connect(ac.destination);
    osc.start(t0);
    osc.stop(t0 + dur + 0.02);
  }

  const sfx = {
    click: function () { tone(660, 0.06, "square", 0, 0.08); },
    move: function () { tone(360, 0.05, "triangle", 0, 0.05); },
    eat: function () { tone(520, 0.08, "sine", 0, 0.16); tone(780, 0.08, "sine", 0.06, 0.12); },
    good: function () { tone(523, 0.09, "sine"); tone(659, 0.09, "sine", 0.08); tone(784, 0.12, "sine", 0.16); },
    match: function () { tone(600, 0.07, "triangle"); tone(900, 0.09, "triangle", 0.05); },
    wrong: function () { tone(200, 0.18, "sawtooth", 0, 0.14); },
    win: function () { [523, 659, 784, 1046].forEach(function (f, i) { tone(f, 0.14, "sine", i * 0.09, 0.18); }); },
    lose: function () { [392, 330, 262, 196].forEach(function (f, i) { tone(f, 0.16, "sawtooth", i * 0.08, 0.14); }); },
    tick: function () { tone(880, 0.03, "square", 0, 0.05); },
    flip: function () { tone(440, 0.05, "triangle", 0, 0.07); }
  };

  let toastEl = null;
  let toastTimer = null;

  function toast(msg, kind) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "pa-toast";
      document.body.appendChild(toastEl);
      if (!document.body.sheetInjected) {
        const st = document.createElement("style");
        st.textContent =
          ".pa-toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(20px);" +
          "background:#161830;color:#f7f8ff;border:1px solid rgba(255,255,255,.16);border-radius:14px;" +
          "padding:12px 18px;font-family:Inter,system-ui,sans-serif;font-size:.95rem;font-weight:600;" +
          "box-shadow:0 16px 40px rgba(0,0,0,.5);opacity:0;pointer-events:none;transition:opacity .2s ease,transform .2s ease;z-index:200}" +
          ".pa-toast.show{opacity:1;transform:translateX(-50%) translateY(0)}" +
          ".pa-toast.good{background:rgba(91,227,164,.16);border-color:rgba(91,227,164,.4)}" +
          ".pa-toast.bad{background:rgba(255,99,99,.16);border-color:rgba(255,99,99,.4)}";
        document.head.appendChild(st);
        document.body.sheetInjected = true;
      }
    }
    toastEl.textContent = msg;
    toastEl.className = "pa-toast show " + (kind || "");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.className = "pa-toast " + (kind || ""); }, 1600);
  }

  function bindMuteBtn() {
    let btn = document.querySelector("[data-mute-toggle]");
    if (!btn) return;
    btn.addEventListener("click", function () {
      muted = !muted;
      btn.textContent = muted ? "Sound: Off" : "Sound: On";
      btn.setAttribute("aria-pressed", String(muted));
      if (!muted) sfx.click();
    });
    btn.textContent = "Sound: On";
    btn.setAttribute("role", "button");
  }

  /* Pause-aware animation driver (added 2026-10-28).
     A game must never burn frames while it is idle, scrolled off-screen, or
     sitting in a background tab — that is what pushed LCP past 6s and INP past
     200ms on mobile. Use this instead of a bare requestAnimationFrame chain.

       var drv = PA.animate(el, shouldRun, frame, fps);
         el        - element watched for visibility (pass null to skip the check)
         shouldRun - () => boolean; when false the loop parks itself
         frame     - (ts) => void; one animation step
         fps       - optional cap, e.g. 12 for a slow idle preview
       drv.kick()  - wake a parked loop (call this when the game starts)
       drv.stop()  - cancel for good
  */
  function animate(el, shouldRun, frame, fps) {
    var minDelta = fps ? 1000 / fps : 0;
    var visible = true, raf = 0, alive = true, last = 0;

    function tick(ts) {
      raf = 0;
      if (!alive) return;
      if (document.hidden || !visible) return;
      if (!shouldRun()) return;
      if (ts - last >= minDelta) { last = ts; frame(ts); }
      schedule();
    }
    function schedule() { if (!raf && alive) raf = requestAnimationFrame(tick); }
    function kick() { last = 0; schedule(); }

    if (el && window.IntersectionObserver) {
      new IntersectionObserver(function (entries) {
        visible = entries[0].isIntersecting;
        if (visible) kick();
      }, { threshold: 0.01 }).observe(el);
    }
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden) kick();
    });
    schedule();
    return {
      kick: kick,
      stop: function () { alive = false; if (raf) cancelAnimationFrame(raf); }
    };
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Unlock audio on first interaction (browser autoplay policy)
    const unlock = function () { audio(); window.removeEventListener("pointerdown", unlock); };
    window.addEventListener("pointerdown", unlock);
    bindMuteBtn();
  });

  window.PA = { sfx: sfx, toast: toast, animate: animate, isMuted: function () { return muted; } };
})(window);
