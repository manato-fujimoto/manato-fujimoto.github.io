// Output Timeline: one square per publication, built from the lists on this page.
(() => {
  const root = document.getElementById('ot-root');
  const yearsEl = document.getElementById('ot-years');
  if (!root || !yearsEl) return;
  let YEAR_OF;
  try { YEAR_OF = JSON.parse(yearsEl.textContent); } catch { return; }

  const TYPES = [
    {k: 'journal', name: 'Journal Articles', one: 'Journal article', color: 'var(--ot-j)'},
    {k: 'conference', name: 'International Conference Proceedings', one: 'International conference', color: 'var(--ot-c)'},
    {k: 'domestic-conference', name: 'Domestic Conference', one: 'Domestic conference', color: 'var(--ot-d)'}
  ];
  const TYPE = Object.fromEntries(TYPES.map((t, i) => [t.k, Object.assign(t, {i})]));
  const TOPICS = [
    {k:'loc',  name:'Localization & navigation',   re:/rfid|locali[sz]ation|position estimation|positioning|navigation|trilateration|位置推定|位置座標|位置情報|ナビゲーション|場所推定|スポット推定|存在領域|移動制御|移動補正|通信境界/},
    {k:'dis',  name:'Disaster & evacuation',       re:/evacu|disaster|emergency|slope failure|shelter|rescue|\bdtn\b|reunification|family tracing|manet|避難|災害|被災|斜面崩壊|ハザード|eress/},
    {k:'act',  name:'Activity recognition',         re:/activit|daily living|living|smarthome|smart home|行動認識|宅内行動|生活行動|行動推定|スマートホーム|行動履歴|動作認識|行動予測|行動分析|コンテキスト認識|echonet/},
    {k:'care', name:'Elderly care',     re:/\bcare|daycare|nursing|elderly|senior|carer|介護|高齢者|デイケア|ケアレポート|フレイル|生きがい/},
    {k:'sens', name:'Sensing',   re:/\bcsi\b|wifi|doppler|\bpir\b|vibration|piezo|energy harvest|acoustic|sensor|sensing|\bble\b|bluetooth|beacon|\bimu\b|inertial|acceleromet|solar cell|センサ|センシング|ビーコン|ドップラー|ピエゾ|環境発電|エナジーハーベスト|ウェアラブル|振動/},
    {k:'tour', name:'Tourism',             re:/touris|sightseeing|trip plan|tour plan|観光|ツーリズム/},
    {k:'bc',   name:'Behavior change',         re:/behavior change|nudg|signage|gamif|incentive|awareness|well-being|行動変容|ナッジ|サイネージ|ゲーミフィケーション|促進|ウェルビーイング/},
    {k:'sport',name:'Sports & exercise',   re:/kendo|exercise|weight training|cane|cycling|剣道|トレーニング|体操|卓球|テニス|自転車競技|杖|歩行|歩容|転倒/},
    {k:'psy',  name:'Concentration & emotion',   re:/concentration|emotion|stress|focussense|work attitude|集中|感情|ストレス|満足度|心身状態|内的活性度/},
    {k:'med',  name:'In-body & medical',       re:/implant|in-body|puncture|blood glucose|bioindicator|semg|vaccine|穿刺|生体内|血糖|糖尿病|生体指標|生体情報|発汗|ヘルスケア/},
    {k:'net',  name:'Networking & IoT', re:/\biot\b|network|federated|\bdns\b|building|multi-hop|forwarding|streaming|blockchain|application distribution|zero-knowledge|ネットワーク|連合学習|ビル|マルチホップ|ストリーミング|cefore|キャッシング|アクセス制御|データプラットフォーム|無線lan|\bllm|ログ解析|システムログ|ログ管理|チャットボット|ヘルプデスク|パーソナルデータ|なりすまし/}
  ];
  // query trigger (Japanese) -> related terms (English and Japanese)
  const DICT = [
    [/高齢|シニア|お年寄り|老人/, /elderly|senior|nursing|day ?care|高齢|フレイル/],
    [/見守り|みまもり/, /monitoring|elderly|senior|day ?care|nursing|高齢|介護|デイケア/],
    [/介護|ケア|福祉/, /\bcare|nursing|carer|daycare|介護|デイケア|ケアレポート/],
    [/センサ|センシング/, /sensor|sensing|\bpir\b|\bimu\b|doppler|piezo|センサ|センシング/],
    [/災害|防災|減災/, /disaster|evacu|emergency|slope failure|\bdtn\b|災害|被災|避難|斜面崩壊/],
    [/避難/, /evacu|shelter|避難/],
    [/配信|配布|共有/, /distribution|forwarding|sharing|exchanging|streaming|共有|配信/],
    [/活動量|行動認識|生活行動|行動推定|活動/, /activit|daily living|exercise|walking|行動認識|生活行動|宅内行動|行動推定/],
    [/位置|測位|屋内|ナビ/, /locali[sz]ation|position|indoor|navigation|位置|屋内|ナビ/],
    [/観光|旅行|ツーリズム/, /touris|sightseeing|trip|tour plan|観光/],
    [/行動変容|ナッジ|介入/, /behavior change|nudg|signage|gamif|incentive|intervention|行動変容|ナッジ|サイネージ/],
    [/スマートホーム|家庭|宅内|家電/, /smart ?home|in-home|general homes|ordinary home|appliance|スマートホーム|宅内|家電|家庭/],
    [/集中/, /concentration|focussense|集中/],
    [/感情|ストレス|満足/, /emotion|stress|satisfaction|感情|ストレス|満足/],
    [/体内|インプラント|医療|手術/, /implant|in-body|puncture|medicine|ct-guided|生体内|穿刺/],
    [/健康|ヘルス|リハビリ|血糖/, /health|exercise|rehabil|blood glucose|well-being|血糖|フレイル|ヘルスケア|糖尿病/],
    [/ネットワーク|通信/, /network|communication|multi-hop|\bdtn\b|manet|ネットワーク|通信|マルチホップ/],
    [/機器識別|デバイス識別|機器同定|IoT機器/i, /device identification|機器同定|機器の同定/],
    [/連合学習/, /federated|連合学習/],
    [/機械学習|深層学習|ＡＩ|人工知能|LLM|生成AI/i, /machine learning|deep ?learning|transformer|attention|\bllm|federated|機械学習|深層学習|連合学習/],
    [/無線|電波|ワイヤレス/, /wifi|wlan|\bcsi\b|\bble\b|bluetooth|rfid|uwb|ultra-wideband|wireless|無線|ワイヤレス/],
    [/ロボット/, /robot|ロボット/],
    [/スポーツ|運動|剣道|トレーニング/, /kendo|training|cycling|exercise|剣道|トレーニング|体操|卓球|テニス|自転車/],
    [/ビル|建物/, /building|ビル/],
    [/混雑|人数|群衆/, /congestion|crowd|混雑|群衆/],
    [/振動/, /vibration|piezo|振動|ピエゾ/],
    [/ブロックチェーン|セキュリティ|プライバシ|真正性|認可/, /blockchain|zero-knowledge|privacy|security|authenticity|アクセス制御|認可|なりすまし/],
    [/アンテナ/, /antenna|アンテナ/],
    [/メタバース|点群|仮想/, /metaverse|point cloud|virtual|点群|バーチャル/],
    [/食|飲料|冷蔵庫/, /beverage|foodstuff|fridge|飲料|飲水|食事|料理/],
    [/非接触|デバイスフリー/, /non-contact|device-free|doppler|非接触|デバイスフリー|ドップラー/],
    [/環境発電|エナジーハーベスト|電力|省電力/, /energy harvest|solar|battery-free|power|環境発電|エナジーハーベスト|電力/],
    [/スマホ|スマートフォン/, /smartphone|ios|スマホ|スマートフォン|携帯端末/],
    [/ウェアラブル/, /wearable|wrist|ウェアラブル|スマートウォッチ/],
    [/カーシェア|交通|自動車|車両/, /car sharing|カーシェア|車両/],
    [/オンライン|講義|授業|教育|採点/, /lecture|video conferencing|grading|paper tests|授業|採点|オンライン|遠隔/]
  ];
  // English query term -> Japanese title term
  const EN_JA = [
    [/evacuat|shelter/, /避難/], [/disaster/, /災害|被災/], [/elderly|senior/, /高齢/], [/\bcare|nursing/, /介護|デイケア|ケアレポート/],
    [/sensor|sensing/, /センサ|センシング/], [/locali[sz]ation|position/, /位置推定|位置座標|場所推定/], [/navigation/, /ナビ/],
    [/touris|sightseeing/, /観光/], [/behavior change|nudg/, /行動変容|ナッジ/], [/activit/, /行動認識|行動推定|生活行動|宅内行動/],
    [/smart ?home/, /スマートホーム|宅内/], [/concentration/, /集中/], [/emotion/, /感情/], [/stress/, /ストレス/], [/robot/, /ロボット/],
    [/network/, /ネットワーク/], [/federated/, /連合学習/], [/machine learning/, /機械学習/], [/deep learning/, /深層学習/],
    [/wearable/, /ウェアラブル/], [/vibration/, /振動/], [/congestion|crowd/, /混雑|群衆/], [/kendo/, /剣道/], [/building/, /ビル/],
    [/puncture/, /穿刺/], [/in-body|implant/, /生体内/], [/blood glucose/, /血糖/], [/doppler/, /ドップラー/], [/beacon/, /ビーコン/],
    [/energy harvest/, /環境発電|エナジーハーベスト/], [/gamif/, /ゲーミフィケーション/], [/signage/, /サイネージ/], [/indoor/, /屋内|宅内/],
    [/car sharing/, /カーシェア/], [/chatbot/, /チャットボット/], [/frail/, /フレイル/], [/satisfaction/, /満足度/],
    [/multimodal/, /マルチモーダル/], [/smartphone/, /スマートフォン|スマホ|携帯端末/], [/wireless/, /無線|ワイヤレス/]
  ];

  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };

  const PUBS = [];
  document.querySelectorAll('.publication-group').forEach(group => {
    if (!TYPE[group.id]) return;
    group.querySelectorAll('li.publication[id]').forEach((li, n) => {
      const y = Number(YEAR_OF[li.id]);
      if (!y) return;
      const title = (li.querySelector('.pub-title') || li).textContent.trim();
      const lt = title.toLowerCase();
      const tags = Array.from(li.querySelectorAll('.pub-tags .status')).map(s => s.textContent.trim());
      PUBS.push({id: li.id, type: group.id, y, n, title, lt, hay: li.textContent.toLowerCase(), s: 1,
        note: tags.find(x => /^(Accepted|Scheduled|採択済み|発表予定)$/i.test(x)) || '',
        topics: TOPICS.filter(tp => tp.re.test(lt)).map(tp => tp.k)});
    });
  });
  if (!PUBS.length) return;

  const Y0 = Math.min(...PUBS.map(p => p.y)), Y1 = Math.max(...PUBS.map(p => p.y));
  const YEARS = Array.from({length: Y1 - Y0 + 1}, (_, i) => Y0 + i);
  const state = {types: new Set(TYPES.map(t => t.k)), year: null, topic: null, q: ''};

  // ---------- skeleton ----------
  root.textContent = '';
  const tiles = el('div', 'ot-tiles'); tiles.setAttribute('role', 'group'); tiles.setAttribute('aria-label', 'Filter by category');
  const form = el('form', 'ot-search'); form.setAttribute('role', 'search');
  const input = el('input'); input.type = 'search'; input.autocomplete = 'off';
  input.setAttribute('aria-label', 'Search publications');
  input.placeholder = 'Search (e.g. activity recognition, evacuation, indoor localization, RFID)';
  const go = el('button', '', 'Search'); go.type = 'submit';
  form.append(input, go);
  const hint = el('p', 'ot-hint', 'Keywords are expanded to related English and Japanese terms and matched against titles, authors and venues. Matching items stay lit; the rest are dimmed.');
  const status = el('div', 'ot-status'); status.setAttribute('aria-live', 'polite');
  const scroll = el('div', 'ot-scroll'), viz = el('div', 'ot-viz');
  const h1 = el('h3', 'ot-h', 'Output by year'); h1.append(el('small', '', '(one square = one item; select a square to jump to it in the list, select a year to highlight it)'));
  const units = el('div', 'ot-grid ot-units'), years = el('div', 'ot-grid ot-years ot-mono');
  const h2 = el('h3', 'ot-h', 'Research topics over time'); h2.append(el('small', '', '(extracted automatically from titles; numbers are item counts; select a row or a cell to highlight)'));
  const heat = el('div', 'ot-grid ot-heat ot-mono');
  const scale = el('div', 'ot-scale');
  [['1', 1], ['2–3', 2], ['4–6', 3], ['7–9', 4], ['10+', 5]].forEach(([label, l]) => { const i = el('i'); i.style.background = 'var(--ot-h' + l + ')'; scale.append(el('span', '', label), i); });
  [units, years, heat].forEach(g => g.style.setProperty('--ot-n', YEARS.length));
  viz.append(h1, units, years, h2, heat, scale); scroll.append(viz);
  const foot = el('p', 'ot-foot', 'Years are publication or presentation years and include accepted and scheduled items. Topics are assigned automatically from words in the title, so an item can count under several topics or under none.');
  const tip = el('div', 'ot-tip'); tip.setAttribute('role', 'status');
  root.append(tiles, form, hint, status, scroll, foot, tip);

  TYPES.forEach(t => {
    const b = el('button', 'ot-tile'); b.type = 'button'; b.setAttribute('aria-pressed', 'true');
    const nm = el('span', 'ot-name'); const i = el('i'); i.style.background = t.color; nm.append(i, t.name);
    b.append(nm, el('b', 'ot-mono', PUBS.filter(p => p.type === t.k).length));
    b.addEventListener('click', () => {
      if (state.types.has(t.k)) { if (state.types.size > 1) state.types.delete(t.k); } else state.types.add(t.k);
      b.setAttribute('aria-pressed', state.types.has(t.k)); render();
    });
    tiles.append(b);
  });

  // ---------- search ----------
  function plan(q) {
    const ql = q.toLowerCase();
    const concepts = DICT.filter(([jp]) => jp.test(q)).map(([, rel]) => rel).concat(EN_JA.filter(([en]) => en.test(ql)).map(([, ja]) => ja));
    const words = ql.match(/[a-z0-9][a-z0-9\-]+/g) || [];
    const chunks = q.split(/[\sa-zA-Z0-9\-、，,・。のとをにがはでへや]+/).filter(c => c.length >= 2);
    return {concepts, words, chunks, n: concepts.length + words.length + chunks.length};
  }
  function rescore() {
    if (!state.q) { PUBS.forEach(p => { p.s = 1; }); return; }
    const pl = plan(state.q);
    PUBS.forEach(p => {
      let s = 0;
      if (pl.n) {
        pl.concepts.forEach(re => { if (re.test(p.lt)) s += 2; });
        pl.words.forEach(w => { if (p.hay.includes(w)) s += 2; });
        pl.chunks.forEach(c => { if (p.hay.includes(c)) s += 2; });
      }
      p.s = s;
    });
    const top = Math.max(0, ...PUBS.map(p => p.s)), cut = Math.ceil(top * (top <= 4 ? 0.5 : 0.6));
    PUBS.forEach(p => { if (p.s < cut) p.s = 0; });
  }
  const okBase = p => state.types.has(p.type) && p.s > 0;
  const okTopic = p => !state.topic || p.topics.includes(state.topic);
  const okYear = p => state.year == null || p.y === state.year;

  // ---------- tooltip ----------
  function showTip(anchor, title, lines, color) {
    tip.textContent = ''; tip.append(el('b', '', title));
    lines.forEach((line, n) => { const s = el('span'); if (n === 0 && color) { const i = el('i'); i.style.background = color; s.append(i); } s.append(line); tip.append(s); });
    tip.style.display = 'block';
    const r = anchor.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    let x = r.left + r.width / 2 - w / 2; x = Math.max(8, Math.min(x, innerWidth - w - 8));
    let y = r.top - h - 8; if (y < 8) y = r.bottom + 8;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }
  const hideTip = () => { tip.style.display = 'none'; };
  addEventListener('scroll', hideTip, true);
  const hover = (node, fn) => { node.addEventListener('mouseenter', fn); node.addEventListener('focus', fn); node.addEventListener('mouseleave', hideTip); node.addEventListener('blur', hideTip); };

  // ---------- render ----------
  function renderUnits() {
    units.textContent = ''; years.textContent = '';
    const note = el('div', 'ot-unit-note'); note.append(el('i'), '= 1 item'); units.append(note);
    YEARS.forEach((y, i) => {
      const col = el('div', 'ot-col'); col.style.gridColumn = i + 2;
      const items = PUBS.filter(p => p.y === y).sort((a, b) => TYPE[a.type].i - TYPE[b.type].i || b.n - a.n);
      let lit = 0;
      items.forEach(p => {
        const on = okBase(p) && okTopic(p) && okYear(p); if (on) lit++;
        const a = el('a', 'ot-u' + (on ? '' : ' ot-dim'));
        a.href = '#' + p.id; a.style.setProperty('--c', TYPE[p.type].color);
        a.setAttribute('aria-label', y + ', ' + TYPE[p.type].one + ': ' + p.title);
        hover(a, () => showTip(a, p.title, [TYPE[p.type].one + ' · ' + p.y + (p.note ? ' (' + p.note.toLowerCase() + ')' : ''), 'Select to jump to this entry'], TYPE[p.type].color));
        col.append(a);
      });
      col.append(el('div', 'ot-cnt ot-mono', lit === items.length ? items.length : lit + '/' + items.length));
      units.append(col);
      const b = el('button', 'ot-year', "'" + String(y).slice(2)); b.type = 'button'; b.style.gridColumn = i + 2;
      b.setAttribute('aria-label', 'Highlight ' + y); b.setAttribute('aria-pressed', state.year === y);
      b.addEventListener('click', () => { state.year = state.year === y ? null : y; render(); });
      years.append(b);
    });
  }
  const level = n => n >= 10 ? 5 : n >= 7 ? 4 : n >= 4 ? 3 : n >= 2 ? 2 : n;
  function renderHeat() {
    heat.textContent = '';
    const all = PUBS.filter(okBase);
    TOPICS.forEach((tp, r) => {
      const lab = el('button', 'ot-row', tp.name); lab.type = 'button'; lab.style.gridRow = r + 1;
      lab.setAttribute('aria-pressed', state.topic === tp.k);
      lab.addEventListener('click', () => { state.topic = state.topic === tp.k ? null : tp.k; render(); });
      heat.append(lab);
      YEARS.forEach((y, i) => {
        const n = all.filter(p => p.y === y && p.topics.includes(tp.k)).length;
        const c = el('button', 'ot-cell' + (state.topic === tp.k && state.year === y ? ' ot-on' : ''), n || '');
        c.type = 'button'; c.style.gridRow = r + 1; c.style.gridColumn = i + 2;
        c.dataset.l = level(n); c.disabled = !n;
        c.setAttribute('aria-label', tp.name + ', ' + y + ': ' + n + ' items');
        if (n) {
          c.addEventListener('click', () => { const same = state.topic === tp.k && state.year === y; state.topic = same ? null : tp.k; state.year = same ? null : y; render(); });
          hover(c, () => showTip(c, tp.name + ' · ' + y, [n + (n === 1 ? ' item' : ' items')]));
        }
        heat.append(c);
      });
    });
  }
  function renderStatus() {
    status.textContent = '';
    const n = PUBS.filter(p => okBase(p) && okTopic(p) && okYear(p)).length;
    const filtered = state.q || state.year != null || state.topic || state.types.size < TYPES.length;
    status.append(el('strong', '', filtered ? n + ' of ' + PUBS.length + ' items highlighted' : PUBS.length + ' items · ' + Y0 + '–' + Y1));
    const chip = (text, clear) => { const b = el('button', 'ot-chip', text); b.type = 'button'; b.setAttribute('aria-label', 'Remove filter: ' + text); b.addEventListener('click', () => { clear(); render(); }); status.append(b); };
    if (state.q) chip('Search: ' + state.q, () => { state.q = ''; input.value = ''; });
    if (state.year != null) chip(String(state.year), () => { state.year = null; });
    if (state.topic) chip(TOPICS.find(t => t.k === state.topic).name, () => { state.topic = null; });
    if (filtered) {
      const c = el('button', 'ot-clear', 'Clear all'); c.type = 'button';
      c.addEventListener('click', () => {
        state.q = ''; input.value = ''; state.year = null; state.topic = null;
        state.types = new Set(TYPES.map(t => t.k));
        tiles.querySelectorAll('.ot-tile').forEach(b => b.setAttribute('aria-pressed', 'true'));
        render();
      });
      status.append(c);
    }
    if (state.q && !n) status.append(el('span', '', 'No match. Try another word such as "care", "evacuation", "localization" or "RFID".'));
  }
  function render() { hideTip(); rescore(); renderUnits(); renderHeat(); renderStatus(); }

  form.addEventListener('submit', e => { e.preventDefault(); state.q = input.value.trim(); render(); });
  input.addEventListener('input', () => { if (!input.value && state.q) { state.q = ''; render(); } });
  render();
})();
