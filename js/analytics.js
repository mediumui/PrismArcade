/**
 * Prism Arcade — global analytics (Google Analytics 4)
 * Single source of truth: every page loads ONLY this file.
 *
 * To change the GA property or add a measurement id, edit it here once —
 * do NOT copy the gtag snippet into individual pages.
 *
 * Usage across the site:
 *   <script src="/js/analytics.js"></script>   (placed just before </head>)
 */
(function () {
  var GA_ID = "G-83BMVG4W6Q"; // edit once here

  // Bootstrap gtag (idempotent: safe if the gtag script was already loaded
  // on a page, though it normally is not).
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  gtag("js", new Date());
  gtag("config", GA_ID, { send_page_view: true });

  // Expose a small helper so pages can fire custom events without
  // re-inlining gtag call code. e.g. trackEvent("game_start", { game: "snake" })
  function trackEvent(name, params) {
    gtag("event", name, params || {});
  }

  // Attach for direct access if needed.
  window.trackEvent = trackEvent;
})();
