# Деплой Stirki ON на VPS

## Требования к серверу

- **1 vCPU, 1 GB RAM** минимум (рекомендуется 2 GB)
- **Ubuntu 24.04 LTS**
- Открытые порты: **80** (HTTP), **443** (HTTPS, когда появится домен)
- Провайдеры: Timeweb Cloud, Selectel, reg.ru VDS

## 1. Первичная настройка сервера

```bash
# Подключение к серверу
ssh root@IP_АДРЕС

# Обновление системы
apt update && apt upgrade -y

# Установка Docker (официальный способ)
curl -fsSL https://get.docker.com | sh

# Проверка
docker --version
docker compose version
```

## 2. Клонирование репозитория

```bash
cd /opt
git clone https://github.com/YOUR_ORG/stirki.git
cd stirki
```

## 3. Настройка `.env`

```bash
cp .env.example .env
nano .env
```

Заполните обязательные переменные:

```env
# PostgreSQL
DB_USER=stirki
DB_PASSWORD=СГЕНЕРИРОВАТЬ_СЛОЖНЫЙ_ПАРОЛЬ
DB_PORT=5432

# Домен — пока нет домена, слушаем HTTP на порту 80
DOMAIN=:80

# URL фронтенда — подставьте IP вашего сервера
FRONTEND_URL=http://IP_АДРЕС
YOOKASSA_RETURN_URL=http://IP_АДРЕС

# Секретный ключ
SECRET_KEY=СГЕНЕРИРОВАТЬ_СЛУЧАЙНУЮ_СТРОКУ

# Режим предзапуска: false = заказы заблокированы, true = всё работает
APP_LAUNCHED=false

# YooKassa
YOOKASSA_SHOP_ID=...
YOOKASSA_SECRET_KEY=...
```

Генерация паролей и ключей:

```bash
# Пароль для БД
openssl rand -base64 24

# Секретный ключ
openssl rand -hex 32
```

## 4. Запуск

```bash
chmod +x run.sh
./run.sh prod
```

Первый запуск займёт несколько минут — собираются Docker-образы.

## 5. Проверка

```bash
# Статус контейнеров
docker compose --profile prod ps

# Логи backend
docker compose --profile prod logs backend -f

# Проверка API
curl http://localhost/api/health
```

Откройте в браузере: `http://IP_АДРЕС` — должна загрузиться PWA.

## 6. Когда появится домен

1. Направьте A-запись домена на IP сервера
2. Обновите `.env`:

```env
DOMAIN=stirki-on.ru
FRONTEND_URL=https://stirki-on.ru
YOOKASSA_RETURN_URL=https://stirki-on.ru
```

3. Перезапустите:

```bash
docker compose --profile prod down
./run.sh prod
```

Caddy автоматически получит SSL-сертификат от Let's Encrypt.

## 7. Переключение в рабочий режим (после предзапуска)

Когда сервис готов принимать заказы:

1. В `.env` измените:
```env
APP_LAUNCHED=true
```
2. Перезапустите backend (без пересборки образа):
```bash
docker compose --profile prod restart backend
```

Лендинг сразу начнёт пускать клиентов к форме заказа.

## 8. QR-аналитика

QR-коды в объявлениях используют числовые коды (`/?ref=142`), которые сопоставляются с адресами в `src/addresses.py` (`QR_CODE_MAP`).

Посмотреть статистику визитов по объявлениям через Adminer (`http://IP:8081`):

```sql
SELECT ref_code, COUNT(*) AS visits, MAX(visited_at) AS last_visit
FROM landing_visits
GROUP BY ref_code
ORDER BY visits DESC;
```

> Важно: таблица `landing_visits` создаётся скриптом `pg_init/01-schema.sql` при первом запуске контейнера PostgreSQL. Если БД уже запущена, создайте таблицу вручную через Adminer.

## Полезные команды

```bash
# Перезапуск всех сервисов
docker compose --profile prod restart

# Пересборка после обновления кода
git pull
docker compose --profile prod up -d --build

# Просмотр логов
docker compose --profile prod logs -f

# Подключение к БД
docker exec -it stirki-db psql -U stirki -d stirki
```
