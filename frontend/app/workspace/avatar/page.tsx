"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

type AvatarData = {
  id: string;
  name: string;
  personality_traits: string[];
  communication_style: string;
  voice_tone: string;
  avatar_url: string | null;
  created_at: string;
};

export default function AvatarPage() {
  const [avatar, setAvatar] = useState<AvatarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [style, setStyle] = useState("professional");
  const [tone, setTone] = useState("friendly");
  const [traits, setTraits] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const result = await apiFetch<AvatarData>("/api/backend/avatar");
      setAvatar(result);
      if (result) {
        setName(result.name);
        setStyle(result.communication_style);
        setTone(result.voice_tone);
        setTraits(result.personality_traits?.join(", ") ?? "");
      }
    } catch {
      setAvatar(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function saveAvatar() {
    setSaving(true); setError(null);
    try {
      const result = await apiFetch<AvatarData>("/api/backend/avatar", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          communication_style: style,
          voice_tone: tone,
          personality_traits: traits.split(",").map(t => t.trim()).filter(Boolean),
        }),
      });
      setAvatar(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка сохранения");
    }
    setSaving(false);
  }

  return (
    <div className="dash-content">
      <header className="dash-header">
        <div className="dash-header-left">
          <h1 className="dash-greeting">AI-аватар</h1>
          <p className="dash-subtitle">Настройте персональный голос и стиль общения вашего AI-маркетолога.</p>
        </div>
      </header>

      {loading ? (
        <div className="dash-loading">Загрузка...</div>
      ) : error && !avatar ? (
        <div className="error-banner top-spacer">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>Повторить</button>
        </div>
      ) : (
        <div className="detail-grid top-spacer">
          <div className="stack">
            <article className="insight-card">
              <h3 className="dash-section-title">Настройка аватара</h3>
              <form onSubmit={e => { e.preventDefault(); saveAvatar(); }} className="form-grid">
                <div className="field">
                  <label>Имя аватара</label>
                  <input value={name} onChange={e => setName(e.target.value)} placeholder="Например: Марк" />
                </div>
                <div className="field-grid">
                  <div className="field">
                    <label>Стиль общения</label>
                    <select value={style} onChange={e => setStyle(e.target.value)} className="dash-select" style={{ width: "100%" }}>
                      <option value="professional">Деловой</option>
                      <option value="casual">Повседневный</option>
                      <option value="creative">Креативный</option>
                      <option value="humorous">С юмором</option>
                    </select>
                  </div>
                  <div className="field">
                    <label>Тон голоса</label>
                    <select value={tone} onChange={e => setTone(e.target.value)} className="dash-select" style={{ width: "100%" }}>
                      <option value="friendly">Дружелюбный</option>
                      <option value="formal">Официальный</option>
                      <option value="energetic">Энергичный</option>
                      <option value="calm">Спокойный</option>
                    </select>
                  </div>
                </div>
                <div className="field">
                  <label>Черты личности (через запятую)</label>
                  <input value={traits} onChange={e => setTraits(e.target.value)} placeholder="креативный, внимательный, экспертный" />
                </div>
                {error && <p className="inline-error">{error}</p>}
                <div className="button-row">
                  <button className="button-primary" type="submit" disabled={saving}>
                    {saving ? "Сохраняем..." : avatar ? "Обновить аватар" : "Создать аватар"}
                  </button>
                </div>
              </form>
            </article>
          </div>

          <div className="stack">
            {avatar && (
              <article className="insight-card">
                <div className="card-topline">
                  <div>
                    <h3>{avatar.name || "Аватар"}</h3>
                    <p>Создан: {new Date(avatar.created_at).toLocaleDateString("ru")}</p>
                  </div>
                </div>
                <div className="summary-list">
                  <div className="summary-row">
                    <span>Стиль</span>
                    <strong>{avatar.communication_style}</strong>
                  </div>
                  <div className="summary-row">
                    <span>Тон</span>
                    <strong>{avatar.voice_tone}</strong>
                  </div>
                </div>
                {avatar.personality_traits?.length > 0 && (
                  <div className="chip-row top-spacer">
                    {avatar.personality_traits.map(t => <span key={t} className="chip">{t}</span>)}
                  </div>
                )}
              </article>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
