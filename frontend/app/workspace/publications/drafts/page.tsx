"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

type Draft = {
  id: string;
  platform: string;
  content_type: string;
  text: string;
  status: string;
  created_at: string;
  scheduled_at: string | null;
};

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const result = await apiFetch<Draft[]>("/api/backend/publishing/drafts");
      setDrafts(Array.isArray(result) ? result : []);
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
            Черновики
          </h1>
          <p style={{ margin: "4px 0 0", color: "var(--ink-soft)", fontSize: "0.92rem" }}>
            Неопубликованные материалы, ожидающие доработки или публикации
          </p>
        </div>
      </header>

      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, padding: "80px 0", color: "var(--ink-faint)" }}>
          <div className="dash-loading-spinner" />
          <span style={{ fontSize: "0.95rem" }}>Загрузка черновиков...</span>
        </div>
      ) : error ? (
        <div className="error-banner">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>Повторить</button>
        </div>
      ) : !drafts.length ? (
        <div className="empty-state" style={{ padding: "60px 28px" }}>
          <p style={{ fontSize: "0.95rem" }}>
            Черновиков пока нет. Создайте материал через генератор контента.
          </p>
        </div>
      ) : (
        <div className="detail-grid">
          {drafts.map((draft) => (
            <article key={draft.id} className="insight-card">
              <div className="card-topline">
                <div>
                  <h3>{platformIcons[draft.platform.toLowerCase()] ?? "📄"} {draft.content_type}</h3>
                  <span className="status-pill draft">Черновик</span>
                </div>
              </div>
              <p style={{ color: "var(--ink-soft)", fontSize: 14, marginTop: 8 }}>
                {draft.text?.slice(0, 200)}{draft.text?.length > 200 ? "..." : ""}
              </p>
              <div className="split-line" style={{ marginTop: 8 }}>
                <span>{draft.platform}</span>
                <span>{new Date(draft.created_at).toLocaleDateString("ru")}</span>
              </div>
              <div className="action-row top-spacer">
                <button className="button-secondary" type="button" style={{ minHeight: 32, fontSize: "0.82rem" }}>Редактировать</button>
                <button className="button-ghost" type="button" style={{ minHeight: 32, fontSize: "0.82rem" }}>Опубликовать</button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
