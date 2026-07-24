"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import { apiFetch } from "@/lib/client";
import type { MvpContentPlanResponse } from "@/lib/types";

const PLATFORM_META: Record<
  string,
  { icon: string; label: string; color: string }
> = {
  instagram: { icon: "📱", label: "Instagram", color: "#E4405F" },
  telegram: { icon: "✈️", label: "Telegram", color: "#0088cc" },
  vk: { icon: "🌐", label: "VK", color: "#4C75A3" },
  youtube: { icon: "▶️", label: "YouTube", color: "#FF0000" },
  tiktok: { icon: "🎵", label: "TikTok", color: "#000000" },
  threads: { icon: "🧵", label: "Threads", color: "#101010" },
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  planned: "Запланировано",
  published: "Опубликовано",
};

const STATUS_VARIANTS: Record<string, string> = {
  draft: "badge",
  planned: "badge badge-active",
  published: "badge badge-admin",
};

function platformMeta(platform: string) {
  return (
    PLATFORM_META[platform.toLowerCase()] ?? {
      icon: "📄",
      label: platform,
      color: "var(--border)",
    }
  );
}

function statusLabel(status: string) {
  return STATUS_LABELS[status.toLowerCase()] ?? status;
}

function statusVariant(status: string) {
  return STATUS_VARIANTS[status.toLowerCase()] ?? "badge";
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleDateString("ru", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function LoadingSpinner() {
  return (
    <div className="empty-state" style={{ padding: "60px 28px" }}>
      <svg
        width="40"
        height="40"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{
          opacity: 0.3,
          animation: "spin 1s linear infinite",
        }}
      >
        <path d="M21 12a9 9 0 1 1-6.219-8.56" />
      </svg>
      <p>Загрузка плана публикаций...</p>
    </div>
  );
}

function EmptyState({ onGenerate }: { onGenerate: () => void }) {
  return (
    <div className="empty-state" style={{ padding: "60px 28px" }}>
      <div style={{ fontSize: "2.5rem", opacity: 0.4, marginBottom: 4 }}>
        📋
      </div>
      <h3
        style={{
          margin: 0,
          fontSize: "1.1rem",
          fontWeight: 600,
          color: "var(--ink)",
        }}
      >
        План публикаций ещё не создан
      </h3>
      <p>
        Сгенерируйте план на 30 дней — AI подберёт оптимальные даты и
        платформы для ваших материалов.
      </p>
      <button
        className="button-primary"
        type="button"
        onClick={onGenerate}
        style={{ marginTop: 8 }}
      >
        Создать план на 30 дней
      </button>
    </div>
  );
}

export default function ContentPlanPage() {
  const [data, setData] = useState<MvpContentPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, startGenerate] = useTransition();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result =
        await apiFetch<MvpContentPlanResponse>("/api/backend/content/plan");
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function generate() {
    setError(null);
    try {
      const result = await apiFetch<MvpContentPlanResponse>(
        "/api/backend/content/plan",
        {
          method: "POST",
          body: JSON.stringify({ period_days: 30, source_mode: "mixed" }),
        },
      );
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка генерации");
    }
  }

  const planStatusLabel = data
    ? statusLabel(data.status)
    : "";
  const planStatusVariant = data ? statusVariant(data.status) : "";

  return (
    <div className="content-page">
      {/* ── Header ── */}
      <div className="content-header">
        <div>
          <span className="eyebrow">Контент</span>
          <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700 }}>
            План публикаций
          </h1>
          <p
            style={{
              margin: "4px 0 0",
              color: "var(--ink-soft)",
              fontSize: "0.92rem",
            }}
          >
            Ежедневные публикации, сгенерированные AI под вашу стратегию
          </p>
        </div>
        <button
          className="button-primary"
          type="button"
          disabled={isGenerating}
          onClick={() => startGenerate(() => generate())}
        >
          {isGenerating ? (
            <>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ animation: "spin 1s linear infinite" }}
              >
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              Генерируем...
            </>
          ) : (
            <>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              Создать план на 30 дней
            </>
          )}
        </button>
      </div>

      {/* ── Error ── */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button
            className="button-ghost button-sm"
            type="button"
            onClick={() => load()}
          >
            Повторить
          </button>
        </div>
      )}

      {/* ── Loading ── */}
      {loading && <LoadingSpinner />}

      {/* ── Empty ── */}
      {!loading && !error && (!data || !data.items?.length) && (
        <EmptyState onGenerate={() => startGenerate(() => generate())} />
      )}

      {/* ── Plan ── */}
      {!loading && data && data.items?.length > 0 && (
        <>
          {/* Summary bar */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 12,
              flexWrap: "wrap",
              padding: "16px 20px",
              borderRadius: "var(--radius-lg)",
              background: "var(--surface)",
              border: "1px solid var(--border)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <div>
                <span
                  style={{
                    fontSize: "0.78rem",
                    fontWeight: 600,
                    color: "var(--ink-faint)",
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                  }}
                >
                  План на {data.period_days} дней
                </span>
                <p
                  style={{
                    margin: "2px 0 0",
                    fontSize: "0.85rem",
                    color: "var(--ink-soft)",
                  }}
                >
                  Источник:{" "}
                  {data.source_mode === "mixed"
                    ? "Смешанный"
                    : data.source_mode}
                </p>
              </div>
            </div>
            <span className={planStatusVariant}>{planStatusLabel}</span>
          </div>

          {/* Cards grid */}
          <div className="content-grid">
            {data.items.map((item) => {
              const meta = platformMeta(item.platform);
              return (
                <article
                  key={item.content_item_id}
                  className="content-card"
                  style={{
                    borderLeft: `4px solid ${meta.color}`,
                    borderTopLeftRadius: 0,
                    borderBottomLeftRadius: 0,
                  }}
                >
                  {/* Top row: platform + status */}
                  <div className="content-card-top">
                    <span className="content-card-type">
                      <span style={{ fontSize: "1.1rem" }}>{meta.icon}</span>
                      {meta.label}
                    </span>
                    <span className={statusVariant(item.status)}>
                      {statusLabel(item.status)}
                    </span>
                  </div>

                  {/* Content type + publish date */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 8,
                      fontSize: "0.82rem",
                      color: "var(--ink-faint)",
                      fontWeight: 500,
                    }}
                  >
                    <span>{item.content_type}</span>
                    <span>{formatDateTime(item.publish_at)}</span>
                  </div>

                  {/* Subtitle / text preview */}
                  <div className="content-card-text">
                    {item.text?.slice(0, 200)}
                    {item.text?.length > 200 ? "…" : ""}
                  </div>
                </article>
              );
            })}
          </div>
        </>
      )}

      {/* Spin animation keyframes */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
