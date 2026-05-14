# Стирки ON

![stirki](./stirki_bot_logo.jpg)

Гиперлокальный сервис доставки стирки для Мытищ (Московская область). Клиент переходит по QR-коду с дома, устанавливает PWA, оформляет заказ — курьер забирает бельё, мы стираем и возвращаем.

---

## Быстрый старт

```bash
cp .env.example .env  # заполнить переменные

./run.sh local   # БД в Docker, backend и frontend с hot-reload
./run.sh dev     # весь стек в Docker (тестовая оплата)
./run.sh prod    # production
./run.sh stop    # остановить
```

Обязательные переменные: `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`, `SMSAERO_EMAIL`, `SMSAERO_API_KEY`.
Для оплаты: `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`.

---

## Документация

- [`CLAUDE.md`](CLAUDE.md) — полное техническое описание проекта (архитектура, тарифы, БД, инфра)
- [`deploy/README.md`](deploy/README.md) — деплой на VPS
- [`docs/TODO.md`](docs/TODO.md) — известные проблемы, требующие исправления
- [`docs/testing-guide.md`](docs/testing-guide.md) — сценарии ручного тестирования
- [`docs/qr-codes.md`](docs/qr-codes.md) — генерация QR-кодов для расклейки
