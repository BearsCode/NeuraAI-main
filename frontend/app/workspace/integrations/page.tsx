"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/client";
import { useSearchParams } from "next/navigation";
import type { SocialAccount } from "@/lib/types";

const OAUTH_PLATFORMS = ["vk", "instagram", "threads"];

const PLATFORMS = [
  { id: "vk", name: "VK", icon: "📱", color: "#0077FF", oauth: true },
  { id: "instagram", name: "Instagram", icon: "📷", color: "#E4405F", oauth: true },
  { id: "threads", name: "Threads", icon: "🧵", color: "#8A8A8A", oauth: true },
  { id: "telegram", name: "Telegram", icon: "✈️", color: "#0088CC", oauth: false },
  { id: "youtube", name: "YouTube", icon: "▶️", color: "#FF0000", oauth: false },
  { id: "tiktok", name: "TikTok", icon: "🎵", color: "#000000", oauth: false },
];

const CALLBACK_URL = typeof window !== "undefined"
  ? window.location.origin + "/workspace/integrations/callback"
  : "";

export default function IntegrationsPageWrapper() {
  return (
    <Suspense>
      <IntegrationsPage />
    </Suspense>
  );
}

function IntegrationsPage() {
  const searchParams = useSearchParams();
  const okPlatform = searchParams.get("ok");
  const errorParam = searchParams.get("error");

  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  /* ── Connect modal state (for non-OAuth platforms) ── */
  const [modalPlatform, setModalPlatform] = useState<string | null>(null);
  const [formHandle, setFormHandle] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (okPlatform) {
      const names: Record<string, string> = { vk: "VK", instagram: "Instagram", threads: "Threads", telegram: "Telegram" };
      setSuccessMsg(`${names[okPlatform] ?? okPlatform} подключён`);
      window.history.replaceState({}, "", "/workspace/integrations");
    }
    if (errorParam) {
      const msgs: Record<string, string> = {
        denied: "Авторизация отклонена",
        state_mismatch: "Ошибка безопасности (state mismatch)",
        invalid_state: "Некорректные данные авторизации",
        callback_failed: "Ошибка при завершении подключения",
      };
      setError(msgs[errorParam] ?? "Ошибка подключения");
      window.history.replaceState({}, "", "/workspace/integrations");
    }
  }, [okPlatform, errorParam]);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const result = await apiFetch<SocialAccount[]>("/api/backend/social");
      setAccounts(Array.isArray(result) ? result : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки интеграций");
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const platformMap = useMemo(() => {
    const m: Record<string, SocialAccount> = {};
    for (const a of accounts) m[a.platform.toLowerCase()] = a;
    return m;
  }, [accounts]);

  function isConnected(id: string) {
    const a = platformMap[id];
    return a && (a.status === "active" || a.status === "connected");
  }

  async function handleDisconnect(platform: string) {
    if (!confirm(`Отключить ${platform}?`)) return;
    try {
      await apiFetch(`/api/backend/social/${platform}`, { method: "DELETE" });
      setSuccessMsg(`${platform} отключён`);
      setAccounts((prev) => prev.filter((a) => a.platform.toLowerCase() !== platform));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка отключения");
    }
  }

  async function startOAuth(platform: string) {
    try {
      const res = await apiFetch<{ authorization_url: string; state: string; code_verifier: string | null }>(
        "/api/backend/social/oauth/" + platform + "/authorize?redirect_uri=" + encodeURIComponent(CALLBACK_URL),
      );
      sessionStorage.setItem(
        "oauth_state_" + res.state,
        JSON.stringify({ platform, code_verifier: res.code_verifier, redirect_uri: CALLBACK_URL }),
      );
      window.location.href = res.authorization_url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка инициализации OAuth");
    }
  }

  function openModal(platform: string) {
    setModalPlatform(platform);
    setFormHandle("");
    setFormError(null);
  }

  function closeModal() {
    setModalPlatform(null);
  }

  const platformNames: Record<string, string> = {
    instagram: "Instagram",
    telegram: "Telegram",
    vk: "VK",
    youtube: "YouTube",
    tiktok: "TikTok",
    threads: "Threads",
  };

  const platformProfileUrls: Record<string, string> = {
    telegram: "t.me/",
  };

  async function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    if (!modalPlatform || !formHandle.trim()) {
      setFormError("Укажите @username канала");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      const handle = formHandle.trim().replace(/^https?:\/\//, "").replace(/\/$/, "");
      await apiFetch("/api/backend/social/connect", {
        method: "POST",
        body: JSON.stringify({
          platform: modalPlatform,
          account_identifier: handle,
          access_token: "connected_via_url",
          settings: {},
          scopes: [],
        }),
      });
      setSuccessMsg(`${platformNames[modalPlatform] ?? modalPlatform} подключён`);
      closeModal();
      await load();
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Ошибка подключения");
    }
    setSubmitting(false);
  }

  return (
    <div className="dash-content">
      <header className="dash-header">
        <div className="dash-header-left">
          <h1 className="dash-greeting">Интеграции</h1>
          <p className="dash-subtitle">Подключите социальные сети для автопубликации и аналитики.</p>
        </div>
      </header>

      {successMsg && (
        <div className="dash-success-bar">
          <span>{successMsg}</span>
          <button className="dash-btn-icon sm" type="button" onClick={() => setSuccessMsg(null)}>✕</button>
        </div>
      )}
      {error && (
        <div className="dash-error-bar">
          <span>{error}</span>
          <button className="dash-btn-icon sm" type="button" onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {loading ? (
        <div className="dash-loading">Загрузка интеграций...</div>
      ) : (
        <div className="integrations-grid">
          {PLATFORMS.map((p) => {
            const connected = isConnected(p.id);
            const account = platformMap[p.id];
            return (
              <article key={p.id} className="integration-card" style={{ borderTopColor: p.color }}>
                <div className="integration-card-header">
                  <span className="integration-icon" style={{ background: `${p.color}15`, color: p.color }}>{p.icon}</span>
                  <div className="integration-info">
                    <strong>{p.name}</strong>
                    {account && <span className="integration-handle">{account.account_identifier}</span>}
                  </div>
                  <span className={`integration-status ${connected ? "connected" : "disconnected"}`}>
                    {connected ? "Подключено" : "Не подключено"}
                  </span>
                </div>
                <div className="integration-actions">
                  {connected ? (
                    <button className="dash-btn dash-btn-ghost xs" type="button" onClick={() => handleDisconnect(p.id)}>Отключить</button>
                  ) : p.oauth ? (
                    <button className="dash-btn dash-btn-primary xs" type="button" onClick={() => startOAuth(p.id)}>
                      Подключить
                    </button>
                  ) : (
                    <button className="dash-btn dash-btn-primary xs" type="button" onClick={() => openModal(p.id)}>
                      Подключить
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}

      {/* ── Manual connect modal (Telegram / YouTube / TikTok) ── */}
      {modalPlatform && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Подключить {platformNames[modalPlatform] ?? modalPlatform}</h2>
              <button className="dash-btn-icon sm" type="button" onClick={closeModal}>✕</button>
            </div>
            <form className="modal-form" onSubmit={handleConnect}>
              <div className="modal-field">
                <label htmlFor="acc-handle">@username канала или сообщества</label>
                <input
                  id="acc-handle"
                  type="text"
                  placeholder={`${platformProfileUrls[modalPlatform] ?? ""}username`}
                  value={formHandle}
                  onChange={(e) => setFormHandle(e.target.value)}
                  autoFocus
                />
                {modalPlatform === "telegram" && (
                  <span className="modal-field-hint">
                    Добавьте бота в канал как администратора и укажите @username канала
                  </span>
                )}
                {(modalPlatform === "youtube" || modalPlatform === "tiktok") && (
                  <span className="modal-field-hint">Подключение через API пока в разработке</span>
                )}
              </div>
              {formError && <div className="modal-error">{formError}</div>}
              <div className="modal-actions">
                <button className="dash-btn dash-btn-ghost" type="button" onClick={closeModal}>Отмена</button>
                <button className="dash-btn dash-btn-primary" type="submit" disabled={submitting}>
                  {submitting ? "Подключение..." : "Подключить"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
