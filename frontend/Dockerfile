FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci


FROM node:20-alpine AS builder

ARG NEXT_PUBLIC_VK_CLIENT_ID
ARG NEXT_PUBLIC_YANDEX_CLIENT_ID
ARG NEXT_PUBLIC_MAILRU_CLIENT_ID
ARG NEXT_PUBLIC_TELEGRAM_BOT_NAME
ENV NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_VK_CLIENT_ID=${NEXT_PUBLIC_VK_CLIENT_ID:-} \
    NEXT_PUBLIC_YANDEX_CLIENT_ID=${NEXT_PUBLIC_YANDEX_CLIENT_ID:-} \
    NEXT_PUBLIC_MAILRU_CLIENT_ID=${NEXT_PUBLIC_MAILRU_CLIENT_ID:-} \
    NEXT_PUBLIC_TELEGRAM_BOT_NAME=${NEXT_PUBLIC_TELEGRAM_BOT_NAME:-}

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN mkdir -p public
RUN npm run build


FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -S app && adduser -S -G app appuser

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

USER appuser

EXPOSE 3000

CMD ["node", "server.js"]
