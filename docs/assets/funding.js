(() => {
  const data = JSON.parse(document.getElementById('rf-data').textContent);
  const root = document.getElementById('research-funding');
  const detail = document.getElementById('rf-detail');
  const tooltip = document.createElement('div');
  tooltip.id = 'rf-tooltip'; tooltip.className = 'rf-tooltip';
  tooltip.setAttribute('role', 'tooltip'); tooltip.hidden = true;
  document.body.append(tooltip);
  const projects = data.flatMap(group => group.projects);
  const currentYear = Number(new Intl.DateTimeFormat('en', {year: 'numeric', timeZone: 'Asia/Tokyo'}).format(new Date()));
  const from = Math.min(...projects.map(project => project.start));
  const to = Math.max(currentYear, ...projects.map(project => project.end));
  root.style.setProperty('--rf-years', to - from + 1);
  root.querySelector('.rf-heading > span').textContent = `FISCAL YEARS · ${from}–${to}`;
  const palette = {
    pi: ['#5899ef', '#183455', '#365b88', '#cee3ff', '#234b78'],
    coi: ['#55becb', '#13353e', '#2c626c', '#c4f0f3', '#1d4f5a'],
    jst: ['#b39ae8', '#302741', '#615076', '#e6dafa', '#47375e'],
    nict: ['#61c09a', '#173a31', '#326b56', '#c9f1df', '#225340'],
    scope: ['#d4ab68', '#3a2d1a', '#745c34', '#f7e3bd', '#554022'],
    other: ['#a2aec2', '#242e3d', '#4c5c73', '#dce4f1', '#34465c']
  };
  function el(tag, cls, text) {
    const x = document.createElement(tag); if (cls) x.className = cls;
    if (text !== undefined) x.textContent = text; return x;
  }
  function color(node, key) {
    ['color', 'bg', 'edge', 'bright', 'hover'].forEach((k, i) => node.style.setProperty('--rf-' + k, palette[key][i]));
  }
  function select(project, group, button) {
    root.querySelectorAll('.rf-bar').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    color(detail, group.color); detail.replaceChildren(); detail.hidden = false;
    const meta = el('div', 'rf-detail-meta');
    meta.append(el('span', '', project.program), el('span', 'rf-role', project.role || group.role));
    const period = project.start === project.end ? `FY${project.start}` : `FY${project.start}–${project.end}`;
    meta.append(el('time', '', period));
    detail.append(meta, el('h4', '', project.title), el('p', '', 'Project PI: ' + project.pi));
  }
  function hideTip() { tooltip.hidden = true; }
  function showTip(project, group, button) {
    color(tooltip, group.color); tooltip.replaceChildren();
    const header = el('div', 'rf-tooltip-head');
    header.append(el('span', '', project.program), el('span', 'rf-role', project.role || group.role));
    const period = project.start === project.end ? `FY${project.start}` : `FY${project.start}–${project.end}`;
    tooltip.append(header, el('p', '', project.title), el('small', '', period + ' · Project PI: ' + project.pi));
    tooltip.hidden = false;
    const box = button.getBoundingClientRect();
    const left = Math.max(12, Math.min(box.left, window.innerWidth - tooltip.offsetWidth - 12));
    const below = box.bottom + 9;
    const top = below + tooltip.offsetHeight <= window.innerHeight - 12 ? below : Math.max(12, box.top - tooltip.offsetHeight - 9);
    tooltip.style.left = left + 'px'; tooltip.style.top = top + 'px';
  }
  window.addEventListener('scroll', hideTip, true);
  window.addEventListener('resize', hideTip);
  document.addEventListener('keydown', event => { if (event.key === 'Escape') hideTip(); });
  function chart(groups, target) {
    const scroll = el('div', 'rf-scroll');
    scroll.setAttribute('role', 'region'); scroll.setAttribute('aria-label', 'Research funding timeline by fiscal year'); scroll.tabIndex = 0;
    const grid = el('div', 'rf-chart');
    const axis = el('div', 'rf-axis'); axis.append(el('span', '', 'FUNDING PROGRAM'));
    const ticks = el('div', 'rf-ticks');
    for (let year = from; year <= to; year++) ticks.append(el('span', year === currentYear ? 'rf-now' : '', year));
    axis.append(ticks); grid.append(axis);
    groups.forEach(group => {
      const row = el('div', 'rf-group'); color(row, group.color);
      const label = el('div', 'rf-label'), main = el('div', 'rf-label-main', group.label);
      label.append(main, el('small', '', group.sub)); row.append(label);
      const tracks = el('div', 'rf-tracks');
      const count = Math.max(...group.projects.map(p => p.track)) + 1;
      tracks.style.setProperty('--rf-tracks', count);
      for (let n = 0; n < count; n++) {
        const track = el('div', 'rf-track');
        group.projects.filter(p => p.track === n).forEach(project => {
          const button = el('button', 'rf-bar' + (project.start === project.end ? ' rf-short' : ''), project.short);
          button.type = 'button'; button.style.gridColumn = `${project.start - from + 1} / span ${project.end - project.start + 1}`;
          button.setAttribute('aria-pressed', 'false'); button.setAttribute('aria-controls', 'rf-detail');
          const period = project.start === project.end ? `FY${project.start}` : `FY${project.start}–${project.end}`;
          button.setAttribute('aria-label', `${group.label}, ${project.role || group.role}, ${project.program}, ${period}, ${project.title}`);
          button.setAttribute('aria-describedby', 'rf-tooltip');
          button.addEventListener('pointerenter', event => { if (event.pointerType !== 'touch') showTip(project, group, button); });
          button.addEventListener('pointerleave', hideTip);
          button.addEventListener('focus', () => showTip(project, group, button));
          button.addEventListener('blur', hideTip);
          button.addEventListener('click', () => select(project, group, button));
          track.append(button);
        }); tracks.append(track);
      }
      row.append(tracks); grid.append(row);
    });
    scroll.append(grid); target.append(scroll);
  }
  chart(data.filter(g => !g.other), document.getElementById('rf-main-chart'));
  chart(data.filter(g => g.other), document.getElementById('rf-other-chart'));
})();
