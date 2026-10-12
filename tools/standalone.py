#!/usr/bin/env python3
"""Делает из страницы самодостаточный HTML-файл: CSS, JS и картинки внутри.
Запуск: python3 tools/standalone.py index.html c/700ml-ru.html  ->  standalone/<имя>.html
Ссылки на другие страницы остаются относительными и из одного файла не откроются."""
import base64, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "standalone"
OUT.mkdir(exist_ok=True)


def inline(page: Path) -> str:
    html = page.read_text(encoding="utf-8")
    base = page.parent

    def css(m):
        return "<style>" + (base / m.group(1)).resolve().read_text(encoding="utf-8") + "</style>"

    def js(m):
        return "<script>" + (base / m.group(1)).resolve().read_text(encoding="utf-8") + "</script>"

    def img(m):
        f = (base / m.group(2)).resolve()
        if not f.exists():
            return m.group(0)
        mime = {"svg": "image/svg+xml", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[f.suffix[1:]]
        return f'{m.group(1)}src="data:{mime};base64,{base64.b64encode(f.read_bytes()).decode()}"'

    html = re.sub(r'<link rel="stylesheet" href="([^"]+\.css)">', css, html)
    html = re.sub(r'<script src="([^"]+\.js)"></script>', js, html)
    html = re.sub(r'(<img [^>]*?)src="((?:\.\./)?assets/[^"]+)"', img, html)
    return html


for arg in sys.argv[1:]:
    p = ROOT / arg
    (OUT / p.name).write_text(inline(p), encoding="utf-8")
    print("ok:", OUT / p.name)
