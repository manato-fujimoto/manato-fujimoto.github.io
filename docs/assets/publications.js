(() => {
  const navigation = document.querySelector('.section-nav');
  const groups = Array.from(document.querySelectorAll('.publication-group'));
  if (!navigation || !groups.length) return;

  const links = Array.from(navigation.querySelectorAll('a[href^="#"]'));
  let selectedGroup = 'journal';

  function hashTarget() {
    try {
      return document.getElementById(decodeURIComponent(location.hash.slice(1)));
    } catch {
      return null;
    }
  }

  function selectGroup(id) {
    selectedGroup = id;
    groups.forEach(group => { group.hidden = group.id !== id; });
    links.forEach(link => {
      if (link.hash === '#' + id) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }

  function followHash() {
    const target = hashTarget();
    const group = target && target.closest('.publication-group');
    selectGroup(group ? group.id : (location.hash ? selectedGroup : 'journal'));
    if (target) requestAnimationFrame(() => target.scrollIntoView({ block: 'start' }));
  }

  navigation.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (!link || !navigation.contains(link) || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const id = link.hash.slice(1);
    if (!groups.some(group => group.id === id)) return;
    event.preventDefault();
    if (location.hash !== link.hash) history.pushState(null, '', link.hash);
    selectGroup(id);
  });

  window.addEventListener('hashchange', followHash);
  followHash();
})();
