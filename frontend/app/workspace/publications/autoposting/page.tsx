"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";
import type { SocialAccount } from "@/lib/types";

export default function AutopostingPage() {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const result = await apiFetch<SocialAccount[]>("/api/backend/social");
      setAccounts(Array.isArray(result) ? result : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : null);
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const platformIcons: Record<string, string> = {
    instagram: "📷", telegram: "✈️", vk: "📱", youtube: "▶️", tiktok: "🎵", threads: "🧵",
  };

  return (
    <div className="content-page">
      <header className="content-header">
        <div>
          <span className="eyebrow">Публикации</span>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "4px 0 0" }}>
            Автопостинг
          </h1>
          <p style={{ margin: "4px 0 0", color: "var(--ink-soft)", fontSize: "0.92rem" }}>
            Настройте автоматическую публикацию контента по расписанию
          </p>
        </div>
      </header>

      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, padding: "80px 0", color: "var(--ink-faint)" }}>
          <div className="dash-loading-spinner" />
          <span style={{ fontSize: "0.95rem" }}>Загрузка...</span>
        </div>
      ) : error ? (
        <div className="error-banner">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>Повторить</button>
        </div>
      ) : (
        <div className="detail-grid">
          {!accounts.length ? (
            <div className="empty-state" style={{ padding: "60px 28px" }}>
              <p style={{ fontSize: "0.95rem" }}>
                Нет подключённых социальных сетей. Перейдите в раздел «Интеграции», чтобы добавить аккаунты.
              </p>
            </div>
          ) : accounts.map((acc) => (
            <article key={acc.id} className="insight-card">
              <div className="card-topline">
                <div>
                  <h3>{platformIcons[acc.platform.toLowerCase()] ?? "🔗"} {acc.platform}</h3>
                  <span className={`status-pill ${acc.status}`}>{acc.status}</span>
                </div>
              </div>
              <div className="summary-list">
                <div className="summary-row">
                  <span>Аккаунт</span>
                  <strong>{acc.account_identifier}</strong>
                </div>
              </div>
              <div className="action-row top-spacer">
                <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                  <input type="checkbox" defaultChecked={acc.status === "active"} />
                  <span>Автопостинг включён</span>
                </label>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
