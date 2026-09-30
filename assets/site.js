(function () {
  // Фильтры рейтинга
  var rows = document.querySelectorAll('#rankingTable .company-card');
  document.querySelectorAll('.chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      document.querySelectorAll('.chip').forEach(function (c) { c.classList.remove('active'); });
      chip.classList.add('active');
      var f = chip.dataset.filter;
      rows.forEach(function (r) {
        var show = f === 'all' || (f === 'prices' && r.dataset.prices === '1') || (f === 'fast' && r.dataset.fast === '1');
        r.hidden = !show;
      });
    });
  });
  // Калькулятор: 67–72% рынка (по таблице 1buyup)
  var form = document.getElementById('calcForm');
  if (form) {
    var fmt = function (n) { return Math.round(n / 100) * 100; };
    var nf = new Intl.NumberFormat('ru-RU');
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var v = parseFloat(document.getElementById('market').value);
      if (!(v > 0)) return;
      document.getElementById('resultPrice').textContent = nf.format(fmt(v * 0.67)) + '–' + nf.format(fmt(v * 0.72)) + ' ₽';
      document.getElementById('resultNote').textContent = 'Это 67–72% от рыночной цены ' + nf.format(v) + ' ₽. Реальное предложение зависит от состояния бутылки.';
    });
  }
  // Поиск по ценам
  var s = document.getElementById('priceSearch');
  if (s) {
    s.addEventListener('input', function () {
      var q = s.value.trim().toLowerCase();
      document.querySelectorAll('#priceTable tbody tr').forEach(function (tr) {
        tr.hidden = q && tr.cells[0].textContent.toLowerCase().indexOf(q) < 0;
      });
    });
  }
  // Отзыв: диалог
  var dlg = document.getElementById('reviewDialog');
  if (dlg) {
    var form = document.getElementById('reviewForm'), msg = document.getElementById('reviewMsg'), who = '';
    document.addEventListener('click', function (ev) {
      var b = ev.target.closest('.btn-review');
      if (!b) return;
      who = b.dataset.company;
      document.getElementById('reviewCompany').textContent = who;
      msg.textContent = '';
      if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
    });
    document.getElementById('reviewCancel').addEventListener('click', function () { dlg.close(); });
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var ep = form.dataset.endpoint;
      if (!ep) { msg.textContent = 'Приём отзывов ещё не подключён к серверу — отзыв не отправлен.'; return; }
      var data = Object.fromEntries(new FormData(form)); data.company = who;
      fetch(ep, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
        .then(function (r) { if (!r.ok) throw 0; msg.textContent = 'Спасибо! Отзыв отправлен.'; form.reset(); })
        .catch(function () { msg.textContent = 'Не удалось отправить отзыв. Попробуйте позже.'; });
    });
  }
  // Согласие на cookie: после нажатия плашка скрывается и больше не показывается
  var bar = document.getElementById('cookieBar');
  if (bar) {
    var accepted = false;
    try { accepted = localStorage.getItem('cookie_consent') === '1'; } catch (e) {}
    if (!accepted) accepted = /(?:^|; )cookie_consent=1/.test(document.cookie);
    if (!accepted) bar.hidden = false;
    document.getElementById('cookieOk').addEventListener('click', function () {
      try { localStorage.setItem('cookie_consent', '1'); } catch (e) {}
      document.cookie = 'cookie_consent=1; max-age=31536000; path=/; SameSite=Lax';
      bar.hidden = true;
    });
  }
})();
