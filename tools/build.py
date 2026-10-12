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
SITE_URL = "https://drink-reviews.ru"   # адрес сайта без слеша в конце (нужен для canonical, sitemap, robots, og)
OPERATOR = dict(                      # оператор сайта и персональных данных (подставляется в политики и на страницу «Для компаний»)
    name="Александр Грудинин",
    email="info@drink-reviews.ru",     # e-mail для обращений
)
# Как подключать шапку и подвал: "inline" — блок вставляется в каждую страницу при сборке (работает на любом хостинге);
# "ssi" — на страницах стоит директива <!--#include virtual="/includes/header.html" --> (нужна поддержка SSI на сервере и размещение в корне домена).
# Файлы includes/header.html и includes/footer.html создаются при любом режиме.
INCLUDE_MODE = os.environ.get("INCLUDE_MODE", "inline")
# Индексация: False — сайт закрыт (meta noindex, robots.txt Disallow: /, заголовок X-Robots-Tag через .htaccess). Для открытия поставьте True и пересоберите.
ALLOW_INDEXING = True

# Автор и эксперт сайта. Блок показывается только при show=True и только когда вы подтвердили реальные сведения:
# имя и фото используются с согласия человека, должность и квалификация подтверждаются документами.
EXPERT = dict(
    show=True,
    name="Александр Грудинин",
    role="Сомелье · Эксперт по винной культуре · Консультант по винным коллекциям",
    about='Александр Грудинин — специалист в области винной культуры, профессиональной дегустации и гастрономического консалтинга. Его профессиональная деятельность связана с изучением винодельческих традиций, подбором премиальных вин и развитием индивидуального подхода к формированию винных коллекций.\n\nЗа годы работы Александр приобрёл опыт взаимодействия с ресторанными проектами и частными ценителями вина. Он занимается составлением винных карт, подбором напитков для гастрономических мероприятий и консультированием клиентов, которые стремятся глубже разобраться в качестве, происхождении и особенностях различных вин.\n\nВ центре его профессиональных интересов находятся классические винодельческие регионы Франции, Италии и Испании, а также Германия и Австрия. При проведении дегустаций Александр уделяет внимание структуре вина, ароматическому профилю, балансу кислотности и танинов, влиянию терруара и особенностям конкретного урожая.\n\nОтдельное направление его работы — консультирование по созданию и развитию частных винных собраний. При подборе бутылок он учитывает предпочтения коллекционера, потенциальную продолжительность выдержки, условия хранения и сочетаемость вина с определёнными блюдами.\n\nАлександр также интересуется современными тенденциями мирового виноделия, знакомится с новыми производителями и изучает региональные особенности винных хозяйств. В рамках профессиональных встреч и дегустационных мероприятий он стремится сделать сложные характеристики вина понятными, уделяя внимание как техническим аспектам, так и впечатлениям от дегустации.\n\nВ своей работе Александр придерживается внимательного и аналитического подхода, сочетая уважение к классическим винодельческим традициям с интересом к новым стилям и технологиям. Для него каждое вино — это сочетание происхождения, мастерства производителя и уникальных особенностей места, в котором оно было создано.',
    credentials="Профессиональный опыт: 18 лет · Москва, Россия",
    photo="assets/expert.jpg",   # фото эксперта; без файла блок показывается с монограммой
    disclosure="Александр Грудинин — эксперт и оператор сайта.",
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

SITE = "drink-reviews.ru"
SITE_SUB = "Рейтинг скупок алкоголя"
_n, _ext = SITE.split(".", 1)
LOGO = "-<b>".join(_n.split("-", 1)) + "</b>." + _ext if "-" in _n else _n + "." + _ext
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
  "Ездить никуда не нужно: отправьте чёткие снимки в мессенджер или через форму и получите два-три предложения для сравнения. О встрече договаривайтесь, лишь когда сумма вас устроила и вы обсудили порядок расчёта. Живёте за пределами Москвы — сразу уточните, возможна ли отправка."
 ],
 [
  "Редкий экземпляр или лимитированная серия",
  "Для подобных бутылок выбирайте тех, у кого оценщик — сомелье и кто не прячет цены. Сообщите год, регион производства и сохранность. Тут решает компетентность оценщика, а не скорость: на сумму влияют даже небольшая убыль жидкости или состояние этикетки."
 ],
 [
  "Большая коллекция",
  "Отправьте перечень бутылок списком и заранее узнайте, как будут вывозить коллекцию, по какому договору и как рассчитаются. Реквизиты контрагента проверьте, а условия по объёму и срокам согласуйте до осмотра."
 ],
 [
  "Остатки ресторана, бара или магазина",
  "Смотрите в сторону оптовых программ: у части компаний опт стартует от 10 бутылок, и в комплекте идёт инвентаризация на месте. Условия для большой партии, как правило, обговариваются индивидуально."
 ],
 [
  "Нужны деньги срочно",
  "Берите тех, кто отвечает за считаные минуты и принимает допоздна. Обратиться можно сразу в несколько компаний, но соглашаться стоит лишь на цену, зафиксированную заранее: из-за спешки сумма не должна проседать."
 ],
 [
  "Бутылки в другом городе",
  "Из других городов бутылки пересылают транспортной компанией — узнайте, кто отвечает за упаковку и доставку. В Москве и области часть компаний приезжает в тот же день. Надёжнее выглядит схема, где передача документов и денег проходит открыто."
 ],
 [
  "Хочу прикинуть сумму",
  "Сначала воспользуйтесь калькулятором и таблицей цен, потом обращайтесь в компании. С таким ориентиром легче отличить реальную сумму от раздутого обещания."
 ],
 [
  "Старая или современная бутылка",
  "У новой бутылки ценятся упаковка и опрятный вид, у старой — год, уровень налива и сохранность. Известный производитель и популярная позиция привлекают покупателей, а редкие вещи дорожают быстрее массовых."
 ],
 [
  "Пока не решил(а), продавать ли",
  "Сомнения — обычное дело. Оценку по фото можно получить, а бутылку оставить у себя: решать вам, и рейтинг никого не торопит с продажей."
 ]
]


def choice_section():
    rows = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td></tr>" for a, b in CHOICES)
    return f"""<section class="section ranking-section" id="choice">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Под вашу задачу</span><h2 class="section-title">Что кому<br>подойдёт</h2></div>
<p class="section-copy">Задачи у людей разные, и подход к выбору тоже. Подарок, наследство, остатки бара — это разные истории: то, что спасает в одной, в другой не пригодится. Проверяемых сведений в нише мало, поэтому подробно опишите компании свою ситуацию и сопоставьте полученные ответы.</p>
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
    items = [f"Всего в рейтинге **{len(CARDS)} компаний**, но открытые цены есть лишь у **{len(priced)}**: {', '.join(priced)}."]
    if topic == "vodka":
        items = ["В рейтинге **20 компаний**, но водку прямо называет в списке принимаемого только **Vine&Co** (Санкт-Петербург).",
                 "Прайса на водку **нет ни у одной** компании: сумму называют по фотографиям и после осмотра.",
                 "Алкоголь СССР, куда входит и советская водка, заявляют **1buyup, TotalStok, SellMeWine и Vine&Co**.",
                 "Недорогие позиции берут, по их словам, **Cupaj Club и Alko Prikup**: проверить это можно только заявкой.",
                 "Обычную магазинную водку скупки, как правило, **не принимают**; интерес вызывают лимитированные серии, оформление и сохранная упаковка."]
        li = "".join("<li>" + re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e(x)) + "</li>" for x in items)
        return f"""<section class="section keyfacts" id="summary-short"><div class="container narrow"><h2 class="sub" style="margin-top:0">Коротко</h2><ul class="goals">{li}</ul></div></section>
"""
    if topic == "elite":
        items.append("Для дорогих и редких бутылок подходят **Red Decanter** (в прайсе до 5 000 000 ₽), 700ml (до 200 000 ₽, Petrus) и SKUPKA-ALKOGOL (сегменты до «свыше 100 000 ₽»).")
    items.append("По опубликованным таблицам типичный выкуп составляет **67–72% от рыночной цены**; посулы «до 90%» и «до 100%» — **рекламный приём**, а не обычная практика.")
    items.append(f"Первый ответ по фотографиям: самый быстрый — **{quick['meta']['speed'].lower()}** ({quick['name']}), самый долгий — **{slow['meta']['speed'].lower()}** ({slow['name']}).")
    items.append(f"Лучший результат по оценке редакции — **{scores(top)[1]:g} из 5** ({top['name']}); оценка собирается из трёх параметров, правила изложены в методике.")
    items.append("Некоторые сайты, **по всей видимости, ведёт один оператор**: 700ml, Alko Lombard и oldcognac; Red Decanter и SKUPKA-ALKOGOL; Cupaj Club и Alko Prikup.")
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
<meta name="theme-color" content="#1b130a">
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
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}assets/style.css?v={ASSET_V}">
{jsonld(site_ld, org, page_ld, *(ld or []))}
{YM_SCRIPT.replace("__ID__", YM_ID) if YM_ID else ""}</head>
<body>
{YM_NOSCRIPT.replace("__ID__", YM_ID) if YM_ID else ""}"""


# Меню шапки: (подпись, ссылка). Ссылка на якорь главной начинается с «#», остальные — файлы в корне.
NAV = [
    ("Скупка алкоголя", "#ranking"),
    ("Элитный алкоголь", "gde-prodat-elitnyy-alkogol.html"),
    ("Водка", "gde-prodat-vodku.html"),
    ("Цены выкупа", "prices.html"),
    ("Как продать", "#prepare"),
    ("Методика", "metodika.html"),
    ("Эксперт", "o-reitinge.html#author"),
    ("Контакты", "kontakty.html"),
]
NAV_TITLES = {
    "#ranking": "Скупки алкоголя в Москве: сопоставление компаний, принимающих коньяк, виски, вино и шампанское",
    "gde-prodat-elitnyy-alkogol.html": "Куда нести элитный и коллекционный алкоголь: редкие бутылки, винтаж, шампанское",
    "gde-prodat-vodku.html": "Куда сдать водку: коллекционные, лимитированные и советские бутылки, упаковка и сохранность",
    "prices.html": "Цены выкупа бутылок: ориентиры, которые публикуют скупки",
    "#prepare": "Как продать бутылку: снимки этикетки, пробки и упаковки, сохранность и хранение",
    "metodika.html": "Методика: критерии рейтинга, источники и подсчёт оценки",
    "o-reitinge.html#author": "Эксперт сайта: опыт, подход к оценке и независимость рейтинга",
    "kontakty.html": "Контакты редакции: e-mail, вопросы и обращения компаний",
}


def contact_short():
    parts = []
    if OPERATOR.get("email"):
        parts.append(f'<a href="mailto:{e(OPERATOR["email"])}">{e(OPERATOR["email"])}</a>')
    return " · ".join(parts)


def header_inline(depth=0, base=None):
    p = base if base else "../" * depth
    home = base if base else (p or "./")
    links = "\n".join(f'<a href="{home + h if h.startswith("#") else p + h}" title="{e(NAV_TITLES[h])}">{e(l)}</a>' for l, h in NAV)
    return f"""<div class="topbar"><div class="container topbar-inner">
<p>Где продать коньяк, виски, вино и шампанское в Москве и области: сопоставляем условия, сроки оценки и цены выкупа.</p>
<p class="topbar-contact">Связь с редакцией: {contact_short()}</p>
</div></div>
<header class="header" id="header">
<div class="container header-inner">
<a href="{home}" class="nav-logo" aria-label="{SITE} — главная страница" title="Главная: рейтинг скупок алкоголя"><img class="logo-mark" src="{p}assets/logo-mark.png" alt="" width="40" height="44"><span class="logo-text"><span class="logo-word">{LOGO}</span><span class="nav-logo-sub">Рейтинг скупок алкоголя</span></span></a>
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
        photo = f'<img class="ex-photo" src="{p}{EXPERT["photo"]}" alt="{e(EXPERT["name"])}" width="200" height="250" loading="lazy">'
    about = "".join(f"<p>{e(t)}</p>" for t in EXPERT["about"].split("\n\n")) if EXPERT["about"] else ""
    cred = f"<p class=\"ex-cred\">{e(EXPERT['credentials'])}</p>" if EXPERT["credentials"] else ""
    disc = f"<p class=\"ex-disc\">{e(EXPERT['disclosure'])}</p>" if EXPERT["disclosure"] else ""
    return f"""<section class="expert" id="author"><div class="ex-card">{photo}<div><span class="eyebrow">Эксперт сайта</span><h2 class="ex-name">{e(EXPERT['name'])}</h2><p class="ex-role">{e(EXPERT['role'])}</p>{about}{cred}{disc}</div></div></section>
"""


def footer_contacts():
    """Блок «Контакты» в подвале: e-mail (и телефон, Telegram, если заданы) крупно и со ссылкой."""
    items = []
    if OPERATOR.get("email"):
        items.append(f'<a class="footer-mail" href="mailto:{e(OPERATOR["email"])}">{e(OPERATOR["email"])}</a>')
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


ASIDE_TEXT = {
    "home": ("Работает с ресторанными проектами и частными ценителями: составляет винные карты, подбирает напитки для гастрономических мероприятий и помогает разобраться в качестве и происхождении вин.",
             ["Франция · Италия · Испания · Германия · Австрия", "Дегустации", "Винные карты"]),
    "elite": ("В центре его интересов — классические регионы Франции, Италии и Испании, а также Германии и Австрии. Оценивая вино, он смотрит на структуру, аромат, баланс кислотности и танинов, влияние терруара и особенности урожая.",
              ["Терруар и урожай", "Кислотность и танины", "Классические регионы"]),
    "vodka": ("Отдельное направление его работы — частные винные собрания: подбор бутылок с учётом вкусов коллекционера, потенциала выдержки, условий хранения и сочетаемости с блюдами.",
              ["Подбор бутылок", "Хранение и выдержка", "Частные коллекции"]),
}


def expert_aside(kind, depth=0):
    """Отдельная карточка эксперта внутри страницы. Текст — пересказ присланной биографии, без выдуманных цитат."""
    if not EXPERT["show"]:
        return ""
    p = "../" * depth
    text, tags = ASIDE_TEXT[kind]
    parts = EXPERT["name"].split()
    initials = (parts[0][0] + parts[-1][0]).upper() if parts else ""
    if EXPERT.get("photo") and (ROOT / EXPERT["photo"]).exists():
        pic = f'<img class="ea-photo" src="{p}{EXPERT["photo"]}" alt="{e(EXPERT["name"])}" width="220" height="260" loading="lazy">'
    else:
        pic = f'<div class="ea-photo ea-mono" aria-hidden="true">{e(initials)}</div>'
    chips = "".join(f"<li>{e(t)}</li>" for t in tags)
    return f"""<section class="section expert-aside-wrap" aria-label="Эксперт сайта"><div class="container">
<article class="expert-aside">
<div class="ea-pic">{pic}</div>
<div class="ea-body">
<span class="eyebrow">Эксперт сайта</span>
<h2 class="ea-name">{e(EXPERT["name"])}</h2>
<p class="ea-role">{e(EXPERT["role"])}</p>
<p class="ea-text">{e(text)}</p>
<ul class="ea-tags">{chips}</ul>
<p class="ea-foot"><span>{e(EXPERT["credentials"])}</span><a class="text-link" href="{p}o-reitinge.html#author">Об эксперте →</a></p>
</div>
</article>
</div></section>
"""


QUOTES = {
    "stevenson": ("…и вино — это бутилированная поэзия.", "and the wine is bottled poetry", "Роберт Льюис Стивенсон", "«Силверадские сквоттеры», 1883. Перевод редакции."),
    "pushkin": ("Вошёл: и пробка в потолок,<br>Вина кометы брызнул ток.", "", "Александр Пушкин", "«Евгений Онегин», глава первая"),
}


def quote_block(key):
    """Цитата отдельным блоком. Только источники, которые можно проверить."""
    text, orig, who, src = QUOTES[key]
    o = f'<p class="qb-orig" lang="en">{e(orig)}</p>' if orig else ""
    return f"""<section class="quote-block" aria-label="Цитата"><div class="container">
<figure><blockquote><p>{text}</p>{o}</blockquote>
<figcaption><b>{e(who)}</b><span>{e(src)}</span></figcaption></figure>
</div></section>
"""


def footer_inline(depth=0, base=None):
    p = base if base else "../" * depth
    home = base if base else (p or "./")
    op = f"Оператор сайта: {ph('name', 'ФИО оператора')}"
    return expert_mini(p) + f"""<footer class="footer">
<div class="container">
<div class="footer-main">
<div>
<a href="{home}" class="nav-logo footer-brand" aria-label="{SITE} — главная"><img class="logo-mark" src="{p}assets/logo-mark.png" alt="" width="40" height="44"><span class="logo-text"><span class="logo-word">{LOGO}</span><span class="nav-logo-sub">Рейтинг скупок алкоголя</span></span></a>
<p class="footer-logo-copy">Независимый рейтинг скупок алкоголя: кто в Москве, области и других городах России берёт коньяк, виски, вино, шампанское, ром, арманьяк и алкоголь СССР, как скоро оценивает по фото и на каких условиях приезжает. Сами мы ничего не покупаем: снимки и заявку вы отправляете выбранной компании — через форму на её сайте или в мессенджер.</p>
</div>
<div><h3 class="footer-title">Разделы</h3><div class="footer-links">
<a href="{home}">Главная</a><a href="{home}#ranking">Рейтинг скупок</a><a href="{p}{TOPICS[0]["file"]}">Элитный алкоголь</a><a href="{p}{TOPICS[1]["file"]}">Водка</a><a href="{p}prices.html">Цены выкупа</a><a href="{home}#calc">Калькулятор</a><a href="{home}#prepare">Как продать</a><a href="{home}#faq">Вопросы и ответы</a></div></div>
<div><h3 class="footer-title">Информация</h3><div class="footer-links">
<a href="{p}metodika.html">Методика</a><a href="{p}o-reitinge.html">О рейтинге</a><a href="{p}dlya-kompanii.html">Для компаний</a><a href="{p}kontakty.html">Контакты</a><a href="{p}karta-sayta.html">Карта сайта</a></div></div>
<div><h3 class="footer-title">Документы</h3><div class="footer-links">
<a href="{p}redakcionnaya-politika.html">Редакционная политика</a><a href="{p}otkaz-ot-otvetstvennosti.html">Отказ от ответственности</a><a href="{p}pravila-polzovaniya.html">Правила пользования</a><a href="{p}politika-konfidencialnosti.html">Политика конфиденциальности</a><a href="{p}politika-cookie.html">Политика cookie</a></div>{footer_contacts()}</div>
</div>
<nav class="footer-tags" aria-label="Разделы сайта"><span class="footer-tags-title">Разделы сайта</span>
<a href="{p}{TOPICS[0]["file"]}">Элитный алкоголь</a><a href="{p}{TOPICS[1]["file"]}">Водка</a><a href="{p}prices.html">Цены выкупа</a><a href="{home}#calc">Калькулятор выкупа</a><a href="{home}#prepare">Как подготовить бутылку</a><a href="{home}#faq">Вопросы и ответы</a>
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
  "В первую очередь интересны выдержанный виски, коньяк от XO и старше, коллекционное вино, шампанское, ром и арманьяк, а ещё советский алкоголь, имеющий ценность для собирателей. Оригинальная коробка, тубус и декантер порой оцениваются отдельно. Массовую водку и ширпотреб, открытые бутылки и контрафакт не берут; Cupaj Club и Alko Prikup говорят, что готовы рассмотреть и недорогие позиции. У каждой компании свой перечень, так что выясните его до отправки снимков. Производители и редкие бутылки подробно описаны на странице об элитном алкоголе."
 ],
 [
  "Из чего складывается стоимость бутылки?",
  "Отправной точкой служат аукционные котировки и прайсы импортёров, а не магазинная полка, поэтому выкуп неизбежно дешевле покупки: опубликованные таблицы дают примерно 67–72% от рыночной цены. Итог зависит от производителя и года, выдержки, вида этикетки, целостности пробки и капсулы, уровня налива, наличия коробки и бумаг, а также от спроса на конкретную бутылку. Поэтому настоящую сумму называют только по снимкам и после осмотра. Если цифру выдают мгновенно и без фотографий — это повод насторожиться; сопоставьте предложения как минимум двух компаний."
 ],
 [
  "Почему при встрече цену могут изменить?",
  "Первичная оценка строится на фотографиях и не видит того, что заметно вживую: затёртую этикетку, след подтёка у пробки, чуть сниженный уровень. Компании, обещающие не менять цену, почти всегда оговариваются: «если не обнаружится ничего нового». Попросите заранее объяснить, что будут проверять и из-за чего сумма может измениться, и сохраните переписку: договорённости в Telegram или на почте можно показать, а устные обещания по телефону — нет."
 ],
 [
  "Сколько времени занимает оценка?",
  "Первый ответ по фото компании обещают за срок от 2–3 до 15 минут; у Room Alco он около получаса, у 700ml — до суток. Это время предварительной оценки, а окончательную цифру эксперт называет после осмотра, и она может не совпасть с первой. Когда дело срочное, сразу спросите, во сколько приедет специалист и когда вы получите деньги. Настоящую скорость покажет только заявка: «5 минут» — это то, что компания сама о себе пишет."
 ],
 [
  "Можно ли продать бутылку без коробки и акцизной марки?",
  "Нередко да: 1buyup принимает бутылки без коробки и акцизной марки, а также алкоголь СССР. Правда, платят обычно меньше: Red Decanter предупреждает о скидке до 30% при отсутствии оригинальной упаковки. Для коллекционной бутылки акцизная марка почти не играет роли, а вот опрятная этикетка, целая пробка и подарочная упаковка добавляют в цене. Держите бутылки в тёмном прохладном месте (обычный холодильник не подходит), не открывайте и не оттирайте этикетку."
 ],
 [
  "Как проходит сделка от заявки до расчёта?",
  "Порядок практически везде одинаков: вы присылаете снимки и несколько строк о бутылке (производитель, год, объём, город), получаете предложение, обсуждаете детали и договариваетесь о встрече или приезде оценщика. Перед осмотром выясните, будет ли договор, и выбирайте такой способ расчёта, который оставляет документальный след: перевод или наличные под расписку. Продавать алкоголь вправе только совершеннолетние. Жителям Самары, Перми, Ростова, Краснодара, Сочи или Уфы обычно предлагают пересылку транспортной компанией — заранее узнайте про упаковку, страховку и ответственность за бой. Вносить предоплату не требуется. Нажимая «Оставить заявку» на сайте компании, вы разрешаете именно ей обрабатывать ваши персональные данные — ознакомьтесь с её политикой."
 ],
 [
  "Как продать коллекцию целиком или остатки ресторана?",
  "Подготовьте перечень с фотографиями (производитель, год, объём, состояние) и разошлите его нескольким компаниям: к партиям у каждой свой подход. Опт берёт, например, Diamant Alko — от 10 бутылок, с выездом и экспресс-инвентаризацией. Уточните, предоставят ли договор до осмотра, есть ли лимиты по объёму, кто занимается вывозом и упаковкой. Контрагента проверяйте по реквизитам, а не только по внешнему виду сайта. Техника и другие предметы, не относящиеся к алкоголю, в такие предложения обычно не входят."
 ]
]


PROMISES = [
    ("«Оценим по фото за 5 минут»", "Речь идёт о предварительной оценке по фотографиям; окончательную сумму озвучивают после осмотра. Узнайте, что может её изменить, и зафиксируйте цену в переписке."),
    ("«Выкупаем дорого и выгодно»", "Это рекламный штамп, а не цифра. Настоящий выкуп ниже рыночной цены (примерно 67–72%), поэтому сравнивайте ответы нескольких компаний."),
    ("«Покупаем любой алкоголь»", "Как правило, имеются в виду коллекционные и премиальные бутылки. Массовые марки и водку принимают нечасто; исключения — лимитированные серии и советский алкоголь."),
    ("«Принимаем без коробки и акциза»", "Часто так и есть, однако без оригинальной упаковки цена порой снижается вплоть до 30% (по данным одной из компаний). Коробки и тубусы лучше сберечь."),
    ("«Приедем бесплатно»", "Узнайте, когда приедет специалист, оформят ли договор и как будет проходить расчёт. Для партии выезд — норма, а ради одной бутылки он нужен не всегда."),
    ("«Предлагаем максимальную цену»", "Без сравнения «максимальной» цены не бывает. Спросите, на что опирается сумма — на аукционные котировки или на цены перекупщиков, — и сверьте с другими предложениями."),
    ("«Пришлите фото — назовём стоимость»", "Это обычный порядок. Присылайте только фото бутылки и способ связи; документы для предварительной оценки не нужны."),
    ("«Оставьте заявку — перезвоним через 5 минут»", "Чаще это время до первого контакта, а не готовая оценка. Проверить скорость можно самому, оставив заявки в двух-трёх компаниях."),
    ("«Деньги сразу»", "Спросите, как платят (наличными или переводом) и в какой момент: до или после осмотра. Деньги за бутылку не передают, пока условия не согласованы."),
    ("«Работаем по Москве, области и всей России»", "Выясните, в какие города выезд реально существует. При пересылке транспортной компанией бутылка может разбиться — узнайте, кто за это отвечает."),
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
<p class="calculator-copy">Интересно, какую сумму можно выручить за коньяк, виски, вино, шампанское, ром или арманьяк? Укажите рыночную цену бутылки (аукционную или импортёрскую), и калькулятор выдаст примерный размер выкупа. По опубликованным таблицам скупки платят порядка 67–72% от неё. Это быстрый ориентир, а не оценка вашей бутылки: точную цифру называет эксперт по фотографиям и после осмотра, а на неё влияют производитель, выдержка, год, состояние и упаковка.</p>
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
<span class="result-disclaimer">Диапазон — всего лишь ориентир, а не цена сделки. На итог влияют подлинность, этикетка, капсула, пробка, уровень налива, коробка и спрос.</span>
</aside>
</div>
<h3 class="sub">Как считается дисконт: опубликованные цены выкупа, виски</h3>
<div class="table-wrap"><table class="data">
<thead><tr><th>Позиция</th><th>Рынок</th><th>Готовы купить до</th><th>Дисконт</th></tr></thead>
<tbody>{disc_rows}</tbody></table></div>
<p class="note">Источник — открытые таблицы цен скупок (раздел «Виски»); цифры приблизительные. Скупка платит не больше 67–72% от рыночной цены. Цены других компаний — на странице <a href="{p}prices.html" class="text-link">«Цены выкупа»</a>.</p>
</div>
</section>

<section class="section" id="choose">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Перед сделкой</span><h2 class="section-title">Пять вопросов,<br>которые стоит задать</h2></div>
<p class="section-copy">Везде порядок одинаков: заявка, фото, предварительная цена, встреча, расчёт. Различия кроются в деталях, и разобраться в них лучше до того, как бутылки отправятся к оценщику.</p>
</div>
<div class="steps-grid">
<article class="step"><div class="step-number">01</div><h3 class="step-title">Цену не поменяют?</h3><p>Сильнее всего клиентов раздражает ситуация, когда на встрече цена внезапно падает. 1buyup, TotalStok, Kupimalko и VykupAlko прямо обещают не менять сумму, названную по фото. Попросите подтвердить её до приезда специалиста — в Telegram, по телефону или по почте — и сохраните ответ.</p></article>
<article class="step"><div class="step-number">02</div><h3 class="step-title">«От» или «до»?</h3><p>У 700ml указано «от» — это нижняя граница, у 1buyup «до» — то есть потолок. По Yamazaki 18 разница достигает 2,5 раза. Сравнивать такие цифры напрямую нельзя: спросите, сколько компания заплатит именно за вашу бутылку и от чего зависит итог.</p></article>
<article class="step"><div class="step-number">03</div><h3 class="step-title">Цены опубликованы?</h3><p>Выставляют цены на сайте четыре компании: 700ml, 1buyup, Red Decanter и SKUPKA-ALKOGOL. Остальные озвучивают сумму лишь после фотографий и заявки, отправленной через форму на сайте или в мессенджер.</p></article>
<article class="step"><div class="step-number">04</div><h3 class="step-title">Кто за сайтом?</h3><p>Независимых операторов меньше, чем сайтов: часть ресурсов, вероятно, принадлежит одной компании (см. <a class="text-link" href="{p}metodika.html">методику</a>). Обратившись в «разные» скупки одной группы, нередко слышишь одно и то же.</p></article>
<article class="step"><div class="step-number">05</div><h3 class="step-title">Чему верить?</h3><p>«До 90%» и «до 100%» от рыночной цены — маркетинг: по таблицам настоящий дисконт составляет около 28–33%. Цифры «10+ лет», «5000 сделок» и «97% выкупа» — слова самих компаний, и никто их не проверял. Распространённые формулировки разобраны ниже.</p></article>
</div>
<div class="prose checklist">
<p><strong>Как продать выгодно и без спешки.</strong> Не берите первое попавшееся предложение: отправьте одни и те же снимки в две-три компании и сравнивайте не только цену, но и условия — срок ответа, время приезда, способ расчёта, наличие договора. Принимайте во внимание сильные стороны каждой: выезд на адрес по Москве и области, готовность забрать коллекцию целиком, работа с другими городами. «Ответ за пять минут» — обещание самой компании, а реальную скорость вы увидите после заявки. Оценка по фото — лишь первый шаг, осмотр она не отменяет. Не соглашайтесь, пока не объяснили, из чего складывается цена, и не отправляйте бутылки, пока сумма не подтверждена.</p>
</div>
</div>
</section>

<section class="section ranking-section" id="promises">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Как читать офферы</span><h2 class="section-title">Что на самом деле<br>обещают скупки</h2></div>
<p class="section-copy">Сайты скупок пестрят одними и теми же формулировками. Ниже — что за ними обычно скрывается и что нужно выяснить, прежде чем соглашаться.</p>
</div>
<div class="table-wrap"><table class="data">
<thead><tr><th>Что пишут скупки</th><th>Что это значит и что проверить</th></tr></thead>
<tbody>{prom_rows}</tbody></table></div>
<p class="note">Эти формулировки характерны для скупок. Наш сайт ничего не покупает и бутылки не оценивает: условия сделки вы согласуете напрямую с выбранной компанией.</p>
</div>
</section>

<section class="section ranking-section" id="quick">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Порядок действий</span><h2 class="section-title">Как продать<br>без лишней спешки</h2></div>
<p class="section-copy">Четыре шага: от съёмки до расчёта. Сделка всегда заключается между вами и выбранной компанией; сайт сам ничего не покупает.</p>
</div>
<div class="trust-grid">
<article class="trust-item"><div class="trust-symbol">1</div><h3 class="trust-title">Фото</h3><p>Сфотографируйте этикетки, пробку, упаковку и уровень налива при дневном свете.</p></article>
<article class="trust-item"><div class="trust-symbol">2</div><h3 class="trust-title">Заявка</h3><p>Подберите компанию в рейтинге и отправьте снимки через форму на её сайте или в Telegram.</p></article>
<article class="trust-item"><div class="trust-symbol">3</div><h3 class="trust-title">Оценка</h3><p>Дождитесь предварительного предложения. Стоимость зависит от состояния, выдержки, сохранности и редкости.</p></article>
<article class="trust-item"><div class="trust-symbol">4</div><h3 class="trust-title">Встреча</h3><p>Если условия подходят, согласуйте время и место. Многие компании приезжают сами, а деньги отдают после осмотра.</p></article>
</div>
<p class="note">Важно: сроки и условия уточняйте напрямую — телефон, Telegram и адрес каждой компании есть в её карточке.</p>
</div>
</section>

<section class="section" id="prepare">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Фото для оценки</span><h2 class="section-title">Как подготовить<br>бутылку к оценке</h2></div>
<p class="section-copy">Чем резче фотографии, тем скорее придёт ответ и тем ближе предварительная цена окажется к итоговой. Сделайте несколько кадров при дневном свете и отправьте их выбранной компании через форму на сайте или в мессенджер — Telegram или WhatsApp.</p>
</div>
<div class="trust-grid">
<article class="trust-item"><div class="trust-symbol">1</div><h3 class="trust-title">Этикетки</h3><p>Сфотографируйте лицевую и обратную этикетки: по ним видно производителя, год и состояние бумаги.</p></article>
<article class="trust-item"><div class="trust-symbol">2</div><h3 class="trust-title">Капсула и пробка</h3><p>Покажите горлышко, капсулу, пробку и акцизную марку: повреждения ощутимо снижают цену.</p></article>
<article class="trust-item"><div class="trust-symbol">3</div><h3 class="trust-title">Уровень и выдержка</h3><p>Снимите бутылку на просвет: у старых и винтажных позиций уровень налива критичен, а выдержка и год влияют на ценность.</p></article>
<article class="trust-item"><div class="trust-symbol">4</div><h3 class="trust-title">Упаковка</h3><p>Коробка, тубус, футляр, декантер и документы повышают цену: без коробки скидка достигает 30% (данные одной из компаний).</p></article>
</div>
<div class="prose checklist">
<p><strong>Онлайн-оценка.</strong> Многие компании делают предварительную оценку по фото бесплатно; телефон, Telegram и другие контакты указаны в карточках компаний.</p>
<p><strong>Что написать в сообщении:</strong> производителя, марку или релиз, год, объём, число бутылок, город и удобный способ связи. Когда бутылок много, сделайте общий кадр и приложите список.</p>
<p><strong>От чего зависит оценка:</strong> от состояния бутылки, сохранности этикетки и пробки, уровня налива, редкости релиза, наличия коробки и документов. Хранить бутылки лучше в тёмном прохладном месте, не открывая. Водку и массовые марки скупки обычно не берут, зато лимитированные серии, алкоголь СССР, арманьяк, ром и прочие редкие напитки принимают к рассмотрению.</p>
<p><strong>Коллекционерам и наследникам.</strong> Продать одну бутылку из собрания легко, а для большой коллекции заранее подготовьте список с фотографиями: оценка займёт больше времени, зато вы узнаете цену за всю партию. Винтажные и редкие экземпляры разумно показывать отдельно. Продавать алкоголь могут только совершеннолетние.</p>
<p><strong>Чего делать не стоит:</strong> открывать бутылку, оттирать и переклеивать этикетки, срывать акцизные марки. Сохраните коробки, тубусы, сертификаты и чеки — они подтверждают подлинность и происхождение.</p>
<p><strong>Как оценщик определяет состояние.</strong> Оценщик изучает внешний вид и содержимое: как сохранилась этикетка, нет ли подтёков у пробки, каков уровень налива, нет ли признаков плохой укупорки. Осмотрите бутылки заранее и сообщите всё, что знаете об их происхождении: производителя или хозяйство, год, комплектацию. Цена определяется редкостью, популярностью производителя и условиями хранения, а ориентиром служат аукционы, а не магазинная розница. Если порядок сделки непонятен, попросите специалиста компании объяснить его до осмотра. Бесплатная оценка не обязывает к продаже: сделка состоится лишь после согласования условий.</p>
</div>
</div>
</section>

<section class="section ranking-section" id="method-link">
<div class="container">
<div class="section-top" style="margin-bottom:0">
<div><span class="eyebrow">Методика</span><h2 class="section-title">Как составлен<br>рейтинг</h2></div>
<div><p class="section-copy" style="margin-bottom:20px">Критерии, источники сведений, правила подсчёта оценки и ситуации, когда рейтинг может ошибаться, изложены на отдельной странице.</p><a class="btn btn-primary" href="{p}metodika.html">Читать методику <span class="arrow">→</span></a></div>
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
<p class="final-copy">Напишите нам: поможем разобраться, как снять бутылку, ответим на вопрос о рейтинге или проверим данные о компании. Консультация бесплатная. Оценку и цену озвучивает выбранная вами компания — обычно на это уходит от нескольких минут до суток.</p>
<p class="final-note">Предварительная оценка и итоговая цена сделки могут различаться.</p>
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
    free = ("<p>Попасть в рейтинг можно бесплатно, а вознаграждений за место, оценку или текст обзора мы от компаний не получаем.</p>"
            if PLACEMENT_IS_FREE else
            "<p>Об отношениях редакции с компаниями рейтинга, в том числе финансовых, — в <a class=\"text-link\" href=\"redakcionnaya-politika.html\">редакционной политике</a>.</p>")
    return f"""<section class="section" id="independence">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Независимость и размещение компаний</h2>
<p>Сайт не предоставляет услуг, не торгует алкоголем и не принимает его у посетителей. Рейтинг строится на открытых данных, а компании для сравнения подбирает редакция.</p>
{free}
<p>Рейтинг не подтверждает наличие разрешений и законность работы компании: мы этого не проверяем. Это отправная точка для поиска, а не замена проверки условий перед сделкой. Если вы представляете компанию и заметили неточность, напишите через <a class="text-link" href="dlya-kompanii.html">страницу для организаций</a>.</p>
</div>
</div>
</section>
"""


def methodology_page():
    clusters = "".join(
        f"<tr><td>{e(n)}</td><td>{', '.join(e(d) for d in ds)}</td></tr>" for n, ds in CLUSTERS)
    return head(f"Методика рейтинга скупок алкоголя: данные, критерии, оценка — {SITE}",
                "Как мы составляем рейтинг скупок алкоголя в Москве: откуда берём сведения, по каким критериям оцениваем, что влияет на цену бутылки, где рейтинг может ошибаться и какие сайты, возможно, ведёт один оператор.",
                path="metodika.html", ld=[breadcrumbs(("Главная", ""), ("Методика", "metodika.html"))]) + header() + f"""
<main id="top">
<section class="topic-hero">
<div class="container">
<span class="eyebrow">Методика</span>
<h1 class="page-title">Как мы составляем рейтинг</h1>
<p class="lead">Откуда берутся данные, как выставляется оценка, от чего зависит цена выкупа и где проходят границы рейтинга.</p>
</div>
</section>
<section class="section" id="method">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Оценка бутылки</span><h2 class="section-title">Как оценивают<br>алкоголь</h2></div>
<p class="section-copy">Оценщик скупки сначала называет цену по фотографиям, а окончательную сумму подтверждает уже после осмотра бутылки.</p>
</div>
<div class="prose">
<p><strong>Что принимают.</strong> Скупки интересуются элитным и коллекционным алкоголем: коньяк (Hennessy, Rémy Martin, Louis XIII, Martell, Courvoisier), виски (Macallan, Yamazaki, Balvenie, Highland Park), вино (французские Petrus, Château Margaux, Château Lafite Rothschild, Château Mouton Rothschild; итальянские Masseto и Sassicaia), шампанское (Dom Pérignon, Cristal, Krug, Salon), ром, арманьяк, бренди и советские бутылки с коллекционной ценностью. Берут как отдельные бутылки, так и частные собрания целиком. Водку, массовые марки, открытые бутылки и подделки, как правило, отвергают; исключение — Cupaj Club и Alko Prikup.</p>
</div>
<div class="factors">
<article><h3>Подлинность и бренд</h3><p>Цена начинается с производителя, марки и линейки, поэтому эксперт просит показать этикетку и все важные детали. Подделки не принимаются.</p></article>
<article><h3>Год и выдержка</h3><p>Винтаж и год выпуска, возраст виски или коньяка, ограниченный тираж и спрос на редкий релиз.</p></article>
<article><h3>Этикетка, капсула, пробка</h3><p>Сохранность бумаги, целая капсула и пробка, акцизная марка, подарочная упаковка.</p></article>
<article><h3>Уровень жидкости</h3><p>Чем ниже уровень налива, тем дешевле бутылка. Открытые экземпляры обычно не принимают.</p></article>
<article><h3>Упаковка и комплект</h3><p>Родная коробка, тубус, футляр, декантер. Порой их покупают отдельно.</p></article>
<article><h3>Объём, регион, партия</h3><p>Формат бутылки, город (в Москве предлагают больше) и количество: коллекцию целиком оценивают не так, как одну бутылку.</p></article>
</div>
<div class="prose" id="disclosure">
<p><strong>Откуда цены.</strong> За основу берутся мировые аукционные котировки и цены импортёров, а не розничные магазинные, поэтому выкуп дешевле такой же бутылки с полки. Суммы на сайтах скупок — заявленные ориентиры, а не оферта.</p>
<p><strong>Как собран рейтинг.</strong> Мы просмотрели главные страницы сайтов и, когда получалось, страницы категорий. Если сайт не открывался для автоматического чтения, брали фрагменты поисковой выдачи (в карточке есть пометка). Сведения собраны 30 сентября 2026 г. «Не публикует» значит, что на проверенных страницах цен нет. Место в списке не измеряет качество услуг: ориентируйтесь на обзоры и таблицу. Независимые отзывы с Яндекс Карт и 2ГИС мы не собирали, поэтому числовые оценки опираются исключительно на открытые данные.</p>
<p><strong>Независимость.</strong> В основе рейтинга лежат открытые данные, а компании для сравнения выбирает редакция сайта.</p>
<p><strong>Что не проверено.</strong> Skupka-Star, Vine-Co (vine-co.ru), VinomerPro, Skupix, СпецВыкуп, Collectors Community, «VIP Выкуп», Vikup-Vina, e-skupka.ru, Alko-vikup, «Скупка PRO»; отзывы на Яндекс Картах и в 2ГИС; цены на подстраницах категорий.</p>
<h3 class="sub">Возможно, один оператор</h3>
<p>Совпадающие шаблоны, тексты и контакты выдают группы сайтов, возможно принадлежащих одному оператору. Это лишь признаки, а не доказательство.</p>
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
                "О проекте: независимый рейтинг скупок элитного и коллекционного алкоголя в Москве. Кто эксперт, откуда берутся данные и почему сайт сам ничего не покупает.",
                path="o-reitinge.html", ld=[{"@context": "https://schema.org", "@type": "AboutPage", "name": f"О рейтинге — {SITE}", "url": f"{SITE_URL}/o-reitinge.html", "inLanguage": "ru"}, breadcrumbs(("Главная", ""), ("О рейтинге", "o-reitinge.html")), expert_ld()]) + header() + f"""
<main id="top">
<section class="topic-hero">
<div class="container">
<span class="eyebrow">О проекте</span>
<h1 class="page-title">О рейтинге и об эксперте</h1>
<p class="lead">Независимое сопоставление компаний, выкупающих элитный и коллекционный алкоголь в Москве.</p>
</div>
</section>
{expert_block()}
<section class="mission" id="mission">
<div class="container">
<span class="eyebrow">Миссия</span>
<p class="mission-statement">Продавать бутылки без иллюзий: честно показывать их цену и называть тех, кому можно доверять.</p>
<p class="mission-copy">Коньяк, виски, вино, шампанское, водка и бутылки советской эпохи — такие же коллекционные предметы, как антиквариат. Их стоимость задают редкость, сохранность и откровенный разговор с оценщиком. Мы изучаем открытые данные, сопоставляем условия компаний и разбираем, что прячется за красивыми обещаниями, — чтобы продавец решал спокойно и заранее.</p>
</div>
</section>
<section class="section goals-section" id="goals">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Цели</span><h2 class="section-title">Чего мы добиваемся</h2></div>
<p class="section-copy">Шесть правил, которым подчиняются все обзоры и оценки на сайте.</p>
</div>
<div class="goal-grid">
<article class="goal"><h3>Прозрачная цена</h3><p>Называем реальные суммы и объясняем, в чём разница между «от» и «до», а также между рыночной ценой и ценой выкупа.</p></article>
<article class="goal"><h3>Факты отдельно от рекламы</h3><p>Громкие заявления компаний («5000 сделок», «до 90% рынка») мы так и подписываем — как заявления, а не как проверенные факты.</p></article>
<article class="goal"><h3>Защита продавца</h3><p>Объясняем, как подготовить бутылку, о чём спросить до сделки и почему не нужно платить вперёд.</p></article>
<article class="goal"><h3>Честность о минусах</h3><p>О недостатках компаний рассказываем столь же подробно, как о достоинствах, и отмечаем сайты, которые, возможно, ведёт один оператор.</p></article>
<article class="goal"><h3>Независимость</h3><p>Места в рейтинге не продаются, в список можно попасть бесплатно, а компании для сравнения редакция выбирает по открытым данным.</p></article>
<article class="goal"><h3>Культура коллекционирования</h3><p>Разбираем, из чего складывается ценность бутылки: производитель, выдержка, хранение, упаковка и документы.</p></article>
</div>
</div>
</section>
<section class="section">
<div class="container narrow">
<div class="prose">
<h2 class="sub">Для кого рейтинг</h2>
<p>Для коллекционеров, желающих знать настоящую цену своих бутылок. Для тех, кому по наследству достался чужой погреб или собрание и непонятно, с чего начинать. Для владельцев ресторанов, баров и магазинов, у которых остались излишки. И для каждого, кто не хочет отдать редкую бутылку за копейки.</p>
<h2 class="sub">О сайте</h2>
<p><strong>Что здесь есть.</strong> Мы сопоставляем компании, скупающие коньяк, виски, вино, шампанское и другой коллекционный алкоголь: смотрим на скорость оценки по фото, открытость цен, условия сделки, сильные и слабые стороны. Наша цель — чтобы продавец заранее знал, к кому обратиться и чего ожидать.</p>
<p><strong>Мы не участвуем в сделках.</strong> Сайт не покупает алкоголь, не принимает бутылки и не берёт комиссию. Все вопросы вы решаете напрямую с выбранной компанией.</p>
<p><strong>Откуда данные.</strong> Публичные сайты компаний, а если сайт закрыт для автоматического чтения — фрагменты поисковой выдачи. Такие цифры, как «5000 сделок» и «97% выкупа», компании приводят сами, мы их не проверяли. Подробности — в <a class="text-link" href="metodika.html">методике</a>.</p>
<p><strong>Ограничения.</strong> Информация носит справочный характер и может устаревать. Цены и сроки — заявления компаний, а не оферта; актуальные данные смотрите на их сайтах.</p>
<h2 class="sub">Как пользоваться рейтингом</h2>
<ol class="steps-list">
<li>Откройте <a class="text-link" href="./#ranking">список компаний</a> и прочтите обзоры: в чём сильна компания, что смущает, каков итог.</li>
<li>Сравните условия в <a class="text-link" href="./#compare">таблице</a> и посмотрите <a class="text-link" href="prices.html">цены выкупа</a>.</li>
<li>Прикиньте сумму в <a class="text-link" href="./#calc">калькуляторе</a>.</li>
<li>Запросите предложения у двух-трёх компаний из разных групп (часть сайтов, возможно, принадлежит одному оператору) и попросите закрепить цену в переписке.</li>
</ol>
<p class="note">Продажа алкоголя лицам младше 18 лет запрещена. Чрезмерное употребление алкоголя вредит здоровью.</p>
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
    body = head(f"Куда продать коньяк и виски в Москве: рейтинг скупок алкоголя — {SITE}",
                "Рейтинг 20 скупок коллекционного алкоголя в Москве и области: где продать коньяк, виски, вино и шампанское, какие цены выкупа, как быстро оценивают по фото, кто приезжает на адрес и на каких условиях.",
                path="", ld=[itemlist(CARDS), faq_ld()]) + header() + f"""
<main id="top">
<section class="hero">
<div class="container hero-grid">
<div class="hero-content">
<h1 class="hero-title">Где выгодно продать алкоголь в Москве:<br><span class="lime">сравнение скупок</span></h1>
<p class="hero-copy">Мы разобрали 20 компаний, которые скупают коньяк, виски, вино, шампанское, ром и арманьяк: кто открыто показывает цены, кто отвечает по фото за пару минут, кто едет к клиенту и как проходит расчёт. Подберите вариант под свою задачу — когда важны скорость, выгода или отсутствие лишних встреч.</p>
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
<section class="photo-band"><div class="container"><span class="eyebrow">Без рекламы</span><p>Места в рейтинге не покупаются: оценки выставляются по открытой методике, а попасть в список можно бесплатно.</p></div></section>
<section class="section ranking-section" id="ranking">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Рейтинг</span><h2 class="section-title">Скупки алкоголя<br>в Москве</h2></div>
<p class="section-copy">Каждая компания получила оценку по трём критериям: открытость цен, скорость и удобство, прозрачность самой компании. В обзорах собраны плюсы и минусы, адрес, график работы и ценовой ориентир. Как считаются оценки — в <a class="text-link" href="metodika.html">методике</a>.</p>
</div>
<div class="filters" role="group" aria-label="Фильтры">
<button class="chip active" data-filter="all">Все 20</button>
<button class="chip" data-filter="prices">Публикуют цены</button>
<button class="chip" data-filter="fast">Оценка до 5 минут</button>
</div>
<div class="company-list" id="rankingTable">
{"".join(company_card(c) for c in CARDS)}
</div>
<p class="note">Сроки и режимы работы — заявления самих компаний. «Не публикует» означает, что на проверенных страницах сайта цен нет.</p>
</div>
</section>

{compare_section([(c, c['meta']) for c in CARDS])}
{choice_section()}
{quote_block("stevenson")}
{shared_blocks()}

<section class="section ranking-section" id="faq">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Вопросы</span><h2 class="section-title">Вопросы<br>и ответы</h2></div>
<p class="section-copy">Что принимают, что не принимают и отчего цена при встрече может измениться — семь кратких ответов.</p>
</div>
<div class="faq">
{"".join(f"<details><summary>{e(q)}</summary><p>{e(an)}</p></details>" for q, an in FAQ)}
</div>
</div>
</section>

{expert_aside("home")}
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
    if topic == "vodka":
        return "цены на водку не публикуются", "Сумму называют по фото и после осмотра. Для коллекционной водки ориентиром служат аукционные цены, состояние бутылки и упаковка."
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
    if topic == "vodka":
        return "Цены на водку не публикует — сумму называет после фото."
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
    return [("cc-lead", "", r["lead"]), ("", "В чём сильна.", r["pros"]), ("", "Что настораживает.", r["cons"]), ("cc-verdict", "Итог.", r["verdict"])]


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
    examples = not hint.startswith(("Цены не", "Цены на вино не", "Цены на водку не"))
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
        ("Независимые отзывы на Яндекс Картах и в 2ГИС", "Почти ни у кого их нет."),
        ("Опубликованный прайс", "700ml, 1buyup, Red Decanter, SKUPKA-ALKOGOL."),
        ("Прозрачный дисконт", "Рядом с рыночной ценой потолок выкупа показывает лишь одна компания: дисконт около 28–33%."),
        ("Обещание «цена по фото = цена на встрече»", "1buyup, VykupAlko, Kupimalko, TotalStok — это слова компаний, а не проверенный факт."),
        ("Вероятные группы сайтов", "700ml + Alko Lombard + oldcognac; Red Decanter + SKUPKA-ALKOGOL; Cupaj Club + Alko Prikup."),
        ("Diamant Alko и Room Alco", "Услуг больше, чем у большинства, но ни независимых отзывов, ни прайса пока нет."),
    ]
    body = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td></tr>" for a, b in rows)
    return f"""<section class="section ranking-section" id="summary">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Итоги проверки</span><h2 class="section-title">Что мы проверили<br>и что выяснили</h2></div>
<p class="section-copy">Что получилось подтвердить по открытым данным, а что пока остаётся лишь словами самих компаний.</p>
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


def compare_section(rows, title="Сравнение<br>условий", copy="График, срок предварительной оценки, открытые цены и специализация — всё в одной таблице. Пригодится, когда нужно быстро выбрать, кому из компаний написать в первую очередь."):
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
<p class="section-copy">Три критерия по шкале от 1 до 5. Баллы выставляются по формальным признакам из открытых данных: это не отзывы клиентов и не проверка качества услуг.</p>
</div>
<div class="factors">
<article><h3>Прозрачность цен</h3><p>5 — опубликовано 20 и больше цен; 4 — есть прайс или ориентиры по части позиций; 2,5 — цен нет, но компания гарантирует цену, согласованную по фото; 2 — цен нет.</p></article>
<article><h3>Скорость и удобство</h3><p>Исходный балл зависит от заявленного срока оценки по фото: до 5 минут — 4,5; до 15 — 4; до 30 — 3; до 2 часов — 2,5; дольше — 2; срок не назван — 2,5. Ещё 0,5 прибавляется за работу от 14 часов в сутки, 0,5 вычитается за 9 часов и меньше и ещё 0,5 — если приём только по будням.</p></article>
<article><h3>Открытость компании</h3><p>Балл начисляется за каждый признак: указан адрес; указан режим работы; сайт самостоятельный (не копия сайта другого оператора); нет противоречий и устаревших сведений; есть публичные подтверждения (кейсы, отзывы с датами). Минимум — 1.</p></article>
</div>
<p class="note">Данные рейтинга в машиночитаемом формате: <a class="text-link" href="data/companies.json">companies.json</a> и <a class="text-link" href="data/companies.csv">companies.csv</a>.</p>
<p class="note">Итог — среднее арифметическое трёх показателей с округлением до десятых. Публичных подтверждений в открытых данных не нашлось ни у одной компании, поэтому максимума по открытости нет ни у кого. Сроки и режимы — заявления компаний. Оценка отражает данные на дату сбора и может измениться.</p>
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
<p class="note">Ориентиры, заявленные компанией; это не оферта.</p>"""


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
    return head(f"{c['name']}: условия, цены и обзор скупки алкоголя — {SITE}",
                f"{c['name']} ({c['domain']}): когда работает, как быстро оценивает по фото, выезжает ли, сколько платит, в чём сильна и что смущает. Оценка редакции — {scores(c)[1]:g} из 5.", 1,
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
<p class="note">Информация собрана {UPDATED} на открытых страницах компании; собственные заявления компании мы не проверяли. Цены и условия лучше уточнить у неё напрямую.</p>
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
                "Что платят за виски, коньяк, шампанское и вино: опубликованные цены выкупа 700ml, 1buyup, Red Decanter и SKUPKA-ALKOGOL в одной таблице с отметками «от», «до» и «прибл.».",
                path="prices.html", ld=[breadcrumbs(("Главная", ""), ("Цены выкупа", "prices.html"))]) + header() + f"""
<main class="page">
<div class="container">
<span class="eyebrow">Сводка по источникам</span>
<h1 class="page-title">Цены выкупа алкоголя в Москве</h1>
<p class="lead">Все суммы в рублях. «От» — нижний порог (700ml), «до» — максимум выкупа (1buyup, в скобках рыночная цена), «прибл.» — ориентир с сайта компании. Прочерк означает, что позицию компания не раскрывает. Столбцы между собой напрямую не сравниваются.</p>
<input class="field search" id="priceSearch" type="search" placeholder="Поиск по позиции, например Macallan" aria-label="Поиск по позиции">
<div class="table-wrap"><table class="data" id="priceTable">
<thead><tr><th>Позиция</th><th>700ml (от)</th><th>1buyup (до)</th><th>Red Decanter</th><th>SKUPKA-ALKOGOL</th></tr></thead>
<tbody>{main}</tbody></table></div>
<div class="two-col">
<div><h2 class="sub">Ром и арманьяк (только 700ml, «от»)</h2><div class="table-wrap"><table class="data"><thead><tr><th>Позиция</th><th>Цена</th></tr></thead><tbody>{rum}</tbody></table></div></div>
<div><h2 class="sub">Ценовые сегменты (SKUPKA-ALKOGOL, ориентировочно)</h2><div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Стоимость</th></tr></thead><tbody>{seg}</tbody></table></div></div>
</div>
<p class="note">Это не рыночная цена и не гарантия выплаты. Одна и та же марка стоит по-разному в зависимости от года, объёма, уровня налива, этикетки и комплектности. К примеру, у Yamazaki 18 максимум 1buyup — 32 000 ₽, а 700ml указывает «от 80 000 ₽», поэтому цифру нужно перепроверить до сделки. Данные на {UPDATED}.</p>
</div>
</main>
{shared_blocks()}
""" + footer()


TOPICS = [
    dict(file="gde-prodat-elitnyy-alkogol.html", key="elite",
         nav="Элитный алкоголь",
         title=f"Продать элитный и коллекционный алкоголь в Москве: рейтинг скупок — {SITE}",
         desc="Где в Москве продать элитный и коллекционный алкоголь: рейтинг скупок, которые берут редкий виски, коньяк, вино и шампанское. Что платят, как быстро оценивают по фото, приезжают ли на адрес и как влияют упаковка и сохранность.",
         h1="Куда продать элитный алкоголь?",
         eyebrow="Рейтинг · премиум и коллекционные бутылки",
         lead="Сопоставляем компании, которые скупают редкий виски, выдержанный коньяк, марочное вино и шампанское: кто открыто называет цены на дорогие бутылки, как скоро присылает оценку по фото и в каких случаях приезжает. Дальше — что относят к элитному алкоголю, как понять ценность бутылки и что проверить до сделки."),
        dict(file="gde-prodat-vodku.html", key="vodka",
         nav="Водка",
         title=f"Продать водку в Москве: коллекционная и премиальная, рейтинг скупок — {SITE}",
         desc="Где в Москве продать водку: какие компании берут коллекционные, лимитированные и советские бутылки, а какие согласны и на недорогие позиции. Рейтинг скупок, сроки оценки по фото, выезд, сохранность и упаковка.",
         h1="Куда продать водку?",
         eyebrow="Рейтинг · коллекционная и премиальная водка",
         lead="Обычная магазинная водка скупкам, как правило, не нужна. Их интересуют лимитированные серии, советские бутылки, премиальные марки в подарочной упаковке и коллекционные экземпляры. Показываем, кто из компаний заявляет приём такого алкоголя, кто берёт и недорогие бутылки и как устроена оценка по фото."),
]
TOPIC_BY_KEY = {tp["key"]: tp for tp in TOPICS}

VODKA_TYPES = [
    ("Премиальные марки", "Grey Goose (Франция), Belvedere и Krolewska (Польша), Ketel One (Голландия), Finlandia (Финляндия), Tito's (США), Elit by Stolichnaya", "Громкое имя, запечатанная бутылка, коробка. Стандартные позиции этих марок недороги, дороже ценятся подарочные и лимитированные выпуски."),
    ("Русские премиальные марки", "Beluga (в том числе Gold Line), Russo-Baltique, Jewel of Russia, «Юрий Долгорукий» (Youri Dolgoruki), «Императорская коллекция» (Imperial Collection)", "Дорогие российские марки в эффектных бутылках. Значение имеют серия, комплект и сохранность упаковки."),
    ("Декорированные и эксклюзивные серии", "Russo-Baltique, Billionaire Vodka, выпуски с кристаллами Swarovski, в стиле Фаберже, подарочные деревянные ящики", "Штучные экземпляры с драгоценными камнями или кристаллами. Оценка индивидуальная — по фото и сертификатам; без документов цена ниже."),
    ("Советская водка и алкоголь СССР", "«Столичная», «Московская особая», «Русская», экспортные серии, бутылки с советскими акцизами и этикетками", "Важны целая пробка, этикетка и период выпуска. Алкоголь СССР среди принимаемого называют 1buyup, TotalStok, SellMeWine и Vine&Co."),
    ("Старинные крепкие напитки", "Полугар, водки дореволюционных и ранних советских лет", "Попадаются редко и требуют проверки подлинности: без документов и истории хранения цену называют с оглядкой."),
    ("Смежные крепкие напитки", "Абсент, ликёры (Alizé), китайская водка байцзю (например, Guojiao 1573), текила", "Принимают не все и выборочно: текилу упоминает Vine&Co, у остальных приём лучше уточнить до отправки фото."),
]

VODKA_CLAIMS = [
    ("Vine&Co (Санкт-Петербург)", "Водка, текила и алкоголь СССР; оценка по фото — 5 минут"),
    ("Cupaj Club", "Любой алкоголь, включая недорогой; допускаются сделки с пересылкой транспортной компанией"),
    ("Alko Prikup", "Недорогие позиции; Москва и Санкт-Петербург, курьер забирает крупные партии"),
    ("1buyup", "Алкоголь СССР; бутылки без коробки и акцизной марки"),
    ("TotalStok", "Алкоголь СССР и старинные бутылки; заявлена работа круглосуточно"),
    ("SellMeWine", "Алкоголь СССР, коробки и футляры; операторы отвечают круглосуточно"),
]

VODKA_FAQ = [
("Принимают ли скупки обычную магазинную водку?",
 "Чаще всего нет: обычная водка дёшево стоит в рознице, и скупке на ней не заработать. Исключения — Cupaj Club и Alko Prikup, которые говорят, что берут и недорогие позиции, а также Vine&Co, прямо включившая водку в перечень принимаемого. Условия у всех свои, поэтому перед отправкой снимков спросите, подойдёт ли ваша бутылка."),
("Какая водка считается коллекционной?",
 "Это лимитированные серии и подарочные выпуски известных марок, украшенные бутылки (кристаллы Swarovski, символика Фаберже), а также советские экземпляры с уцелевшими этикеткой, пробкой и акцизом. Играют роль тираж, комплектность и документы. Обычная «Столичная» из магазина коллекционной не станет, а выпуск прошлых десятилетий с сохранившейся упаковкой — вполне может."),
("От чего зависит стоимость и почему цен на водку нет?",
 "Стоимость определяют бренд, серия, возраст бутылки, акциз, вид этикетки, герметичность пробки, уровень, коробка, документы и спрос. Цен на водку не публикует ни одна компания рейтинга: сумму называют по фото, так что просите зафиксировать её письменно. Для редких экземпляров ориентиром служат аукционные цены, а не розница."),
("Как хранить водку до продажи?",
 "В тёмном и прохладном месте, в вертикальном положении, при стабильной температуре. Крепость 40% сохраняет саму водку, но этикетка, пробка и упаковка страдают от сырости, света и перепадов температуры. Не открывайте бутылку: початые экземпляры не берут. Сберегите коробку, футляр, чек и сертификат."),
("Можно ли продать самогон или напиток домашнего изготовления?",
 "Нет. Напитки без заводской маркировки и документов не принимают, а торговля алкоголем домашнего производства запрещена законом. Бутылку с самодельной этикеткой оценщик не возьмёт."),
]


def vodka_guide():
    rows = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in VODKA_TYPES)
    return f"""<section class="section" id="guide">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">О водке</span><h2 class="section-title">Какая водка<br>интересна скупкам</h2></div>
<p class="section-copy">Рядовая магазинная водка скупкам неинтересна. Их внимание привлекают лимитированные серии, премиальные марки в подарочной упаковке, украшенные бутылки и советская водка. В таблице — категории и имена, которые встречаются чаще всего.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Примеры</th><th>Что учитывают</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="prose" style="margin-top:28px">
<p><strong>Как читать этикетку.</strong> На бутылке указаны крепость (чаще 40%), объём, страна и производитель, номер партии, дата розлива и акцизная марка. Надписи Limited edition, Collection, Series и Edition говорят о лимитированном выпуске, а Premium и Super Premium обозначают лишь ценовой класс и ничего не гарантируют. Стоимость коллекционной бутылки определяют тираж и сохранность, а не слово на этикетке.</p>
<p><strong>Из чего делают водку.</strong> Водка делается из зернового спирта (пшеница, рожь, ячмень), иногда из картофеля или кукурузы, и очищенной воды. Сырьё и страна задают вкус: в польской традиции чаще встречается рожь, во французской, голландской и американской — пшеница и кукуруза, в финской — ячмень. Для скупки вкус вторичен: смотрят на бренд, серию и сохранность бутылки.</p>
<p><strong>Что продают вместе с водкой.</strong> Вместе с водкой нередко продают коньяк, ром, абсент, ликёры и коробки. Если позиций несколько, укажите их в одной заявке: цена партии зависит от состава, а единый выезд обходится компании дешевле нескольких отдельных.</p>
</div>
</div>
</section>
"""


def vodka_assess():
    return """<section class="section ranking-section" id="assess">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Как оценивают водку</h2>
<p>Цена складывается из бренда, серии и состояния конкретной бутылки: по названию одного бренда её не назвать. Разберём, на что смотрит оценщик и что влияет на итоговую сумму.</p>
<p><strong>Подлинность и маркировка.</strong> Оценщик сверяет название, серию, тираж и номер партии, изучает акцизную марку и печать на этикетке. Дорогие и украшенные выпуски подделывают чаще, поэтому для них запрашивают сертификат, коробку и снимки со всех сторон. Подарочная упаковка и документы подтверждают происхождение и повышают ценность.</p>
<p><strong>Целостность бутылки.</strong> Проверяют герметичность пробки и капсулы, уровень содержимого, наличие подтёков, сколов и потёртостей на стекле и этикетке. У бутылок с кристаллами и декором важен каждый элемент: потерянный камень заметно снижает цену. Открытые и частично опустошённые бутылки обычно не берут.</p>
<p><strong>Упаковка и комплект.</strong> Деревянный ящик, футляр, подарочная коробка и сертификат способны оцениваться отдельно: Red Decanter предупреждает, что без оригинальной коробки цена может оказаться ниже до 30%. У советской водки главное — этикетка, пробка и период выпуска.</p>
<p><strong>Честная цена.</strong> Честной можно считать ту цену, для которой заранее объяснили, что будут осматривать и из-за чего сумма изменится. Бесплатная оценка по фото — лишь первый шаг; окончательную цифру компании озвучивают после осмотра. Если сумму называют мгновенно и без снимков, сопоставьте предложения хотя бы двух компаний.</p>
<p><strong>Кто покупает.</strong> Коллекционеры редких бутылок и советской атрибутики, рестораны и бары, те, кто собирает подарочные наборы. Спрос меняется, поэтому ценовые ориентиры всегда временные.</p>
</div>
</div>
</section>
"""


def vodka_more():
    return """<section class="section" id="regions">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Что ещё важно знать</h2>
<p><strong>Как пишут названия.</strong> Названия марок пишут по-разному: Grey Goose и «Грей Гус», Belvedere и «Бельведер», Krolewska и «Кролевска», Ketel One и «Кетел Ван», Finlandia и «Финляндия», Stolichnaya и «Столичная», Beluga и «Белуга», Youri Dolgoruki и «Юрий Долгорукий». Если сомневаетесь, напишите оба варианта и приложите фото этикетки.</p>
<p><strong>Подарок, который не нужен.</strong> Нередко продают подаренную бутылку: запечатанную премиальную водку в коробке берут охотнее, чем бутылку без упаковки. Не открывайте её, пока не решили, продавать или оставить: открытая бутылка для скупки почти ничего не стоит.</p>
<p><strong>Что не принимают.</strong> Отказывают напиткам без заводской маркировки, самогону, бутылкам с самодельными этикетками, открытым и початым экземплярам и сомнительным копиям. Продавать алкоголь могут только совершеннолетние.</p>
<p><strong>Где хранить.</strong> Подойдёт тёмное прохладное место с ровной температурой, без прямого света и сырости. Бутылки в деревянной упаковке не ставьте на пол и вплотную к батарее: дерево и бумага портятся раньше самой водки.</p>
<p><strong>Если компания в другом городе.</strong> Из других городов бутылки обычно пересылают транспортной компанией: заранее узнайте, как их упаковать, кто платит за страховку и кто отвечает за бой. Стекло укладывают плотно, в жёсткую коробку с прокладкой, а не в пакет.</p>
</div>
</div>
</section>
"""


def vodka_deal():
    return """<section class="section ranking-section" id="deal">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Как проходит сделка</h2>
<p>Общий порядок описан выше, в блоке «Как продать без лишней спешки». У водки есть собственные нюансы.</p>
<p><strong>Заявка.</strong> Пришлите снимки этикеток, пробки, коробки и акциза через форму на сайте компании, в Telegram, WhatsApp или Viber. Укажите марку, серию, объём, число бутылок, город и способ связи. Берёт ли компания вашу водку, лучше спросить сразу: многие принимают только коллекционные позиции.</p>
<p><strong>Оценка.</strong> Сумма по фото предварительная. Попросите закрепить цену письменно и узнайте, что может изменить её при осмотре.</p>
<p><strong>Встреча.</strong> Оценщик приезжает по адресу в Москве или области, либо вы встречаетесь в офисе. Он осматривает бутылку, сверяет серию, проверяет пробку и уровень. Если бутылка не совпадает со снимками, цену пересматривают.</p>
<p><strong>Расчёт.</strong> Расчёт идёт наличными или банковским переводом. Могут попросить паспорт — уточните это заранее. Не отдавайте бутылки, пока не получили деньги, и сохраните договор или расписку.</p>
</div>
</div>
</section>
"""


def vodka_faq():
    items = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in VODKA_FAQ)
    return f"""<section class="section ranking-section" id="faq">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Вопросы</span><h2 class="section-title">Вопросы<br>о продаже водки</h2></div>
<p class="section-copy">Что принимают, как хранить, от чего зависит цена и что продавать нельзя.</p>
</div>
<div class="faq">{items}</div>
</div>
</section>
"""


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
        order = ["vikup-alco.ru", "cupajclub.ru", "alkoprikup.ru", "1buyup.ru", "prodat-alko.ru", "sellmewine.ru"]
        order += [c["domain"] for c in CARDS if c["domain"] not in order]
        over = {
            "vikup-alco.ru": dict(nom="Прямо называет водку, текилу и алкоголь СССР (Петербург)"),
            "cupajclub.ru": dict(nom="Заявляет приём любого алкоголя, в том числе недорогого"),
            "alkoprikup.ru": dict(nom="Недорогие позиции; Москва и Петербург"),
            "1buyup.ru": dict(nom="Алкоголь СССР, бутылки без коробки и акциза"),
            "prodat-alko.ru": dict(nom="Алкоголь СССР и старинные бутылки, круглосуточно"),
            "sellmewine.ru": dict(nom="Алкоголь СССР, коробки и футляры, операторы 24/7"),
        }
        for c in CARDS:
            over.setdefault(c["domain"], {})
            over[c["domain"]].update(price="Не публикует", price_n="цены на водку")
    out = []
    for i, d in enumerate(order, 1):
        c = by[d]
        m = dict(c["meta"])
        m.update(over.get(d, {}))
        out.append((c, m, i))
    return out


ELITE_CATS = [
    ("Виски", "The Macallan, Glenfiddich, Glenmorangie, Highland Park, Balvenie, Yamazaki, Johnnie Walker (Black Label, Blue Label)", "Шотландский виски гонят уже не одно столетие. Смотрят на винокурню, возраст, лимитированность и тираж; обиходные версии вроде Red Label к элитным не причисляют."),
    ("Коньяк, арманьяк, кальвадос, бренди", "Hennessy, Rémy Martin, Martell, Courvoisier, Hine, Frapin, Camus, Metaxa, Torres, Saint-Rémy, Veterano, Vecchia Romagna", "Производство коньяка, арманьяка и кальвадоса жёстко регламентировано — от сырья и урожая до выдержки. Коллекционные категории — XO, XXO, Hors d'Age, Grande Champagne; важны год и состояние бутылки."),
    ("Вина Франции", "Бордо: Lafite Rothschild, Chateau Mouton Rothschild, Château Latour, Margaux, Haut-Brion, Cheval Blanc, Lafleur, Le Pin, Petrus. Бургундия: Domaine de la Romanée-Conti, Domaine Leroy, Leflaive, Meo-Camuzet", "Бордо и бургундские вина оценивают по урожаю и классификации (Grand Cru, Premier Cru). Интерес представляют и вина долины Роны (Кот-дю-Рон), и эльзасские."),
    ("Вина Италии, Испании, США, Австралии", "Gaja, Ornellaia, Sassicaia, Masseto, Bruno Giacosa, Soldera (Case Basse), Vega Sicilia, Pingus, Harlan Estate, Screaming Eagle, Penfolds Grange", "Из Италии ценят вина Тосканы, Пьемонта, Венето и Сицилии, из Испании — Vega Sicilia и Pingus. Американские и австралийские бутылки попадают в собрания за счёт малых тиражей."),
    ("Шампанское", "Dom Pérignon, Cristal, Krug, Salon, Veuve Clicquot, Moët & Chandon, Bollinger", "Дороже других — миллезимные выпуски и крупные форматы: магнум и больше."),
    ("Ром, портвейн, херес, ликёры, абсент", "Havana Club, Zacapa, Caroni, Taylor's (Oporto), херес, ликёры, абсент, ракия", "Принимают их не все компании и выборочно: значение имеют возраст, редкость и сохранность. Сомневаетесь — пришлите фото; ракию и другие региональные напитки оценивают отдельно."),
    ("Алкоголь СССР и старые бутылки", "Массандра (Крым), грузинское и крымское вино, коньяки и вина, выпущенные до 1990 года", "Красное и белое вино, коньяки, коллекционная водка и ликёры советских лет интересны при условии, что сохранились этикетка, пробка и уровень. Открытые бутылки обычно не принимают."),
]

ELITE_FAQ = [
("Как понять, что бутылка элитная и сколько она может стоить?",
 "Элитной считается бутылка, чью ценность создают редкость, производитель, возраст и сохранность: место производства, винокурня или шато, урожай, выдержка, миллезим, тираж. Повседневные позиции сюда не относятся, а шестизначные суммы характерны для супер-премиума от 100 000 ₽. Определите год, объём, серию и номер партии, осмотрите этикетку, пробку и уровень, а затем сверьте цифры с открытыми прайсами скупок и аукционов. Если не уверены, обратитесь к специалисту: даже известный бренд без опыта оценить непросто. Видеть в бутылке инвестицию рискованно — рост цены никто не гарантирует."),
("Можно ли продать подаренную или унаследованную бутылку, если в этом не разбираешься?",
 "Да. Если коньяк или виски достались человеку, который не пьёт, не открывайте их: сфотографируйте этикетки, пробку и уровень, найдите коробку и бумаги и отправьте снимки в две-три компании. Спросить знакомых, разбирающихся в теме, полезно, но сравнивать лучше с профессиональной оценкой. Магазинной цены за подарочную бутылку ждать не стоит: выкуп всегда дешевле розницы, ведь компания закладывает свою выгоду."),
("Как не нарваться на подделку и испорченное хранение?",
 "Подделки чаще попадаются среди самых дорогих позиций, а по фото их трудно распознать. Внимательно изучите вживую этикетку и контрэтикетку, шрифт, печать, знаки на стекле, номер партии, пробку и капсулу; фотографируйте при хорошем свете. Бутылка должна быть запечатана, укупорка — цела: жара, свет и сквозняки портят содержимое и снижают цену. Для долгого хранения обычный холодильник не годится — нужны постоянная температура и умеренная влажность. Сомневаетесь в подлинности — покажите бутылку эксперту до сделки."),
("Почему цены на одну и ту же бутылку так отличаются?",
 "За образец берут мировые аукционные котировки и цены импортёров, а не магазинный ценник, поэтому в интернете встречаются и завышенные предложения, и демпинг. Разброс объясняют год, формат (магнум и литровые бутылки), сохранность, упаковка и популярность выпуска. Не опирайтесь на одну цифру и не верьте «самой высокой цене»: сравните не меньше двух предложений. Цена, во много раз превышающая рыночную, так же подозрительна, как и сильно заниженная. Крупную коллекцию обсуждайте отдельно: для партии из десятков бутылок условия обычно другие."),
("Работают ли скупки с регионами и другими странами?",
 "Многие компании заявляют, что работают по России и СНГ, но условия у них разные. Жителям Екатеринбурга, Челябинска, Омска, Воронежа, Ростова-на-Дону, Самары, Перми, Уфы, Сочи, Владивостока, Симферополя и других городов чаще всего предлагают пересылку транспортной компанией или встречу в Москве. Для Казахстана, Армении, Белоруссии, Украины, Литвы, Латвии и Эстонии многое определяют таможенные правила — уточняйте заранее и не отправляйте бутылку без предварительных договорённостей. Узнайте, кто отвечает за доставку, и упакуйте бутылки плотно."),
("Как безопаснее обсудить цену и расчёт?",
 "Договариваться лучше там, где остаётся переписка, и ничего не платить вперёд. Схема «цена по фото, расчёт на месте» вполне нормальна, но итоговую сумму подтвердите письменно ещё до встречи. Выясните, как проходит расчёт и нет ли комиссий (обычно их нет), и добейтесь конкретной, а не «примерной» цены. На встречу возьмите родную коробку и документы и внимательно прочитайте договор. Если предлагают провести сделку через сторонний сервис — откажитесь. Не торопитесь: ответы нескольких компаний обычно приходят за день-два."),
]


def elite_guide():
    rows = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in ELITE_CATS)
    return f"""<section class="section ranking-section" id="guide">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">О категории</span><h2 class="section-title">Что относят<br>к элитному алкоголю</h2></div>
<p class="section-copy">Элитным называют алкоголь, ценность которого создаёт не вкус одного вечера, а редкость, производитель, возраст и состояние бутылки. В таблице — основные категории и то, на что обращают внимание в каждой.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Примеры</th><th>Что учитывают</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="prose" style="margin-top:28px">
<p><strong>Почему одни бутылки дороже других.</strong> Страна и место производства, винокурня или хозяйство, урожай, выдержка, миллезим и малый тираж делают из обычной бутылки предмет коллекции. Вековые традиции виноделия объясняют, почему одни экземпляры стоят десятки тысяч евро, а другие остаются малоценными: даже любопытный современный выпуск не привлечёт собирателей, если тираж огромен. На цену влияют и подлинность, упаковка, сохранность, а не только название.</p>
<p><strong>На что обратить внимание перед продажей.</strong> Осмотрите бутылку: этикетку, пробку, уровень, упаковку; установите год и объём, соберите документы и чеки. Открывать и пробовать ничего не нужно — початые бутылки обычно не берут. Свяжитесь с несколькими компаниями и учтите, что аукционные цены и цены скупок расходятся. Выбирать лучше по профилю: виски, коньяк, вино или шампанское — у каждой категории свои специалисты.</p>
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
<p><strong>Откуда берётся ценность.</strong> Рынок коллекционного алкоголя вырос на давних традициях. Шотландский виски делают веками, а в последние десятилетия он из ремесла превратился в мировую индустрию: винокурен сотни, и у каждой свой почерк. Коньяк производят в одноимённом регионе по строгим правилам; для арманьяка и кальвадоса действуют похожие. В вине всё решают сорт, почва и погода конкретного года, поэтому выпусков великое множество — от лёгких свежих белых до выдержанных красных бордо вроде Шато Мутон Ротшильд, Шато Марго или Петрюс. Коллекционеры особенно дорожат бутылками, о которых известно всё: производство, год, тираж, история владения.</p>
<p><strong>Регионы и стили.</strong> Среди итальянских вин выделяются тосканские и пьемонтские производители, среди французских — бургундские, бордоские и вина долины Роны. Любопытны немецкий рислинг и эльзасские белые, хотя в скупках они встречаются реже. Мода на недооценённые регионы и возрождение забытых виноделен открывает изящные вина из менее известных мест, но коллекционный рынок консервативен: в основном нужно легендарное имя. Лимитированный выпуск, как правило, ценится выше обычного.</p>
<p><strong>Как проходит продажа.</strong> Почти любую сделку можно начать с дистанционной оценки по фото, но потом понадобится осмотр. Составьте список бутылок и снимите каждую так, чтобы в кадр попала контрэтикетка: надёжно лишь то, что подтверждено документами. На встрече бутылки осматривает оценщик, а предварительная подготовка экономит время. После сделки сохраните договор или расписку. Если бутылка досталась вам от прежнего владельца, комплект документов поможет подтвердить её происхождение, а импортное происхождение без бумаг может усложнить оценку. Ответы нескольких компаний проясняют картину и позволяют решить спокойнее.</p>
<p><strong>Цены в валюте.</strong> Результаты аукционов публикуют в долларах, евро и фунтах, поэтому перед сравнением пересчитайте их в рубли по курсу на дату продажи. Десятки тысяч долларов за редчайшую бутылку — не диковина, но к ожиданиям от обычной скупки это отношения не имеет: такие суммы бывают лишь у единичных позиций. Если коллекция собиралась годами, помните и о спросе: через год картина может измениться.</p>
</div>
</div>
</section>
"""


def elite_more():
    return """<section class="section ranking-section" id="more">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Что ещё важно знать перед продажей</h2>
<p><strong>Коллекция, хобби и вложение.</strong> Для одних коллекционирование алкоголя — страсть на всю жизнь, другие видят в редкой бутылке инвестиционный актив. Но и покупая, и продавая, помните: цену определяет спрос, а не возраст. Бутылка, десятилетиями стоявшая в серванте, может оказаться малоценной, а выпуск малого тиража, напротив, дорожает. Пополняя собрание, покупатель смотрит на редкость, сохранность и документы, а не на красивую этикетку.</p>
<p><strong>Что не относится к алкоголю.</strong> Скупка алкоголя и скупка антиквариата — разные вещи. Самовары, граммофоны, монеты, произведения искусства, мебель, электронику, оборудование и транспорт рейтинг не оценивает. Если компания занимается и антиквариатом, и алкоголем, как Alcovikup и TotalStok, стоит внимательнее проверить её специализацию.</p>
<p><strong>Какие вина встречаются реже.</strong> Помимо бордо и бургундского скупки обращают внимание на эльзасские и прочие французские сухие вина, южноитальянские и сицилийские бутылки, австрийский рислинг, крымское и грузинское вино советского розлива. Малоценными считаются массовые полусладкие вина и большинство игристых без года. Спрос на недооценённые регионы растёт, но у скупок он пока невысок. О водке подробнее — на странице про <a class="text-link" href="gde-prodat-vodku.html">скупку водки</a>.</p>
<p><strong>Если вы живёте не в Москве.</strong> Если бутылки находятся в Крыму, Сочи, Ростове-на-Дону, Перми, Воронеже, Омске, Екатеринбурге, Челябинске или Владивостоке, вопрос чаще решают пересылкой. При продаже за границу — в Казахстан, Армению, Белоруссию, Литву, Великобританию и другие страны — действуют ограничения на ввоз и вывоз алкоголя, а для бывших союзных республик условия отличаются: выясняйте их заранее и письменно. Если нужна встреча в Москве, согласуйте время и место и не передавайте бутылки, пока сумма не подтверждена.</p>
<p><strong>Когда продавать, а когда подождать.</strong> Рано или поздно продавать приходится всем, кто собирает алкоголь, но оставлять бутылки без присмотра на месяцы не стоит: в серванте или обычном холодильнике вино и коньяк портятся, и растёт риск остаться с испорченной бутылкой. То, что лежит мёртвым грузом, лучше оценить сразу. Не открывайте бутылки к праздникам, если планируете продавать: в цене только запечатанные экземпляры. Когда закрывается ресторан или бар, остатки алкоголя продают одной партией.</p>
<p><strong>Как работают профессионалы.</strong> Оценщики внимательно осматривают бутылку: знаки на стекле, контрэтикетку, пробку, уровень налива. Дегустацию при оценке не устраивают, а открытую бутылку, как правило, не берут. Дорогие позиции с шестизначной ценой оценивают отдельно: ориентируются на мировые аукционы, а не на магазинный ценник. Ситуации бывают разные — подаренная бутылка у непьющего владельца, распродажа остатков, частное собрание из десятков экземпляров, — и у каждой свой подход, поэтому обращайтесь к тем, кто разбирается в вашей теме: французских, итальянских или испанских винах, шотландском виски, коньяке. Стили Бордо, Бургундии, Тосканы, Пьемонта, Венето и Сицилии знатоки различают сразу, а свежие малоценные выпуски обычно не вызывают интереса.</p>
<p><strong>Как общаться с компанией.</strong> Пишите на электронную почту, в Telegram или WhatsApp: переписка остаётся в архиве. Оценщики обязаны отвечать на вопросы о цене и подлинности, не подгоняя вас. Картинки из интернета не годятся — нужны снимки именно вашей бутылки. Оставляя заявку, вы разрешаете обработку данных компании, а не нашему сайту. Аукционные цены — ориентир, но не гарантия итоговой суммы, поэтому записывайте условия и сохраняйте переписку.</p>
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
<p class="section-copy">Ценность бутылки, подделки, цена, регионы и безопасная сделка.</p>
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
<p class="section-copy">Грань между обычным и элитным алкоголем размыта. Для выкупа ориентиром считается премиум-класс от 10 000 ₽ и супер-премиум свыше 100 000 ₽.</p>
</div>
<div class="two-col">
<div><h3 class="sub" style="margin-top:0">Ценовые сегменты (SKUPKA-ALKOGOL)</h3><div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Стоимость</th></tr></thead><tbody>{seg}</tbody></table></div>
<p class="note">Цифры приблизительные: это не рыночная цена и не гарантия выплаты.</p></div>
<div><h3 class="sub" style="margin-top:0">Как выбрать скупку для дорогих бутылок</h3><div class="prose">
<p>Для редких и дорогих бутылок решают подлинность и экспертиза. Red Decanter заявляет оценку силами сомелье, 700ml даёт самый подробный прайс, а 1buyup показывает рыночную цену рядом с потолком выкупа.</p>
<p>После фото попросите закрепить сумму письменно и узнайте, как компания подтверждает подлинность. Для партии из нескольких бутылок запросите предложения у двух-трёх компаний из разных групп (см. «Возможно, один оператор»).</p>
<p>Упаковка отражается на цене: без родной коробки она бывает ниже до 30% (данные Red Decanter). Сохраните тубус, футляр и документы.</p></div></div>
</div>
<h3 class="sub">Примеры дорогих позиций из прайсов</h3>
<div class="table-wrap"><table class="data"><thead><tr><th>Позиция</th><th>Цена</th><th>Источник</th></tr></thead><tbody>{exr}</tbody></table></div>
<p class="note">Ориентиры заявлены компаниями и не являются офертой. Полный перечень — на странице <a class="text-link" href="{p}prices.html">«Цены выкупа»</a>.</p>
</div>
</section>
"""
    seg = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td></tr>" for a, b in SEG)
    claims = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td></tr>" for a, b in VODKA_CLAIMS)
    return f"""<section class="section" id="topic">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Что заявляют компании</span><h2 class="section-title">Кто и что берёт<br>из водки</h2></div>
<p class="section-copy">Цен на водку нет ни у одной компании рейтинга, но некоторые прямо пишут, какой алкоголь берут. Ниже — только эти заявления: проверить их можно, отправив заявку с фото.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Компания</th><th>Что заявляет</th></tr></thead><tbody>{claims}</tbody></table></div>
<p class="note">Это заявления компаний, а не оферта. У остальных компаний рейтинга водка в перечне принимаемого не значится.</p>
<div class="two-col" style="margin-top:36px">
<div><h3 class="sub" style="margin-top:0">Ценовые сегменты (SKUPKA-ALKOGOL)</h3><div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Стоимость</th></tr></thead><tbody>{seg}</tbody></table></div>
<p class="note">Сегменты относятся к алкоголю в целом, водку компания отдельно не выделяет. Это не рыночная цена и не гарантия выплаты.</p></div>
<div><h3 class="sub" style="margin-top:0">От чего зависит цена бутылки</h3><div class="prose">
<p>Бренд и серия: лимитированные выпуски и украшенные бутылки с кристаллами или символикой Фаберже оценивают отдельно — по фото и сертификатам.</p>
<p>Сохранность: целые пробка и акциз, ровный уровень, чистая этикетка. Без родной коробки цена порой ниже до 30% (данные Red Decanter).</p>
<p>Период выпуска: у советской водки главное — уцелели ли этикетка и пробка.</p></div></div>
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
    return head(tp["title"], tp["desc"], path=tp["file"], ld=[breadcrumbs(("Главная", ""), (tp["h1"].rstrip("?"), tp["file"])), itemlist([c for c, m, i in rows])] + ([faq_ld(VODKA_FAQ)] if tp['key'] == 'vodka' else [faq_ld(ELITE_FAQ)])) + header() + f"""
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
<div><span class="eyebrow">Рейтинг</span><h2 class="section-title">{e('Скупки водки' if tp['key']=='vodka' else 'Скупки элитного алкоголя')}<br>в Москве</h2></div>
<p class="section-copy">{'Компании расставлены по тому, насколько открыто они заявляют приём водки и алкоголя СССР; цен на водку не публикует никто. Как считаются оценки — в <a class="text-link" href="metodika.html">методике</a>.' if tp['key']=='vodka' else 'Скупки дорогих и редких бутылок сравниваются по скорости оценки, ценам и условиям сделки. Как считаются оценки — в <a class="text-link" href="metodika.html">методике</a>.'}</p>
</div>
<div class="company-list" id="rankingTable">
{cards_html}
</div>
<p class="note">Сроки оценки и режимы работы — заявления самих компаний. «Не публикует» означает, что на проверенных страницах сайта цен нет. Порядок компаний здесь определяется профильностью для темы и полнотой данных, а не качеством услуг; подробности — в методике.</p>
</div>
</section>

{compare_section([(c, m) for c, m, i in rows])}
{topic_extra(tp['key'], 0)}
{vodka_guide() + expert_aside('vodka') + vodka_assess() + vodka_more() + vodka_deal() + vodka_faq() if tp['key'] == 'vodka' else elite_guide() + expert_aside('elite') + elite_notes() + quote_block('pushkin') + elite_more() + elite_faq()}
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
    op = f"{ph('name', 'ФИО оператора')}"
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
<h2>1. Общие положения</h2>
<p>Настоящая политика описывает, как сайт «{SITE}» ({SITE_URL}) обрабатывает персональные данные посетителей. Оператор персональных данных — {op}, e-mail для обращений: {ph('email', 'e-mail')}. Политика составлена в соответствии с Федеральным законом от 27.07.2006 № 152-ФЗ «О персональных данных».</p>
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
<p>{op}<br>E-mail: {ph('email', 'e-mail')}</p>
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
<p>Рейтинг опирается на открытые данные, поэтому в нём возможны неточности и устаревшая информация. Если вы представляете компанию из списка, свяжитесь с нами: мы проверим сведения и при необходимости исправим карточку.</p>
<h2>С чем можно обратиться</h2>
<ul>
<li>устаревшие или ошибочные контакты, адрес, график работы, срок оценки;</li>
<li>неверно указанные цены и условия сделки;</li>
<li>фактические ошибки в обзоре;</li>
<li>претензии к опубликованным материалам.</li>
</ul>
<h2>Как рассматриваем обращения</h2>
<ol class="steps-list">
<li>Заполните форму ниже или напишите на {ph('email', 'e-mail')}: объясните, что именно не так, и приложите ссылку на страницу сайта, документ или иное подтверждение.</li>
<li>Мы сверяем данные с открытыми источниками и отвечаем в течение {CLAIM_DAYS} рабочих дней.</li>
<li>Если ошибка подтвердилась, исправляем данные и при необходимости пересчитываем оценку; если нет — объясняем причину.</li>
<li>По вашему желанию в карточке можно разместить краткий ответ компании.</li>
</ol>
<h2>Что остаётся без изменений</h2>
<ul>
<li>Оценка, рассчитанная по формуле из <a class="text-link" href="metodika.html#score">методики</a>, если исходные данные верны.</li>
<li>Выводы обзоров, основанные на проверяемых фактах: оценочные суждения мы не удаляем по просьбе компании.</li>
<li>Заявления компаний о самих себе («5000 сделок», «до 90% рынка»): мы лишь помечаем их как заявления и не проверяем.</li>
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
<p class="note">Если форма не открывается или удобнее написать письмом — воспользуйтесь {ph('email', 'e-mail')}.</p>
"""
    return simple_page(f"Для компаний: как исправить данные в карточке — {SITE}", "Для компаний из рейтинга: как сообщить об ошибке в карточке, отправить претензию и получить ответ редакции.",
                       "dlya-kompanii.html", "Для организаций", "Нашли неточность в карточке своей компании? Напишите — проверим и поправим.", body, eyebrow="Обратная связь")


def contacts_page():
    body = f"""
<p>«{SITE}» — независимый справочник, а не скупка алкоголя. Здесь можно написать редакции: спросить о рейтинге, сообщить об ошибке или предложить компанию для сравнения.</p>
<h2>Редакция</h2>
<p>Оператор сайта: {ph('name', 'ФИО оператора')}<br>E-mail: {ph('email', 'e-mail')}</p>
<h2>Куда написать</h2>
<ul>
<li><strong>Вы представитель компании из рейтинга</strong> и обнаружили ошибку или хотите отправить претензию — <a class="text-link" href="dlya-kompanii.html">страница для компаний</a>.</li>
<li><strong>Вы читатель</strong>: хотите указать на неточность или поделиться опытом сделки — пишите на e-mail редакции.</li>
<li><strong>Вопросы о персональных данных</strong> (доступ, удаление, отзыв согласия) — на тот же адрес, подробнее в <a class="text-link" href="politika-konfidencialnosti.html">политике конфиденциальности</a>.</li>
</ul>
<p class="note">Мы не покупаем алкоголь и не принимаем бутылки. Чтобы продать коньяк, виски или вино, обратитесь напрямую в выбранную компанию — её контакты указаны в карточке.</p>
"""
    return simple_page(f"Контакты редакции — {SITE}", "Как написать редакции рейтинга скупок алкоголя: e-mail, оператор сайта и страница для компаний.",
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
             "> Обзор 20 компаний, принимающих коньяк, виски, вино, шампанское и другой коллекционный алкоголь: как быстро оценивают по фото, какие цены раскрывают, на каких условиях заключают сделки, в чём сильны и слабы, какую оценку редакции получили по трём критериям. Сайт ничего не продаёт и услуг не оказывает; сведения справочные и могут устареть, актуальные данные — на сайтах компаний. Данные собраны 30.09.2026.", "",
             "## Основные страницы", "",
             f"- [Где продать алкоголь в Москве]({SITE_URL}/): рейтинг и таблица сравнения 20 компаний",
             f"- [{TOPICS[0]['h1'].rstrip('?')}]({SITE_URL}/{TOPICS[0]['file']}): скупки, работающие с дорогими и редкими бутылками",
             f"- [{TOPICS[1]['h1'].rstrip('?')}]({SITE_URL}/{TOPICS[1]['file']}): компании, заявляющие приём водки и алкоголя СССР",
             f"- [Цены выкупа]({SITE_URL}/prices.html): свод опубликованных цен четырёх компаний",
             f"- [Методика]({SITE_URL}/metodika.html): источники, правила оценки, ограничения",
             f"- [О рейтинге]({SITE_URL}/o-reitinge.html): миссия, принципы и эксперт",
             f"- [Для организаций]({SITE_URL}/dlya-kompanii.html): как поправить данные или отправить претензию", "",
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
        money = "<p>Попасть в рейтинг можно бесплатно. Редакция не получает от компаний денег за место в списке, оценку или текст обзора.</p>"
    else:
        money = f"<p>{ph('name', 'опишите, получает ли сайт вознаграждение от компаний; если да — размещение является рекламой и требует маркировки')}</p>"
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
{expert_block()}
<h2>1. Принципы</h2>
<ul>
<li>Все компании сравниваются по одним и тем же открытым данным и по единым правилам.</li>
<li>Факты отделены от заявлений: «5000 сделок» или «до 90% рынка» мы подписываем как заявления и не выдаём за проверенные.</li>
<li>О недостатках пишем столь же подробно, как о достоинствах.</li>
<li>Мы не оцениваем качество услуг и не гарантируем результат сделки: оценка отражает прозрачность и открытость компании.</li>
</ul>
<h2>2. Источники</h2>
<p>Публичные сайты компаний. Если сайт нельзя было прочитать автоматически, использовались фрагменты поисковой выдачи — в карточке это отмечено. Сведения собраны 30 сентября 2026 г. Оценки и отзывы с карт в расчёте не учитываются.</p>
<h2>3. Как считается оценка</h2>
<p>Оценка редакции строится на трёх параметрах по правилам из <a class="text-link" href="metodika.html#score">методики</a>. Исходные данные и итог по каждой компании доступны: <a class="text-link" href="data/companies.json">companies.json</a>.</p>
<h2>4. Как отбираем компании</h2>
<p>Компании для сравнения подбирает редакция. Если вы представляете компанию и хотите, чтобы её рассмотрели, используйте <a class="text-link" href="dlya-kompanii.html">страницей для компаний</a>.</p>
<h2>5. Исправления и право ответа</h2>
<p>Если мы ошиблись, сообщите через <a class="text-link" href="dlya-kompanii.html">страницу для компаний</a> или на {ph('email', 'e-mail')}. Проверка занимает до {CLAIM_DAYS} рабочих дней, подтверждённые ошибки мы исправляем. По просьбе компании в её карточке можно разместить краткий ответ.</p>
<h2>6. Независимость и конфликт интересов</h2>
{money}
<p>Если у редакции возникнут отношения с оцениваемой компанией — владение, партнёрство или оплата, — мы раскроем их на сайте до публикации.</p>
<h2>7. Обновление данных</h2>
<p>Информация устаревает. Дата сбора указана в методике; при существенных изменениях карточки обновляются.</p>
"""
    return simple_page(f"Редакционная политика — {SITE}", "Правила, по которым составляется рейтинг скупок алкоголя: источники данных, отбор компаний, исправление ошибок и независимость редакции.",
                       "redakcionnaya-politika.html", "Редакционная политика", "Как строится рейтинг и как мы поступаем, когда ошибаемся.", body)


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
<p>{ph('name', 'ФИО оператора')}, e-mail: {ph('email', 'e-mail')}. Страница <a class="text-link" href="kontakty.html">«Контакты»</a>.</p>
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
        (ROOT / ".htaccess").write_text("# Шапка и подвал подключаются директивами SSI (<!--#include virtual=\"/includes/...\" -->)\nOptions +Includes\nAddType text/html .html\nAddOutputFilter INCLUDES .html\n", encoding="utf-8")
    else:
        (ROOT / ".htaccess").unlink(missing_ok=True)
    bots = "".join(f"User-agent: {b}\nAllow: /\n\n" for b in AI_BOTS)
    (ROOT / "robots.txt").write_text(f"# Поисковые и ИИ-краулеры допускаются явно; служебные папки закрыты для всех\n{bots}User-agent: *\nAllow: /\nDisallow: /standalone/\nDisallow: /tools/\nDisallow: /includes/\nDisallow: /send.php\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")


# Фото-полосы между текстовыми блоками: (файл страницы) -> [(id секции, перед которой вставить, картинка, подпись, текст, ссылка, текст кнопки)]
# Контрастные вставки-цитаты между блоками (без кнопок и перелинковки): (id секции, перед которой вставить, картинка-класс, подпись, текст, —, —)
BANDS = {
    "index.html": [
        ("calc", "banner2.jpg", "Прежде чем продавать", "Сопоставляйте не только цены, но и условия: срок оценки, способ оплаты и приезд курьера.", "#choose", "Пять вопросов перед сделкой"),
        ("prepare", "banner3.jpg", "Подготовка", "Коробка, документы и неповреждённая этикетка ощутимо влияют на итоговую цену выкупа.", "#prepare", "Как подготовить бутылку"),
    ],
    "gde-prodat-elitnyy-alkogol.html": [
        ("topic", "banner2.jpg", "Редкие бутылки", "У дорогих бутылок особенно важны подлинность, комплектность и условия хранения.", "#guide", "Что считается элитным"),
        ("faq", "banner3.jpg", "Перед сделкой", "Снимите этикетку, пробку и уровень налива — тогда оценка пройдёт быстрее.", "#prepare", "Как подготовить бутылку"),
    ],
    "gde-prodat-vodku.html": [
        ("topic", "banner.jpg", "Водка", "Скупки принимают не всякую водку: решают серия, упаковка и сохранность бутылки.", "#guide", "Какая водка интересна"),
        ("faq", "banner2.jpg", "Перед сделкой", "Целая пробка, акциз и родная коробка помогают сохранить цену бутылки.", "#assess", "Как оценивают водку"),
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


STATS = [("67–72%", "типичный выкуп от рыночной цены бутылки"), ("28–33%", "скидка по таблице 1buyup: потолок выкупа против рынка"),
         ("до −30%", "к цене, если нет родной коробки (данные Red Decanter)"), ("×2,5", "разрыв «от» и «до» по Yamazaki 18: 80 000 против 32 000 ₽")]


def stats_strip():
    tiles = "".join(f'<div class="stat-tile"><b>{e(a)}</b><span>{e(b)}</span></div>' for a, b in STATS)
    return f'<section class="section stats-section" aria-label="Цифры рынка"><div class="container"><div class="stats-strip">{tiles}</div><p class="note">Ориентиры построены на открытых данных компаний и таблицах цен; это не оферта и не гарантия выплаты.</p></div></section>\n'


def decorate_page(page, key):
    page = decorate_prose(page)
    if key in ("gde-prodat-vodku.html", "gde-prodat-elitnyy-alkogol.html"):
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
