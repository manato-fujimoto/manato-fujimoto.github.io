(() => {
  const ja = document.documentElement.lang === 'ja';
  const t = (en, jp) => ja ? jp : en;
  const translations = {
    'KAKENHI': '科研費', 'Grants-in-Aid for\nScientific Research': '科学研究費助成事業',
    'Principal Investigator': '研究代表者', 'Co-Investigator': '研究分担者',
    'Grant-in-Aid for JSPS Fellows': '特別研究員奨励費', 'JSPS': '特別研究員',
    'Grant-in-Aid for Scientific Research (A)': '基盤研究（A）',
    'Grant-in-Aid for Scientific Research (B)': '基盤研究（B）',
    'Grant-in-Aid for Scientific Research (C)': '基盤研究（C）',
    'Grant-in-Aid for Challenging Research (Exploratory)': '挑戦的研究（萌芽）',
    'C · Activity recognition': '基盤C · 行動認識', 'B · Care planning': '基盤B · 介護計画',
    'B · Smart platform network': '基盤B · スマート基盤ネットワーク', 'B': '基盤B',
    'A · Participatory sensing': '基盤A · 参加型センシング',
    'C · Vehicle–pedestrian safety': '基盤C · 車両・歩行者の安全',
    'Exploratory · AI card game': '萌芽 · AIカードゲーム',
    'B · Disaster information': '基盤B · 災害情報', 'C · Emergency evacuation': '基盤C · 緊急避難',
    'A · Disaster information · Phase 2': '基盤A · 災害情報（第2期）',
    'JST-Mirai Program': '未来社会創造事業',
    'JST-Mirai Program (Small-start Type)': 'JST 未来社会創造事業（探索加速型）',
    'Mirai · Child well-being': '未来社会 · 子どものウェルビーイング',
    'Commissioned Research': '委託研究', 'NICT Commissioned Research (Category A)': 'NICT 委託研究（区分A）',
    'Strategic ICT R&D\nPromotion Programme': '戦略的情報通信研究開発推進事業',
    'SCOPE: Priority-Area R&D, Type II (Phase I)': 'SCOPE 重点領域型研究開発・タイプII（フェーズI）',
    'Foundation Grants': '民間財団助成', 'JR-West Relief Foundation': 'JR西日本あんしん社会財団',
    'JR-West Relief Foundation Research Grant': 'JR西日本あんしん社会財団 研究助成', 'Grant': '研究助成',
    'Grand Challenge Research': 'グランドチャレンジ研究',
    'Osaka University Society 5.0 Grand Challenge Research': '大阪大学 Society 5.0 グランドチャレンジ研究',
    'Care activity logs': '介護行動記録', 'Care logs · Phase 2': '介護行動記録（第2期）', 'Daily-life data': '生活行動データ',
    'Manato Fujimoto': '藤本まなと', 'Shingo Ata': '阿多信吾', 'Keiichi Yasumoto': '安本慶一',
    'Tomotaka Wada': '和田友孝', 'Yuki Minami': '南裕樹', 'Hirohiko Suwa': '諏訪博彦',
    'Takefumi Kikusui': '菊水健史', 'Satoshi Nakamura': '中村哲', 'Yafei Hou': '侯亜飛',
    'Development of an RFID-Based Autonomous Navigation System for Advanced Care Robots': '高度介護ロボットのためのRFIDを用いた自律ナビゲーションシステムの開発',
    'Development and Applications of an Activity Recognition System Using BLE and Energy-Harvesting Sensors': 'BLEと環境発電センサを用いた行動認識システムの開発と応用',
    'A Next-Generation Care Planning Platform Based on Spatiotemporal Activity Recognition to Reduce Caregiver Workload': '介護者の負担軽減に向けた時空間行動認識に基づく次世代介護計画基盤',
    'An Integrated Facility and Information Network Architecture for Smart Platforms': 'スマートプラットフォームのための設備・情報ネットワーク統合アーキテクチャ',
    'Highly Efficient Participatory Video Sensing Through Adaptive Sensing Granularity and Gamification': '適応的なセンシング粒度とゲーミフィケーションによる参加型映像センシングの高効率化',
    'A Participatory Sensing Platform for Real-Time Content Curation': 'リアルタイムなコンテンツ編纂のための参加型センシング基盤',
    'Safe and Effective Vehicle–Pedestrian Interaction Through the Integration of Machine Learning and Wireless Communication': '機械学習と無線通信の融合による安全かつ効果的な車両・歩行者間インタラクション',
    'A Control Engineering AI Card Game: Designing Fake Assistance to Stimulate Learning Engagement': '制御工学AIカードゲーム：学習意欲を刺激するフェイク支援の設計',
    'Development of a Sustainable Disaster Information Distribution Support System During Internet Outages': 'インターネット途絶時にも持続可能な災害情報配信支援システムの開発',
    'Development of an Emergency Rescue and Evacuation Support System Based on Human-Collaborative Automatic Detection of Local Disasters': '人と協調した局所災害の自動検知に基づく緊急救助・避難支援システムの開発',
    'Development of a Sustainable Disaster Information Distribution Support System During Internet Outages: Phase 2': 'インターネット途絶時にも持続可能な災害情報配信支援システムの開発（第2期）',
    'Development of Technologies to Support Child Well-Being Using Physical Function and Household Network Information': '身体機能と家庭内ネットワーク情報を用いた子どものウェルビーイング支援技術の開発',
    'Research and Development of an IoT-to-Human System for Inbound Tourism in Kyoto': '京都のインバウンド観光に向けたIoT-to-Humanシステムの研究開発',
    'Research and Development of Sensor Network Construction Technology for Slope Failure Detection Using Smartphone Applications': 'スマートフォンアプリケーションを用いた斜面崩壊検知のためのセンサネットワーク構築技術の研究開発',
    'Automatic Detection of Sudden Disasters and Evacuation Guidance Using Mobile Devices': 'モバイル端末を用いた突発災害の自動検知と避難誘導',
    'A Care Activity Logging System to Reduce Caregiver Workload': '介護者の負担軽減に向けた介護行動記録システム',
    'A Care Activity Logging System to Reduce Caregiver Workload: Phase 2': '介護者の負担軽減に向けた介護行動記録システム（第2期）',
    'A Daily-Life Data Collection Platform for Smart Communities': 'スマートコミュニティのための生活行動データ収集基盤'
  };
  const translate = value => ja ? (translations[value] || value) : value;
  const localize = record => Object.fromEntries(Object.entries(record).map(([key, value]) => [key, typeof value === 'string' ? translate(value) : value]));
  const data = JSON.parse(document.getElementById('rf-data').textContent).map(group => ({...localize(group), projects: group.projects.map(localize)}));
  const periodOf = project => ja ? (project.start === project.end ? `${project.start}年度` : `${project.start}–${project.end}年度`) : (project.start === project.end ? `FY${project.start}` : `FY${project.start}–${project.end}`);
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
  root.querySelector('.rf-heading > span').textContent = t(`FISCAL YEARS · ${from}–${to}`, `年度 · ${from}–${to}`);
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
    const period = periodOf(project);
    meta.append(el('time', '', period));
    detail.append(meta, el('h4', '', project.title), el('p', '', t('Project PI: ', '研究代表者：') + project.pi));
  }
  function hideTip() { tooltip.hidden = true; }
  function showTip(project, group, button) {
    color(tooltip, group.color); tooltip.replaceChildren();
    const header = el('div', 'rf-tooltip-head');
    header.append(el('span', '', project.program), el('span', 'rf-role', project.role || group.role));
    const period = periodOf(project);
    tooltip.append(header, el('p', '', project.title), el('small', '', period + t(' · Project PI: ', ' · 研究代表者：') + project.pi));
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
    scroll.setAttribute('role', 'region'); scroll.setAttribute('aria-label', t('Research funding timeline by fiscal year', '年度別の研究費獲得実績')); scroll.tabIndex = 0;
    const grid = el('div', 'rf-chart');
    const axis = el('div', 'rf-axis'); axis.append(el('span', '', t('FUNDING PROGRAM', '研究費の種別')));
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
          const period = periodOf(project);
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
