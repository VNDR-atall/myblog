#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

MODE="${1:-local}"
VENV_DIR="${VENV_DIR:-.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

print_usage() {
  cat <<'EOF'
Usage:
  bash start.sh [local|docker|docker-detached|docker-down]

Modes:
  local            Start Flask app locally (default)
  docker           Build and start with Docker Compose (foreground)
  docker-detached  Build and start with Docker Compose (background)
  docker-down      Stop Docker Compose services

Environment variables (for local mode):
  VENV_DIR   Python virtual environment directory (default: .venv)
  PYTHON_BIN Python executable (default: python3)
EOF
}

ensure_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: command not found: $1"
    exit 1
  fi
}

start_local() {
  ensure_cmd "$PYTHON_BIN"

  if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR ..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi

  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"

  echo "Installing dependencies ..."
  python -m pip install --upgrade pip
  pip install -r requirements.txt

  echo "Preparing directories and database ..."
  mkdir -p content/posts app/static/images
  python init_db.py

  echo "Starting app at http://localhost:5000 ..."
  exec python run.py
}

start_docker() {
  ensure_cmd docker
  docker compose up --build
}

start_docker_detached() {
  ensure_cmd docker
  docker compose up --build -d
}

stop_docker() {
  ensure_cmd docker
  docker compose down
}

case "$MODE" in
  local)
    start_local
    ;;
  docker)
    start_docker
    ;;
  docker-detached)
    start_docker_detached
    ;;
  docker-down)
    stop_docker
    ;;
  -h|--help|help)
    print_usage
    ;;
  *)
    echo "Unknown mode: $MODE"
    print_usage
    exit 1
    ;;
esac

