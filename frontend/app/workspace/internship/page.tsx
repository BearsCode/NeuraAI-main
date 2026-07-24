"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

type InternshipState = {
  state: string;
  current_stage: number;
  total_stages: number;
  stage_name: string;
  progress: number;
  started_at: string | null;
  completed_at: string | null;
};

const stageNames = [
  "Знакомство с брендом",
  "Анализ ниши",
  "Изучение аудитории",
  "Обучение тону коммуникации",
  "Тестовые публикации",
  "Финальное тестирование",
];

function RocketIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.4 }}>
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
      <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
      <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
      <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
    </svg>
  );
}

function CheckCircleIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.4 }}>
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
      <polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
  );
}

export default function InternshipPage() {
  const [state, setState] = useState<InternshipState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const result = await apiFetch<InternshipState>("/api/backend/internship/state");
      setState(result);
    } catch {
      setState(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function startInternship() {
    setStarting(true); setError(null);
    try {
      const result = await apiFetch<InternshipState>("/api/backend/internship/start", { method: "POST" });
      setState(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка запуска");
    }
    setStarting(false);
  }

  const isRunning = state && (state.state === "in_progress" || state.state === "active");
  const isComplete = state?.state === "completed";
  const isIdle = !state || state.state === "idle" || state.state === "not_started";

  return (
    <div className="dash-content">
      <header className="dash-header">
        <div className="dash-header-left">
          <h1 className="dash-greeting">AI-стажировка</h1>
          <p className="dash-subtitle">14-дневное обучение нейросети вашему бренду перед выходом в автономный режим.</p>
        </div>
      </header>

      {loading ? (
        <div className="dash-loading">
          <div className="dash-loading-spinner" />
          <span>Загрузка состояния стажировки...</span>
        </div>
      ) : error ? (
        <div className="error-banner top-spacer">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>Повторить</button>
        </div>
      ) : (
        <>
          <div className="dash-card" style={{ padding: 28 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 24 }}>
              <div style={{ flex: 1 }}>
                <h2 className="dash-section-title" style={{ marginBottom: 6 }}>
                  {isComplete ? "Стажировка пройдена" : isRunning ? `Этап ${state.current_stage} из ${state.total_stages}` : "Стажировка не начата"}
                </h2>
                <p className="dash-subtitle">
                  {isComplete
                    ? "Нейросеть обучена и готова к автономной работе."
                    : isRunning
                      ? `Текущий этап: ${state.stage_name || stageNames[state.current_stage - 1] || "Обучение"}`
                      : "Запустите 14-дневную стажировку, чтобы нейросеть изучила ваш бренд и научилась работать в вашем тоне."}
                </p>
              </div>
              {isIdle && (
                <button className="dash-btn dash-btn-primary" type="button" disabled={starting} onClick={() => startInternship()} style={{ flexShrink: 0 }}>
                  {starting ? "Запускаем..." : "Запустить стажировку"}
                </button>
              )}
            </div>

            {isRunning && (
              <div style={{ marginTop: 24 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: "0.88rem" }}>
                  <span style={{ color: "var(--ink-soft)" }}>Общий прогресс</span>
                  <strong>{Math.round(state.progress)}%</strong>
                </div>
                <div style={{ height: 10, background: "var(--bg-secondary)", borderRadius: 6, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${state.progress}%`, background: "linear-gradient(90deg, var(--accent), #60A5FA)", borderRadius: 6, transition: "width 0.6s ease" }} />
                </div>
              </div>
            )}
          </div>

          <div className="step-list">
            {stageNames.map((name, i) => {
              const stageNum = i + 1;
              const isDone = isComplete || (isRunning && stageNum < (state?.current_stage ?? 1));
              const isCurrent = isRunning && stageNum === (state?.current_stage ?? 1);
              return (
                <div key={name} className={`step-item ${isDone ? "is-ready" : ""}`} style={{
                  padding: "14px 18px", borderRadius: 12, border: isCurrent ? "1.5px solid var(--accent)" : "1px solid var(--border)",
                  background: isCurrent ? "rgba(59,130,246,0.04)" : undefined,
                  display: "flex", alignItems: "center", gap: 14, transition: "all 0.25s ease",
                }}>
                  <span className="step-badge" style={isCurrent ? { background: "var(--accent)", color: "#fff", borderColor: "var(--accent)" } : undefined}>
                    {String(stageNum).padStart(2, "0")}
                  </span>
                  <div style={{ flex: 1 }}>
                    <strong>{name}</strong>
                    {isCurrent && <span style={{ color: "var(--accent)", fontSize: 13, marginLeft: 8 }}>— текущий этап</span>}
                  </div>
                  {isDone && (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
