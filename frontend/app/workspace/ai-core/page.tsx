"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

type CoreStatus = {
  mode: string;
  startup_phase: string;
  health: string;
  pipelines_active: number;
  pipelines_queued: number;
  pipelines_completed: number;
  pipelines_failed: number;
  uptime_seconds: number;
};

type Pipeline = {
  id: string;
  name: string;
  status: string;
  progress: number;
  started_at: string;
};

function CpuIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.35 }}>
      <rect x="4" y="4" width="16" height="16" rx="2" ry="2"/>
      <rect x="9" y="9" width="6" height="6"/>
      <line x1="9" y1="1" x2="9" y2="4"/>
      <line x1="15" y1="1" x2="15" y2="4"/>
      <line x1="9" y1="20" x2="9" y2="23"/>
      <line x1="15" y1="20" x2="15" y2="23"/>
      <line x1="20" y1="9" x2="23" y2="9"/>
      <line x1="20" y1="14" x2="23" y2="14"/>
      <line x1="1" y1="9" x2="4" y2="9"/>
      <line x1="1" y1="14" x2="4" y2="14"/>
    </svg>
  );
}

export default function AiCorePage() {
  const [status, setStatus] = useState<CoreStatus | null>(null);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [s, p] = await Promise.all([
        apiFetch<CoreStatus>("/api/backend/ai-core/status").catch(() => null),
        apiFetch<Pipeline[]>("/api/backend/ai-core/pipelines").catch(() => [] as Pipeline[]),
      ]);
      setStatus(s);
      setPipelines(Array.isArray(p) ? p : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : null);
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const modeLabels: Record<string, string> = {
    auto: "Автономный",
    semi: "Полуавтоматический",
    manual: "Ручной",
    internship: "Стажировка",
  };

  const statusLabels: Record<string, string> = {
    active: "Активен", running: "Выполняется", completed: "Завершён", failed: "Ошибка", queued: "В очереди",
  };

  function formatUptime(seconds: number) {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${d}д ${h}ч ${m}м`;
  }

  return (
    <div className="dash-content">
      <header className="dash-header">
        <div className="dash-header-left">
          <h1 className="dash-greeting">AI Core</h1>
          <p className="dash-subtitle">Управление и мониторинг AI-пайплайнов и режимов работы.</p>
        </div>
        <div className="dash-header-right">
          <button className="dash-btn dash-btn-ghost" type="button" onClick={() => load()} disabled={loading}>
            {loading ? "Загрузка..." : "Обновить"}
          </button>
        </div>
      </header>

      {loading ? (
        <div className="dash-loading">
          <div className="dash-loading-spinner" />
          <span>Загрузка состояния AI Core...</span>
        </div>
      ) : error ? (
        <div className="error-banner top-spacer">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>Повторить</button>
        </div>
      ) : (
        <>
          {status && (
            <div className="dash-kpi-row">
              <article className="dash-card dash-kpi-card">
                <div className="dash-kpi-value" style={{ fontSize: 20 }}>{modeLabels[status.mode] ?? status.mode}</div>
                <div className="dash-kpi-label">Режим работы</div>
              </article>
              <article className="dash-card dash-kpi-card">
                <div className="dash-kpi-value" style={{ fontSize: 20, color: status.health === "healthy" ? "var(--success)" : "var(--danger)" }}>
                  {status.health === "healthy" ? "✓ Здоров" : "✗ Проблемы"}
                </div>
                <div className="dash-kpi-label">Состояние</div>
              </article>
              <article className="dash-card dash-kpi-card">
                <div className="dash-kpi-value">{status.pipelines_active}</div>
                <div className="dash-kpi-label">Активных пайплайнов</div>
              </article>
              <article className="dash-card dash-kpi-card">
                <div className="dash-kpi-value">{status.uptime_seconds ? formatUptime(status.uptime_seconds) : "—"}</div>
                <div className="dash-kpi-label">Аптайм</div>
              </article>
            </div>
          )}

          {pipelines.length > 0 && (
            <div className="dash-card" style={{ padding: 24 }}>
              <div className="dash-card-header" style={{ marginBottom: 16 }}>
                <h2 className="dash-section-title">Пайплайны</h2>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {pipelines.map((p) => (
                  <article key={p.id} style={{ padding: "14px 16px", border: "1px solid var(--border)", borderRadius: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                      <strong>{p.name}</strong>
                      <span className={`status-pill ${p.status}`}>{statusLabels[p.status] ?? p.status}</span>
                    </div>
                    {p.status === "running" && (
                      <div style={{ height: 4, background: "var(--bg-secondary)", borderRadius: 2, overflow: "hidden", marginBottom: 4 }}>
                        <div style={{ height: "100%", width: `${p.progress}%`, background: "linear-gradient(90deg, var(--accent), #60A5FA)", borderRadius: 2, transition: "width 0.5s ease" }} />
                      </div>
                    )}
                    <p style={{ fontSize: 12, color: "var(--ink-faint)", margin: 0 }}>
                      {new Date(p.started_at).toLocaleDateString("ru", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          )}

          {!pipelines.length && status && (
            <div className="dash-card" style={{ padding: 40, textAlign: "center" }}>
              <CpuIcon />
              <p style={{ marginTop: 12, color: "var(--ink-faint)", fontSize: "0.92rem" }}>
                Нет активных пайплайнов. Система ожидает задач.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
