#!/bin/sh
set -eu

: "${WEB__DOMAIN:?WEB__DOMAIN is required}"
: "${LETSENCRYPT_EMAIL:?LETSENCRYPT_EMAIL is required}"
: "${NGINX_HOST:=nginx}"
: "${NGINX_PORT:=80}"

CERT_FILE="/etc/letsencrypt/live/${WEB__DOMAIN}/fullchain.pem"

if [ -f "${CERT_FILE}" ]; then
  echo "Certificate already exists for ${WEB__DOMAIN}"
  exit 0
fi

python - <<'PY'
import os
import socket
import time

host = os.environ["NGINX_HOST"]
port = int(os.environ["NGINX_PORT"])
deadline = time.time() + 120

while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit(f"Timed out waiting for {host}:{port}")
PY

mkdir -p /var/www/certbot/.well-known/acme-challenge

certbot certonly \
  --webroot \
  --webroot-path /var/www/certbot \
  --email "${LETSENCRYPT_EMAIL}" \
  --agree-tos \
  --no-eff-email \
  --non-interactive \
  -d "${WEB__DOMAIN}"
