"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";
import type { PublishedPost } from "@/lib/types";

const statusLabels: Record<string, string> = {
  published: "Опубликовано", completed: "Завершено", scheduled: "Запланировано",
  failed: "Ошибка", draft: "Черновик", queued: "В очереди", pending: "Ожидает",
};

export default function HistoryPage() {
  const [posts, setPosts] = useState<PublishedPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const result = await apiFetch<PublishedPost[]>("/api/backend/publishing/history");
      setPosts(Array.isArray(result) ? result : []);
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
            История публикаций
          </h1>
          <p style={{ margin: "4px 0 0", color: "var(--ink-soft)", fontSize: "0.92rem" }}>
            Все опубликованные и запланированные посты
          </p>
        </div>
        <button className="button-ghost" type="button" onClick={() => load()} disabled={loading} style={{ minHeight: 40 }}>
          {loading ? "Загрузка..." : "Обновить"}
        </button>
      </header>

      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, padding: "80px 0", color: "var(--ink-faint)" }}>
          <div className="dash-loading-spinner" />
          <span style={{ fontSize: "0.95rem" }}>Загрузка истории...</span>
        </div>
      ) : error ? (
        <div className="error-banner">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>Повторить</button>
        </div>
      ) : !posts.length ? (
        <div className="empty-state" style={{ padding: "60px 28px" }}>
          <p style={{ fontSize: "0.95rem" }}>
            Публикаций пока нет. Создайте контент-план и запустите публикацию.
          </p>
        </div>
      ) : (
        <div className="timeline">
          {posts.map((post) => (
            <article key={post.publication_id} className="timeline-item" style={{ padding: 16, marginBottom: 8, background: "var(--surface)", borderRadius: 12, border: "1px solid var(--border)" }}>
              <header style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <strong>{platformIcons[post.platform.toLowerCase()] ?? "📄"} {post.platform}</strong>
                <span className={`status-pill ${post.status}`}>{statusLabels[post.status] ?? post.status}</span>
              </header>
              <div className="summary-list">
                <div className="summary-row">
                  <span>Запланировано</span>
                  <strong>{new Date(post.scheduled_at).toLocaleDateString("ru", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" })}</strong>
                </div>
                {post.published_at && (
                  <div className="summary-row">
                    <span>Опубликовано</span>
                    <strong>{new Date(post.published_at).toLocaleDateString("ru", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" })}</strong>
                  </div>
                )}
                {post.platform_post_id && (
                  <div className="summary-row">
                    <span>ID публикации</span>
                    <strong>{post.platform_post_id}</strong>
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
