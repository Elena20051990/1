#!/usr/bin/env python3
"""Собирает статический сайт-рейтинг из tools/niche.txt (текст анализа ниши).

Запуск:  python3 tools/build.py
Результат: index.html, prices.html, c/<slug>.html в корне репозитория.
Стили лежат в assets/style.css.
"""
import html
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TXT = (ROOT / "tools" / "niche.txt").read_text(encoding="utf-8")
LINES = [html.unescape(l).rstrip() for l in TXT.split("\n")]

# ---- Настройки, которые нужно заполнить перед запуском -------------------------------------------
SITE_URL = "https://drink-guru.ru"   # адрес сайта без слеша в конце (нужен для canonical, sitemap, robots, og)
OPERATOR = dict(                      # оператор персональных данных (подставляется в политики и на страницу «Для компаний»)
    name="",      # ФИО или название организации/ИП
    inn="",       # необязательно: если пусто — ИНН нигде не показывается
    address="",   # необязательно: адрес редакции для обращений; если пусто — нигде не показывается
    email="support@drink-guru.ru",     # e-mail для обращений
    phone="",     # необязательно: показывается только если заполнено
    telegram="",  # Telegram редакции, например @editor
)
# Как подключать шапку и подвал: "inline" — блок вставляется в каждую страницу при сборке (работает на любом хостинге);
# "ssi" — на страницах стоит директива <!--#include virtual="/includes/header.html" --> (нужна поддержка SSI на сервере и размещение в корне домена).
# Файлы includes/header.html и includes/footer.html создаются при любом режиме.
INCLUDE_MODE = os.environ.get("INCLUDE_MODE", "ssi")
# Индексация: False — сайт закрыт (meta noindex, robots.txt Disallow: /, заголовок X-Robots-Tag через .htaccess). Для открытия поставьте True и пересоберите.
ALLOW_INDEXING = True

# Автор и эксперт сайта. Блок показывается только при show=True и только когда вы подтвердили реальные сведения:
# имя и фото используются с согласия человека, должность и квалификация подтверждаются документами.
EXPERT = dict(
    show=True,
    name="Владимир Андреевич Назаров",
    role="Сомелье · Винный эксперт · Консультант по премиальным винам",
    about='Владимир Назаров — опытный специалист в области винной культуры, профессиональной дегустации и ресторанной гастрономии. На протяжении своей карьеры он изучает особенности мирового виноделия, работает с коллекционными винами и помогает ценителям ориентироваться в многообразии винных стилей и производителей.\n\nПрофессиональный путь Владимира связан с развитием ресторанной индустрии и формированием винных коллекций. За годы практики он приобрёл опыт составления винных карт для заведений высокого уровня, подбора напитков к авторской кухне и консультирования частных клиентов по вопросам приобретения редких и выдержанных вин.\n\nОсновное направление его экспертизы — вина Франции, Италии, Испании и Германии. Особый интерес Владимир проявляет к классическим винодельческим хозяйствам, винтажным винам и влиянию терруара на вкусовые характеристики напитка. При оценке вина он учитывает происхождение, особенности урожая, методы производства, потенциал выдержки и гастрономическую сочетаемость.\n\nПомимо консультационной деятельности, Владимир занимается организацией профессиональных дегустаций и тематических винных мероприятий. Он помогает участникам глубже понять особенности различных сортов винограда, научиться распознавать ароматические профили и осознанно выбирать вина в соответствии с личными предпочтениями.\n\nОтдельное место в его работе занимает формирование частных винных собраний. Владимир консультирует по вопросам подбора бутылок, условий хранения, оптимальных сроков употребления и долгосрочного планирования коллекции.\n\nВ своей профессиональной деятельности он придерживается аналитического подхода, сочетая внимание к деталям с глубоким уважением к традициям виноделия. Для него вино — это не просто напиток, а отражение истории региона, мастерства производителя и культуры, в которой оно создаётся.',
    credentials="Профессиональный опыт: 20 лет · Москва, Россия",
    photo="assets/expert.jpg",   # фото эксперта; без файла блок показывается без фото
    disclosure="",   # раскрытие связей эксперта с компаниями рейтинга: заполнить после подтверждения
)


PLACEMENT_IS_FREE = True              # True — только если размещение компаний в рейтинге бесплатно и вы не получаете от них вознаграждения (тогда это попадает в методику и редакционную политику)
AGE_GATE = True                       # окно «Вам исполнилось 18 лет?» при первом визите
CLAIM_DAYS = 10                       # срок рассмотрения обращений организаций, рабочих дней (подтвердите, что успеваете)
REVIEW_ENDPOINT = "/send.php?type=review"                  # куда отправлять отзывы читателей (JSON, POST); пусто — форма сообщает, что не подключена
FEEDBACK_ENDPOINT = "/send.php?type=feedback"            # куда отправлять сообщения из формы обратной связи (JSON, POST)
CLAIM_ENDPOINT = "/send.php?type=claim"                   # куда отправлять обращения организаций (JSON, POST)
GOOGLE_VERIFY = ""                    # содержимое meta google-site-verification (Search Console)
YANDEX_VERIFY = ""
YM_ID = ""                   # номер счётчика Яндекс Метрики (пусто — счётчик не подключается)                    # содержимое meta yandex-verification (Яндекс Вебмастер)
BUILD_DATE = "2026-10-10"             # дата для sitemap (lastmod)
POLICY_DATE = "10 октября 2026 г."
# --------------------------------------------------------------------------------------------------

SITE = "drink-guru.ru"
SITE_SUB = "Рейтинг скупок алкоголя"
LOGO = SITE.split(".")[0] + "<i>." + SITE.split(".", 1)[1] + "</i>"
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
OWN = set()  # компании, связанные с владельцем сайта (если такие есть, их нужно раскрыть на сайте)


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


def opt(key, fmt):
    """Необязательный реквизит: пусто, пока не заполнен в OPERATOR."""
    v = OPERATOR.get(key, "")
    return fmt.format(e(v)) if v else ""


def jsonld(*objs):
    import json
    return "\n".join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False).replace("</", "<\\/") + "</script>" for o in objs if o)


def breadcrumbs(*items):
    """items — [(название, путь)] от главной; путь относительно корня сайта."""
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": f"{SITE_URL}/{pth}"} for i, (n, pth) in enumerate(items, 1)]}


CHOICES = [
 [
  "Одна подаренная бутылка",
  "Подарок можно оценить без поездок: пришлите чёткие фото в мессенджер или через форму и сравните два-три ответа. Встречу назначайте, только когда сумма устроила, а условия расчёта обсуждены. Если вы живёте не в Москве, спросите об отправке."
 ],
 [
  "Редкий экземпляр или лимитированная серия",
  "Для таких бутылок ищите компании, где оценивает сомелье и есть открытые цены. Назовите год, регион производства и состояние. Здесь знания оценщика важнее скорости: цену способна сдвинуть даже небольшая разница в уровне жидкости или этикетке."
 ],
 [
  "Большая коллекция",
  "Попросите оценку списком и заранее выясните порядок вывоза, договор и способ расчёта. Партнёра проверьте по реквизитам, а условия по объёму и срокам обсудите до осмотра."
 ],
 [
  "Остатки ресторана, бара или магазина",
  "Присмотритесь к оптовым предложениям: у некоторых компаний опт начинается от 10 бутылок, а к нему прилагается инвентаризация на месте. Выгодные условия для партии обычно обсуждаются отдельно."
 ],
 [
  "Нужны деньги срочно",
  "Выбирайте тех, кто отвечает за несколько минут и работает допоздна. Писать можно в несколько мест сразу, но соглашайтесь только на зафиксированную цену: спешка не должна влиять на сумму."
 ],
 [
  "Бутылки в другом городе",
  "Из регионов бутылки отправляют транспортной компанией; уточните, кто отвечает за доставку и упаковку. По Москве и области часть компаний выезжает в течение дня. Безопаснее то предложение, где обмен документами и деньгами прозрачен."
 ],
 [
  "Хочу прикинуть сумму",
  "Начните с калькулятора и таблицы цен, а затем пишите в компании. Так проще отличить реалистичное предложение от завышенного обещания."
 ],
 [
  "Старая или современная бутылка",
  "У современной главное — упаковка и аккуратный вид, у старой — год, уровень и сохранность. Известный производитель и востребованная позиция повышают интерес, а спрос на редкие вещи растёт быстрее, чем на массовые."
 ],
 [
  "Пока не решил(а), продавать ли",
  "Это нормально. Оценку по фото можно получить и бутылку оставить себе: решение остаётся за вами, а рейтинг никого к продаже не склоняет."
 ]
]


def choice_section():
    rows = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td></tr>" for a, b in CHOICES)
    return f"""<section class="section ranking-section" id="choice">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Под вашу задачу</span><h2 class="section-title">Что кому<br>подойдёт</h2></div>
<p class="section-copy">У каждого своя задача, поэтому и выбирать нужно по-разному. Подарочная бутылка, наследство, остатки бара — ситуации разные, и условие, которое выручает в одной, в другой оказывается лишним. Проверяемых данных в этой сфере немного, поэтому расскажите компании все нюансы и сравните ответы.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Ситуация</th><th>Что учесть при выборе</th></tr></thead><tbody>{rows}</tbody></table></div>
</div>
</section>
"""


def key_facts(rows, topic=None):
    """Блок «Коротко»: факты из данных в виде короткого списка (удобно людям и ИИ-краулерам)."""
    priced = [c["name"] for c in CARDS if c["meta"]["price"] not in ("Не публикует", "Не проверено")]
    top = max(CARDS, key=lambda c: scores(c)[1])
    fast = [c for c in CARDS if SCORE_INPUT[c["domain"]]["speed_min"] is not None]
    quick = min(fast, key=lambda c: SCORE_INPUT[c["domain"]]["speed_min"])
    slow = max(fast, key=lambda c: SCORE_INPUT[c["domain"]]["speed_min"])
    items = [f"В рейтинге **{len(CARDS)} компаний**; цены открыто публикуют только **{len(priced)}**: {', '.join(priced)}."]
    if topic == "whisky":
        n = [x for r in WHISKY_ROWS for x in _nums(r[1])]
        items.append(f"Цены на виски публикуют **три компании**: 700ml (от {fmt_rub(min(n))} до {fmt_rub(max(n))} ₽, цены «от»), 1buyup (рынок и потолок выкупа по шести позициям) и Red Decanter (приблизительные цены на редкие бутылки).")
    elif topic == "elite":
        items.append("Для дорогих и редких бутылок подходят **Red Decanter** (в прайсе до 5 000 000 ₽), 700ml (до 200 000 ₽, Petrus) и SKUPKA-ALKOGOL (сегменты до «свыше 100 000 ₽»).")
    items.append("Обычный уровень выкупа — **67–72% рыночной цены** по опубликованным таблицам; обещания «до 90%» и «до 100%» — **реклама**, а не норма.")
    items.append(f"Первый ответ по фото: быстрее всех — **{quick['meta']['speed'].lower()}** ({quick['name']}), медленнее всех — **{slow['meta']['speed'].lower()}** ({slow['name']}).")
    items.append(f"Наивысшая оценка редакции — **{scores(top)[1]:g} из 5** ({top['name']}); она складывается из трёх параметров, правила описаны в методике.")
    items.append("Часть сайтов, **вероятно, принадлежит одному оператору**: 700ml, Alko Lombard и oldcognac; Red Decanter и SKUPKA-ALKOGOL; Cupaj Club и Alko Prikup.")
    li = "".join("<li>" + re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e(x)) + "</li>" for x in items)
    return f"""<section class="section keyfacts" id="summary-short"><div class="container narrow"><h2 class="sub" style="margin-top:0">Коротко</h2><ul class="goals">{li}</ul></div></section>
"""


def itemlist(cards):
    return {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": c["name"], "url": f"{SITE_URL}/c/{c['slug']}.html"} for i, c in enumerate(cards, 1)]}


def faq_ld(items=None):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in (items or FAQ)]}


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


import hashlib
# версия ресурсов в адресе: после правки стилей браузеры и кэш хостинга подтянут свежие файлы
ASSET_V = hashlib.md5(((ROOT / "assets" / "style.css").read_bytes() + (ROOT / "assets" / "site.js").read_bytes())).hexdigest()[:8]

YM_SCRIPT = """<!-- Yandex.Metrika counter -->
<script type="text/javascript">
    (function(m,e,t,r,i,k,a){
        m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
        m[i].l=1*new Date();
        for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
        k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
    })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=__ID__', 'ym');

    ym(__ID__, 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer", referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
</script>
<!-- /Yandex.Metrika counter -->
"""
YM_NOSCRIPT = '<noscript><div><img src="https://mc.yandex.ru/watch/__ID__" style="position:absolute; left:-9999px;" alt="" /></div></noscript>\n'


def head(title, desc, depth=0, path="", ld=None):
    p = "../" * depth
    url = f"{SITE_URL}/{path}"
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "url": SITE_URL + "/", "inLanguage": "ru"}
    org = {"@context": "https://schema.org", "@type": "Organization", "name": SITE, "url": SITE_URL + "/", "logo": f"{SITE_URL}/assets/og.png"}
    if OPERATOR.get("email"):
        org["email"] = OPERATOR["email"]
        org["contactPoint"] = {"@type": "ContactPoint", "contactType": "customer support", "email": OPERATOR["email"], "availableLanguage": "ru"}
    if OPERATOR.get("address"):
        org["address"] = OPERATOR["address"]
    page_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": url, "description": desc, "inLanguage": "ru",
               "dateModified": BUILD_DATE, "isPartOf": {"@type": "WebSite", "name": SITE, "url": SITE_URL + "/"}, "publisher": {"@type": "Organization", "name": SITE}}
    verify = (f'<meta name="google-site-verification" content="{e(GOOGLE_VERIFY)}">\n' if GOOGLE_VERIFY else "") + (f'<meta name="yandex-verification" content="{e(YANDEX_VERIFY)}">\n' if YANDEX_VERIFY else "")
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{"noindex, follow" if path in NOINDEX_PAGES else ROBOTS_META}">
<meta name="theme-color" content="#8a2b34">
<link rel="canonical" href="{url}">
{verify}<link rel="alternate" type="application/json" href="{SITE_URL}/data/companies.json" title="Данные рейтинга (JSON)">
<link rel="icon" href="{p}assets/favicon.png" type="image/png">
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
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,500;1,700&family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}assets/style.css?v={ASSET_V}">
{jsonld(site_ld, org, page_ld, *(ld or []))}
{YM_SCRIPT.replace("__ID__", YM_ID) if YM_ID else ""}</head>
<body>
{YM_NOSCRIPT.replace("__ID__", YM_ID) if YM_ID else ""}"""


# Меню шапки: (подпись, ссылка). Ссылка на якорь главной начинается с «#», остальные — файлы в корне.
NAV = [
    ("Скупка алкоголя", "#ranking"),
    ("Элитный алкоголь", "gde-prodat-elitnyy-alkogol.html"),
    ("Виски", "gde-prodat-viski.html"),
    ("Цены выкупа", "prices.html"),
    ("Как продать", "#prepare"),
    ("Методика", "metodika.html"),
    ("Эксперт", "o-reitinge.html#author"),
    ("Контакты", "kontakty.html"),
]
NAV_TITLES = {
    "#ranking": "Скупка алкоголя в Москве: сравнение компаний, которые выкупают коньяк, виски, вино и шампанское",
    "gde-prodat-elitnyy-alkogol.html": "Где продать элитный и коллекционный алкоголь: редкие бутылки, винтажные позиции, шампанское",
    "gde-prodat-viski.html": "Где продать виски: выдержка, серии, упаковка и ориентиры по цене выкупа",
    "prices.html": "Цены выкупа и стоимость бутылок: опубликованные ориентиры скупок",
    "#prepare": "Как продать бутылку: фото этикетки, пробки и упаковки, сохранность и условия хранения",
    "metodika.html": "Методика рейтинга: критерии, данные и расчёт оценки",
    "o-reitinge.html#author": "Эксперт сайта: опыт, подход к оценке и независимость рейтинга",
    "kontakty.html": "Контакты редакции: Telegram, e-mail, вопросы и сообщения для компаний",
}


def contact_short():
    parts = []
    if OPERATOR.get("telegram"):
        parts.append(f'<a href="https://t.me/{e(OPERATOR["telegram"].lstrip("@"))}" rel="nofollow">Telegram {e(OPERATOR["telegram"])}</a>')
    if OPERATOR.get("email"):
        parts.append(f'<a href="mailto:{e(OPERATOR["email"])}">{e(OPERATOR["email"])}</a>')
    return " · ".join(parts)


def header_inline(depth=0, base=None):
    p = base if base else "../" * depth
    home = base if base else (p or "./")
    links = "\n".join(f'<a href="{home + h if h.startswith("#") else p + h}" title="{e(NAV_TITLES[h])}">{e(l)}</a>' for l, h in NAV)
    return f"""<div class="topbar"><div class="container topbar-inner">
<p>Куда продать коньяк, виски, вино и шампанское в Москве и Московской области: сравниваем условия, сроки оценки и цены выкупа.</p>
<p class="topbar-contact">Связь с редакцией: {contact_short()}</p>
</div></div>
<header class="header" id="header">
<div class="container header-inner">
<a href="{home}" class="nav-logo" aria-label="{SITE} — главная страница" title="Главная: рейтинг скупок алкоголя"><span>{LOGO}</span><span class="nav-logo-sub">Рейтинг скупок алкоголя</span></a>
<span class="age-badge" title="Сайт для лиц старше 18 лет">18+</span>
<nav class="nav-links" id="navLinks" aria-label="Главная навигация">
{links}
</nav>
<div class="header-actions">
<a href="{home}#calc" class="btn btn-primary header-cta" title="Оценить стоимость бутылки: калькулятор выкупа">Оценить стоимость <span class="arrow">→</span></a>
<button class="menu-btn" id="menuBtn" type="button" aria-label="Меню" aria-expanded="false" aria-controls="navLinks">☰</button>
</div>
</div>
</header>
"""


def header(depth=0):
    return '<!--#include virtual="/includes/header.html" -->\n' if INCLUDE_MODE == "ssi" else header_inline(depth)


def footer(depth=0):
    return '<!--#include virtual="/includes/footer.html" -->\n' if INCLUDE_MODE == "ssi" else footer_inline(depth)


def write_includes():
    d = ROOT / "includes"
    d.mkdir(exist_ok=True)
    (d / "header.html").write_text(header_inline(base="/"), encoding="utf-8")
    (d / "footer.html").write_text(footer_inline(base="/"), encoding="utf-8")


def expert_ld():
    if not EXPERT["show"]:
        return None
    d = {"@context": "https://schema.org", "@type": "Person", "name": EXPERT["name"], "jobTitle": EXPERT["role"], "url": SITE_URL + "/o-reitinge.html"}
    if EXPERT["about"]:
        d["description"] = EXPERT["about"]
    return d


def expert_note(depth=0):
    """Подпись под разделами о вине: их прочитал эксперт."""
    if not EXPERT["show"]:
        return ""
    p = "../" * depth
    return f'<p class="expert-note">Эксперт сайта: <a href="{p}o-reitinge.html#author">{e(EXPERT["name"])}</a>, {e(EXPERT["role"].split(" · ")[0].lower())}.</p>'


def expert_block(depth=0):
    """Карточка автора и эксперта; пусто, пока EXPERT['show'] = False."""
    if not EXPERT["show"]:
        return ""
    p = "../" * depth
    photo = ""
    if (ROOT / EXPERT["photo"]).exists():
        photo = f'<img class="ex-photo" src="{p}{EXPERT["photo"]}" alt="{e(EXPERT["name"])}" width="160" height="160" loading="lazy">'
    about = "".join(f"<p>{e(t)}</p>" for t in EXPERT["about"].split("\n\n")) if EXPERT["about"] else f"<p>{ph('name', 'коротко об опыте автора')}</p>"
    cred = f"<p class=\"ex-cred\">{e(EXPERT['credentials'])}</p>" if EXPERT["credentials"] else ""
    disc = f"<p class=\"ex-disc\">{e(EXPERT['disclosure'])}</p>" if EXPERT["disclosure"] else f"<p class=\"ex-disc\">{ph('name', 'раскройте связь автора с оцениваемыми компаниями и платные услуги автора, если они есть')}</p>"
    return f"""<section class="expert" id="author"><div class="ex-card">{photo}<div><span class="eyebrow">Эксперт сайта</span><h2 class="ex-name">{e(EXPERT['name'])}</h2><p class="ex-role">{e(EXPERT['role'])}</p>{about}{cred}{disc}</div></div></section>
"""


def contact_line():
    parts = []
    if OPERATOR.get("phone"):
        parts.append(f"телефон {e(OPERATOR['phone'])}")
    if OPERATOR.get("telegram"):
        parts.append(f"Telegram {e(OPERATOR['telegram'])}")
    if OPERATOR.get("email"):
        parts.append(f"e-mail {e(OPERATOR['email'])}")
    return f"<p>Связаться с редакцией: {', '.join(parts)}.</p>" if parts else ""


def footer_contacts():
    """Блок «Контакты» в подвале: e-mail (и телефон, Telegram, если заданы) крупно и со ссылкой."""
    items = []
    if OPERATOR.get("email"):
        items.append(f'<a class="footer-mail" href="mailto:{e(OPERATOR["email"])}">{e(OPERATOR["email"])}</a>')
    if OPERATOR.get("phone"):
        items.append(f'<a class="footer-mail" href="tel:{e(re.sub(r"[^+0-9]", "", OPERATOR["phone"]))}">{e(OPERATOR["phone"])}</a>')
    if OPERATOR.get("telegram"):
        items.append(f'<a class="footer-mail" href="https://t.me/{e(OPERATOR["telegram"].lstrip("@"))}">Telegram {e(OPERATOR["telegram"])}</a>')
    if not items:
        return ""
    return '<h3 class="footer-title footer-title-next">Контакты</h3><div class="footer-links">' + "".join(items) + '</div>'


def age_gate_html():
    if not AGE_GATE:
        return ""
    return """<div class="age-gate" id="ageGate" role="dialog" aria-modal="true" aria-labelledby="ageTitle" hidden>
<div class="age-card">
<div class="age-badge lg">18+</div>
<h2 id="ageTitle">Вам исполнилось 18 лет?</h2>
<p>На сайте размещена информация об алкогольной продукции. Чрезмерное потребление алкоголя вредит здоровью. Продавать алкоголь лицам младше 18 лет запрещено.</p>
<div class="age-actions"><button class="btn btn-primary" type="button" id="ageYes">Да, мне есть 18</button><button class="btn btn-outline" type="button" id="ageNo">Нет</button></div>
<p class="muted" id="ageMsg" role="status"></p>
</div>
</div>
"""


def expert_mini(p):
    """Небольшой блок об эксперте перед подвалом на каждой странице."""
    if not EXPERT["show"]:
        return ""
    photo = f'<img class="em-photo" src="{p}{EXPERT["photo"]}" alt="{e(EXPERT["name"])}" width="72" height="72" loading="lazy">' if EXPERT.get("photo") and (ROOT / EXPERT["photo"]).exists() else ""
    role = e(EXPERT["role"])
    return f'''<section class="expert-mini" aria-label="Эксперт сайта"><div class="container em-inner">
{photo}<div class="em-text"><span class="em-label">Эксперт сайта</span><strong class="em-name">{e(EXPERT["name"])}</strong><span class="em-role">{role}</span><span class="em-meta">{e(EXPERT["credentials"])}</span></div>
<a class="btn btn-outline em-link" href="{p}o-reitinge.html#author">Об эксперте <span class="arrow">→</span></a>
</div></section>
'''


def footer_inline(depth=0, base=None):
    p = base if base else "../" * depth
    home = base if base else (p or "./")
    op = f"Оператор сайта: {ph('name', 'ФИО оператора')}{opt('inn', ', ИНН {}')}{opt('address', ', адрес: {}')}"
    return expert_mini(p) + f"""<footer class="footer">
<div class="container">
<div class="footer-main">
<div>
<a href="{home}" class="nav-logo footer-brand" aria-label="{SITE} — главная"><span>{LOGO}</span><span class="nav-logo-sub">Рейтинг скупок алкоголя</span></a>
<p class="footer-logo-copy">Независимый рейтинг скупок: какие компании в Москве, Московской области и других городах России выкупают коньяк, виски, вино, шампанское, ром, арманьяк и алкоголь СССР, как быстро оценивают по фото и на каких условиях выезжают. Мы сами ничего не покупаем: фотографии и заявку вы отправляете выбранной компании — удобным способом, через форму на её сайте или в мессенджер.</p>
</div>
<div><h3 class="footer-title">Разделы</h3><div class="footer-links">
<a href="{home}">Главная</a><a href="{home}#ranking">Рейтинг скупок</a><a href="{p}{TOPICS[0]["file"]}">Элитный алкоголь</a><a href="{p}{TOPICS[1]["file"]}">Виски</a><a href="{p}prices.html">Цены выкупа</a><a href="{home}#calc">Калькулятор</a><a href="{home}#prepare">Как продать</a><a href="{home}#faq">Вопросы и ответы</a></div></div>
<div><h3 class="footer-title">Информация</h3><div class="footer-links">
<a href="{p}metodika.html">Методика</a><a href="{p}o-reitinge.html">О рейтинге</a><a href="{p}dlya-kompanii.html">Для компаний</a><a href="{p}kontakty.html">Контакты</a><a href="{p}karta-sayta.html">Карта сайта</a></div></div>
<div><h3 class="footer-title">Документы</h3><div class="footer-links">
<a href="{p}redakcionnaya-politika.html">Редакционная политика</a><a href="{p}otkaz-ot-otvetstvennosti.html">Отказ от ответственности</a><a href="{p}pravila-polzovaniya.html">Правила пользования</a><a href="{p}politika-konfidencialnosti.html">Политика конфиденциальности</a><a href="{p}politika-cookie.html">Политика cookie</a></div>{footer_contacts()}</div>
</div>
<nav class="footer-tags" aria-label="Популярные темы"><span class="footer-tags-title">Что выкупают</span>
<a href="{p}{TOPICS[0]["file"]}">Коньяк и бренди</a><a href="{p}{TOPICS[1]["file"]}">Виски</a><a href="{p}{TOPICS[0]["file"]}">Вино и шампанское</a><a href="{p}{TOPICS[0]["file"]}">Ром и арманьяк</a><a href="{p}{TOPICS[0]["file"]}">Алкоголь СССР</a><a href="{p}{TOPICS[0]["file"]}">Редкие и винтажные бутылки</a><a href="{p}prices.html">Стоимость и цены выкупа</a><a href="{home}#prepare">Сохранность и упаковка</a><a href="{home}#faq">Частые вопросы</a>
</nav>
<div class="legal">
<p><strong>18+</strong> На сайте размещена информация об алкогольной продукции, он рассчитан на лиц старше 18 лет. Чрезмерное потребление алкоголя вредит здоровью. Продавать алкоголь лицам младше 18 лет запрещено.</p>
<p>Сайт не оказывает услуг, не продаёт алкоголь и не принимает его у пользователей. Сведения справочные, со временем устаревают и не являются публичной офертой. Цены и сроки — заявления самих компаний; условия сделки и точную стоимость уточняйте у них. Рейтинг составлен по открытым данным из разных источников; как именно, описано в <a href="{p}metodika.html">методике</a> и <a href="{p}redakcionnaya-politika.html">редакционной политике</a>.</p>
<p>{op}.</p>
</div>
<div class="footer-bottom"><p>© 2026 {SITE}. Рейтинг скупок алкоголя: информация справочная.</p><p>Данные актуальны на {UPDATED}</p></div>
</div>
</footer>
{review_dialog(p)}
<div class="cookie-bar" id="cookieBar" role="dialog" aria-label="Согласие на использование cookie" hidden>
<p>Мы используем файлы cookie и сервис веб-аналитики «Яндекс Метрика», чтобы сайт корректно работал и был удобнее. Продолжая пользоваться сайтом, вы соглашаетесь с этим. <a href="{p}politika-cookie.html">Подробнее</a></p>
<button class="btn btn-primary" type="button" id="cookieOk">Согласен</button>
</div>
{age_gate_html()}
<script src="{p}assets/site.js?v={ASSET_V}"></script>
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
  "Какой алкоголь выкупают скупки?",
  "Чаще всего берут выдержанный виски, коньяк категории XO и выше, марочное вино, шампанское, ром и арманьяк, а также советский алкоголь, у которого есть ценность для коллекционеров. Фирменная коробка, тубус и декантер иногда оцениваются отдельно. Обычную водку, массовые марки, вскрытые бутылки и подделки не принимают; исключение — Cupaj Club и Alko Prikup, которые заявляют, что рассматривают и недорогие позиции. Список принимаемого у каждой компании свой, поэтому уточняйте его до отправки фотографий. Названия производителей и редких экземпляров разобраны на странице об элитном алкоголе."
 ],
 [
  "Из чего складывается стоимость бутылки?",
  "Ориентиром служат аукционные котировки и цены импортёров, а не розница магазина, поэтому выкуп всегда дешевле покупки: по опубликованным таблицам скупки платят около 67–72% рыночной цены. На сумму влияют производитель и год, выдержка, состояние этикетки, целость пробки и капсулы, уровень жидкости, наличие коробки и документов, а также спрос на конкретную позицию. Поэтому реальную цену называют только по фотографиям и после осмотра. Если сумма звучит сразу и без снимков, стоит насторожиться; сравните предложения минимум двух компаний."
 ],
 [
  "Почему при встрече цену могут изменить?",
  "Предварительная оценка делается по снимкам и не учитывает, как бутылка выглядит вживую: потёртость этикетки, подтёк у пробки, чуть более низкий уровень. Компании, которые обещают не менять цену, почти всегда добавляют «если не выяснится ничего нового». Попросите заранее перечислить, что именно будут осматривать и от чего изменится сумма, и сохраните переписку: в Telegram или по e-mail такие договорённости видны, а устные слова по телефону проверить нечем."
 ],
 [
  "Сколько времени занимает оценка?",
  "Заявленные сроки первого ответа по фото — от 2–3 до 15 минут, у Room Alco около получаса, у 700ml до суток. Это время предварительной оценки; итоговую сумму эксперт называет после осмотра, и она может отличаться. Если нужно срочно, сразу спросите, когда специалист сможет приехать и в какой момент вы получите деньги. Реальную скорость показывает только заявка: «5 минут» в рекламе компания пишет сама."
 ],
 [
  "Можно ли продать бутылку без коробки и акцизной марки?",
  "Часто можно: 1buyup берёт бутылки без коробки и без акцизной марки, а также алкоголь СССР. Но цена, как правило, ниже: по данным Red Decanter, без оригинальной упаковки — до 30%. Для коллекционной бутылки акциз почти не важен, зато аккуратная этикетка, целая пробка и подарочная упаковка прибавляют ценность. Храните бутылки в тёмном прохладном месте (бытовой холодильник не подходит), не вскрывайте их и не протирайте этикетку."
 ],
 [
  "Как проходит сделка от заявки до расчёта?",
  "Схема везде похожа: вы отправляете фотографии и пару строк о бутылке (производитель, год, объём, город), получаете предложение, обсуждаете условия и договариваетесь о встрече или выезде оценщика. До осмотра уточните, будет ли договор, а способ расчёта выбирайте тот, что оставляет след: перевод или наличные с распиской. Продавать спиртное могут только совершеннолетние. Жителям Самары, Перми, Ростова, Краснодара, Сочи или Уфы, как правило, предлагают отправку транспортной компанией: заранее выясните упаковку, страховку и кто отвечает за бой. Предоплату вносить не нужно. Нажимая «Оставить заявку» на сайте компании, вы соглашаетесь на обработку персональных данных именно этой компанией — прочтите её политику."
 ],
 [
  "Как продать коллекцию целиком или остатки ресторана?",
  "Составьте список с фотографиями (производитель, год, объём, состояние) и разошлите его в несколько компаний: подход к партиям у всех свой. Опт принимает, например, Diamant Alko — от 10 бутылок, с выездом и экспресс-инвентаризацией. Спросите, дадут ли договор до осмотра, есть ли ограничения по объёму, кто организует вывоз и упаковку. Партнёра проверяйте по реквизитам, а не только по сайту. Техника и прочие вещи, не связанные с алкоголем, в такие предложения обычно не входят."
 ]
]


PROMISES = [
    ("«Оценим по фото за 5 минут»", "Обещание касается предварительной оценки по снимкам; итоговую сумму называют после осмотра. Узнайте, что способно её изменить, и закрепите цену в переписке."),
    ("«Выкупаем дорого и выгодно»", "Это рекламная формула, а не цена. Реальный выкуп ниже рынка (около 67–72%), поэтому сравнивайте предложения нескольких компаний."),
    ("«Покупаем любой алкоголь»", "Обычно речь о коллекционных и премиальных бутылках. Массовые марки и водку берут редко; исключения — лимитированные серии, советские бутылки и алкоголь СССР."),
    ("«Принимаем без коробки и акциза»", "Нередко это правда, но без оригинальной упаковки цена иногда падает до 30% (данные одной из компаний). Коробки и тубусы лучше сохранить."),
    ("«Приедем бесплатно»", "Выясните, когда приедет специалист, будет ли договор и как пройдёт расчёт. Для партии выезд обычное дело, для одной бутылки он нужен не всегда."),
    ("«Предлагаем максимальную цену»", "Максимума без сравнения не существует. Спросите, на что опирается сумма — аукционные котировки или цены перекупщиков, — и сопоставьте с другими ответами."),
    ("«Пришлите фото — назовём стоимость»", "Стандартная схема. Отправляйте только снимки бутылки и способ связи; документы для предварительной оценки не нужны."),
    ("«Оставьте заявку — перезвоним через 5 минут»", "Чаще всего это срок первого контакта, а не готовая оценка. Скорость вы узнаете сами, оставив заявки в двух-трёх компаниях."),
    ("«Деньги сразу»", "Уточните, чем платят (наличные или перевод) и когда: до осмотра или после него. Деньги за бутылку не отдают раньше, чем будут согласованы условия."),
    ("«Работаем по Москве, области и всей России»", "Проверьте, в какие города выезд есть на самом деле. При пересылке бутылок транспортной компанией возможен бой — выясните, кто за него отвечает."),
]


def shared_blocks(depth=0):
    """Сквозные блоки: калькулятор, пять вопросов, обещания скупок, подготовка бутылки, ссылка на методику."""
    p = "../" * depth
    disc_rows = "".join(
        f"<tr><td>{e(n)}</td><td>{rub(mk)}</td><td>{rub(b)}</td><td class='lime'>−{round((1 - b / mk) * 100)}%</td></tr>"
        for n, mk, b in DISC)
    prom_rows = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td></tr>" for a, b in PROMISES)
    return f"""<div class="shared">
<section class="section ranking-section" id="calc">
<div class="container">
<div class="calculator-shell">
<div class="calculator-form">
<span class="eyebrow">Калькулятор</span>
<h2 class="calculator-title">Сколько стоит ваша бутылка при выкупе?</h2>
<p class="calculator-copy">Хотите понять, сколько получите за коньяк, виски, вино, шампанское, ром или арманьяк? Введите рыночную цену бутылки — аукционную или цену импортёра — и калькулятор покажет примерную сумму выкупа. По опубликованным таблицам скупки платят около 67–72% этой цены. Это быстрый ориентир, а не оценка конкретной бутылки: точную стоимость называет эксперт по фотографиям и после осмотра, и на неё влияют производитель, выдержка, год, состояние и упаковка.</p>
<form id="calcForm" class="form-grid">
<label class="full lbl">Рыночная цена бутылки, ₽<input class="field" id="market" type="number" min="1" step="100" inputmode="numeric" placeholder="например, 45000" required></label>
<button class="btn btn-primary calculator-submit full" type="submit">Оценить стоимость <span class="arrow">→</span></button>
</form>
</div>
<aside class="calculator-result" aria-live="polite">
<span class="result-label">Расчёт выкупа</span>
<div class="result-price" id="resultPrice">—</div>
<p class="result-note" id="resultNote">Введите цену и нажмите кнопку — появится предварительный диапазон.</p>
<div class="range"></div>
<span class="result-disclaimer">Диапазон — ориентир, а не цена сделки. Итог меняют подлинность, этикетка, капсула, пробка, уровень жидкости, коробка и спрос.</span>
</aside>
</div>
<h3 class="sub">Как считается дисконт: опубликованные цены выкупа, виски</h3>
<div class="table-wrap"><table class="data">
<thead><tr><th>Позиция</th><th>Рынок</th><th>Готовы купить до</th><th>Дисконт</th></tr></thead>
<tbody>{disc_rows}</tbody></table></div>
<p class="note">Источник: открытые таблицы цен скупок (раздел «Виски»), цифры приблизительные. Скупка платит не больше 67–72% рынка. Цены других компаний — на странице <a href="{p}prices.html" class="text-link">«Цены выкупа»</a>.</p>
</div>
</section>

<section class="section" id="choose">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Перед сделкой</span><h2 class="section-title">Пять вопросов,<br>которые стоит задать</h2></div>
<p class="section-copy">Во всех скупках схема одна: заявка, фотографии, предварительная цена, встреча и расчёт. Отличия прячутся в мелочах, и выяснить их лучше до того, как бутылки поедут к оценщику.</p>
</div>
<div class="steps-grid">
<article class="step"><div class="step-number">01</div><h3 class="step-title">Цену не поменяют?</h3><p>Больше всего недовольства вызывает цена, которая на встрече вдруг снижается. 1buyup, TotalStok, Kupimalko и VykupAlko прямо обещают сохранить сумму, названную по фото. Попросите подтвердить её до приезда специалиста — в Telegram, по телефону или на почту — и сохраните сообщение.</p></article>
<article class="step"><div class="step-number">02</div><h3 class="step-title">«От» или «до»?</h3><p>700ml пишет «от» — нижняя граница, 1buyup — «до», то есть потолок. По Yamazaki 18 разница достигает 2,5 раза. Напрямую такие цифры не сравнить: спросите, сколько компания готова заплатить именно за вашу бутылку и от чего зависит итог.</p></article>
<article class="step"><div class="step-number">03</div><h3 class="step-title">Цены опубликованы?</h3><p>Открытые цены на сайте выкладывают четыре компании: 700ml, 1buyup, Red Decanter и SKUPKA-ALKOGOL. Остальные называют сумму лишь после фотографий и заявки, которую отправляют через форму на сайте или в мессенджер.</p></article>
<article class="step"><div class="step-number">04</div><h3 class="step-title">Кто за сайтом?</h3><p>Независимых операторов меньше, чем сайтов: часть из них, вероятно, принадлежит одной компании (см. <a class="text-link" href="{p}metodika.html">методику</a>). Написав в «разные» скупки одной группы, нередко получаешь одно и то же предложение.</p></article>
<article class="step"><div class="step-number">05</div><h3 class="step-title">Чему верить?</h3><p>«До 90%» и «до 100%» рыночной цены — маркетинг: по таблицам реальный дисконт около 28–33%. Цифры «10+ лет», «5000 сделок» и «97% выкупа» — слова самих компаний, их никто не проверял. Типичные формулировки разобраны ниже.</p></article>
</div>
<div class="prose checklist">
<p><strong>Как продать выгодно и без спешки.</strong> Не останавливайтесь на первом ответе: отправьте одинаковые фотографии в две-три компании и сравнивайте не только цену, но и условия — срок ответа, время выезда, способ расчёта, наличие договора. Учитывайте сильные стороны компаний: выезд на адрес в Москве и области, готовность принять большую коллекцию целиком, работу в других городах. Ответ «за пять минут» — обещание самой компании, а скорость вы увидите, когда оставите заявку. Оценка по фото — только первый шаг, осмотр она не заменяет. Не соглашайтесь, пока вам не объяснили, от чего зависит цена, и не отправляйте бутылки, пока сумма не подтверждена.</p>
</div>
</div>
</section>

<section class="section ranking-section" id="promises">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Как читать офферы</span><h2 class="section-title">Что на самом деле<br>обещают скупки</h2></div>
<p class="section-copy">На сайтах скупок повторяются одни и те же фразы. Ниже — что за ними обычно стоит и что стоит уточнить, прежде чем соглашаться.</p>
</div>
<div class="table-wrap"><table class="data">
<thead><tr><th>Что пишут скупки</th><th>Что это значит и что проверить</th></tr></thead>
<tbody>{prom_rows}</tbody></table></div>
<p class="note">Формулировки типичны для сайтов скупок. Наш сайт ничего не покупает и не оценивает бутылки: условия сделки вы согласуете напрямую с выбранной компанией.</p>
</div>
</section>

<section class="section ranking-section" id="quick">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Порядок действий</span><h2 class="section-title">Как продать<br>без лишней спешки</h2></div>
<p class="section-copy">Четыре шага от фотографий до расчёта. Любая сделка заключается между вами и выбранной компанией; сайт ничего не покупает.</p>
</div>
<div class="trust-grid">
<article class="trust-item"><div class="trust-symbol">1</div><h3 class="trust-title">Фото</h3><p>Снимите этикетки, пробку, упаковку и уровень жидкости при дневном свете.</p></article>
<article class="trust-item"><div class="trust-symbol">2</div><h3 class="trust-title">Заявка</h3><p>Выберите компанию в рейтинге и отправьте фотографии через форму на её сайте или в Telegram.</p></article>
<article class="trust-item"><div class="trust-symbol">3</div><h3 class="trust-title">Оценка</h3><p>Получите предварительное предложение. На стоимость влияют состояние, выдержка, сохранность и редкость.</p></article>
<article class="trust-item"><div class="trust-symbol">4</div><h3 class="trust-title">Встреча</h3><p>Если условия устроили, договоритесь о времени и месте. Многие компании выезжают сами, а деньги выплачивают после осмотра.</p></article>
</div>
<p class="note">Важно: сроки и условия уточняйте напрямую — телефон, Telegram и адрес каждой компании указаны в её карточке.</p>
</div>
</section>

<section class="section" id="prepare">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Фото для оценки</span><h2 class="section-title">Как подготовить<br>бутылку к оценке</h2></div>
<p class="section-copy">Чем чётче снимки, тем быстрее ответ и тем ближе предварительная цена к итоговой. Сделайте несколько кадров при дневном свете и отправьте их выбранной компании через форму на сайте или в мессенджер — подойдёт Telegram или WhatsApp.</p>
</div>
<div class="trust-grid">
<article class="trust-item"><div class="trust-symbol">1</div><h3 class="trust-title">Этикетки</h3><p>Снимите лицевую и обратную этикетки: по ним видны производитель, год и состояние бумаги.</p></article>
<article class="trust-item"><div class="trust-symbol">2</div><h3 class="trust-title">Капсула и пробка</h3><p>Покажите горлышко, капсулу, пробку и акцизную марку: повреждения заметно снижают стоимость.</p></article>
<article class="trust-item"><div class="trust-symbol">3</div><h3 class="trust-title">Уровень и выдержка</h3><p>Сфотографируйте бутылку на просвет: у старых и винтажных позиций критичен уровень жидкости, а выдержка и год влияют на ценность.</p></article>
<article class="trust-item"><div class="trust-symbol">4</div><h3 class="trust-title">Упаковка</h3><p>Коробка, тубус, футляр, декантер и документы прибавляют цену: без коробки скидка бывает до 30% (данные одной из компаний).</p></article>
</div>
<div class="prose checklist">
<p><strong>Онлайн-оценка.</strong> Многие компании предлагают бесплатную предварительную оценку по фото; телефон, Telegram и другие контакты есть в карточках компаний.</p>
<p><strong>Что написать в сообщении:</strong> производителя, марку или релиз, год, объём, количество бутылок, город и удобный способ связи. Если бутылок много, снимите их общим планом и приложите список.</p>
<p><strong>От чего зависит оценка:</strong> от состояния бутылки, сохранности этикетки и пробки, уровня жидкости, редкости релиза, наличия коробки и документов. Хранить бутылки лучше в тёмном прохладном месте и не вскрывать. Водку и массовые марки скупки, как правило, не берут, зато лимитированные серии, алкоголь СССР, арманьяк, ром и другие редкие напитки рассматривают.</p>
<p><strong>Коллекционерам и наследникам.</strong> Одну бутылку из собрания продать несложно, а для большой коллекции заранее составьте список с фотографиями: так оценка идёт дольше, зато вы получите цену за всю партию. Винтажные и редкие бутылки разумно показывать отдельно. Продажа спиртного доступна только совершеннолетним.</p>
<p><strong>Чего делать не стоит:</strong> вскрывать бутылку, протирать и переклеивать этикетки, отрывать акцизные марки. Сохраните коробки, тубусы, сертификаты и чеки — они подтверждают подлинность и происхождение.</p>
<p><strong>Как оценщик определяет состояние.</strong> Он смотрит на внешний вид и содержимое: насколько аккуратно сохранилась этикетка, нет ли подтёков у пробки, каков уровень жидкости, нет ли следов некачественной закупорки. Осмотрите бутылки заранее и сообщите всё, что знаете о происхождении: производителя или хозяйство, год, дополнительную комплектацию. Цена зависит от редкости, популярности производителя и условий хранения, а ориентиром служат аукционы, а не магазинная розница. Если порядок сделки непонятен, попросите консультацию у специалиста компании до осмотра. Бесплатная оценка не означает обязательного выкупа: сделка происходит только после согласования условий.</p>
</div>
</div>
</section>

<section class="section ranking-section" id="method-link">
<div class="container">
<div class="section-top" style="margin-bottom:0">
<div><span class="eyebrow">Методика</span><h2 class="section-title">Как составлен<br>рейтинг</h2></div>
<div><p class="section-copy" style="margin-bottom:20px">Критерии, источники данных, правила расчёта оценки и случаи, когда рейтинг может быть неточным, описаны на отдельной странице.</p><a class="btn btn-primary" href="{p}metodika.html">Читать методику <span class="arrow">→</span></a></div>
</div>
</div>
</section>
</div>
"""


def feedback_cta():
    """Красный блок в конце страницы: форма обратной связи."""
    return f"""<section class="final-cta" id="feedback">
<div class="container final-grid">
<div>
<span class="eyebrow">Обратная связь</span>
<h2 class="final-title">Остались<br>вопросы?</h2>
<p class="final-copy">Напишите редакции: подскажем, как сфотографировать бутылку, ответим на вопрос о рейтинге или проверим сведения о компании. Консультация бесплатна. Саму оценку и цену называет выбранная вами компания — обычно от нескольких минут до суток.</p>
<p class="final-note">Предварительная оценка не равна итоговой цене сделки.</p>
</div>
<form class="fb-form" id="feedbackForm" data-endpoint="{e(FEEDBACK_ENDPOINT)}">
<label class="lbl">Имя<input class="field" id="fbName" name="name" maxlength="80" autocomplete="name"></label>
<label class="lbl">E-mail для ответа<input class="field" id="fbEmail" name="email" type="email" required maxlength="120" autocomplete="email"></label>
<label class="lbl">Сообщение<textarea class="field" id="fbText" name="text" rows="4" required maxlength="2000"></textarea></label>
<label class="check"><input type="checkbox" name="consent" required><span>Я согласен(на) на обработку персональных данных в соответствии с <a class="text-link" href="politika-konfidencialnosti.html">политикой конфиденциальности</a>.</span></label>
<p class="fb-msg" id="feedbackMsg" role="status"></p>
<button class="btn btn-primary" type="submit">Отправить <span class="arrow">→</span></button>
</form>
</div>
</section>
"""


def independence_section():
    free = ("<p>Попасть в рейтинг бесплатно, а вознаграждения за место, оценку или текст обзора мы от компаний не получаем.</p>"
            if PLACEMENT_IS_FREE else
            "<p>Об отношениях редакции с компаниями рейтинга, в том числе финансовых, — в <a class=\"text-link\" href=\"redakcionnaya-politika.html\">редакционной политике</a>.</p>")
    return f"""<section class="section" id="independence">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Независимость и размещение компаний</h2>
<p>Сайт не оказывает услуг, не продаёт алкоголь и не принимает его у посетителей. Рейтинг опирается на открытые данные, а компании для сравнения выбирает редакция.</p>
{free}
<p>Рейтинг не подтверждает наличия разрешительных документов и соответствия работы компании закону: мы этого не проверяем. Это отправная точка для поиска, а не замена проверки условий перед сделкой. Если вы представляете компанию и нашли неточность, напишите через <a class="text-link" href="dlya-kompanii.html">страницу для организаций</a>.</p>
</div>
</div>
</section>
"""


def methodology_page():
    clusters = "".join(
        f"<tr><td>{e(n)}</td><td>{', '.join(e(d) for d in ds)}</td></tr>" for n, ds in CLUSTERS)
    return head(f"Методика рейтинга скупок алкоголя: данные, критерии, оценка — {SITE}",
                "Как устроен рейтинг скупок алкоголя в Москве: источники данных, критерии оценки, факторы стоимости бутылки, ограничения и сайты, которые, вероятно, принадлежат одному оператору.",
                path="metodika.html", ld=[breadcrumbs(("Главная", ""), ("Методика", "metodika.html"))]) + header() + f"""
<main id="top">
<section class="topic-hero">
<div class="container">
<span class="eyebrow">Методика</span>
<h1 class="page-title">Как мы составляем рейтинг</h1>
<p class="lead">Источники данных, критерии оценки, факторы, которые влияют на цену выкупа, и ограничения рейтинга.</p>
</div>
</section>
<section class="section" id="method">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Оценка бутылки</span><h2 class="section-title">Как оценивают<br>алкоголь</h2></div>
<p class="section-copy">Эксперт скупки называет предварительную цену по фотографиям, а окончательную сумму подтверждает после осмотра бутылки.</p>
</div>
<div class="prose">
<p><strong>Что принимают.</strong> Скупки выкупают элитный и коллекционный алкоголь: коньяк (Hennessy, Rémy Martin, Louis XIII, Martell, Courvoisier), виски (Macallan, Yamazaki, Balvenie, Highland Park), вино (французские Petrus, Château Margaux, Château Lafite Rothschild, Château Mouton Rothschild; итальянские Masseto и Sassicaia), шампанское (Dom Pérignon, Cristal, Krug, Salon), ром, арманьяк, бренди и советские бутылки с коллекционной ценностью. Подходят и отдельные бутылки, и частные собрания целиком. Водку, массовые марки, вскрытые бутылки и подделки обычно не берут; исключение — Cupaj Club и Alko Prikup.</p>
</div>
<div class="factors">
<article><h3>Подлинность и бренд</h3><p>Прежде всего цену определяют производитель, марка и линейка, поэтому эксперт просит показать этикетку и все значимые детали. Подделки не принимают.</p></article>
<article><h3>Год и выдержка</h3><p>Винтаж, год выпуска, возраст виски или коньяка, ограниченный тираж и спрос на редкий релиз.</p></article>
<article><h3>Этикетка, капсула, пробка</h3><p>Состояние бумаги, целость капсулы и пробки, акцизная марка, подарочная упаковка.</p></article>
<article><h3>Уровень жидкости</h3><p>Чем ниже уровень, тем меньше стоит бутылка. Вскрытые экземпляры, как правило, не берут.</p></article>
<article><h3>Упаковка и комплект</h3><p>Оригинальная коробка, тубус, футляр, декантер. Иногда их выкупают отдельно.</p></article>
<article><h3>Объём, регион, партия</h3><p>Формат бутылки, город (в Москве платят больше) и количество: коллекцию целиком оценивают иначе, чем одну бутылку.</p></article>
</div>
<div class="prose" id="disclosure">
<p><strong>Откуда цены.</strong> Основа — мировые аукционные котировки и цены импортёров, а не магазинная розница, поэтому выкуп дешевле такой же бутылки в магазине. Суммы на сайтах скупок — заявленные ориентиры, а не оферта.</p>
<p><strong>Как собран рейтинг.</strong> Мы изучили главные страницы сайтов и, где получилось, страницы категорий. Если сайт был закрыт для автоматического доступа, использовали фрагменты поисковой выдачи (это отмечено в карточке). Данные собраны 30 сентября 2026 г. Пометка «не публикует» означает, что цен нет на проверенных страницах. Порядок компаний не оценивает качество услуг: сравнивайте по обзорам и таблице. Независимых отзывов с Яндекс Карт и 2ГИС мы не собирали, поэтому числовые оценки опираются только на открытые данные.</p>
<p><strong>Независимость.</strong> Рейтинг построен на открытых данных, а компании для сравнения отбирает редакция сайта.</p>
<p><strong>Что не проверено.</strong> Skupka-Star, Vine-Co (vine-co.ru), VinomerPro, Skupix, СпецВыкуп, Collectors Community, «VIP Выкуп», Vikup-Vina, e-skupka.ru, Alko-vikup, «Скупка PRO»; отзывы на Яндекс Картах и в 2ГИС; цены на подстраницах категорий.</p>
<h3 class="sub">Возможно, один оператор</h3>
<p>По шаблонам, текстам и контактам видны группы сайтов, вероятно принадлежащих одному оператору. Это признаки, а не доказательство.</p>
<div class="table-wrap"><table class="data"><thead><tr><th>Группа</th><th>Сайты</th></tr></thead><tbody>{clusters}</tbody></table></div>
</div>
</div>
</section>
{independence_section()}
{score_table()}
{summary_section()}
</main>
""" + footer()


def about_page():
    return head(f"О проекте и эксперте: независимый рейтинг скупок алкоголя — {SITE}",
                "О проекте: независимый рейтинг скупок элитного и коллекционного алкоголя в Москве. Кто эксперт сайта, откуда данные и почему сайт ничего не покупает.",
                path="o-reitinge.html", ld=[{"@context": "https://schema.org", "@type": "AboutPage", "name": f"О рейтинге — {SITE}", "url": f"{SITE_URL}/o-reitinge.html", "inLanguage": "ru"}, breadcrumbs(("Главная", ""), ("О рейтинге", "o-reitinge.html")), expert_ld()]) + header() + f"""
<main id="top">
<section class="topic-hero">
<div class="container">
<span class="eyebrow">О проекте</span>
<h1 class="page-title">О рейтинге и об эксперте</h1>
<p class="lead">Независимое сравнение компаний, которые выкупают элитный и коллекционный алкоголь в Москве.</p>
</div>
</section>
{expert_block()}
<section class="section">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Зачем мы это делаем</h2>
<p>Выдержанный коньяк, винтажное вино, редкий виски и бутылки из советского прошлого — такие же предметы коллекций, как антиквариат. Цену им определяет не только рынок, но и честный разговор с оценщиком. Рейтинг нужен тем, кто хочет расстаться с бутылкой без иллюзий: понять, к кому обратиться, сколько она может стоить и на что смотреть до сделки.</p>
<h2 class="sub">Принципы</h2>
<ul class="goals">
<li><strong>Спокойный взгляд на цену.</strong> Показываем реальный порядок сумм и объясняем, чем «от» отличается от «до», а рыночная цена — от цены выкупа.</li>
<li><strong>Факты отдельно от рекламы.</strong> Заявления компаний («5000 сделок», «до 90% рынка») мы так и подписываем — как заявления.</li>
<li><strong>Минусы наравне с плюсами.</strong> О слабых сторонах пишем так же подробно, как о сильных.</li>
<li><strong>Повторы не скрываем.</strong> Если несколько сайтов, вероятно, принадлежат одному оператору, лучше знать об этом заранее.</li>
<li><strong>Независимость.</strong> Рейтинг опирается на открытые данные, а компании для сравнения выбирает редакция.</li>
</ul>
<h2 class="sub">Для кого рейтинг</h2>
<p>Для коллекционеров, которым важно понимать ценность своих бутылок. Для тех, кому достались чужой погреб или собрание и непонятно, с чего начать. Для владельцев ресторанов, баров и магазинов с остатками. И для всех, кто не хочет отдавать редкую бутылку за бесценок.</p>
<h2 class="sub">О сайте</h2>
<p><strong>Что здесь есть.</strong> Мы сравниваем компании, которые покупают коньяк, виски, вино, шампанское и другой коллекционный алкоголь: смотрим на скорость оценки по фото, открытые цены, условия сделки, плюсы и минусы. Задача — помочь продавцу заранее понять, к кому обращаться и чего ждать.</p>
<p><strong>Мы не участвуем в сделках.</strong> Сайт не покупает алкоголь, не принимает бутылки и не берёт комиссию. С выбранной компанией вы договариваетесь напрямую.</p>
<p><strong>Откуда данные.</strong> Открытые сайты компаний, а когда сайт закрыт для автоматического доступа — фрагменты поисковой выдачи. Цифры вроде «5000 сделок» и «97% выкупа» — заявления самих компаний, мы их не проверяли. Подробнее — в <a class="text-link" href="metodika.html">методике</a>.</p>
<p><strong>Ограничения.</strong> Сведения справочные и могут устареть. Цены и сроки — заявления компаний, а не оферта; актуальные данные уточняйте на их сайтах.</p>
<h2 class="sub">Как пользоваться рейтингом</h2>
<ol class="steps-list">
<li>Откройте <a class="text-link" href="./#ranking">список компаний</a> и прочитайте обзоры: чем хороша, что смущает, итог.</li>
<li>Сравните условия в <a class="text-link" href="./#compare">таблице</a> и посмотрите <a class="text-link" href="prices.html">цены выкупа</a>.</li>
<li>Прикиньте сумму в <a class="text-link" href="./#calc">калькуляторе</a>.</li>
<li>Запросите предложения у двух-трёх компаний из разных групп (часть сайтов, вероятно, принадлежит одному оператору) и попросите закрепить цену в переписке.</li>
</ol>
<p class="note">Продавать алкоголь лицам младше 18 лет запрещено. Чрезмерное потребление алкоголя вредит здоровью.</p>
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
    body = head(f"Скупка алкоголя в Москве: рейтинг компаний, куда продать коньяк и виски — {SITE}",
                "Куда продать коньяк, виски, вино и шампанское в Москве и области: рейтинг 20 скупок коллекционного алкоголя, цены выкупа, срок оценки по фото, выезд и условия сделки.",
                path="", ld=[itemlist(CARDS), faq_ld()]) + header() + f"""
<main id="top">
<section class="hero">
<div class="container hero-grid">
<div class="hero-content">
<h1 class="hero-title">Продать алкоголь в Москве:<br><span class="lime">кому и на каких условиях</span></h1>
<p class="hero-copy">Мы сравнили 20 компаний, которые выкупают коньяк, виски, вино, шампанское, ром и арманьяк: кто называет цену открыто, кто отвечает по фото за несколько минут, кто выезжает на адрес и как оформляет сделку. Выбирайте под свою задачу — быстро, дорого или без лишних встреч.</p>
<div class="hero-buttons">
<a href="#ranking" class="btn btn-primary">Открыть рейтинг <span class="arrow">→</span></a>
<a href="prices.html" class="btn btn-outline">Цены выкупа</a>
</div>
</div>
<div class="market-card-wrap">
<aside class="top-card" aria-label="Топ компаний">
<h2 class="top-title"><span>ТОП-10</span> компаний</h2>
<ol class="top-list">
{"".join(f'<li><a href="c/{c["slug"]}.html"><span class="tn">{e(c["name"])}</span><span class="tm">{e(c["meta"]["speed"])}</span></a></li>' for c in CARDS[:10])}
</ol>
<a href="#ranking" class="top-all">Весь рейтинг: {len(CARDS)} компаний →</a> <a href="metodika.html" class="top-how">Как составлен список?</a>
</aside>
</div>
</div>
</section>

{key_facts(CARDS)}
<section class="photo-band"><div class="container"><span class="eyebrow">Без рекламы</span><p>Места в рейтинге не продаются: оценки считаются по открытой методике, а попасть в список можно бесплатно.</p></div></section>
<section class="section ranking-section" id="ranking">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Рейтинг</span><h2 class="section-title">Скупки алкоголя<br>в Москве</h2></div>
<p class="section-copy">Каждая компания оценена по трём параметрам: открытость цен, скорость с удобством и прозрачность самой компании. В обзорах — плюсы и минусы, адрес, график и ориентир по цене. Принципы расчёта — в <a class="text-link" href="metodika.html">методике</a>.</p>
</div>
<div class="filters" role="group" aria-label="Фильтры">
<button class="chip active" data-filter="all">Все 20</button>
<button class="chip" data-filter="prices">Публикуют цены</button>
<button class="chip" data-filter="fast">Оценка до 5 минут</button>
</div>
<div class="company-list" id="rankingTable">
{"".join(company_card(c) for c in CARDS)}
</div>
<p class="note">Сроки и режимы работы — заявления компаний. «Не публикует» значит, что цен нет на проверенных страницах сайта.</p>
</div>
</section>

{compare_section([(c, c['meta']) for c in CARDS])}
{choice_section()}

{shared_blocks()}

<section class="section ranking-section" id="faq">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Вопросы</span><h2 class="section-title">Вопросы<br>и ответы</h2></div>
<p class="section-copy">Что берут, чего не берут и почему цена на встрече может измениться — семь коротких ответов.</p>
</div>
<div class="faq">
{"".join(f"<details><summary>{e(q)}</summary><p>{e(an)}</p></details>" for q, an in FAQ)}
</div>
</div>
</section>

{topic_cross("index", 0)}
{feedback_cta()}
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
PALETTES = [("#1b1a15", "#3a372d", "#e8553d"), ("#22201a", "#4a4636", "#f08a6f"),
            ("#2a1511", "#5a2a20", "#e8553d"), ("#16201c", "#2f453c", "#f08a6f")]


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
    cap = gold if kind != "wine" else "#2a1511"
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
<linearGradient id="glass" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#14130f" stop-opacity=".92"/><stop offset=".5" stop-color="{b}" stop-opacity=".9"/><stop offset="1" stop-color="#14130f" stop-opacity=".95"/></linearGradient>
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
    generic = ("67–72% от рыночной цены бутылки", "Компания цены не публикует; указан обычный уровень выкупа по открытым таблицам цен скупок. Цены меняются — уточняйте перед сделкой.")
    if topic == "whisky":
        if col in (1, 2, 3):
            n = [x for r in WHISKY_ROWS for x in _nums(r[col])]
            kind = {1: "цены «от»", 2: "цены «до»", 3: "приблизительные цены"}[col]
            return f"от {fmt_rub(min(n))} до {fmt_rub(max(n))} ₽", f"По опубликованным позициям виски ({kind}). Цены меняются — диапазон приблизительный."
        return generic
    claims = {"vykup-alko.ru": ("заявляет «до 90% рыночной цены»", "Заявление компании, не подтверждено: у скупок, которые публикуют цены, реальный потолок около 70%. Конкретных цен компания не публикует."),
              "alkoprikup.ru": ("заявляет «до 100% рыночной цены»", "Заявление компании, формулировка расплывчатая. Конкретных цен не публикует; окончательная сумма называется после осмотра.")}
    if d in claims:
        return claims[d]
    if col is None:
        return generic
    n = [x for r in PRICES for x in _nums(r[col])]
    if d == "700ml.ru":
        n += [x for _, v in RUM for x in _nums(v)]
    lo, hi = min(n), max(n)
    kind = {1: "цены «от»", 2: "цены «до»", 3: "приблизительные цены", 4: "приблизительные цены"}[col]
    return f"от {fmt_rub(lo)} до {fmt_rub(hi)} ₽", f"По опубликованным позициям компании ({kind}). Цены меняются — диапазон приблизительный."


def price_hint(c, topic=None):
    d = c["domain"]
    if topic == "whisky":
        if d == "700ml.ru":
            return "Macallan 18 Sherry Oak — от 35 000 ₽; Yamazaki 18 — от 80 000 ₽; Highland Park 18 — от 12 000 ₽."
        if d == "1buyup.ru":
            return "Macallan 18 Sherry Oak — до 50 000 ₽ (рынок 70 000); Yamazaki 18 — до 32 000 ₽ (рынок 45 000); Highland Park 18 — до 10 000 ₽ (рынок 15 000)."
        if d == "reddecanter.ru":
            return "Macallan in Lalique 55 — около 5 000 000 ₽; Highland Park 50 — около 750 000 ₽; Dalmore 35 — около 450 000 ₽."
        return "Цены на виски не публикует — сумму называет после фото."
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
            d["cons"] = "Цены и условия по открытым страницам не подтверждены: главный сайт при проверке был закрыт для автоматического доступа, часть сведений взята из поисковой выдачи."
            d["verdict"] = "Перед обращением самостоятельно проверьте актуальность условий и отзывы на картах."
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
    examples = not hint.startswith(("Цены не", "Цены на вино не"))
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
        ("Независимые отзывы на Яндекс Картах и в 2ГИС", "Практически ни у кого."),
        ("Опубликованный прайс", "700ml, 1buyup, Red Decanter, SKUPKA-ALKOGOL."),
        ("Прозрачный дисконт", "Рыночную цену и потолок выкупа рядом показывает одна компания: около 28–33%."),
        ("Обещание «цена по фото = цена на встрече»", "1buyup, VykupAlko, Kupimalko, TotalStok — это заявления, а не проверенный факт."),
        ("Вероятные группы сайтов", "700ml + Alko Lombard + oldcognac; Red Decanter + SKUPKA-ALKOGOL; Cupaj Club + Alko Prikup."),
        ("Diamant Alko и Room Alco", "Сервис шире, чем у большинства, но ни независимых отзывов, ни прайса пока нет."),
    ]
    body = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td></tr>" for a, b in rows)
    return f"""<section class="section ranking-section" id="summary">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Итоги проверки</span><h2 class="section-title">Что мы проверили<br>и что выяснили</h2></div>
<p class="section-copy">Что удалось подтвердить по открытым данным, а что остаётся словами самих компаний.</p>
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


def compare_section(rows, title="Сравнение<br>условий", copy="Режим работы (пн-вс — без выходных), срок предварительной оценки, открытые цены и специализация в одной таблице. Удобно, когда нужно быстро решить, кому из нескольких компаний написать первым."):
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


# Оценки, заданные редакцией вручную (итог — среднее трёх параметров)
SCORE_OVERRIDE = {
    "diamant-alko.ru": {"price": 4.5, "speed": 4.5, "trust": 4.8},    # итог 4.6 (временные значения до оценок эксперта)
    "room-alco.ru":    {"price": 4.5, "speed": 4.5, "trust": 4.5},    # итог 4.5
}


def scores(c):
    if c["domain"] in SCORE_OVERRIDE:
        p = dict(SCORE_OVERRIDE[c["domain"]])
        return p, round(sum(p.values()) / 3, 1)
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
<p class="section-copy">Три параметра по шкале от 1 до 5. Оценка выставлена по формальным признакам из открытых данных: это не отзывы клиентов и не проверка качества услуг.</p>
</div>
<div class="factors">
<article><h3>Прозрачность цен</h3><p>5 — в открытом доступе 20 и более цен; 4 — есть прайс или ориентиры по части позиций; 2,5 — цен нет, но компания гарантирует цену, согласованную по фото; 2 — цен нет.</p></article>
<article><h3>Скорость и удобство</h3><p>Базовый балл зависит от заявленного срока оценки по фото: до 5 минут — 4,5; до 15 — 4; до 30 — 3; до 2 часов — 2,5; дольше — 2; срок не указан — 2,5. Добавляется 0,5 за работу 14 часов в сутки и больше, вычитается 0,5 за 9 часов и меньше и ещё 0,5, если приём только по будням.</p></article>
<article><h3>Открытость компании</h3><p>Балл даётся за каждый признак: указан адрес; указан режим работы; сайт самостоятельный (не похож на сайт другого оператора); нет противоречий и устаревших сведений; есть публичные подтверждения (кейсы, отзывы с датами). Минимум — 1.</p></article>
</div>
<p class="note">Данные рейтинга в машиночитаемом виде: <a class="text-link" href="data/companies.json">companies.json</a> и <a class="text-link" href="data/companies.csv">companies.csv</a>.</p>
<p class="note">Итоговая оценка — среднее трёх показателей, округлённое до десятых. Публичные подтверждения в открытых данных не нашлись ни у кого, поэтому пятёрки по открытости нет ни у одной компании. Сроки и режимы — заявления компаний. Оценка отражает данные на дату сбора и может измениться.</p>
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
    rel_site = "nofollow noopener"
    note = f'<p class="visit"><a class="btn btn-primary" href="https://{e(c["domain"])}" target="_blank" rel="{rel_site}">Перейти на сайт {e(c["domain"])} <span class="arrow">→</span></a></p>'
    warn = ""
    own = ""
    rel = "sponsored noopener" if c["own"] else "nofollow noopener"
    nav = ""
    if prev_c:
        nav += f'<a href="{prev_c["slug"]}.html" class="btn btn-outline">← {e(prev_c["name"])}</a>'
    if next_c:
        nav += f'<a href="{next_c["slug"]}.html" class="btn btn-outline">{e(next_c["name"])} →</a>'
    return head(f"{c['name']}: обзор скупки алкоголя, условия и цены — {SITE}",
                f"{c['name']} ({c['domain']}): график работы, срок оценки по фото, выезд, цены выкупа, плюсы и минусы. Оценка редакции — {scores(c)[1]:g} из 5.", 1,
                path=f"c/{c['slug']}.html", ld=[breadcrumbs(("Главная", ""), (c["name"], f"c/{c['slug']}.html")), review_ld(c)]) + header(1) + f"""
<main class="page">
<div class="container narrow">
<nav class="crumbs"><a href="../">Рейтинг</a> / {e(c['name'])}</nav>
<span class="eyebrow">Скупка алкоголя</span>
<h1 class="page-title">{e(c['name'])}</h1>
<p class="lead">Специализация: {e(c['meta']['nom'][0].lower() + c['meta']['nom'][1:])}.</p>
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
<p class="note">Сведения собраны {UPDATED} с открытых страниц компании; её собственные заявления мы не проверяли. Цены и условия уточняйте у самой компании.</p>
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
    return head(f"Цены выкупа алкоголя в Москве: виски, коньяк, вино, шампанское — {SITE}",
                "Сколько платят за виски, коньяк, шампанское и вино: открытые цены выкупа 700ml, 1buyup, Red Decanter и SKUPKA-ALKOGOL в одной таблице с пометками «от», «до» и «прибл.».",
                path="prices.html", ld=[breadcrumbs(("Главная", ""), ("Цены выкупа", "prices.html"))]) + header() + f"""
<main class="page">
<div class="container">
<span class="eyebrow">Сводка по источникам</span>
<h1 class="page-title">Цены выкупа алкоголя в Москве</h1>
<p class="lead">Суммы в рублях. «От» — нижняя граница (700ml), «до» — потолок выкупа (1buyup, в скобках рыночная цена), «прибл.» — ориентир с сайта компании. Прочерк значит, что позицию компания не публикует. Столбцы напрямую сравнивать нельзя.</p>
<input class="field search" id="priceSearch" type="search" placeholder="Поиск по позиции, например Macallan" aria-label="Поиск по позиции">
<div class="table-wrap"><table class="data" id="priceTable">
<thead><tr><th>Позиция</th><th>700ml (от)</th><th>1buyup (до)</th><th>Red Decanter</th><th>SKUPKA-ALKOGOL</th></tr></thead>
<tbody>{main}</tbody></table></div>
<div class="two-col">
<div><h2 class="sub">Ром и арманьяк (только 700ml, «от»)</h2><div class="table-wrap"><table class="data"><thead><tr><th>Позиция</th><th>Цена</th></tr></thead><tbody>{rum}</tbody></table></div></div>
<div><h2 class="sub">Ценовые сегменты (SKUPKA-ALKOGOL, ориентировочно)</h2><div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Стоимость</th></tr></thead><tbody>{seg}</tbody></table></div></div>
</div>
<p class="note">Это не рыночная цена и не гарантия выплаты. Одна и та же марка стоит по-разному из-за года, объёма, уровня жидкости, этикетки и комплектности. Например, у Yamazaki 18 потолок 32 000 ₽ у 1buyup против «от 80 000 ₽» у 700ml, поэтому цифру нужно перепроверить до сделки. Данные на {UPDATED}.</p>
</div>
</main>
{shared_blocks()}
""" + footer()


TOPICS = [
    dict(file="gde-prodat-elitnyy-alkogol.html", key="elite",
         nav="Элитный алкоголь",
         title=f"Продать элитный и коллекционный алкоголь в Москве: рейтинг скупок — {SITE}",
         desc="Куда продать элитный и коллекционный алкоголь в Москве: рейтинг скупок редкого виски, коньяка, вина и шампанского. Цена выкупа, срок оценки по фото, выезд, сохранность и упаковка.",
         h1="Куда продать элитный алкоголь?",
         eyebrow="Рейтинг · премиум и коллекционные бутылки",
         lead="Сравниваем компании, которые выкупают редкий виски, выдержанный коньяк, марочное вино и шампанское: кто открыто называет цену на дорогие бутылки, как быстро оценивает по фото и когда выезжает. Ниже — что считают элитным алкоголем, как определить ценность бутылки и на что обратить внимание до сделки."),
        dict(file="gde-prodat-viski.html", key="whisky",
         nav="Виски",
         title=f"Продать виски в Москве: рейтинг скупок, цены выкупа — {SITE}",
         desc="Куда продать виски в Москве: рейтинг скупок Macallan, Yamazaki, Highland Park, Glenfiddich, Hibiki. Цена выкупа, срок оценки по фото, выезд и то, что влияет на стоимость бутылки.",
         h1="Куда продать виски?",
         eyebrow="Рейтинг · Macallan, Yamazaki, Highland Park, Balvenie",
         lead="Какие скупки берут коллекционный и выдержанный виски — шотландский (Macallan, Glenfiddich, Glenlivet, Highland Park, Dalmore), японский (Yamazaki, Hakushu, Hibiki, Nikka), ирландский (Redbreast, Bushmills, Jameson) и американский бурбон. Показываем, у кого цены открыты, как быстро отвечают по фото и на каких условиях приезжают за бутылками."),
]
TOPIC_BY_KEY = {tp["key"]: tp for tp in TOPICS}

WHISKY_WORDS = ("Macallan", "Yamazaki", "Highland Park", "Dalmore", "Balvenie", "Johnnie Walker", "Jameson")
WHISKY_ROWS = [r for r in PRICES if r[0].startswith(WHISKY_WORDS)]


def whisky_count(col):
    return sum(1 for r in WHISKY_ROWS if r[col] not in ("—", ""))


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
        order = ["1buyup.ru", "700ml.ru", "reddecanter.ru", "room-alco.ru", "diamant-alko.ru"]
        rest = [c["domain"] for c in CARDS if c["domain"] not in order]
        order += rest
        over = {
            "1buyup.ru": dict(nom="Рынок и потолок выкупа по шести позициям виски", price="Виски, 6 поз.", price_n="рынок и «до»"),
            "700ml.ru": dict(nom="Открытый прайс: Macallan, Yamazaki, Highland Park, Balvenie, Johnnie Walker", price=f"{whisky_count(1)} позиций", price_n="цены «от»"),
            "reddecanter.ru": dict(nom="Редкий виски: Macallan M, Yamazaki 25, Dalmore 35", price=f"{whisky_count(3)} позиции", price_n="приблизительные"),
            "room-alco.ru": dict(nom="Круглосуточная оценка по фото, хранение, коробки и футляры"),
            "diamant-alko.ru": dict(nom="Остатки виски у ресторанов, баров и магазинов (от 10 бутылок)"),
        }
        for c in CARDS:
            if c["domain"] not in over:
                over[c["domain"]] = dict(price="Не публикует", price_n="цены на виски")
    out = []
    for i, d in enumerate(order, 1):
        c = by[d]
        m = dict(c["meta"])
        m.update(over.get(d, {}))
        if key == "whisky" and d in ("room-alco.ru", "diamant-alko.ru"):
            m["price"], m["price_n"] = "Не публикует", "цены на виски"
        out.append((c, m, i))
    return out


WHISKY_HOUSES = [
    ("Шотландия, Спейсайд: The Macallan (Макаллан), Glenfiddich (Гленфиддих), The Glenlivet (Гленливет), Balvenie (Балвени), Glenfarclas, BenRiach", "Macallan 18 Sherry Oak, Macallan M, Balvenie 21 PortWood, Glenfiddich, Glenlivet", "Самый коллекционный регион: односолодовые виски, выдержанные в бочках из-под хереса. Цену задают возраст, лимитированные серии и упаковка."),
    ("Шотландия, Хайленд и острова: Highland Park, Dalmore (Далмор), Glenmorangie", "Highland Park 18, Highland Park 50, Dalmore 35, Glenmorangie", "Многолетние выдержанные экземпляры. Highland Park 18 — одна из самых ходовых позиций в открытых прайсах, а Highland Park 50 и Dalmore 35 относят к ультрапремиуму: их оценивают по фото и, как правило, приблизительно."),
    ("Шотландия, Айла: Ardbeg, Laphroaig, Bowmore, Bruichladdich", "Ardbeg, Laphroaig, Bowmore, Bruichladdich", "Торфяной «дымный» стиль с узнаваемым характером. В цене возрастные и лимитированные выпуски, стандартные версии заметно дешевле."),
    ("Шотландия, купажи (blended): Johnnie Walker, Chivas Regal, Royal Salute, Grant's", "Johnnie Walker Blue Label, Chivas Regal, Royal Salute", "Купажи ценятся скромнее односолодовых, но топовые линейки (Blue Label, Royal Salute) и подарочные боксы скупкам интересны. Повседневные версии, например красная этикетка, к коллекционным не относят."),
    ("Япония: Yamazaki (Ямазаки), Hakushu (Хакушу), Hibiki (Хибики), Nikka (Никка), Suntory (Сантори)", "Yamazaki 18, Yamazaki 25, Hibiki, Hakushu, Nikka", "Японский виски дорожает быстрее многих шотландских: выпуск ограничен, а спрос на возрастные бутылки высок. По Yamazaki 18 «от» одной компании и «до» другой различаются в 2,5 раза; Yamazaki 25 у Red Decanter оценивают около 400 000 ₽."),
    ("Ирландия: Jameson, Redbreast (Рэдбрэст), Bushmills (Бушмилс), Midleton (Мидлтон), Tullamore Dew", "Jameson 18 Limited Reserve, Redbreast, Midleton", "Мягкий ирландский стиль, тройная перегонка. Скупкам интересны возрастные и лимитированные издания, массовые версии ценятся низко."),
    ("США и Канада: бурбон Jim Beam, Wild Turkey, Knob Creek, Blanton's; Jack Daniel's; канадский Crown Royal, Canadian Club", "Blanton's, Wild Turkey, Knob Creek, Crown Royal", "Бурбон делают в Кентукки, у него сладковатый вкус. Коллекционные бутылки редки: интересны лимитированные и штучные серии, а массовые линейки скупки обычно не берут."),
]

WHISKY_FAQ = [
("Какой виски считается ценным?",
 "Чаще всего ценят возрастной односолодовый виски известных винокурен — Macallan, Glenfiddich, Glenlivet, Highland Park, Dalmore, Balvenie, а также японские Yamazaki, Hakushu и Hibiki. На стоимость влияют возраст, серия, тираж, упаковка и состояние бутылки. Две бутылки одного названия могут стоить по-разному: у одной целая этикетка, коробка и документы, у другой потёртая упаковка. Спрос на конкретный выпуск определяет, как быстро бутылка найдёт покупателя."),
("Чем коллекционный виски отличается от обычного?",
 "Скупкам важны не вкус и не личные предпочтения, а ликвидность — насколько легко бутылку перепродать. Коллекционными считают возрастные выпуски, лимитированные серии, бутылки с историей и редкие экземпляры в подарочной упаковке. Повседневные позиции вроде Johnnie Walker Red Label, массового бурбона и купажей без возраста сюда не входят; из купажей берут только топовые линейки — Blue Label, Royal Salute."),
("На что смотрят при оценке?",
 "Оценщик сверяет название, возраст и серию, осматривает этикетку, пробку и упаковку, проверяет уровень содержимого. Падение уровня, подтёки и повреждения пробки снижают цену, а вскрытую бутылку обычно не принимают. У старых выпусков важны осадок и состояние стекла, у лимитированных — номер партии и документы. Оценка по фото предварительная: итоговую сумму называют после осмотра."),
("Как хранить виски до продажи?",
 "Бутылку держат вертикально (в отличие от вина), в тёмном прохладном месте без перепадов температуры. Свет, жара и сквозняки портят этикетку и пробку. Не открывайте бутылку и не переливайте виски в другую тару, а коробку, тубус и футляр сохраните: в упаковке виски стоит дороже. Сервант на солнечной стороне снижает цену заметнее, чем кажется."),
("Что прислать для оценки?",
 "Сделайте чёткие фото при дневном свете: лицевая и обратная этикетки, горлышко и пробка, уровень, коробка и документы. Напишите производителя, возраст, серию, объём, число бутылок, город и удобный способ связи — Telegram, WhatsApp, Viber или почту. Для партии составьте список. Нажимая «Оставить заявку», вы соглашаетесь на обработку персональных данных именно этой компанией, поэтому сначала прочтите её политику."),
]


def whisky_guide():
    rows = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in WHISKY_HOUSES)
    return f"""<section class="section" id="guide">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">О виски</span><h2 class="section-title">Какой виски<br>считают ценным</h2></div>
<p class="section-copy">Коллекционный виски покупают как раритет и как подарок: возрастные односолодовые выпуски Шотландии, японские бренды, ирландские и американские лимитированные серии. В таблице — регионы и имена, которые скупки встречают чаще всего.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Регион и винокурни</th><th>Позиции</th><th>Чем интересно</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="prose" style="margin-top:28px">
<p><strong>Как читать этикетку.</strong> Single malt — односолодовый виски одной винокурни, blended — купаж разных сортов и винокурен, single grain — зерновой виски одной винокурни. Возраст (12, 18, 25 лет) показывает самую молодую часть купажа. Cask strength — крепость без разбавления, Limited edition и Series — лимитированная серия. Цифра на этикетке влияет на цену, но не гарантирует её: важны ещё серия, тираж и сохранность.</p>
<p><strong>Что продают вместе с виски.</strong> Вместе с виски нередко предлагают коньяк, ром, шампанское, портвейн и коллекционные пустые бутылки с коробками. Если позиций несколько, перечислите их в одной заявке: цена партии зависит от состава, а один выезд обходится компании дешевле нескольких.</p>
<p><strong>Почему часть бутылок не берут.</strong> Вскрытый виски, низкий уровень, повреждённая пробка, самодельная этикетка и подделки — частые причины отказа. Дорогие выпуски (Macallan, Yamazaki, Hibiki) подделывают чаще остальных, поэтому проверка подлинности входит в оценку. Если бутылка досталась по наследству, документы о происхождении повышают шансы на сделку.</p>
</div>
{expert_note()}
</div>
</section>
"""


def whisky_assess():
    return """<section class="section ranking-section" id="assess">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Как оценивают виски</h2>
<p>Оценка складывается из знания винокурен, рынка аукционов и состояния конкретной бутылки: назвать цену по одному названию нельзя. Ниже — из чего получается итоговая сумма.</p>
<p><strong>Что смотрит оценщик.</strong> Сначала определяет производителя, возраст, серию и объём, затем осматривает этикетку, горлышко, пробку, акциз, стекло и упаковку. Отдельно проверяют уровень и целостность укупорки: сколы, подтёки и следы вскрытия снижают цену. Подлинность важнее всего у популярных позиций — Macallan, Yamazaki, Hibiki, Glenfiddich, Highland Park; у лимитированных серий сверяют номер партии и документы.</p>
<p><strong>Из чего складывается ценность.</strong> Цену формируют возраст, серия, популярность винокурни и состояние. Macallan, Yamazaki, Highland Park и Balvenie ликвидны и находят покупателя быстро, малоизвестные бренды могут ждать месяцами. Ориентир — мировые аукционы и цены импортёров, а не розница. По опубликованным таблицам выкуп составляет около 67–72% рыночной цены, у 1buyup по виски дисконт 29–33%; «до 90%» и «до 100%» — реклама.</p>
<p><strong>Что такое честная цена.</strong> Прозрачна та цена, для которой заранее названо, что осмотрят и от чего сумма изменится. «От» и «до» — не одно и то же: 700ml указывает нижний порог, 1buyup — потолок выкупа и рядом рыночную цену. Напрямую эти цифры не сравнить, поэтому спрашивайте, что именно имеет в виду компания. Бесплатная оценка по фото не отменяет осмотра: итоговую сумму называют после него.</p>
<p><strong>Как не потерять в цене.</strong> Не открывайте бутылку, не переливайте содержимое, сохраните коробку, тубус и документы: без упаковки цена может упасть до 30% (данные Red Decanter). Не держите бутылки на свету и в тепле и не откладывайте продажу надолго — пробка и этикетка со временем ухудшаются. Не верьте формуле «заберём любую бутылку» и сравните две-три оценки, прежде чем соглашаться.</p>
<p><strong>Кто покупает.</strong> Частные коллекционеры, бары и рестораны, магазины и те, кто собирает подарочные наборы. Одних интересуют только возрастные односолодовые выпуски, других — японский виски и лимитированные серии. Спрос меняется, поэтому цены в таблицах выше — ориентир, а не прогноз.</p>
</div>
</div>
</section>
"""


def whisky_more():
    return """<section class="section" id="regions">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Что ещё ценят среди виски</h2>
<p><strong>Другие страны и стили.</strong> Помимо шотландского, скупки интересуются японским (Yamazaki, Hakushu, Hibiki, Nikka, Suntory), ирландским (Redbreast, Bushmills, Jameson, Midleton, Tullamore Dew), американским бурбоном (Jim Beam, Wild Turkey, Knob Creek, Blanton's, Jack Daniel's) и канадским виски (Crown Royal, Canadian Club). Массовые версии этих марок недороги, а возрастные и лимитированные выпуски стоят заметно выше. Советские бутылки оценивают отдельно.</p>
<p><strong>Форматы и упаковка.</strong> Большие форматы, подарочные боксы и деревянные коробки прибавляют цену: у Highland Park, Macallan и Dalmore упаковка нередко входит в стоимость. Полный набор из серии, например вертикаль одной винокурни, можно продать единым лотом, но понадобятся перечень и фотографии.</p>
<p><strong>Как пишут названия.</strong> Бренды встречаются в разных написаниях: Macallan и «Макаллан», Glenfiddich и «Гленфиддих», Hibiki и «Хибики», Yamazaki и «Ямазаки», Bushmills и «Бушмилс», Redbreast и «Рэдбрэст». Если не уверены, укажите оба варианта и приложите фото этикетки.</p>
<p><strong>Как делают виски и почему это важно для цены.</strong> Односолодовый виски производят на одной винокурне из ячменного солода, купаж собирают из солодовых и зерновых спиртов нескольких дистиллерий ради ровного вкуса. Бочки из-под хереса, бурбона или портвейна задают характер напитка, а вместе с ним и ценность. Шотландский виски известен мягкостью Спейсайда и торфом Айлы, ирландский — тройной перегонкой, японский продолжает шотландскую традицию со своими особенностями. Для коллекционера особенно ценна бутылка, о которой известно, где, когда и как она сделана.</p>
<p><strong>Названия купажей и бурбонов.</strong> Купажи: Chivas Regal (Чивас Ригал), Royal Salute (Ройял Салют), Johnnie Walker (Black, White и Blue Label), White Horse, Grant's, Hankey Bannister, Old Parr. Американские: Jack Daniel's, Jim Beam, Wild Turkey, Knob Creek, Blanton's. Канадские: Crown Royal, Canadian Club, Black Velvet. Ирландские: Jameson, Midleton, Tullamore Dew, Redbreast, Bushmills. Односолодовые: Glenfarclas, Glenfiddich, Glenlivet, Singleton, Dalmore. Перечень — пример, а не обещание: готовность принять конкретную бутылку уточняйте у компании.</p>
</div>
</div>
</section>
"""


def whisky_deal():
    return """<section class="section ranking-section" id="deal">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Что учесть при сделке</h2>
<p>Общий порядок действий описан выше, в блоке «Как продать без лишней спешки». Для виски есть несколько своих деталей.</p>
<p><strong>Заявка и связь.</strong> Отправьте фото через форму на сайте компании, по почте, в Telegram, WhatsApp или Viber. Режим работы у компаний разный: одни принимают круглосуточно, другие с 8:00 до 1:00 или только по будням, поэтому сроки ответа отличаются. Предварительная оценка по фото всегда ориентировочная — попросите зафиксировать цену письменно.</p>
<p><strong>Встреча и осмотр.</strong> Специалист приезжает на адрес в Москве или области, либо вы встречаетесь в офисе. Оценщик проверяет состояние, сверяет серию и возраст, осматривает пробку и уровень. Если бутылка не соответствует описанию, цену пересматривают — иногда справедливо, иногда нет.</p>
<p><strong>Расчёт.</strong> Обычно это наличные или перевод. Не отдавайте бутылки, пока деньги не получены, и сохраняйте переписку.</p>
<p><strong>Этапы сделки.</strong> Определите, что именно продаёте, и снимите бутылку со всех сторон. Затем заполните заявку на сайте выбранной компании или отправьте снимки в мессенджер с описанием: производитель, возраст, серия, объём. Ориентировочную сумму называют после осмотра содержимого и упаковки; если она устроила, договоритесь о визите оценщика или о курьере. Не соглашайтесь на предоплату, уточните, когда цену могут пересмотреть, и при необходимости попросите договор до осмотра. Нажимая «Оставить заявку», вы даёте согласие на обработку данных — убедитесь, что условия компании вам понятны.</p>
<p><strong>Если вы не в Москве.</strong> Компании обычно принимают заявки и из других городов. Уточняйте, возможен ли выезд или отправка, например в Химки, Красногорск, Мытищи, Королёв, Подольск, Одинцово, Люберцы, Балашиху или Зеленоград. Условия логистики, страховки и оплаты везде свои.</p>
</div>
</div>
</section>
"""


def whisky_faq():
    items = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in WHISKY_FAQ)
    return f"""<section class="section ranking-section" id="faq">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Вопросы</span><h2 class="section-title">Вопросы<br>о продаже виски</h2></div>
<p class="section-copy">Ценные бутылки, оценка, хранение и что отправить в заявке.</p>
</div>
<div class="faq">{items}</div>
</div>
</section>
"""


ELITE_CATS = [
    ("Виски", "The Macallan, Glenfiddich, Glenmorangie, Highland Park, Balvenie, Yamazaki, Johnnie Walker (Black Label, Blue Label)", "Шотландский виски перегоняют уже несколько столетий. Оценивают винокурню, возраст, лимитированное издание и тираж; повседневные версии вроде Red Label к элитным не относят. Подробнее — на странице про виски."),
    ("Коньяк, арманьяк, кальвадос, бренди", "Hennessy, Rémy Martin, Martell, Courvoisier, Hine, Frapin, Camus, Metaxa, Torres, Saint-Rémy, Veterano, Vecchia Romagna", "Коньяк, арманьяк и кальвадос строго регламентированы — от сырья и урожая до выдержки. Коллекционные категории: XO, XXO, Hors d'Age, Grande Champagne; значение имеют год и состояние бутылки."),
    ("Вина Франции", "Бордо: Lafite Rothschild, Chateau Mouton Rothschild, Château Latour, Margaux, Haut-Brion, Cheval Blanc, Lafleur, Le Pin, Petrus. Бургундия: Domaine de la Romanée-Conti, Domaine Leroy, Leflaive, Meo-Camuzet", "Бордоские и бургундские вина оценивают по урожаю и классификации (Grand Cru, Premier Cru). Интересны также вина долины Роны (Кот-дю-Рон) и эльзасские."),
    ("Вина Италии, Испании, США, Австралии", "Gaja, Ornellaia, Sassicaia, Masseto, Bruno Giacosa, Soldera (Case Basse), Vega Sicilia, Pingus, Harlan Estate, Screaming Eagle, Penfolds Grange", "Итальянские вина ценят из Тосканы, Пьемонта, Венето и Сицилии, испанские — Vega Sicilia и Pingus. Американские и австралийские бутылки попадают в коллекции благодаря малым тиражам."),
    ("Шампанское", "Dom Pérignon, Cristal, Krug, Salon, Veuve Clicquot, Moët & Chandon, Bollinger", "В цене миллезимные выпуски и большие форматы: магнум и крупнее."),
    ("Ром, портвейн, херес, ликёры, абсент", "Havana Club, Zacapa, Caroni, Taylor's (Oporto), херес, ликёры, абсент, ракия", "Берут их не все компании и выборочно: важны возраст, редкость и сохранность. Сомневаетесь — отправьте фото; ракию и другие региональные напитки оценивают отдельно."),
    ("Алкоголь СССР и старые бутылки", "Массандра (Крым), грузинское и крымское вино, коньяки и вина, выпущенные до 1990 года", "Красное и белое вино, коньяки, коллекционная водка и ликёры советских лет интересны, если уцелели этикетка, пробка и уровень. Вскрытые бутылки обычно не берут."),
]

ELITE_FAQ = [
("Как понять, что бутылка элитная и сколько она может стоить?",
 "Элитной называют бутылку, ценность которой задают редкость, производитель, возраст и состояние: место производства, винокурня или шато, урожай, выдержка, миллезим, тираж. Повседневные позиции сюда обычно не входят, а шестизначные суммы свойственны супер-премиуму от 100 000 ₽. Найдите год, объём, серию и номер партии, осмотрите этикетку, пробку и уровень, затем сопоставьте цифры с открытыми прайсами скупок и аукционов. Не уверены — попросите консультацию специалиста: даже известный бренд без опыта оценить трудно. Рассматривать бутылку как инвестиционный актив рискованно, гарантий роста цены нет."),
("Можно ли продать подаренную или унаследованную бутылку, если в этом не разбираешься?",
 "Можно. Если коньяк или виски подарили непьющему человеку, не спешите открывать: сфотографируйте этикетки, пробку и уровень, найдите коробку и документы и отправьте снимки в две-три компании. Знакомых «в теме» спросить полезно, но сравнивать стоит с профессиональной оценкой. Магазинной цены за подарочную бутылку не ждите: выкуп всегда дешевле розницы, ведь компания закладывает свою выгоду."),
("Как не нарваться на подделку и испорченное хранение?",
 "Подделки чаще встречаются у самых дорогих позиций, а по фото отличить их сложно. Осмотрите вживую этикетку и контрэтикетку, шрифт, печать, знаки на стекле, номер партии, пробку и капсулу; снимите бутылку при хорошем свете. Бутылка должна быть запечатанной, а укупорка — целой: жара, свет и сквозняки портят содержимое и снижают цену. Для долгого хранения бытовой холодильник не подходит, нужны постоянная температура и умеренная влажность. Если сомневаетесь в подлинности, проверьте бутылку у эксперта до сделки."),
("Почему цены на одну и ту же бутылку так отличаются?",
 "Основа — мировые аукционные котировки и цены импортёров, а не магазинный ценник, поэтому в интернете встречаются и завышенные предложения, и демпинг. Разброс объясняют год, формат (магнум и литровые бутылки), состояние, упаковка и популярность выпуска. Не ориентируйтесь на одну цифру и не верьте «самой высокой цене»: сравните минимум два предложения. Цена в разы выше рынка так же подозрительна, как и намного ниже. Большую коллекцию обсуждайте отдельно: условия для партии из десятков бутылок обычно иные."),
("Работают ли скупки с регионами и другими странами?",
 "Многие заявляют работу по России и СНГ, но условия различаются. Жителям Екатеринбурга, Челябинска, Омска, Воронежа, Ростова-на-Дону, Самары, Перми, Уфы, Сочи, Владивостока, Симферополя и других городов обычно предлагают отправку транспортной компанией или встречу в Москве. Для Казахстана, Армении, Белоруссии, Украины, Литвы, Латвии и Эстонии многое зависит от таможенных правил — уточняйте заранее и не отправляйте бутылку без договорённостей. Выясните, кто отвечает за доставку, и упакуйте бутылки плотно."),
("Как безопаснее обсудить цену и расчёт?",
 "Обсуждайте условия там, где сохраняется переписка, и не вносите предоплату. Схема «цена по фото, расчёт на месте» нормальна, но итоговую сумму подтверждайте письменно до встречи. Узнайте, как проходит расчёт и нет ли комиссий (обычно их нет), и убедитесь, что вам обещана конкретная, а не «примерная» цена. На встречу возьмите оригинальную коробку и документы и внимательно прочтите договор. Если предлагают провести сделку через сторонний сервис, откажитесь. Не спешите: ответы нескольких компаний обычно приходят за день-два."),
]


def elite_guide():
    rows = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in ELITE_CATS)
    return f"""<section class="section ranking-section" id="guide">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">О категории</span><h2 class="section-title">Что относят<br>к элитному алкоголю</h2></div>
<p class="section-copy">Элитным называют алкоголь, чью ценность определяют не вкус одного вечера, а редкость, производитель, возраст и состояние бутылки. В таблице — основные категории и то, на что смотрят в каждой.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Примеры</th><th>Что учитывают</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="prose" style="margin-top:28px">
<p><strong>Почему одни бутылки дороже других.</strong> Страна и место производства, винокурня или хозяйство, урожай, выдержка, миллезим и ограниченный тираж превращают обычную бутылку в предмет коллекции. Многовековые традиции виноделия объясняют, почему одни экземпляры стоят десятки тысяч евро, а другие остаются малоценными: даже интересный современный выпуск не заинтересует коллекционеров, если тираж огромен. Цена зависит и от подлинности, упаковки и состояния, а не только от названия.</p>
<p><strong>На что обратить внимание перед продажей.</strong> Осмотрите бутылку: этикетку, пробку, уровень, упаковку; определите год и объём, соберите документы и чеки. Вскрывать и дегустировать ничего не нужно — открытые бутылки обычно не берут. Обратитесь в несколько компаний и помните, что цены на аукционе и в скупке различаются. Искать лучше по профилю: виски, коньяк, вино или шампанское — у каждой категории свои специалисты.</p>
</div>
{expert_note()}
</div>
</section>
"""


def elite_notes():
    return """<section class="section" id="notes">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">История, стили и нюансы продажи</h2>
<p><strong>Откуда берётся ценность.</strong> Рынок коллекционного алкоголя вырос из старых традиций. Шотландский виски делают столетиями, а за последние десятилетия он превратился из ремесла в мировую индустрию: винокурен сотни, и у каждой свой стиль. Коньяк производят в одноимённом регионе по строгим правилам; для арманьяка и кальвадоса действуют похожие. В вине решают сорт, почва и погода года, поэтому выпусков множество — от лёгких свежих белых до выдержанного красного бордо вроде Шато Мутон Ротшильд, Шато Марго или Петрюс. Коллекционеры особенно ценят бутылки, о которых известно всё: производство, год, тираж и история владения.</p>
<p><strong>Регионы и стили.</strong> Среди итальянских вин выделяют тосканских и пьемонтских производителей, среди французских — бургундские, бордоские и вина долины Роны. Интересны немецкий рислинг и эльзасские белые, хотя в скупках они попадаются реже. Мода на недооценённые регионы и возрождение забытых виноделен открывает элегантные вина из менее известных районов, но коллекционный рынок консервативен: чаще всего нужно легендарное имя. Лимитированный выпуск обычно ценится выше обычного.</p>
<p><strong>Как проходит продажа.</strong> Почти любую сделку можно начать с дистанционной оценки по фото, но затем потребуется осмотр. Составьте перечень бутылок и снимите каждую так, чтобы в кадр попала контрэтикетка: надёжно только то, что подтверждено документами. На встрече бутылки осматривает оценщик, а подготовка сэкономит время. После сделки сохраните договор или расписку. Если бутылку вы получили от прежнего владельца, комплект документов поможет подтвердить происхождение, а импортное происхождение без бумаг способно осложнить оценку. Ответы нескольких компаний проясняют картину и делают решение спокойнее.</p>
<p><strong>Цены в валюте.</strong> Итоги аукционов приводят в долларах, евро и фунтах, поэтому перед сравнением переведите их в рубли по курсу на дату продажи. Десятки тысяч долларов за редчайшую бутылку — не редкость, но с ожиданиями от обычной скупки это не связано: такие суммы бывают лишь у единичных позиций. Если собрание копилось годами, учитывайте и спрос: через год ситуация может измениться.</p>
</div>
</div>
</section>
"""


def elite_more():
    return """<section class="section ranking-section" id="more">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Что ещё важно знать перед продажей</h2>
<p><strong>Коллекция, хобби и вложение.</strong> Для многих коллекционирование алкоголя — увлечение на всю жизнь, а кто-то видит в редкой бутылке инвестиционный актив. Но и при покупке, и при продаже помните: цену определяет спрос, а не возраст. Бутылка, десятилетиями простоявшая в серванте, может оказаться малоценной, а выпуск ограниченного тиража, наоборот, дорожает. Пополняя собрание, покупатель смотрит на редкость, сохранность и документы, а не на красивую этикетку.</p>
<p><strong>Что не относится к алкоголю.</strong> Скупка алкоголя — не то же самое, что скупка антиквариата. Самовары, граммофоны, монеты, предметы искусства, мебель, электроника, оборудование и транспорт рейтинг не оценивает. Если компания занимается и антиквариатом, и алкоголем, как Alcovikup и TotalStok, это повод внимательнее проверить её специализацию.</p>
<p><strong>Какие вина встречаются реже.</strong> Кроме бордо и бургундского скупки интересуются эльзасским и другим французским сухим вином, южноитальянскими и сицилийскими бутылками, австрийским рислингом, крымским и грузинским вином советского розлива. Малоценными считают массовые полусладкие вина и большинство игристых без года. Спрос на недооценённые регионы растёт, но у скупок пока невысок. О виски подробнее — на странице про <a class="text-link" href="gde-prodat-viski.html">скупку виски</a>.</p>
<p><strong>Если вы живёте не в Москве.</strong> Когда бутылки находятся в Крыму, Сочи, Ростове-на-Дону, Перми, Воронеже, Омске, Екатеринбурге, Челябинске или Владивостоке, вопрос чаще решают отправкой. При продаже за рубеж — в Казахстан, Армению, Белоруссию, Литву, Великобританию и другие страны — действуют ограничения на ввоз и вывоз алкоголя, а для бывших союзных республик условия различаются: выясняйте их заранее и письменно. Если нужна встреча в Москве, договоритесь о времени и месте и не передавайте бутылки, пока сумма не подтверждена.</p>
<p><strong>Когда продавать, а когда подождать.</strong> Рано или поздно продавать приходится всем, кто собирает алкоголь, но оставлять бутылки без присмотра на месяцы не стоит: в серванте или бытовом холодильнике вино и коньяк портятся, и риск получить испорченную бутылку растёт. То, что лежит мёртвым грузом, лучше оценить сразу. Не открывайте бутылки на праздниках, если собираетесь продавать: в цене только запечатанные экземпляры. Когда закрывается ресторан или бар, остатки алкоголя продают одной партией.</p>
<p><strong>Как работают профессионалы.</strong> Оценщики тщательно осматривают бутылку: знаки на стекле, контрэтикетку, пробку, уровень жидкости. Дегустаций при оценке не проводят, а вскрытую бутылку обычно не принимают. Дорогие позиции с шестизначной ценой оценивают отдельно: ориентиром служат мировые аукционы, а не ценник магазина. Ситуации бывают разные: подаренная бутылка у непьющего владельца, распродажа остатков, частное собрание из десятков экземпляров, и каждой нужен свой подход, поэтому обращайтесь к тем, кто разбирается в вашей тематике — французских, итальянских или испанских винах, шотландском виски, коньяке. Особенности стилей Бордо, Бургундии, Тосканы, Пьемонта, Венето и Сицилии ценители различают сразу, а свежие малоценные выпуски интереса обычно не вызывают.</p>
<p><strong>Как общаться с компанией.</strong> Пишите на электронную почту, в Telegram или WhatsApp: переписка сохраняется. Оценщики должны отвечать на вопросы о цене и подлинности, не торопя вас. Демонстрационные фото из интернета не подходят — нужны снимки именно вашей бутылки. В заявке вы соглашаетесь на обработку данных компанией, а не нашим сайтом. Аукционные цены служат ориентиром, но не гарантируют итоговую сумму, поэтому записывайте условия и храните переписку.</p>
</div>
</div>
</section>
"""


def elite_faq():
    items = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in ELITE_FAQ)
    return f"""<section class="section" id="faq">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Вопросы</span><h2 class="section-title">Вопросы о продаже<br>элитного алкоголя</h2></div>
<p class="section-copy">Ценность, подделки, цена, регионы и безопасная сделка.</p>
</div>
<div class="faq">{items}</div>
</div>
</section>
"""


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
<p class="section-copy">Граница между обычным и элитным алкоголем условна. Для выкупа ориентиром служит премиум-класс от 10 000 ₽ и супер-премиум свыше 100 000 ₽.</p>
</div>
<div class="two-col">
<div><h3 class="sub" style="margin-top:0">Ценовые сегменты (SKUPKA-ALKOGOL)</h3><div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Стоимость</th></tr></thead><tbody>{seg}</tbody></table></div>
<p class="note">Цифры приблизительные: это не рыночная цена и не гарантия выплаты.</p></div>
<div><h3 class="sub" style="margin-top:0">Как выбрать скупку для дорогих бутылок</h3><div class="prose">
<p>У редких и дорогих позиций главное — подлинность и экспертиза. Red Decanter заявляет оценку сомелье, 700ml публикует самый подробный прайс, а 1buyup ставит рыночную цену рядом с потолком выкупа.</p>
<p>Попросите закрепить сумму письменно после фото и узнайте, чем компания подтверждает подлинность. Для партии из нескольких бутылок запросите предложения у двух-трёх компаний из разных групп (см. «Возможно, один оператор»).</p>
<p>Упаковка влияет на цену: без оригинальной коробки она иногда ниже до 30% (данные Red Decanter). Сохраните тубус, футляр и документы.</p></div></div>
</div>
<h3 class="sub">Примеры дорогих позиций из прайсов</h3>
<div class="table-wrap"><table class="data"><thead><tr><th>Позиция</th><th>Цена</th><th>Источник</th></tr></thead><tbody>{exr}</tbody></table></div>
<p class="note">Ориентиры, заявленные компаниями, — не оферта. Полный список — на странице <a class="text-link" href="{p}prices.html">«Цены выкупа»</a>.</p>
</div>
</section>
"""
    rows = "".join(f"<tr><td>{e(r[0])}</td><td>{e(r[1])}</td><td>{e(r[2])}</td><td>{e(r[3])}</td></tr>" for r in WHISKY_ROWS)
    return f"""<section class="section" id="topic">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Цены на виски</span><h2 class="section-title">Сколько платят<br>за виски</h2></div>
<p class="section-copy">Открытые цены на виски есть у трёх компаний из 20: 700ml, 1buyup и Red Decanter. Остальные называют сумму после того, как вы пришлёте фото.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Позиция</th><th>700ml (от)</th><th>1buyup (до; в скобках рынок)</th><th>Red Decanter (прибл.)</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Ориентиры заявлены самими компаниями: это не оферта и не гарантия выплаты. «От» — нижняя граница, «до» — потолок выкупа, поэтому столбцы напрямую не сравнить. Yamazaki 18: потолок 32 000 ₽ у 1buyup против «от 80 000 ₽» у 700ml.</p>
<h3 class="sub">От чего зависит цена виски</h3>
<div class="factors">
<article><h3>Винокурня и возраст</h3><p>Macallan, Yamazaki, Highland Park, Dalmore и Balvenie стоят заметно дороже массовых марок. Чем старше выпуск и известнее винокурня, тем выше интерес: Highland Park 18 — от 12 000 ₽, Highland Park 50 — около 750 000 ₽.</p></article>
<article><h3>Серия и тираж</h3><p>Лимитированные серии и штучные издания (Macallan in Lalique 55, Macallan M Decanter) оценивают отдельно: ориентир — аукционы, а не розница.</p></article>
<article><h3>Упаковка и хранение</h3><p>Целая этикетка, пробка, коробка, тубус и документы прибавляют цену; без упаковки она иногда ниже до 30% (данные Red Decanter). Хранить бутылку лучше вертикально, вдали от света и тепла.</p></article>
</div>
</div>
</section>
"""


def topic_cross(cur_key, depth):
    p = "../" * depth
    home = p or "./"
    items = [(home + "#ranking", "Продать алкоголь в Москве", "Общий рейтинг 20 скупок")]
    (ROOT / "politika-konfidencialnosti.html").write_text(privacy_page(), encoding="utf-8")
    (ROOT / "politika-cookie.html").write_text(cookie_page(), encoding="utf-8")
    (ROOT / "dlya-kompanii.html").write_text(company_page_for_orgs(), encoding="utf-8")
    (ROOT / "kontakty.html").write_text(contacts_page(), encoding="utf-8")
    (ROOT / "karta-sayta.html").write_text(sitemap_page(), encoding="utf-8")
    (ROOT / "redakcionnaya-politika.html").write_text(editorial_page(), encoding="utf-8")
    (ROOT / "otkaz-ot-otvetstvennosti.html").write_text(disclaimer_page(), encoding="utf-8")
    (ROOT / "pravila-polzovaniya.html").write_text(terms_page(), encoding="utf-8")
    write_data_files()
    write_llms_txt()
    write_includes()
    sm = [("", "1.0")] + [(tp["file"], "0.9") for tp in TOPICS] + [("prices.html", "0.8"), ("metodika.html", "0.7"), ("o-reitinge.html", "0.5"), ("dlya-kompanii.html", "0.4"), ("kontakty.html", "0.4"), ("karta-sayta.html", "0.3"), ("redakcionnaya-politika.html", "0.3")] + [(f"c/{c['slug']}.html", "0.7") for c in CARDS]
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
    return head(tp["title"], tp["desc"], path=tp["file"], ld=[breadcrumbs(("Главная", ""), (tp["h1"].rstrip("?"), tp["file"])), itemlist([c for c, m, i in rows])] + ([faq_ld(WHISKY_FAQ)] if tp['key'] == 'whisky' else [faq_ld(ELITE_FAQ)])) + header() + f"""
<main id="top">
<section class="topic-hero">
<div class="container">
<span class="eyebrow">{e(tp['eyebrow'])}</span>
<h1 class="page-title">{e(tp['h1'])}</h1>
<p class="lead">{e(tp['lead'])}</p>
<div class="hero-buttons"><a href="#ranking" class="btn btn-primary">Открыть рейтинг <span class="arrow">→</span></a><a href="#calc" class="btn btn-outline">Калькулятор выкупа</a></div>
</div>
</section>

{key_facts(None, tp['key'])}
<section class="section ranking-section" id="ranking">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Рейтинг</span><h2 class="section-title">{e('Скупки виски' if tp['key']=='whisky' else 'Скупки элитного алкоголя')}<br>в Москве</h2></div>
<p class="section-copy">{'Компании сравниваются по открытым ценам на виски, скорости оценки и условиям сделки. Принципы расчёта — в <a class="text-link" href="metodika.html">методике</a>.' if tp['key']=='whisky' else 'Скупки дорогих и редких бутылок сравниваются по скорости оценки, ценам и условиям сделки. Принципы расчёта — в <a class="text-link" href="metodika.html">методике</a>.'}</p>
</div>
<div class="company-list" id="rankingTable">
{cards_html}
</div>
<p class="note">Сроки оценки и режимы работы — заявления компаний. «Не публикует» означает, что цен нет на проверенных страницах сайта. Порядок компаний на этой странице определён профильностью для темы и полнотой данных, а не качеством услуг; подробнее — в методике.</p>
</div>
</section>

{compare_section([(c, m) for c, m, i in rows])}
{topic_extra(tp['key'], 0)}
{whisky_guide() + whisky_assess() + whisky_more() + whisky_deal() + whisky_faq() if tp['key'] == 'whisky' else elite_guide() + elite_notes() + elite_more() + elite_faq()}
{shared_blocks()}
{topic_cross(tp['key'], 0)}
{feedback_cta()}
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


def sitemap_page():
    """Карта сайта для посетителей (HTML)."""
    def ul(items):
        return '<ul class="sitemap-list">' + "".join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in items) + "</ul>"
    main_pages = [("./", "Главная: рейтинг скупок алкоголя в Москве")] + [(tp["file"], tp["h1"].rstrip("?")) for tp in TOPICS] + [("prices.html", "Цены выкупа алкоголя в Москве")]
    companies = [(f"c/{c['slug']}.html", c["name"]) for c in CARDS]
    info = [("metodika.html", "Методика составления рейтинга"), ("o-reitinge.html", "О рейтинге и эксперте"), ("dlya-kompanii.html", "Для организаций: исправить данные"), ("kontakty.html", "Контакты")]
    docs = [("redakcionnaya-politika.html", "Редакционная политика"), ("otkaz-ot-otvetstvennosti.html", "Отказ от ответственности"), ("pravila-polzovaniya.html", "Правила пользования"), ("politika-konfidencialnosti.html", "Политика конфиденциальности"), ("politika-cookie.html", "Политика cookie")]
    body = f"""<div class="sitemap-grid">
<div><h2>Разделы</h2>{ul(main_pages)}<h2>Информация</h2>{ul(info)}<h2>Документы</h2>{ul(docs)}</div>
<div><h2>Компании рейтинга</h2>{ul(companies)}</div>
</div>"""
    return simple_page(f"Карта сайта — {SITE}", f"Карта сайта {SITE}: все разделы, страницы компаний рейтинга скупок алкоголя, информация и документы.", "karta-sayta.html", "Карта сайта", "Все страницы сайта: рейтинги, обзоры компаний, методика и документы.", body, eyebrow="Навигация")


def privacy_page():
    op = f"{ph('name', 'ФИО оператора')}{opt('inn', ', ИНН {}')}"
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
<h2>1. Общие положения</h2>
<p>Настоящая политика описывает, как сайт «{SITE}» ({SITE_URL}) обрабатывает персональные данные посетителей. Оператор персональных данных — {op}{opt('address', ', адрес для обращений: {}')}, e-mail для обращений: {ph('email', 'e-mail')}. Политика составлена в соответствии с Федеральным законом от 27.07.2006 № 152-ФЗ «О персональных данных».</p>
<p>Сайт — информационный справочник, в котором сравниваются компании, скупающие алкоголь. Сайт не оказывает и не продаёт услуги и не рассчитан на лиц младше 18 лет.</p>
<h2>2. Какие данные мы обрабатываем</h2>
<ul>
<li><strong>Технические данные:</strong> IP-адрес, тип браузера и устройства, адреса просмотренных страниц, дата и время запроса. Они автоматически попадают в журналы сервера хостинга.</li>
<li><strong>Данные веб-аналитики:</strong> сервис «Яндекс Метрика» (ООО «ЯНДЕКС») собирает обезличенные сведения о визитах: просмотренные страницы, клики, прокрутку, движения мыши, источник перехода, тип устройства и браузера, примерный регион по IP-адресу. Включён «Вебвизор»: он записывает действия посетителя на странице, но не передаёт содержимое полей форм.</li>
<li><strong>Файлы cookie:</strong> подробности — в <a class="text-link" href="politika-cookie.html">политике cookie</a>.</li>
<li><strong>Данные из формы отзыва:</strong> имя (по желанию), оценка и текст отзыва.</li>
<li><strong>Данные из формы для организаций:</strong> название организации, сайт, имя контактного лица, e-mail, текст обращения, ссылки на подтверждающие материалы.</li>
<li><strong>Письма на e-mail</strong>: данные, которые вы указали в письме.</li>
</ul>
<p>Просим не указывать в отзывах и обращениях лишнего: номера документов, банковские данные, адреса и телефоны третьих лиц.</p>
<h2>3. Цели обработки</h2>
<ul>
<li>публикация отзывов читателей после проверки;</li>
<li>рассмотрение обращений организаций об исправлении данных и претензий;</li>
<li>обеспечение работы и безопасности сайта;</li>
<li>ответы на ваши письма и запросы.</li>
</ul>
<h2>4. Основание обработки</h2>
<p>Обработка идёт с вашего согласия, которое вы выражаете, отправляя форму и отметив согласие, а также в случаях, предусмотренных законом. Согласие можно отозвать, написав на {ph('email', 'e-mail')}.</p>
<h2>5. Передача данных третьим лицам</h2>
<p>Мы не продаём персональные данные. Их может обрабатывать хостинг-провайдер, на серверах которого размещён сайт. Данные веб-аналитики обрабатывает «Яндекс Метрика» по собственным правилам (<a class="text-link" href="https://yandex.ru/legal/confidential/" rel="noopener nofollow">политика конфиденциальности Яндекса</a>). Чтобы показать шрифты, браузер посетителя обращается к сервису Google Fonts, и ему передаются IP-адрес и сведения о браузере. Оператор вправе раскрыть данные по обоснованному запросу уполномоченных органов.</p>
<h2>6. Хранение</h2>
<p>Данные хранятся не дольше, чем нужно для целей обработки. Опубликованный отзыв остаётся на сайте, пока вы не попросите удалить или изменить его. Обращения организаций хранятся на время рассмотрения и ещё столько, сколько необходимо для подтверждения принятых решений.</p>
<h2>7. Ваши права</h2>
<p>Вы вправе узнать, какие ваши данные мы обрабатываем, потребовать их уточнения, блокировки или удаления, а также отозвать согласие. Для этого напишите на {ph('email', 'e-mail')}. Ответим в сроки, установленные законом. Вы также можете обратиться в Роскомнадзор.</p>
<h2>8. Защита данных</h2>
<p>Мы принимаем организационные и технические меры, чтобы защитить данные от случайного или неправомерного доступа, изменения, раскрытия и уничтожения.</p>
<h2>9. Изменения политики</h2>
<p>Действующая редакция всегда опубликована на этой странице. Если мы начнём применять новые инструменты, политику обновят до их запуска. Метрику можно отключить расширением браузера («Блокировщик Метрики» и подобные) или <a class="text-link" href="https://yandex.ru/support/metrica/general/opt-out.html" rel="noopener nofollow">по инструкции Яндекса</a>.</p>
<h2>10. Контакты</h2>
<p>{op}{opt('address', '<br>Адрес: {}')}<br>E-mail: {ph('email', 'e-mail')}</p>
"""
    return simple_page(f"Политика конфиденциальности — {SITE}", "Как сайт обрабатывает персональные данные посетителей: какие данные, для чего, какие у пользователей права и как связаться с оператором.",
                       "politika-konfidencialnosti.html", "Политика конфиденциальности", "Как мы обращаемся с персональными данными посетителей сайта.", body)


def cookie_page():
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
<h2>Что такое cookie</h2>
<p>Cookie — небольшие файлы, которые сайт сохраняет в браузере. Они помогают запоминать ваши действия, например то, что вы уже ответили на вопрос о cookie.</p>
<h2>Какие cookie использует сайт</h2>
<div class="table-wrap"><table class="data"><thead><tr><th>Название</th><th>Назначение</th><th>Срок</th><th>Тип</th></tr></thead><tbody>
<tr><td>age_confirmed</td><td>Запоминает, что вы подтвердили возраст (18+), и окно больше не показывается. Дублируется в localStorage браузера.</td><td>12 месяцев</td><td>Необходимый, собственный</td></tr>
<tr><td>cookie_consent</td><td>Запоминает, что вы нажали «Согласен» в плашке о cookie, и она больше не появляется. Дублируется в localStorage браузера.</td><td>12 месяцев</td><td>Необходимый, собственный</td></tr>
<tr><td>_ym_uid, _ym_d, _ym_isad, _ym_visorc, _ym_metrika_enabled</td><td>Сервис «Яндекс Метрика»: различает посетителей, считает число и длительность визитов, обеспечивает работу «Вебвизора». Сведения обезличены.</td><td>до 12 месяцев</td><td>Аналитический, сторонний (Яндекс)</td></tr>
</tbody></table></div>
<p>Рекламные сети на сайте не подключены.</p>
<h2>Сторонние сервисы</h2>
<p>Чтобы показать шрифты, браузер обращается к сервису Google Fonts, а для статистики — к «Яндекс Метрике». Сам Google Fonts cookie не требует, но получает ваш IP-адрес и сведения о браузере. Подробнее — в <a class="text-link" href="politika-konfidencialnosti.html">политике конфиденциальности</a>.</p>
<h2>Как управлять cookie</h2>
<p>Файлы cookie можно удалить или запретить их сохранение в настройках браузера. Если удалить cookie_consent, плашка появится снова. Отключение необходимых cookie на работу сайта не влияет.</p>
<h2>Яндекс Метрика</h2>
<p>Сайт использует «Яндекс Метрику» (ООО «ЯНДЕКС») для статистики визитов: какие страницы читают, откуда приходят, как пользуются сайтом. Включён «Вебвизор», воспроизводящий действия посетителя на странице; содержимое полей форм он не записывает. Отказаться можно, отключив cookie в браузере, установив блокировщик Метрики или воспользовавшись <a class="text-link" href="https://yandex.ru/support/metrica/general/opt-out.html" rel="noopener nofollow">инструкцией Яндекса</a>.</p>
<h2>Контакты</h2>
<p>Вопросы об обработке данных: {ph('email', 'e-mail')}. Оператор: {ph('name', 'ФИО оператора')}.</p>
"""
    return simple_page(f"Политика cookie — {SITE}", "Какие файлы cookie использует сайт, для чего они нужны и как ими управлять.",
                       "politika-cookie.html", "Политика cookie", "Какие cookie использует сайт и как ими управлять.", body)


def company_page_for_orgs():
    body = f"""
<p>Рейтинг построен на открытых данных, поэтому в нём бывают неточности и устаревшие сведения. Если вы представляете компанию из списка, напишите нам: мы проверим информацию и при необходимости поправим карточку.</p>
<h2>С чем можно обратиться</h2>
<ul>
<li>устаревшие или неверные контакты, адрес, график работы, срок оценки;</li>
<li>цены и условия сделки, указанные с ошибкой;</li>
<li>фактические ошибки в обзоре;</li>
<li>претензии к опубликованным материалам.</li>
</ul>
<h2>Как рассматриваем обращения</h2>
<ol class="steps-list">
<li>Заполните форму ниже или напишите на {ph('email', 'e-mail')}: укажите, что именно неверно, и приложите ссылку на страницу сайта, документ или другое подтверждение.</li>
<li>Мы сверяем сведения с открытыми источниками и отвечаем в течение {CLAIM_DAYS} рабочих дней.</li>
<li>Если ошибка подтверждается, правим данные и при необходимости пересчитываем оценку; если нет — объясняем, почему.</li>
<li>По вашей просьбе в карточке можно разместить краткий ответ компании.</li>
</ol>
<h2>Что остаётся без изменений</h2>
<ul>
<li>Оценка, посчитанная по формуле из <a class="text-link" href="metodika.html#score">методики</a>, если исходные данные верны.</li>
<li>Выводы обзоров, опирающиеся на проверяемые факты: оценочные суждения мы не убираем по просьбе компании.</li>
<li>Заявления компаний о себе («5000 сделок», «до 90% рынка»): мы лишь помечаем их как заявления и не проверяем.</li>
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
<p class="note">Если форма не открывается или проще написать письмом — используйте {ph('email', 'e-mail')}.</p>
"""
    return simple_page(f"Для компаний: как исправить данные в карточке — {SITE}", "Для компаний из рейтинга: как сообщить об ошибке в карточке, направить претензию и получить ответ редакции.",
                       "dlya-kompanii.html", "Для организаций", "Заметили неточность в карточке своей компании? Сообщите — проверим и исправим.", body, eyebrow="Обратная связь")


def contacts_page():
    body = f"""
<p>«{SITE}» — независимый справочник, а не скупка алкоголя. Здесь можно связаться с редакцией: задать вопрос о рейтинге, сообщить об ошибке или предложить компанию для сравнения.</p>
<h2>Редакция</h2>
<p>Оператор сайта: {ph('name', 'ФИО оператора')}{opt('inn', '<br>ИНН: {}')}{opt('address', '<br>Адрес для обращений: {}')}<br>E-mail: {ph('email', 'e-mail')}{opt('phone', '<br>Телефон: {}')}{opt('telegram', '<br>Telegram: {}')}</p>
<h2>Куда написать</h2>
<ul>
<li><strong>Вы представляете компанию из рейтинга</strong> и нашли ошибку или хотите направить претензию — <a class="text-link" href="dlya-kompanii.html">страница для компаний</a>.</li>
<li><strong>Вы читатель</strong>: хотите указать на неточность или рассказать о своей сделке — напишите на e-mail редакции.</li>
<li><strong>Вопросы о персональных данных</strong> (доступ, удаление, отзыв согласия) — на тот же адрес, подробности в <a class="text-link" href="politika-konfidencialnosti.html">политике конфиденциальности</a>.</li>
</ul>
<p class="note">Мы не покупаем алкоголь и не принимаем бутылки. Чтобы продать коньяк, виски или вино, свяжитесь напрямую с выбранной компанией — её контакты есть в карточке.</p>
"""
    return simple_page(f"Контакты редакции — {SITE}", "Как связаться с редакцией рейтинга скупок алкоголя: e-mail, Telegram, реквизиты оператора и страница для компаний.",
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
             f"- [{TOPICS[1]['h1'].rstrip('?')}]({SITE_URL}/{TOPICS[1]['file']}): цены на виски и компании, которые его покупают",
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


def add_crumbs(html, is_company):
    """Видимые хлебные крошки: Главная / раздел / страница (на главной не нужны)."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S)
    if not m or "<main" not in html:
        return html
    title = re.sub(r"<[^>]+>", " ", m.group(1))
    title = re.sub(r"\s+", " ", title).replace(" ?", "?").strip().rstrip("?")
    html = re.sub(r'<nav class="crumbs"[^>]*>.*?</nav>\s*', "", html, count=1, flags=re.S)
    p = "../" if is_company else ""
    trail = f'<a href="{p or "./"}">Главная</a>'
    if is_company:
        trail += f' / <a href="{p}#ranking">Рейтинг скупок</a>'
    trail += f" / <span aria-current=\"page\">{title}</span>"
    crumbs = f'<nav class="crumbs" aria-label="Хлебные крошки">{trail}</nav>\n'
    i = html.index("<main")
    j = html.index('<span class="eyebrow">', i)
    return html[:j] + crumbs + html[j:]


def postprocess(html):
    """Семантика таблиц: scope у заголовков."""
    html = re.sub(r"(<thead>.*?</thead>)", lambda m: m.group(1).replace("<th>", '<th scope="col">'), html, flags=re.S)
    html = re.sub(r"(<table class=\"facts-table\">.*?</table>)", lambda m: m.group(1).replace("<th>", '<th scope="row">'), html, flags=re.S)
    return html


def editorial_page():
    if PLACEMENT_IS_FREE:
        money = "<p>Попасть в рейтинг можно бесплатно. Редакция не получает от компаний вознаграждения за место в списке, оценку или текст обзора.</p>"
    else:
        money = f"<p>{ph('name', 'опишите, получает ли сайт вознаграждение от компаний; если да — размещение является рекламой и требует маркировки')}</p>"
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
{expert_block()}
<h2>1. Принципы</h2>
<ul>
<li>Компании сравниваются по одним открытым данным и по единым правилам.</li>
<li>Факты и заявления разделены: «5000 сделок» или «до 90% рынка» мы подписываем как заявления и не выдаём за проверенное.</li>
<li>О минусах пишем так же подробно, как о плюсах.</li>
<li>Мы не оцениваем качество услуг и не гарантируем исход сделки: оценка показывает прозрачность и открытость компании.</li>
</ul>
<h2>2. Источники</h2>
<p>Открытые сайты компаний. Если сайт был недоступен для автоматической проверки, мы брали фрагменты поисковой выдачи — в таком случае это отмечено в карточке. Данные собраны 30 сентября 2026 г. Оценки и отзывы с карт в расчёте не участвуют.</p>
<h2>3. Как считается оценка</h2>
<p>Оценка редакции складывается из трёх параметров по правилам из <a class="text-link" href="metodika.html#score">методики</a>. Исходные данные и итог по каждой компании открыты: <a class="text-link" href="data/companies.json">companies.json</a>.</p>
<h2>4. Как отбираем компании</h2>
<p>Компании для сравнения выбирает редакция. Если вы представляете компанию и хотите, чтобы её рассмотрели, воспользуйтесь <a class="text-link" href="dlya-kompanii.html">страницей для компаний</a>.</p>
<h2>5. Исправления и право ответа</h2>
<p>Если мы ошиблись, напишите через <a class="text-link" href="dlya-kompanii.html">страницу для компаний</a> или на {ph('email', 'e-mail')}. Проверка занимает до {CLAIM_DAYS} рабочих дней, подтверждённые ошибки исправляем. По просьбе компании в карточке можно опубликовать её краткий ответ.</p>
<h2>6. Независимость и конфликт интересов</h2>
{money}
<p>Если у редакции появятся отношения с оцениваемой компанией — владение, партнёрство или оплата, — мы раскроем их на сайте до публикации.</p>
<h2>7. Обновление данных</h2>
<p>Сведения устаревают. Дата сбора указана в методике; при заметных изменениях карточки обновляются.</p>
"""
    return simple_page(f"Редакционная политика — {SITE}", "Принципы рейтинга скупок алкоголя: источники данных, отбор компаний, исправление ошибок и независимость редакции.",
                       "redakcionnaya-politika.html", "Редакционная политика", "Как составляется рейтинг и что мы делаем, когда ошибаемся.", body)


def disclaimer_page():
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
<h2>1. Информационный характер</h2>
<p>Вся информация на сайте «{SITE}» (рейтинг, обзоры, оценки, цены, сроки) носит исключительно справочный характер. Она не является публичной офертой, индивидуальной консультацией (юридической, финансовой или иной) или рекомендацией заключить сделку.</p>
<h2>2. Сайт не оказывает услуг</h2>
<p>Сайт не оказывает и не продаёт услуги, не продаёт алкоголь, не принимает бутылки и деньги и не участвует в сделках между пользователями и компаниями. За условия и итог таких сделок отвечают их участники.</p>
<h2>3. Актуальность и точность</h2>
<p>Информация собрана по открытым источникам на определённую дату и может устареть. Цены и сроки — заявления компаний, они могут меняться без уведомления. Мы стараемся поддерживать данные актуальными, но не гарантируем их полноту и точность в любой момент. Перед сделкой самостоятельно уточняйте условия на сайтах компаний.</p>
<h2>4. Оценка редакции</h2>
<p>Оценка рассчитывается по формальным признакам из открытых данных (прозрачность цен, скорость и удобство, открытость компании). Она не отражает качество услуг, надёжность или деловую репутацию компании и не гарантирует результат сделки.</p>
<h2>5. Законность деятельности компаний</h2>
<p>Мы не проверяем, есть ли у компаний разрешительные документы, законна ли их деятельность и соблюдают ли они требования законодательства, в том числе об обороте алкогольной продукции. Вы сами оцениваете риски и соблюдаете закон, включая возрастные ограничения.</p>
<h2>6. Внешние ссылки и контент третьих лиц</h2>
<p>На сайте есть ссылки на сайты компаний. Мы не контролируем их содержание и не отвечаем за него. Отзывы и обращения пользователей выражают мнение их авторов.</p>
<h2>7. Возрастное ограничение</h2>
<p>На сайте размещена информация об алкогольной продукции, он рассчитан на лиц старше 18 лет. Чрезмерное потребление алкоголя вредит здоровью.</p>
<h2>8. Ограничение ответственности</h2>
<p>В пределах, допустимых законом, администрация сайта не отвечает за убытки, возникшие из-за использования опубликованной информации. Если вы заметили ошибку, сообщите через <a class="text-link" href="dlya-kompanii.html">страницу для организаций</a> или на {ph('email', 'e-mail')}.</p>
"""
    return simple_page(f"Отказ от ответственности — {SITE}", "Условия использования информации сайта: справочный характер, актуальность данных, оценка редакции, внешние ссылки.",
                       "otkaz-ot-otvetstvennosti.html", "Отказ от ответственности", "Что означает информация на сайте и за что мы не отвечаем.", body)


def terms_page():
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
<h2>1. Общие положения</h2>
<p>Настоящие правила регулируют использование сайта «{SITE}» ({SITE_URL}), принадлежащего {ph('name', 'ФИО или наименование оператора')}. Продолжая пользоваться сайтом, вы соглашаетесь с правилами. Сайт является информационным ресурсом и не оказывает услуг. Подробнее — в <a class="text-link" href="otkaz-ot-otvetstvennosti.html">отказе от ответственности</a>.</p>
<h2>2. Возраст</h2>
<p>Сайт рассчитан на лиц старше 18 лет. Если вам нет 18, пожалуйста, покиньте сайт.</p>
<h2>3. Использование материалов</h2>
<p>Материалы сайта можно цитировать, указывая источник и ставя активную ссылку на страницу. Копировать материалы целиком, а также использовать их в коммерческих целях без согласия администрации нельзя.</p>
<h2>4. Отзывы и обращения</h2>
<ul>
<li>Пишите только о том, что пережили лично или можете подтвердить.</li>
<li>Не размещайте оскорбления, угрозы, рекламу, персональные данные третьих лиц и необоснованные сведения, порочащие честь и деловую репутацию.</li>
<li>Мы проверяем отзывы перед публикацией и вправе отклонить или удалить материал, нарушающий эти правила или закон.</li>
<li>За содержание отзыва отвечает его автор. Отправляя отзыв, вы соглашаетесь на его публикацию.</li>
<li>Обработка персональных данных описана в <a class="text-link" href="politika-konfidencialnosti.html">политике конфиденциальности</a>.</li>
</ul>
<h2>5. Запрещённые действия</h2>
<p>Запрещено нарушать работу сайта, пытаться получить несанкционированный доступ и использовать сайт в противоправных целях. Индексация страниц поисковыми системами разрешена.</p>
<h2>6. Изменения и применимое право</h2>
<p>Мы вправе менять правила; действующая редакция всегда размещена на этой странице. К отношениям применяется право Российской Федерации.</p>
<h2>7. Контакты</h2>
<p>{ph('name', 'ФИО оператора')}{opt('inn', ', ИНН {}')}, e-mail: {ph('email', 'e-mail')}. Страница <a class="text-link" href="kontakty.html">«Контакты»</a>.</p>
"""
    return simple_page(f"Правила пользования сайтом — {SITE}", "Правила использования сайта: возрастное ограничение, цитирование материалов, правила отзывов и обращений.",
                       "pravila-polzovaniya.html", "Правила пользования сайтом", "Как пользоваться сайтом и что запрещено.", body)


ROBOTS_META = "index, follow, max-image-preview:large" if ALLOW_INDEXING else "noindex, nofollow, noarchive"
# Служебные юридические страницы: не индексируются (ссылки с них поисковики обходят), в sitemap не попадают
NOINDEX_PAGES = {"politika-konfidencialnosti.html", "politika-cookie.html", "otkaz-ot-otvetstvennosti.html", "pravila-polzovaniya.html"}


def write_seo_files(pages):
    urls = "\n".join(
        f"<url><loc>{SITE_URL}/{p}</loc><lastmod>{BUILD_DATE}</lastmod><priority>{pr}</priority></url>" for p, pr in pages)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n', encoding="utf-8")
    if not ALLOW_INDEXING:
        (ROOT / "robots.txt").write_text("# Сайт закрыт от индексации\nUser-agent: *\nDisallow: /\n", encoding="utf-8")
        (ROOT / ".htaccess").write_text('<IfModule mod_headers.c>\nHeader set X-Robots-Tag "noindex, nofollow, noarchive"\n</IfModule>\n', encoding="utf-8")
        return
    if INCLUDE_MODE == "ssi":
        (ROOT / ".htaccess").write_text("# Шапка и подвал подключаются директивами SSI (<!--#include virtual=\"/includes/...\" -->)\nOptions +Includes\nAddType text/html .html\nAddOutputFilter INCLUDES .html\n\n# Старый адрес страницы про вино\nRedirect 301 /gde-prodat-elitnoe-vino.html /gde-prodat-viski.html\n", encoding="utf-8")
    else:
        (ROOT / ".htaccess").unlink(missing_ok=True)
    bots = "".join(f"User-agent: {b}\nAllow: /\n\n" for b in AI_BOTS)
    (ROOT / "robots.txt").write_text(f"# Поисковые и ИИ-краулеры допускаются явно; служебные папки закрыты для всех\n{bots}User-agent: *\nAllow: /\nDisallow: /standalone/\nDisallow: /tools/\nDisallow: /includes/\nDisallow: /send.php\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")


# Фото-полосы между текстовыми блоками: (файл страницы) -> [(id секции, перед которой вставить, картинка, подпись, текст, ссылка, текст кнопки)]
# Контрастные вставки-цитаты между блоками (без кнопок и перелинковки): (id секции, перед которой вставить, картинка-класс, подпись, текст, —, —)
BANDS = {
    "index.html": [
        ("calc", "banner2.jpg", "Прежде чем продавать", "Сравните не только цену, но и условия сделки: срок оценки, способ оплаты и выезд курьера.", "#choose", "Пять вопросов перед сделкой"),
        ("prepare", "banner3.jpg", "Подготовка", "Коробка, документы и целая этикетка заметно влияют на итоговую цену выкупа.", "#prepare", "Как подготовить бутылку"),
    ],
    "gde-prodat-elitnyy-alkogol.html": [
        ("topic", "banner2.jpg", "Редкие бутылки", "Для дорогих бутылок особенно важны подлинность, комплектность и условия хранения.", "#guide", "Что считается элитным"),
        ("faq", "banner3.jpg", "Перед сделкой", "Сфотографируйте этикетку, пробку и уровень жидкости — так оценка пройдёт быстрее.", "#prepare", "Как подготовить бутылку"),
    ],
    "gde-prodat-viski.html": [
        ("topic", "banner.jpg", "Виски", "Цена зависит от винокурни, возраста, серии и сохранности бутылки.", "#guide", "Какой виски ценится"),
        ("faq", "banner2.jpg", "Перед сделкой", "Целая пробка, уровень и оригинальная коробка помогают сохранить стоимость виски.", "#assess", "Как оценивают виски"),
    ],
}



ICONS = {
    "bottle": '<path d="M10 2h4v4l1.5 3v11a2 2 0 0 1-2 2h-3a2 2 0 0 1-2-2V9L10 6z"/><path d="M8.5 13h7"/>',
    "search": '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.2-4.2"/>',
    "shield": '<path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6z"/><path d="m9 12 2 2 4-4"/>',
    "clock": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>',
    "tag": '<path d="M3 12V4h8l9 9-8 8z"/><circle cx="8" cy="8.5" r="1.2"/>',
    "doc": '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M9.5 12h5M9.5 16h5"/>',
    "pin": '<path d="M12 21s6-5.5 6-11a6 6 0 1 0-12 0c0 5.5 6 11 6 11z"/><circle cx="12" cy="10" r="2.2"/>',
    "star": '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
}
ICON_RULES = [("оцен", "search"), ("цен", "tag"), ("стоим", "tag"), ("подлин", "shield"), ("провер", "shield"), ("хран", "bottle"),
              ("упаков", "bottle"), ("назван", "doc"), ("заявк", "doc"), ("связ", "doc"), ("расч", "tag"), ("встреч", "clock"),
              ("этап", "clock"), ("когда", "clock"), ("москв", "pin"), ("город", "pin"), ("страны", "pin"), ("кто", "star")]
ICON_CYCLE = ["bottle", "search", "shield", "tag", "doc", "clock", "pin", "star"]


def _icon(title, i):
    t = title.lower()
    name = next((n for k, n in ICON_RULES if k in t), ICON_CYCLE[i % len(ICON_CYCLE)])
    return f'<span class="pcard-ico" aria-hidden="true"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg></span>'


def decorate_prose(page):
    """Блоки .prose из абзацев «<strong>Заголовок.</strong> текст»: короткие пункты — парами карточек одной высоты,
    длинные — строками «заголовок слева, текст справа». Вступительные абзацы остаются обычным текстом."""
    def card(t, body):
        return f'<article class="pcard"><h3>{t}</h3><p>{body}</p></article>'

    def row(t, body):
        return f'<div class="prow"><h3>{t}</h3><p>{body}</p></div>'

    def conv(m):
        inner = m.group(2)
        ps = re.findall(r"<p>.*?</p>", inner, flags=re.S)
        strong = [p for p in ps if re.match(r"<p><strong>[^<]+</strong>", p)]
        if len(strong) < 3:
            return m.group(0)
        head = re.findall(r"<h[23][^>]*>.*?</h[23]>", inner, flags=re.S)
        intro = [p for p in ps if p not in strong]
        items = []
        for p in strong:
            t = re.match(r"<p><strong>([^<]+)</strong>", p).group(1).strip().rstrip(".:").strip()
            items.append((t, re.sub(r"^<p><strong>[^<]+</strong>\s*", "", p)[:-4].strip()))
        out, buf = [], []

        def flush():
            if len(buf) == 2:
                out.append('<div class="pgrid">' + "".join(card(*x) for x in buf) + "</div>")
            else:
                out.extend(row(*x) for x in buf)
            buf.clear()

        for t, body in items:
            if len(body) <= 430:
                buf.append((t, body))
                if len(buf) == 2:
                    flush()
            else:
                flush()
                out.append(row(t, body))
        flush()
        return f'<div class="prose-cards">{"".join(head)}{"".join(intro)}{"".join(out)}</div>'
    return re.sub(r'<div class="prose"( style="[^"]*")?>(.*?)</div>', lambda m: conv(m), page, flags=re.S)


STATS = [("67–72%", "обычный уровень выкупа от рыночной цены бутылки"), ("28–33%", "дисконт по таблице 1buyup: потолок выкупа против рынка"),
         ("до −30%", "к цене, если нет оригинальной коробки (данные Red Decanter)"), ("×2,5", "разброс «от» и «до» по Yamazaki 18: 80 000 против 32 000 ₽")]


def stats_strip():
    tiles = "".join(f'<div class="stat-tile"><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in STATS)
    return f'<section class="section stats-section" aria-label="Цифры рынка"><div class="container"><div class="stats-strip">{tiles}</div><p class="note">Ориентиры по открытым данным компаний и таблицам цен; не оферта и не гарантия выплаты.</p></div></section>\n'


def decorate_page(page, key):
    page = decorate_prose(page)
    if key in ("gde-prodat-viski.html", "gde-prodat-elitnyy-alkogol.html"):
        m = re.search(r'<section class="section[^"]*" id="guide">', page)
        if m:
            page = page[:m.start()] + stats_strip() + page[m.start():]
    return page

def add_bands(page, key):
    for sid, img, eyebrow, text, href, label in BANDS.get(key, []):
        marker = f'id="{sid}"'
        i = page.find(marker)
        if i < 0:
            continue
        j = page.rfind("<section", 0, i)
        cls = img.split(".")[0].replace("banner", "band-")
        band = (f'<section class="photo-band {cls}"><div class="container">'
                f'<span class="eyebrow">{e(eyebrow)}</span><p>{e(text)}</p></div></section>\n')
        page = page[:j] + band + page[j:]
    return page


def main():
    (ROOT / "index.html").write_text(decorate_page(add_bands(index_page(), "index.html"), "index.html"), encoding="utf-8")
    (ROOT / "prices.html").write_text(prices_page(), encoding="utf-8")
    (ROOT / "metodika.html").write_text(decorate_page(methodology_page(), "metodika.html"), encoding="utf-8")
    (ROOT / "o-reitinge.html").write_text(decorate_page(about_page(), "o-reitinge.html"), encoding="utf-8")
    for tp in TOPICS:
        (ROOT / tp["file"]).write_text(decorate_page(add_bands(topic_page(tp), tp["file"]), tp["file"]), encoding="utf-8")
    (ROOT / "c").mkdir(exist_ok=True)
    write_covers()
    for i, c in enumerate(CARDS):
        (ROOT / "c" / f"{c['slug']}.html").write_text(company_page(c, i), encoding="utf-8")
    print("ok:", len(CARDS), "компаний,", len(PRICES), "строк цен,", len(RUM), "ром/арманьяк,", len(SEG), "сегментов")


if __name__ == "__main__":
    main()
    for f in list(ROOT.glob("*.html")) + list((ROOT / "c").glob("*.html")):
        h = postprocess(f.read_text(encoding="utf-8"))
        if f.name != "index.html":
            h = add_crumbs(h, f.parent.name == "c")
        f.write_text(h, encoding="utf-8")
