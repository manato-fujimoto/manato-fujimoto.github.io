/**
 * アクセスカウンター（Google Apps Script）
 *
 * - GET  ?action=hit&u=1&p=/path … アクセスを1件記録（u=1 はその日初めての訪問者、p は見たページ）
 * - POST {"action":"stats","id":"...","password":"..."} … 集計を返す（認証必須）
 *
 * ID とパスワードはこのコードには書かず、
 * 「プロジェクトの設定 → スクリプト プロパティ」に
 *   ADMIN_ID / ADMIN_PASSWORD
 * として登録してください。
 */

const TZ = 'Asia/Tokyo';
const KEEP_DAYS = 120;          // 日別データの保存日数（プロパティの容量制限のため）
const MAX_FAILS = 10;           // 連続ログイン失敗の上限
const LOCK_SECONDS = 15 * 60;   // 上限到達後のロック時間
const PAGE_DAYS = 31;           // ページ別の日次データの保存日数
const MAX_PAGES = 300;          // 記録するページ数の上限（いたずら対策）

function doGet(e) {
  const p = (e && e.parameter) || {};
  if (p.action === 'hit') return json_(hit_(p.u === '1', cleanPath_(p.p)));
  return json_({ ok: true });
}

function doPost(e) {
  let body = {};
  try { body = JSON.parse(e.postData.contents); } catch (_) {}
  if (body.action === 'stats') return json_(stats_(String(body.id || ''), String(body.password || '')));
  return json_({ ok: false, error: 'bad_request' });
}

function hit_(isNewVisitor, path) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) return { ok: false, error: 'busy' };
  try {
    const props = PropertiesService.getScriptProperties();
    const data = load_(props);
    const today = dateKey_(new Date());
    const d = data.days[today] || (data.days[today] = { pv: 0, uv: 0 });
    data.pv++; d.pv++;
    if (isNewVisitor) { data.uv++; d.uv++; }

    const keys = Object.keys(data.days).sort();
    while (keys.length > KEEP_DAYS) delete data.days[keys.shift()];

    props.setProperty('COUNTER', JSON.stringify(data));
    if (path) countPage_(props, today, path);
    return { ok: true };
  } finally {
    lock.releaseLock();
  }
}

function stats_(id, password) {
  const cache = CacheService.getScriptCache();
  const fails = Number(cache.get('fails') || 0);
  if (fails >= MAX_FAILS) return { ok: false, error: 'locked' };

  const props = PropertiesService.getScriptProperties();
  const okId = props.getProperty('ADMIN_ID');
  const okPw = props.getProperty('ADMIN_PASSWORD');
  if (!okId || !okPw || id !== okId || password !== okPw) {
    cache.put('fails', String(fails + 1), LOCK_SECONDS);
    Utilities.sleep(800);
    return { ok: false, error: 'auth' };
  }
  cache.remove('fails');

  const data = load_(props);
  const now = new Date();
  const today = dateKey_(now);
  const yesterday = dateKey_(new Date(now.getTime() - 86400000));
  const month = today.slice(0, 7);

  const last30 = [];
  for (let i = 29; i >= 0; i--) {
    const k = dateKey_(new Date(now.getTime() - i * 86400000));
    const d = data.days[k] || { pv: 0, uv: 0 };
    last30.push({ date: k, pv: d.pv, uv: d.uv });
  }

  const monthTotal = { pv: 0, uv: 0 };
  Object.keys(data.days).forEach(function (k) {
    if (k.slice(0, 7) === month) {
      monthTotal.pv += data.days[k].pv;
      monthTotal.uv += data.days[k].uv;
    }
  });

  return {
    ok: true,
    since: data.since,
    total: { pv: data.pv, uv: data.uv },
    today: data.days[today] || { pv: 0, uv: 0 },
    yesterday: data.days[yesterday] || { pv: 0, uv: 0 },
    month: monthTotal,
    last30: last30,
    pages: pageStats_(props, now)
  };
}

// ---- ページ別の集計 ----
function cleanPath_(p) {
  if (!p) return '';
  p = String(p).split('?')[0].split('#')[0].slice(0, 120);
  if (!/^\/[A-Za-z0-9\/_.\-]*$/.test(p)) return '';
  return p.replace(/index\.html$/, '');
}

function countPage_(props, today, path) {
  const total = JSON.parse(props.getProperty('PAGES_TOTAL') || '{}');
  if (!(path in total) && Object.keys(total).length >= MAX_PAGES) return;
  total[path] = (total[path] || 0) + 1;
  props.setProperty('PAGES_TOTAL', JSON.stringify(total));

  const key = 'PAGES_' + today;
  const day = JSON.parse(props.getProperty(key) || '{}');
  day[path] = (day[path] || 0) + 1;
  props.setProperty(key, JSON.stringify(day));

  const old = props.getKeys().filter(function (k) { return /^PAGES_\d{4}-\d{2}-\d{2}$/.test(k); }).sort();
  while (old.length > PAGE_DAYS) props.deleteProperty(old.shift());
}

function pageStats_(props, now) {
  const all = props.getProperties();
  const total = JSON.parse(all.PAGES_TOTAL || '{}');
  const today = JSON.parse(all['PAGES_' + dateKey_(now)] || '{}');
  const last30 = {};
  for (let i = 0; i < 30; i++) {
    const day = JSON.parse(all['PAGES_' + dateKey_(new Date(now.getTime() - i * 86400000))] || '{}');
    Object.keys(day).forEach(function (p) { last30[p] = (last30[p] || 0) + day[p]; });
  }
  return Object.keys(total).map(function (p) {
    return { path: p, today: today[p] || 0, last30: last30[p] || 0, total: total[p] };
  }).sort(function (a, b) { return b.last30 - a.last30 || b.total - a.total; });
}

function load_(props) {
  const raw = props.getProperty('COUNTER');
  if (raw) return JSON.parse(raw);
  return { since: dateKey_(new Date()), pv: 0, uv: 0, days: {} };
}

function dateKey_(d) {
  return Utilities.formatDate(d, TZ, 'yyyy-MM-dd');
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/** カウントを0に戻したいときだけ、エディタから手動で実行してください */
function resetCounter() {
  const props = PropertiesService.getScriptProperties();
  props.getKeys().forEach(function (k) {
    if (k === 'COUNTER' || /^PAGES_/.test(k)) props.deleteProperty(k);
  });
}
