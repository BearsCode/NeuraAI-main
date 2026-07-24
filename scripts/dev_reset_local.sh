#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
VENV_PYTHON="${ROOT_DIR}/.venv/bin/python"
LOCAL_DB_PATH="${ROOT_DIR}/neuaraai.db"
TRASH_DB_PATH="${HOME}/.Trash/neuaraai.db"
PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"
START_SERVER="${START_SERVER:-1}"
STOP_DOCKER_API="${STOP_DOCKER_API:-1}"

if [ ! -x "${VENV_PYTHON}" ]; then
  echo "Missing virtualenv python at ${VENV_PYTHON}" >&2
  exit 1
fi

kill_project_uvicorns() {
  pgrep -f "uvicorn backend.app.main:app" | while IFS= read -r pid; do
    [ -n "${pid}" ] || continue
    cwd="$(lsof -a -p "${pid}" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')"
    if [ "${cwd}" = "${ROOT_DIR}" ]; then
      kill "${pid}" 2>/dev/null || true
    fi
  done
}

stop_docker_api() {
  if [ "${STOP_DOCKER_API}" != "1" ]; then
    return 0
  fi

  if command -v docker >/dev/null 2>&1 && docker compose ps api >/dev/null 2>&1; then
    docker compose stop api >/dev/null 2>&1 || true
  fi
}

remove_local_db() {
  rm -f "${LOCAL_DB_PATH}"
  rm -f "${TRASH_DB_PATH}"
}

bootstrap_db() {
  (cd "${ROOT_DIR}" && "${VENV_PYTHON}" scripts/bootstrap_db.py)
}

start_server() {
  if [ "${START_SERVER}" != "1" ]; then
    return 0
  fi

  cd "${ROOT_DIR}"
  exec "${VENV_PYTHON}" -m uvicorn backend.app.main:app --host "${HOST}" --port "${PORT}"
}

echo "Stopping local project uvicorn processes..."
kill_project_uvicorns

echo "Stopping docker api on port 8000 if it is running..."
stop_docker_api

echo "Removing local SQLite database..."
remove_local_db

echo "Bootstrapping a fresh local database..."
bootstrap_db

echo "Local reset complete."
echo "Database: ${LOCAL_DB_PATH}"
echo "Server target: http://${HOST}:${PORT}"

start_server
