# Структура проекта Stirki ON

> Этот файл — быстрый справочник по файловой структуре. Обновляй при добавлении/удалении файлов.

## Дерево файлов

```
stirki/
├── CLAUDE.md                        # Инструкции для Claude Code
├── PROJECT_STRUCTURE.md             # Этот файл
├── README.md                        # Описание проекта на русском
├── compose.yml                      # Docker Compose (postgres, backend, frontend, caddy, adminer, baserow)
├── Caddyfile                        # Конфиг Caddy (reverse proxy)
├── Dockerfile.backend               # Docker-образ backend
├── pyproject.toml                   # Python-зависимости (uv)
├── uv.lock
├── main.py                          # Sandbox-скрипт для тестирования Kaiten API
├── run.sh                           # Скрипт запуска
│
├── frontend/                        # React PWA
│   ├── Dockerfile                   # Сборка frontend
│   ├── package.json                 # React 19, TypeScript 5.7, Vite 6, React Router 7, Vite PWA
│   ├── vite.config.ts               # Vite + PWA plugin конфиг
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx                 # Точка входа
│       ├── App.tsx                  # Router: / → LandingPage, /order → OrderPage, /orders → OrdersPage
│       ├── index.css
│       ├── api/
│       │   ├── client.ts            # HTTP-клиент, управление токеном и телефоном (localStorage)
│       │   └── index.ts             # API-функции: auth, orders, services, addresses, trackVisit, getAppStatus
│       ├── hooks/
│       │   └── useOrderFlow.ts      # Состояние многошагового флоу заказа
│       ├── pages/
│       │   ├── LandingPage.tsx      # Лендинг: описание сервиса, QR-трекинг, режим предзапуска
│       │   ├── OrderPage.tsx        # Форма создания заказа (многошаговый флоу)
│       │   └── OrdersPage.tsx       # Список заказов клиента
│       ├── types/
│       │   └── index.ts             # TypeScript-интерфейсы (Order, Service, Client...)
│       ├── utils/
│       │   └── statusNames.ts       # Утилиты (перевод статусов)
│       └── components/
│           ├── UserHeader.tsx       # Хедер с телефоном и кнопкой выхода (лендинг + OrderPage)
│           ├── ui/                  # Переиспользуемые компоненты
│           │   ├── Button.tsx
│           │   ├── Input.tsx
│           │   ├── ServiceCard.tsx
│           │   ├── StepIndicator.tsx
│           │   └── InfoModal.tsx
│           └── steps/               # Шаги формы заказа
│               ├── WelcomeStep.tsx
│               ├── PhoneStep.tsx
│               ├── CodeStep.tsx
│               ├── NameStep.tsx
│               ├── StreetStep.tsx
│               ├── HouseStep.tsx
│               ├── ApartmentStep.tsx
│               ├── BagsStep.tsx
│               ├── ServicesStep.tsx
│               ├── ConfirmStep.tsx
│               └── StatusStep.tsx
│
├── src/                             # FastAPI backend
│   ├── database.py                  # SQLAlchemy async engine + session factory
│   ├── settings.py                  # Pydantic Settings: DBSettings, AppSettings (APP_LAUNCHED), KaitenSettings, YookassaSettings
│   ├── enums.py                     # OrderStatusName, PaymentStatus, ServiceSlug, KaitenColumns/Tags
│   ├── addresses.py                 # STREETS, HOUSE_STREET_MAP, QR_CODE_MAP (числовой код → адрес-slug)
│   ├── messages_text.py             # Тексты для legacy Telegram-бота
│   │
│   ├── api/
│   │   ├── app.py                   # FastAPI app, CORS, подключение роутеров
│   │   ├── dependencies.py          # get_db(), get_current_client() (Bearer token auth)
│   │   └── routers/
│   │       ├── auth.py              # POST /auth/request-code, POST /auth/verify
│   │       ├── addresses.py         # GET /addresses
│   │       ├── services.py          # GET /services
│   │       ├── orders.py            # POST /orders, GET /orders, GET /orders/{id}
│   │       ├── payments.py          # POST /payments/webhook, POST /payments/test/simulate/{id}
│   │       └── analytics.py         # POST /analytics/track-visit (QR-трекинг лендинга)
│   │
│   ├── schemas/                     # Pydantic request/response модели
│   │   ├── auth.py                  # RequestCodeIn, VerifyCodeIn, AuthTokenOut, ClientOut
│   │   ├── address.py               # StreetOut, AddressesOut
│   │   ├── order.py                 # CreateOrderIn, OrderOut, OrderListOut
│   │   ├── service.py               # ServiceOut
│   │   └── payment.py               # PaymentOut, YooKassaWebhookIn
│   │
│   ├── models/                      # SQLAlchemy ORM модели
│   │   ├── base.py                  # DeclarativeBase
│   │   ├── client.py                # Client (phone, name, address, auth_token, verification_code)
│   │   ├── order.py                 # Order, OrderStatus, OrderStatusHistory
│   │   └── service.py               # Service (slug, name, price_rub, is_active)
│   │
│   ├── repositories/                # Data access layer (async SQLAlchemy)
│   │   ├── client.py                # ClientRepository: get_by_phone/token, create, verify_code, update
│   │   ├── order.py                 # OrderRepository: create, get_by_id/client_id, update_status/payment
│   │   └── service.py               # ServiceRepository: get_all_active, get_by_slugs, get_base_price
│   │
│   ├── services/                    # Бизнес-логика
│   │   ├── auth.py                  # generate_verification_code() → 4-значная строка
│   │   ├── pricing.py               # PricingService: цена = (база + услуги) × кол-во мешков
│   │   ├── payment.py               # PaymentService: создание платежа YooKassa
│   │   └── kaiten_kanban.py         # Kaiten: создание/перемещение карточек канбана
│   │
│   └── bot/                         # Legacy Telegram-бот (python-telegram-bot)
│       ├── main.py
│       ├── states.py                # FSM-состояния ConversationHandler
│       ├── settings.py              # TgSettings (токен бота, payment provider)
│       └── handlers/
│
├── pg_init/
│   └── 01-schema.sql                # DDL схемы + seed-данные (статусы, услуги)
│
├── deploy/
│   └── README.md                    # Инструкции по деплою
│
├── description/                     # Проектная документация
│   ├── функционал.md
│   ├── tables.txt
│   └── ...
│
└── prompts/                         # Сохранённые промпты
    ├── deploy.txt
    ├── first_result.txt
    └── order_history.txt
```

## Ключевые зависимости между файлами

```
routers/*.py
  → schemas/*.py        (валидация запросов/ответов)
  → dependencies.py     (get_db, get_current_client)
  → repositories/*.py   (запросы к БД)
  → services/*.py       (бизнес-логика)

repositories/order.py
  → services/kaiten_kanban.py   (автоматически при смене статуса)

routers/orders.py
  → services/pricing.py         (расчёт стоимости)
  → services/payment.py         (создание платежа)

routers/payments.py
  → repositories/order.py       (обновление статуса по вебхуку)
```

## База данных (pg_init/01-schema.sql)

| Таблица               | Назначение                                    |
|-----------------------|-----------------------------------------------|
| `clients`             | Клиенты (телефон, имя, адрес, токен)          |
| `order_statuses`      | Справочник статусов (11 записей)              |
| `services`            | Услуги с ценами (8 записей)                   |
| `orders`              | Заказы (связь с клиентом, статусом, услугами) |
| `order_status_history`| Аудит смены статусов заказа                   |
| `promo_codes`         | Промокоды (задел, в API не используются)      |
| `promo_code_uses`     | Использование промокодов                      |
| `landing_visits`      | Визиты на лендинг по QR-кодам (ref_code, visited_at) |

## Цены услуг (seed-данные)

| Slug             | Название              | Цена    |
|------------------|-----------------------|---------|
| *(базовая)*      | Стирка + сушка        | 890 ₽   |
| ironing          | Глажка                | 990 ₽   |
| conditioner      | Кондиционер           | 50 ₽    |
| vacuum_pack      | Вакуумная упаковка    | 150 ₽   |
| stain_remover    | Пятновыводитель       | 100 ₽   |
| wash_bag         | Мешок для стирки      | 30 ₽    |
| bleach           | Отбеливатель          | 50 ₽    |
| color_catcher_sheets | Салфетки цветозащита | 30 ₽ |

Формула: `(890 + сумма_выбранных_услуг) × количество_мешков`

## Флоу заказа (Frontend шаги)

**Лендинг** (`/`): описание сервиса → кнопки в зависимости от состояния сессии и `APP_LAUNCHED`

**Новый клиент** (`/order`): welcome → phone → code → name → street → house → apartment → bags → services → confirm → [payment] → status

**Вернувшийся клиент** (`/order`): welcome → phone → code → bags → services → confirm → [payment] → status

## Статусы заказа

```
WAITING_FOR_CAPTURE → NEW → COURIER_PICKUP → PICKED_UP →
WASHING → DRYING → IRONING → PACKING → COURIER_DELIVERY → DELIVERED
                                                         ↘ CANCELED
```

## Окружения

| Параметр         | dev                     | prod                    |
|------------------|-------------------------|-------------------------|
| `APP_ENV`        | любое, кроме production | production              |
| `APP_LAUNCHED`   | false (предзапуск)      | true (рабочий режим)    |
| Оплата           | Авто-успех              | YooKassa redirect       |
| Вебхук оплаты    | `/payments/test/simulate/{id}` | `/payments/webhook` |
| Caddy            | не запускается          | 80/443                  |
