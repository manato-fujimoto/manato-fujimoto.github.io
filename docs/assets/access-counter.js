/* Access counter: records page views and shows totals after ID/password login.
   The counter and the credentials live in Google Apps Script (data-endpoint on the script tag);
   nothing secret is stored in this file. */
(function () {
  var script = document.currentScript;
  var ENDPOINT = script && script.getAttribute('data-endpoint');
  var ja = document.documentElement.lang === 'ja';
  var T = ja ? {
    title: 'アクセスカウンター', id: 'ID', pw: 'パスワード', login: 'ログイン', close: '閉じる',
    loading: '読み込み中…', auth: 'ID またはパスワードが違います。', locked: '試行回数が多すぎます。15分後にお試しください。',
    error: '接続できませんでした。', today: '今日', yesterday: '昨日', month: '今月', total: '合計',
    pv: '表示回数', uv: '訪問者', last30: '直近30日の表示回数', since: '集計開始：'
  } : {
    title: 'Access Counter', id: 'ID', pw: 'Password', login: 'Log in', close: 'Close',
    loading: 'Loading…', auth: 'ID or password is incorrect.', locked: 'Too many attempts. Try again in 15 minutes.',
    error: 'Could not connect.', today: 'Today', yesterday: 'Yesterday', month: 'This month', total: 'Total',
    pv: 'Views', uv: 'Visitors', last30: 'Views in the last 30 days', since: 'Counting since '
  };

  // ---- Record the visit (a reload in the same tab is not counted again) ----
  try {
    var key = 'ac_hit:' + location.pathname;
    if (ENDPOINT && !navigator.webdriver && !sessionStorage.getItem(key)) {
      sessionStorage.setItem(key, '1');
      var d = new Date();
      var today = d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate();
      var isNew = localStorage.getItem('ac_last') !== today;
      localStorage.setItem('ac_last', today);
      fetch(ENDPOINT + '?action=hit&u=' + (isNew ? '1' : '0'), { mode: 'no-cors', keepalive: true });
    }
  } catch (e) {}

  // ---- Login dialog ----
  var dlg;
  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (text) n.textContent = text;
    return n;
  }
  function build() {
    dlg = el('dialog', { 'class': 'ac-dialog', 'aria-label': T.title });
    dlg.innerHTML =
      '<form class="ac-form" method="dialog">' +
      '<p class="ac-title"></p>' +
      '<label><span></span><input name="id" type="email" autocomplete="username" required></label>' +
      '<label><span></span><input name="pw" type="password" autocomplete="current-password" required></label>' +
      '<div class="ac-buttons"><button type="submit" class="ac-primary"></button><button type="button" class="ac-close"></button></div>' +
      '<p class="ac-msg" role="status"></p></form>' +
      '<div class="ac-result" hidden></div>';
    var form = dlg.querySelector('form');
    form.querySelector('.ac-title').textContent = T.title;
    var spans = form.querySelectorAll('label span');
    spans[0].textContent = T.id; spans[1].textContent = T.pw;
    form.querySelector('.ac-primary').textContent = T.login;
    form.querySelector('.ac-close').textContent = T.close;
    form.querySelector('.ac-close').addEventListener('click', function () { dlg.close(); });
    form.addEventListener('submit', function (e) { e.preventDefault(); login(form); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    document.body.appendChild(dlg);
  }
  function login(form) {
    var msg = form.querySelector('.ac-msg');
    msg.className = 'ac-msg'; msg.textContent = T.loading;
    fetch(ENDPOINT, {
      method: 'POST',
      body: JSON.stringify({ action: 'stats', id: form.elements['id'].value.trim(), password: form.elements['pw'].value })
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (!d.ok) { msg.className = 'ac-msg ac-error'; msg.textContent = d.error === 'locked' ? T.locked : T.auth; return; }
      form.elements['pw'].value = ''; msg.textContent = '';
      render(d);
    }).catch(function () { msg.className = 'ac-msg ac-error'; msg.textContent = T.error; });
  }
  function render(d) {
    var res = dlg.querySelector('.ac-result');
    var max = Math.max.apply(null, d.last30.map(function (x) { return x.pv; }).concat([1]));
    function row(label, o) { return '<tr><th scope="row">' + label + '</th><td>' + o.pv + '</td><td>' + o.uv + '</td></tr>'; }
    res.innerHTML =
      '<p class="ac-title">' + T.title + '</p>' +
      '<table><thead><tr><th></th><th scope="col">' + T.pv + '</th><th scope="col">' + T.uv + '</th></tr></thead><tbody>' +
      row(T.today, d.today) + row(T.yesterday, d.yesterday) + row(T.month, d.month) + row(T.total, d.total) +
      '</tbody></table>' +
      '<div class="ac-bars" aria-hidden="true">' + d.last30.map(function (x) {
        return '<span title="' + x.date + ': ' + x.pv + ' / ' + x.uv + '" style="height:' + Math.round(x.pv / max * 100) + '%"></span>';
      }).join('') + '</div>' +
      '<p class="ac-note">' + T.last30 + ' · ' + T.since + d.since + '</p>' +
      '<div class="ac-buttons"><button type="button" class="ac-close"></button></div>';
    res.querySelector('.ac-close').textContent = T.close;
    res.querySelector('.ac-close').addEventListener('click', function () { dlg.close(); });
    dlg.querySelector('form').hidden = true;
    res.hidden = false;
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('[data-access-counter]');
    if (!a) return;
    e.preventDefault();
    if (!dlg) build();
    dlg.querySelector('form').hidden = false;
    dlg.querySelector('.ac-result').hidden = true;
    dlg.querySelector('.ac-msg').textContent = '';
    if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
    dlg.querySelector('input[name="id"]').focus();
  });
})();
