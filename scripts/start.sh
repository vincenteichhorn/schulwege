#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [ ! -f .env ]; then
  printf 'Missing .env. Create it with: cp .env.example .env\n' >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

case "${1:-container}" in
  container)
    exec docker compose --profile serve up --build
    ;;
  dev)
    docker compose up -d schulwege-nominatim schulwege-opentripplanner
    trap 'docker compose stop schulwege-nominatim schulwege-opentripplanner' EXIT INT TERM
    export PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
    export DEV_MODE=1
    poetry run streamlit run src/schulwege/app.py --server.port "${APP_PORT:-5173}"
    ;;
  *)
    printf 'Usage: %s [container|dev]\n' "$0" >&2
    exit 2
    ;;
esac
