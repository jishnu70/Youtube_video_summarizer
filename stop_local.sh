#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Stop redis
docker compose -f compose.redis.yaml down || true

# Stop local processes if they’re still running
pkill -f "celery -A src.background.celery_app:celery_app worker" || true
pkill -f "uvicorn src.presentation.routes:app" || true
