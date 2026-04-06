# TODO — Критические проблемы проекта

> Выявлены в ходе аудита кода. Устранить до production-запуска.

---

## 🔴 Критические (блокируют production)

- [ ] **Вебхук YooKassa не защищён** — `src/api/routers/payments.py:17`
  - При `yookassa_payment_id = NULL` любой может подделать оплату через POST к `/payments/webhook`
  - Исправление: верифицировать платёж через `Payment.find_one(payment_id)` из YooKassa SDK

- [x] **Небезопасная генерация кода верификации** — `src/services/auth.py`
  - `random.randint` → `secrets.randbelow`, логирование кода удалено

- [ ] **Молчащий сбой создания платежа** — `src/api/routers/orders.py:92`
  - При сбое YooKassa: заказ создаётся, клиент получает `200 OK` с `confirmation_url: null`
  - Заказ навсегда зависает в `WAITING_FOR_CAPTURE`
  - Исправление: в `except` → `raise HTTPException(status_code=500)`

---

## 🟠 Высокий приоритет

- [ ] **Адрес не валидируется на сервере** — `src/api/routers/orders.py:37`
  - `street` и `house` принимают произвольные строки, `HOUSE_STREET_MAP` не проверяется
  - Исправление: валидация в `CreateOrderIn` или в роутере

- [ ] **Устаревший токен не очищается при 401** — `frontend/src/api/client.ts`
  - Пользователь застрянет в авторизованном состоянии
  - Исправление: при `response.status === 401` → `clearToken()` + редирект на `/`

- [ ] **Подъезд и этаж не собираются у пользователя** — `frontend/src/components/steps/ApartmentStep.tsx`
  - Всегда `entrance: 1, floor: 1` — курьер не знает реального адреса
  - Исправление: добавить поля ввода в `ApartmentStep`

---

## 🟡 Средний приоритет (UX)

- [ ] **Молчащая ошибка в OrdersPage** — `frontend/src/pages/OrdersPage.tsx:57`
  - `.catch(() => {})` — пользователь не видит ошибку загрузки деталей заказа

- [ ] **Polling в StatusStep не восстанавливается после ошибки** — `frontend/src/components/steps/StatusStep.tsx:17`
  - Временная ошибка → постоянный режим ошибки

- [ ] **Нет состояния загрузки и обработки ошибок в StreetStep/HouseStep**
  - `getAddresses().then(...)` без `.catch()` — при ошибке пользователь не может выбрать улицу

---

## 🟠 Предзапуск / лендинг

- [ ] **Таблица `landing_visits` не мигрирует автоматически на существующей БД**
  - `pg_init/01-schema.sql` выполняется только при первом запуске контейнера
  - Создать вручную через Adminer или добавить отдельный migration-скрипт

- [ ] **Нет уведомления клиентам при запуске** — `APP_LAUNCHED=true` переключается, но зарегистрированным клиентам ничего не приходит
  - Возможное решение: рассылка SMS через SmsAero всем клиентам с `is_verified=true`

- [ ] **QR-коды не сгенерированы физически** — есть `QR_CODE_MAP` в коде, но сами PNG/SVG файлы для печати не созданы
  - Нужен скрипт или ручная генерация через qr-code сервис

- [ ] **Нет защиты от спама `/analytics/track-visit`** — эндпоинт открыт без auth и rate-limit
  - Добавить rate limiting (slowapi или middleware) или переключить на анонимный токен

## 🔵 Низкий приоритет

- [ ] `SECRET_KEY = "change-me-in-production"` без предупреждения — `src/settings.py:45`
- [ ] Нет Rate Limiting на `/auth/request-code` и `/auth/verify`
- [ ] Нет валидации формата телефонного номера
- [ ] Нет глобального Error Boundary в React — `frontend/src/App.tsx`
- [ ] `getServices()` вызывается дважды: в `ServicesStep` и `ConfirmStep`
- [ ] **Интеграция рекламы с БД** — сейчас картинки захардкожены в `OrderPage.tsx`
  - Создать таблицу `ads` (id, url, active, display_order)
  - Добавить эндпоинт `GET /api/ads` для получения списка активных объявлений
  - Вести статистику просмотров (таблица `ad_views`: ad_id, client_id, viewed_at)
  - Поддержка ротации и A/B тестирования через порядок показа
