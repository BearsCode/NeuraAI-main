#!/bin/sh
set -eu

: "${WEB__DOMAIN:?WEB__DOMAIN is required}"
: "${APP_UPSTREAM:=api:8000}"

HTTP_TEMPLATE="/opt/neura/nginx/templates/http.api-only.conf.template"
TLS_TEMPLATE="/opt/neura/nginx/templates/tls.api-only.conf.template"
OUTPUT_CONFIG="/etc/nginx/conf.d/default.conf"
CERT_DIR="/etc/letsencrypt/live/${WEB__DOMAIN}"
CERT_FILE="${CERT_DIR}/fullchain.pem"
KEY_FILE="${CERT_DIR}/privkey.pem"

render_http_config() {
  envsubst '${WEB__DOMAIN} ${APP_UPSTREAM}' < "${HTTP_TEMPLATE}" > "${OUTPUT_CONFIG}"
}

render_tls_config() {
  envsubst '${WEB__DOMAIN} ${APP_UPSTREAM}' < "${TLS_TEMPLATE}" > "${OUTPUT_CONFIG}"
}

if [ -f "${CERT_FILE}" ] && [ -f "${KEY_FILE}" ]; then
  render_tls_config
else
  render_http_config
fi

exec nginx -g 'daemon off;'
