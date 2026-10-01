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

# ---- Настройки, которые нужно заполнить перед запуском -------------------------------------------
SITE_URL = "https://valura.example"   # адрес сайта без слеша в конце (нужен для canonical, sitemap, robots, og)
OPERATOR = dict(                      # оператор персональных данных (подставляется в политики и на страницу «Для компаний»)
    name="",      # ФИО или название организации/ИП
    inn="",       # ИНН (и ОГРН/ОГРНИП, если есть)
    address="",   # адрес для обращений
    email="",     # e-mail для обращений
)
CLAIM_DAYS = 10                       # срок рассмотрения обращений организаций, рабочих дней (подтвердите, что успеваете)
REVIEW_ENDPOINT = ""                  # куда отправлять отзывы читателей (JSON, POST); пусто — форма сообщает, что не подключена
CLAIM_ENDPOINT = ""                   # куда отправлять обращения организаций (JSON, POST)
GOOGLE_VERIFY = ""                    # содержимое meta google-site-verification (Search Console)
YANDEX_VERIFY = ""                    # содержимое meta yandex-verification (Яндекс Вебмастер)
BUILD_DATE = "2026-10-01"             # дата для sitemap (lastmod)
POLICY_DATE = "1 октября 2026 г."
# --------------------------------------------------------------------------------------------------

SITE = "ВАЛЮРА"
SITE_SUB = "Скупка алкоголя · рейтинг"
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
def ph(key, label):
    """Реквизит оператора или заметная заглушка, пока он не заполнен."""
    v = OPERATOR.get(key, "")
    return e(v) if v else f'<span class="ph">[укажите {label}]</span>'


def jsonld(*objs):
    import json
    return "\n".join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False).replace("</", "<\\/") + "</script>" for o in objs if o)


def breadcrumbs(*items):
    """items — [(название, путь)] от главной; путь относительно корня сайта."""
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": f"{SITE_URL}/{pth}"} for i, (n, pth) in enumerate(items, 1)]}


def key_facts(rows, topic=None):
    """Блок «Коротко»: факты из данных в виде короткого списка (удобно людям и ИИ-краулерам)."""
    priced = [c["name"] for c in CARDS if c["meta"]["price"] not in ("Не публикует", "Не проверено")]
    top = max(CARDS, key=lambda c: scores(c)[1])
    fast = [c for c in CARDS if SCORE_INPUT[c["domain"]]["speed_min"] is not None]
    quick = min(fast, key=lambda c: SCORE_INPUT[c["domain"]]["speed_min"])
    slow = max(fast, key=lambda c: SCORE_INPUT[c["domain"]]["speed_min"])
    items = [f"В рейтинге {len(CARDS)} компаний; открытые цены публикуют {len(priced)}: {', '.join(priced)}."]
    if topic == "champagne":
        n = [x for r in CHAMP_ROWS for col in (1, 3) for x in _nums(r[col])]
        items.append(f"Цены на шампанское публикуют только 700ml и Red Decanter: от {fmt_rub(min(n))} до {fmt_rub(max(n))} ₽ за бутылку по их прайсам (цены «от» и приблизительные).")
    elif topic == "elite":
        items.append("Для дорогих и редких бутылок профильны Red Decanter (до 5 000 000 ₽ в прайсе), 700ml (до 200 000 ₽, Petrus), SKUPKA-ALKOGOL (сегменты до «свыше 100 000 ₽»).")
    items.append("Типичный уровень выкупа — 67–72% рыночной цены бутылки по опубликованным таблицам скупок; обещания «до 90%» и «до 100%» — рекламные заявления.")
    items.append(f"Заявленный срок оценки по фото: самый быстрый — {quick['meta']['speed'].lower()} ({quick['name']}), самый медленный — {slow['meta']['speed'].lower()} ({slow['name']}).")
    items.append(f"Высшая оценка редакции — {scores(top)[1]:g} из 5 ({top['name']}); оценка считается по трём параметрам, правила — в методике.")
    items.append("Часть сайтов, вероятно, принадлежит одному оператору: 700ml, Alko Lombard и oldcognac; Red Decanter и SKUPKA-ALKOGOL; Cupaj Club и Alko Prikup.")
    li = "".join(f"<li>{e(x)}</li>" for x in items)
    return f"""<section class="section keyfacts" id="summary-short"><div class="container narrow"><h2 class="sub" style="margin-top:0">Коротко</h2><ul class="goals">{li}</ul></div></section>
"""


def itemlist(cards):
    return {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": c["name"], "url": f"{SITE_URL}/c/{c['slug']}.html"} for i, c in enumerate(cards, 1)]}


def faq_ld():
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}


def review_ld(c):
    org = {"@type": "Organization", "name": c["name"], "url": f"https://{c['domain']}"}
    phone, _, addr, _ = FACTS[c["domain"]]
    if phone:
        m = re.search(r"(?:\+7|8)\s*\(\d{3}\)\s*[\d\-]+", phone)
        if m:
            org["telephone"] = m.group(0)
    if addr != ND:
        org["address"] = {"@type": "PostalAddress", "streetAddress": addr}
    r = REVIEWS[c["domain"]]
    return {"@context": "https://schema.org", "@type": "Review", "itemReviewed": org,
            "author": {"@type": "Organization", "name": SITE},
            "reviewRating": {"@type": "Rating", "ratingValue": scores(c)[1], "bestRating": 5, "worstRating": 1},
            "name": f"{c['name']}: оценка редакции", "reviewBody": f"{r['lead']} {r['verdict']}", "inLanguage": "ru"}


def head(title, desc, depth=0, path="", ld=None):
    p = "../" * depth
    url = f"{SITE_URL}/{path}"
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "url": SITE_URL + "/", "inLanguage": "ru"}
    org = {"@context": "https://schema.org", "@type": "Organization", "name": OPERATOR.get("name") or SITE, "url": SITE_URL + "/", "logo": f"{SITE_URL}/assets/og.png"}
    if OPERATOR.get("email"):
        org["email"] = OPERATOR["email"]
        org["contactPoint"] = {"@type": "ContactPoint", "contactType": "customer support", "email": OPERATOR["email"], "availableLanguage": "ru"}
    if OPERATOR.get("address"):
        org["address"] = OPERATOR["address"]
    page_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": url, "description": desc, "inLanguage": "ru",
               "dateModified": BUILD_DATE, "isPartOf": {"@type": "WebSite", "name": SITE, "url": SITE_URL + "/"}, "publisher": {"@type": "Organization", "name": OPERATOR.get("name") or SITE}}
    verify = (f'<meta name="google-site-verification" content="{e(GOOGLE_VERIFY)}">\n' if GOOGLE_VERIFY else "") + (f'<meta name="yandex-verification" content="{e(YANDEX_VERIFY)}">\n' if YANDEX_VERIFY else "")
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#431f2a">
<link rel="canonical" href="{url}">
{verify}<link rel="alternate" type="application/json" href="{SITE_URL}/data/companies.json" title="Данные рейтинга (JSON)">
<link rel="icon" href="{p}assets/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE_URL}/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{SITE_URL}/assets/og.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Open+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}assets/style.css">
{jsonld(site_ld, org, page_ld, *(ld or []))}
</head>
<body>
"""


# Меню шапки: (подпись, ссылка). Ссылка на якорь главной начинается с «#», остальные — файлы в корне.
NAV = [
    ("Где продать", "#ranking"),
    ("Элитный алкоголь", "gde-prodat-elitnyy-alkogol.html"),
    ("Шампанское", "gde-prodat-elitnoe-shampanskoe.html"),
    ("Цены", "prices.html"),
    ("Методика", "metodika.html"),
    ("О рейтинге", "o-reitinge.html"),
]


def header(depth=0):
    p = "../" * depth
    home = p or "./"
    links = "\n".join(f'<a href="{(home if h.startswith("#") else p)}{h}">{e(l)}</a>' for l, h in NAV)
    return f"""<header class="header" id="header">
<div class="container header-inner">
<a href="{home}" class="nav-logo" aria-label="{SITE} — главная">{SITE}<span class="nav-logo-sub">{SITE_SUB}</span></a>
<nav class="nav-links" id="navLinks" aria-label="Главная навигация">
{links}
</nav>
<div class="header-actions">
<a href="{home}#calc" class="btn btn-primary header-cta">Оценить алкоголь <span class="arrow">→</span></a>
<button class="menu-btn" id="menuBtn" type="button" aria-label="Меню" aria-expanded="false" aria-controls="navLinks">☰</button>
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
<p class="footer-logo-copy">Где продать алкоголь в Москве: рейтинг скупок коньяка, виски, вина и шампанского.</p>
</div>
<div><h3 class="footer-title">Разделы</h3><div class="footer-links">
<a href="{home}#ranking">Рейтинг скупок</a><a href="{p}{TOPICS[0]["file"]}">Элитный алкоголь</a><a href="{p}{TOPICS[1]["file"]}">Элитное шампанское</a><a href="{p}prices.html">Цены выкупа</a><a href="{home}#calc">Калькулятор</a><a href="{home}#faq">Вопросы</a></div></div>
<div><h3 class="footer-title">Информация</h3><div class="footer-links">
<a href="{p}metodika.html">Методика</a><a href="{p}o-reitinge.html">О рейтинге</a><a href="{p}dlya-kompanii.html">Для компаний</a><a href="{p}kontakty.html">Контакты</a><a href="{p}politika-konfidencialnosti.html">Политика конфиденциальности</a><a href="{p}politika-cookie.html">Политика cookie</a></div></div>
</div>
<p class="legal">Независимый рейтинг: составлен по открытым данным из разных источников, компании отобраны редакцией сайта. Сайт не оказывает и не продаёт услуги. Вся информация носит исключительно информационный характер и может быть устаревшей. Точную информацию уточняйте на сайтах компаний. Цены и сроки — заявления компаний, не оферта. Продажа алкоголя лицам младше 18 лет запрещена.</p>
<div class="footer-bottom"><p>© 2026 {SITE}. Информация носит справочный характер.</p><p>Данные актуальны на {UPDATED}</p></div>
</div>
</footer>
{review_dialog(p)}
<div class="cookie-bar" id="cookieBar" role="dialog" aria-label="Согласие на использование cookie" hidden>
<p>Мы используем файлы cookie, чтобы сайт работал корректно и был удобнее. Продолжая пользоваться сайтом, вы соглашаетесь на их использование. <a href="{p}politika-cookie.html">Подробнее</a></p>
<button class="btn btn-primary" type="button" id="cookieOk">Согласен</button>
</div>
<script src="{p}assets/site.js"></script>
</body>
</html>
"""


def badges(c):
    out = []
    if c["cluster"]:
        out.append('<span class="pill pill-warn">Возможно, один оператор</span>')
    return out


def row(c, m=None, rank=None):
    m = m or c["meta"]
    rank = rank or c["rank"]
    tags = "".join(f'<span class="pill">{e(t)}</span>' for t in m["tags"][:3]) + "".join(badges(c))
    return f"""<a href="{PREFIX}c/{c['slug']}.html" class="ranking-row" data-prices="{'1' if m['price'] not in ('Не публикует', 'Не проверено') else '0'}" data-own="{'1' if c['own'] else '0'}" data-fast="{'1' if c['slug'] in FAST else '0'}">
<span class="rank-number">{rank:02d}</span>
<span><span class="company-name">{e(c['name']).upper()}</span><span class="company-site">{e(c['domain'])}</span></span>
<span class="company-nomination">{e(m['nom'])}</span>
<span class="company-metric"><strong>{e(m['speed'])}</strong>{e(m['speed_n'])}</span>
<span class="company-metric"><strong>{e(m['price'])}</strong>{e(m['price_n'])}</span>
<span class="tag-list">{tags}</span>
<span class="row-arrow">→</span>
</a>
"""


PREFIX = ""


# «быстрые» — заявляют оценку до 5 минут включительно
FAST = {"alkoprikup-ru", "kupimalko-ru", "cupajclub-ru", "alcovikup-ru", "vikup-alco-ru", "diamant-alko-ru", "skupka-alkogol-ru"}


MODE_FIX = {"sellmewine.ru": "операторы круглосуточно", "sellawine.ru": "оценка 11:00–24:00; заявлена круглосуточная доступность"}


def mode_of(c):
    if c["domain"] in MODE_FIX:
        return MODE_FIX[c["domain"]]
    m = re.search(r"Режим[^:]*:\s*(.+?)\.?\s*$", c["contacts"])
    return m[1].strip().rstrip(".") if m else "не указан"


FAQ = [
 [
  "Что покупают скупки элитного алкоголя?",
  "Возрастной виски (Macallan, Yamazaki, Balvenie, Highland Park), коньяк (Hennessy XO/Paradis/Richard, Louis XIII, Martell Cordon Bleu), вина (Petrus, Lafite, Margaux, Masseto, Sassicaia), шампанское (Dom Pérignon, Cristal, Krug, Salon), ром и арманьяк, алкоголь СССР с коллекционной ценностью. Упаковка, тубус и декантер часто дают надбавку или покупаются отдельно."
 ],
 [
  "Что не берут?",
  "Открытые бутылки, повреждённую пробку и капсулу, подделки, массовый сегмент. Исключение — Cupaj Club и Alko Prikup: они заявляют, что рассматривают и бюджетные позиции."
 ],
 [
  "Как формируется цена выкупа?",
  "Ориентир — мировые аукционные цены и цены импортёров, а не розница магазина. Поэтому предложение ниже магазинной цены. На итог влияют бренд, год и тираж, уровень жидкости, состояние этикетки, капсулы и пробки, наличие коробки, формат бутылки, регион (в Москве платят больше) и объём партии."
 ],
 [
  "Почему цена меняется при встрече?",
  "Предварительная оценка по фото не учитывает состояние бутылки вживую. Компании, которые гарантируют неизменность цены, оговаривают «если нет новых обстоятельств». Уточняйте условие до выезда."
 ],
 [
  "Как быстро оценивают бутылку?",
  "Заявленные сроки — от 2 до 15 минут, у Room Alco около 30 минут, у 700ml до 24 часов. Скорость оценки не выделяет ни одного игрока."
 ],
 [
  "Можно ли продать бутылку без коробки или акцизной марки?",
  "Часто можно: например, 1buyup берёт бутылки без коробки и без акцизной марки, а также алкоголь СССР. Но без коробки цена может быть ниже до 30% (по данным Red Decanter)."
 ]
]


def shared_blocks(depth=0):
    """Сквозные блоки: калькулятор, пять вопросов, подготовка бутылки, методика оценки."""
    p = "../" * depth
    disc_rows = "".join(
        f"<tr><td>{e(n)}</td><td>{rub(mk)}</td><td>{rub(b)}</td><td class='lime'>−{round((1 - b / mk) * 100)}%</td></tr>"
        for n, mk, b in DISC)
    clusters = "".join(
        f"<tr><td>{e(n)}</td><td>{', '.join(e(d) for d in ds)}</td></tr>" for n, ds in CLUSTERS)
    return f"""<div class="shared">
<section class="section ranking-section" id="calc">
<div class="container">
<div class="calculator-shell">
<div class="calculator-form">
<span class="eyebrow">Калькулятор</span>
<h2 class="calculator-title">Сколько стоит ваш алкоголь при выкупе?</h2>
<p class="calculator-copy">Хотите понять, за какую сумму можно продать коньяк, виски, вино или шампанское? Введите рыночную цену бутылки — аукционную или цену импортёра. Скупки обычно платят 67–72% от неё: так получается по опубликованным таблицам цен скупок. Это быстрый ориентир, а не оценка конкретной бутылки — точную сумму назовёт эксперт после фото и осмотра.</p>
<form id="calcForm" class="form-grid">
<label class="full lbl">Рыночная цена бутылки, ₽<input class="field" id="market" type="number" min="1" step="100" inputmode="numeric" placeholder="например, 45000" required></label>
<button class="btn btn-primary calculator-submit full" type="submit">Узнать стоимость <span class="arrow">→</span></button>
</form>
</div>
<aside class="calculator-result" aria-live="polite">
<span class="result-label">Ориентир выкупа</span>
<div class="result-price" id="resultPrice">—</div>
<p class="result-note" id="resultNote">Введите цену и нажмите кнопку — получите предварительный диапазон.</p>
<div class="range"></div>
<span class="result-disclaimer">Не является ценой сделки. Подлинность, этикетка, капсула, пробка, уровень жидкости, коробка и спрос меняют итоговую сумму.</span>
</aside>
</div>
<h3 class="sub">Как считается дисконт: опубликованные цены выкупа, виски</h3>
<div class="table-wrap"><table class="data">
<thead><tr><th>Позиция</th><th>Рынок</th><th>Готовы купить до</th><th>Дисконт</th></tr></thead>
<tbody>{disc_rows}</tbody></table></div>
<p class="note">Источник: открытые таблицы цен скупок (раздел «Виски»), цифры ориентировочные. Скупка платит не больше 67–72% рынка. Реальные цены других скупок — на странице <a href="{p}prices.html" class="text-link">«Цены выкупа»</a>.</p>
</div>
</section>

<section class="section" id="choose">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Перед сделкой</span><h2 class="section-title">Пять вопросов<br>перед сделкой</h2></div>
<p class="section-copy">Скупка устроена однотипно: заявка, фото, предварительная цена, встреча и расчёт. Различия скрыты в деталях — проверьте их до того, как отправить бутылку или вызвать выезд.</p>
</div>
<div class="steps-grid">
<article class="step"><div class="step-number">01</div><h3 class="step-title">Цена изменится?</h3><p>Главная причина недовольства клиентов — цена меняется при встрече. 1buyup, TotalStok, Kupimalko и VykupAlko прямо обещают, что согласованная по фото сумма не изменится. Попросите подтвердить это в переписке до приезда специалиста.</p></article>
<article class="step"><div class="step-number">02</div><h3 class="step-title">«От» или «до»?</h3><p>700ml пишет «от» (нижняя граница), 1buyup — «до» (потолок). По Yamazaki 18 разброс достигает 2,5 раза. Напрямую такие цифры сравнивать нельзя — уточняйте, что именно компания готова заплатить.</p></article>
<article class="step"><div class="step-number">03</div><h3 class="step-title">Есть ли цены на сайте?</h3><p>Конкретные цены публикуют четыре компании: 700ml, 1buyup, Red Decanter и SKUPKA-ALKOGOL. Остальные называют сумму только после того, как вы пришлёте фото.</p></article>
<article class="step"><div class="step-number">04</div><h3 class="step-title">Кто на самом деле?</h3><p>Независимых операторов меньше, чем сайтов: часть сайтов, вероятно, принадлежит одной компании (см. <a class="text-link" href="{p}metodika.html">методику</a>). Запрос в «разные» скупки одной группы даст то же предложение.</p></article>
<article class="step"><div class="step-number">05</div><h3 class="step-title">Что с обещаниями?</h3><p>«До 90%» и «до 100%» рыночной цены — маркетинг: реальный дисконт около 28–33%. Цифры «10+ лет», «5000 сделок» и «97% выкупа» — самозаявления, их никто не проверял.</p></article>
<article class="step"><div class="step-number">06</div><h3 class="step-title">Как пройдёт сделка?</h3><p>Обычно так: заявка → фото в мессенджер → предварительная цена → выезд или встреча → осмотр → расчёт наличными или переводом на карту. Уточните, будет ли договор и кто приедет.</p></article>
</div>
<div class="prose checklist">
<p><strong>Как продать алкоголь выгодно и быстро.</strong> Не ограничивайтесь одним предложением: отправьте одинаковые фотографии в две-три компании любым удобным способом — через мессенджер, по телефону или заявку на сайте — и сравните сумму, срок ответа и условия. Обратите внимание на преимущества: выезд на адрес в Москве и Московской области, оплату наличными или на карту, возможность продать целую коллекцию, работу с регионами России. Важно: не соглашайтесь на предложение без объяснения, от чего зависит цена, и не отправляйте бутылку, пока сумма не подтверждена.</p>
</div>
</div>
</section>

<section class="section ranking-section" id="prepare">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Фото для оценки</span><h2 class="section-title">Как подготовить<br>бутылку к оценке</h2></div>
<p class="section-copy">Чем точнее фотографии, тем быстрее придёт ответ и тем ближе предварительная цена к итоговой. Сделайте снимки при дневном свете и отправьте в Telegram, WhatsApp, Viber или Max выбранной компании.</p>
</div>
<div class="trust-grid">
<article class="trust-item"><div class="trust-symbol">1</div><h3 class="trust-title">Этикетки</h3><p>Сфотографируйте лицевую и обратную этикетки, чтобы эксперт увидел бренд, производителя, год и состояние бумаги.</p></article>
<article class="trust-item"><div class="trust-symbol">2</div><h3 class="trust-title">Капсула и пробка</h3><p>Покажите горлышко, капсулу, пробку и акцизную марку — повреждения заметно снижают стоимость.</p></article>
<article class="trust-item"><div class="trust-symbol">3</div><h3 class="trust-title">Уровень жидкости</h3><p>Снимите бутылку на просвет: для старых бутылок и винтажных вин уровень жидкости критичен.</p></article>
<article class="trust-item"><div class="trust-symbol">4</div><h3 class="trust-title">Упаковка</h3><p>Коробка, тубус, подарочная упаковка, декантер и документы повышают цену: без коробки до −30% (данные Red Decanter).</p></article>
</div>
<div class="prose checklist">
<p><strong>В сообщении укажите:</strong> бренд, название или релиз, год, объём, количество бутылок, город и удобный способ связи. Несколько экземпляров или целую коллекцию сфотографируйте общим планом и отправьте список.</p>
<p><strong>Чего не делать:</strong> не открывайте бутылку, не протирайте и не переклеивайте этикетки, не отрывайте акцизные марки. Сохраните коробки, тубусы, сертификаты и чеки — они подтверждают подлинность и происхождение.</p>
</div>
</div>
</section>

<section class="section" id="method-link">
<div class="container">
<div class="section-top" style="margin-bottom:0">
<div><span class="eyebrow">Методика</span><h2 class="section-title">Как составлен<br>рейтинг</h2></div>
<div><p class="section-copy" style="margin-bottom:20px">Что проверялось, какие факторы влияют на цену выкупа и как отбирались компании — на отдельной странице.</p><a class="btn btn-primary" href="{p}metodika.html">Читать методику <span class="arrow">→</span></a></div>
</div>
</div>
</section>
</div>
"""


def methodology_page():
    clusters = "".join(
        f"<tr><td>{e(n)}</td><td>{', '.join(e(d) for d in ds)}</td></tr>" for n, ds in CLUSTERS)
    return head(f"Методика составления рейтинга скупок алкоголя — {SITE}",
                "Как составлен рейтинг скупок алкоголя в Москве: источники данных, что проверялось, факторы оценки бутылки, ограничения и группы сайтов одного оператора.",
                path="metodika.html", ld=[breadcrumbs(("Главная", ""), ("Методика", "metodika.html"))]) + header() + f"""
<main id="top">
<section class="topic-hero">
<div class="container">
<span class="eyebrow">Методика</span>
<h1 class="page-title">Методика составления рейтинга</h1>
<p class="lead">Откуда берутся данные, что проверялось, какие факторы влияют на цену выкупа и где у рейтинга есть ограничения.</p>
</div>
</section>
<section class="section" id="method">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Методика оценки</span><h2 class="section-title">Как оценивают<br>алкоголь</h2></div>
<p class="section-copy">Так оценивают элитный и коллекционный алкоголь в Москве: эксперт называет цену по фото, а итоговую сумму подтверждает после осмотра бутылки.</p>
</div>
<div class="prose">
<p><strong>Какой алкоголь принимают.</strong> Скупки покупают элитные алкогольные напитки и коллекционное спиртное: коньяк (Hennessy, Rémy Martin, Louis XIII, Martell, Courvoisier), виски (Macallan, Yamazaki, Balvenie, Highland Park), вино (Petrus, Château Margaux, Château Lafite Rothschild, Château Mouton Rothschild — французские, Masseto и Sassicaia — итальянские), шампанское (Dom Pérignon, Cristal, Krug, Salon), ром, арманьяк и бренди, а также старые бутылки советского времени (СССР) с коллекционной ценностью. Принимают и отдельные бутылки, и целую коллекцию частного собрания. Водку и другой массовый сегмент, открытые бутылки и подделки обычно не берут — исключение делают Cupaj Club и Alko Prikup.</p>
</div>
<div class="factors">
<article><h3>Подлинность и бренд</h3><p>Производитель, марка и линейка — то, что влияет на стоимость в первую очередь. Поэтому эксперт просит показать этикетку и все основные детали бутылки. Подделки не принимают.</p></article>
<article><h3>Год и выдержка</h3><p>Винтаж, год выпуска, возраст виски и коньяка, ограниченный тираж и спрос на редкие релизы.</p></article>
<article><h3>Этикетка, капсула, пробка</h3><p>Сохранность бумаги, целая капсула и пробка, наличие акцизной марки и подарочной упаковки.</p></article>
<article><h3>Уровень жидкости</h3><p>Чем ниже уровень, тем дешевле бутылка. Открытые бутылки обычно не берут.</p></article>
<article><h3>Упаковка и комплектность</h3><p>Оригинальная коробка, тубус, футляр и декантер. Иногда их покупают отдельно.</p></article>
<article><h3>Объём, регион, партия</h3><p>Формат бутылки, город (в Москве платят больше) и количество: целая коллекция может оцениваться иначе, чем одна бутылка.</p></article>
</div>
<div class="prose" id="disclosure">
<p><strong>Откуда берутся цены.</strong> Ориентир — мировые аукционные цены и цены импортёров, а не розница магазина. Поэтому выкуп стоит дешевле, чем та же бутылка в магазине. Цены на сайтах скупок — заявленные ориентиры, а не оферта.</p>
<p><strong>Как составлен рейтинг.</strong> Изучены главные страницы сайтов и, где удалось, страницы категорий. Если сайт закрыт для автоматического доступа, использованы фрагменты поисковой выдачи (это отмечено в карточке). Данные собраны 30 сентября 2026 г. «Не публикует» значит: цен нет на проверенных страницах. Порядок компаний в списке не является оценкой качества услуг: сравнивайте по обзорам и таблице. Числовые рейтинги не выставлялись: независимого источника нет, оценки на Яндекс Картах и 2ГИС не собирались.</p>
<p><strong>Независимость.</strong> Рейтинг составлен по открытым данным из разных источников. Компании для сравнения отобраны редакцией сайта.</p>
<p><strong>Не проверено.</strong> Skupka-Star, Vine-Co (vine-co.ru), VinomerPro, Skupix, СпецВыкуп, Collectors Community, «VIP Выкуп», Vikup-Vina, e-skupka.ru, Alko-vikup, «Скупка PRO»; отзывы на Яндекс Картах и 2ГИС; цены на подстраницах категорий.</p>
<h3 class="sub">Возможно, один оператор</h3>
<p>По шаблонам, текстам и контактам видны группы сайтов, которые, вероятно, принадлежат одному оператору. Это признаки, а не доказательство.</p>
<div class="table-wrap"><table class="data"><thead><tr><th>Группа</th><th>Сайты</th></tr></thead><tbody>{clusters}</tbody></table></div>
</div>
</div>
</section>
{score_table()}
{summary_section()}
</main>
""" + footer()


def about_page():
    return head(f"О рейтинге скупок алкоголя — {SITE}",
                "О проекте: независимый рейтинг скупок элитного и коллекционного алкоголя в Москве. Сайт не оказывает и не продаёт услуги, информация носит справочный характер.",
                path="o-reitinge.html", ld=[{"@context": "https://schema.org", "@type": "AboutPage", "name": f"О рейтинге — {SITE}", "url": f"{SITE_URL}/o-reitinge.html", "inLanguage": "ru"}, breadcrumbs(("Главная", ""), ("О рейтинге", "o-reitinge.html"))]) + header() + f"""
<main id="top">
<section class="topic-hero">
<div class="container">
<span class="eyebrow">О рейтинге</span>
<h1 class="page-title">О рейтинге скупок алкоголя</h1>
<p class="lead">Независимый рейтинг компаний, которые покупают элитный и коллекционный алкоголь в Москве.</p>
</div>
</section>
<section class="section">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Миссия</h2>
<p>Старый коньяк, винтажное вино, редкий виски, бутылки из советского прошлого — это такие же предметы коллекций, как антиквариат. У них есть история, и цену им назначает не только рынок, но и честный разговор. Мы делаем этот рейтинг для тех, кто любит старину и коллекционные вещи и хочет расстаться со своей бутылкой без лишних иллюзий: понимать, кому можно доверять, сколько она может стоить на самом деле и на что обратить внимание, пока сделка не состоялась.</p>
<h2 class="sub">Наши цели</h2>
<ul class="goals">
<li><strong>Трезвый взгляд на цену.</strong> Показывать реальный порядок сумм и объяснять, чем «от» отличается от «до», а рыночная цена — от цены выкупа.</li>
<li><strong>Факты отдельно от рекламы.</strong> Заявление компании мы не выдаём за проверенный факт: «5000 сделок» и «до 90% рынка» так и подписываем — как заявления.</li>
<li><strong>Минусы наравне с плюсами.</strong> О слабых местах компаний пишем так же подробно, как о сильных.</li>
<li><strong>Честно о повторах.</strong> Если несколько сайтов, вероятно, принадлежат одному оператору, об этом нужно знать заранее.</li>
<li><strong>Независимость.</strong> Рейтинг составлен по открытым данным из разных источников, а компании для сравнения отобраны редакцией сайта.</li>
</ul>
<h2 class="sub">Для кого этот рейтинг</h2>
<p>Для коллекционеров и любителей старины, которые хотят понимать ценность своих вещей. Для тех, кому достался чужой погреб или коллекция и кто не знает, с чего начать. Для владельцев ресторанов и магазинов с остатками. И вообще для всех, кто ценит честные оценки и не хочет отдавать редкую бутылку за бесценок.</p>
<h2 class="sub">О сайте</h2>
<p><strong>Что это за сайт.</strong> Мы сравниваем компании, которые скупают коньяк, виски, вино, шампанское и другой коллекционный алкоголь: скорость оценки по фото, публичные цены, условия сделки, плюсы и минусы. Цель — чтобы продавец мог заранее понять, к кому обращаться и чего ожидать.</p>
<p><strong>Мы не оказываем и не продаём услуги.</strong> Сайт не покупает алкоголь, не принимает бутылки и не участвует в сделках. Вы договариваетесь с выбранной компанией напрямую.</p>
<p><strong>Откуда данные.</strong> Публичные сайты компаний и, где сайт закрыт для автоматического доступа, фрагменты поисковой выдачи. Показатели вроде «5000 сделок» или «97% выкупа» — заявления самих компаний, мы их не проверяли. Подробности — в <a class="text-link" href="metodika.html">методике</a>.</p>
<p><strong>Ограничения.</strong> Вся информация носит исключительно информационный характер и может быть устаревшей. Цены и сроки — заявления компаний, а не оферта. Точную информацию уточняйте на сайтах компаний.</p>
<h2 class="sub">Как пользоваться рейтингом</h2>
<ol class="steps-list">
<li>Посмотрите <a class="text-link" href="./#ranking">список компаний</a> и прочитайте обзоры: чем хороша компания, что смущает, итог.</li>
<li>Сравните условия в <a class="text-link" href="./#compare">таблице</a> и <a class="text-link" href="prices.html">цены выкупа</a>.</li>
<li>Прикиньте сумму в <a class="text-link" href="./#calc">калькуляторе</a>.</li>
<li>Запросите предложения у двух-трёх компаний из разных групп (часть сайтов, вероятно, принадлежит одному оператору) и попросите зафиксировать цену в переписке.</li>
</ol>
<p class="note">Продажа алкоголя лицам младше 18 лет запрещена. Чрезмерное употребление алкоголя вредит вашему здоровью.</p>
</div>
</div>
</section>
</main>
""" + footer()


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
    body = head(f"Где можно продать алкоголь в Москве? Рейтинг скупок — {SITE}",
                "Где продать коньяк, виски, вино и шампанское в Москве выгодно и быстро: рейтинг 20 скупок элитного и коллекционного алкоголя, цены выкупа, скорость оценки по фото, условия выезда.",
                path="", ld=[itemlist(CARDS), faq_ld()]) + header() + f"""
<main id="top">
<section class="hero">
<div class="container hero-grid">
<div class="hero-content">
<span class="eyebrow">Независимый рейтинг · Москва</span>
<h1 class="hero-title">Где можно продать<br><span class="lime">алкоголь в Москве?</span></h1>
<p class="hero-copy">Рейтинг 20 скупок коллекционного виски, коньяка, вина и шампанского: кто называет цену открыто, как быстро делает оценку по фото и на каких условиях приезжает на выкуп.</p>
<div class="hero-buttons">
<a href="#ranking" class="btn btn-primary">Смотреть рейтинг <span class="arrow">→</span></a>
<a href="prices.html" class="btn btn-outline">Цены выкупа</a>
</div>
</div>
<div class="market-card-wrap">
<aside class="top-card" aria-label="Топ компаний">
<h2 class="top-title"><span>ТОП</span> компаний</h2>
<ol class="top-list">
{"".join(f'<li><a href="c/{c["slug"]}.html"><span class="tn">{e(c["name"])}</span><span class="tm">{e(c["meta"]["speed"])}</span></a></li>' for c in CARDS)}
</ol>
<a href="metodika.html" class="top-how">Как составлен список?</a>
</aside>
</div>
</div>
</section>

{key_facts(CARDS)}
<section class="section ranking-section" id="ranking">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Рейтинг</span><h2 class="section-title">Скупки алкоголя<br>в Москве</h2></div>
<p class="section-copy">Сравнение по скорости оценки, прозрачности цен и условиям сделки. Как составлен список — в <a class="text-link" href="metodika.html">методике</a>.</p>
</div>
<div class="filters" role="group" aria-label="Фильтры">
<button class="chip active" data-filter="all">Все 20</button>
<button class="chip" data-filter="prices">Публикуют цены</button>
<button class="chip" data-filter="fast">Оценка до 5 минут</button>
</div>
<div class="company-list" id="rankingTable">
{"".join(company_card(c) for c in CARDS)}
</div>
<p class="note">Сроки оценки и режимы работы — заявления компаний. Слова «не публикует» означают, что цен нет на проверенных страницах сайта.</p>
</div>
</section>

{compare_section([(c, c['meta']) for c in CARDS])}

{shared_blocks()}

<section class="section ranking-section" id="faq">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Вопросы</span><h2 class="section-title">Частые<br>вопросы</h2></div>
<p class="section-copy">Коротко о том, что покупают, что не берут и от чего зависит цена.</p>
</div>
<div class="faq">
{"".join(f"<details><summary>{e(q)}</summary><p>{e(an)}</p></details>" for q, an in FAQ)}
</div>
</div>
</section>

{topic_cross("index", 0)}
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


# ---------------------------------------------------------------- карточка компании: факты и иллюстрация
ND = "не указан"
FACTS = {
    "room-alco.ru": ("+7 (930) 935-31-48", "Info@whiskeygram.ru", "Москва, ул. Маршала Катукова, 24к6", "WhatsApp, Telegram, Max"),
    "diamant-alko.ru": ("+7 (930) 935-32-06 (WhatsApp; телефона в шапке сайта нет)", "", "Москва, ул. Петровка, 7", "WhatsApp, Telegram @evgenich322, Max"),
    "700ml.ru": ("+7 (977) 720-70-73", "24h@700ml.ru", "Москва, Пресненская наб., 2 (ТЦ «Афимолл») — место встречи", "WhatsApp, Telegram, Max"),
    "1buyup.ru": ("+7 (965) 340-66-00", "fine@1buyup.ru", "Москва, Тверская ул., 7 (м. Охотный Ряд)", "WhatsApp, Viber, Telegram, Max"),
    "reddecanter.ru": ("8 (495) 740-65-67, +7 (999) 546-63-03", "info@reddecanter.ru", "Москва, ул. Викторенко, 16 стр. 1, оф. 408 (м. Аэропорт)", "Telegram, Max"),
    "skupka-alkogol.ru": ("8 (910) 453-99-08", "info@skupka-alkogol.ru", "Москва, ул. Дорожная, 54 стр. 1 (м. Аннино)", "Telegram, Max"),
    "vykup-alko.ru": ("+7 (925) 875-28-20", "vykup.alko@yandex.ru", ND, "Telegram"),
    "alkoprikup.ru": ("+7 (929) 102-55-55", "info@alkoprikup.ru", "Москва, ул. Зорге, 17А", "Telegram, Max"),
    "sellmewine.ru": ("+7 (905) 714-82-82", "info@sellmewine.ru", "Москва, Ленинский пр-т, 44", "WhatsApp, Telegram, Max"),
    "skup-ka.ru": ("+7 (925) 986-34-06", "sale@skup-ka.ru", "Москва, ул. Руставели, 14с6", "WhatsApp, Telegram, Max"),
    "kupimalko.ru": ("+7 (929) 557-44-60", "kupimalko@mail.ru", ND, "WhatsApp, Telegram"),
    "cupajclub.ru": ("+7 (499) 755-93-73, +7 (925) 215-63-36", "", "Москва, Варшавское ш., 170Б стр. 2", "Telegram, Max"),
    "probkabar.com": ("+7 (968) 096-75-58 (в описании страницы также +7 (925) 929-63-01)", "sales@probkabar.com", ND, "Telegram skupkapremium"),
    "sellawine.ru": ("+7 (901) 578-11-16", "alcoskupka.ru@gmail.com", ND, ""),
    "alcobuyer.ru": ("+7 (916) 033-62-25", "alcobuyer@mail.ru", ND, "Telegram"),
    "oldcognac.ru": ("8 (903) 535-50-20", "sale@oldcognac.ru", "Москва, ул. Академика Челомея, 11", "WhatsApp, Telegram, Max"),
    "alcovikup.ru": ("+7 (977) 540-09-99", "", "Москва, МО, Казань (заявлено 11 офисов)", "WhatsApp, Telegram"),
    "prodat-alko.ru": ("+7 (985) 991-15-56", "", ND, "WhatsApp, Telegram"),
    "alkolombard.ru": ("+7 (999) 988-67-77", "", ND, "WhatsApp, Telegram, Max"),
    "vikup-alco.ru": ("+7 (981) 268-10-45 (WhatsApp, Telegram, Viber)", "", "Санкт-Петербург, Апраксин пер., 15", ""),
}
assert set(FACTS) == {c["domain"] for c in CARDS}

# какие бутылки рисовать на обложке: по специализации из анализа
SHAPES = {
    "reddecanter.ru": ["champagne", "whisky", "decanter", "champagne"],
    "skupka-alkogol.ru": ["decanter", "cognac", "glass", "cognac"],
    "700ml.ru": ["whisky", "wine", "champagne", "decanter"],
    "1buyup.ru": ["whisky", "whisky", "glass", "decanter"],
    "room-alco.ru": ["whisky", "decanter", "wine", "champagne"],
    "diamant-alko.ru": ["wine", "champagne", "whisky", "wine", "champagne"],
}
PALETTES = [("#431f2a", "#6b3342", "#d1ac6b"), ("#32151e", "#5a2a3a", "#e0c48c"),
            ("#3a2418", "#6a4329", "#d1ac6b"), ("#2b1a2a", "#573552", "#d9b878")]


def bottle(kind, x, h, col, rnd):
    """Силуэт бутылки с центром по x и высотой h, основание на y=470."""
    base = 470
    top = base - h
    w = {"whisky": 120, "cognac": 130, "decanter": 150, "wine": 100, "champagne": 112, "glass": 110}[kind]
    a, b, gold = col
    if kind == "glass":
        gh = h * 0.45
        y0 = base - gh
        return (f'<path d="M{x-w/2:.0f} {y0:.0f} L{x+w/2:.0f} {y0:.0f} L{x+w/2-10:.0f} {base} L{x-w/2+10:.0f} {base} Z" fill="url(#glass)" stroke="{gold}" stroke-opacity=".45"/>'
                f'<path d="M{x-w/2+6:.0f} {y0+gh*0.45:.0f} L{x+w/2-6:.0f} {y0+gh*0.45:.0f} L{x+w/2-12:.0f} {base-4} L{x-w/2+12:.0f} {base-4} Z" fill="{gold}" fill-opacity=".55"/>')
    neck = {"whisky": 26, "cognac": 24, "decanter": 30, "wine": 22, "champagne": 26}[kind]
    shoulder = top + h * {"whisky": .30, "cognac": .36, "decanter": .34, "wine": .34, "champagne": .42}[kind]
    L, R = x - w / 2, x + w / 2
    d = (f'M{x-neck/2:.0f} {top:.0f} L{x+neck/2:.0f} {top:.0f} L{x+neck/2:.0f} {top+h*.12:.0f} '
         f'C{x+neck/2:.0f} {shoulder-h*.1:.0f} {R:.0f} {shoulder-h*.04:.0f} {R:.0f} {shoulder+h*.08:.0f} '
         f'L{R:.0f} {base-10} Q{R:.0f} {base} {R-10:.0f} {base} L{L+10:.0f} {base} Q{L:.0f} {base} {L:.0f} {base-10} '
         f'L{L:.0f} {shoulder+h*.08:.0f} C{L:.0f} {shoulder-h*.04:.0f} {x-neck/2:.0f} {shoulder-h*.1:.0f} {x-neck/2:.0f} {top+h*.12:.0f} Z')
    cap = gold if kind != "wine" else "#2a1219"
    ly = shoulder + h * .18
    lh = h * .30
    return (f'<path d="{d}" fill="url(#glass)" stroke="{gold}" stroke-opacity=".5"/>'
            f'<rect x="{x-neck/2-2:.0f}" y="{top-8:.0f}" width="{neck+4}" height="14" rx="3" fill="{cap}"/>'
            f'<rect x="{L+8:.0f}" y="{ly:.0f}" width="{w-16}" height="{lh:.0f}" rx="3" fill="#f4ead6" fill-opacity=".92"/>'
            f'<rect x="{L+14:.0f}" y="{ly+lh*.22:.0f}" width="{w-28}" height="3" fill="{a}" fill-opacity=".7"/>'
            f'<rect x="{L+22:.0f}" y="{ly+lh*.5:.0f}" width="{w-44}" height="3" fill="{a}" fill-opacity=".45"/>'
            f'<path d="M{L+10:.0f} {shoulder+h*.06:.0f} L{L+10:.0f} {base-18}" stroke="#fff" stroke-opacity=".18" stroke-width="5" stroke-linecap="round"/>')


def cover_svg(c):
    import random
    rnd = random.Random(c["domain"])
    col = PALETTES[rnd.randrange(len(PALETTES))]
    a, b, gold = col
    kinds = SHAPES.get(c["domain"]) or [rnd.choice(["whisky", "cognac", "wine", "champagne", "decanter"]) for _ in range(rnd.choice([3, 4, 4]))]
    n = len(kinds)
    span = 1200 * .62
    x0 = 1200 * .5 - span / 2
    out = []
    for i, k in enumerate(kinds):
        x = x0 + span * (i + .5) / n
        h = {"whisky": 250, "cognac": 240, "decanter": 215, "wine": 300, "champagne": 310, "glass": 200}[k] * rnd.uniform(.92, 1.08)
        out.append(bottle(k, x, h, col, rnd))
    dots = "".join(f'<circle cx="{rnd.randrange(60,1140)}" cy="{rnd.randrange(40,300)}" r="{rnd.randrange(14,48)}" fill="{gold}" fill-opacity="{rnd.uniform(.05,.14):.2f}"/>' for _ in range(14))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 520" role="img" aria-label="Иллюстрация: {e(c['name'])}">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>
<linearGradient id="glass" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1c0c12" stop-opacity=".92"/><stop offset=".5" stop-color="{b}" stop-opacity=".9"/><stop offset="1" stop-color="#1c0c12" stop-opacity=".95"/></linearGradient>
<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{gold}" stop-opacity=".28"/><stop offset="1" stop-color="{gold}" stop-opacity="0"/></linearGradient>
</defs>
<rect width="1200" height="520" fill="url(#bg)"/>
{dots}
<rect x="0" y="470" width="1200" height="50" fill="url(#floor)"/>
<rect x="0" y="470" width="1200" height="2" fill="{gold}" fill-opacity=".6"/>
{''.join(out)}
</svg>
"""


def write_covers():
    d = ROOT / "assets" / "ill"
    d.mkdir(parents=True, exist_ok=True)
    for c in CARDS:
        (d / f"{c['slug']}.svg").write_text(cover_svg(c), encoding="utf-8")


def cover_figure(c):
    """Обложка: реальный скриншот assets/shots/<slug>.(jpg|png|webp), если он есть, иначе иллюстрация."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        if (ROOT / "assets" / "shots" / f"{c['slug']}.{ext}").exists():
            return (f'<figure class="cover"><img src="../assets/shots/{c["slug"]}.{ext}" alt="Главная страница {e(c["domain"])}" loading="lazy">'
                    f'<figcaption>Главная страница сайта {e(c["domain"])} (снимок на 1 октября 2026)</figcaption></figure>')
    return (f'<figure class="cover"><img src="../assets/ill/{c["slug"]}.svg" alt="Иллюстрация: {e(c["name"])}" width="1200" height="520">'
            f'<figcaption>Иллюстрация: {e(c["name"])}</figcaption></figure>')


def facts_table(c):
    phone, email, addr, msg = FACTS[c["domain"]]
    rows = [("Сайт", f'<a href="https://{e(c["domain"])}" rel="{"sponsored noopener" if c["own"] else "nofollow noopener"}" target="_blank">{e(c["domain"])}</a>')]
    rows.append(("Телефон", e(phone)))
    rows.append(("График работы", e(mode_of(c))))
    rows.append(("Адрес", e(addr)))
    if email:
        rows.append(("Почта", e(email)))
    if msg:
        rows.append(("Мессенджеры", e(msg)))
    rows.append(("Скорость оценки", e(c["speed"])))
    rows.append(("Цены", e(c["prices"])))
    rows.append(("Диапазон цен", e(price_range(c)[0]) + " <span class='muted'>— " + e(price_range(c)[1]) + "</span>"))
    return '<table class="facts-table"><tbody>' + "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows) + "</tbody></table>"


# ---------------------------------------------------------------- карточки рейтинга


def lf(s):
    """С маленькой буквы, если слово не бренд/аббревиатура."""
    return s[0].lower() + s[1:] if len(s) > 1 and s[0].isalpha() and s[0].isupper() and s[1].islower() and "а" <= s[0].lower() <= "я" else s


def price_of(name, col):
    for r in PRICES:
        if r[0] == name:
            return r[col]
    raise KeyError(name)


def _nums(val):
    val = re.sub(r"\([^)]*\)", "", val.replace("\xa0", " "))
    return [int(x.replace(" ", "")) for x in re.findall(r"\d{1,3}(?: \d{3})+|\d+", val)]


def fmt_rub(n):
    return f"{n:,}".replace(",", " ")


def price_range(c, topic=None):
    """(диапазон, пояснение). Считается из прайса самой компании; у остальных — общий рыночный ориентир."""
    d = c["domain"]
    col = {"700ml.ru": 1, "1buyup.ru": 2, "reddecanter.ru": 3, "skupka-alkogol.ru": 4}.get(d)
    generic = ("67–72% от рыночной цены бутылки", "Компания цены не публикует; указан типичный уровень выкупа по открытым таблицам цен скупок. Цены меняются — уточняйте перед сделкой.")
    if topic == "champagne":
        if col in (1, 3):
            n = [x for r in CHAMP_ROWS for x in _nums(r[col])]
            return f"от {fmt_rub(min(n))} до {fmt_rub(max(n))} ₽", "По опубликованным позициям шампанского. Цены меняются — диапазон ориентировочный."
        return generic
    claims = {"vykup-alko.ru": ("заявляет «до 90% рыночной цены»", "Заявление компании, не подтверждено: у скупок, публикующих цены, реальный потолок около 70%. Конкретных цен компания не публикует."),
              "alkoprikup.ru": ("заявляет «до 100% рыночной цены»", "Заявление компании, формулировка расплывчатая. Конкретных цен не публикует; окончательная сумма — после осмотра.")}
    if d in claims:
        return claims[d]
    if col is None:
        return generic
    n = [x for r in PRICES for x in _nums(r[col])]
    if d == "700ml.ru":
        n += [x for _, v in RUM for x in _nums(v)]
    lo, hi = min(n), max(n)
    kind = {1: "цены «от»", 2: "цены «до»", 3: "приблизительные цены", 4: "приблизительные цены"}[col]
    return f"от {fmt_rub(lo)} до {fmt_rub(hi)} ₽", f"По опубликованным позициям компании ({kind}). Цены меняются — диапазон ориентировочный."


def price_hint(c, topic=None):
    d = c["domain"]
    if topic == "champagne":
        col = {"700ml.ru": 1, "reddecanter.ru": 3}.get(d)
        if col:
            return "Цены на шампанское не публикует"  # примеры не выводим: диапазон задаёт price_range
        return "Цены на шампанское не публикует — сумму называет после фото."
    if d == "700ml.ru":
        return f"Hennessy XO — от {price_of('Hennessy XO', 1)} ₽; Highland Park 18 — от {price_of('Highland Park 18', 1)} ₽; Cristal Brut 2012 — от {price_of('Cristal Brut 2012', 1)} ₽."
    if d == "1buyup.ru":
        ex = [("Macallan 18 Sherry Oak", 50000), ("Yamazaki 18", 32000), ("Highland Park 18", 10000)]
        return "; ".join(f"{n} — до {fmt_rub(v)} ₽" for n, v in ex) + "."
    if d == "reddecanter.ru":
        return f"Macallan M Decanter — {price_of('Macallan M Decanter', 3)} ₽; Yamazaki 25 — {price_of('Yamazaki 25', 3)} ₽; Cristal Brut 2012 — {price_of('Cristal Brut 2012', 3)} ₽ (приблизительно)."
    if d == "skupka-alkogol.ru":
        return "Коньяк VS / VSOP / XO — от 500 / 1 500 / 3 000 ₽; Hennessy Paradis — около 50 000 ₽ (приблизительно)."
    if d == "sellawine.ru":
        return "Цены не проверены."
    return "Цены не публикует — сумму называет после фото."


# ---------------------------------------------------------------- обзоры (tools/reviews.txt)
# Отзывы с 2ГИС в обзоре №14 из исходного текста не проверены: по умолчанию не публикуются.
INCLUDE_2GIS_CLAIMS = False


def load_reviews():
    txt = (ROOT / "tools" / "reviews.txt").read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^(\d{1,2})\. ", txt)[1:]
    out = {}
    for num, body in zip(blocks[0::2], blocks[1::2]):
        lines = [l.strip() for l in body.split("\n")[1:] if l.strip()]
        d = {}
        for l in lines:
            if l.startswith(("Кратко:", "Независимая оценка:")):
                d["lead"] = l.split(":", 1)[1].strip()
            elif l.startswith("Плюсы."):
                d["pros"] = l[len("Плюсы."):].strip()
            elif l.startswith("Минусы."):
                d["cons"] = l[len("Минусы."):].strip()
            elif l.startswith("Вердикт."):
                d["verdict"] = l[len("Вердикт."):].strip()
            elif l.startswith("Что заявляет сайт."):
                d["pros"] = l[len("Что заявляет сайт."):].strip()
            elif l.startswith("Что видно на 2ГИС."):
                d["cons"] = l[len("Что видно на 2ГИС."):].strip()
        if int(num) == 14 and not INCLUDE_2GIS_CLAIMS:
            d["lead"] = "данных для однозначного вывода мало: сайт закрывается для автоматического доступа."
            d["pros"] = d["pros"].split(" Главный сайт")[0]
            d["cons"] = "Цены и условия по открытым страницам не подтверждены: главный сайт при проверке закрывался для автоматического доступа, часть данных взята из поисковой выдачи."
            d["verdict"] = "Перед обращением самостоятельно проверьте актуальность условий и отзывы в картах."
        lead = d["lead"]
        d["lead"] = lead[0].upper() + lead[1:]
        out[CARDS[int(num) - 1]["domain"]] = d
    return out


REVIEWS = load_reviews()
assert set(REVIEWS) == {c["domain"] for c in CARDS}, "обзоры не для всех компаний"
assert all({"lead", "pros", "cons", "verdict"} <= set(v) for v in REVIEWS.values())


def overview(c):
    """Список (css-класс, подпись, текст) для карточки."""
    r = REVIEWS[c["domain"]]
    return [("cc-lead", "", r["lead"]), ("", "Чем хороша.", r["pros"]), ("", "Что смущает.", r["cons"]), ("cc-verdict", "Итог.", r["verdict"])]


def card_image(c, prefix=""):
    for ext in ("jpg", "jpeg", "png", "webp"):
        if (ROOT / "assets" / "shots" / f"{c['slug']}.{ext}").exists():
            return f'{prefix}assets/shots/{c["slug"]}.{ext}', f"Главная страница {c['domain']}"
    return f'{prefix}assets/ill/{c["slug"]}.svg', f"Иллюстрация: {c['name']}"


def company_card(c, m=None, topic=None, prefix="", hint=None):
    m = m or c["meta"]
    addr = FACTS[c["domain"]][2]
    mode = mode_of(c)
    img, alt = card_image(c, prefix)
    rel = "noopener nofollow"
    paras = "".join(f'<p class="{k}">' + (f"<strong>{l}</strong> " if l else "") + f"{e(x)}</p>" for k, l, x in overview(c))
    hint = hint or price_hint(c, topic)
    rng, rng_note = price_range(c, topic)
    examples = not hint.startswith(("Цены не", "Цены на шампанское не"))
    return f"""<article class="company-card" id="{c['slug']}" data-prices="{'1' if m['price'] not in ('Не публикует', 'Не проверено') else '0'}" data-fast="{'1' if c['slug'] in FAST else '0'}">
<h3 class="cc-name"><a href="{prefix}c/{c['slug']}.html">{e(c['name'])}</a></h3>
<div class="cc-body">
<div class="cc-side"><figure class="cc-img"><img src="{img}" alt="{e(alt)}" loading="lazy" width="1200" height="520"></figure>
{rating_block(c, compact=True)}</div>
<div class="cc-main">
<dl class="cc-facts">
<div><dt>График работы</dt><dd>{e(mode)}</dd></div>
<div><dt>Адрес</dt><dd>{e(addr)}</dd></div>
<div><dt>Сайт</dt><dd><a href="https://{e(c['domain'])}" target="_blank" rel="{rel}">{e(c['domain'])}</a></dd></div>
</dl>
<div class="cc-text">{paras}</div>
</div>
</div>
<div class="cc-foot">
<div class="cc-price"><span>Диапазон цен</span><strong>{e(rng)}</strong><em>{e(rng_note)}{e(' Например: ' + hint) if examples else ''}</em></div>
<div class="cc-actions">
<a class="btn btn-outline" href="{prefix}c/{c['slug']}.html">Подробнее</a>
<button class="btn btn-primary btn-review" type="button" data-company="{e(c['name'])}">Оставить отзыв</button>
</div>
</div>
</article>
"""


def summary_section():
    rows = [
        ("Живые отзывы на Яндекс Картах / 2ГИС", "Почти ни у кого."),
        ("Открытый прайс", "700ml, 1buyup, Red Decanter, SKUPKA-ALKOGOL."),
        ("Честный дисконт", "Рынок и потолок рядом показывает одна компания: ≈28–33%."),
        ("Гарантия «цена по фото = цена на встрече»", "1buyup, VykupAlko, Kupimalko, TotalStok (заявления, не аудит)."),
        ("Вероятные группы сайтов", "700ml + Alko Lombard + oldcognac; Red Decanter + SKUPKA-ALKOGOL; Cupaj Club + Alko Prikup."),
        ("Room Alco / Diamant Alko", "Услуги шире рынка, но независимой репутации и прайса нет."),
    ]
    body = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td></tr>" for a, b in rows)
    return f"""<section class="section ranking-section" id="summary">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Итоги проверки</span><h2 class="section-title">Что проверялось<br>и что нашли</h2></div>
<p class="section-copy">Коротко о том, что действительно можно проверить по открытым данным, а что остаётся заявлением компаний.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Что проверялось</th><th>Итог</th></tr></thead><tbody>{body}</tbody></table></div>
</div>
</section>
"""


def compare_rows(rows):
    return "\n".join(
        f"<tr><td><a href='c/{c['slug']}.html'><strong>{e(c['name'])}</strong></a><br><span class='muted'>{e(c['domain'])}</span></td>"
        f"<td><strong>{scores(c)[1]:g}</strong></td><td>{e(mode_of(c))}</td><td>{e(m['speed'])}</td><td>{e(m['price'])}</td><td>{e(m['nom'])}</td></tr>"
        for c, m in rows)


def compare_section(rows, title="Сравнение<br>условий", copy="Режим работы, заявленная скорость предварительной оценки, публичность цен и специализация."):
    return f"""<section class="section" id="compare">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Сравнительная таблица</span><h2 class="section-title">{title}</h2></div>
<p class="section-copy">{copy}</p>
</div>
<div class="table-wrap"><table class="data">
<thead><tr><th>Компания</th><th>Оценка</th><th>Режим</th><th>Скорость оценки</th><th>Цены</th><th>Специализация</th></tr></thead>
<tbody>
{compare_rows(rows)}
</tbody></table></div>
</div>
</section>
"""


def review_dialog(p=""):
    return f"""<dialog id="reviewDialog" class="review">
<form method="dialog" id="reviewForm" data-endpoint="{e(REVIEW_ENDPOINT)}">
<h3 class="sub" style="margin:0 0 6px">Оставить отзыв</h3>
<p class="muted" id="reviewCompany" style="margin-bottom:14px"></p>
<label class="lbl">Ваше имя<input class="field" name="name" maxlength="80" autocomplete="name"></label>
<label class="lbl">Оценка<select class="field" name="rating" required><option value="">Выберите</option><option>5</option><option>4</option><option>3</option><option>2</option><option>1</option></select></label>
<label class="lbl">Отзыв<textarea class="field" name="text" rows="5" maxlength="2000" required></textarea></label>
<p class="muted">Отправляя отзыв, вы соглашаетесь с <a class="text-link" href="{p}politika-konfidencialnosti.html">политикой конфиденциальности</a>.</p>
<p class="muted" id="reviewMsg" role="status"></p>
<div class="cc-actions"><button class="btn btn-outline" type="button" id="reviewCancel">Закрыть</button><button class="btn btn-primary" type="submit">Отправить</button></div>
</form>
</dialog>
"""


# ---------------------------------------------------------------- оценка редакции (3 параметра, 1–5)
# Параметры считаются по правилам из «Методики» только из открытых данных анализа.
PARAMS = [
    ("price", "Прозрачность цен"),
    ("speed", "Скорость и удобство"),
    ("trust", "Открытость компании"),
]
# price: full — ≥20 цен в открытом доступе; partial — есть прайс/ориентиры; guarantee — цен нет, но гарантирует цену по фото; none — цен нет
# speed_min — верхняя граница заявленной оценки по фото (мин.); hours — часов работы в сутки (24 — круглосуточно); weekdays — только будни
# checks — 5 признаков открытости: адрес, режим работы, самостоятельный сайт, нет противоречий/устаревших данных, публичные подтверждения
SCORE_INPUT = {
    "room-alco.ru":      dict(price="none", speed_min=30, hours=24, weekdays=False, checks=(1, 1, 0, 0, 0)),
    "diamant-alko.ru":   dict(price="none", speed_min=10, hours=None, weekdays=False, checks=(1, 0, 1, 0, 0)),
    "700ml.ru":          dict(price="full", speed_min=1440, hours=17, weekdays=False, checks=(1, 1, 0, 1, 0)),
    "1buyup.ru":         dict(price="partial", speed_min=30, hours=12, weekdays=False, checks=(1, 1, 1, 1, 0)),
    "reddecanter.ru":    dict(price="partial", speed_min=15, hours=9, weekdays=False, checks=(1, 1, 0, 1, 0)),
    "skupka-alkogol.ru": dict(price="partial", speed_min=15, hours=9, weekdays=False, checks=(1, 1, 0, 0, 0)),
    "vykup-alko.ru":     dict(price="guarantee", speed_min=15, hours=11, weekdays=False, checks=(0, 1, 1, 0, 0)),
    "alkoprikup.ru":     dict(price="none", speed_min=3, hours=10, weekdays=False, checks=(1, 1, 0, 0, 0)),
    "sellmewine.ru":     dict(price="none", speed_min=15, hours=24, weekdays=False, checks=(1, 1, 1, 0, 0)),
    "skup-ka.ru":        dict(price="none", speed_min=None, hours=12, weekdays=True, checks=(1, 1, 1, 0, 0)),
    "kupimalko.ru":      dict(price="guarantee", speed_min=5, hours=14, weekdays=False, checks=(0, 1, 0, 1, 0)),
    "cupajclub.ru":      dict(price="none", speed_min=5, hours=10, weekdays=False, checks=(1, 1, 0, 0, 0)),
    "probkabar.com":     dict(price="none", speed_min=15, hours=None, weekdays=False, checks=(0, 0, 1, 0, 0)),
    "sellawine.ru":      dict(price="none", speed_min=15, hours=13, weekdays=False, checks=(0, 1, 1, 0, 0)),
    "alcobuyer.ru":      dict(price="none", speed_min=None, hours=24, weekdays=False, checks=(0, 1, 1, 0, 0)),
    "oldcognac.ru":      dict(price="none", speed_min=None, hours=None, weekdays=False, checks=(1, 0, 0, 1, 0)),
    "alcovikup.ru":      dict(price="none", speed_min=5, hours=11, weekdays=False, checks=(0, 1, 1, 0, 0)),
    "prodat-alko.ru":    dict(price="guarantee", speed_min=None, hours=24, weekdays=False, checks=(0, 1, 1, 1, 0)),
    "alkolombard.ru":    dict(price="none", speed_min=None, hours=17, weekdays=False, checks=(0, 1, 0, 1, 0)),
    "vikup-alco.ru":     dict(price="none", speed_min=5, hours=None, weekdays=False, checks=(1, 0, 1, 1, 0)),
}
assert set(SCORE_INPUT) == {c["domain"] for c in CARDS}
PRICE_SCORE = {"full": 5, "partial": 4, "guarantee": 2.5, "none": 2}


def speed_score(i):
    m = i["speed_min"]
    s = 2.5 if m is None else 4.5 if m <= 5 else 4 if m <= 15 else 3 if m <= 30 else 2.5 if m <= 120 else 2
    h = i["hours"]
    if h is not None:
        s += 0.5 if h >= 14 else -0.5 if h <= 9 else 0
    if i["weekdays"]:
        s -= 0.5
    return min(5, max(1, s))


def scores(c):
    i = SCORE_INPUT[c["domain"]]
    p = {"price": PRICE_SCORE[i["price"]], "speed": speed_score(i), "trust": max(1, sum(i["checks"]))}
    total = round(sum(p.values()) / 3, 1)
    return p, total


def stars(v, cls=""):
    return f'<span class="stars {cls}" style="--p:{v / 5 * 100:.0f}%" role="img" aria-label="{v:g} из 5">★★★★★</span>'


def rating_block(c, compact=False):
    p, total = scores(c)
    rows = "".join(f'<div class="rt-row"><span>{e(lbl)}</span>{stars(p[k], "sm")}<b>{p[k]:g}</b></div>' for k, lbl in PARAMS)
    return f"""<div class="rating">
<div class="rt-head"><div class="rt-total">{total:g}</div><div>{stars(total)}<div class="rt-cap">Оценка редакции из 5</div></div></div>
<div class="rt-rows">{rows}</div>
<a class="rt-how" href="{'' if compact else '../'}metodika.html#score">Как считается оценка</a>
</div>
"""


def score_table():
    rows = "".join(
        f"<tr><td><strong>{e(c['name'])}</strong></td>" + "".join(f"<td>{scores(c)[0][k]:g}</td>" for k, _ in PARAMS) + f"<td><strong>{scores(c)[1]:g}</strong></td></tr>"
        for c in CARDS)
    return f"""<section class="section ranking-section" id="score">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Оценка редакции</span><h2 class="section-title">Как считается<br>оценка</h2></div>
<p class="section-copy">Три параметра по шкале от 1 до 5. Оценка выставлена по формальным признакам из открытых данных, это не отзывы клиентов и не проверка качества услуг.</p>
</div>
<div class="factors">
<article><h3>Прозрачность цен</h3><p>5 — в открытом доступе 20 и более цен; 4 — есть прайс или ориентиры по части позиций; 2,5 — цен нет, но компания гарантирует цену, согласованную по фото; 2 — цен нет.</p></article>
<article><h3>Скорость и удобство</h3><p>База по заявленному сроку оценки по фото: до 5 минут — 4,5; до 15 — 4; до 30 — 3; до 2 часов — 2,5; дольше — 2; срок не указан — 2,5. Плюс 0,5 за работу 14 часов в сутки и больше, минус 0,5 за 9 часов и меньше и ещё минус 0,5, если только по будням.</p></article>
<article><h3>Открытость компании</h3><p>По баллу за каждый признак: указан адрес; указан режим работы; сайт самостоятельный (не похож на сайт другого оператора); нет противоречий и устаревших данных; есть публичные подтверждения (кейсы, датированные отзывы). Минимум — 1.</p></article>
</div>
<p class="note">Данные рейтинга в машиночитаемом виде: <a class="text-link" href="data/companies.json">companies.json</a> и <a class="text-link" href="data/companies.csv">companies.csv</a>.</p>
<p class="note">Итоговая оценка — среднее трёх параметров, округлённое до десятых. Публичных подтверждений в открытых данных не нашлось ни у кого, поэтому пятёрки по открытости нет у всех. Сроки и режимы — заявления компаний. Оценка отражает данные на дату сбора и может измениться.</p>
<div class="table-wrap"><table class="data"><thead><tr><th>Компания</th><th>Прозрачность цен</th><th>Скорость и удобство</th><th>Открытость</th><th>Итого</th></tr></thead><tbody>{rows}</tbody></table></div>
</div>
</section>
"""


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
    own = ""
    rel = "sponsored noopener" if c["own"] else "nofollow noopener"
    nav = ""
    if prev_c:
        nav += f'<a href="{prev_c["slug"]}.html" class="btn btn-outline">← {e(prev_c["name"])}</a>'
    if next_c:
        nav += f'<a href="{next_c["slug"]}.html" class="btn btn-outline">{e(next_c["name"])} →</a>'
    return head(f"{c['name']} — скупка алкоголя: обзор, цены, условия | {SITE}",
                f"{c['name']} ({c['domain']}): режим работы, скорость оценки, цены выкупа, плюсы и минусы. Оценка редакции {scores(c)[1]:g} из 5.", 1,
                path=f"c/{c['slug']}.html", ld=[breadcrumbs(("Главная", ""), (c["name"], f"c/{c['slug']}.html")), review_ld(c)]) + header(1) + f"""
<main class="page">
<div class="container narrow">
<nav class="crumbs"><a href="../">Рейтинг</a> / {e(c['name'])}</nav>
<span class="eyebrow">Скупка алкоголя</span>
<h1 class="page-title">{e(c['name'])}</h1>
<p class="lead">Скупка алкоголя: {e(c['meta']['nom'][0].lower() + c['meta']['nom'][1:])}.</p>
{note}{own}{warn}
{cover_figure(c)}
{rating_block(c)}
<div class="badges">
<div class="badge"><span>График работы</span><strong>{e(mode_of(c))}</strong></div>
<div class="badge"><span>Оценка по фото</span><strong>{e(c['meta']['speed'])}</strong></div>
<div class="badge"><span>Цены на сайте</span><strong>{e(c['meta']['price'])}</strong></div>
</div>
{facts_table(c)}
<div class="proscons">
<div><h2 class="sub">Плюсы</h2><ul class="list plus">{pros}</ul></div>
<div><h2 class="sub">Минусы</h2><ul class="list minus">{cons}</ul></div>
</div>
{company_prices(c)}
<p class="note">Данные собраны {UPDATED} по публичным сайтам компании. Самозаявления не проверялись. Цены и условия уточняйте у компании.</p>
<div class="pager">{nav}</div>
</div>
</main>
{shared_blocks(1)}
""" + footer(1)


def prices_page():
    def td(v):
        return f"<td class='{'dash' if v == '—' else ''}'>{e(v)}</td>"
    main = "".join("<tr>" + f"<td>{e(r[0])}</td>" + "".join(td(v) for v in r[1:]) + "</tr>" for r in PRICES)
    rum = "".join(f"<tr><td>{e(a)}</td><td>{e(b)} ₽</td></tr>" for a, b in RUM)
    seg = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td></tr>" for a, b in SEG)
    return head(f"Цены выкупа элитного алкоголя в Москве — {SITE}",
                "Сводка цен выкупа виски, коньяка, шампанского и вина по данным 700ml, 1buyup, Red Decanter и SKUPKA-ALKOGOL.",
                path="prices.html", ld=[breadcrumbs(("Главная", ""), ("Цены выкупа", "prices.html"))]) + header() + f"""
<main class="page">
<div class="container">
<span class="eyebrow">Сводка по источникам</span>
<h1 class="page-title">Цены выкупа алкоголя в Москве</h1>
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
{shared_blocks()}
""" + footer()


TOPICS = [
    dict(file="gde-prodat-elitnyy-alkogol.html", key="elite",
         nav="Элитный алкоголь",
         title=f"Где можно продать элитный алкоголь в Москве? Рейтинг скупок — {SITE}",
         desc="Где продать элитный алкоголь в Москве: рейтинг скупок редкого виски, коньяка, вина и шампанского премиум-класса. Цены выкупа, скорость оценки по фото, выезд, условия сделки.",
         h1="Где можно продать элитный алкоголь?",
         eyebrow="Рейтинг · премиум и коллекционные бутылки",
         lead="Сравнение скупок, которые берут премиальный и коллекционный алкоголь: редкий виски, выдержанный коньяк, марочное вино и шампанское. Кто публикует цены на дорогие позиции, как быстро оценивает по фото и на каких условиях приезжает."),
    dict(file="gde-prodat-elitnoe-shampanskoe.html", key="champagne",
         nav="Шампанское",
         title=f"Где можно продать элитное шампанское в Москве? Рейтинг скупок — {SITE}",
         desc="Где продать элитное шампанское в Москве: рейтинг скупок Dom Pérignon, Cristal, Krug, Salon. Цены выкупа, скорость оценки по фото, выезд, что влияет на стоимость.",
         h1="Где можно продать элитное шампанское?",
         eyebrow="Рейтинг · Dom Pérignon, Cristal, Krug, Salon",
         lead="Сравнение скупок, которые покупают шампанское премиум-класса: винтажные кюве, розовое, большие форматы. Показываем, у кого есть открытые цены на шампанское, а у кого сумму называют только после фото."),
]
TOPIC_BY_KEY = {tp["key"]: tp for tp in TOPICS}

CHAMP_WORDS = ("Cristal", "Dom Pérignon", "Krug", "Salon", "Veuve", "Bollinger")
CHAMP_ROWS = [r for r in PRICES if r[0].startswith(CHAMP_WORDS)]


def champ_count(col):
    return sum(1 for r in CHAMP_ROWS if r[col] not in ("—", ""))


def ranked_cards(key):
    """Возвращает [(карточка, meta, место)] для тематической страницы."""
    by = {c["domain"]: c for c in CARDS}
    if key == "elite":
        order = ["room-alco.ru", "diamant-alko.ru", "reddecanter.ru", "700ml.ru", "1buyup.ru", "skupka-alkogol.ru"]
        tail_low = ["cupajclub.ru", "alkoprikup.ru"]  # заявляют, что берут и бюджетные позиции
        rest = [c["domain"] for c in CARDS if c["domain"] not in order + tail_low]
        order += rest + tail_low
        over = {
            "room-alco.ru": dict(nom="Круглосуточная оценка, хранение бутылок, подарочные коробки"),
            "diamant-alko.ru": dict(nom="Остатки ресторанов и баров, опт от 10 бутылок"),
            "reddecanter.ru": dict(nom="Ультрапремиум: Macallan M, Yamazaki 25, Dalmore 35", price="10 позиций", price_n="до 5 000 000 ₽"),
            "700ml.ru": dict(nom="Самый подробный прайс: Petrus, Louis XIII, Macallan", price="21 позиция", price_n="цены «от»"),
            "1buyup.ru": dict(nom="Macallan 25 и другой виски: рынок и потолок выкупа"),
            "skupka-alkogol.ru": dict(nom="Ценовые сегменты до «свыше 100 000 ₽»"),
            "cupajclub.ru": dict(nom="Берёт и бюджетные позиции — для элитного сегмента не профильная"),
            "alkoprikup.ru": dict(nom="Берёт и бюджетные позиции — для элитного сегмента не профильная"),
        }
    else:
        order = ["room-alco.ru", "diamant-alko.ru", "700ml.ru", "reddecanter.ru"]
        rest = [c["domain"] for c in CARDS if c["domain"] not in order]
        order += rest
        over = {
            "room-alco.ru": dict(nom="Круглосуточная оценка по фото, хранение, коробки и футляры"),
            "diamant-alko.ru": dict(nom="Остатки шампанского у ресторанов, баров и магазинов (от 10 бутылок)"),
            "700ml.ru": dict(nom="Самый подробный прайс на шампанское", price=f"{champ_count(1)} позиций", price_n="цены «от»"),
            "reddecanter.ru": dict(nom="Редкие кюве: Salon, Krug, Dom Pérignon P2", price=f"{champ_count(3)} позиции", price_n="приблизительные"),
        }
        for c in CARDS:
            if c["domain"] not in over:
                over[c["domain"]] = dict(price="Не публикует", price_n="цены на шампанское")
    out = []
    for i, d in enumerate(order, 1):
        c = by[d]
        m = dict(c["meta"])
        m.update(over.get(d, {}))
        if key == "champagne" and d in ("room-alco.ru", "diamant-alko.ru"):
            m["price"], m["price_n"] = "Не публикует", "цены на шампанское"
        out.append((c, m, i))
    return out


def topic_extra(key, depth):
    p = "../" * depth
    if key == "elite":
        seg = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td></tr>" for a, b in SEG)
        ex = [("Macallan in Lalique 55", "5 000 000 ₽", "Red Decanter, приблизительно"),
              ("Highland Park 50", "750 000 ₽", "Red Decanter, приблизительно"),
              ("Dalmore 35", "450 000 ₽", "Red Decanter, приблизительно"),
              ("Yamazaki 25", "400 000 ₽", "Red Decanter, приблизительно"),
              ("Macallan 25", "180 000 ₽ (рынок ~250 000 ₽)", "1buyup, «до»"),
              ("Macallan M Decanter", "160 000 ₽", "Red Decanter, приблизительно"),
              ("Hennessy Richard Crystal Decanter", "120 000 ₽", "SKUPKA-ALKOGOL, приблизительно"),
              ("Rémy Martin Louis XIII", "100 000 ₽", "700ml «от»; SKUPKA-ALKOGOL, приблизительно"),
              ("Petrus 2006", "200 000 ₽", "700ml, «от»")]
        exr = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in ex)
        return f"""<section class="section" id="topic">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Что считается элитным</span><h2 class="section-title">Сколько стоит<br>элитный алкоголь</h2></div>
<p class="section-copy">Граница между обычным и элитным алкоголем условна. Ориентир для выкупа — премиум-класс от 10 000 ₽ и супер-премиум свыше 100 000 ₽.</p>
</div>
<div class="two-col">
<div><h3 class="sub" style="margin-top:0">Ценовые сегменты (SKUPKA-ALKOGOL)</h3><div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Стоимость</th></tr></thead><tbody>{seg}</tbody></table></div>
<p class="note">Цифры ориентировочные, не рыночная цена и не гарантия выплаты.</p></div>
<div><h3 class="sub" style="margin-top:0">Как выбрать скупку для дорогих бутылок</h3><div class="prose">
<p>Для редких и дорогих позиций важнее всего подлинность и экспертиза. Red Decanter заявляет оценку сомелье, 700ml публикует самый подробный прайс, а одна из компаний показывает рыночную цену рядом с потолком выкупа.</p>
<p>Просите письменно зафиксировать сумму после фото и уточняйте, чем подтверждается подлинность. Для партии из нескольких бутылок запросите предложения у двух-трёх компаний из разных групп (см. «Возможно, один оператор»).</p>
<p>Упаковка важна: без оригинальной коробки цена бывает ниже до 30% (данные Red Decanter). Сохраните тубус, футляр и документы.</p></div></div>
</div>
<h3 class="sub">Примеры дорогих позиций из прайсов</h3>
<div class="table-wrap"><table class="data"><thead><tr><th>Позиция</th><th>Цена</th><th>Источник</th></tr></thead><tbody>{exr}</tbody></table></div>
<p class="note">Заявленные компаниями ориентиры, не оферта. Полный список — на странице <a class="text-link" href="{p}prices.html">«Цены выкупа»</a>.</p>
</div>
</section>
"""
    rows = "".join(f"<tr><td>{e(r[0])}</td><td class='{'dash' if r[1]=='—' else ''}'>{e(r[1])}</td><td class='{'dash' if r[3]=='—' else ''}'>{e(r[3])}</td></tr>" for r in CHAMP_ROWS)
    return f"""<section class="section" id="topic">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Цены на шампанское</span><h2 class="section-title">Сколько платят<br>за шампанское</h2></div>
<p class="section-copy">Открытые цены на шампанское публикуют только две компании из 20: 700ml и Red Decanter. У остальных сумму называют после того, как вы пришлёте фото.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Позиция</th><th>700ml (от)</th><th>Red Decanter (прибл.)</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Заявленные компаниями ориентиры, не оферта. Позиции сравнивать напрямую нельзя: у 700ml цена «от», у Red Decanter приблизительная; у Krug разные объёмы (0,75 л и 1,5 л).</p>
<h3 class="sub">От чего зависит цена шампанского</h3>
<div class="factors">
<article><h3>Кюве и бренд</h3><p>Престижные кюве — Dom Pérignon, Cristal, Krug, Salon — стоят дороже обычного брют. Розовое и позднее выпускаемое P2 оцениваются отдельно.</p></article>
<article><h3>Год и объём</h3><p>Винтаж влияет на цену: Dom Pérignon 2010 — от 16 000 ₽ у 700ml, P2 2002 — около 25 000 ₽ у Red Decanter. Большой формат дороже: Krug Grande Cuvée 1,5 л около 25 000 ₽ против 12 000 ₽ за 0,75 л.</p></article>
<article><h3>Упаковка и сохранность</h3><p>Оригинальная коробка, этикетка, капсула и проволочная уздечка без повреждений. Без коробки цена бывает ниже до 30% (данные Red Decanter).</p></article>
</div>
</div>
</section>
"""


def topic_cross(cur_key, depth):
    p = "../" * depth
    home = p or "./"
    items = [(home + "#ranking", "Где можно продать алкоголь в Москве", "Общий рейтинг 20 скупок")]
    (ROOT / "politika-konfidencialnosti.html").write_text(privacy_page(), encoding="utf-8")
    (ROOT / "politika-cookie.html").write_text(cookie_page(), encoding="utf-8")
    (ROOT / "dlya-kompanii.html").write_text(company_page_for_orgs(), encoding="utf-8")
    (ROOT / "kontakty.html").write_text(contacts_page(), encoding="utf-8")
    write_data_files()
    write_llms_txt()
    sm = [("", "1.0")] + [(tp["file"], "0.9") for tp in TOPICS] + [("prices.html", "0.8"), ("metodika.html", "0.7"), ("o-reitinge.html", "0.5"), ("dlya-kompanii.html", "0.4"), ("kontakty.html", "0.4"), ("politika-konfidencialnosti.html", "0.2"), ("politika-cookie.html", "0.2")] + [(f"c/{c['slug']}.html", "0.7") for c in CARDS]
    write_seo_files(sm)
    for tp in TOPICS:
        if tp["key"] != cur_key:
            items.append((p + tp["file"], tp["h1"].rstrip("?"), "Отдельный рейтинг"))
    items.append((p + "prices.html", "Цены выкупа алкоголя", "Сводка цен по источникам"))
    cards = "".join(f'<a class="cross" href="{h}"><strong>{e(a)}</strong><span>{e(b)} →</span></a>' for h, a, b in items)
    return f"""<section class="section"><div class="container"><h2 class="sub" style="margin-top:0">Другие рейтинги</h2><div class="cross-grid">{cards}</div></div></section>
"""


def topic_page(tp):
    rows = ranked_cards(tp["key"])
    cards_html = "".join(company_card(c, m, topic=tp["key"]) for c, m, i in rows)
    return head(tp["title"], tp["desc"], path=tp["file"], ld=[breadcrumbs(("Главная", ""), (tp["h1"].rstrip("?"), tp["file"])), itemlist([c for c, m, i in rows])]) + header() + f"""
<main id="top">
<section class="topic-hero">
<div class="container">
<span class="eyebrow">{e(tp['eyebrow'])}</span>
<h1 class="page-title">{e(tp['h1'])}</h1>
<p class="lead">{e(tp['lead'])}</p>
<div class="hero-buttons"><a href="#ranking" class="btn btn-primary">Смотреть рейтинг <span class="arrow">→</span></a><a href="#calc" class="btn btn-outline">Калькулятор выкупа</a></div>
</div>
</section>

{key_facts(None, tp['key'])}
<section class="section ranking-section" id="ranking">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Рейтинг</span><h2 class="section-title">{e(tp['nav'] if tp['key']=='champagne' else 'Скупки элитного алкоголя')}<br>в Москве</h2></div>
<p class="section-copy">{'Сравнение по открытым ценам на шампанское, скорости оценки и условиям сделки. Как составлен список — в <a class="text-link" href="metodika.html">методике</a>.' if tp['key']=='champagne' else 'Сравнение скупок дорогих и редких бутылок по скорости оценки, ценам и условиям сделки. Как составлен список — в <a class="text-link" href="metodika.html">методике</a>.'}</p>
</div>
<div class="company-list" id="rankingTable">
{cards_html}
</div>
<p class="note">Сроки оценки и режимы работы — заявления компаний. «Не публикует» значит, что цен нет на проверенных страницах сайта. Порядок компаний на этой странице составлен по профильности для темы и полноте данных, а не по качеству услуг; подробнее — в методике.</p>
</div>
</section>

{compare_section([(c, m) for c, m, i in rows])}
{topic_extra(tp['key'], 0)}
{shared_blocks()}
{topic_cross(tp['key'], 0)}
</main>
""" + footer()


# ---------------------------------------------------------------- юридические страницы и страница для организаций
def simple_page(title, desc, path, h1, lead, body, eyebrow="Документ"):
    return head(title, desc, path=path, ld=[breadcrumbs(("Главная", ""), (h1, path))]) + header() + f"""
<main id="top">
<section class="topic-hero">
<div class="container">
<span class="eyebrow">{e(eyebrow)}</span>
<h1 class="page-title">{e(h1)}</h1>
<p class="lead">{lead}</p>
</div>
</section>
<section class="section">
<div class="container narrow">
<div class="prose legal-doc">
{body}
</div>
</div>
</section>
</main>
""" + footer()


def privacy_page():
    op = f"{ph('name', 'ФИО или наименование оператора')}, ИНН {ph('inn', 'ИНН')}"
    body = f"""
<p class="note-draft">Редакция от {POLICY_DATE}. Текст подготовлен как рабочий шаблон: подставьте реквизиты оператора и согласуйте текст с юристом.</p>
<h2>1. Общие положения</h2>
<p>Настоящая политика описывает, как сайт «{SITE}» ({SITE_URL}) обрабатывает персональные данные посетителей. Оператор персональных данных — {op}, адрес для обращений: {ph('address', 'адрес')}, e-mail: {ph('email', 'e-mail')}. Политика составлена в соответствии с Федеральным законом от 27.07.2006 № 152-ФЗ «О персональных данных».</p>
<p>Сайт — информационный справочник со сравнением компаний, которые скупают алкоголь. Сайт не оказывает и не продаёт услуги и не предназначен для лиц младше 18 лет.</p>
<h2>2. Какие данные мы обрабатываем</h2>
<ul>
<li><strong>Технические данные:</strong> IP-адрес, тип браузера и устройства, адреса посещённых страниц, дата и время запроса. Они попадают в журналы сервера хостинга автоматически.</li>
<li><strong>Файлы cookie:</strong> подробности — в <a class="text-link" href="politika-cookie.html">политике cookie</a>.</li>
<li><strong>Данные из формы отзыва:</strong> имя (необязательно), оценка и текст отзыва.</li>
<li><strong>Данные из формы для организаций:</strong> название организации, сайт, имя контактного лица, e-mail, текст обращения, ссылки на подтверждающие материалы.</li>
<li><strong>Письма на e-mail</strong>: данные, которые вы указали в письме.</li>
</ul>
<p>Мы просим не указывать в отзывах и обращениях лишнего: номера документов, банковские данные, адреса и телефоны третьих лиц.</p>
<h2>3. Цели обработки</h2>
<ul>
<li>публикация отзывов читателей после проверки;</li>
<li>рассмотрение обращений организаций об исправлении данных и претензий;</li>
<li>обеспечение работы и безопасности сайта;</li>
<li>ответы на ваши письма и запросы.</li>
</ul>
<h2>4. Основание обработки</h2>
<p>Обработка осуществляется с вашего согласия, которое вы даёте, отправляя форму и отмечая согласие, а также в случаях, предусмотренных законом. Согласие можно отозвать, написав на {ph('email', 'e-mail')}.</p>
<h2>5. Передача данных третьим лицам</h2>
<p>Мы не продаём персональные данные. Данные могут обрабатываться провайдером хостинга, на серверах которого размещён сайт. Для отображения шрифтов браузер посетителя обращается к сервису Google Fonts, при этом сервису передаются IP-адрес и сведения о браузере. Оператор вправе раскрыть данные по обоснованному запросу уполномоченных органов.</p>
<h2>6. Хранение</h2>
<p>Данные хранятся не дольше, чем необходимо для целей обработки. Опубликованный отзыв остаётся на сайте, пока вы не попросите его удалить или изменить. Обращения организаций хранятся на время рассмотрения и ещё столько, сколько нужно для подтверждения принятых решений.</p>
<h2>7. Ваши права</h2>
<p>Вы можете запросить сведения о том, какие ваши данные мы обрабатываем, потребовать уточнить, заблокировать или удалить их, а также отозвать согласие. Для этого напишите на {ph('email', 'e-mail')}. Мы ответим в сроки, установленные законом. Вы также вправе обратиться в Роскомнадзор.</p>
<h2>8. Защита данных</h2>
<p>Мы принимаем организационные и технические меры для защиты данных от случайного или неправомерного доступа, изменения, раскрытия и уничтожения.</p>
<h2>9. Изменения политики</h2>
<p>Актуальная редакция всегда размещена на этой странице. Если мы начнём использовать новые инструменты (например, сервис веб-аналитики), политика будет обновлена до их запуска.</p>
<h2>10. Контакты</h2>
<p>{op}<br>Адрес: {ph('address', 'адрес')}<br>E-mail: {ph('email', 'e-mail')}</p>
"""
    return simple_page(f"Политика конфиденциальности — {SITE}", "Как сайт обрабатывает персональные данные посетителей: состав данных, цели, права пользователей и контакты оператора.",
                       "politika-konfidencialnosti.html", "Политика конфиденциальности", "Как мы обрабатываем персональные данные посетителей сайта.", body)


def cookie_page():
    body = f"""
<p class="note-draft">Редакция от {POLICY_DATE}. Список cookie соответствует текущей версии сайта; при подключении аналитики или рекламы его нужно обновить до запуска.</p>
<h2>Что такое cookie</h2>
<p>Cookie — небольшие файлы, которые сайт сохраняет в вашем браузере. Они помогают запомнить ваши действия, например то, что вы уже ответили на вопрос о cookie.</p>
<h2>Какие cookie использует сайт</h2>
<div class="table-wrap"><table class="data"><thead><tr><th>Название</th><th>Назначение</th><th>Срок</th><th>Тип</th></tr></thead><tbody>
<tr><td>cookie_consent</td><td>Запоминает, что вы нажали «Согласен» в плашке о cookie, чтобы не показывать её повторно. Дублируется в localStorage браузера.</td><td>12 месяцев</td><td>Необходимый, собственный</td></tr>
</tbody></table></div>
<p>Других cookie сайт сейчас не устанавливает. Сервисы веб-аналитики и рекламные сети на сайте не подключены.</p>
<h2>Сторонние сервисы</h2>
<p>Для отображения шрифтов браузер обращается к сервису Google Fonts. Сам сервис не требует cookie, но получает ваш IP-адрес и сведения о браузере. Подробнее — в <a class="text-link" href="politika-konfidencialnosti.html">политике конфиденциальности</a>.</p>
<h2>Как управлять cookie</h2>
<p>Вы можете удалить cookie или запретить их сохранение в настройках браузера. Если удалить cookie_consent, плашка появится снова. Отключение необходимых cookie не влияет на работу сайта.</p>
<h2>Если мы подключим аналитику</h2>
<p>Мы запустим её только после вашего согласия и заранее добавим её cookie в эту таблицу.</p>
<h2>Контакты</h2>
<p>По вопросам об обработке данных: {ph('email', 'e-mail')}. Оператор: {ph('name', 'ФИО или наименование оператора')}.</p>
"""
    return simple_page(f"Политика cookie — {SITE}", "Какие файлы cookie использует сайт, зачем они нужны и как ими управлять.",
                       "politika-cookie.html", "Политика cookie", "Какие cookie использует сайт и как ими управлять.", body)


def company_page_for_orgs():
    body = f"""
<p>Рейтинг составлен по открытым данным, и в нём могут быть ошибки или устаревшие сведения. Если вы представляете организацию из рейтинга, напишите нам: мы проверим сведения и при необходимости исправим карточку.</p>
<h2>С чем можно обратиться</h2>
<ul>
<li>неверные или устаревшие контакты, адрес, режим работы, сроки оценки;</li>
<li>неверные цены или условия сделки;</li>
<li>ошибки в тексте обзора: факты, которые можно проверить;</li>
<li>претензии к опубликованным материалам.</li>
</ul>
<h2>Как мы рассматриваем обращения</h2>
<ol class="steps-list">
<li>Вы отправляете форму ниже или пишете на {ph('email', 'e-mail')}. Укажите, что именно неверно, и приложите ссылку на страницу сайта, документ или другое подтверждение.</li>
<li>Мы проверяем сведения по открытым источникам и отвечаем в течение {CLAIM_DAYS} рабочих дней.</li>
<li>Если ошибка подтверждена, исправляем данные и при необходимости пересчитываем оценку. Если не подтверждена, объясняем почему.</li>
<li>По вашей просьбе мы можем опубликовать краткий ответ компании в карточке.</li>
</ol>
<h2>Что мы не меняем</h2>
<ul>
<li>Оценку, которая рассчитана по формуле из <a class="text-link" href="metodika.html#score">методики</a>, если сведения, на которых она основана, верны.</li>
<li>Мнения и выводы обзоров, основанные на проверяемых фактах: оценочные суждения мы не удаляем по просьбе компании.</li>
<li>Заявления компаний о самих себе («5000 сделок», «до 90% рынка»): мы лишь указываем, что это заявления, и не проверяем их.</li>
</ul>
<h2>Форма обращения</h2>
<form class="org-form" id="claimForm" data-endpoint="{e(CLAIM_ENDPOINT)}">
<label class="lbl">Название организации<input class="field" name="company" required maxlength="120"></label>
<label class="lbl">Сайт организации<input class="field" name="site" type="url" placeholder="https://" required maxlength="200"></label>
<label class="lbl">Контактное лицо<input class="field" name="contact" required maxlength="120" autocomplete="name"></label>
<label class="lbl">E-mail для ответа<input class="field" name="email" type="email" required maxlength="120" autocomplete="email"></label>
<label class="lbl">Тип обращения<select class="field" name="kind" required><option value="">Выберите</option><option>Исправить контакты, адрес, режим</option><option>Исправить цены или условия</option><option>Ошибка в обзоре</option><option>Претензия</option><option>Другое</option></select></label>
<label class="lbl">Что нужно исправить<textarea class="field" name="text" rows="6" required maxlength="3000"></textarea></label>
<label class="lbl">Ссылка на подтверждение<input class="field" name="proof" type="url" placeholder="https://" maxlength="300"></label>
<label class="check"><input type="checkbox" name="consent" required><span>Я согласен(на) на обработку персональных данных в соответствии с <a class="text-link" href="politika-konfidencialnosti.html">политикой конфиденциальности</a>.</span></label>
<p class="muted" id="claimMsg" role="status"></p>
<button class="btn btn-primary" type="submit">Отправить обращение <span class="arrow">→</span></button>
</form>
<p class="note">Если форма не открывается или вы предпочитаете письмо, напишите на {ph('email', 'e-mail')}.</p>
"""
    return simple_page(f"Для организаций: исправить данные и направить претензию — {SITE}", "Страница для компаний из рейтинга: как исправить данные в карточке, направить претензию и получить ответ.",
                       "dlya-kompanii.html", "Для организаций", "Нашли ошибку в карточке вашей компании? Расскажите, мы проверим и исправим.", body, eyebrow="Обратная связь")


def contacts_page():
    body = f"""
<p>Сайт «{SITE}» — независимый справочник и не оказывает услуг по скупке алкоголя. Через эту страницу можно связаться с редакцией.</p>
<h2>Редакция</h2>
<p>Оператор сайта: {ph('name', 'ФИО или наименование оператора')}<br>ИНН: {ph('inn', 'ИНН')}<br>Адрес для обращений: {ph('address', 'адрес')}<br>E-mail: {ph('email', 'e-mail')}</p>
<h2>По какому вопросу писать</h2>
<ul>
<li><strong>Вы представляете компанию из рейтинга</strong> и нашли ошибку или хотите направить претензию — <a class="text-link" href="dlya-kompanii.html">страница для организаций</a>.</li>
<li><strong>Вы читатель</strong> и хотите сообщить об ошибке в данных или поделиться опытом сделки — напишите на e-mail редакции.</li>
<li><strong>Вопросы о персональных данных</strong> (доступ, удаление, отзыв согласия) — на тот же e-mail, см. <a class="text-link" href="politika-konfidencialnosti.html">политику конфиденциальности</a>.</li>
</ul>
<p class="note">Мы не покупаем алкоголь и не принимаем бутылки: по вопросам продажи обращайтесь напрямую в выбранную компанию.</p>
"""
    return simple_page(f"Контакты — {SITE}", "Как связаться с редакцией рейтинга скупок алкоголя: реквизиты оператора, e-mail и страница для организаций.",
                       "kontakty.html", "Контакты", "Как связаться с редакцией.", body, eyebrow="Связь")


def company_records():
    out = []
    for c in CARDS:
        p, total = scores(c)
        phone, email, addr, msg = FACTS[c["domain"]]
        rng, rng_note = price_range(c)
        r = REVIEWS[c["domain"]]
        out.append({
            "name": c["name"], "domain": c["domain"], "site": f"https://{c['domain']}", "page": f"{SITE_URL}/c/{c['slug']}.html",
            "hours": mode_of(c), "address": None if addr == ND else addr, "phone": phone, "email": email or None, "messengers": msg or None,
            "speed_claim": c["speed"], "prices_claim": c["prices"], "price_range": rng, "price_range_note": rng_note,
            "possible_same_operator": c["cluster"],
            "editorial_score": {"total": total, "price_transparency": p["price"], "speed_convenience": p["speed"], "openness": p["trust"], "scale": "1-5"},
            "summary": r["lead"], "pros": r["pros"], "cons": r["cons"], "verdict": r["verdict"],
        })
    return out


def write_data_files():
    import csv, io, json
    d = ROOT / "data"
    d.mkdir(exist_ok=True)
    recs = company_records()
    meta = {"title": f"{SITE}: рейтинг скупок элитного алкоголя в Москве", "url": SITE_URL + "/", "data_collected": "2026-09-30",
            "note": "Заявления компаний, не оферта; информация справочная и может быть устаревшей. Оценка редакции рассчитана по открытым данным (см. методику).",
            "methodology": f"{SITE_URL}/metodika.html", "companies": recs}
    (d / "companies.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name", "site", "page", "hours", "address", "phone", "email", "speed_claim", "price_range", "score_total", "score_price", "score_speed", "score_openness"])
    for r in recs:
        sc = r["editorial_score"]
        w.writerow([r["name"], r["site"], r["page"], r["hours"], r["address"] or "", r["phone"], r["email"] or "", r["speed_claim"], r["price_range"], sc["total"], sc["price_transparency"], sc["speed_convenience"], sc["openness"]])
    (d / "companies.csv").write_text("\ufeff" + buf.getvalue(), encoding="utf-8")


def write_llms_txt():
    lines = [f"# {SITE} — рейтинг скупок элитного и коллекционного алкоголя в Москве", "",
             "> Сравнение 20 компаний, которые скупают коньяк, виски, вино, шампанское и другой коллекционный алкоголь: скорость оценки по фото, открытые цены, условия сделки, плюсы и минусы, оценка редакции по трём параметрам. Сайт не оказывает и не продаёт услуги; информация справочная и может быть устаревшей, точные данные — на сайтах компаний. Данные собраны 30.09.2026.", "",
             "## Основные страницы", "",
             f"- [Где можно продать алкоголь в Москве]({SITE_URL}/): рейтинг и сравнительная таблица 20 компаний",
             f"- [{TOPICS[0]['h1'].rstrip('?')}]({SITE_URL}/{TOPICS[0]['file']}): скупки дорогих и редких бутылок",
             f"- [{TOPICS[1]['h1'].rstrip('?')}]({SITE_URL}/{TOPICS[1]['file']}): цены на шампанское и компании, которые его покупают",
             f"- [Цены выкупа]({SITE_URL}/prices.html): сводка опубликованных цен по четырём компаниям",
             f"- [Методика]({SITE_URL}/metodika.html): источники, правила оценки, ограничения",
             f"- [О рейтинге]({SITE_URL}/o-reitinge.html): миссия и принципы",
             f"- [Для организаций]({SITE_URL}/dlya-kompanii.html): как исправить данные или направить претензию", "",
             "## Данные для машинной обработки", "",
             f"- [companies.json]({SITE_URL}/data/companies.json): все компании, оценки, диапазоны цен, обзоры",
             f"- [companies.csv]({SITE_URL}/data/companies.csv): то же в табличном виде", "",
             "## Компании", ""]
    for c in CARDS:
        lines.append(f"- [{c['name']}]({SITE_URL}/c/{c['slug']}.html): {REVIEWS[c['domain']]['lead'].rstrip('.')} (оценка редакции {scores(c)[1]:g} из 5)")
    (ROOT / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User",
           "Google-Extended", "Applebot-Extended", "CCBot", "YandexBot", "YandexAdditional", "Googlebot", "Bingbot"]


def postprocess(html):
    """Семантика таблиц: scope у заголовков."""
    html = re.sub(r"(<thead>.*?</thead>)", lambda m: m.group(1).replace("<th>", '<th scope="col">'), html, flags=re.S)
    html = re.sub(r"(<table class=\"facts-table\">.*?</table>)", lambda m: m.group(1).replace("<th>", '<th scope="row">'), html, flags=re.S)
    return html


def write_seo_files(pages):
    urls = "\n".join(
        f"<url><loc>{SITE_URL}/{p}</loc><lastmod>{BUILD_DATE}</lastmod><priority>{pr}</priority></url>" for p, pr in pages)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n', encoding="utf-8")
    bots = "".join(f"User-agent: {b}\nAllow: /\n\n" for b in AI_BOTS)
    (ROOT / "robots.txt").write_text(f"# Поисковые и ИИ-краулеры допускаются явно; служебные папки закрыты для всех\n{bots}User-agent: *\nAllow: /\nDisallow: /standalone/\nDisallow: /tools/\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")


def main():
    (ROOT / "index.html").write_text(index_page(), encoding="utf-8")
    (ROOT / "prices.html").write_text(prices_page(), encoding="utf-8")
    (ROOT / "metodika.html").write_text(methodology_page(), encoding="utf-8")
    (ROOT / "o-reitinge.html").write_text(about_page(), encoding="utf-8")
    for tp in TOPICS:
        (ROOT / tp["file"]).write_text(topic_page(tp), encoding="utf-8")
    (ROOT / "c").mkdir(exist_ok=True)
    write_covers()
    for i, c in enumerate(CARDS):
        (ROOT / "c" / f"{c['slug']}.html").write_text(company_page(c, i), encoding="utf-8")
    print("ok:", len(CARDS), "компаний,", len(PRICES), "строк цен,", len(RUM), "ром/арманьяк,", len(SEG), "сегментов")


if __name__ == "__main__":
    main()
    for f in list(ROOT.glob("*.html")) + list((ROOT / "c").glob("*.html")):
        f.write_text(postprocess(f.read_text(encoding="utf-8")), encoding="utf-8")
