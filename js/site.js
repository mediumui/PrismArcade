document.addEventListener('DOMContentLoaded', () => {
  const filterButtons = [...document.querySelectorAll('[data-filter]')];
  const cards = [...document.querySelectorAll('.game-card')];

  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const value = button.dataset.filter;
      filterButtons.forEach((item) => item.classList.toggle('active', item === button));
      cards.forEach((card) => {
        const match = value === 'all' || card.dataset.category === value;
        card.style.display = match ? 'grid' : 'none';
      });
    });
  });

  const year = document.querySelector('[data-year]');
  if (year) year.textContent = new Date().getFullYear();
});
