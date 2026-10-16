/* Prism Arcade — global analytics (Google Analytics 4).
   Single source of truth: every page loads ONLY this file.
   To change the GA property, edit the GA_ID here once. */
(function () {
  var GA_ID = "G-83BMVG4W6Q"; // edit once here

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag("js", new Date());
  gtag("config", GA_ID, { send_page_view: true });

  // Helper so pages can fire custom events without re-inlining gtag code:
  //   trackEvent("game_start", { game: "snake" })
  window.trackEvent = function (name, params) {
    gtag("event", name, params || {});
  };
})();
