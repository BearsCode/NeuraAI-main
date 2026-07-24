"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import { apiFetch } from "@/lib/client";
import type { MvpStrategyResponse } from "@/lib/types";

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  draft: { label: "Черновик", className: "badge" },
  completed: { label: "Готово", className: "badge badge-active" },
  generating: { label: "В работе", className: "badge" },
  processing: { label: "В работе", className: "badge" },
};

function formatRecord(value: Record<string, unknown> | string): string {
  if (typeof value === "string") return value;
  if (!value || Object.keys(value).length === 0) return "";
  return Object.entries(value)
    .map(([k, v]) => {
      const val = typeof v === "object" && v !== null ? JSON.stringify(v, null, 2) : String(v);
      return `${k}: ${val}`;
    })
    .join("\n\n");
}

function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat("ru-RU", {
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export default function StrategyPage() {
  const [data, setData] = useState<MvpStrategyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, startGenerate] = useTransition();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch<MvpStrategyResponse>(
        "/api/backend/business/strategy"
      );
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
      await apiFetch<{ task_id: string }>(
        "/api/backend/business/strategy",
        { method: "POST" }
      );
      let attempts = 0;
      while (attempts < 30) {
        await new Promise((r) => setTimeout(r, 2000));
        try {
          const result = await apiFetch<MvpStrategyResponse>(
            "/api/backend/business/strategy"
          );
          if (result.strategy_id && result.status === "completed") {
            setData(result);
            return;
          }
        } catch {
          /* retry */
        }
        attempts++;
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка генерации");
    }
  }

  const statusInfo = data?.status ? STATUS_MAP[data.status] : null;

  if (loading) {
    return (
      <div className="content-page">
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, padding: "80px 0", color: "var(--ink-faint)" }}>
          <div className="dash-loading-spinner" />
          <span style={{ fontSize: "0.95rem" }}>Загрузка стратегии...</span>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="content-page">
        <div className="strategy-empty">
          <div className="strategy-empty-icon">!</div>
          <h3>Ошибка загрузки</h3>
          <p>{error}</p>
          <button className="button-secondary" type="button" onClick={() => load()}>
            Повторить
          </button>
        </div>
      </div>
    );
  }

  const isEmpty = !data || !data.strategy_id;

  return (
    <div className="content-page">
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <div>
          <span className="eyebrow">Маркетинговая стратегия</span>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, letterSpacing: "-0.03em", marginTop: 4 }}>
            AI-стратегия
          </h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {statusInfo && <span className={statusInfo.className}>{statusInfo.label}</span>}
          {!isEmpty && (
            <button
              className="button-primary"
              type="button"
              disabled={isGenerating}
              onClick={() => startGenerate(() => generate())}
            >
              {isGenerating ? "Генерируем…" : "Запустить AI-стратегию"}
            </button>
          )}
        </div>
      </header>

      {isGenerating && (
        <div className="strategy-section" style={{ alignItems: "center", padding: "32px 20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div className="dash-loading-spinner" />
            <span style={{ color: "var(--ink-soft)", fontSize: "0.95rem", fontWeight: 500 }}>
              AI анализирует ваш бизнес…
            </span>
          </div>
        </div>
      )}

      {error && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "var(--radius-sm)",
            background: "var(--error-soft)",
            color: "var(--error)",
            fontSize: "0.88rem",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span>{error}</span>
        </div>
      )}

      {isEmpty ? (
        <div className="strategy-empty">
          <div className="strategy-empty-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
          </div>
          <h3>Стратегия ещё не создана</h3>
          <p>
            Запустите AI-анализ вашего бизнеса. Нейра изучит рынок, конкурентов и предложит
            стратегию продвижения.
          </p>
          <button
            className="button-primary"
            type="button"
            disabled={isGenerating}
            onClick={() => startGenerate(() => generate())}
          >
            {isGenerating ? "Генерируем…" : "Запустить AI-стратегию"}
          </button>
        </div>
      ) : (
        <>
          <div className="strategy-grid">
            <div className="strategy-section">
              <h2 className="strategy-section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                Анализ рынка
              </h2>
              <div className="strategy-section-content" style={{ whiteSpace: "normal" }}>
                {data.market_analysis?.length > 0 ? (
                  <ul style={{ margin: 0, paddingLeft: 18, display: "flex", flexDirection: "column", gap: 6 }}>
                    {data.market_analysis.map((item, i) => (
                      <li key={i} style={{ lineHeight: 1.6 }}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <span style={{ color: "var(--ink-faint)" }}>Нет данных</span>
                )}
              </div>
            </div>

            <div className="strategy-section">
              <h2 className="strategy-section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                  <circle cx="9" cy="7" r="4" />
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                  <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                </svg>
                Конкуренты
              </h2>
              <div className="strategy-section-content" style={{ whiteSpace: "normal" }}>
                {(data as unknown as Record<string, unknown>).competitors
                  ? ((data as unknown as Record<string, string[]>).competitors?.length ?? 0) > 0 ? (
                    <ul style={{ margin: 0, paddingLeft: 18, display: "flex", flexDirection: "column", gap: 6 }}>
                      {(data as unknown as Record<string, string[]>).competitors!.map((item, i) => (
                        <li key={i} style={{ lineHeight: 1.6 }}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <span style={{ color: "var(--ink-faint)" }}>Нет данных</span>
                  )
                  : data.competitor_analysis?.length > 0 ? (
                    <ul style={{ margin: 0, paddingLeft: 18, display: "flex", flexDirection: "column", gap: 6 }}>
                      {data.competitor_analysis.map((item, i) => (
                        <li key={i} style={{ lineHeight: 1.6 }}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <span style={{ color: "var(--ink-faint)" }}>Нет данных</span>
                  )}
              </div>
            </div>
          </div>

          <div className="strategy-grid">
            <div className="strategy-section" style={{ gridColumn: "1 / -1" }}>
              <h2 className="strategy-section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 20h9" />
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                </svg>
                Стратегический план
              </h2>
              <div className="strategy-section-content">
                {data.strategy_plan && Object.keys(data.strategy_plan).length > 0
                  ? formatRecord(data.strategy_plan)
                  : "План появится после генерации стратегии."}
              </div>
            </div>
          </div>

          <div className="strategy-grid">
            <div className="strategy-section" style={{ gridColumn: "1 / -1" }}>
              <h2 className="strategy-section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                  <line x1="8" y1="21" x2="16" y2="21" />
                  <line x1="12" y1="17" x2="12" y2="21" />
                </svg>
                Контент-стратегия
              </h2>
              <div className="strategy-section-content">
                {data.content_strategy && Object.keys(data.content_strategy).length > 0
                  ? formatRecord(data.content_strategy)
                  : "Контент-стратегия появится после генерации."}
              </div>
            </div>
          </div>

          <div style={{ fontSize: "0.82rem", color: "var(--ink-faint)", textAlign: "center" }}>
            Создано: {formatDate((data as unknown as Record<string, string>).created_at ?? new Date().toISOString())}
          </div>
        </>
      )}
    </div>
  );
}
