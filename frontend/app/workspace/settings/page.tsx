"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";
import type { ProfileResponse, UpdateProfilePayload } from "@/lib/types";

function IconUser() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>;
}
function IconBuilding() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="9" y1="6" x2="9" y2="6.01"/><line x1="15" y1="6" x2="15" y2="6.01"/><line x1="9" y1="10" x2="9" y2="10.01"/><line x1="15" y1="10" x2="15" y2="10.01"/><line x1="9" y1="14" x2="9" y2="14.01"/><line x1="15" y1="14" x2="15" y2="14.01"/><line x1="9" y1="18" x2="9" y2="18.01"/><line x1="15" y1="18" x2="15" y2="18.01"/></svg>;
}
function IconMail() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>;
}
function IconPhone() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>;
}
function IconSend() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>;
}
function IconCpu() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3"/><path d="M15 1v3"/><path d="M9 20v3"/><path d="M15 20v3"/><path d="M20 9h3"/><path d="M20 14h3"/><path d="M1 9h3"/><path d="M1 14h3"/></svg>;
}
function IconShield() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>;
}
function IconCheck() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>;
}

export default function SettingsPage() {
  const [session, setSession] = useState<ProfileResponse | null>(null);
  const [form, setForm] = useState({ full_name: "", phone: "", company_name: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [autoPublish, setAutoPublish] = useState(true);
  const [aiMode, setAiMode] = useState("auto");

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await apiFetch<{ user: ProfileResponse }>("/api/auth/session");
      setSession(res.user);
      setForm({ full_name: res.user.full_name, phone: res.user.phone ?? "", company_name: res.user.company_name ?? "" });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function saveProfile() {
    setSaving(true); setError(null); setNotice(null);
    try {
      const payload: UpdateProfilePayload = { full_name: form.full_name.trim(), phone: form.phone.trim() || null, company_name: form.company_name.trim() || null };
      const res = await apiFetch<{ user: ProfileResponse }>("/api/auth/session", { method: "PATCH", body: JSON.stringify(payload) });
      setSession(res.user);
      setNotice("Настройки сохранены.");
      setTimeout(() => setNotice(null), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка сохранения");
    }
    setSaving(false);
  }

  const initials = session?.full_name
    ? session.full_name.split(/\s+/).map(s => s[0]).join("").toUpperCase().slice(0, 2)
    : "П";

  if (loading) {
    return (
      <div className="dash-content">
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, padding: "80px 0", color: "var(--ink-faint)" }}>
          <div className="dash-loading-spinner" />
          <span style={{ fontSize: "0.95rem" }}>Загрузка настроек...</span>
        </div>
      </div>
    );
  }

  if (error && !session) {
    return (
      <div className="dash-content">
        <header className="dash-header">
          <h1 className="dash-greeting">Настройки</h1>
        </header>
        <div className="error-banner" style={{ marginTop: 24 }}>
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>Повторить</button>
        </div>
      </div>
    );
  }

  return (
    <div className="dash-content">
      <header className="dash-header">
        <div>
          <span className="eyebrow">Настройки</span>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "4px 0 0" }}>Управление аккаунтом</h1>
          <p style={{ color: "var(--ink-faint)", fontSize: "0.88rem", margin: "4px 0 0" }}>Профиль, предпочтения и параметры системы</p>
        </div>
      </header>

      <div style={{ display: "grid", gap: 20, gridTemplateColumns: "1fr 1fr", alignItems: "start" }}>
        {/* ─── Left Column ─── */}
        <div style={{ display: "grid", gap: 20 }}>

          {/* Profile Card */}
          <article style={{ padding: 24, borderRadius: "var(--radius-lg)", background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-sm)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
              <div style={{
                width: 56, height: 56, borderRadius: "50%",
                background: "linear-gradient(135deg, var(--accent), #60A5FA)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontWeight: 700, fontSize: "1.2rem", color: "#fff", flexShrink: 0,
              }}>
                {initials}
              </div>
              <div>
                <h3 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0, color: "var(--ink)" }}>
                  {session?.full_name || "Пользователь"}
                </h3>
                <p style={{ fontSize: "0.82rem", color: "var(--ink-faint)", margin: "2px 0 0" }}>
                  {session?.email || ""}
                </p>
              </div>
            </div>

            <form onSubmit={e => { e.preventDefault(); saveProfile(); }}>
              <div style={{ display: "grid", gap: 16 }}>
                <div style={{ display: "grid", gap: 12, gridTemplateColumns: "1fr 1fr" }}>
                  <div className="field">
                    <label><IconUser /> Имя и фамилия</label>
                    <input value={form.full_name} onChange={e => setForm(p => ({ ...p, full_name: e.target.value }))} required />
                  </div>
                  <div className="field">
                    <label><IconBuilding /> Компания</label>
                    <input value={form.company_name} onChange={e => setForm(p => ({ ...p, company_name: e.target.value }))} placeholder="Название компании" />
                  </div>
                </div>
                <div style={{ display: "grid", gap: 12, gridTemplateColumns: "1fr 1fr" }}>
                  <div className="field">
                    <label><IconMail /> Email</label>
                    <input value={session?.email ?? ""} disabled readOnly style={{ opacity: 0.6 }} />
                  </div>
                  <div className="field">
                    <label><IconPhone /> Телефон</label>
                    <input value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))} placeholder="+7 999 123 45 67" />
                  </div>
                </div>
              </div>

              {notice && (
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 16, padding: "10px 14px", borderRadius: "var(--radius-sm)", background: "rgba(36,194,106,0.08)", color: "var(--success)", fontSize: "0.88rem" }}>
                  <IconCheck /> {notice}
                </div>
              )}
              {error && (
                <div className="inline-error" style={{ marginTop: 16 }}>{error}</div>
              )}

              <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
                <button className="button-primary" type="submit" disabled={saving}>
                  {saving ? "Сохраняем..." : "Сохранить изменения"}
                </button>
              </div>
            </form>
          </article>

          {/* Account Info Card */}
          <article style={{ padding: 24, borderRadius: "var(--radius-lg)", background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-sm)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
              <span style={{ display: "flex", color: "var(--accent)" }}><IconShield /></span>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--ink)" }}>Аккаунт</h3>
            </div>
            <div style={{ display: "grid", gap: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "12px 16px", borderRadius: "var(--radius-sm)", background: "var(--bg)", border: "1px solid var(--border)" }}>
                <span style={{ color: "var(--ink-faint)", fontSize: "0.85rem" }}>Роль</span>
                <strong style={{ fontSize: "0.85rem" }}>{session?.role === "admin" ? "Администратор" : session?.role === "partner" ? "Партнёр" : "Владелец"}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "12px 16px", borderRadius: "var(--radius-sm)", background: "var(--bg)", border: "1px solid var(--border)" }}>
                <span style={{ color: "var(--ink-faint)", fontSize: "0.85rem" }}>Реферальный код</span>
                <strong style={{ fontSize: "0.85rem", fontFamily: "monospace" }}>{session?.referral_code ?? "—"}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "12px 16px", borderRadius: "var(--radius-sm)", background: "var(--bg)", border: "1px solid var(--border)" }}>
                <span style={{ color: "var(--ink-faint)", fontSize: "0.85rem" }}>Статус</span>
                <span style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--success)", display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--success)", display: "inline-block" }} />
                  Активен
                </span>
              </div>
            </div>
          </article>
        </div>

        {/* ─── Right Column ─── */}
        <div style={{ display: "grid", gap: 20 }}>

          {/* Publications Card */}
          <article style={{ padding: 24, borderRadius: "var(--radius-lg)", background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-sm)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
              <span style={{ display: "flex", color: "var(--accent)" }}><IconSend /></span>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--ink)" }}>Публикации</h3>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 16px", borderRadius: "var(--radius-sm)", background: "var(--bg)", border: "1px solid var(--border)" }}>
              <div>
                <strong style={{ display: "block", fontSize: "0.88rem", color: "var(--ink)", marginBottom: 2 }}>Автопубликация</strong>
                <span style={{ fontSize: "0.78rem", color: "var(--ink-faint)" }}>Автоматическая публикация по расписанию</span>
              </div>
              <label style={{
                position: "relative", display: "inline-block", width: 44, height: 24, flexShrink: 0, cursor: "pointer",
              }}>
                <input
                  type="checkbox"
                  checked={autoPublish}
                  onChange={e => setAutoPublish(e.target.checked)}
                  style={{ opacity: 0, width: 0, height: 0, position: "absolute" }}
                />
                <span style={{
                  position: "absolute", inset: 0, borderRadius: 24, transition: "background 0.2s",
                  background: autoPublish ? "var(--accent)" : "var(--border)",
                }}>
                  <span style={{
                    position: "absolute", top: 2, left: autoPublish ? "calc(100% - 22px)" : 2,
                    width: 20, height: 20, borderRadius: "50%", background: "#fff",
                    transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
                  }} />
                </span>
              </label>
            </div>
          </article>

          {/* AI Mode Card */}
          <article style={{ padding: 24, borderRadius: "var(--radius-lg)", background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-sm)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
              <span style={{ display: "flex", color: "var(--accent)" }}><IconCpu /></span>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--ink)" }}>AI-режим</h3>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 16px", borderRadius: "var(--radius-sm)", background: "var(--bg)", border: "1px solid var(--border)" }}>
              <div>
                <strong style={{ display: "block", fontSize: "0.88rem", color: "var(--ink)", marginBottom: 2 }}>Режим работы AI</strong>
                <span style={{ fontSize: "0.78rem", color: "var(--ink-faint)" }}>Степень автоматизации генерации контента</span>
              </div>
              <select value={aiMode} onChange={e => setAiMode(e.target.value)} className="dash-select" style={{ width: "auto", minWidth: 150 }}>
                <option value="auto">Автоматический</option>
                <option value="semi">Полуавтоматический</option>
                <option value="manual">Ручной</option>
              </select>
            </div>
            <div style={{ marginTop: 12, display: "grid", gap: 8, gridTemplateColumns: "1fr 1fr 1fr" }}>
              {[
                { value: "auto", label: "Авто", desc: "AI сам создаёт контент", active: aiMode === "auto" },
                { value: "semi", label: "Полуавто", desc: "AI предлагает — вы утверждаете", active: aiMode === "semi" },
                { value: "manual", label: "Ручной", desc: "Вы контролируете всё", active: aiMode === "manual" },
              ].map(m => (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => setAiMode(m.value)}
                  style={{
                    padding: "12px 10px", borderRadius: "var(--radius-sm)", cursor: "pointer", border: "none", textAlign: "center", fontFamily: "inherit",
                    background: m.active ? "rgba(59,130,246,0.1)" : "var(--surface-muted)",
                    color: m.active ? "var(--accent)" : "var(--ink-faint)", fontWeight: m.active ? 600 : 400,
                    transition: "all 0.15s",
                  }}
                >
                  <div style={{ fontSize: "0.82rem", fontWeight: 600, marginBottom: 4 }}>{m.label}</div>
                  <div style={{ fontSize: "0.7rem", opacity: 0.7, lineHeight: 1.3 }}>{m.desc}</div>
                </button>
              ))}
            </div>
          </article>
        </div>
      </div>
    </div>
  );
}
