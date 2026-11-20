#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
    echo "Использование: ./run.sh {local|server|stop|backup|check-web}"
    echo ""
    echo "  local  — БД + adminer в docker, backend и frontend локально с hot-reload (для разработки)"
    echo "  server — весь стек в docker (backend, frontend, caddy) — так запускается сервер"
    echo "  stop  — остановить всё"
    echo "  backup — дамп БД в \$BACKUP_DIR (по умолчанию /var/backups/stirki), хранятся 14 последних"
    echo "  check-web — на сервере: Caddy держит порты 80/443, иначе освободить их и пересоздать Caddy (для cron)"
    echo ""
    echo "  Окружение одно: оплата через Точку настоящая везде, SMS включаются флагом в админке"
    echo "  («Системные настройки» → «Вход по SMS»). В .env обязательны SECRET_KEY и ADMIN_PASSWORD."
    exit 1
}

cmd_local() {
    echo "==> Запуск инфраструктуры (postgres, adminer)..."
    docker compose up -d

    echo "==> Ожидание готовности postgres..."
    until docker compose exec -T postgres pg_isready -U "${DB_USER:-postgres}" -d stirki > /dev/null 2>&1; do
        sleep 1
    done
    echo "==> Postgres готов"

    trap 'echo ""; echo "==> Остановка процессов..."; kill 0; exit 0' INT TERM

    echo "==> Освобождение порта 8001..."
    fuser -k 8001/tcp 2>/dev/null || true

    echo "==> Запуск backend (uvicorn --reload) на :8001..."
    uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8001 --reload &

    echo "==> Запуск frontend (npm run dev) на :5173..."
    (cd frontend && npm run dev) &

    wait
}

# PID-ы процессов, которые слушают TCP-порт $1, кроме Docker (docker-proxy — это Caddy).
foreign_listeners() {
    ss -Htlnp "sport = :$1" | grep -v docker-proxy | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u || true
}

# ISPmanager держит на сервере свой nginx (README, «Сервер»): стоит Caddy остановиться, nginx занимает порт 80,
# и Caddy после этого не поднимается. Освобождаем 80/443 от всего, что не Docker.
free_web_ports() {
    local port pids svc
    for port in 80 443; do
        pids=$(foreign_listeners "$port")
        [ -z "$pids" ] && continue
        echo "==> Порт $port занят не Docker: $(ps -o comm= -p "$(echo $pids | tr ' ' ',')" | sort -u | tr '\n' ' ')— освобождаем"
        for svc in nginx apache2 httpd; do
            if systemctl is-active --quiet "$svc" 2>/dev/null; then timeout 30 systemctl stop "$svc" || true; fi
        done
        sleep 1
        pids=$(foreign_listeners "$port")
        if [ -n "$pids" ]; then kill $pids 2>/dev/null || true; sleep 1; fi
    done
}

caddy_ok() {
    [ "$(docker inspect -f '{{.State.Running}}' stirki-caddy 2>/dev/null)" = "true" ] \
        && ss -Htlnp "sport = :80" | grep -q docker-proxy \
        && ss -Htlnp "sport = :443" | grep -q docker-proxy
}

# Caddy, запущенный при занятом порте, остаётся без сети — его нужно пересоздать (README, «Первичная установка»).
ensure_caddy() {
    caddy_ok && return 0
    echo "==> $(date '+%F %T') Caddy не держит порты 80/443 — освобождаем порты и пересоздаём Caddy"
    free_web_ports
    docker compose --profile prod up -d --force-recreate --no-deps caddy
    sleep 3
    if caddy_ok; then
        echo "==> Caddy работает"
    else
        echo "==> ОШИБКА: Caddy так и не занял порты 80/443 — смотрите: ss -tlnp | grep -E ':(80|443) '"
        return 1
    fi
}

cmd_server() {
    echo "==> Сборка frontend без кеша..."
    docker compose --profile prod build --no-cache frontend
    free_web_ports
    echo "==> Запуск всего стека (без SECRET_KEY и ADMIN_PASSWORD в .env бэкенд не стартует)..."
    docker compose --profile prod up -d --build
    # Caddyfile подключён в контейнер отдельным файлом: git pull заменяет файл, а контейнер видит старый,
    # пока его не пересоздать. Пересоздаём всегда — пара секунд, зато правки Caddyfile не теряются.
    echo "==> Пересоздание Caddy (новый Caddyfile)..."
    docker compose --profile prod up -d --force-recreate --no-deps caddy
    sleep 3
    ensure_caddy
}

# Для cron раз в 5 минут: молчит, пока всё в порядке.
cmd_check_web() {
    ensure_caddy
}

cmd_stop() {
    echo "==> Остановка docker compose..."
    docker compose --profile prod down
    echo "==> Остановлено"
}

cmd_backup() {
    # Каталог вне репозитория: репозиторий публичный, дампы с ПДн в git попасть не должны.
    local dir="${BACKUP_DIR:-/var/backups/stirki}"
    local file="$dir/stirki-$(date +%Y%m%d-%H%M%S).sql.gz"
    mkdir -p "$dir" && chmod 700 "$dir"
    # Пишем во временный файл: оборванный дамп не должен вытеснить ротацией целые копии.
    docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d stirki' | gzip > "$file.tmp"
    mv "$file.tmp" "$file"
    ls -1t "$dir"/stirki-*.sql.gz | tail -n +15 | xargs -r rm --
    echo "==> Дамп: $file"
}

case "${1:-}" in
    local) cmd_local ;;
    server) cmd_server ;;
    stop)  cmd_stop  ;;
    backup) cmd_backup ;;
    check-web) cmd_check_web ;;
    *)     usage     ;;
esac
