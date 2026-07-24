"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";
import type { AnalyticsSummary } from "@/lib/types";

function IconUsers() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
function IconEye() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}
function IconHeart() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  );
}
function IconMessageCircle() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}
function IconBookmark() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
    </svg>
  );
}
function IconLink() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  );
}
function IconBarChart() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}
function IconRefresh() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  );
}
function IconChartNoData() {
  return (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" opacity="0.4">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
      <line x1="2" y1="2" x2="22" y2="22" />
    </svg>
  );
}

const PERIODS = [
  { value: "30d", label: "30 дней" },
] as const;

type Period = (typeof PERIODS)[number]["value"];

interface KpiCardDef {
  key: keyof AnalyticsSummary;
  label: string;
  icon: React.ComponentType;
  accent: string;
  bg: string;
}

const KPI_CARDS: KpiCardDef[] = [
  { key: "followers", label: "Подписчики", icon: IconUsers, accent: "#3B82F6", bg: "rgba(59,130,246,0.08)" },
  { key: "impressions", label: "Охваты", icon: IconEye, accent: "#8B5CF6", bg: "rgba(139,92,246,0.08)" },
  { key: "likes", label: "Лайки", icon: IconHeart, accent: "#EC4899", bg: "rgba(236,72,153,0.08)" },
  { key: "comments", label: "Комментарии", icon: IconMessageCircle, accent: "#F59E0B", bg: "rgba(245,158,11,0.08)" },
  { key: "saves", label: "Сохранения", icon: IconBookmark, accent: "#10B981", bg: "rgba(16,185,129,0.08)" },
  { key: "ctr", label: "CTR", icon: IconLink, accent: "#06B6D4", bg: "rgba(6,182,212,0.08)" },
  { key: "er", label: "Вовлеченность", icon: IconBarChart, accent: "#F97316", bg: "rgba(249,115,22,0.08)" },
];

function formatNumber(n: number): string {
  if (Number.isNaN(n)) return "—";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, "") + "K";
  return n.toLocaleString();
}

function formatPercent(n: number): string {
  return n.toFixed(1) + "%";
}

function renderValue(key: keyof AnalyticsSummary, val: number | undefined): string {
  if (val == null) return "—";
  if (key === "ctr" || key === "er") return formatPercent(val);
  return formatNumber(val);
}

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<Period>("30d");
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch<AnalyticsSummary>("/api/backend/analytics/summary");
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const hasData = data !== null && Object.values(data).some((v) => typeof v === "number" && v > 0);

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div>
          <span className="eyebrow">Аналитика</span>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "4px 0 0" }}>
            Ключевые показатели
          </h1>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div className="analytics-period">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                className={`analytics-period-btn${period === p.value ? " active" : ""}`}
                onClick={() => setPeriod(p.value)}
              >
                {p.label}
              </button>
            ))}
          </div>
          <button
            className="button-secondary"
            style={{ minHeight: 36, padding: "0 14px", fontSize: "0.82rem" }}
            type="button"
            onClick={() => load()}
            disabled={loading}
          >
            <IconRefresh />
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, padding: "80px 0", color: "var(--ink-faint)" }}>
          <div className="dash-loading-spinner" />
          <span style={{ fontSize: "0.95rem" }}>Загрузка аналитики...</span>
        </div>
      ) : error ? (
        <div className="error-banner" style={{ margin: 0 }}>
          <span className="error-icon">!</span>
          <span>Ошибка загрузки. {error.toLowerCase().includes("profile not found") || error.toLowerCase().includes("business") ? "Создайте компанию в настройках профиля." : error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>
            Повторить
          </button>
        </div>
      ) : !hasData ? (
        <div className="empty-state" style={{ padding: "60px 28px" }}>
          <IconChartNoData />
          <p style={{ fontSize: "0.95rem" }}>
            Подключите социальные сети, чтобы увидеть аналитику
          </p>
        </div>
      ) : (
        <>
          <div className="analytics-kpi-grid">
            {KPI_CARDS.map((cfg) => {
              const val = data?.[cfg.key];
              const numericVal = typeof val === "number" ? val : 0;
              return (
                <article
                  key={cfg.key}
                  className="analytics-kpi-card"
                  style={{ background: cfg.bg, borderColor: "transparent" }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                    <span style={{ color: cfg.accent, display: "flex" }}>
                      <cfg.icon />
                    </span>
                  </div>
                  <div className="analytics-kpi-label" style={{ color: cfg.accent }}>
                    {cfg.label}
                  </div>
                  <div className="analytics-kpi-value" style={{ color: "var(--ink)" }}>
                    {renderValue(cfg.key, numericVal)}
                  </div>
                </article>
              );
            })}
          </div>

          <section className="analytics-detail-section">
            <h2 style={{ fontSize: "1rem", fontWeight: 700, letterSpacing: "-0.01em" }}>
              Детальная аналитика
            </h2>
            <div className="analytics-detail-grid">
              {KPI_CARDS.map((cfg) => {
                const val = data?.[cfg.key];
                const numericVal = typeof val === "number" ? val : 0;
                return (
                  <div key={cfg.key} className="analytics-detail-item">
                    <span className="analytics-detail-label">{cfg.label}</span>
                    <span className="analytics-detail-value">{renderValue(cfg.key, numericVal)}</span>
                  </div>
                );
              })}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
