"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/client";

type Message = {
  role: "user" | "assistant";
  content: string;
};

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4 20-7z" />
    </svg>
  );
}

function BotIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="10" rx="2" /><circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" /><path d="M8 16h8" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
    </svg>
  );
}

export default function AiAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Привет! Я AI-ассистент Нейры. Задай мне вопрос о маркетинге, контенте или стратегии." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [recsLoading, setRecsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadRecs = useCallback(async () => {
    try {
      const result = await apiFetch<{ recommendations: string[] } | Record<string, unknown>[]>("/api/backend/business/recommendations");
      if (Array.isArray(result)) {
        setRecommendations(result.map(r => typeof r === "string" ? r : JSON.stringify(r)));
      } else if (result && "recommendations" in result) {
        setRecommendations(result.recommendations as string[]);
      }
    } catch {
    }
    setRecsLoading(false);
  }, []);

  useEffect(() => { void loadRecs(); }, [loadRecs]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: "user", content: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await apiFetch<{ reply: string }>("/api/backend/ai-assistant/chat", {
        method: "POST",
        body: JSON.stringify({ message: userMsg.content }),
      });
      setMessages(prev => [...prev, { role: "assistant", content: res.reply }]);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "Не удалось получить ответ. Проверьте подключение AI-сервиса и попробуйте ещё раз." }]);
    }
    setLoading(false);
  }

  return (
    <div className="content-page">
      <header className="content-header">
        <div>
          <span className="eyebrow">AI-ассистент</span>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "4px 0 0" }}>
            AI-ассистент
          </h1>
          <p style={{ margin: "4px 0 0", color: "var(--ink-soft)", fontSize: "0.92rem" }}>
            Задайте вопрос о маркетинге, контент-стратегии или аудитории
          </p>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => setError(null)}>
            Закрыть
          </button>
        </div>
      )}

      <div className="detail-grid">
        <div className="stack">
          <div className="dash-card" style={{ padding: 0, minHeight: 500, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>
              {messages.map((msg, i) => (
                <div key={i} style={{
                  display: "flex", marginBottom: 16, gap: 10,
                  flexDirection: msg.role === "user" ? "row-reverse" : "row",
                  alignItems: "flex-start",
                }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: "50%", flexShrink: 0,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    background: msg.role === "user" ? "var(--accent)" : "var(--bg-secondary)",
                    color: msg.role === "user" ? "#fff" : "var(--ink)",
                  }}>
                    {msg.role === "user" ? <UserIcon /> : <BotIcon />}
                  </div>
                  <div style={{
                    maxWidth: "75%", padding: "10px 16px", borderRadius: 12,
                    background: msg.role === "user" ? "var(--accent)" : "var(--bg-secondary)",
                    color: msg.role === "user" ? "#fff" : "var(--ink)",
                    fontSize: 14, lineHeight: 1.5, whiteSpace: "pre-wrap",
                  }}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{ display: "flex", marginBottom: 12, gap: 10, alignItems: "flex-start" }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: "50%", flexShrink: 0,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    background: "var(--bg-secondary)", color: "var(--ink)",
                  }}>
                    <BotIcon />
                  </div>
                  <div style={{
                    padding: "10px 16px", borderRadius: 12,
                    background: "var(--bg-secondary)", fontSize: 14,
                  }}>
                    <span className="spinner" /> Думаю...
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border-color)" }}>
              <form onSubmit={e => { e.preventDefault(); sendMessage(); }} style={{ display: "flex", gap: 8 }}>
                <input
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder="Напишите сообщение..."
                  disabled={loading}
                  style={{
                    flex: 1, padding: "10px 14px", borderRadius: 8,
                    border: "1px solid var(--border-color)",
                    background: "var(--bg)", fontSize: 14,
                  }}
                />
                <button
                  className="button-primary"
                  type="submit"
                  disabled={loading || !input.trim()}
                  style={{ display: "flex", alignItems: "center", gap: 6, whiteSpace: "nowrap", minHeight: 40 }}
                >
                  <SendIcon /> Отправить
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="stack">
          <article className="insight-card">
            <div className="card-topline">
              <h3>Рекомендации</h3>
            </div>
            {recsLoading ? (
              <p className="dash-muted-text">Загрузка...</p>
            ) : recommendations.length === 0 ? (
              <p className="dash-muted-text">Подключите аналитику для получения рекомендаций.</p>
            ) : (
              <div className="step-list compact-list">
                {recommendations.slice(0, 5).map((rec, i) => (
                  <div key={i} className="step-item is-ready">
                    <span className="step-badge">{String(i + 1).padStart(2, "0")}</span>
                    <div><p>{rec}</p></div>
                  </div>
                ))}
              </div>
            )}
          </article>
        </div>
      </div>
    </div>
  );
}
