FROM python:3.12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VENV_PATH=/opt/venv

WORKDIR /build

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv "${VENV_PATH}"
ENV PATH="${VENV_PATH}/bin:${PATH}"

COPY pyproject.toml README.md ./

RUN python - <<'PY'
import subprocess
import tomllib
from pathlib import Path

project = tomllib.loads(Path("pyproject.toml").read_text())
dependencies = project["project"]["dependencies"]

subprocess.check_call(["pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
subprocess.check_call(["pip", "install", *dependencies])
PY

COPY alembic.ini ./
COPY backend ./backend
COPY migrations ./migrations
COPY scripts ./scripts
COPY main.py ./

RUN pip install --no-deps .


FROM python:3.12-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VENV_PATH=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH=/app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system app \
    && adduser --system --ingroup app appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts
COPY main.py ./

RUN mkdir -p /app/storage/uploads /app/data \
    && chown -R appuser:app /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live')" || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
