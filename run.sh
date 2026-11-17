#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
    echo "Использование: ./run.sh {local|server|stop|backup}"
    echo ""
    echo "  local  — БД + adminer в docker, backend и frontend локально с hot-reload (для разработки)"
    echo "  server — весь стек в docker (backend, frontend, caddy) — так запускается сервер"
    echo "  stop  — остановить всё"
    echo "  backup — дамп БД в \$BACKUP_DIR (по умолчанию /var/backups/stirki), хранятся 14 последних"
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

cmd_server() {
    echo "==> Сборка frontend без кеша..."
    docker compose --profile prod build --no-cache frontend
    echo "==> Запуск всего стека (без SECRET_KEY и ADMIN_PASSWORD в .env бэкенд не стартует)..."
    docker compose --profile prod up -d --build
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
    *)     usage     ;;
esac
