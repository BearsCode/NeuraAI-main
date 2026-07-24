"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

type Tariff = {
  plan_id: string;
  code: string;
  name: string;
  description: string;
  price_amount: number;
  currency: string;
  requests_per_minute: number;
  content_generations_per_hour: number;
  publications_per_hour: number;
  features: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type TariffForm = {
  code: string;
  name: string;
  description: string;
  price_amount: number;
  currency: string;
  requests_per_minute: number;
  content_generations_per_hour: number;
  publications_per_hour: number;
  features: Record<string, unknown>;
  is_active: boolean;
};

const EMPTY_FORM: TariffForm = {
  code: "",
  name: "",
  description: "",
  price_amount: 0,
  currency: "RUB",
  requests_per_minute: 120,
  content_generations_per_hour: 100,
  publications_per_hour: 50,
  features: {},
  is_active: true,
};

function IconPlus() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
}
function IconEdit() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>;
}
function IconRefreshCw() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>;
}
function IconX() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>;
}

function Badge({ active }: { active: boolean }) {
  return active
    ? <span className="admin2-badge" style={{ background: "#24C26A" }}>Активен</span>
    : <span className="admin2-badge" style={{ background: "#6B7280" }}>Неактивен</span>;
}

export default function AdminTariffs() {
  const [tariffs, setTariffs] = useState<Tariff[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Tariff | null>(null);
  const [form, setForm] = useState<TariffForm>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const data = await apiFetch<Tariff[]>("/api/backend/admin/tariffs").catch(() => []);
    setTariffs(data);
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setModal(true);
  };

  const openEdit = (t: Tariff) => {
    setEditing(t);
    setForm({
      code: t.code,
      name: t.name,
      description: t.description,
      price_amount: t.price_amount,
      currency: t.currency,
      requests_per_minute: t.requests_per_minute,
      content_generations_per_hour: t.content_generations_per_hour,
      publications_per_hour: t.publications_per_hour,
      features: t.features,
      is_active: t.is_active,
    });
    setModal(true);
  };

  const close = () => { setModal(false); setEditing(null); };

  const save = async () => {
    setSaving(true);
    try {
      await apiFetch("/api/backend/admin/tariffs", {
        method: "POST",
        body: JSON.stringify(form),
      });
      close();
      void load();
    } catch {
    } finally {
      setSaving(false);
    }
  };

  const fmt = (n: number) => n.toLocaleString("ru-RU");

  return (
    <div className="admin2-page">
      <div className="admin2-page-hd">
        <h2 className="admin2-page-title">Тарифы</h2>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="admin2-btn" onClick={load} title="Обновить"><IconRefreshCw /></button>
          <button className="admin2-btn primary" onClick={openCreate}><IconPlus /> Создать тариф</button>
        </div>
      </div>

      {loading ? (
        <div className="admin2-loading"><div className="admin-spinner" /></div>
      ) : tariffs.length === 0 ? (
        <div className="admin2-empty">Тарифы не найдены</div>
      ) : (
        <div className="admin2-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
          {tariffs.map((t) => (
            <div key={t.plan_id} className="admin2-card" style={{ flexDirection: "column", alignItems: "stretch", padding: 22, position: "relative" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>{t.name}</div>
                <Badge active={t.is_active} />
              </div>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "var(--aaccent)", marginBottom: 6 }}>
                {fmt(t.price_amount)} {t.currency}
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--atext-faint)", marginBottom: 14, lineHeight: 1.5 }}>{t.description}</div>
              <div style={{ display: "grid", gap: 6, fontSize: "0.8rem", color: "var(--atext-soft)", marginBottom: 16 }}>
                <span>{fmt(t.requests_per_minute)} запросов/мин</span>
                <span>{fmt(t.content_generations_per_hour)} генераций/ч</span>
                <span>{fmt(t.publications_per_hour)} публикаций/ч</span>
              </div>
              <div style={{ marginTop: "auto" }}>
                <button className="admin2-btn" style={{ width: "100%", justifyContent: "center" }} onClick={() => openEdit(t)}>
                  <IconEdit /> Редактировать
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {modal && (
        <div className="admin2-modal-overlay" onClick={close}>
          <div className="admin2-modal" onClick={(e) => e.stopPropagation()}>
            <div className="admin2-modal-hd">
              {editing ? "Редактировать тариф" : "Новый тариф"}
              <button onClick={close}><IconX /></button>
            </div>
            <div className="admin2-modal-bd">
              <div className="admin2-field">
                <span className="admin2-field-label">Код</span>
                <input className="admin2-field-input" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="startup" />
              </div>
              <div className="admin2-field">
                <span className="admin2-field-label">Название</span>
                <input className="admin2-field-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Стартовый" />
              </div>
              <div className="admin2-field">
                <span className="admin2-field-label">Описание</span>
                <textarea className="admin2-field-textarea" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
              <div className="admin2-field-row">
                <div className="admin2-field">
                  <span className="admin2-field-label">Цена</span>
                  <input className="admin2-field-input" type="number" value={form.price_amount} onChange={(e) => setForm({ ...form, price_amount: Number(e.target.value) })} />
                </div>
                <div className="admin2-field">
                  <span className="admin2-field-label">Валюта</span>
                  <input className="admin2-field-input" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
                </div>
              </div>
              <div className="admin2-field-row">
                <div className="admin2-field">
                  <span className="admin2-field-label">Запросов/мин</span>
                  <input className="admin2-field-input" type="number" value={form.requests_per_minute} onChange={(e) => setForm({ ...form, requests_per_minute: Number(e.target.value) })} />
                </div>
                <div className="admin2-field">
                  <span className="admin2-field-label">Генераций/ч</span>
                  <input className="admin2-field-input" type="number" value={form.content_generations_per_hour} onChange={(e) => setForm({ ...form, content_generations_per_hour: Number(e.target.value) })} />
                </div>
              </div>
              <div className="admin2-field-row">
                <div className="admin2-field">
                  <span className="admin2-field-label">Публикаций/ч</span>
                  <input className="admin2-field-input" type="number" value={form.publications_per_hour} onChange={(e) => setForm({ ...form, publications_per_hour: Number(e.target.value) })} />
                </div>
                <div className="admin2-field">
                  <span className="admin2-field-label">Статус</span>
                  <select className="admin2-field-select" value={form.is_active ? "1" : "0"} onChange={(e) => setForm({ ...form, is_active: e.target.value === "1" })}>
                    <option value="1">Активен</option>
                    <option value="0">Неактивен</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="admin2-modal-ft">
              <button className="admin2-btn" onClick={close}>Отмена</button>
              <button className="admin2-btn primary" onClick={save} disabled={saving}>{saving ? "Сохранение..." : "Сохранить"}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
