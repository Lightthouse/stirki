# QR-коды для рекламных объявлений

Скрипт `scripts/gen_qr.py` генерирует PNG-файлы QR-кодов и HTML-превью для проверки и печати.

## Быстрый старт

```bash
# Установить dev-зависимости (одноразово)
uv sync --dev

# Сгенерировать QR-коды (localhost по умолчанию)
uv run scripts/gen_qr.py
```

Результат — директория `qr_codes/` с PNG-файлами и `index.html`.

## Варианты запуска

```bash
# Локальная разработка
uv run scripts/gen_qr.py

# VPS (подставить реальный IP)
uv run scripts/gen_qr.py --base-url http://95.181.XXX.XXX

# Продакшн домен
uv run scripts/gen_qr.py --base-url https://stirki-on.ru

# Другая директория для файлов
uv run scripts/gen_qr.py --output-dir /tmp/qr
```

## Проверка

1. Запустить скрипт → появляется `qr_codes/` с PNG + `index.html`
2. Открыть `qr_codes/index.html` в браузере → все QR-коды с подписями
3. Отсканировать QR-код телефоном → переход на `/?ref=<код>`
4. Аналитика визитов пишется в таблицу `landing_visits` через `POST /api/analytics/track-visit`

## Добавление нового адреса

1. Добавить дом в `HOUSE_STREET_MAP` в `src/addresses.py`
2. Добавить запись в `QR_CODE_MAP` (выбрать уникальный код от 1 до 1000)
3. Перегенерировать QR-коды

## Структура файлов

```
qr_codes/
├── 142.png       # Рождественская, 11
├── 287.png       # Рождественская, 9
├── ...
└── index.html    # HTML-превью для печати
```

> `qr_codes/` добавлена в `.gitignore` — файлы не попадают в репозиторий.
