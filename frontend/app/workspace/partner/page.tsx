"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";
import type { PartnerDashboardData } from "@/lib/types";

function formatIncome(value: number): string {
  return value.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function PartnerPage() {
  const [data, setData] = useState<PartnerDashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const load = useCallback(async () => {
    try {
      const result = await apiFetch<PartnerDashboardData>("/api/backend/partner/dashboard");
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const copyLink = useCallback(async () => {
    if (!data?.referral_link) return;
    try {
      await navigator.clipboard.writeText(data.referral_link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const input = document.createElement("input");
      input.value = data.referral_link;
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      document.body.removeChild(input);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [data]);

  return (
    <div className="content-page">
      <header className="content-header">
        <div>
          <span className="eyebrow">Партнёрская программа</span>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "4px 0 0" }}>
            Партнёрская программа
          </h1>
          <p style={{ margin: "4px 0 0", color: "var(--ink-soft)", fontSize: "0.92rem" }}>
            Приглашайте друзей и получайте {data ? Math.round((data.commission_rate ?? 0.1) * 100) : "..."}% от их платежей
          </p>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>Повторить</button>
        </div>
      )}

      {!data && !error && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, padding: "80px 0", color: "var(--ink-faint)" }}>
          <div className="dash-loading-spinner" />
          <span style={{ fontSize: "0.95rem" }}>Загрузка...</span>
        </div>
      )}

      {data && (
        <>
          <div className="analytics-kpi-grid">
            <article className="analytics-kpi-card" style={{ background: "rgba(59,130,246,0.08)", borderColor: "transparent" }}>
              <div className="analytics-kpi-label" style={{ color: "#3B82F6" }}>Приглашено</div>
              <div className="analytics-kpi-value" style={{ color: "var(--ink)" }}>{data.total_referrals}</div>
            </article>
            <article className="analytics-kpi-card" style={{ background: "rgba(16,185,129,0.08)", borderColor: "transparent" }}>
              <div className="analytics-kpi-label" style={{ color: "#10B981" }}>Активных подписок</div>
              <div className="analytics-kpi-value" style={{ color: "var(--ink)" }}>{data.successful_payments_count}</div>
            </article>
            <article className="analytics-kpi-card" style={{ background: "rgba(245,158,11,0.08)", borderColor: "transparent" }}>
              <div className="analytics-kpi-label" style={{ color: "#F59E0B" }}>Заработано</div>
              <div className="analytics-kpi-value" style={{ color: "var(--success)" }}>{formatIncome(data.total_commission)} ₽</div>
            </article>
            <article className="analytics-kpi-card" style={{ background: "rgba(139,92,246,0.08)", borderColor: "transparent" }}>
              <div className="analytics-kpi-label" style={{ color: "#8B5CF6" }}>Доступно к выплате</div>
              <div className="analytics-kpi-value" style={{ color: "var(--accent)" }}>{formatIncome(data.available_balance)} ₽</div>
            </article>
          </div>

          <div className="partner-link-section">
            <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--ink)", margin: 0 }}>Ваша реферальная ссылка</h2>
            <div className="partner-link-row">
              <input className="partner-link-input" type="text" value={data.referral_link} readOnly onClick={(e) => (e.target as HTMLInputElement).select()} />
              <button className="button-primary" onClick={copyLink} type="button" style={{ minHeight: 44, whiteSpace: "nowrap" }}>
                {copied ? "Скопировано" : "Копировать"}
              </button>
            </div>
          </div>

          <div className="partner-footer">
            <Link href="/workspace/settings" className="partner-footer-link">Настройки профиля →</Link>
          </div>
        </>
      )}
    </div>
  );
}
