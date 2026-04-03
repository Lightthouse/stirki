# Руководство по тестированию Stirki ON

## Общие предусловия

- `.env` заполнен: `DB_PASSWORD`, `SECRET_KEY`, `SMSAERO_EMAIL`, `SMSAERO_API_KEY`, `SMSAERO_SIGN`
- `APP_ENV=development` → код авторизации виден в консоли бэкенда (SMS реально не отправляются)
- Docker запущен

## Быстрый старт: `./run.sh`

| Команда | Где запускается | Оплата | Типичный стенд |
|---|---|---|---|
| `./run.sh local` | БД в docker, backend и frontend — на хосте (hot-reload) | без оплаты | локальная разработка |
| `./run.sh dev` | Весь стек в docker | без оплаты | проверка prod-сборки локально |
| `./run.sh prod` | Весь стек в docker | реальная | VPS / staging |
| `./run.sh stop` | — | — | остановить всё |

---

## Сценарий 1: Локально, рекламный режим (`APP_LAUNCHED=false`)

1. Запустить стек:
   ```bash
   ./run.sh local
   ```
   > Запускает postgres + adminer + baserow в docker, backend на :8000 и frontend на :5173 локально с hot-reload.
2. Открыть `http://localhost:5173`
5. ✅ Кнопки "Сделать заказ" и "Список заказов" → модаль "Скоро открываемся"
6. ✅ Кнопка регистрации ведёт на `/order` (без модали)
7. Пройти регистрацию: телефон → код из консоли бэкенда → имя → адрес
   - Код виден в терминале с бэкендом: `INFO ... [DEV] Код подтверждения +79...: 1234`
8. ✅ После регистрации возврат на лендинг снова показывает модаль

---

## Сценарий 2: Локально, запущенный режим (`APP_LAUNCHED=true`)

1. В `.env`: `APP_LAUNCHED=true`
2. Перезапустить стек: `./run.sh local`
3. Открыть `http://localhost:5173`
3. ✅ Кнопка "Сделать заказ" ведёт на `/order`
4. Пройти полный flow: телефон → код → адрес → мешки → услуги → подтверждение
5. После создания заказа — вместо YooKassa симулировать оплату:
   ```bash
   # Найти order_id в ответе на создание заказа, затем:
   POST http://localhost:8000/api/payments/test/simulate/{order_id}
   ```
   (через `aero.http` или curl)
6. ✅ StatusStep показывает актуальный статус заказа

---

## Сценарий 2.5: Локально, всё в docker (`dev`-режим)

Альтернатива сценариям 1–2 если не нужен hot-reload на хост-машине (например, проверка prod-сборки фронта):

1. В `.env`: нужные значения (`APP_LAUNCHED=true/false`)
2. ```bash
   ./run.sh dev
   ```
   > Весь стек в docker (backend, frontend, caddy), `APP_ENV=development` → SMS не отправляются. Логи: `docker compose --profile prod logs -f backend`
3. Открыть `http://localhost`

---

## Сценарий 3: VPS, рекламный режим + QR-аналитика

1. `.env` на сервере:
   ```
   APP_LAUNCHED=false
   APP_ENV=development
   DOMAIN=<IP сервера>
   ```
2. Запустить весь стек:
   ```bash
   ./run.sh prod
   ```
   > Весь стек в docker: backend, frontend, caddy, postgres, adminer, baserow.
3. Открыть `http://<IP>`
4. Те же проверки что в Сценарии 1; код смотреть через:
   ```bash
   docker compose --profile prod logs -f backend
   ```
5. **QR-аналитика**:
   - Сгенерировать QR:
     ```bash
     uv run scripts/gen_qr.py --base-url http://<IP>
     ```
   - Открыть `qr_codes/index.html`, отсканировать один QR-код телефоном
   - Проверить в Adminer (`http://<IP>:8081`):
     ```sql
     SELECT * FROM landing_visits ORDER BY visited_at DESC LIMIT 5;
     ```
   - ✅ Запись с нужным `ref_code` появилась

---

## Сценарий 4: VPS, запущенный режим + Baserow

1. `.env` на сервере: `APP_LAUNCHED=true`
2. Перезапустить стек:
   ```bash
   ./run.sh prod
   ```
3. Пройти полный flow заказа (как Сценарий 2, через `http://<IP>`)
4. **Проверка Baserow** (`http://<IP>:8082`):
   - Войти / зарегистрировать аккаунт администратора
   - Убедиться что в `.env` заполнены:
     ```
     BASEROW_URL=http://<IP>:8082
     BASEROW_API_TOKEN=
     BASEROW_CLIENTS_TABLE_ID=
     BASEROW_ORDERS_TABLE_ID=
     ```
   - После изменения `.env`: `docker compose --profile prod restart backend`
   - ✅ В таблице клиентов есть запись с номером телефона
   - ✅ В таблице заказов есть запись с ID и суммой

---

## Проверка логирования кода

| Условие | Ожидаемое поведение |
|---|---|
| `APP_ENV=development` | В консоли бэкенда: `INFO ... [DEV] Код подтверждения +79...: 1234` |
| `APP_ENV=production` | Строка `[DEV]` не появляется, SMS отправляется реально |
