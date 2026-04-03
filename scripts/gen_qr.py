"""Генерация QR-кодов для рекламных объявлений Stirki ON.

Использование:
    uv run scripts/gen_qr.py                                  # localhost
    uv run scripts/gen_qr.py --base-url http://95.181.X.X    # VPS
    uv run scripts/gen_qr.py --base-url https://stirki-on.ru # прод
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Добавляем корень проекта в путь, чтобы импортировать src.addresses
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.addresses import HOUSE_STREET_MAP, QR_CODE_MAP, STREETS_SLUG

try:
    import qrcode
    from qrcode.image.pil import PilImage
except ImportError:
    print("Ошибка: установите зависимость: uv sync --dev")
    sys.exit(1)


_TRANSLIT: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _house_to_slug(house: str) -> str:
    """Преобразует номер дома в slug: пробелы → «-», кириллица → латиница."""
    result = house.replace(" ", "-").lower()
    return "".join(_TRANSLIT.get(ch, ch) for ch in result)


def build_slug_to_label() -> dict[str, str]:
    """Строим обратный словарь slug → читаемый адрес."""
    result: dict[str, str] = {}
    for street, houses in HOUSE_STREET_MAP.items():
        slug = STREETS_SLUG[street]
        for house in houses:
            house_slug = _house_to_slug(house)
            result[f"{slug}-{house_slug}"] = f"{street}, {house}"
    return result


def generate_qr_codes(base_url: str, output_dir: Path) -> list[dict]:
    """Генерирует PNG-файлы QR-кодов и возвращает метаданные."""
    output_dir.mkdir(parents=True, exist_ok=True)
    slug_to_label = build_slug_to_label()
    results = []

    for code, slug in QR_CODE_MAP.items():
        url = f"{base_url}/?ref={code}"
        label = slug_to_label.get(slug, slug)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img: PilImage = qr.make_image(fill_color="black", back_color="white")
        png_path = output_dir / f"{code}.png"
        img.save(str(png_path))

        print(f"  [{code}] {label} → {png_path}")
        results.append({"code": code, "slug": slug, "label": label, "url": url})

    return results


def generate_html(results: list[dict], base_url: str, output_dir: Path) -> None:
    """Генерирует index.html для просмотра всех QR-кодов в браузере."""
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    cards = ""
    for r in results:
        cards += f"""
        <div class="card">
            <img src="{r['code']}.png" alt="QR {r['code']}">
            <div class="label">{r['label']}</div>
            <div class="url">{r['url']}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QR-коды Stirki ON</title>
<style>
  body {{ font-family: sans-serif; padding: 24px; background: #f5f5f5; }}
  h1 {{ margin-bottom: 4px; }}
  .meta {{ color: #888; font-size: 14px; margin-bottom: 24px; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }}
  .card {{ background: white; border-radius: 8px; padding: 16px; text-align: center;
           box-shadow: 0 1px 4px rgba(0,0,0,.12); }}
  .card img {{ width: 100%; max-width: 200px; }}
  .label {{ font-weight: 600; margin-top: 8px; }}
  .url {{ font-size: 11px; color: #888; word-break: break-all; margin-top: 4px; }}
  @media print {{
    .meta {{ display: none; }}
    .grid {{ gap: 12px; }}
  }}
</style>
</head>
<body>
<h1>QR-коды Stirki ON</h1>
<div class="meta">base-url: {base_url} &nbsp;|&nbsp; сгенерировано: {now} &nbsp;|&nbsp; кодов: {len(results)}</div>
<div class="grid">{cards}
</div>
</body>
</html>
"""
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Генерация QR-кодов для объявлений Stirki ON")
    parser.add_argument(
        "--base-url",
        default="http://localhost:5173",
        help="Базовый URL сервиса (по умолчанию: http://localhost:5173)",
    )
    parser.add_argument(
        "--output-dir",
        default="qr_codes",
        help="Директория для сохранения файлов (по умолчанию: qr_codes/)",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    output_dir = Path(args.output_dir)

    print(f"Генерирую QR-коды для {base_url}")
    results = generate_qr_codes(base_url, output_dir)
    generate_html(results, base_url, output_dir)
    print(f"Готово: {len(results)} файлов + {output_dir}/index.html")


if __name__ == "__main__":
    main()
