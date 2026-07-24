"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

type AudienceData = {
  total_followers: number;
  demographics: Record<string, number>;
  top_locations: string[];
  active_hours: number[];
  interests: string[];
};

export default function AudiencePage() {
  const [data, setData] = useState<AudienceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const result = await apiFetch<AudienceData>("/api/backend/analytics/audience");
      setData(result);
    } catch {
      setData(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="content-page">
      <header className="content-header">
        <div>
          <span className="eyebrow">Аналитика</span>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "4px 0 0" }}>
            Аудитория
          </h1>
          <p style={{ margin: "4px 0 0", color: "var(--ink-soft)", fontSize: "0.92rem" }}>
            Демография, интересы и поведение ваших подписчиков
          </p>
        </div>
      </header>

      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, padding: "80px 0", color: "var(--ink-faint)" }}>
          <div className="dash-loading-spinner" />
          <span style={{ fontSize: "0.95rem" }}>Загрузка данных об аудитории...</span>
        </div>
      ) : error ? (
        <div className="error-banner">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>Повторить</button>
        </div>
      ) : !data ? (
        <div className="empty-state" style={{ padding: "60px 28px" }}>
          <p style={{ fontSize: "0.95rem" }}>
            Подключите социальные сети, чтобы увидеть данные об аудитории
          </p>
        </div>
      ) : (
        <div className="detail-grid">
          <article className="insight-card">
            <h3 className="dash-section-title">Подписчики</h3>
            <div className="signal-value" style={{ fontSize: 36 }}>
              {(data.total_followers ?? 0).toLocaleString()}
            </div>
          </article>

          {data.demographics && Object.keys(data.demographics).length > 0 && (
            <article className="insight-card">
              <h3 className="dash-section-title">Демография</h3>
              <div className="summary-list">
                {Object.entries(data.demographics).map(([key, val]) => (
                  <div key={key} className="summary-row">
                    <span>{key}</span>
                    <strong>{val}%</strong>
                  </div>
                ))}
              </div>
            </article>
          )}

          {data.interests?.length > 0 && (
            <article className="insight-card">
              <h3 className="dash-section-title">Интересы</h3>
              <div className="chip-row">
                {data.interests.map((interest) => (
                  <span key={interest} className="chip">{interest}</span>
                ))}
              </div>
            </article>
          )}

          {data.top_locations?.length > 0 && (
            <article className="insight-card">
              <h3 className="dash-section-title">Топ-локации</h3>
              <div className="chip-row">
                {data.top_locations.map((loc) => (
                  <span key={loc} className="chip">{loc}</span>
                ))}
              </div>
            </article>
          )}
        </div>
      )}
    </div>
  );
}
