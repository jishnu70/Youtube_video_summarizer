# #!/usr/bin/env bash
# set -euo pipefail

# cd "$(dirname "$0")"

# # Start redis container
# docker compose -f compose.redis.yaml up -d

# # Activate venv
# source .venv/bin/activate

# # Optional: make sure env vars are loaded (only if you rely on .env in shell)
# set -a
# [[ -f .env ]] && source .env
# set +a

# # Start celery in background
# celery -A src.background.celery_app:celery_app worker --loglevel=INFO --pool=solo flower --port=5555 -E &
# CELERY_PID=$!

# celery -A src.background.celery_app:celery_app flower --port=5555

# # Ensure celery stops when script exits
# cleanup() {
#   kill "$CELERY_PID" 2>/dev/null || true
# }
# trap cleanup EXIT

# # Start fastapi in foreground
# uvicorn src.presentation.routes:app --reload


#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Start redis
docker compose -f compose.redis.yaml up -d --remove-orphans

source .venv/bin/activate

# Load local env file if you have it
set -a
[[ -f .env ]] && source .env
set +a

# Start celery worker (NO --port here)
celery -A src.background.celery_app:celery_app worker --loglevel=INFO --pool=threads --concurrency=4 -E &
CELERY_PID=$!

# (Optional) start flower on 5555
celery -A src.background.celery_app:celery_app flower --address=127.0.0.1 --port=5555 &
FLOWER_PID=$!

cleanup() {
  kill "$FLOWER_PID" 2>/dev/null || true
  kill "$CELERY_PID" 2>/dev/null || true
}
trap cleanup EXIT

uvicorn src.presentation.routes:app --reload
