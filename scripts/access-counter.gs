/**
 * アクセスカウンター（Google Apps Script）
 *
 * - GET  ?action=hit&u=1   … アクセスを1件記録（u=1 はその日初めての訪問者）
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

function doGet(e) {
  const p = (e && e.parameter) || {};
  if (p.action === 'hit') return json_(hit_(p.u === '1'));
  return json_({ ok: true });
}

function doPost(e) {
  let body = {};
  try { body = JSON.parse(e.postData.contents); } catch (_) {}
  if (body.action === 'stats') return json_(stats_(String(body.id || ''), String(body.password || '')));
  return json_({ ok: false, error: 'bad_request' });
}

function hit_(isNewVisitor) {
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
    last30: last30
  };
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
  PropertiesService.getScriptProperties().deleteProperty('COUNTER');
}
