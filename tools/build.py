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
SITE_URL = "https://gradus-rating.ru"   # адрес сайта без слеша в конце (нужен для canonical, sitemap, robots, og)
OPERATOR = dict(                      # оператор персональных данных (подставляется в политики и на страницу «Для компаний»)
    name="Филипп Антипов",      # ФИО или название организации/ИП
    inn="",       # необязательно: если пусто — ИНН нигде не показывается
    address="",   # необязательно: если пусто — адрес нигде не показывается
    email="expert@gradus-rating.ru",     # e-mail для обращений
    phone="",     # необязательно: показывается только если заполнено
    telegram="",  # Telegram редакции, например @gradus_rating
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
    name="Филипп Антипов",
    role="Винный консультант · Сомелье · Эксперт по дегустации",
    about='Филипп Антипов — специалист в области вина и гастрономической культуры, посвятивший профессиональную деятельность изучению винодельческих традиций и развитию современной культуры потребления вина.\n\nЗа годы работы он сформировал глубокую экспертизу в области европейского виноделия, уделяя особое внимание французским, итальянским и испанским регионам. В его профессиональной практике — подбор вин для ресторанных проектов, работа с частными винными собраниями и проведение дегустаций для любителей и профессионалов.\n\nФилипп регулярно знакомится с новыми винодельческими хозяйствами, следит за изменениями на международном винном рынке и изучает особенности различных терруаров. При выборе вина особое внимание уделяет балансу, стилю производителя, происхождению и гастрономической сочетаемости.\n\nВ профессиональной работе придерживается индивидуального подхода: помогает подобрать вино с учётом вкусовых предпочтений, блюда и повода. Также консультирует по формированию винных коллекций и оптимальным условиям хранения.\n\nЕго подход основан на сочетании практического опыта, внимательного отношения к деталям и стремления сделать винную культуру понятной и доступной для широкой аудитории.',
    credentials="Профессиональный опыт: более 10 лет · Москва, Россия",
    photo="assets/expert.jpg",   # фото эксперта (положите файл с таким именем); без файла блок показывается без фото
    disclosure="Филипп Антипов — независимый эксперт и оператор сайта.",
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
BUILD_DATE = "2026-10-01"             # дата для sitemap (lastmod)
POLICY_DATE = "1 октября 2026 г."
# --------------------------------------------------------------------------------------------------

SITE = "ГРАДУС"
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
  "Подаренный коньяк или виски проще всего оценить онлайн: заполните форму или отправьте качественный снимок и дополнительные фото, и сравните два-три ответа. Достаточно, чтобы работала электронная почта или мессенджер, а ехать на встречу сразу не обязательно (скажем, практически всё можно согласовать удалённо): комфортные условия расчёта можно обсудить удалённо, и компания сможет выкупить бутылку даже при отправке."
 ],
 [
  "Редкий экземпляр ограниченной серии",
  "Редкие экземпляры, выпущенные ограниченным тиражом, лучше доверять профессионалам: выбирайте компании с оценкой сомелье и публичными ценами. Сообщите точный год, место производства и состояние. Знания оценщика здесь важнее скорости: это обусловлено тем, что цену меняет даже небольшая разница в уровне жидкости или состоянии этикетки."
 ],
 [
  "Большая коллекция",
  "Для большой коллекции попросите полной оценки списком и узнайте, как организовать вывоз, договор и способ расчёта. Партнёра по сделке стоит проверить по реквизитам. Уточните, нет ли ограничений по объёму и предоставят ли вам договор до проведения осмотра; дополнительная консультация специалиста не повредит."
 ],
 [
  "Остатки ресторана или магазина",
  "Ищите опт: условия у некоторых компаний начинаются от 10 бутылок, и они выезжают с инвентаризацией. Для объектов подобного рода выезд — обычная практика, а наиболее выгодные условия обычно обсуждают отдельно."
 ],
 [
  "Срочно",
  "Если нужно решить вопрос сейчас, выбирайте компании с оценкой за несколько минут и поздним графиком. Звоните или пишите сразу нескольким представителям, но принять решение стоит только после того, как цена названа и подтверждена в точности. Чтобы не позволить спешке повлиять на сумму, зафиксируйте условия письменно."
 ],
 [
  "Другой город или страна",
  "Из других городов и страны возможна отправка транспортной компанией; выясните, кто отвечает за доставку. На территории Москвы и области выехать могут, по заявлениям компаний, в течение дня. Когда рассмотрено несколько предложений, выберите то, где обмен документами и деньгами происходит безопаснее."
 ],
 [
  "Нужно понять, сколько стоит",
  "Если надо определить порядок суммы, перейдите к калькулятору и таблице цен, а уже потом обращайтесь в интересующую вас компанию. Потребность в консультации возникает почти у каждого: она помогает разобраться в нюансах и не ждать, что цена окажется гораздо выше рыночной."
 ],
 [
  "Старые и современные бутылки",
  "Для современной бутылки решают упаковка и аккуратное состояние, а для старых — год, уровень и сохранность. Именитый производитель и популярные позиции повышают интерес, а спрос на редкие вещи увеличивается быстрее, чем на массовые продукты."
 ],
 [
  "Вы ещё не решились",
  "Это нормально: оценку можно запросить, а бутылку оставить себе — по вкусу или по иному поводу. Для определения цены достаточно качественного фото, а некачественной съёмки лучше избегать, обеспечивая оценщику чёткий кадр и копии сопроводительных документов. Мы понимаем, что в жизни коллекции решение личное, и никакого давления в отношении продажи у рейтинга нет."
 ]
]


def choice_section():
    rows = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td></tr>" for a, b in CHOICES)
    return f"""<section class="section ranking-section" id="choice">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Под вашу задачу</span><h2 class="section-title">Кому что<br>подойдёт</h2></div>
<p class="section-copy">Задача у каждого своя, поэтому и подход к выбору разный. По опыту рынка, условия, удобные в одной ситуации, бывают лишними в другой. Алкоскупка — направление деятельности, где проверяемых данных далеко не всегда достаточно, поэтому сообщите компании все нюансы и сравните ответы.</p>
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
    items = [f"В рейтинге **{len(CARDS)} компаний**; открытые цены публикуют **{len(priced)}**: {', '.join(priced)}."]
    if topic == "wine":
        n = [x for r in WINE_ROWS for x in _nums(r[1])]
        items.append(f"Цены на вино публикует **только 700ml**: от {fmt_rub(min(n))} до {fmt_rub(max(n))} ₽ за бутылку (Petrus, Château Lafite, Château Margaux, Masseto, Sassicaia; цены «от»).")
    elif topic == "elite":
        items.append("Для дорогих и редких бутылок профильны **Red Decanter** (до 5 000 000 ₽ в прайсе), 700ml (до 200 000 ₽, Petrus), SKUPKA-ALKOGOL (сегменты до «свыше 100 000 ₽»).")
    items.append("Типичный уровень выкупа — **67–72% рыночной цены** бутылки по опубликованным таблицам скупок; обещания «до 90%» и «до 100%» — **рекламные заявления**.")
    items.append(f"Заявленный срок оценки по фото: самый быстрый — **{quick['meta']['speed'].lower()}** ({quick['name']}), самый медленный — **{slow['meta']['speed'].lower()}** ({slow['name']}).")
    items.append(f"Высшая оценка редакции — **{scores(top)[1]:g} из 5** ({top['name']}); оценка считается по трём параметрам, правила — в методике.")
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
<meta name="theme-color" content="#d6361f">
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
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,800;0,900;1,700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}assets/style.css?v={ASSET_V}">
{jsonld(site_ld, org, page_ld, *(ld or []))}
{YM_SCRIPT.replace("__ID__", YM_ID) if YM_ID else ""}</head>
<body>
{YM_NOSCRIPT.replace("__ID__", YM_ID) if YM_ID else ""}"""


# Меню шапки: (подпись, ссылка). Ссылка на якорь главной начинается с «#», остальные — файлы в корне.
NAV = [
    ("Главная", ""),
    ("Скупка алкоголя", "#ranking"),
    ("Элитный алкоголь", "gde-prodat-elitnyy-alkogol.html"),
    ("Вино", "gde-prodat-elitnoe-vino.html"),
    ("Цены выкупа", "prices.html"),
    ("Методика", "metodika.html"),
    ("О рейтинге", "o-reitinge.html"),
    ("Контакты", "kontakty.html"),
]


def header_inline(depth=0, base=None):
    p = base if base else "../" * depth
    home = base if base else (p or "./")
    links = "\n".join(f'<a href="{home if h == "" else (home + h if h.startswith("#") else p + h)}">{e(l)}</a>' for l, h in NAV)
    return f"""<header class="header" id="header">
<div class="container header-inner">
<a href="{home}" class="nav-logo" aria-label="{SITE} — главная"><span>ГРАДУС<i>.</i></span><span class="nav-logo-sub">Рейтинг скупок алкоголя</span></a>
<span class="age-badge" title="Сайт для лиц старше 18 лет">18+</span>
<nav class="nav-links" id="navLinks" aria-label="Главная навигация">
{links}
</nav>
<div class="header-actions">
<a href="{home}#calc" class="btn btn-primary header-cta">Узнать стоимость <span class="arrow">→</span></a>
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
<p>Сайт содержит информацию об алкогольной продукции. Чрезмерное употребление алкоголя вредит вашему здоровью. Продажа алкоголя лицам младше 18 лет запрещена.</p>
<div class="age-actions"><button class="btn btn-primary" type="button" id="ageYes">Да, мне есть 18</button><button class="btn btn-outline" type="button" id="ageNo">Нет</button></div>
<p class="muted" id="ageMsg" role="status"></p>
</div>
</div>
"""


def footer_inline(depth=0, base=None):
    p = base if base else "../" * depth
    home = base if base else (p or "./")
    op = f"Оператор сайта: {ph('name', 'ФИО оператора')}{opt('inn', ', ИНН {}')}"
    return f"""<footer class="footer">
<div class="container">
<div class="footer-main">
<div>
<a href="{home}" class="nav-logo footer-brand" aria-label="{SITE} — главная"><span>ГРАДУС<i>.</i></span><span class="nav-logo-sub">Рейтинг скупок алкоголя</span></a>
<p class="footer-logo-copy">Где продать алкоголь в Москве и Московской области выгодно: рейтинг компаний, которые принимают коньяк, виски, вино, шампанское, ром, арманьяк, водку и другое спиртное, в том числе коллекционный и винтажный алкоголь СССР. Сравните условия: цену, сроки оценки, выезд, наличие бесплатных услуг и преимущества каждой компании в городах и областях России.</p>
</div>
<div><h3 class="footer-title">Разделы</h3><div class="footer-links">
<a href="{home}#ranking">Рейтинг скупок</a><a href="{p}{TOPICS[0]["file"]}">Элитный алкоголь</a><a href="{p}{TOPICS[1]["file"]}">Элитное вино</a><a href="{p}prices.html">Цены выкупа</a><a href="{home}#calc">Калькулятор</a><a href="{home}#faq">Вопросы</a></div></div>
<div><h3 class="footer-title">Информация</h3><div class="footer-links">
<a href="{p}metodika.html">Методика</a><a href="{p}o-reitinge.html">О рейтинге</a><a href="{p}dlya-kompanii.html">Для компаний</a><a href="{p}kontakty.html">Контакты</a><a href="{p}karta-sayta.html">Карта сайта</a></div></div>
<div><h3 class="footer-title">Документы</h3><div class="footer-links">
<a href="{p}redakcionnaya-politika.html">Редакционная политика</a><a href="{p}otkaz-ot-otvetstvennosti.html">Отказ от ответственности</a><a href="{p}pravila-polzovaniya.html">Правила пользования</a><a href="{p}politika-konfidencialnosti.html">Политика конфиденциальности</a><a href="{p}politika-cookie.html">Политика cookie</a></div>{footer_contacts()}</div>
</div>
<div class="legal">
<p><strong>18+</strong> Сайт содержит информацию об алкогольной продукции и предназначен для лиц старше 18 лет. Чрезмерное употребление алкоголя вредит вашему здоровью. Продажа алкоголя лицам младше 18 лет запрещена.</p>
<p>Сайт не оказывает и не продаёт услуги, не продаёт алкоголь и не принимает его от пользователей. Вся информация носит исключительно информационный характер, может быть устаревшей и не является публичной офертой. Цены и сроки — заявления компаний; точную информацию уточняйте на сайтах компаний. Рейтинг составлен по открытым данным из разных источников, порядок его составления описан в <a href="{p}metodika.html">методике</a> и <a href="{p}redakcionnaya-politika.html">редакционной политике</a>.</p>
<p>{op}.</p>
</div>
<div class="footer-bottom"><p>© 2026 {SITE}. Информация носит справочный характер.</p><p>Данные актуальны на {UPDATED}</p></div>
</div>
</footer>
{review_dialog(p)}
<div class="cookie-bar" id="cookieBar" role="dialog" aria-label="Согласие на использование cookie" hidden>
<p>Мы используем файлы cookie и сервис веб-аналитики «Яндекс Метрика», чтобы сайт работал корректно и становился удобнее. Продолжая пользоваться сайтом, вы соглашаетесь на их использование. <a href="{p}politika-cookie.html">Подробнее</a></p>
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
  "Что покупают скупки элитного алкоголя?",
  "Премиальные и коллекционные позиции: возрастной виски (Macallan, Yamazaki, Balvenie, Highland Park), коньяк (Hennessy XO/Paradis/Richard, Louis XIII, Martell Cordon Bleu), вина (Petrus, Lafite, Margaux, Masseto, Sassicaia), шампанское (Dom Pérignon, Cristal, Krug, Salon), ром и арманьяк, алкоголь СССР с коллекционной ценностью. Упаковка, тубус и декантер часто дают надбавку или покупаются отдельно. Профессиональный оценщик смотрит на бутылку как на предмет коллекционирования, а не как на обычный товар, поэтому для него важны подлинность и сохранность. Интересы у компаний разные, и полный перечень принимаемых позиций у каждой свой; конечно, окончательно его нужно уточнять напрямую."
 ],
 [
  "Что не берут?",
  "Открытые бутылки, повреждённую пробку и капсулу, подделки, массовый сегмент. Исключение — Cupaj Club и Alko Prikup: они заявляют, что рассматривают и бюджетные позиции. Перечень требований к бутылке у разных компаний отличается, поэтому в спорных случаях можно попробовать написать в несколько мест, а бутылки, которые представляют интерес, но вызывают сомнения, лучше показать эксперту."
 ],
 [
  "Какие бутылки считаются коллекционными?",
  "Коллекционными обычно называют бутылки с историей, ограниченным тиражом или именитым производителем, особенно если сохранилась идеальная упаковка. Среди коньяков и бренди это Hennessy, Rémy Martin, Martell, Courvoisier, Hine, Frapin и Camus (категории XO, XXO, Hors d'Age, Grande Champagne), а также Metaxa, Torres, Saint-Rémy, Veterano и Vecchia Romagna. Из виски — The Macallan, Glenfiddich, Glenmorangie, Yamazaki, Balvenie, Highland Park и Royal Salute. Французские вина: Domaine de la Romanée-Conti (Romanee-Conti), Domaine Leroy, Leflaive, Meo-Camuzet, Château Latour, Chateau Mouton Rothschild, Haut-Brion, Cheval Blanc, Lafleur, Le Pin, Lafite, Margaux, Petrus. Итальянские вина: Gaja, Ornellaia, Sassicaia, Masseto, Bruno Giacosa и Soldera; испанские — Vega Sicilia и Pingus; из Америки и Австралии — Harlan Estate, Screaming Eagle и Penfolds Grange. Шампанское: Dom Perignon, Cristal, Krug, Salon, Veuve Clicquot, Moet & Chandon. Названия часто пишут по-разному: Remy Martin и Rémy Martin, Saint-Remy и Saint-Rémy, Romanee Conti и Romanée-Conti, Case Basse (Casse Basse) у Soldera; уровень вина в хозяйстве, класс Grand Cru и дом (производитель) указаны на этикетке. Российские коллекционеры часто пишут названия по-русски: Шато Марго, Шато Мутон Ротшильд, Петрюс. В мире коллекционирования интересен и другой крепкий алкоголь: портвейн (Oporto), ром (Havana Club, Zacapa), кальвадос, ликёр, ракия, армянский коньяк из Армении, лимитированные серии водки (limited series: Absolut, Diva) и антикварное крепкое спиртное. Часто продают подаренный коньяк или виски и вещи с историей, оставшиеся от близких. Бренды названы как примеры из мира коллекционирования: готовность купить конкретную бутылку уточняйте у самой компании."
 ],
 [
  "Как формируется цена выкупа и почему скупки не называют сумму сразу?",
  "Ценообразование строится на мировых аукционных ценах и ценах импортёров, а не на розничной цене магазина, поэтому выкуп всегда дешевле покупки. Особенно заметно это у редких бутылок: цена зависит от производства и тиража, объёму бутылки и случая продажи, а небольшими партиями и целой коллекцией оценивают по-разному. Факторы, которые влияют на сумму: бренд и год изготовления, внешний вид и состояние этикетки, пробка и капсула, уровень жидкости, коробка и документы, регион, популярность бренда. Компании часто пишут «мы не занижаем цену» и «оценка моментальная» — это заявления: определить реальную сумму можно только по фото и после осмотра. Если цену называют сразу и без фото, это повод насторожиться. Подход к цене у разных компаний различается, ведь одна ориентируется на аукционы, другая на цены перекупщиков, поэтому запросите предложение минимум у двух. Если сложно оценить бутылку самостоятельно, поможет консультация специалиста: он проконсультирует, как определить ценность и почему она дешевле или выше ожиданий. Заказать оценку на нашем сайте нельзя: мы ничего не оцениваем и не покупаем."
 ],
 [
  "Почему цена меняется при встрече?",
  "Предварительная оценка по фото не учитывает состояние бутылки вживую. Компании, которые гарантируют неизменность цены, оговаривают «если нет новых обстоятельств». Прозрачной считается цена, в которой заранее названы условия: что осмотрят и от чего сумма может измениться. Если вы не уверены в условиях, строго фиксируйте их до выезда и сохраняйте переписку; если друзья уже продавали бутылки, спросите об их опыте; компания, которая давно работает на рынке, обычно говорит об этом сама."
 ],
 [
  "Как быстро оценивают бутылку?",
  "Заявленные сроки — от 2 до 15 минут, у Room Alco около 30 минут, у 700ml до 24 часов. Моментальная оценка возможна только предварительная: она производится по фото, а осмотр произведёт эксперт при встрече. Кратчайшие сроки итоговой оценки зависят от осмотра, а для людей, которым нужно срочно, важно сразу уточнить время. Скорость оценки не выделяет ни одного игрока: ориентируйтесь на условия и прозрачность цены."
 ],
 [
  "Можно ли продать бутылку без коробки или акцизной марки?",
  "Часто можно: например, 1buyup берёт бутылки без коробки и без акцизной марки, а также алкоголь СССР. Но без коробки цена может быть ниже до 30% (по данным Red Decanter), а бутылка в аккуратном состоянии и идеальной сохранности ценится выше. Особого значения для коллекционных бутылок акциз не имеет, но его отсутствие может косвенно влиять на цену. Поскольку упаковка требует бережного хранения, не выбрасывайте тубусы и сопроводительные документы. Для самих бутылок бытовой холодильник не подходит, а специальные винные холодильники и шкафы — подходят: хранение влияет на состояние."
 ],
 [
  "Как оформляется сделка и что происходит после заявки?",
  "Процесс обычно такой: вы отправляете заявку и фото (на электронную почту, в мессенджер Viber или Telegram либо через форму в интернете), обсуждаете цену, затем нужно организовать встречу или выезд оценщика, пообщавшись с представителями компании. Оформление занимает от одной встречи до нескольких дней, если бутылки едут из другого города. Для получения денег обычно необходимо подтвердить личность (уточните это у компании), а сама продажа возможна только людям, достигшими 18 лет. Нажимая «Оставить заявку» на сайте компании, вы даёте согласие на обработку персональных данных — проверьте её политику. Осмотрите бутылки перед передачей: содержимому и внешнему виду должно соответствовать то, что показано на фото. В случае пересылки транспортной компанией важны упаковка и страховка, а при выезде — безопасный способ расчёта: наличными или переводом. После согласования цены можно перейти к договору. Следующие шаги и вывоз коллекции согласуйте заранее: если бутылка уже оценивалась ранее, сообщите об этом, а из доступного способа расчёта выбирайте тот, что оставляет след. Если вы живёте в Самаре, Перми, Ростове, Краснодаре, Сочи или Уфе, вам обычно предлагают отправку: условия и права сторон проверяйте тщательно. Оплата обычно осуществляется после осмотра, а никаких предоплат вносить не нужно. Пересылку заявки можно вести по email."
 ]
]


PROMISES = [
    ("«Оценим по фото за 5 минут»", "Это предварительная оценка по фотографиям, а итоговую сумму называют после осмотра. Спросите, что именно может её изменить, и попросите зафиксировать цену в переписке."),
    ("«Выкупаем дорого и выгодно»", "Это не цена, а рекламная формула. Реальный уровень выкупа ниже рыночной цены (около 67–72%), поэтому сравните предложения нескольких компаний."),
    ("«Покупаем любой алкоголь»", "Обычно речь о коллекционных и премиальных бутылках. Водку и массовые марки скупки чаще не берут; исключения — редкая или советская водка и алкоголь СССР."),
    ("«Принимаем без коробки и акцизной марки»", "Часто это возможно, но без оригинальной упаковки цена бывает ниже до 30% (по данным одной из компаний). Подарочные коробки и тубусы лучше сохранить."),
    ("«Готовы приехать, выезд бесплатно»", "Уточните, когда приедет специалист, будет ли договор и как проходит расчёт. Для крупных партий выезд — стандартная практика, для одной бутылки он нужен не всегда."),
    ("«Предлагаем максимально высокую цену»", "Максимальной цены без сравнения не бывает. Спросите, на чём она основана (аукционные цены, цены импортёров), и сравните с предложениями других компаний."),
    ("«Пришлите фото — оценим стоимость»", "Обычная схема. Отправляйте только фотографии бутылки и не передавайте документы без необходимости: для предварительной оценки они не нужны."),
    ("«Оставьте заявку — перезвоним в течение 5 минут»", "Чаще всего это срок первого контакта, а не готовая оценка. Реальную скорость вы проверите сами, оставив заявку нескольким компаниям."),
    ("«Деньги сразу»", "Узнайте способ оплаты (наличными или переводом на карту) и момент выплаты: до осмотра или после него."),
    ("«Позвоните или свяжитесь любым удобным способом»", "Любой способ связи подходит, но договорённости об условиях и цене лучше вести там, где остаётся переписка: в Telegram, WhatsApp или по e-mail."),
    ("«Работаем по Москве, Московской области и России»", "Уточните, в каких городах реально есть выезд. При отправке бутылок по России транспортной компанией появляется риск боя: выясните, кто за него отвечает."),
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
<h2 class="calculator-title">Сколько стоит ваш алкоголь при выкупе?</h2>
<p class="calculator-copy">Хотите продать коньяк, виски, вино, шампанское, ром, арманьяк или другое спиртное и понять, какую сумму можно получить? Введите рыночную цену бутылки — аукционную или цену импортёра: так вы заранее увидите примерный выкуп и сможете сравнить его с предложением компании в день обращения. Скупки обычно платят 67–72% этой цены: такой уровень видно по опубликованным таблицам. Это быстрый ориентир, а не оценка конкретной бутылки: точную стоимость называет эксперт после фото и осмотра, и на неё влияют производитель, выдержка, год, состояние и упаковка.</p>
<form id="calcForm" class="form-grid">
<label class="full lbl">Рыночная цена бутылки, ₽<input class="field" id="market" type="number" min="1" step="100" inputmode="numeric" placeholder="например, 45000" required></label>
<button class="btn btn-primary calculator-submit full" type="submit">Узнать стоимость <span class="arrow">→</span></button>
</form>
</div>
<aside class="calculator-result" aria-live="polite">
<span class="result-label">Расчёт выкупа</span>
<div class="result-price" id="resultPrice">—</div>
<p class="result-note" id="resultNote">Введите цену и нажмите кнопку — получите предварительный диапазон.</p>
<div class="range"></div>
<span class="result-disclaimer">Диапазон является ориентиром, а не ценой сделки. Подлинность, этикетка, капсула, пробка, уровень жидкости, коробка и спрос меняют итоговую сумму.</span>
</aside>
</div>
<h3 class="sub">Как считается дисконт: опубликованные цены выкупа, виски</h3>
<div class="table-wrap"><table class="data">
<thead><tr><th>Позиция</th><th>Рынок</th><th>Готовы купить до</th><th>Дисконт</th></tr></thead>
<tbody>{disc_rows}</tbody></table></div>
<p class="note">Источник: открытые таблицы цен скупок (раздел «Виски»), цифры ориентировочные. Скупка платит не больше 67–72% рынка. Цены других компаний — на странице <a href="{p}prices.html" class="text-link">«Цены выкупа»</a>.</p>
</div>
</section>

<section class="section" id="choose">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Перед сделкой</span><h2 class="section-title">Пять вопросов<br>перед сделкой</h2></div>
<p class="section-copy">Скупка алкоголя устроена однотипно: заявка, фото, предварительная цена, встреча и расчёт. Различия скрыты в деталях, поэтому важно задать несколько вопросов до того, как отправить бутылки или вызвать выезд.</p>
</div>
<div class="steps-grid">
<article class="step"><div class="step-number">01</div><h3 class="step-title">Цена изменится?</h3><p>Главная причина недовольства клиентов — цена меняется при встрече. 1buyup, TotalStok, Kupimalko и VykupAlko прямо заявляют, что согласованная по фото сумма не изменится. Попросите подтвердить её до приезда специалиста любым удобным способом: в Telegram, по телефону или по e-mail.</p></article>
<article class="step"><div class="step-number">02</div><h3 class="step-title">«От» или «до»?</h3><p>700ml пишет «от» (нижняя граница), 1buyup — «до» (потолок). По Yamazaki 18 разброс достигает 2,5 раза. Напрямую такие цифры сравнивать нельзя: уточняйте, что именно компания готова заплатить, и помните, что цена выше или ниже в зависимости от состояния.</p></article>
<article class="step"><div class="step-number">03</div><h3 class="step-title">Есть ли цены на сайте?</h3><p>Конкретные цены публикуют четыре компании: 700ml, 1buyup, Red Decanter и SKUPKA-ALKOGOL. Остальные называют сумму только после заявки и фотографий бутылки, которые нужно отправить через форму на сайте или в мессенджер.</p></article>
<article class="step"><div class="step-number">04</div><h3 class="step-title">Кто на самом деле?</h3><p>Разных операторов меньше, чем сайтов: часть сайтов, вероятно, принадлежит одной компании (см. <a class="text-link" href="{p}metodika.html">методику</a>). Запрос в «разные» скупки одной группы часто даёт то же предложение.</p></article>
<article class="step"><div class="step-number">05</div><h3 class="step-title">Что с обещаниями?</h3><p>«До 90%» и «до 100%» рыночной цены — маркетинг: реальный дисконт около 28–33%. Очень высокие обещания всегда стоит проверить. Цифры «10+ лет», «5000 сделок» и «97% выкупа» — заявления самих компаний, их никто не проверял. Разбор типичных формулировок — ниже.</p></article>
</div>
<div class="prose checklist">
<p><strong>Как продать алкоголь выгодно и быстро.</strong> Не ограничивайтесь одним предложением: отправьте одинаковые фотографии в две-три компании любым удобным способом — через форму на сайте, в мессенджер или по телефону — и сравните не только цену, но и условия: время ответа, сроки выезда, способ оплаты, наличие договора. Обратите внимание на преимущества: выезд на адрес в Москве и Московской области, возможность продать большую коллекцию целиком, работа в других городах России. Смотрите и на то, как оперативно отвечает компания: ответ в течение нескольких минут — её заявление, а реальную скорость вы сможете проверить сами, когда решите оставить заявку. Онлайн-оценка по фото имеет смысл как первый шаг, но не заменяет осмотра. Важно: не соглашайтесь на предложение, если не объяснили, от чего зависит цена, и не отправляйте бутылки, пока сумма не подтверждена.</p>
</div>
</div>
</section>

<section class="section ranking-section" id="promises">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Как читать офферы</span><h2 class="section-title">Что обещают<br>скупки</h2></div>
<p class="section-copy">Почти на каждом сайте скупки встречаются одни и те же фразы. Вот что за ними обычно стоит и что стоит уточнить, прежде чем соглашаться.</p>
</div>
<div class="table-wrap"><table class="data">
<thead><tr><th>Что пишут скупки</th><th>Что это значит и что проверить</th></tr></thead>
<tbody>{prom_rows}</tbody></table></div>
<p class="note">Формулировки приведены как типичные для сайтов скупок. Наш сайт ничего не покупает и не оценивает бутылки: условия сделки вы согласуете с выбранной компанией.</p>
</div>
</section>

<section class="section ranking-section" id="quick">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Порядок действий</span><h2 class="section-title">Как продать<br>быстро</h2></div>
<p class="section-copy">Четыре шага от фотографий до расчёта. Любой выкуп оформляется между вами и выбранной компанией: сайт ничего не покупает.</p>
</div>
<div class="trust-grid">
<article class="trust-item"><div class="trust-symbol">1</div><h3 class="trust-title">Фото</h3><p>Сделайте фотографии бутылки: этикетки, пробки, упаковки и коробки, покажите уровень жидкости.</p></article>
<article class="trust-item"><div class="trust-symbol">2</div><h3 class="trust-title">Заявка</h3><p>Выберите компанию в рейтинге, оставьте заявку через форму на сайте или напишите в Telegram.</p></article>
<article class="trust-item"><div class="trust-symbol">3</div><h3 class="trust-title">Оценка</h3><p>Получите предварительную оценку онлайн. Стоимость влияет на состояние, выдержка, сохранность и редкость бутылки.</p></article>
<article class="trust-item"><div class="trust-symbol">4</div><h3 class="trust-title">Встреча</h3><p>После согласования условий сделки договоритесь о времени и месте встречи: многие компании делают выезд, а деньги выплачивают сразу.</p></article>
</div>
<p class="note">Важно: позвоните или свяжитесь по контактам из обзора, если хотите уточнить условия и сроки.</p>
</div>
</section>

<section class="section" id="prepare">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Фото для оценки</span><h2 class="section-title">Как подготовить<br>бутылку к оценке</h2></div>
<p class="section-copy">Чем точнее фотографии, тем быстрее придёт ответ и тем ближе предварительная цена к итоговой. Сделайте несколько снимков при дневном свете и отправьте их выбранной компании — на заявку через форму сайта или в мессенджер: можно написать в Telegram или WhatsApp.</p>
</div>
<div class="trust-grid">
<article class="trust-item"><div class="trust-symbol">1</div><h3 class="trust-title">Этикетки</h3><p>Сфотографируйте лицевую и обратную этикетки, чтобы эксперт увидел производителя, марку, год и состояние бумаги.</p></article>
<article class="trust-item"><div class="trust-symbol">2</div><h3 class="trust-title">Капсула и пробка</h3><p>Покажите горлышко, капсулу, пробку и акцизную марку: повреждения заметно снижают стоимость.</p></article>
<article class="trust-item"><div class="trust-symbol">3</div><h3 class="trust-title">Уровень и выдержка</h3><p>Снимите бутылку на просвет: для старых и винтажных бутылок уровень жидкости критичен, а выдержка и год влияют на ценность.</p></article>
<article class="trust-item"><div class="trust-symbol">4</div><h3 class="trust-title">Упаковка</h3><p>Коробка, тубус, наличие подарочной упаковки, декантер и документы повышают цену: без коробки до −30% (данные одной из компаний).</p></article>
</div>
<div class="prose checklist">
<p><strong>Онлайн-оценка.</strong> Многие компании заявляют бесплатную онлайн-оценку по фото; телефон, Telegram и другие контакты указаны в карточках компаний.</p>
<p><strong>В сообщении укажите:</strong> производителя, марку или релиз, год, объём, количество бутылок, город и удобный способ связи. Если у вас несколько бутылок или целая коллекция, сфотографируйте её общим планом и приложите список.</p>
<p><strong>Что влияет на оценку:</strong> состояние бутылки, сохранность этикетки и пробки, уровень жидкости, редкость релиза, наличие коробки и документов. Хранение тоже важно: бутылки лучше держать в тёмном прохладном месте, лёжа или стоя в зависимости от типа закупорки, и не открывать. Обычную водку и массовые марки скупки, как правило, не берут, а вот коллекционную водку, алкоголь СССР, арманьяк, ром и редкие виды алкоголя рассматривают.</p>
<p><strong>Для коллекционеров и наследников коллекций.</strong> Продать одну бутылку из коллекции просто, а для большой коллекции лучше подготовить список с фотографиями: онлайн-оценка такого списка занимает больше времени, зато позволяет предложить цену за всю партию. Винтажный алкоголь, редкие релизы и другие бутылки с историей имеет смысл показывать отдельно. Условия хранения и подтверждение происхождения повышают ценность. Помните: условия продажи спиртного действуют только для совершеннолетних.</p>
<p><strong>Чего не делать:</strong> не открывайте бутылку, не протирайте и не переклеивайте этикетки, не отрывайте акцизные марки. Сохраните коробки, тубусы, сертификаты и чеки: они подтверждают подлинность и происхождение.</p>
</div>
</div>
</section>

<section class="section ranking-section" id="method-link">
<div class="container">
<div class="section-top" style="margin-bottom:0">
<div><span class="eyebrow">Методика</span><h2 class="section-title">Как составлен<br>рейтинг</h2></div>
<div><p class="section-copy" style="margin-bottom:20px">Основные критерии, источники данных, правила расчёта оценки и условия, при которых рейтинг может быть неточным, — на отдельной странице.</p><a class="btn btn-primary" href="{p}metodika.html">Читать методику <span class="arrow">→</span></a></div>
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
<p class="final-copy">Напишите редакции: ответим на вопрос по рейтингу, проверим данные о компании или подскажем, как сделать фото бутылки для предварительной оценки. Консультация редакции бесплатна. Саму оценку и цену называет выбранная вами компания, обычно от нескольких минут до суток.</p>
<p class="final-note">Предварительная оценка не является окончательной ценой сделки.</p>
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
    free = ("<p>Размещение компаний в рейтинге бесплатно. Мы не получаем вознаграждения от компаний за место в списке, оценку или текст обзора.</p>"
            if PLACEMENT_IS_FREE else
            "<p>О финансовых и иных отношениях редакции с компаниями рейтинга — в <a class=\"text-link\" href=\"redakcionnaya-politika.html\">редакционной политике</a>.</p>")
    return f"""<section class="section" id="independence">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Независимость и размещение компаний</h2>
<p>Сайт не оказывает и не продаёт услуги, не продаёт алкоголь и не принимает его от пользователей. Рейтинг составляется по открытым данным из разных источников, а компании для сравнения отбирает редакция сайта.</p>
{free}
<p>Рейтинг не подтверждает, что у компаний есть разрешительные документы и что их деятельность соответствует законодательству; мы этого не проверяем. Рейтинг — отправная точка для поиска, а не замена проверки условий перед сделкой. Если вы представляете компанию и нашли неточность, напишите через <a class="text-link" href="dlya-kompanii.html">страницу для организаций</a>.</p>
</div>
</div>
</section>
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
{independence_section()}
{score_table()}
{summary_section()}
</main>
""" + footer()


def about_page():
    return head(f"О рейтинге скупок алкоголя — {SITE}",
                "О проекте: независимый рейтинг скупок элитного и коллекционного алкоголя в Москве. Сайт не оказывает и не продаёт услуги, информация носит справочный характер.",
                path="o-reitinge.html", ld=[{"@context": "https://schema.org", "@type": "AboutPage", "name": f"О рейтинге — {SITE}", "url": f"{SITE_URL}/o-reitinge.html", "inLanguage": "ru"}, breadcrumbs(("Главная", ""), ("О рейтинге", "o-reitinge.html")), expert_ld()]) + header() + f"""
<main id="top">
<section class="topic-hero">
<div class="container">
<span class="eyebrow">О рейтинге</span>
<h1 class="page-title">О рейтинге скупок алкоголя</h1>
<p class="lead">Независимый рейтинг компаний, которые покупают элитный и коллекционный алкоголь в Москве.</p>
</div>
</section>
{expert_block()}
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
<p class="hero-copy">Рейтинг 20 скупок коллекционного виски, коньяка, вина и шампанского: кто называет цену открыто, как быстро делает оценку по фото и на каких условиях приезжает на выкуп. Выберите компанию, исходя из своих интересов: скорости, цены или удобства.</p>
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
<section class="photo-band"><div class="container"><span class="eyebrow">Независимый рейтинг</span><p>Места не продаются: оценки считаются по открытой методике, а размещение в рейтинге бесплатное.</p></div></section>
<section class="section ranking-section" id="ranking">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Рейтинг</span><h2 class="section-title">Скупки алкоголя<br>в Москве</h2></div>
<p class="section-copy">Сравнение по скорости оценки, прозрачности цен и условиям сделки. Благодаря единым критериям вы сможете определить, к какой компании обратиться в вашем случае. Как составлен список — в <a class="text-link" href="metodika.html">методике</a>.</p>
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
{choice_section()}

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
    generic = ("67–72% от рыночной цены бутылки", "Компания цены не публикует; указан типичный уровень выкупа по открытым таблицам цен скупок. Цены меняются — уточняйте перед сделкой.")
    if topic == "wine":
        if col == 1:
            n = [x for r in WINE_ROWS for x in _nums(r[col])]
            return f"от {fmt_rub(min(n))} до {fmt_rub(max(n))} ₽", "По опубликованным позициям вина (цены «от»). Цены меняются — диапазон ориентировочный."
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
    if topic == "wine":
        if d == "700ml.ru":
            return "Petrus 2006 — от 200 000 ₽; Château Lafite 2008 — от 60 000 ₽; Sassicaia 2010 — от 25 000 ₽."
        return "Цены на вино не публикует — сумму называет после фото."
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
        ("Живые отзывы на Яндекс Картах / 2ГИС", "Почти ни у кого."),
        ("Открытый прайс", "700ml, 1buyup, Red Decanter, SKUPKA-ALKOGOL."),
        ("Честный дисконт", "Рынок и потолок рядом показывает одна компания: ≈28–33%."),
        ("Гарантия «цена по фото = цена на встрече»", "1buyup, VykupAlko, Kupimalko, TotalStok (заявления, не аудит)."),
        ("Вероятные группы сайтов", "700ml + Alko Lombard + oldcognac; Red Decanter + SKUPKA-ALKOGOL; Cupaj Club + Alko Prikup."),
        ("Diamant Alko / Room Alco", "Услуги шире рынка, но независимой репутации и прайса нет."),
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


def compare_section(rows, title="Сравнение<br>условий", copy="Режим работы (пн-вс означает без выходных), заявленная скорость предварительной оценки, публичность цен и специализация. Особенно полезно, когда нужно обсудить условия сразу с несколькими компаниями и выбрать подход под свой товар."):
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
         lead="Сравнение скупок, которые берут премиальный и коллекционный алкоголь: редкий виски, выдержанный коньяк, марочное вино и шампанское. Кто публикует цены на дорогостоящие позиции, как быстро оценивает по фото и на каких условиях приезжает. Ниже — что считается элитным, как определить ценность бутылки и на что обратить внимание при продаже."),
        dict(file="gde-prodat-elitnoe-vino.html", key="wine",
         nav="Вино",
         title=f"Где можно продать элитное вино в Москве? Рейтинг скупок — {SITE}",
         desc="Где продать элитное вино в Москве: рейтинг скупок Petrus, Lafite, Sassicaia, Masseto, Romanée-Conti. Цены выкупа, скорость оценки по фото, выезд, что влияет на стоимость бутылки.",
         h1="Где можно продать элитное вино?",
         eyebrow="Рейтинг · Petrus, Lafite, Sassicaia, Masseto",
         lead="Сравнение скупок, которые покупают коллекционное и марочное вино: бордо (Лафит, Мутон Ротшильд, Латур, Марго, Петрюс), бургундские вина (Romanée-Conti), супертосканские Sassicaia, Ornellaia и Masseto, испанские Vega Sicilia и Pingus. Показываем, у кого есть открытые цены, как быстро делают оценку по фото и на каких условиях забирают бутылки."),
]
TOPIC_BY_KEY = {tp["key"]: tp for tp in TOPICS}

WINE_WORDS = ("Petrus", "Château", "Masseto", "Sassicaia")
WINE_ROWS = [r for r in PRICES if r[0].startswith(WINE_WORDS)]


def wine_count(col):
    return sum(1 for r in WINE_ROWS if r[col] not in ("—", ""))


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
            "diamant-alko.ru": dict(nom="Остатки вина у ресторанов, баров и магазинов (от 10 бутылок)"),
            "700ml.ru": dict(nom="Единственный открытый прайс на вино: Petrus, Lafite, Margaux, Masseto, Sassicaia", price=f"{wine_count(1)} позиций", price_n="цены «от»"),
            "reddecanter.ru": dict(nom="Редкие бутылки, оценка сомелье (прайс на вино не публикует)", price="Не публикует", price_n="цены на вино"),
        }
        for c in CARDS:
            if c["domain"] not in over:
                over[c["domain"]] = dict(price="Не публикует", price_n="цены на вино")
    out = []
    for i, d in enumerate(order, 1):
        c = by[d]
        m = dict(c["meta"])
        m.update(over.get(d, {}))
        if key == "wine" and d in ("room-alco.ru", "diamant-alko.ru"):
            m["price"], m["price_n"] = "Не публикует", "цены на вино"
        out.append((c, m, i))
    return out


WINE_HOUSES = [
    ("Бордо (Bordeaux): Château Lafite Rothschild, Château Mouton Rothschild, Château Latour, Château Margaux, Haut-Brion", "Лафит Ротшильд, Мутон Ротшильд, Латур, Марго, О-Брион", "Первые гран крю по классификации 1855 года (Mouton Rothschild получил этот статус в 1973 году). Красные бордо на основе каберне и мерло десятилетиями считаются эталоном марочного вина. Цену задают удачный урожай и бутылки, которые хранились в одном погребе, а название шато (chateau) на этикетке — только начало разговора."),
    ("Château Pétrus (Петрюс), Помроль", "Petrus, Le Pin, вина Помроля", "Помроль не входил в классификацию 1855 года, но Петрюс стабильно называют одним из самых дорогих вин мира. В прайсе 700ml Petrus 2006 стоит от 200 000 ₽, это самая высокая цена на вино среди опубликованных."),
    ("Château Beychevelle и другие шато Сен-Жюльена", "Beychevelle (Бешвель), Léoville, Ducru-Beaucaillou", "Beychevelle относится к четвёртым гран крю. Такие вина более доступны, чем легенды Медока, и востребованы у тех, кто собирает погреб с разумным бюджетом, а не гонится за самыми громкими именами."),
    ("Бургундия (Bourgogne): Domaine de la Romanée-Conti (DRC), Domaine Leroy", "Romanée-Conti (Романе-Конти), La Tâche, красные из пино нуар, белые из шардоне (chardonnay)", "Крошечные тиражи с отдельных виноградников. Бургундские вина подделывают чаще других, поэтому провенанс (история владения бутылкой) и проверка подлинности значат здесь больше, чем год урожая."),
    ("Тоскана и Пьемонт: Sassicaia, Ornellaia, Masseto, Solaia, Luce, Barolo", "Сассикайя, Орнеллайя (Ornellaia, Ornelaia), Массето (Masseto), Солайя, Люче (Luce), Бароло", "Культовые «супертосканские» красные из Болгери (Bolgheri, категория Superiore — Болгери Супериоре), Монтальчино и Бароло из Пьемонта (неббиоло; ценят, например, Bruno Giacosa). Masseto делают из мерло, Sassicaia — из каберне. Кьянти (Chianti Classico) обычно дешевле. Среди сицилийских и тосканских имён ещё встречаются Planeta (Сицилия, Sicilia), Avignonesi, Antinori."),
    ("Испания: Vega Sicilia, Pingus, Contador, Rioja", "Вега Сисилия Unico (Vega Sicilia), Dominio de Pingus (Пингус), Contador (Контадор), L'Ermita (Эрмита), Marqués de Murrieta Castillo Ygay Gran Reserva Especial, Faustino I, Contino, Capellanía Blanco", "Риоха (Rioja) и Рибера-дель-Дуэро: на цену влияют возраст выдержки (Reserva, Gran Reserva) и оценки критиков. Херес (шерри) и мадеру — крепленое вино, которое десятилетиями остаётся в хорошем состоянии, — тоже принимают, но реже и дешевле."),
    ("США, Австралия, Новая Зеландия: Screaming Eagle, Penfolds Grange", "Screaming Eagle (долина Напа, Калифорния), Penfolds Grange, Hill of Grace, каберне, шардоне, рислинг (riesling)", "Культовые вина Нового Света: тиражи небольшие, цену задают оценки критиков и дефицит. На российском рынке американские и австралийские бутылки встречаются редко, поэтому ликвидность ниже, чем у бордо и тосканских супертосканцев."),
    ("Аргентина и Чили: Catena Zapata, Rutini, Cobos, Don Maximiano, Clos Apalta", "Мальбек (Malbec) Катена Запата (Zapata), Рутини, Кобос; Clos (Кло) Apalta (Апальта) от Alexandre de Lapostolle; Don Maximiano Founder's Reserve (Maximiano)", "Мальбек из Мендосы (Catena Zapata, Rutini, Cobos) и чилийские красные (Clos Apalta, Don Maximiano) относятся к самым ценным позициям Южной Америки. Покупают их скорее как раритеты, чем как ликвидный товар."),
    ("Грузия и Абхазия", "Киндзмараули, Хванчкара, Мукузани, Оцханури Сапере, Усахелоури, Твиши; «Лыхны», «Апсны», «Диоскурия»", "Грузинское вино советского розлива и новые выпуски. Значение имеют сохранность, целость пробки и подтверждённое происхождение; абхазские вина (Сухум, Эшера) покупают реже, и без экспертизы цену не назвать."),
]

WINE_FAQ = [
("Какое вино считают ценным?",
 "Ценным обычно называют вино, которое сочетает громкое имя, удачный год урожая и безупречное хранение: Château Lafite Rothschild, Mouton Rothschild, Latour, Margaux, Pétrus, Romanée-Conti, а из Италии и Испании — Sassicaia, Masseto, Ornellaia, Vega Sicilia, Pingus. Название на этикетке само по себе ничего не гарантирует. Две бутылки одного шато и одного года могут стоить по-разному: одна лежала в профессиональном погребе, а другая годами хранилась в тепле. Эксклюзивные винтажи и запечатанные бутылки в оригинальном деревянном ящике оцениваются выше."),
("Чем вино для продажи отличается от обычного?",
 "Для скупки важны не вкус и не ваши личные предпочтения, а ликвидность: насколько легко перепродать бутылку. Красные вина Бордо, Бургундии, Тосканы и Пьемонта (Бароло) покупают охотнее, чем кьянти или белое вино из малоизвестных хозяйств. Белое (шардоне, рислинг) и десертные вина ценятся, когда это марочные бутылки известных домов. Игристое, крепкое и крепленое (херес, мадера, портвейн) оценивают отдельно."),
("Что смотрят при оценке: уровень, пробку, этикетку?",
 "Эксперт сверяет год и производителя, осматривает пробку и капсулу, этикетку и контрэтикетку, а также уровень вина в горлышке (ullage). Чем выше уровень, тем лучше сохранность; очень низкий уровень и подтёки на пробке снижают цену или делают бутылку непригодной для продажи. Отдельно проверяют формат: магнум (1,5 л) и Jeroboam (3 л) встречаются реже и стоят иначе, чем обычные 0,75 л. Подробности — в разделе об оценке выше."),
("Как хранить вино перед продажей?",
 "Вину нужны темнота, постоянная температура (около 12–14 °C), умеренная влажность и отсутствие вибрации. Бытовой холодильник и кухонный шкаф для долгого хранения не подходят, особенно если бутылки стоят у плиты или на свету. Лучше всего — винный шкаф или погреб. Бутылки с пробкой хранят лёжа, чтобы пробка не пересыхала. Вина, которые в течение многих лет стояли в плохих условиях, теряют в цене даже при безупречной этикетке."),
("Что прислать для оценки и что оформить дополнительно?",
 "Нужны фото этикетки, контрэтикетки, пробки и капсулы, горлышка с уровнем вина, а при наличии — упаковки и документов (чеки, письмо от продавца, сертификаты хранения, паспорта партии). Укажите год, объём, количество бутылок и где они хранились. Не передавайте документы на личность и коды из СМС без необходимости. Заранее обсудите расчёт: наличные, банковский перевод, в том числе в валюте. Итоговая сумма называется только после осмотра, а мгновенная оценка по фото всегда предварительная."),
("Работают ли скупки в других городах?",
 "Многие компании заявляют выезд по Москве и области; из других городов, например Нижнего Новгорода, Воронежа, Ростова-на-Дону, Перми, Уфы, Ульяновска, Кемерова или Брянска, вопрос обычно решают отправкой транспортной компанией. Уточняйте, кто отвечает за доставку и страховку: вино при перевозке легко пострадает. График у компаний разный: у одних пн–пт, у других сб–вс по сокращённому расписанию. Это видно в карточках выше."),
]


def wine_guide():
    rows = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in WINE_HOUSES)
    return f"""<section class="section" id="guide">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">О вине</span><h2 class="section-title">Какое вино<br>считается ценным</h2></div>
<p class="section-copy">Коллекционные вина покупают в основном как раритеты и вложение: к ним относятся культовые красные Франции, Италии и Испании, а также избранные вина других стран. Ниже — регионы и имена, которые чаще всего интересны скупкам.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Регион и хозяйства</th><th>Вина</th><th>Чем интересно</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="prose" style="margin-top:28px">
<p><strong>Как читать этикетку.</strong> Château (шато) — винодельческое хозяйство, Domaine — бургундский аналог. Cuvée — купаж или отдельная партия вина; Reserva и Gran Reserva в Испании указывают на минимальную выдержку, Superiore в Италии — на более строгие требования к категории вина. Слова Grand Cru Classé, Premier Cru и Classe относятся к классификации виноградников и хозяйств. Контрэтикетка — задняя этикетка с данными импортёра и объёмом; она помогает проверить подлинность. Год урожая (vintage) на красных винах влияет на цену сильнее, чем на других напитках: разница между удачным и средним урожаем одного шато может быть многократной. Выбираете, что оставить, а что продать, — ориентируйтесь на производителя и год, а не на громкое название.</p>
<p><strong>Что продают вместе с вином.</strong> Вместе с вином предлагают коньяк (например, Frapin), виски, ликёр, джин (Gordon&#39;s), херес и мадеру, а иногда и редкий ром. Если у вас несколько позиций, перечислите их в одной заявке: стоимость партии зависит от состава, а общий выезд обходится компании дешевле, чем несколько отдельных.</p>
<p><strong>Почему многие бутылки не принимают.</strong> Скупки не берут вино с признаками порчи, открытые бутылки, бутылки с низким уровнем жидкости и вина с сомнительным провенансом. Поддельные Lafite, Pétrus, Romanée-Conti и другие дорогие бордо и бургундские вина встречаются на рынке, поэтому раритеты проверяют особенно тщательно. Даже если вы получили бутылку как подарок или по наследству, документы о происхождении повышают шансы на сделку.</p>
</div>
{expert_note()}
</div>
</section>
"""


def wine_assess():
    return """<section class="section ranking-section" id="assess">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Как оценивают вино</h2>
<p>Оценка вина — процесс, в котором участвуют знания о регионе, опыт и экспертиза: определить цену по названию невозможно. Рассмотрим, из чего складывается итоговая сумма.</p>
<p><strong>На что смотрит эксперт.</strong> Профессионал изучает производителя, год, объём и формат, затем состояние бутылки: этикетку, контрэтикетку, капсулу, пробку, дно, стекло. Особенно внимательно смотрят на уровень вина в горлышке (ullage): у вин с десятилетиями выдержки небольшое падение уровня нормально, а резкое снижение говорит о проблемах с пробкой и хранением. Проверяют признаки подделки: нетипичный шрифт, неровную печать, неправильный цвет стекла, несоответствие капсулы году. У самых известных вин (Lafite, Mouton, Pétrus, Romanée-Conti) риск подделки выше, поэтому экспертиза подлинности обязательна и проводится до расчёта.</p>
<p><strong>Из чего складывается ценность.</strong> Цена вина зависит от репутации хозяйства, года урожая, оценок критиков, редкости выпуска и состояния бутылки. Бордо первых гран крю, Romanée-Conti, Masseto, Sassicaia, Vega Sicilia и Pingus считаются ликвидными, поэтому находят покупателя быстрее, а малоизвестные вина могут лежать месяцами. Аукционные результаты помогают понять рынок, но не гарантируют суммы: в скупке бутылку выкупают дешевле, чем продают, ведь компания закладывает свою маржу. По опубликованным таблицам типичный выкуп составляет около 67–72% рыночной цены; обещания «до 90%» и «до 100%» — реклама.</p>
<p><strong>Как не потерять в цене.</strong> Если вы решили продавать, не откладывайте надолго: у вина есть возраст и свой срок, а при плохом хранении ценность снижается. Не открывайте бутылку, не трясите, не переносите в тепло. Оригинальный деревянный ящик (OWC), сертификаты и чеки заметно повышают цену, потому что подтверждают, что вино хранилось в нормальных условиях. Вина, срок хранения которых вышел за разумные пределы, оценивают дешевле, а испорченные не принимают вовсе. Не верьте обещанию «заберём любую бутылку»: компания обязана оценить состояние. Сравните две-три оценки, прежде чем соглашаться.</p>
<p><strong>Кто покупает.</strong> Покупателями становятся частные коллекционеры, рестораны и винные бутики, а также те, кто пополняет собственный погреб или собирает подарочные наборы. Одни интересуются только культовыми красными, другие готовы взять и бургундские белые, и десертные, и крепленые вина. Спрос меняется: сегодня популярны одни регионы, завтра другие. Поэтому цены в таблицах выше лишь ориентир.</p>
<p><strong>Практические советы.</strong> Заранее соберите данные о каждой бутылке: производитель, год, объём, состояние, где хранилась. Сфотографируйте лицевую и заднюю этикетки при хорошем освещении, горлышко и капсулу, чтобы эксперту было проще понять состояние. Для встречи выберите комфортные условия и не оставляйте бутылки без присмотра. Не торопитесь: если оценка кажется заниженной, обратитесь в другую компанию. Узнать нюансы можно по телефону или в мессенджере (Telegram, WhatsApp), а ответ придёт письмом или сообщением.</p>
<p><strong>Кому подойдёт.</strong> Продажа интересна тем, кто получил вино в подарок или в наследство, не планирует его пить и хочет освободить место, а также владельцам ресторанов и магазинов с невостребованными остатками. Если бутылок много, составьте список (производитель, год, объём, состояние) и отправьте одной заявкой: менеджер оценит партию быстрее. Сделки возможны только для совершеннолетних, а условия договора, форму расчёта и адрес встречи лучше фиксировать письменно.</p>
</div>
</div>
</section>
"""


def wine_more():
    return """<section class="section" id="regions">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Что ещё ценят в мире вина</h2>
<p><strong>Другие страны и стили.</strong> Помимо Франции, Италии и Испании скупки проявляют интерес к вину Австрии (рислинг и белое из Вахау), Португалии (портвейн, мадера) и австралийским вином: помимо Penfolds Grange, это Hill of Grace. Из Нового Света называют калифорнийские каберне долины Напа, аргентинское вино (Malbec из Мендосы) и чилийское вино (Don Maximiano, Clos Apalta). Белое вино и сухие красные берут охотнее десертных, но очень старые десертные вина, например выпущенные десятилетия назад сотерн, тоже находят покупателя. Крепкого алкоголя это не касается: виски и коньяк оценивают по другим правилам.</p>
<p><strong>Грузинское и абхазское вино.</strong> Грузинское вино советского розлива (Хванчкара, Киндзмараули, Мукузани, Оцханури Сапере, Усахелоури, Твиши) и абхазское вино («Лыхны», «Апсны», «Диоскурия», «Анакопия»; встречаются бутылки из Сухума и района Эшера) покупают, но с осторожностью. Вина «Апсха», «Киси» и «Чегем» в разных каталогах называют по-разному, поэтому вам понадобится фото этикетки, а не пересказ. Такие бутылки редко стоят много, и без экспертизы оценка не будет объективной.</p>
<p><strong>Форматы и упаковка.</strong> Магнум (1,5 л) и Jeroboam (3 л) выдерживаются дольше и ценятся коллекционерами; бутылка из деревянного ящика (OWC) стоит дороже одиночной. Полный набор бутылок одной вертикали (одно вино разных лет) или горизонтали (разные вина одного года) можно продать единым лотом: так выгоднее, чем отдельными бутылками, но потребуется перечень и фотографии.</p>
<p><strong>Как пишут названия.</strong> Одно и то же вино встречается в разных написаниях: Romanee-Conti и Romanée-Conti (в русских текстах «Романе-Конти»), Lafite-Rothschild и Château Lafite Rothschild, Haut-Brion и «О-Брион», Mouton Rothschild и «Мутон Ротшильд», Marques de Murrieta и Marqués de Murrieta, Masseto и Masetto, Ornellaia и Ornelaia, а Château Pétrus просто называют Petrus. Не путайте название с лёгкой опиской на фото: подделки часто выдаёт именно ошибка в написании. Поместите в заявку фотографию, а не только слова, и укажите оба варианта названия, если не уверены.</p>
<p><strong>Что можно приложить.</strong> Любые подтверждения происхождения: чеки, переписку с продавцом, паспорта партии, сертификаты хранения. Для итальянских вин (Tenuta San Guido, Tenuta dell'Ornellaia, Antinori) полезна контрэтикетка с данными импортёра, для испанских (Faustino, Marqués de Murrieta, Contino) — информация о выдержке (Reserva, Gran Reserva). Домены Бургундии (Domaine de la Romanée-Conti, Domaine Leroy, Domaine Faiveley) нередко подделывают, поэтому провенанс особенно важен.</p>
<p><strong>Что продают вместе с вином.</strong> Шампанское (Dom Pérignon, Moët), коньяк (Frapin), ликёр, джин, херес и другие напитки. Если вы собираете большой набор, укажите всё в одной заявке: компании делают единое предложение и назначают одну встречу.</p>
</div>
</div>
</section>
"""


def wine_deal():
    return """<section class="section ranking-section" id="deal">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Что учесть при сделке</h2>
<p>Порядок действий описан выше, в блоке «Как продать быстро». Для вина стоит добавить несколько деталей.</p>
<p><strong>Заявка и связь.</strong> Отправьте фото через форму на сайте, по email (часто это адрес вида info@...), в телеграм или WhatsApp. Режим работы у компаний отличается: у одних пн-пт, у других сб-вс по сокращённому графику, поэтому сроки ответа тоже разные. Мгновенная оценка по фото всегда ориентировочная; просите зафиксировать цену письменно.</p>
<p><strong>Встреча и осмотр.</strong> Специалист приезжает по адресу (улица и дом в Москве или области) либо вы встречаетесь в офисе. Эксперт проверяет состояние, сверяет год, осматривает пробку и уровень, при необходимости организует экспертизу подлинности. Если бутылка не соответствует описанию, цену пересмотрят: иногда это справедливо, иногда нет.</p>
<p><strong>Расчёт.</strong> Обычно наличные или банковский перевод; уточните, возможна ли выплата в валюте, и не отдавайте бутылки, пока сумма не получена. Условия лучше сохранить письменно.</p>
<p><strong>На что обращать внимание.</strong> Опытный специалист не торопит, объясняет, из чего складывается цена, и не пытается скрыть обмен или комиссию. Если вам обещают «максимум» без осмотра, это повод сомневаться. Обратите внимание на отзывы, на то, есть ли у компании адрес и контакты, а также на соблюдение требований закона. Не спешите: стоит получить ответы нескольких скупщиков и сравнить, прежде чем решать.</p>
<p><strong>Если вы за пределами Москвы.</strong> Компании, как правило, принимают заявки из других городов России. Уточняйте возможность выезда или отправки, например, в Нижний Новгород, Воронеж, Ростов, Пермь, Уфу, Ульяновск, Кемерово, Брянск. Условия логистики, страховки и оплаты везде свои.</p>
</div>
</div>
</section>
"""


def wine_faq():
    items = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in WINE_FAQ)
    return f"""<section class="section ranking-section" id="faq">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Вопросы</span><h2 class="section-title">Вопросы о продаже<br>вина</h2></div>
<p class="section-copy">Коротко о ценных бутылках, хранении, оценке и том, что прислать.</p>
</div>
<div class="faq">{items}</div>
</div>
</section>
"""


ELITE_CATS = [
    ("Виски", "The Macallan, Glenfiddich, Glenmorangie, Highland Park, Balvenie, Yamazaki, Johnnie Walker (Black Label, Blue Label)", "Шотландский виски перегоняют уже несколько столетий. Смотрят на винокурню, возраст, лимитированное издание и ограниченный тираж; повседневные версии вроде Red Label (красная этикетка) к элитным не относят."),
    ("Коньяк, арманьяк, кальвадос, бренди", "Hennessy, Rémy Martin, Martell, Courvoisier, Hine, Frapin, Camus, Metaxa", "Коньяк, арманьяк и кальвадос строго регламентированы: от сырья и урожая до выдержки. Коллекционные категории — XO, XXO, Hors d'Age, Grande Champagne; значение имеют год и состояние бутылки."),
    ("Вина Франции", "Бордо: Lafite Rothschild, Mouton Rothschild, Latour, Margaux, Haut-Brion, Cheval Blanc, Lafleur, Le Pin, Petrus. Бургундия: Domaine de la Romanée-Conti, Domaine Leroy, Leflaive, Meo-Camuzet", "Бордоское и бургундское вино оценивают по урожаю и классификации (Grand Cru, Premier Cru — в русской записи «гран крю» и «премьер крю»). Интересны и вина долины Роны (Кот-дю-Рон), и эльзасское."),
    ("Вина Италии, Испании, США, Австралии", "Gaja, Ornellaia, Sassicaia, Masseto, Bruno Giacosa, Soldera, Vega Sicilia, Pingus, Harlan Estate, Screaming Eagle, Penfolds Grange", "Итальянского вина ценят прежде всего из Тосканы, Пьемонта, Венето и Сицилии; испанского — Vega Sicilia и Pingus. Американское и австралийское вино часто попадает в коллекции из-за малых тиражей."),
    ("Шампанское", "Dom Pérignon, Cristal, Krug, Salon, Veuve Clicquot, Bollinger", "Ценятся миллезимные выпуски и большие форматы (магнум и крупнее). О винах подробнее — на странице «Где можно продать элитное вино»."),
    ("Ром, портвейн, херес, ликёры, абсент", "Havana Club, Zacapa, Caroni, Taylor's (Porto), херес, ликёры, абсент, ракия", "Берут их не все компании и только выборочно: важны возраст, редкость и сохранность. Если сомневаетесь, отправьте фото: ракию и другие региональные напитки оценивают отдельно."),
    ("Алкоголь СССР и старые бутылки", "Массандра (Крым), грузинское и крымское вино, коньяки и вина, выпущенные до 1990 года", "Красное и белое вино, коньяки, коллекционная водка и ликёры советского периода интересны, если сохранились этикетка, пробка и уровень. Открытые бутылки обычно не берут."),
]

ELITE_FAQ = [
("Чем элитный алкоголь отличается от обычного и как определить ценность бутылки?",
 "Элитным называют алкоголь, ценность которого определяют редкость, производитель, возраст и состояние: страна и место производства, винокурня или шато, урожай, выдержка, миллезим и ограниченный тираж. Бутылки повседневного потребления в эту категорию обычно не попадают, а шестизначным ценником отличаются позиции супер-премиум от 100 000 ₽. Чтобы определить ценность, найдите год, объём, серию и номер партии, осмотрите этикетку, пробку и уровень, а затем сравните цену с открытыми прайсами скупок и аукционов. Если вы не уверены, подойдёт консультация эксперта: сложно оценить без опыта даже известный бренд. Бутылку как инвестиционный актив рассматривают некоторые, но это рискованно и не является рекомендацией."),
("Можно ли продать подаренную или унаследованную бутылку, если я в этом не разбираюсь?",
 "Можно. Если вы непьющий и вам подарили бутылочку дорогого коньяка или виски, не спешите открывать: сделайте качественные фото этикеток, пробки и уровня, найдите коробку и документы и отправьте снимки в две-три компании. Знакомых и друзей, которые «в теме», тоже можно спросить о цене, но сравнивать лучше с профессиональной оценкой. Не стоит ждать, что за бутылку праздничного набора заплатят цену из магазина: выкупить её готовы дешевле, ведь компания закладывает свою выгоду. Особенно это заметно, если вы хотите продать бутылку, купленную на распродаже со скидкой: рыночная цена у такой бутылки может быть выше цены покупки."),
("Как не нарваться на подделку и некачественное хранение?",
 "Подделки встречаются у самых дорогостоящих позиций, и распознать поддельную бутылку по фото без опыта сложно. Тщательно осмотрите вживую этикетку и контрэтикетку, шрифты, печать, опознавательные знаки и значки на стекле, номера партии, пробку и капсулу, а затем сделайте фото при хорошем освещении на камеру телефона. Бутылка должна быть запечатанной, а укупорка целой: некачественное хранение (жара, свет, сквозняки) портит содержимое и снижает цену. Бытовой холодильник для долгого хранения не подходит, а постоянная температура и умеренная влажность — подходят. Если вам предлагают купить подозрительный экземпляр, проверьте его подлинность у эксперта: фэйк обнаружить проще до сделки."),
("Сколько стоит дорогая бутылка и почему цены в интернете так различаются?",
 "Ценообразование основывается на мировых аукционных ценах и ценах импортёров, а не на ценнике магазина, поэтому в интернете встречаются необоснованно завышенные предложения и демпинг. Разброс объясняют год, формат (магнум и литровые бутылки), состояние, упаковка, редкость и популярность выпуска. Не ориентируйтесь на один ценник и не верьте формулам «самая высокая цена»: сравните минимум два предложения, и не забывайте, что перекупщикам тоже нужна выгода. Если цена в разы выше рыночной, это повод насторожиться, как и цена, которая намного ниже рынка. Распродажу целой коллекции стоит обсуждать отдельно: условия для партии из десятков бутылок обычно другие."),
("Работают ли скупки с регионами, СНГ и Прибалтикой?",
 "Многие компании заявляют работу по России и СНГ, но реальные условия различаются. Если вы живёте в Екатеринбурге, Челябинске, Омске, Новосибирске, Воронеже, Ростове-на-Дону, Самаре, Перми, Уфе, Сочи, Владивостоке, Симферополе, Саранске или Брянске, вам обычно предложат отправку транспортной компанией или встречу в Москве. Для Казахстана, Армении, Украины, Белоруссии, а также Эстонии, Латвии и Литвы условия зависят от таможенных правил: уточняйте заранее и не отправляйте бутылку без договорённостей. Заранее выясните, кто отвечает за доставку, и упакуйте бутылки плотно, чтобы они не добирались до адреса разбитыми."),
("Как безопаснее договориться о цене и расчёте?",
 "Обсуждайте условия там, где остаётся переписка, и не соглашайтесь на предоплату. Компании часто пишут «договариваемся о цене по фото» и «расплатимся на месте»: это нормальная схема, но итоговую сумму подтверждайте письменно до встречи. Узнайте, как происходит расчёт, нужно ли будет оплатить какие-либо комиссии (обычно нет), и убедитесь, что обещана гарантированная цена, а не «примерная». На встречу берите оригинальную коробку и документы, внимательно осмотрите условия договора. Если вам подсказывают оформить сделку в стороннем сервисе, откажитесь. Рекомендуем не спешить: ответов от нескольких компаний обычно можно дождаться за день-два, и так риски минимальны."),
]


def elite_guide():
    rows = "".join(f"<tr><td><strong>{e(a)}</strong></td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in ELITE_CATS)
    return f"""<section class="section ranking-section" id="guide">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">О категории</span><h2 class="section-title">Что считается<br>элитным алкоголем</h2></div>
<p class="section-copy">Элитным называют алкоголь, чью ценность определяют не вкус одного вечера, а редкость, производитель, возраст и состояние бутылки. Ниже — основные категории и на что в каждой смотрят при оценке.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Категория</th><th>Примеры</th><th>Что учитывают</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="prose" style="margin-top:28px">
<p><strong>Почему одни бутылки дороже других.</strong> Страна и место производства, винокурня или хозяйство, урожай, выдержка, миллезим и ограниченный тираж превращают обычную бутылку в предмет коллекции. Многовековая традиция виноделия и винокурения объясняет, почему одни экземпляры стоят десятки тысяч евро, а другие остаются малоценными: даже современный интересный выпуск может быть неинтересным коллекционерам, если тираж огромен. Разумеется, цена зависит и от состояния, упаковки и подлинности, а не только от названия.</p>
<p><strong>На что обратить внимание при продаже.</strong> Если вы решили продавать, тщательно осмотрите бутылку: этикетку, пробку, уровень и упаковку, определите год и объём, соберите документы и чеки. Для получения точной оценки не нужно вскрывать бутылку и проводить дегустации: открытые бутылки обычно не берут. Обратитесь в несколько компаний, попробуйте сравнить условия и не забывайте, что цены на аукционе и в скупке различаются. Профессионально оценивают те, кто разбирается именно в вашей категории, поэтому искать стоит по профилю: виски, коньяк, вино или шампанское.</p>
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
<p><strong>Откуда берётся ценность.</strong> Современный рынок коллекционного алкоголя вырос из давних традиций. Шотландский виски создавали столетия назад, а за последние десятилетия он превратился из ремесла в мировой бизнес: существуют сотни винокурен, и каждая предлагает свой стиль. Коньяк производится в одноимённом регионе, и производство строго регламентировано правилами; для арманьяка и кальвадоса действуют похожие нормы. Для вина важны сорта, почва и погода года, и следствием становится огромное множество выпусков: от свежих лёгких белых вин до выдержанного красного бордо (например, Шато Мутон Ротшильд, Шато Марго, Шато Петрюс). Особый интерес у ценителей вызывают бутылки, о которых известно всё: производство, год, тираж и история владения.</p>
<p><strong>Регионы и стили.</strong> Среди итальянского вина коллекционеры выделяют тосканских и пьемонтских производителей, среди французского — бургундское, бордоское и вина долины Роны. Интересные позиции бывают и среди немецкого рислинга, и среди эльзасских сухих белых вин, хотя на рынке скупок их встречают реже. Новая мода на недооценённые регионы и возрождение забытых виноделен делают элегантные вина из менее известных районов заметными, но коллекционный рынок остаётся консервативным: чаще всего достаточно легендарного имени. Лимитированная версия, изданная ограниченным тиражом, как правило, ценится выше обычного выпуска.</p>
<p><strong>Как проходит продажа на практике.</strong> Практически любую сделку можно начать с дистанционной оценки по фото, но потом потребуется осмотр. Подготовьте перечень бутылок и снимите каждую так, чтобы контрэтикетка тоже была в кадре: гарантированным можно считать только то, что подтверждено документами. На встрече бутылки должен осмотреть оценщик, а вы можете сэкономить время, если всё подготовлено заранее. Не забывайте и о том, что происходит после сделки: сохраните договор или расписку. Если коньяк уже выкуплен у прежнего владельца, имеющийся комплект документов поможет подтвердить происхождение, а иностранное происхождение без сопроводительных документов может осложнить оценку. Общение с несколькими компаниями делает ситуации понятнее, а решение — комфортнее.</p>
<p><strong>Про цены в валюте.</strong> Результаты аукционов приводят в долларах, евро и фунтах, поэтому перед сравнением переведите их в рубли по курсу на дату продажи. Десятки тысяч долларов за редчайшую бутылку не редкость, но к ожиданиям от обычной скупки это отношения не имеет: подобные суммы бывают только у единичных позиций мира коллекционирования. Для собраний, которые собирают годами, учитывайте влияние факторов спроса: следующий год может изменить ситуацию.</p>
</div>
</div>
</section>
"""


def elite_more():
    return """<section class="section ranking-section" id="more">
<div class="container narrow">
<div class="prose">
<h2 class="sub" style="margin-top:0">Что ещё важно знать перед продажей</h2>
<p><strong>Коллекция, хобби и вложение.</strong> Для многих коллекционирование алкоголя — хобби и увлечение на всю жизнь, а часть людей рассматривает редкую бутылку как инвестиционный актив. Но при покупке и при продаже важно помнить: цену определяет спрос, а не возраст. Бутылка, которая десятилетиями стояла в серванте, может оказаться малоценной, а вещь, изготовленная ограниченным тиражом и выпущенная миллезимом, напротив, дорожает. Молодые винокурни вроде шотландской NC&#39;nean (виски Ainnir) интересны, но редкими их не назовут. Для пополнения собрания покупатель смотрит на редкость, сохранность и документы, а не на красивую открытку на этикетке.</p>
<p><strong>Что не относится к алкоголю.</strong> Скупка алкоголя не равна скупке антиквара. Самовары, граммофоны и патефоны, монеты, предметы искусства и поделки, мебель, электроника, медицинское и спортивное оборудование, транспорт, недвижимость и прочие товары в рейтинге не оцениваются. Если компания одновременно занимается антиквариатом и алкоголем, как Alcovikup и TotalStok, это скорее повод внимательнее проверить её специализацию.</p>
<p><strong>Какие вина встречаются реже.</strong> Помимо бордо и бургундского, скупки интересуются эльзасским и другим французским сухим вином, южноитальянскими и сицилийскими винами, австрийским рислингом, крымским и грузинским вином советского розлива. К малоценным относят массовое немецкое Liebfraumilch и большинство игристых без года. Недооценённые регионы появляются в разговорах всё чаще, но на рынке скупок спрос на них пока невысок. Подробнее о винах — на странице про <a class="text-link" href="gde-prodat-elitnoe-vino.html">элитное вино</a>.</p>
<p><strong>Если вы живёте не в Москве.</strong> Если бутылки находятся на побережье, в Крыму, Сочи, Ростове-на-Дону, Перми, Воронеже, Омске, Екатеринбурге, Челябинске или Владивостоке, вопрос чаще решают отправкой. При продаже за рубеж (в Казахстан, Армению, Белоруссию, на Украину, в Литву, Прибалтику, Великобританию) действуют ограничения на ввоз и вывоз алкоголя, а для бывших союзных республик условия различаются, поэтому уточняйте их заранее, в письменной форме. Если нужна встреча в Москве, договоритесь о времени и месте и не передавайте бутылки без подтверждения суммы.</p>
<p><strong>Когда продавать, а когда подождать.</strong> Рано или поздно продавать придётся всем, кто собирает алкоголь, но не стоит оставлять бутылки без присмотра на долгие месяцы: в серванте или в бытовом холодильнике вино и коньяк портятся, а вероятность испорченной бутылки растёт. Вещи, которые долго лежат мёртвым грузом, лучше оценить сразу. Не открывайте бутылки на вечеринки и торжества, если собираетесь продавать: цена увеличивается только у запечатанных экземпляров. Если закрывается ресторан или бар, остатки алкоголя продают одной партией.</p>
<p><strong>Как общаться с компанией.</strong> Пишите на электронную почту, в Telegram или WhatsApp, а ответ получите письмом или сообщением. Оценщики и сотрудники компаний должны отвечать на вопросы о цене и подлинности, не торопя вас. Любые демонстрационные фото из интернета не годятся: нужны снимки именно вашей бутылки. В заявке вы даёте согласие на обработку персональных данных компании, а не нашему сайту. Мировые аукционные цены служат ориентиром, но никогда не гарантируют итоговую сумму, поэтому записывайте условия и сохраняйте переписку.</p>
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
<p class="section-copy">Коротко о ценности, подделках, цене, регионах и безопасной сделке.</p>
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
    rows = "".join(f"<tr><td>{e(r[0])}</td><td>{e(r[1])}</td></tr>" for r in WINE_ROWS)
    return f"""<section class="section" id="topic">
<div class="container">
<div class="section-top">
<div><span class="eyebrow">Цены на вино</span><h2 class="section-title">Сколько платят<br>за вино</h2></div>
<p class="section-copy">Открытые цены на вино публикует только одна компания из 20: 700ml. У остальных сумму называют после того, как вы пришлёте фото.</p>
</div>
<div class="table-wrap"><table class="data"><thead><tr><th>Позиция</th><th>700ml (от)</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Заявленные компанией ориентиры, не оферта и не гарантия выплаты. Цены «от» — нижняя граница, ровно такую сумму получить можно не всегда.</p>
<h3 class="sub">От чего зависит цена вина</h3>
<div class="factors">
<article><h3>Хозяйство и вино</h3><p>Первые гран крю Бордо, Petrus, Romanée-Conti, Masseto, Sassicaia, Vega Sicilia и Pingus стоят заметно дороже вин малоизвестных винодельческих хозяйств. Репутация шато и оценки критиков определяют спрос.</p></article>
<article><h3>Год и формат</h3><p>Урожай влияет на цену сильнее, чем у других напитков: Petrus 2006 — от 200 000 ₽, Château Lafite 2008 — от 60 000 ₽, Château Margaux 2009 — от 50 000 ₽, Masseto 2015 — от 45 000 ₽, Sassicaia 2010 — от 25 000 ₽ (700ml). Магнум и Jeroboam оцениваются отдельно.</p></article>
<article><h3>Хранение и документы</h3><p>Уровень вина в горлышке, целая пробка и капсула, этикетка и контрэтикетка, оригинальный ящик и документы о происхождении (провенанс). Вино, которое хранилось в тепле или на свету, теряет цену.</p></article>
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
    return head(tp["title"], tp["desc"], path=tp["file"], ld=[breadcrumbs(("Главная", ""), (tp["h1"].rstrip("?"), tp["file"])), itemlist([c for c, m, i in rows])] + ([faq_ld(WINE_FAQ)] if tp['key'] == 'wine' else [faq_ld(ELITE_FAQ)])) + header() + f"""
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
<div><span class="eyebrow">Рейтинг</span><h2 class="section-title">{e('Скупки элитного вина' if tp['key']=='wine' else 'Скупки элитного алкоголя')}<br>в Москве</h2></div>
<p class="section-copy">{'Сравнение по открытым ценам на вино, скорости оценки и условиям сделки. Как составлен список — в <a class="text-link" href="metodika.html">методике</a>.' if tp['key']=='wine' else 'Сравнение скупок дорогих и редких бутылок по скорости оценки, ценам и условиям сделки. Как составлен список — в <a class="text-link" href="metodika.html">методике</a>.'}</p>
</div>
<div class="company-list" id="rankingTable">
{cards_html}
</div>
<p class="note">Сроки оценки и режимы работы — заявления компаний. «Не публикует» значит, что цен нет на проверенных страницах сайта. Порядок компаний на этой странице составлен по профильности для темы и полноте данных, а не по качеству услуг; подробнее — в методике.</p>
</div>
</section>

{compare_section([(c, m) for c, m, i in rows])}
{topic_extra(tp['key'], 0)}
{wine_guide() + wine_assess() + wine_more() + wine_deal() + wine_faq() if tp['key'] == 'wine' else elite_guide() + elite_notes() + elite_more() + elite_faq()}
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
<p>Сайт — информационный справочник со сравнением компаний, которые скупают алкоголь. Сайт не оказывает и не продаёт услуги и не предназначен для лиц младше 18 лет.</p>
<h2>2. Какие данные мы обрабатываем</h2>
<ul>
<li><strong>Технические данные:</strong> IP-адрес, тип браузера и устройства, адреса посещённых страниц, дата и время запроса. Они попадают в журналы сервера хостинга автоматически.</li>
<li><strong>Данные веб-аналитики:</strong> сервис «Яндекс Метрика» (ООО «ЯНДЕКС») собирает обезличенные сведения о посещении: просмотренные страницы, клики, прокрутку, движения мыши, источник перехода, тип устройства и браузера, примерный регион по IP-адресу. Работает функция «Вебвизор»: она записывает действия посетителя на странице, но не передаёт содержимое полей форм.</li>
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
<p>Мы не продаём персональные данные. Данные могут обрабатываться провайдером хостинга, на серверах которого размещён сайт. Данные веб-аналитики обрабатывает «Яндекс Метрика» по собственным правилам (<a class="text-link" href="https://yandex.ru/legal/confidential/" rel="noopener nofollow">политика конфиденциальности Яндекса</a>). Для отображения шрифтов браузер посетителя обращается к сервису Google Fonts, при этом сервису передаются IP-адрес и сведения о браузере. Оператор вправе раскрыть данные по обоснованному запросу уполномоченных органов.</p>
<h2>6. Хранение</h2>
<p>Данные хранятся не дольше, чем необходимо для целей обработки. Опубликованный отзыв остаётся на сайте, пока вы не попросите его удалить или изменить. Обращения организаций хранятся на время рассмотрения и ещё столько, сколько нужно для подтверждения принятых решений.</p>
<h2>7. Ваши права</h2>
<p>Вы можете запросить сведения о том, какие ваши данные мы обрабатываем, потребовать уточнить, заблокировать или удалить их, а также отозвать согласие. Для этого напишите на {ph('email', 'e-mail')}. Мы ответим в сроки, установленные законом. Вы также вправе обратиться в Роскомнадзор.</p>
<h2>8. Защита данных</h2>
<p>Мы принимаем организационные и технические меры для защиты данных от случайного или неправомерного доступа, изменения, раскрытия и уничтожения.</p>
<h2>9. Изменения политики</h2>
<p>Актуальная редакция всегда размещена на этой странице. Если мы начнём использовать новые инструменты, политика будет обновлена до их запуска. Отключить Метрику можно расширением браузера («Блокировщик Метрики» и аналогичные) или <a class="text-link" href="https://yandex.ru/support/metrica/general/opt-out.html" rel="noopener nofollow">по инструкции Яндекса</a>.</p>
<h2>10. Контакты</h2>
<p>{op}{opt('address', '<br>Адрес: {}')}<br>E-mail: {ph('email', 'e-mail')}</p>
"""
    return simple_page(f"Политика конфиденциальности — {SITE}", "Как сайт обрабатывает персональные данные посетителей: состав данных, цели, права пользователей и контакты оператора.",
                       "politika-konfidencialnosti.html", "Политика конфиденциальности", "Как мы обрабатываем персональные данные посетителей сайта.", body)


def cookie_page():
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
<h2>Что такое cookie</h2>
<p>Cookie — небольшие файлы, которые сайт сохраняет в вашем браузере. Они помогают запомнить ваши действия, например то, что вы уже ответили на вопрос о cookie.</p>
<h2>Какие cookie использует сайт</h2>
<div class="table-wrap"><table class="data"><thead><tr><th>Название</th><th>Назначение</th><th>Срок</th><th>Тип</th></tr></thead><tbody>
<tr><td>age_confirmed</td><td>Запоминает, что вы подтвердили возраст (18+), чтобы не показывать окно повторно. Дублируется в localStorage браузера.</td><td>12 месяцев</td><td>Необходимый, собственный</td></tr>
<tr><td>cookie_consent</td><td>Запоминает, что вы нажали «Согласен» в плашке о cookie, чтобы не показывать её повторно. Дублируется в localStorage браузера.</td><td>12 месяцев</td><td>Необходимый, собственный</td></tr>
<tr><td>_ym_uid, _ym_d, _ym_isad, _ym_visorc, _ym_metrika_enabled</td><td>Сервис «Яндекс Метрика»: отличает посетителей друг от друга, определяет число и длительность визитов, поддерживает работу «Вебвизора». Сведения обезличены.</td><td>до 12 месяцев</td><td>Аналитический, сторонний (Яндекс)</td></tr>
</tbody></table></div>
<p>Рекламные сети на сайте не подключены.</p>
<h2>Сторонние сервисы</h2>
<p>Для отображения шрифтов браузер обращается к сервису Google Fonts, а для статистики — к «Яндекс Метрике». Сам сервис Google Fonts не требует cookie, но получает ваш IP-адрес и сведения о браузере. Подробнее — в <a class="text-link" href="politika-konfidencialnosti.html">политике конфиденциальности</a>.</p>
<h2>Как управлять cookie</h2>
<p>Вы можете удалить cookie или запретить их сохранение в настройках браузера. Если удалить cookie_consent, плашка появится снова. Отключение необходимых cookie не влияет на работу сайта.</p>
<h2>Яндекс Метрика</h2>
<p>Сайт использует «Яндекс Метрику» (ООО «ЯНДЕКС») для статистики посещений: какие страницы читают, откуда приходят, как пользуются сайтом. Работает «Вебвизор», который воспроизводит действия посетителя на странице; содержимое полей форм он не записывает. Отказаться можно, отключив cookie в браузере, установив блокировщик Метрики или воспользовавшись <a class="text-link" href="https://yandex.ru/support/metrica/general/opt-out.html" rel="noopener nofollow">инструкцией Яндекса</a>.</p>
<h2>Контакты</h2>
<p>По вопросам об обработке данных: {ph('email', 'e-mail')}. Оператор: {ph('name', 'ФИО оператора')}.</p>
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
<p>Оператор сайта: {ph('name', 'ФИО оператора')}{opt('inn', '<br>ИНН: {}')}{opt('address', '<br>Адрес для обращений: {}')}<br>E-mail: {ph('email', 'e-mail')}{opt('phone', '<br>Телефон: {}')}{opt('telegram', '<br>Telegram: {}')}</p>
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
             f"- [{TOPICS[1]['h1'].rstrip('?')}]({SITE_URL}/{TOPICS[1]['file']}): цены на вино и компании, которые его покупают",
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
        money = "<p>Размещение компаний в рейтинге бесплатно. Редакция не получает вознаграждения от компаний за место в списке, оценку или текст обзора.</p>"
    else:
        money = f"<p>{ph('name', 'опишите, получает ли сайт вознаграждение от компаний; если да — размещение является рекламой и требует маркировки')}</p>"
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
{expert_block()}
<h2>1. Принципы</h2>
<ul>
<li>Компании сравниваются по одним и тем же открытым данным и одним правилам.</li>
<li>Факты и заявления компаний разделены: заявления («5000 сделок», «до 90% рынка») мы так и подписываем и не выдаём за проверенное.</li>
<li>О минусах пишем так же подробно, как о плюсах.</li>
<li>Мы не оцениваем качество услуг и не гарантируем результат сделки: оценка отражает прозрачность и открытость компании.</li>
</ul>
<h2>2. Источники данных</h2>
<p>Публичные сайты компаний. Если сайт был недоступен для автоматической проверки, использовались фрагменты поисковой выдачи, о чём сказано в карточке. Данные собраны 30 сентября 2026 г. Оценки и отзывы с сервисов карт в расчёте не используются.</p>
<h2>3. Как определяется оценка</h2>
<p>Оценка редакции считается по трём параметрам по правилам, опубликованным в <a class="text-link" href="metodika.html#score">методике</a>. Входные данные и результат по каждой компании открыты: <a class="text-link" href="data/companies.json">companies.json</a>.</p>
<h2>4. Как отбираются компании</h2>
<p>Компании для сравнения отбирает редакция сайта. Если вы представляете компанию и хотите предложить её для рассмотрения, воспользуйтесь <a class="text-link" href="dlya-kompanii.html">страницей для организаций</a>.</p>
<h2>5. Исправления и право ответа</h2>
<p>Если мы ошиблись, напишите нам через <a class="text-link" href="dlya-kompanii.html">страницу для организаций</a> или на {ph('email', 'e-mail')}. Мы проверим сведения в течение {CLAIM_DAYS} рабочих дней и исправим подтверждённые ошибки. Краткий ответ компании по её просьбе можно опубликовать в карточке.</p>
<h2>6. Независимость и конфликт интересов</h2>
{money}
<p>Если у редакции появятся отношения с оцениваемой компанией (владение, партнёрство, оплата), мы раскроем их на сайте до публикации.</p>
<h2>7. Обновление</h2>
<p>Данные могут устаревать. Дата сбора указана в методике; при существенных изменениях карточки обновляются.</p>
"""
    return simple_page(f"Редакционная политика — {SITE}", "Принципы составления рейтинга скупок алкоголя: источники данных, отбор компаний, исправление ошибок, независимость.",
                       "redakcionnaya-politika.html", "Редакционная политика", "Как мы составляем рейтинг и что делаем, если ошиблись.", body)


def disclaimer_page():
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
<h2>1. Информационный характер</h2>
<p>Вся информация на сайте «{SITE}» (рейтинг, обзоры, оценки, цены, сроки) носит исключительно информационный характер. Она не является публичной офертой, индивидуальной консультацией (юридической, финансовой или иной) или рекомендацией совершить сделку.</p>
<h2>2. Сайт не оказывает услуг</h2>
<p>Сайт не оказывает и не продаёт услуги, не продаёт алкоголь, не принимает бутылки и деньги и не является стороной сделок между пользователями и компаниями. За условия и результат таких сделок отвечают их участники.</p>
<h2>3. Актуальность и точность</h2>
<p>Информация собрана по открытым источникам на определённую дату и может быть устаревшей. Цены и сроки — заявления компаний; они могут меняться без уведомления. Мы стараемся поддерживать данные в актуальном состоянии, но не гарантируем их полноту и точность в каждый момент. Перед сделкой самостоятельно уточняйте условия на сайтах компаний.</p>
<h2>4. Оценка редакции</h2>
<p>Оценка рассчитывается по формальным признакам из открытых данных (прозрачность цен, скорость и удобство, открытость компании). Она не является оценкой качества услуг, надёжности или деловой репутации компании и не гарантирует результат сделки.</p>
<h2>5. Законность деятельности компаний</h2>
<p>Мы не проверяем наличие у компаний разрешительных документов, законность их деятельности и соблюдение ими требований законодательства, в том числе об обороте алкогольной продукции. Вы самостоятельно оцениваете риски и соблюдаете закон, включая возрастные ограничения.</p>
<h2>6. Внешние ссылки и контент третьих лиц</h2>
<p>Сайт содержит ссылки на сайты компаний. Мы не контролируем их содержание и не отвечаем за него. Отзывы и обращения пользователей выражают мнение их авторов.</p>
<h2>7. Возрастное ограничение</h2>
<p>Сайт содержит информацию об алкогольной продукции и предназначен для лиц старше 18 лет. Чрезмерное употребление алкоголя вредит вашему здоровью.</p>
<h2>8. Ограничение ответственности</h2>
<p>В пределах, допустимых законом, администрация сайта не отвечает за убытки, возникшие из-за использования опубликованной информации. Если вы нашли ошибку, сообщите нам через <a class="text-link" href="dlya-kompanii.html">страницу для организаций</a> или на {ph('email', 'e-mail')}.</p>
"""
    return simple_page(f"Отказ от ответственности — {SITE}", "Условия использования информации сайта: справочный характер, актуальность данных, оценка редакции, внешние ссылки.",
                       "otkaz-ot-otvetstvennosti.html", "Отказ от ответственности", "Что означает информация на сайте и за что мы не отвечаем.", body)


def terms_page():
    body = f"""
<p class="muted">Редакция от {POLICY_DATE}</p>
<h2>1. Общие положения</h2>
<p>Настоящие правила регулируют использование сайта «{SITE}» ({SITE_URL}), принадлежащего {ph('name', 'ФИО или наименование оператора')}. Продолжая пользоваться сайтом, вы соглашаетесь с правилами. Сайт является информационным ресурсом и не оказывает услуг. Подробнее — в <a class="text-link" href="otkaz-ot-otvetstvennosti.html">отказе от ответственности</a>.</p>
<h2>2. Возраст</h2>
<p>Сайт предназначен для лиц старше 18 лет. Если вам нет 18, пожалуйста, покиньте сайт.</p>
<h2>3. Использование материалов</h2>
<p>Материалы сайта можно цитировать с указанием источника и активной ссылкой на страницу. Копирование материалов целиком, а также использование их в коммерческих целях без согласия администрации не допускается.</p>
<h2>4. Отзывы и обращения</h2>
<ul>
<li>Пишите только то, что вы лично пережили или можете подтвердить.</li>
<li>Не размещайте оскорбления, угрозы, рекламу, персональные данные третьих лиц и сведения, порочащие честь и деловую репутацию без оснований.</li>
<li>Мы проверяем отзывы перед публикацией и вправе отклонить или удалить материал, нарушающий эти правила или закон.</li>
<li>Автор отзыва отвечает за его содержание. Отправляя отзыв, вы соглашаетесь на его публикацию.</li>
<li>Обработка персональных данных описана в <a class="text-link" href="politika-konfidencialnosti.html">политике конфиденциальности</a>.</li>
</ul>
<h2>5. Запрещённые действия</h2>
<p>Запрещено нарушать работу сайта, пытаться получить несанкционированный доступ и использовать сайт в противоправных целях. Индексация страниц поисковыми системами допускается.</p>
<h2>6. Изменения и применимое право</h2>
<p>Мы вправе изменять правила; актуальная редакция всегда размещена на этой странице. К отношениям применяется право Российской Федерации.</p>
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
        (ROOT / ".htaccess").write_text("# Шапка и подвал подключаются директивами SSI (<!--#include virtual=\"/includes/...\" -->)\nOptions +Includes\nAddType text/html .html\nAddOutputFilter INCLUDES .html\n", encoding="utf-8")
    else:
        (ROOT / ".htaccess").unlink(missing_ok=True)
    bots = "".join(f"User-agent: {b}\nAllow: /\n\n" for b in AI_BOTS)
    (ROOT / "robots.txt").write_text(f"# Поисковые и ИИ-краулеры допускаются явно; служебные папки закрыты для всех\n{bots}User-agent: *\nAllow: /\nDisallow: /standalone/\nDisallow: /tools/\nDisallow: /includes/\nDisallow: /send.php\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")


# Фото-полосы между текстовыми блоками: (файл страницы) -> [(id секции, перед которой вставить, картинка, подпись, текст, ссылка, текст кнопки)]
# Контрастные вставки-цитаты между блоками (без кнопок и перелинковки): (id секции, перед которой вставить, картинка-класс, подпись, текст, —, —)
BANDS = {
    "index.html": [
        ("calc", "banner2.jpg", "Прежде чем продавать", "Сравните не только цену, но и условия сделки: срок оценки, способ оплаты и выезд курьера.", "#choose", "Пять вопросов перед сделкой"),
        ("prepare", "banner3.jpg", "Подготовка", "Коробка, документы и сохранность этикетки заметно влияют на итоговую цену выкупа.", "#prepare", "Как подготовить бутылку"),
    ],
    "gde-prodat-elitnyy-alkogol.html": [
        ("topic", "banner2.jpg", "Редкие бутылки", "Для дорогих бутылок особенно важны подлинность, комплектность и условия хранения.", "#guide", "Что считается элитным"),
        ("faq", "banner3.jpg", "Перед сделкой", "Сфотографируйте этикетку, пробку и уровень жидкости: так оценка пройдёт быстрее.", "#prepare", "Как подготовить бутылку"),
    ],
    "gde-prodat-elitnoe-vino.html": [
        ("topic", "banner.jpg", "Вино", "Цена зависит от хозяйства, года урожая, формата и сохранности бутылки.", "#guide", "Какое вино ценится"),
        ("faq", "banner2.jpg", "Перед сделкой", "Условия хранения, целая пробка и оригинальный ящик помогают сохранить стоимость вина.", "#assess", "Как оценивают вино"),
    ],
}


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
    (ROOT / "index.html").write_text(add_bands(index_page(), "index.html"), encoding="utf-8")
    (ROOT / "prices.html").write_text(prices_page(), encoding="utf-8")
    (ROOT / "metodika.html").write_text(methodology_page(), encoding="utf-8")
    (ROOT / "o-reitinge.html").write_text(about_page(), encoding="utf-8")
    for tp in TOPICS:
        (ROOT / tp["file"]).write_text(add_bands(topic_page(tp), tp["file"]), encoding="utf-8")
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
