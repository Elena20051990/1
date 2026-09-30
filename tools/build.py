#!/usr/bin/env python3
"""Собирает статический сайт-рейтинг из tools/niche.txt (текст анализа ниши).

Запуск:  python3 tools/build.py
Результат: index.html, prices.html, c/<slug>.html в корне репозитория.
Стили лежат в assets/style.css.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TXT = (ROOT / "tools" / "niche.txt").read_text(encoding="utf-8")
LINES = [html.unescape(l).rstrip() for l in TXT.split("\n")]

SITE = "ВАЛЮРА"
SITE_SUB = "Рейтинг скупок алкоголя"
UPDATED = "30 сентября 2026"
e = html.escape

# ---------------------------------------------------------------- данные
# Короткие значения для таблицы рейтинга (взяты из сводной таблицы анализа).
META = {
    "room-alco.ru":      dict(speed="Около 30 минут", speed_n="предварительная оценка", price="Не публикует", price_n="открытый прайс",
                              nom="Круглосуточная оценка и хранение бутылок", tags=["24/7", "Хранение", "Квиз", "Крипта"]),
    "diamant-alko.ru":   dict(speed="5–10 минут", speed_n="заявленный срок", price="Не публикует", price_n="открытый прайс",
                              nom="Опт и остатки ресторанов, баров, магазинов (от 10 бутылок)", tags=["Опт от 10 бутылок", "Выезд"]),
    "700ml.ru":          dict(speed="До 24 часов", speed_n="ответ по фото", price="21 позиция", price_n="цены «от»",
                              nom="Прозрачность цен", tags=["Выезд до 2 ч", "8:00–1:00", "МО и регионы"]),
    "1buyup.ru":         dict(speed="15–30 минут", speed_n="предварительная оценка", price="Виски, 6 поз.", price_n="рынок и «до»",
                              nom="Гарантия неизменности цены", tags=["Цена по фото", "Курьеры РФ/СНГ"]),
    "reddecanter.ru":    dict(speed="Около 15 минут", speed_n="экспертиза", price="10 позиций", price_n="приблизительные",
                              nom="Редкие и ультрапремиальные бутылки", tags=["Сомелье", "Офис"]),
    "skupka-alkogol.ru": dict(speed="2–15 минут", speed_n="заявлено компанией", price="Коньяк + сегменты", price_n="приблизительные",
                              nom="Коньяк и понятная лестница цен", tags=["Коньяк", "Выезд", "МО и СПб"]),
    "vykup-alko.ru":     dict(speed="15 минут", speed_n="оценка", price="Не публикует", price_n="открытый прайс",
                              nom="Фиксация цены до выезда", tags=["С 2014 года", "Выезд"]),
    "alkoprikup.ru":     dict(speed="2–3 минуты", speed_n="онлайн-оценка", price="Не публикует", price_n="открытый прайс",
                              nom="Быстрая онлайн-оценка, в том числе бюджетные позиции", tags=["Москва и СПб"]),
    "sellmewine.ru":     dict(speed="Онлайн 24/7", speed_n="15 минут по коньяку", price="Не публикует", price_n="открытый прайс",
                              nom="Круглосуточные операторы", tags=["24/7", "Алкоголь СССР"]),
    "skup-ka.ru":        dict(speed="Не указана", speed_n="по договорённости", price="Не публикует", price_n="открытый прайс",
                              nom="Смешанные коллекции целиком", tags=["РФ и СНГ"]),
    "kupimalko.ru":      dict(speed="5 минут", speed_n="контакт по заявке", price="Не публикует", price_n="открытый прайс",
                              nom="Гарантия цены и работа до 23:00", tags=["9:00–23:00"]),
    "cupajclub.ru":      dict(speed="5 минут", speed_n="заявлено", price="Не публикует", price_n="открытый прайс",
                              nom="Принимает и бюджетные позиции", tags=["Выезд"]),
    "probkabar.com":     dict(speed="15 минут", speed_n="заявлено", price="Не публикует", price_n="открытый прайс",
                              nom="Премиальный алкоголь", tags=[]),
    "sellawine.ru":      dict(speed="10–15 минут", speed_n="оценка бутылки", price="Не проверено", price_n="",
                              nom="Заявлена круглосуточная доступность", tags=[]),
    "alcobuyer.ru":      dict(speed="Не указана", speed_n="дистанционная оценка", price="Не публикует", price_n="открытый прайс",
                              nom="Бесплатная оценка по фото", tags=["24/7"]),
    "oldcognac.ru":      dict(speed="Не указана", speed_n="дистанционная оценка", price="Не публикует", price_n="открытый прайс",
                              nom="Коньяк и коллекционный алкоголь", tags=[]),
    "alcovikup.ru":      dict(speed="5 минут", speed_n="заявлено", price="Не публикует", price_n="открытый прайс",
                              nom="Быстрая оценка по фото", tags=[]),
    "prodat-alko.ru":    dict(speed="Не указана", speed_n="предварительный ответ", price="Не публикует", price_n="открытый прайс",
                              nom="Гарантия неизменности цены", tags=["24/7"]),
    "alkolombard.ru":    dict(speed="Выезд до 2 ч", speed_n="после согласования цены", price="Не публикует", price_n="открытый прайс",
                              nom="Выезд в течение 2 часов", tags=["8:00–1:00"]),
    "vikup-alco.ru":     dict(speed="5 минут", speed_n="заявлено", price="Не публикует", price_n="открытый прайс",
                              nom="Санкт-Петербург", tags=["СПб"]),
}

# Группы сайтов, вероятно принадлежащих одному оператору (раздел 7 анализа).
CLUSTERS = [
    ("Кластер 700ml", ["700ml.ru", "alkolombard.ru", "oldcognac.ru"]),
    ("Кластер Red Decanter", ["reddecanter.ru", "skupka-alkogol.ru"]),
    ("Кластер Cupaj Club", ["cupajclub.ru", "alkoprikup.ru"]),
    ("Текстовые клоны", ["room-alco.ru", "skup-alco.ru", "kupimalko.ru"]),
]
OWN = {"room-alco.ru", "diamant-alko.ru"}  # места 1–2 заданы владельцем сайта


def parse_cards():
    start = next(i for i, l in enumerate(LINES) if l.startswith("5. Карточки компаний"))
    end = next(i for i, l in enumerate(LINES) if l.startswith("6. Цены выкупа"))
    head = re.compile(r"^(\d+)\. (.+?) — (\S+)(?: \((.+)\))?$")
    cards, cur, mode = [], None, None
    for l in LINES[start + 1:end]:
        m = head.match(l)
        if m:
            cur = dict(rank=int(m[1]), name=m[2], domain=m[3], note=m[4] or "",
                       contacts="", speed="", prices="", pros=[], cons=[])
            cards.append(cur)
            mode = None
            continue
        if cur is None or not l.strip():
            continue
        if l.startswith("Контакты и режим:"):
            cur["contacts"] = l.split(":", 1)[1].strip()
        elif l.startswith("Скорость оценки:"):
            cur["speed"] = l.split(":", 1)[1].strip()
        elif l.startswith("Цены:"):
            cur["prices"] = l.split(":", 1)[1].strip()
        elif l.strip() == "Плюсы":
            mode = "pros"
        elif l.strip() == "Минусы":
            mode = "cons"
        elif mode:
            cur[mode].append(l.strip())
    return cards


def cells_between(start_marker, end_marker):
    txt = "\n".join(LINES)
    a = txt.index(start_marker)
    b = txt.index(end_marker, a)
    chunk = txt[a:b]
    return [c.strip() for c in re.split(r"\n \| ?|\n ?\| ", chunk)]


def parse_prices():
    txt = "\n".join(LINES)
    a = txt.index("6. Цены выкупа")
    b = txt.index("7. Реальных игроков")
    sec = txt[a:b]
    # основная таблица: 5 столбцов
    i = sec.index("Позиция\n | 700ml (от)")
    j = sec.index("Ром и арманьяк")
    main = [c.strip() for c in re.split(r"\n \| ", sec[i:j]) if c.strip() != ""]
    main = main[5:]
    rows = [main[k:k + 5] for k in range(0, len(main) - 4, 5)]
    # ром и арманьяк: 4 столбца (пары)
    k = sec.index("Позиция\n | Цена, ₽\n | Позиция")
    l = sec.index("Ценовые сегменты")
    rum = [c.strip() for c in re.split(r"\n \| ", sec[k:l]) if c.strip() != ""][4:]
    rum_rows = []
    for q in range(0, len(rum) - 3, 4):
        rum_rows += [(rum[q], rum[q + 1]), (rum[q + 2], rum[q + 3])]
    # сегменты
    m = sec.index("Категория\n | Стоимость")
    n = sec.index("Эти цифры")
    seg = [c.strip() for c in re.split(r"\n \| ", sec[m:n]) if c.strip() != ""][2:]
    seg_rows = [(seg[q], seg[q + 1]) for q in range(0, len(seg) - 1, 2)]
    return rows, rum_rows, seg_rows


CARDS = parse_cards()
assert len(CARDS) == 20, len(CARDS)
PRICES, RUM, SEG = parse_prices()
for c in CARDS:
    c["slug"] = re.sub(r"[^a-z0-9]+", "-", c["domain"].lower()).strip("-")
    c["meta"] = META[c["domain"]]
    c["own"] = c["domain"] in OWN
    c["cluster"] = next((n for n, m in CLUSTERS if c["domain"] in m), None)

# дисконт по таблице 1buyup (раздел 3): рынок → «до»
DISC = [("Macallan 18 Sherry Oak", 70000, 50000), ("Macallan 25", 250000, 180000),
        ("Yamazaki 18", 45000, 32000), ("Highland Park 18", 15000, 10000),
        ("Jameson 18 Limited Reserve", 12000, 8500), ("Balvenie 21 PortWood", 25000, 17000)]


def rub(n):
    return f"{n:,}".replace(",", " ") + " ₽"


# ---------------------------------------------------------------- шаблоны
def head(title, desc, depth=0):
    p = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Open+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}assets/style.css">
</head>
<body>
"""


def header(depth=0):
    p = "../" * depth
    home = p or "./"
    return f"""<header class="header" id="header">
<div class="container header-inner">
<a href="{home}" class="nav-logo" aria-label="{SITE} — главная">{SITE}<span class="nav-logo-sub">{SITE_SUB}</span></a>
<nav class="nav-links" aria-label="Главная навигация">
<a href="{home}#ranking">Рейтинг</a>
<a href="{p}prices.html">Цены выкупа</a>
<a href="{home}#calc">Калькулятор</a>
<a href="{home}#choose">Как выбрать</a>
<a href="{home}#faq">Вопросы</a>
<a href="{home}#method">Методика</a>
</nav>
<div class="header-actions">
<a href="{home}#calc" class="btn btn-primary header-cta">Прикинуть выкуп <span class="arrow">→</span></a>
</div>
</div>
</header>
"""


def footer(depth=0):
    p = "../" * depth
    home = p or "./"
    return f"""<footer class="footer">
<div class="container">
<div class="footer-main">
<div>
<a href="{home}" class="nav-logo">{SITE}<span class="nav-logo-sub">{SITE_SUB}</span></a>
<p class="footer-logo-copy">Сравнение компаний, которые скупают элитный и коллекционный алкоголь в Москве. Данные собраны по публичным сайтам компаний.</p>
</div>
<div><h3 class="footer-title">Разделы</h3><div class="footer-links">
<a href="{home}#ranking">Рейтинг</a><a href="{p}prices.html">Цены выкупа</a><a href="{home}#calc">Калькулятор</a><a href="{home}#faq">Вопросы</a></div></div>
<div><h3 class="footer-title">Информация</h3><div class="footer-links">
<a href="{home}#method">Методика и оговорки</a><a href="{home}#disclosure">Реклама и раскрытие</a></div></div>
</div>
<p class="legal">Реклама. Первые два места в рейтинге занимают проекты владельца сайта (Room Alco и Diamant Alko), места 3–20 расставлены по прозрачности цен и полноте данных. Рейтинг не является независимым. Цены и сроки — заявленные компаниями ориентиры, а не оферта; самозаявления компаний не проверялись. Чрезмерное употребление алкоголя вредит вашему здоровью. Лицам младше 18 лет продажа алкоголя запрещена.</p>
<div class="footer-bottom"><p>© 2026 {SITE}. Информация носит справочный характер.</p><p>Данные актуальны на {UPDATED}</p></div>
</div>
</footer>
<script src="{p}assets/site.js"></script>
</body>
</html>
"""


def badges(c):
    out = []
    if c["own"]:
        out.append('<span class="pill pill-own">Проект автора сайта</span>')
    if c["cluster"]:
        out.append('<span class="pill pill-warn">Возможно, один оператор</span>')
    return out


def row(c):
    m = c["meta"]
    tags = "".join(f'<span class="pill">{e(t)}</span>' for t in m["tags"][:3]) + "".join(badges(c))
    return f"""<a href="c/{c['slug']}.html" class="ranking-row" data-prices="{'1' if m['price'] not in ('Не публикует', 'Не проверено') else '0'}" data-own="{'1' if c['own'] else '0'}" data-fast="{'1' if c['slug'] in FAST else '0'}">
<span class="rank-number">{c['rank']:02d}</span>
<span><span class="company-name">{e(c['name']).upper()}</span><span class="company-site">{e(c['domain'])}</span></span>
<span class="company-nomination">{e(m['nom'])}</span>
<span class="company-metric"><strong>{e(m['speed'])}</strong>{e(m['speed_n'])}</span>
<span class="company-metric"><strong>{e(m['price'])}</strong>{e(m['price_n'])}</span>
<span class="tag-list">{tags}</span>
<span class="row-arrow">→</span>
</a>
"""


# «быстрые» — заявляют оценку до 5 минут включительно
FAST = {"alkoprikup-ru", "kupimalko-ru", "cupajclub-ru", "alcovikup-ru", "vikup-alco-ru", "diamant-alko-ru", "skupka-alkogol-ru"}


MODE_FIX = {"sellmewine.ru": "операторы круглосуточно", "sellawine.ru": "оценка 11:00–24:00; заявлена круглосуточная доступность"}


def mode_of(c):
    if c["domain"] in MODE_FIX:
        return MODE_FIX[c["domain"]]
    m = re.search(r"Режим[^:]*:\s*(.+?)\.?\s*$", c["contacts"])
    return m[1].strip().rstrip(".") if m else "не указан"


def index_page():
    disc_rows = "".join(
        f"<tr><td>{e(n)}</td><td>{rub(mk)}</td><td>{rub(b)}</td><td class='lime'>−{round((1 - b / mk) * 100)}%</td></tr>"
        for n, mk, b in DISC)
    cmp_rows = "\n".join(
        f"<tr><td class='n'>{c['rank']}</td><td><a href='c/{c['slug']}.html'><strong>{e(c['name'])}</strong></a><br><span class='muted'>{e(c['domain'])}</span></td>"
        f"<td>{e(mode_of(c))}</td><td>{e(c['meta']['speed'])}</td><td>{e(c['meta']['price'])}</td></tr>"
        for c in CARDS)
    clusters = "".join(
        f"<tr><td>{e(n)}</td><td>{', '.join(e(d) for d in ds)}</td></tr>" for n, ds in CLUSTERS)
    priced = sum(1 for c in CARDS if c["meta"]["price"] not in ("Не публикует", "Не проверено"))
    body = head(f"Рейтинг скупок элитного алкоголя в Москве — {SITE}",
                "Сравнение 20 компаний по скупке элитного и коллекционного алкоголя в Москве: скорость оценки, публичные цены, условия выезда, плюсы и минусы.") + header() + f"""
<main id="top">
<section class="hero">
<div class="container hero-grid">
<div class="hero-content">
<span class="eyebrow">Москва · обновлено {UPDATED}</span>
<h1 class="hero-title">Кому продать<br><span class="lime">элитный алкоголь?</span></h1>
<p class="hero-copy">Рейтинг 20 скупок коллекционного виски, коньяка, вина и шампанского: кто называет цены открыто, как быстро оценивает по фото и что обещает клиенту.</p>
<div class="hero-buttons">
<a href="#ranking" class="btn btn-primary">Смотреть рейтинг <span class="arrow">→</span></a>
<a href="prices.html" class="btn btn-outline">Цены выкупа</a>
</div>
<div class="hero-stats">
<div class="hero-stat"><span class="stat-value">20</span><span class="stat-label">Компаний<br>в рейтинге</span></div>
<div class="hero-stat"><span class="stat-value">{priced}</span><span class="stat-label">Публикуют<br>цены</span></div>
<div class="hero-stat"><span class="stat-value">≈ 28–33%</span><span class="stat-label">Типичный дисконт<br>к рынку</span></div>
</div>
</div>
<div class="market-card-wrap">
<aside class="market-card" aria-label="Сколько платят скупки относительно рынка">
<div class="market-topline"><span><span class="market-dot"></span>Данные 1buyup.ru</span><span class="market-live">Ориентир</span></div>
<span class="market-label">Платят от рыночной цены</span>
<div class="market-price">67–72%</div>
<div class="market-change"><strong>−28…33%</strong><span>дисконт скупки</span></div>
<p class="market-note">По таблице 1buyup на 6 позиций виски. Обещания «до 90%» и «до 100%» у других компаний — маркетинг.</p>
<p class="market-disclaimer">Не является гарантией выкупа.<br>Итог зависит от состояния бутылки.</p>
</aside>
</div>
</div>
</section>

<section class="section ranking-section" id="ranking">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Рейтинг</span><h2 class="section-title">Скупки алкоголя<br>в Москве</h2></div>
<p class="section-copy">Места 1–2 занимают проекты автора сайта, места 3–20 расставлены по прозрачности цен и полноте данных. Подробности — в разделе «Методика».</p>
</div>
<div class="filters" role="group" aria-label="Фильтры">
<button class="chip active" data-filter="all">Все 20</button>
<button class="chip" data-filter="prices">Публикуют цены</button>
<button class="chip" data-filter="fast">Оценка до 5 минут</button>
</div>
<div class="ranking-table" id="rankingTable">
<div class="ranking-header"><span>Место</span><span>Компания</span><span>Номинация</span><span>Оценка по фото</span><span>Цены</span><span>Особенности</span><span></span></div>
{"".join(row(c) for c in CARDS)}
</div>
<p class="note">Сроки оценки и режимы работы — заявления компаний. Слова «не публикует» означают, что цен нет на проверенных страницах сайта.</p>
</div>
</section>

<section class="section" id="compare">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Сводная таблица</span><h2 class="section-title">Сравнение<br>условий</h2></div>
<p class="section-copy">Режим работы, заявленная скорость предварительной оценки и публичность цен.</p>
</div>
<div class="table-wrap"><table class="data">
<thead><tr><th>№</th><th>Компания</th><th>Режим</th><th>Скорость оценки</th><th>Цены</th></tr></thead>
<tbody>
{cmp_rows}
</tbody></table></div>
</div>
</section>

<section class="section ranking-section" id="calc">
<div class="container">
<div class="calculator-shell">
<div class="calculator-form">
<span class="eyebrow">Калькулятор</span>
<h2 class="calculator-title">Сколько предложит скупка?</h2>
<p class="calculator-copy">Введите рыночную цену бутылки (аукцион, импортёр). Скупки обычно платят 67–72% от неё — так получается по таблице 1buyup. Это грубый ориентир, а не оценка конкретной бутылки.</p>
<form id="calcForm" class="form-grid">
<label class="full lbl">Рыночная цена бутылки, ₽<input class="field" id="market" type="number" min="1" step="100" inputmode="numeric" placeholder="например, 45000" required></label>
<button class="btn btn-primary calculator-submit full" type="submit">Посчитать <span class="arrow">→</span></button>
</form>
</div>
<aside class="calculator-result" aria-live="polite">
<span class="result-label">Ориентир выкупа</span>
<div class="result-price" id="resultPrice">—</div>
<p class="result-note" id="resultNote">Введите цену и нажмите «Посчитать».</p>
<div class="range"></div>
<span class="result-disclaimer">Не является ценой сделки. Подлинность, этикетка, капсула, пробка, уровень жидкости, коробка и спрос меняют итог.</span>
</aside>
</div>
<h3 class="sub">Как считается дисконт: таблица 1buyup, виски</h3>
<div class="table-wrap"><table class="data">
<thead><tr><th>Позиция</th><th>Рынок</th><th>Готовы купить до</th><th>Дисконт</th></tr></thead>
<tbody>{disc_rows}</tbody></table></div>
<p class="note">Источник: 1buyup.ru, страница «Виски», цифры ориентировочные. По таблице компания платит не больше 67–72% рынка.</p>
</div>
</section>

<section class="section" id="choose">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Как выбрать</span><h2 class="section-title">Пять вопросов<br>перед сделкой</h2></div>
<p class="section-copy">Ниша устроена однотипно: фото, предварительная цена, встреча и расчёт. Различия — в деталях.</p>
</div>
<div class="steps-grid">
<article class="step"><div class="step-number">01</div><h3 class="step-title">Цена изменится?</h3><p>Главная боль клиента — цена меняется при встрече. 1buyup, TotalStok, Kupimalko и VykupAlko прямо обещают, что согласованная по фото цена не изменится. Спросите это письменно.</p></article>
<article class="step"><div class="step-number">02</div><h3 class="step-title">«От» или «до»?</h3><p>700ml пишет «от» (нижняя граница), 1buyup — «до» (потолок). По Yamazaki 18 разброс 2,5 раза. Напрямую такие цифры сравнивать нельзя.</p></article>
<article class="step"><div class="step-number">03</div><h3 class="step-title">Есть ли открытые цены?</h3><p>Конкретные цены публикуют четыре компании: 700ml, 1buyup, Red Decanter и SKUPKA-ALKOGOL. Остальные называют цену только после фото.</p></article>
<article class="step"><div class="step-number">04</div><h3 class="step-title">Кто на самом деле?</h3><p>Независимых операторов меньше, чем сайтов: часть сайтов, вероятно, принадлежит одной компании (см. «Методику»). Запрос в «разные» скупки одной группы даст то же предложение.</p></article>
<article class="step"><div class="step-number">05</div><h3 class="step-title">Что с обещаниями?</h3><p>«До 90%» и «до 100%» рыночной цены — маркетинг: реальный дисконт около 28–33%. Проверяйте цифры «10+ лет», «5000 сделок» и «97% выкупа» — это самозаявления.</p></article>
</div>
<h3 class="sub">Как подготовить бутылку к оценке</h3>
<div class="trust-grid">
<article class="trust-item"><div class="trust-symbol">1</div><h3 class="trust-title">Фото этикеток</h3><p>Сфотографируйте лицевую и обратную этикетки.</p></article>
<article class="trust-item"><div class="trust-symbol">2</div><h3 class="trust-title">Капсула и пробка</h3><p>Покажите горлышко, капсулу, пробку и акцизную марку.</p></article>
<article class="trust-item"><div class="trust-symbol">3</div><h3 class="trust-title">Уровень жидкости</h3><p>Снимите бутылку на просвет — уровень влияет на цену.</p></article>
<article class="trust-item"><div class="trust-symbol">4</div><h3 class="trust-title">Общий вид и упаковка</h3><p>Коробка или тубус повышают цену: без коробки до −30% (данные Red Decanter).</p></article>
</div>
</div>
</section>

<section class="section ranking-section" id="faq">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Вопросы</span><h2 class="section-title">Частые<br>вопросы</h2></div>
<p class="section-copy">Коротко о том, что покупают, что не берут и от чего зависит цена.</p>
</div>
<div class="faq">
<details><summary>Что покупают скупки элитного алкоголя?</summary><p>Возрастной виски (Macallan, Yamazaki, Balvenie, Highland Park), коньяк (Hennessy XO/Paradis/Richard, Louis XIII, Martell Cordon Bleu), вина (Petrus, Lafite, Margaux, Masseto, Sassicaia), шампанское (Dom Pérignon, Cristal, Krug, Salon), ром и арманьяк, алкоголь СССР с коллекционной ценностью. Упаковка, тубус и декантер часто дают надбавку или покупаются отдельно.</p></details>
<details><summary>Что не берут?</summary><p>Открытые бутылки, повреждённую пробку и капсулу, подделки, массовый сегмент. Исключение — Cupaj Club и Alko Prikup: они заявляют, что рассматривают и бюджетные позиции.</p></details>
<details><summary>Как формируется цена выкупа?</summary><p>Ориентир — мировые аукционные цены и цены импортёров, а не розница магазина. Поэтому предложение ниже магазинной цены. На итог влияют бренд, год и тираж, уровень жидкости, состояние этикетки, капсулы и пробки, наличие коробки, формат бутылки, регион (в Москве платят больше) и объём партии.</p></details>
<details><summary>Почему цена меняется при встрече?</summary><p>Предварительная оценка по фото не учитывает состояние бутылки вживую. Компании, которые гарантируют неизменность цены, оговаривают «если нет новых обстоятельств». Уточняйте условие до выезда.</p></details>
<details><summary>Как быстро оценивают бутылку?</summary><p>Заявленные сроки — от 2 до 15 минут, у Room Alco около 30 минут, у 700ml до 24 часов. Скорость оценки не выделяет ни одного игрока.</p></details>
<details><summary>Можно ли продать бутылку без коробки или акцизной марки?</summary><p>Часто можно: например, 1buyup берёт бутылки без коробки и без акцизной марки, а также алкоголь СССР. Но без коробки цена может быть ниже до 30% (по данным Red Decanter).</p></details>
</div>
</div>
</section>

<section class="section" id="method">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Методика</span><h2 class="section-title">Как составлен<br>рейтинг</h2></div>
<p class="section-copy">Что изучено, что не проверено и где возможны ошибки.</p>
</div>
<div class="prose" id="disclosure">
<p><strong>Реклама и раскрытие.</strong> Места 1 и 2 занимают Room Alco и Diamant Alko — проекты владельца этого сайта, места закреплены заранее. Рейтинг не является независимым. Места 3–20 расставлены по прозрачности цен и полноте данных.</p>
<p><strong>Источники.</strong> Изучены главные страницы сайтов и, где это удалось, страницы категорий. Если сайт закрыт для автоматического доступа, использованы фрагменты поисковой выдачи (это отмечено в карточке). Данные собраны 30 сентября 2026 г.</p>
<p><strong>Что значит «не публикует».</strong> Цен нет на проверенных страницах. На неизученных подстраницах они могут быть.</p>
<p><strong>Цены.</strong> Это заявленные компаниями ориентиры, а не оферта. Итог зависит от подлинности, этикетки, капсулы и пробки, уровня жидкости, упаковки, года, объёма и спроса.</p>
<p><strong>Оценки.</strong> Числовые рейтинги не выставлялись: независимого источника нет, рейтинги на Яндекс Картах и 2ГИС не собирались. Показатели вида «10+ лет», «5000 сделок», «97% выкупа» — самозаявления компаний и не проверялись.</p>
<p><strong>Не проверено.</strong> Skupka-Star, Vine-Co (vine-co.ru), VinomerPro, Skupix, СпецВыкуп, Collectors Community, «VIP Выкуп», Vikup-Vina, e-skupka.ru, Alko-vikup, «Скупка PRO»; отзывы на Яндекс Картах и 2ГИС; цены на подстраницах категорий.</p>
<h3 class="sub">Возможно, один оператор</h3>
<p>По шаблонам, текстам и контактам видны группы сайтов, которые, вероятно, принадлежат одному оператору. Это признаки, а не доказательство.</p>
<div class="table-wrap"><table class="data"><thead><tr><th>Группа</th><th>Сайты</th></tr></thead><tbody>{clusters}</tbody></table></div>
</div>
</div>
</section>

<section class="final-cta">
<div class="container">
<span class="eyebrow">Начните с фото</span>
<h2 class="final-title">Нужна оценка<br>бутылки?</h2>
<p class="final-copy">Сделайте фото этикеток, капсулы и уровня жидкости и отправьте в мессенджер выбранной компании.</p>
<a href="#ranking" class="btn btn-primary">К рейтингу <span class="arrow">→</span></a>
<p class="final-note">Предварительная оценка не является окончательной ценой сделки.</p>
</div>
</section>
</main>
""" + footer()
    return body


def company_prices(c):
    col = {"700ml.ru": 1, "1buyup.ru": 2, "reddecanter.ru": 3, "skupka-alkogol.ru": 4}.get(c["domain"])
    if col is None:
        return ""
    rows = [(r[0], r[col]) for r in PRICES if r[col] not in ("—", "")]
    extra = ""
    if c["domain"] == "700ml.ru":
        rows += RUM
    if c["domain"] == "skupka-alkogol.ru":
        rows += SEG
    label = {1: "от", 2: "до (в скобках — рынок)", 3: "приблизительно", 4: "приблизительно"}[col]
    tr = "".join(f"<tr><td>{e(a)}</td><td>{e(b if b.endswith('₽') or 'от' in b or 'свыше' in b else b + ' ₽')}</td></tr>" for a, b in rows)
    return f"""<h2 class="sub">Опубликованные цены ({label})</h2>
<div class="table-wrap"><table class="data"><thead><tr><th>Позиция</th><th>Цена</th></tr></thead><tbody>{tr}</tbody></table></div>
<p class="note">Заявленные компанией ориентиры, не оферта.</p>"""


def company_page(c, i):
    prev_c, next_c = CARDS[i - 1] if i else None, CARDS[i + 1] if i + 1 < len(CARDS) else None
    pros = "".join(f"<li>{e(x)}</li>" for x in c["pros"])
    cons = "".join(f"<li>{e(x)}</li>" for x in c["cons"])
    note = f'<p class="muted">{e(c["note"])}</p>' if c["note"] else ""
    warn = ""
    if c["cluster"]:
        mates = [d for n, m in CLUSTERS if c["domain"] in m for d in m if d != c["domain"]]
        warn = f'<p class="callout">Возможно, один оператор: {e(c["cluster"])} (сайты: {", ".join(e(d) for d in mates)}). Это признаки по шаблонам и контактам, а не доказательство.</p>'
    own = ('<p class="callout">Проект владельца сайта. Место в рейтинге закреплено заранее. Реклама.</p>'
           if c["own"] else "")
    rel = "sponsored noopener" if c["own"] else "nofollow noopener"
    nav = ""
    if prev_c:
        nav += f'<a href="{prev_c["slug"]}.html" class="btn btn-outline">← {e(prev_c["name"])}</a>'
    if next_c:
        nav += f'<a href="{next_c["slug"]}.html" class="btn btn-outline">{e(next_c["name"])} →</a>'
    return head(f"{c['name']} — скупка алкоголя: отзывы, цены, условия | {SITE}",
                f"{c['name']} ({c['domain']}): режим работы, скорость оценки, цены выкупа, плюсы и минусы. Данные на {UPDATED}.", 1) + header(1) + f"""
<main class="page">
<div class="container narrow">
<nav class="crumbs"><a href="../">Рейтинг</a> / {e(c['name'])}</nav>
<span class="eyebrow">Место {c['rank']} из 20</span>
<h1 class="page-title">{e(c['name'])}</h1>
<p><a class="text-link" href="https://{e(c['domain'])}" rel="{rel}" target="_blank">{e(c['domain'])} <span class="arrow">↗</span></a></p>
{note}{own}{warn}
<dl class="facts">
<div><dt>Контакты и режим</dt><dd>{e(c['contacts'])}</dd></div>
<div><dt>Скорость оценки</dt><dd>{e(c['speed'])}</dd></div>
<div><dt>Цены</dt><dd>{e(c['prices'])}</dd></div>
</dl>
<div class="proscons">
<div><h2 class="sub">Плюсы</h2><ul class="list plus">{pros}</ul></div>
<div><h2 class="sub">Минусы</h2><ul class="list minus">{cons}</ul></div>
</div>
{company_prices(c)}
<p class="note">Данные собраны {UPDATED} по публичным сайтам компании. Самозаявления не проверялись. Цены и условия уточняйте у компании.</p>
<div class="pager">{nav}</div>
</div>
</main>
""" + footer(1)


def prices_page():
    def td(v):
        return f"<td class='{'dash' if v == '—' else ''}'>{e(v)}</td>"
    main = "".join("<tr>" + f"<td>{e(r[0])}</td>" + "".join(td(v) for v in r[1:]) + "</tr>" for r in PRICES)
    rum = "".join(f"<tr><td>{e(a)}</td><td>{e(b)} ₽</td></tr>" for a, b in RUM)
    seg = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td></tr>" for a, b in SEG)
    return head(f"Цены выкупа элитного алкоголя в Москве — {SITE}",
                "Сводка цен выкупа виски, коньяка, шампанского и вина по данным 700ml, 1buyup, Red Decanter и SKUPKA-ALKOGOL.") + header() + f"""
<main class="page">
<div class="container">
<span class="eyebrow">Сводка по источникам</span>
<h1 class="page-title">Цены выкупа</h1>
<p class="lead">Все суммы в рублях. «От» — нижняя граница (700ml), «до» — потолок (1buyup, в скобках рыночная цена), «прибл.» — приблизительная цена на сайте. Прочерк — компания эту позицию не публикует. Сравнивать столбцы напрямую нельзя.</p>
<input class="field search" id="priceSearch" type="search" placeholder="Поиск по позиции, например Macallan" aria-label="Поиск по позиции">
<div class="table-wrap"><table class="data" id="priceTable">
<thead><tr><th>Позиция</th><th>700ml (от)</th><th>1buyup (до)</th><th>Red Decanter</th><th>SKUPKA-ALKOGOL</th></tr></thead>
<tbody>{main}</tbody></table></div>
<div class="two-col">
<div><h2 class="sub">Ром и арманьяк (только 700ml, «от»)</h2><div class="table-wrap"><table class="data"><thead><tr><th>Позиция</th><th>Цена</th></tr></thead><tbody>{rum}</tbody></table></div></div>
<div><h2 class="sub">Ценовые сегменты (SKUPKA-ALKOGOL, ориентировочно)</h2><div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Стоимость</th></tr></thead><tbody>{seg}</tbody></table></div></div>
</div>
<p class="note">Эти цифры — не рыночная цена и не гарантия выплаты. Один и тот же бренд может стоить по-разному из-за винтажа, объёма, уровня жидкости, состояния этикетки и комплектности. Например, Yamazaki 18: потолок 32 000 ₽ у 1buyup против «от 80 000 ₽» у 700ml — проверяйте цифру перед сделкой. Данные на {UPDATED}.</p>
</div>
</main>
""" + footer()


def main():
    (ROOT / "index.html").write_text(index_page(), encoding="utf-8")
    (ROOT / "prices.html").write_text(prices_page(), encoding="utf-8")
    (ROOT / "c").mkdir(exist_ok=True)
    for i, c in enumerate(CARDS):
        (ROOT / "c" / f"{c['slug']}.html").write_text(company_page(c, i), encoding="utf-8")
    print("ok:", len(CARDS), "компаний,", len(PRICES), "строк цен,", len(RUM), "ром/арманьяк,", len(SEG), "сегментов")


if __name__ == "__main__":
    main()
