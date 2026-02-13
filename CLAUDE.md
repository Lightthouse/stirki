# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stirki ON — a hyperlocal laundry delivery service for Mytishchi (Moscow region). Customers create orders via a PWA (React) or Telegram bot (legacy), a courier picks up laundry, it gets washed/dried, and delivered back.

**The project language is Russian** — all user-facing text, commit messages, and documentation are in Russian.

## Commands

```bash
# Start infrastructure (PostgreSQL, Adminer, Baserow)
docker compose up -d

# Start the FastAPI backend
uv run uvicorn src.api.app:app --reload --port 8000

# Start the frontend dev server
cd frontend && npm run dev

# Start the Telegram bot (legacy)
uv run -m src.bot.main

# Seed / clear test data
uv run -m test_db seed
uv run -m test_db clear
uv run -m test_db reset

# Lint
uv run ruff check src/
uv run ruff format src/
```

## Architecture

### Two Frontends

1. **PWA** (`frontend/`) — React 19 + TypeScript + Vite. Multi-step order form in `frontend/src/pages/OrderPage.tsx`, state managed by `useOrderFlow` hook. API calls in `frontend/src/api/`.
2. **Telegram bot** (`src/bot/`) — Legacy. Uses `python-telegram-bot` ConversationHandler with FSM states in `src/bot/states.py`.

### Backend Layers

```
API Router (src/api/routers/)     ← FastAPI endpoints, Pydantic validation
       ↓ Depends()
Repository (src/repositories/)    ← SQLAlchemy async queries
       ↓
Model (src/models/)               ← SQLAlchemy ORM (Client, Order, Service, OrderStatusHistory)
       ↓
PostgreSQL                        ← Schema managed via pg_init/01-schema.sql (NOT auto-generated)
```

**Services** (`src/services/`) contain business logic orthogonal to the data layer:
- `pricing.py` — price = `(base_price + service_prices) × bags_number`
- `kaiten_kanban.py` — creates/moves cards on kaiten.ru kanban board per order status
- `auth.py` — phone verification code generation
- `payment.py` — YooKassa payment creation and processing

### Authentication

Phone → SMS verification code → UUID auth token stored in `Client.auth_token`. Protected routes use `get_current_client` dependency (`src/api/dependencies.py`).

### Order Lifecycle

New client flow: `phone → code → name → street → house → apartment → bags → services → confirm → payment → status`
Returning client: `phone → code → bags → services → confirm → payment → status`

Order statuses: `WAITING_FOR_CAPTURE → NEW → COURIER_PICKUP → PICKED_UP → WASHING → DRYING → IRONING → PACKING → COURIER_DELIVERY → DELIVERED`

### Address System

Service area hardcoded in `src/addresses.py` as `dict[str, list[str]]` (street → house numbers). No free-text input — users pick from dropdowns/buttons.

### Key Enums

`src/enums.py` — order statuses, payment statuses, service slugs (English), service display names (Cyrillic), Kaiten column/tag ID mappings.

### Settings

All settings use `pydantic-settings` loading from `.env`:
- `src/settings.py` — `DBSettings`, `KaitenSettings`, `AppSettings`, `YookassaSettings`
- `src/bot/settings.py` — `TgSettings` (bot token, payment provider token)

### Database

PostgreSQL 16. Schema in `pg_init/01-schema.sql` includes table definitions and seed data (services with prices, order statuses). The schema is **manually managed** — not auto-generated from ORM models.

### Infrastructure (compose.yml)

- `postgres` — DB with init script
- `backend` — FastAPI on port 8000
- `frontend` — Vite/React build
- `caddy` — reverse proxy (prod profile)
- `adminer` — DB UI on port 8081
- `baserow` — no-code DB UI on port 8082

### Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0 (async) + asyncpg, httpx, yookassa, pydantic-settings, ruff
- **Frontend**: React 19, TypeScript 5.7, Vite 6, vite-plugin-pwa
- **Infra**: Docker Compose, Caddy 2, PostgreSQL 16
