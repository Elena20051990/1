#!/usr/bin/env python3
"""Пересчёт оценок только из фактов карточек (data/companies.json). Без ручных поправок баллов.
Три критерия, шкала 1-5, итог = среднее трёх."""
import json, sys
SRC = sys.argv[1]
d = json.load(open(SRC, encoding="utf-8"))["companies"]

# Факты, вынесенные из карточек вручную (поле -> значение): число опубликованных цен, срок оценки (мин, верхняя граница), график.
# speed: None = срок не указан; hours: None = график не указан, "ext" = круглосуточно или >=12 ч каждый день.
F = {
 "Diamant Alko":      dict(prices=0,  speed=10,   hours=None),
 "Room Alco":         dict(prices=0,  speed=30,   hours="ext"),
 "700ml":             dict(prices=21, speed=1440, hours="ext"),
 "1buyup":            dict(prices=6,  speed=30,   hours="ext"),
 "Red Decanter":      dict(prices=10, speed=15,   hours="set"),
 "SKUPKA-ALKOGOL":    dict(prices=6,  speed=15,   hours="set"),
 "VykupAlko":         dict(prices=0,  speed=15,   hours="set"),
 "Alko Prikup":       dict(prices=0,  speed=3,    hours="set"),
 "SellMeWine":        dict(prices=0,  speed=15,   hours="ext"),
 "Skup-ka":           dict(prices=0,  speed=None, hours="set"),
 "Kupimalko":         dict(prices=0,  speed=5,    hours="ext"),
 "Cupaj Club":        dict(prices=0,  speed=5,    hours="set"),
 "ProbkaBar (Skupka Premium)": dict(prices=0, speed=15, hours=None),
 "Alco-Skupka":       dict(prices=0,  speed=15,   hours="ext"),
 "AlcoBuyer":         dict(prices=0,  speed=None, hours="ext"),
 "oldcognac.ru («СкупкаАлкоголя»)": dict(prices=0, speed=None, hours=None),
 "Alcovikup":         dict(prices=0,  speed=5,    hours="set"),
 "TotalStok":         dict(prices=0,  speed=None, hours="ext"),
 "Alko Lombard":      dict(prices=0,  speed=None, hours="ext"),
 "Vine&Co":           dict(prices=0,  speed=5,    hours=None),
}

def price_score(n):          # прозрачность цен
    return 5 if n >= 20 else 4 if n >= 6 else 1
def speed_score(f):          # скорость и удобство: 1 + баллы (срок указан, срок <=15 мин, график указан, широкий график)
    p = (f["speed"] is not None) + (f["speed"] is not None and f["speed"] <= 15) \
        + (f["hours"] is not None) + (f["hours"] == "ext")
    return 1 + p
def open_score(c, f):        # открытость: адрес, график, e-mail, нет признаков общей сети с другими сайтами
    p = bool(c.get("address")) + (f["hours"] is not None) + bool(c.get("email")) + (not c.get("possible_same_operator"))
    return 1 + p

rows = []
for c in d:
    f = F[c["name"]]
    a, b, o = price_score(f["prices"]), speed_score(f), open_score(c, f)
    rows.append((round((a + b + o) / 3, 1), c["name"], a, b, o, c["editorial_score"]["total"]))
rows.sort(key=lambda r: (-r[0], -r[2], r[1]))
print("| Новое место | Компания | Цены | Скорость и удобство | Открытость | Итог | Было (старая оценка) |")
print("|---|---|---|---|---|---|---|")
for i, r in enumerate(rows, 1):
    print(f"| {i} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | **{r[0]}** | {r[5]} |")
