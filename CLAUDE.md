# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stirki ON — гиперлокальный сервис доставки стирки для Мытищ (Московская область). Клиент оформляет заказ через PWA (React), курьер забирает бельё, мы стираем/сушим/гладим и возвращаем.

**Язык проекта — русский**: весь пользовательский текст, коммиты и документация на русском.

## Commands

```bash
# Локально: БД в Docker, backend и frontend с hot-reload
./run.sh local

# Dev на сервере: весь стек в Docker
./run.sh dev

# Production
./run.sh prod

# Остановить
./run.sh stop

# Линтер
uv run ruff check src/
uv run ruff format src/
```

## Architecture

### Frontend (`frontend/`)

React 19 + TypeScript 5.7 + Vite 6 + vite-plugin-pwa.

Маршруты:
- `/` → `LandingPage` — лендинг; для авторизованного — профиль и список заказов
- `/login` → `LoginPage` — вход по телефону + SMS-код
- `/order` → `OrderPage` — создание заказа, свайп-карточки

**OrderPage** — свайп-интерфейс из 4 карточек:
1. `AddressCard` — выбор улицы, дома, квартиры, комментарий
2. `TariffCard` — выбор тарифа (бесплатный / платный)
3. `MachinesCard` — выбор машинки (только при бесплатном тарифе)
4. `ServicesCard` — выбор типа и допуслуг, кнопка добавления в корзину

Корзина: `CartMini` (плавающий бейдж) + `CartExpanded` (модальное дно).
Статус заказа: `StatusScreen` (оверлей с таймлайном и polling).

### Два тарифа

| | Бесплатный | Платный |
|---|---|---|
| Цена | 0 ₽ | от 190 ₽ |
| Условие | просмотр 3 рекламных объявлений | оплата YooKassa |
| Тип | только пакет | вещь или пакет |
| Позиции | 1 | до 3 |
| Допуслуги | нет | кондиционер, вакуум, глажка |

Компонент `AdViewer` — оверлей с 3 случайными картинками из `advertising/`, 5 сек на каждую. После просмотра счётчик `adsWatched` = 3 и разблокируется кнопка "добавить в корзину".

### Реклама (`advertising/`)

Картинки (jpg/jpeg/png/webp/gif) в папке `advertising/` в корне проекта.
- Backend монтирует папку как `StaticFiles` по пути `/advertising`
- `GET /api/advertising` — возвращает список доступных файлов (сканирует папку динамически)
- Caddy проксирует `/advertising/*` → backend (настроено в `Caddyfile`)
- Vite проксирует `/advertising` → `http://localhost:8001` в dev-режиме (`vite.config.ts`)

### Backend Layers

```
src/api/routers/      ← FastAPI эндпоинты, Pydantic-валидация
       ↓ Depends()
src/schemas/          ← Pydantic модели запросов/ответов
       ↓
src/repositories/     ← SQLAlchemy async-запросы
       ↓
src/models/           ← ORM (Client, Order, Service, OrderStatusHistory)
       ↓
PostgreSQL            ← схема в pg_init/01-schema.sql (НЕ автогенерируется)
```

**Services** (`src/services/`):
- `pricing.py` — цена = `(base_price + service_prices) × bags_number`
- `auth.py` — генерация SMS-кода верификации (через `secrets`)
- `payment.py` — создание платежей YooKassa
- `sms/` — отправка SMS через SmsAero

**Роутеры** (`src/api/routers/`):
- `auth.py` — `/api/auth/*`: request-code, verify, me
- `orders.py` — `/api/orders/*`: создание, получение
- `payments.py` — `/api/payments/*`: YooKassa webhook
- `addresses.py` — `/api/addresses`: список улиц и домов
- `services.py` — `/api/services`: список услуг с ценами
- `analytics.py` — `POST /api/analytics/track-visit`: трекинг QR-переходов
- `app.py` — `GET /api/advertising`: список рекламных файлов

### Authentication

Phone → SMS-код → UUID auth token в `Client.auth_token`. Защищённые роуты используют `get_current_client` (`src/api/dependencies.py`).

### Order Lifecycle

Статусы: `WAITING_FOR_CAPTURE → NEW → COURIER_PICKUP → PICKED_UP → WASHING → DRYING → IRONING → PACKING → COURIER_DELIVERY → DELIVERED`

В `dev`-режиме (`APP_ENV=development`) оплата игнорируется, заказ сразу переходит в `NEW`.

### Address System

Зона обслуживания захардкожена в `src/addresses.py` как `dict[str, list[str]]` (улица → список домов). Свободный ввод недоступен — только выбор из выпадающих списков.

`QR_CODE_MAP: dict[int, str]` — маппинг числовых кодов из `/?ref=N` на адрес-slug. Коды несеквентные, 1–1000, по одному на дом.

### Settings

`pydantic-settings` загружает из `.env`:
- `src/settings.py` — `DBSettings`, `AppSettings` (включает `APP_LAUNCHED: bool`), `YookassaSettings`

`APP_LAUNCHED=false` — предзапускной режим: регистрация работает, кнопка заказа на лендинге показывает модалку.

### Database

PostgreSQL 16. Схема в `pg_init/01-schema.sql` — управляется вручную.

Таблицы: `clients`, `orders`, `order_statuses`, `order_status_history`, `services`, `landing_visits`, `promo_codes`, `promo_code_uses`.

### Infrastructure

- `postgres` — БД с init-скриптом
- `backend` — FastAPI на порту 8000 (внутри Docker), раздаёт `/advertising/*`
- `frontend` — Vite build → статика в volume `frontend_dist`
- `caddy` — reverse proxy: `/advertising/*` и `/api/*` → backend, остальное → `file_server`
- `adminer` — веб-UI БД на порту 8081
- `baserow` — no-code UI на порту 8082

### Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0 (async) + asyncpg, httpx, yookassa, pydantic-settings, ruff
- **Frontend**: React 19, TypeScript 5.7, Vite 6, vite-plugin-pwa
- **Infra**: Docker Compose, Caddy 2, PostgreSQL 16
