// Prism Arcade — catalog filter + pagination (games.html)
// Static HTML cards are the source of truth, so the page is fully crawlable
// and degrades gracefully when JS is unavailable (all cards stay visible).
// IDs are resolved defensively so the script works whether the page uses the
// canonical (catalogGrid/pager/catalogCounts) or legacy (gameGrid/pagination/
// resultCount) markup.
(function () {
  'use strict';

  var PER_PAGE = 12;

  document.addEventListener('DOMContentLoaded', function () {
    var grid =
      document.getElementById('catalogGrid') ||
      document.getElementById('gameGrid') ||
      document.querySelector('.catalog-grid');
    var pager = document.getElementById('pager') || document.getElementById('pagination');
    var countsEl =
      document.getElementById('catalogCounts') || document.getElementById('resultCount');
    if (!grid || !pager) return;

    var cards = Array.prototype.slice.call(grid.querySelectorAll('.game-card'));
    var chips = Array.prototype.slice.call(document.querySelectorAll('[data-filter]'));

    var state = { filter: 'all', page: 1 };

    function labelFor(filter) {
      if (filter === 'all') return 'games';
      return filter.charAt(0).toUpperCase() + filter.slice(1) + ' games';
    }

    function filteredCards() {
      if (state.filter === 'all') return cards;
      return cards.filter(function (c) {
        return c.dataset.category === state.filter;
      });
    }

    function render() {
      var list = filteredCards();
      var total = list.length;
      var pages = Math.max(1, Math.ceil(total / PER_PAGE));
      if (state.page > pages) state.page = pages;
      if (state.page < 1) state.page = 1;

      var start = (state.page - 1) * PER_PAGE;
      var end = Math.min(start + PER_PAGE, total);

      cards.forEach(function (c) { c.style.display = 'none'; });
      list.forEach(function (c, i) {
        if (i >= start && i < end) c.style.display = 'flex';
      });

      if (countsEl) {
        if (total === 0) {
          countsEl.textContent = 'No games in this category.';
        } else if (pages === 1) {
          countsEl.textContent = 'Showing ' + total + ' ' + labelFor(state.filter) + '.';
        } else {
          countsEl.textContent =
            'Showing ' + (start + 1) + '–' + end + ' of ' + total + ' ' + labelFor(state.filter) + '.';
        }
      }

      renderPager(pages);
    }

    function renderPager(pages) {
      pager.innerHTML = '';

      if (pages <= 1) {
        var info = document.createElement('span');
        info.className = 'pager-info';
        info.textContent = 'Page 1 of 1';
        pager.appendChild(info);
        return;
      }

      var info = document.createElement('span');
      info.className = 'pager-info';
      info.textContent = 'Page ' + state.page + ' of ' + pages;
      pager.appendChild(info);

      var prev = document.createElement('button');
      prev.type = 'button';
      prev.className = 'pager-btn';
      prev.textContent = '‹ Prev';
      prev.disabled = state.page === 1;
      prev.addEventListener('click', function () { goTo(state.page - 1); });
      pager.appendChild(prev);

      for (var p = 1; p <= pages; p++) {
        (function (page) {
          var btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'pager-btn';
          btn.textContent = String(page);
          if (page === state.page) btn.setAttribute('aria-current', 'page');
          btn.addEventListener('click', function () { goTo(page); });
          pager.appendChild(btn);
        })(p);
      }

      var next = document.createElement('button');
      next.type = 'button';
      next.className = 'pager-btn';
      next.textContent = 'Next ›';
      next.disabled = state.page === pages;
      next.addEventListener('click', function () { goTo(state.page + 1); });
      pager.appendChild(next);
    }

    function goTo(page) {
      state.page = page;
      render();
      var top = document.getElementById('catalog');
      if (top) top.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        chips.forEach(function (c) { c.classList.toggle('active', c === chip); });
        state.filter = chip.dataset.filter;
        state.page = 1;
        render();
      });
    });

    render();
  });
})();
