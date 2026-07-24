#!/bin/sh
set -eu

RENEW_INTERVAL_SECONDS="${CERTBOT_RENEW_INTERVAL_SECONDS:-43200}"

while true; do
  certbot renew --webroot --webroot-path /var/www/certbot --quiet
  sleep "${RENEW_INTERVAL_SECONDS}"
done
