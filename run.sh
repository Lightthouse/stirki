#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
    echo "Использование: ./run.sh {local|dev|prod|stop}"
    echo ""
    echo "  local — БД + adminer + baserow в docker, backend и frontend локально с hot-reload, без оплаты"
    echo "  dev   — весь стек в docker (включая backend, frontend, caddy), без оплаты"
    echo "  prod  — весь стек в docker (включая backend, frontend, caddy), с реальной оплатой"
    echo "  stop  — остановить всё"
    exit 1
}

cmd_local() {
    echo "==> Запуск инфраструктуры (postgres, adminer, baserow)..."
    docker compose up -d

    echo "==> Ожидание готовности postgres..."
    until docker compose exec -T postgres pg_isready -U "${DB_USER:-postgres}" -d stirki > /dev/null 2>&1; do
        sleep 1
    done
    echo "==> Postgres готов"

    trap 'echo ""; echo "==> Остановка процессов..."; kill 0; exit 0' INT TERM

    export APP_ENV=development

    echo "==> Запуск backend (uvicorn --reload) на :8000 (APP_ENV=development)..."
    uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload &

    echo "==> Запуск frontend (npm run dev) на :5173..."
    (cd frontend && npm run dev) &

    wait
}

cmd_dev() {
    echo "==> Запуск в dev-режиме (без оплаты)..."
    APP_ENV=development docker compose --profile prod up -d --build
}

cmd_prod() {
    echo "==> Запуск в prod-режиме..."
    APP_ENV=production docker compose --profile prod up -d --build
}

cmd_stop() {
    echo "==> Остановка docker compose..."
    docker compose --profile prod down
    echo "==> Остановлено"
}

case "${1:-}" in
    local) cmd_local ;;
    dev)   cmd_dev   ;;
    prod)  cmd_prod  ;;
    stop)  cmd_stop  ;;
    *)     usage     ;;
esac
