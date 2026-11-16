(() => {
  const page = document.querySelector('[data-news-index]');
  if (!page) return;

  const filters = page.querySelector('.news-filters');
  const buttons = Array.from(filters.querySelectorAll('[data-news-filter]'));
  const cards = Array.from(page.querySelectorAll('[data-news-category]'));
  const archives = Array.from(page.querySelectorAll('.news-archive'));
  const status = page.querySelector('.news-filter-status');
  const ja = document.documentElement.lang === 'ja';

  function selectCategory(category) {
    const selected = buttons.find(button => button.dataset.newsFilter === category);
    if (!selected) return;

    cards.forEach(card => {
      card.hidden = category !== 'all' && card.dataset.newsCategory !== category;
    });
    archives.forEach(archive => {
      const count = archive.querySelectorAll('.news-card:not([hidden])').length;
      archive.hidden = count === 0;
      archive.querySelector('[data-news-count]').textContent = ja ? `${count}件` : `${count} ${count === 1 ? 'update' : 'updates'}`;
    });
    buttons.forEach(button => {
      button.setAttribute('aria-pressed', String(button === selected));
    });
    const count = cards.filter(card => !card.hidden).length;
    if (ja) {
      const label = category === 'all' ? '' : `${category === 'journal' ? '論文誌' : '国際会議'}：`;
      status.textContent = `${label}${count}件`;
      return;
    }
    const label = category === 'all' ? '' : `${category === 'journal' ? 'Journal' : 'Conference'} `;
    status.textContent = `${count} ${label}${count === 1 ? 'update' : 'updates'}`;
  }

  filters.addEventListener('click', event => {
    const button = event.target.closest('[data-news-filter]');
    if (button && filters.contains(button)) selectCategory(button.dataset.newsFilter);
  });

  selectCategory('all');
  filters.hidden = false;
})();
