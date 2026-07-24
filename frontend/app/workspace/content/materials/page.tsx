"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/client";

type ContentItem = {
  content_item_id: string;
  platform: string | null;
  content_type: string;
  title: string;
  text: string;
  status: string;
  created_at: string;
};

const PLATFORM_META: Record<string, { icon: string; label: string; color: string }> = {
  instagram: { icon: "📱", label: "Instagram", color: "#E4405F" },
  telegram: { icon: "✈️", label: "Telegram", color: "#0088CC" },
  vk: { icon: "🌐", label: "VK", color: "#0077FF" },
  youtube: { icon: "▶️", label: "YouTube", color: "#FF0000" },
  tiktok: { icon: "🎵", label: "TikTok", color: "#111111" },
  threads: { icon: "🧵", label: "Threads", color: "#101010" },
};

const TYPE_LABELS: Record<string, string> = {
  post: "Пост",
  story: "История",
  reels: "Reels",
  video: "Видео",
  carousel: "Карусель",
  article: "Статья",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  ready: "Готов",
  published: "Опубликован",
};

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export default function MaterialsPage() {
  const [items, setItems] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch<ContentItem[]>("/api/backend/content/materials");
      setItems(Array.isArray(result) ? result : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className="content-page">
        <div className="content-header">
          <div>
            <span className="eyebrow">Контент</span>
            <h1 className="dash-greeting">Мои материалы</h1>
          </div>
        </div>
        <div className="dash-loading">
          <div className="dash-loading-spinner" />
          <p>Загрузка материалов…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="content-page">
        <div className="content-header">
          <div>
            <span className="eyebrow">Контент</span>
            <h1 className="dash-greeting">Мои материалы</h1>
          </div>
        </div>
        <div className="error-banner">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={load}>
            Повторить
          </button>
        </div>
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="content-page">
        <div className="content-header">
          <div>
            <span className="eyebrow">Контент</span>
            <h1 className="dash-greeting">Мои материалы</h1>
          </div>
          <div className="dash-header-right">
            <Link href="/workspace/content/generator" className="button-primary">
              Создать материал
            </Link>
          </div>
        </div>
        <div className="empty-state" style={{ padding: "60px 28px" }}>
          <div className="empty-icon">📂</div>
          <p style={{ fontSize: "1rem", fontWeight: 600, color: "var(--ink)" }}>
            У вас пока нет сохранённых материалов
          </p>
          <p style={{ fontSize: "0.88rem", maxWidth: "40ch" }}>
            Создайте первый материал через генератор контента — ИИ поможет
            подготовить тексты для ваших соцсетей.
          </p>
          <Link
            href="/workspace/content/generator"
            className="button-primary"
            style={{ marginTop: 8 }}
          >
            Перейти в генератор
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="content-page">
      <div className="content-header">
        <div>
          <span className="eyebrow">Контент</span>
          <h1 className="dash-greeting">Мои материалы</h1>
          <p className="dash-subtitle">
            {items.length}{" "}
            {items.length === 1 ? "сохранённый материал" :
              items.length >= 2 && items.length <= 4 ? "сохранённых материала" :
                "сохранённых материалов"}
          </p>
        </div>
        <div className="dash-header-right">
          <Link href="/workspace/content/generator" className="button-primary">
            Создать материал
          </Link>
        </div>
      </div>

      <div className="content-grid stagger-grid">
        {items.map((item) => {
          const platform = item.platform?.toLowerCase() ?? "";
          const platformMeta = PLATFORM_META[platform] ?? {
            icon: "📄",
            label: item.platform ?? "Без платформы",
            color: "var(--ink-faint)",
          };
          const typeLabel = TYPE_LABELS[item.content_type] ?? item.content_type;
          const statusKey = item.status?.toLowerCase() ?? "draft";
          const statusLabel = STATUS_LABELS[statusKey] ?? item.status;
          const title =
            item.title?.trim() ||
            item.text?.split("\n")[0]?.trim()?.slice(0, 60) ||
            "Без названия";
          const textPreview = item.text?.slice(0, 150);
          const hasMore = item.text?.length > 150;

          return (
            <article
              key={item.content_item_id}
              className="content-card"
              style={{ borderLeft: `3px solid ${platformMeta.color}` }}
            >
              <div className="content-card-top">
                <div className="content-card-type">
                  <span style={{ fontSize: "1.1rem" }}>{platformMeta.icon}</span>
                  <span>{platformMeta.label}</span>
                  <span style={{ color: "var(--ink-faint)" }}>·</span>
                  <span>{typeLabel}</span>
                </div>
                <span className={`status-pill ${statusKey}`}>{statusLabel}</span>
              </div>

              <div className="content-card-title">{title}</div>

              <div className="content-card-text">
                {textPreview}
                {hasMore && "…"}
              </div>

              <div className="content-card-meta">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                  <line x1="16" y1="2" x2="16" y2="6" />
                  <line x1="8" y1="2" x2="8" y2="6" />
                  <line x1="3" y1="10" x2="21" y2="10" />
                </svg>
                <span>{formatDate(item.created_at)}</span>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
