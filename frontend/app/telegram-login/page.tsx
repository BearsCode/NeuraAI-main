"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef } from "react";

export default function TelegramLoginPage() {
  const router = useRouter();
  const done = useRef(false);

  const handleAuth = useCallback(
    (user: { id: number; first_name: string; last_name?: string; username?: string; photo_url?: string; auth_date: number; hash: string }) => {
      if (done.current) return;
      done.current = true;
      fetch("/api/auth/oauth/telegram", {
        method: "POST",
        body: JSON.stringify(user),
      })
        .then((r) => {
          if (r.ok) {
            router.replace("/workspace");
            router.refresh();
          } else {
            router.replace("/login?error=telegram_auth_failed");
          }
        })
        .catch(() => {
          router.replace("/login?error=telegram_auth_failed");
        });
    },
    [router],
  );

  useEffect(() => {
    const botName = process.env.NEXT_PUBLIC_TELEGRAM_BOT_NAME || "";
    const w = window as unknown as Record<string, unknown>;

    function onTelegramAuth(user: unknown) {
      handleAuth(user as Parameters<typeof handleAuth>[0]);
    }

    if (w.Telegram) {
      const tg = w.Telegram as Record<string, unknown>;
      tg.Login = tg.Login || {};
    }

    w.onTelegramAuth = onTelegramAuth;

    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botName);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.setAttribute("data-request-access", "write");
    script.async = true;
    document.getElementById("telegram-widget")?.appendChild(script);

    return () => {
      delete w.onTelegramAuth;
    };
  }, [handleAuth]);

  return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center",
      justifyContent: "center", minHeight: "100vh", gap: 24,
      background: "var(--bg)", color: "var(--ink)",
    }}>
      <div style={{ textAlign: "center" }}>
        <h1 style={{ fontSize: "1.3rem", fontWeight: 700, margin: 0 }}>Вход через Telegram</h1>
        <p style={{ color: "var(--ink-faint)", fontSize: "0.9rem", margin: "8px 0 0" }}>
          Нажмите кнопку ниже, чтобы войти через Telegram
        </p>
      </div>
      <div id="telegram-widget" style={{ minHeight: 60 }} />
      <noscript>JavaScript необходим для входа через Telegram</noscript>
    </div>
  );
}
