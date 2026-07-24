#!/bin/sh
set -eu

: "${WEB__DOMAIN:?WEB__DOMAIN is required}"
: "${APP_UPSTREAM:=api:8000}"
: "${FRONTEND_UPSTREAM:=frontend:3000}"

HTTP_TEMPLATE="/opt/neura/nginx/templates/http.conf.template"
TLS_TEMPLATE="/opt/neura/nginx/templates/tls.conf.template"
OUTPUT_CONFIG="/etc/nginx/conf.d/default.conf"
CERT_DIR="/etc/letsencrypt/live/${WEB__DOMAIN}"
CERT_FILE="${CERT_DIR}/fullchain.pem"
KEY_FILE="${CERT_DIR}/privkey.pem"

render_http_config() {
  envsubst '${WEB__DOMAIN} ${APP_UPSTREAM} ${FRONTEND_UPSTREAM}' \
    < "${HTTP_TEMPLATE}" \
    > "${OUTPUT_CONFIG}"
}

render_tls_config() {
  envsubst '${WEB__DOMAIN} ${APP_UPSTREAM} ${FRONTEND_UPSTREAM}' \
    < "${TLS_TEMPLATE}" \
    > "${OUTPUT_CONFIG}"
}

cert_mtime() {
  if [ -f "${CERT_FILE}" ]; then
    stat -c '%Y' "${CERT_FILE}"
    return 0
  fi

  echo ""
}

mode="http"
last_cert_mtime=""

if [ -f "${CERT_FILE}" ] && [ -f "${KEY_FILE}" ]; then
  render_tls_config
  mode="tls"
  last_cert_mtime="$(cert_mtime)"
else
  render_http_config
fi

nginx -g 'daemon off;' &
nginx_pid=$!

while sleep 15; do
  cert_present="false"
  if [ -f "${CERT_FILE}" ] && [ -f "${KEY_FILE}" ]; then
    cert_present="true"
  fi

  if [ "${cert_present}" = "true" ]; then
    current_cert_mtime="$(cert_mtime)"
    if [ "${mode}" != "tls" ]; then
      render_tls_config
      nginx -s reload
      mode="tls"
      last_cert_mtime="${current_cert_mtime}"
      continue
    fi

    if [ "${current_cert_mtime}" != "${last_cert_mtime}" ]; then
      render_tls_config
      nginx -s reload
      last_cert_mtime="${current_cert_mtime}"
    fi
    continue
  fi

  if [ "${mode}" != "http" ]; then
    render_http_config
    nginx -s reload
    mode="http"
    last_cert_mtime=""
  fi
done &

wait "${nginx_pid}"
