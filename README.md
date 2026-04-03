# Стирки ON

![stirki](./stirki_bot_logo.jpg)

Гиперлокальный сервис доставки стирки для Мытищ (Московская область). Клиент оформляет заказ через PWA-приложение, курьер забирает бельё, мы стираем/сушим/гладим и возвращаем.

---

## Концепция

Клиент переходит по ссылке из QR-кода (расклеенного на домах), устанавливает сайт как PWA-приложение и регистрируется по номеру телефона. Далее выбирает тариф и оформляет заказ.

### Два тарифа

| | Бесплатный | Платный |
|---|---|---|
| Стоимость | 0 ₽ | от 190 ₽ |
| Тип | только пакет | вещь или пакет |
| Позиции | 1 | до 3 |
| Допуслуги | недоступны | кондиционер, вакуум, глажка |
| Условие | просмотр 3 рекламных объявлений | оплата через YooKassa |

### Жизненный цикл заказа

```
WAITING_FOR_CAPTURE → NEW → COURIER_PICKUP → PICKED_UP →
WASHING → DRYING → IRONING → PACKING → COURIER_DELIVERY → DELIVERED
```

Каждый статус отражается карточкой на канбан-доске Kaiten и отображается клиенту в PWA.

---

## Запуск

```bash
# Локально (БД в Docker, backend и frontend с hot-reload)
./run.sh local

# Dev на сервере (весь стек в Docker, оплата в тестовом режиме)
./run.sh dev

# Production (весь стек в Docker, реальная оплата)
./run.sh prod

# Остановить всё
./run.sh stop
```

### Переменные окружения

Скопировать `.env.example` → `.env` и заполнить:

```bash
cp .env.example .env
```

Обязательные поля: `DB_USER`, `DB_PASSWORD`, `SECRET_KEY`, `SMSAERO_EMAIL`, `SMSAERO_API_KEY`.

Для оплаты: `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`.

Для Kaiten: `KAITEN_API_KEY`, `KAITEN_BASE_URL`.

---

## Архитектура

### Frontend (`frontend/`)

React 19 + TypeScript + Vite 6 + vite-plugin-pwa. Маршруты:

- `/` → `LandingPage` — лендинг, список заказов для авторизованного пользователя
- `/login` → `LoginPage` — вход по телефону + SMS-код
- `/order` → `OrderPage` — создание заказа (свайп-карточки)
- `/orders` → `OrdersPage` — история заказов

`OrderPage` использует свайп-интерфейс: `AddressCard` → `TariffCard` → `MachinesCard` (только бесплатный тариф) → `ServicesCard`.

### Backend (`src/`)

```
src/api/routers/     — FastAPI эндпоинты
src/schemas/         — Pydantic модели запросов/ответов
src/repositories/    — SQLAlchemy async запросы
src/models/          — ORM модели (Client, Order, Service, OrderStatusHistory)
src/services/        — бизнес-логика (pricing, auth, payment, kaiten, sms)
```

Ключевые эндпоинты:
- `GET /api/advertising` — список рекламных картинок из папки `advertising/`
- `POST /api/auth/request-code` — отправка SMS с кодом
- `POST /api/auth/verify` — верификация кода, выдача токена
- `GET /api/orders` — список заказов клиента
- `POST /api/orders` — создание заказа
- `POST /api/analytics/track-visit` — трекинг QR-переходов

### Инфраструктура

| Сервис | Описание | Порт |
|---|---|---|
| `postgres` | БД PostgreSQL 16 | 5432 |
| `backend` | FastAPI | 8000 |
| `frontend` | Vite build | — |
| `caddy` | Reverse proxy (HTTPS) | 80/443 |
| `adminer` | Веб-UI для БД | 8081 |
| `baserow` | No-code UI для менеджеров | 8082 |

### Реклама (`advertising/`)

Папка с рекламными изображениями (jpg/jpeg/png/webp). Backend отдаёт их через `/advertising/*` как статику. Caddy проксирует `/advertising/*` → backend. При выборе бесплатного тарифа клиенту показываются 3 случайных изображения по 5 секунд.

---

## База данных

Схема в `pg_init/01-schema.sql` — управляется вручную, не автогенерируется из ORM.

Таблицы: `clients`, `orders`, `order_statuses`, `order_status_history`, `services`, `landing_visits`, `promo_codes`, `promo_code_uses`.

---

## Мониторинг

- **Kaiten** — канбан-доска с карточками заказов, каждый статус = отдельная колонка
- **Baserow** — no-code таблицы для менеджеров (клиенты, заказы)
- **Adminer** — прямой доступ к БД

QR-аналитика: каждый переход по QR-ссылке (`/?ref=N`) записывается в `landing_visits` с привязкой к адресу дома.
