/* Adaptive one-screen fit for Prism Arcade game pages.
   Sizes the main board / canvas so the whole play area stays inside the
   current viewport without forcing vertical page scrolling.

   Usage:
   - Add `data-fit` to the board/canvas element itself, or to the `.play-stage`
     wrapper.
   - If the wrapper has `data-fit`, this script finds the board automatically.
   - It keeps the page layout responsive on resize and orientation changes.
*/
(function () {
  "use strict";

  function isBoard(el) {
    if (!el || el.nodeType !== 1) return false;
    if (el.hasAttribute("data-fit-target") || el.classList.contains("fit-target")) return true;
    if (el.tagName === "CANVAS") return true;
    return [
      "g2048", "bs-grid", "memory-grid", "merge-grid", "board-grid", "sud", "whack-grid",
      "wm-pool", "wm-bin", "react-zone", "option-list"
    ].some((cls) => el.classList.contains(cls));
  }

  function targetFor(root) {
    if (isBoard(root)) return root;
    return root.querySelector("[data-fit-target], .fit-target, canvas, .g2048, .bs-grid, .memory-grid, .merge-grid, .board-grid, .sud, .whack-grid, .wm-pool, .react-zone, .option-list");
  }

  function aspectOf(el) {
    if (el.tagName === "CANVAS" && Number(el.getAttribute("width")) > 0 && Number(el.getAttribute("height")) > 0) {
      return Number(el.getAttribute("height")) / Number(el.getAttribute("width"));
    }

    var ar = getComputedStyle(el).aspectRatio;
    if (ar && ar !== "auto") {
      if (ar.includes("/")) {
        var parts = ar.split("/");
        return Number(parts[1]) / Number(parts[0]);
      }
      return Number(ar);
    }

    var rect = el.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) return rect.height / rect.width;
    return 1;
  }

  function fitStage(stage) {
    var target = targetFor(stage);
    if (!target) return;

    var t;
    function measure() {
      var vh = window.innerHeight || document.documentElement.clientHeight;
      var vw = window.innerWidth || document.documentElement.clientWidth;

      var chrome = 96;
      var header = document.querySelector(".site-header");
      if (header) chrome += header.offsetHeight;
      var hero = document.querySelector(".game-page .hero");
      if (hero) chrome += Math.min(hero.offsetHeight, Math.max(56, vh * 0.14));
      var controls = stage.querySelector(".game-controls, .snake-controls, .sud-num");
      if (controls) chrome += controls.offsetHeight + 18;
      var hint = stage.querySelector(".tile-hint, .tap-hint");
      if (hint) chrome += hint.offsetHeight + 8;
      var sidePanel = document.querySelector(".side-panel");
      if (sidePanel && vw >= 1080) chrome += Math.min(70, vh * 0.08);

      var availableH = Math.max(220, vh - chrome - 42);
      var availableW = Math.max(280, stage.clientWidth || vw - 48);
      var ratio = aspectOf(target);

      var fitWidth = Math.min(availableW * 0.9, availableH / ratio, vw * 0.88);
      fitWidth = Math.max(240, Math.floor(fitWidth));
      var width = fitWidth;
      if (target.classList.contains("wm-pool")) width = 560;
      if (target.classList.contains("option-list")) width = 560;
      if (target.id === "run") width = Math.max(width, Math.min(420, Math.floor(vw * 0.62)));

      var rootStyle = document.documentElement.style;
      if (ratio >= 0.8) {
        rootStyle.setProperty("--fit-board", width + "px");
        rootStyle.setProperty("--fit-board-max", Math.floor(width * ratio) + "px");
      } else {
        rootStyle.setProperty("--fit-board", width + "px");
        rootStyle.setProperty("--fit-board-max", Math.min(Math.floor(availableH * 0.78), 420) + "px");
      }
      if (target.tagName === "CANVAS") {
        target.style.width = "var(--fit-board)";
        target.style.maxWidth = "var(--fit-board)";
        target.style.height = "auto";
        if (target.id === "run") target.style.minHeight = vw >= 768 ? "160px" : "auto";
      }
    }

    function raf() {
      cancelAnimationFrame(t);
      t = requestAnimationFrame(measure);
    }
    window.addEventListener("resize", raf);
    window.addEventListener("orientationchange", raf);
    measure();
  }

  function init() {
    var roots = document.querySelectorAll("[data-fit], .play-stage");
    var seen = {};
    Array.prototype.forEach.call(roots, function (root) {
      var target = targetFor(root);
      if (!target || seen[target.id || target.className]) return;
      seen[target.id || target.className] = true;
      target.dataset.fitApplied = "true";
      fitStage(root);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
  window.Fit = { stage: fitStage };
})();
