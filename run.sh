#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
    echo "Использование: ./run.sh {dev|prod|stop}"
    echo ""
    echo "  dev   — БД + adminer + baserow в docker, backend и frontend локально с hot-reload"
    echo "  prod  — весь стек в docker (включая backend, frontend, caddy)"
    echo "  stop  — остановить всё"
    exit 1
}

cmd_dev() {
    echo "==> Запуск инфраструктуры (postgres, adminer, baserow)..."
    docker compose up -d

    echo "==> Ожидание готовности postgres..."
    until docker compose exec -T postgres pg_isready -U "${DB_USER:-postgres}" -d stirki > /dev/null 2>&1; do
        sleep 1
    done
    echo "==> Postgres готов"

    trap 'echo ""; echo "==> Остановка процессов..."; kill 0; exit 0' INT TERM

    echo "==> Запуск backend (uvicorn --reload) на :8000..."
    uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload &

    echo "==> Запуск frontend (npm run dev) на :5173..."
    (cd frontend && npm run dev) &

    wait
}

cmd_prod() {
    echo "==> Запуск всего стека в docker..."
    docker compose --profile prod up -d --build
    echo "==> Готово. Caddy на :80, backend на :8000"
}

cmd_stop() {
    echo "==> Остановка docker compose..."
    docker compose --profile prod down
    echo "==> Остановлено"
}

case "${1:-}" in
    dev)  cmd_dev  ;;
    prod) cmd_prod ;;
    stop) cmd_stop ;;
    *)    usage    ;;
esac
