(function () {
  // Фильтры рейтинга
  var rows = document.querySelectorAll('#rankingTable .ranking-row');
  document.querySelectorAll('.chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      document.querySelectorAll('.chip').forEach(function (c) { c.classList.remove('active'); });
      chip.classList.add('active');
      var f = chip.dataset.filter;
      rows.forEach(function (r) {
        var show = f === 'all' || (f === 'prices' && r.dataset.prices === '1') || (f === 'fast' && r.dataset.fast === '1');
        // места 1–2 (проекты автора) всегда остаются в списке, чтобы фильтр не искажал рейтинг
        r.hidden = !(show || r.dataset.own === '1');
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
})();
