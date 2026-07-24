"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/client";
import type { SocialAccount } from "@/lib/types";

const PLATFORMS = [
  { value: "instagram", label: "Instagram", color: "#E4405F" },
  { value: "telegram", label: "Telegram", color: "#0088CC" },
  { value: "vk", label: "VK", color: "#0077FF" },
  { value: "youtube", label: "YouTube", color: "#FF0000" },
  { value: "tiktok", label: "TikTok", color: "#111111" },
  { value: "threads", label: "Threads", color: "#101010" },
];

const CONTENT_TYPES = [
  { value: "post", label: "Пост" },
  { value: "story", label: "История" },
  { value: "reels", label: "Reels" },
  { value: "video", label: "Видео" },
  { value: "carousel", label: "Карусель" },
  { value: "article", label: "Статья" },
];

const TONES = [
  { value: "professional", label: "Профессиональный" },
  { value: "casual", label: "Непринуждённый" },
  { value: "inspirational", label: "Вдохновляющий" },
  { value: "humorous", label: "Юмористический" },
  { value: "educational", label: "Обучающий" },
  { value: "persuasive", label: "Убедительный" },
];

function SkeletonCard() {
  return (
    <div className="generator-result-card" style={{ gap: 20 }}>
      <div className="skeleton skeleton-heading" style={{ width: "40%" }} />
      <div className="skeleton skeleton-text" />
      <div className="skeleton skeleton-text" />
      <div className="skeleton skeleton-text-short" />
      <div className="skeleton skeleton-text" style={{ width: "90%" }} />
      <div className="skeleton skeleton-text-short" />
      <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
        <div className="skeleton skeleton-pill" style={{ width: 120 }} />
        <div className="skeleton skeleton-pill" style={{ width: 160 }} />
      </div>
    </div>
  );
}

export default function GeneratorPage() {
  const [prompt, setPrompt] = useState("");
  const [topic, setTopic] = useState("");
  const [keywords, setKeywords] = useState("");
  const [platform, setPlatform] = useState("instagram");
  const [contentType, setContentType] = useState("post");
  const [tone, setTone] = useState("professional");
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [socials, setSocials] = useState<SocialAccount[]>([]);
  const [socialsLoading, setSocialsLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setSocialsLoading(true);
    apiFetch<SocialAccount[]>("/api/backend/social")
      .then((data) => {
        setSocials(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        setSocials([]);
      })
      .finally(() => setSocialsLoading(false));
  }, []);

  const isConnected = useMemo(() => {
    if (socialsLoading) return null;
    return socials.some((s) => s.platform === platform && s.status === "active");
  }, [socials, platform, socialsLoading]);

  const generate = useCallback(async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await apiFetch<{ text: string }>("/api/backend/content/generate", {
        method: "POST",
        body: JSON.stringify({
          prompt: prompt.trim(),
          platform,
          content_type: contentType,
          tone,
          topic: topic.trim(),
          keywords: keywords.trim(),
        }),
      });
      setResult(res.text);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка генерации контента");
    }
    setLoading(false);
  }, [prompt, platform, contentType, tone, topic, keywords]);

  const handleCopy = useCallback(async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = result;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [result]);

  const handleSave = useCallback(async () => {
    if (!result) return;
    setSaving(true);
    try {
      await apiFetch("/api/backend/content/materials", {
        method: "POST",
        body: JSON.stringify({
          text: result,
          platform,
          content_type: contentType,
          title: prompt.trim().slice(0, 80),
        }),
      });
      setSaving(false);
    } catch {
      setSaving(false);
    }
  }, [result, platform, contentType, prompt]);

  const platformLabel = useMemo(
    () => PLATFORMS.find((p) => p.value === platform)?.label ?? platform,
    [platform],
  );

  const contentTypeLabel = useMemo(
    () => CONTENT_TYPES.find((t) => t.value === contentType)?.label ?? contentType,
    [contentType],
  );

  return (
    <div className="content-page">
      {/* ── Hero Header ── */}
      <div
        style={{
          position: "relative",
          overflow: "hidden",
          borderRadius: "var(--radius-lg)",
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
          border: "1px solid rgba(59,130,246,0.15)",
          padding: "36px 40px",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "radial-gradient(600px circle at 20% 50%, rgba(59,130,246,0.08) 0%, transparent 60%), radial-gradient(400px circle at 80% 20%, rgba(139,92,246,0.06) 0%, transparent 50%)",
            pointerEvents: "none",
          }}
        />
        <div style={{ position: "relative", display: "flex", alignItems: "center", gap: 24, flexWrap: "wrap", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: "var(--radius-md)",
                background: "linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))",
                border: "1px solid rgba(59,130,246,0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 3a6 6 0 0 0-6 6c0 2.5 1.5 4.5 3 6l3 4 3-4c1.5-1.5 3-3.5 3-6a6 6 0 0 0-6-6z" />
                <circle cx="12" cy="9" r="2" />
              </svg>
            </div>
            <div>
              <span style={{ fontSize: "0.78rem", fontWeight: 600, color: "rgba(96,165,250,0.8)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                AI-генератор контента
              </span>
              <h1 className="dash-greeting" style={{ color: "#f1f5f9", marginTop: 4 }}>
                Создайте идеальный текст
              </h1>
              <p className="dash-subtitle" style={{ color: "rgba(148,163,184,0.9)", fontSize: "0.92rem" }}>
                Искусственный интеллект напишет публикацию под вашу платформу и аудиторию за секунды
              </p>
            </div>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "6px 14px 6px 10px",
              borderRadius: "var(--radius-pill)",
              background: "rgba(59,130,246,0.1)",
              border: "1px solid rgba(59,130,246,0.15)",
              fontSize: "0.78rem",
              color: "rgba(148,163,184,0.9)",
              fontWeight: 500,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>
            GPT-4 Turbo
          </div>
        </div>
      </div>

      {/* ── Main Layout ── */}
      <div className="generator-layout">
        {/* ══ Left: Form ══ */}
        <div className="generator-form-section">
          <div className="generator-form-card">
            {/* Platform + Content Type */}
            <div className="field-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
              <div className="field">
                <label htmlFor="gen-platform">Платформа</label>
                <select
                  id="gen-platform"
                  value={platform}
                  onChange={(e) => setPlatform(e.target.value)}
                >
                  {PLATFORMS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="gen-type">Тип контента</label>
                <select
                  id="gen-type"
                  value={contentType}
                  onChange={(e) => setContentType(e.target.value)}
                >
                  {CONTENT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Tone + Topic */}
            <div className="field-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
              <div className="field">
                <label htmlFor="gen-tone">Тон текста</label>
                <select
                  id="gen-tone"
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                >
                  {TONES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="gen-topic">Тема</label>
                <input
                  id="gen-topic"
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Например: запуск продукта"
                />
              </div>
            </div>

            {/* Keywords */}
            <div className="field">
              <label htmlFor="gen-keywords">Ключевые слова</label>
              <input
                id="gen-keywords"
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="Через запятую: инновация, качество, стиль"
              />
            </div>

            {/* Prompt */}
            <div className="field">
              <label htmlFor="gen-prompt">Описание публикации</label>
              <textarea
                id="gen-prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Опишите, о чём должен быть текст. Например: расскажи о новой коллекции весна-лето 2026 в формате сторителлинга с акцентом на экологичность"
                rows={5}
                style={{ minHeight: 110 }}
              />
            </div>

            {/* Social connection */}
            {socialsLoading ? (
              <div
                className="generator-social-check"
                style={{ background: "var(--bg-secondary)", color: "var(--ink-faint)" }}
              >
                <span style={{ opacity: 0.5 }}>Проверка подключения...</span>
              </div>
            ) : isConnected ? (
              <div className="generator-social-check connected">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M5 8.5L7 10.5L11 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {platformLabel} подключён
              </div>
            ) : (
              <div className="generator-social-check disconnected">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M6 6L10 10M10 6L6 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                {platformLabel} не подключён
                <a
                  href="/workspace/integrations"
                  className="button-ghost button-sm"
                  style={{ marginLeft: "auto" }}
                >
                  Настроить
                </a>
              </div>
            )}

            {/* Generate button */}
            <button
              className="button-primary"
              type="button"
              disabled={loading || !prompt.trim()}
              onClick={generate}
              style={{ width: "100%", minHeight: 52, fontSize: "1rem" }}
            >
              {loading ? (
                <>
                  <span className="dash-loading-spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
                  Генерируем...
                </>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 3a6 6 0 0 0-6 6c0 2.5 1.5 4.5 3 6l3 4 3-4c1.5-1.5 3-3.5 3-6a6 6 0 0 0-6-6z" />
                    <circle cx="12" cy="9" r="2" />
                  </svg>
                  Сгенерировать контент
                </>
              )}
            </button>

            {/* Error */}
            {error && (
              <div className="error-banner" style={{ margin: 0 }}>
                <span className="error-icon">!</span>
                <span>{error}</span>
              </div>
            )}
          </div>
        </div>

        {/* ══ Right: Result / Preview ══ */}
        <div className="generator-result-section">
          {loading ? (
            <SkeletonCard />
          ) : result ? (
            <div className="generator-result-card" style={{ gap: 16 }}>
              {/* Meta badge */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                      padding: "4px 12px",
                      borderRadius: "var(--radius-pill)",
                      background: "var(--surface-muted)",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      color: "var(--ink-soft)",
                    }}
                  >
                    <span
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: PLATFORMS.find((p) => p.value === platform)?.color ?? "var(--ink-faint)",
                        flexShrink: 0,
                      }}
                    />
                    {platformLabel}
                  </span>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 500,
                      color: "var(--ink-faint)",
                    }}
                  >
                    {contentTypeLabel}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: "0.72rem",
                    fontWeight: 500,
                    color: "var(--ink-faint)",
                    padding: "4px 10px",
                    borderRadius: "var(--radius-pill)",
                    background: "var(--surface-muted)",
                  }}
                >
                  {TONES.find((t) => t.value === tone)?.label ?? tone}
                </span>
              </div>

              {/* Generated text */}
              <div
                style={{
                  background: "var(--bg-secondary)",
                  borderRadius: "var(--radius-md)",
                  padding: 24,
                  fontSize: "0.92rem",
                  lineHeight: 1.75,
                  whiteSpace: "pre-wrap",
                  color: "var(--ink)",
                  flex: 1,
                  minHeight: 160,
                  maxHeight: 420,
                  overflowY: "auto",
                }}
              >
                {result}
              </div>

              {/* Actions */}
              <div className="generator-btn-row" style={{ marginTop: 4 }}>
                <button
                  className="button-secondary button-sm"
                  type="button"
                  onClick={handleCopy}
                  style={{ gap: 6 }}
                >
                  {copied ? (
                    <>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      Скопировано
                    </>
                  ) : (
                    <>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                      </svg>
                      Копировать
                    </>
                  )}
                </button>
                <button
                  className="button-primary button-sm"
                  type="button"
                  disabled={saving}
                  onClick={handleSave}
                  style={{ gap: 6 }}
                >
                  {saving ? (
                    <>
                      <span className="dash-loading-spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                      Сохранение...
                    </>
                  ) : (
                    <>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                      </svg>
                      Сохранить в материалы
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            /* ── Empty State ── */
            <div className="generator-result-card" style={{ flex: 1, alignItems: "center", justifyContent: "center", minHeight: 400, gap: 16 }}>
              <div
                style={{
                  width: 80,
                  height: 80,
                  borderRadius: "50%",
                  background: "var(--surface-muted)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--ink-faint)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="12" y1="18" x2="12" y2="12" />
                  <line x1="9" y1="15" x2="15" y2="15" />
                </svg>
              </div>
              <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 600, color: "var(--ink)" }}>
                Контент ещё не создан
              </h3>
              <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--ink-faint)", maxWidth: "36ch", textAlign: "center", lineHeight: 1.6 }}>
                Заполните форму слева и нажмите «Сгенерировать контент» — AI создаст текст за несколько секунд
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
