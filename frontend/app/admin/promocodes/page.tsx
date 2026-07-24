"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

type Promocode = {
  promo_code_id: string;
  code: string;
  description: string;
  type_promo: string;
  value: number;
  max_uses: number | null;
  uses_total: number;
  remaining_uses: number | null;
  start_time: string;
  expire_time: string;
  is_active: boolean;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
};

type PromoForm = {
  code: string;
  description: string;
  type_promo: string;
  value: number;
  max_uses: string;
  start_time: string;
  expire_time: string;
  is_active: boolean;
};

const EMPTY_FORM: PromoForm = {
  code: "",
  description: "",
  type_promo: "balance",
  value: 0,
  max_uses: "",
  start_time: "",
  expire_time: "",
  is_active: true,
};

const TYPE_LABELS: Record<string, string> = {
  balance: "Баланс",
  percent: "Процент",
  discount: "Скидка",
  gift_plan: "Подарочный план",
};

function IconPlus() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
}
function IconEdit() {
  return <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>;
}
function IconTrash() {
  return <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>;
}
function IconRefreshCw() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>;
}
function IconX() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>;
}
function IconList() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>;
}

function fmtDate(s: string) {
  if (!s) return "—";
  return new Date(s).toLocaleDateString("ru-RU");
}

function toLocalDatetime(s: string) {
  if (!s) return "";
  const d = new Date(s);
  const off = d.getTimezoneOffset();
  const local = new Date(d.getTime() - off * 60000);
  return local.toISOString().slice(0, 16);
}

export default function AdminPromocodes() {
  const [items, setItems] = useState<Promocode[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<Promocode | null>(null);
  const [form, setForm] = useState<PromoForm>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<Promocode | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const data = await apiFetch<Promocode[]>("/api/backend/admin/promocodes").catch(() => []);
    setItems(data);
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setModal(true);
  };

  const openEdit = (p: Promocode) => {
    setEditing(p);
    setForm({
      code: p.code,
      description: p.description,
      type_promo: p.type_promo,
      value: p.value,
      max_uses: p.max_uses != null ? String(p.max_uses) : "",
      start_time: toLocalDatetime(p.start_time),
      expire_time: toLocalDatetime(p.expire_time),
      is_active: p.is_active,
    });
    setModal(true);
  };

  const close = () => { setModal(false); setEditing(null); };

  const save = async () => {
    setSaving(true);
    const body: Record<string, unknown> = {
      code: form.code,
      description: form.description,
      type_promo: form.type_promo,
      value: form.value,
      start_time: new Date(form.start_time).toISOString(),
      expire_time: new Date(form.expire_time).toISOString(),
      is_active: form.is_active,
    };
    if (form.max_uses) body.max_uses = Number(form.max_uses);
    try {
      if (editing) {
        await apiFetch(`/api/backend/admin/promocodes/${editing.code}`, {
          method: "PUT",
          body: JSON.stringify(body),
        });
      } else {
        await apiFetch("/api/backend/admin/promocodes", {
          method: "POST",
          body: JSON.stringify(body),
        });
      }
      close();
      void load();
    } catch {
    } finally {
      setSaving(false);
    }
  };

  const remove = async (code: string) => {
    await apiFetch(`/api/backend/admin/promocodes/${code}`, { method: "DELETE" }).catch(() => {});
    setConfirmDelete(null);
    void load();
  };

  return (
    <div className="admin2-page">
      <div className="admin2-page-hd">
        <h2 className="admin2-page-title">Промокоды</h2>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="admin2-btn" onClick={load} title="Обновить"><IconRefreshCw /></button>
          <button className="admin2-btn primary" onClick={openCreate}><IconPlus /> Создать</button>
        </div>
      </div>

      <div className="admin2-card" style={{ padding: 0 }}>
        {loading ? (
          <div className="admin2-empty"><div className="admin-spinner" /></div>
        ) : items.length === 0 ? (
          <div className="admin2-empty"><IconList /> Промокоды не найдены</div>
        ) : (
          <div className="admin2-table">
            <div className="admin2-tr admin2-tr-hd">
              <span>Код</span>
              <span>Описание</span>
              <span>Тип</span>
              <span>Значение</span>
              <span>Использования</span>
              <span>Активен</span>
              <span>Даты</span>
              <span />
            </div>
            {items.map((p) => (
              <div key={p.promo_code_id} className="admin2-tr" style={{ gridTemplateColumns: "1fr 1.5fr 1fr 0.8fr 1.2fr 0.7fr 1.3fr auto" }}>
                <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{p.code}</span>
                <span style={{ color: "var(--atext-soft)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.description}</span>
                <span><span className="admin2-badge" style={{ background: "#3B82F6" }}>{TYPE_LABELS[p.type_promo] || p.type_promo}</span></span>
                <span style={{ fontWeight: 600 }}>{p.value}</span>
                <span>{p.uses_total}{p.max_uses != null ? ` / ${p.max_uses}` : ""}</span>
                <span>{p.is_active
                  ? <span className="admin2-badge" style={{ background: "#24C26A" }}>Да</span>
                  : <span className="admin2-badge" style={{ background: "#6B7280" }}>Нет</span>
                }</span>
                <span className="admin2-date">{fmtDate(p.start_time)} — {fmtDate(p.expire_time)}</span>
                <span style={{ display: "flex", gap: 6 }}>
                  <button className="admin2-btn sm" onClick={() => openEdit(p)}><IconEdit /></button>
                  <button className="admin2-btn sm danger" onClick={() => setConfirmDelete(p)}><IconTrash /></button>
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {modal && (
        <div className="admin2-modal-overlay" onClick={close}>
          <div className="admin2-modal" onClick={(e) => e.stopPropagation()}>
            <div className="admin2-modal-hd">
              {editing ? "Редактировать промокод" : "Новый промокод"}
              <button onClick={close}><IconX /></button>
            </div>
            <div className="admin2-modal-bd">
              <div className="admin2-field">
                <span className="admin2-field-label">Код</span>
                <input className="admin2-field-input" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} placeholder="SALE20" />
              </div>
              <div className="admin2-field">
                <span className="admin2-field-label">Описание</span>
                <textarea className="admin2-field-textarea" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
              <div className="admin2-field-row">
                <div className="admin2-field">
                  <span className="admin2-field-label">Тип</span>
                  <select className="admin2-field-select" value={form.type_promo} onChange={(e) => setForm({ ...form, type_promo: e.target.value })}>
                    <option value="balance">Баланс</option>
                    <option value="percent">Процент</option>
                    <option value="discount">Скидка</option>
                    <option value="gift_plan">Подарочный план</option>
                  </select>
                </div>
                <div className="admin2-field">
                  <span className="admin2-field-label">Значение</span>
                  <input className="admin2-field-input" type="number" value={form.value} onChange={(e) => setForm({ ...form, value: Number(e.target.value) })} />
                </div>
              </div>
              <div className="admin2-field">
                <span className="admin2-field-label">Макс. использований (без лимита — пусто)</span>
                <input className="admin2-field-input" type="number" value={form.max_uses} onChange={(e) => setForm({ ...form, max_uses: e.target.value })} />
              </div>
              <div className="admin2-field-row">
                <div className="admin2-field">
                  <span className="admin2-field-label">Дата начала</span>
                  <input className="admin2-field-input" type="datetime-local" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
                </div>
                <div className="admin2-field">
                  <span className="admin2-field-label">Дата окончания</span>
                  <input className="admin2-field-input" type="datetime-local" value={form.expire_time} onChange={(e) => setForm({ ...form, expire_time: e.target.value })} />
                </div>
              </div>
              <div className="admin2-field">
                <span className="admin2-field-label">Статус</span>
                <select className="admin2-field-select" value={form.is_active ? "1" : "0"} onChange={(e) => setForm({ ...form, is_active: e.target.value === "1" })}>
                  <option value="1">Активен</option>
                  <option value="0">Неактивен</option>
                </select>
              </div>
            </div>
            <div className="admin2-modal-ft">
              <button className="admin2-btn" onClick={close}>Отмена</button>
              <button className="admin2-btn primary" onClick={save} disabled={saving}>{saving ? "Сохранение..." : "Сохранить"}</button>
            </div>
          </div>
        </div>
      )}

      {confirmDelete && (
        <div className="admin2-modal-overlay" onClick={() => setConfirmDelete(null)}>
          <div className="admin2-modal" style={{ width: 380 }} onClick={(e) => e.stopPropagation()}>
            <div className="admin2-modal-hd">
              Удалить промокод
              <button onClick={() => setConfirmDelete(null)}><IconX /></button>
            </div>
            <div className="admin2-modal-bd">
              <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--atext-soft)" }}>
                Вы уверены, что хотите удалить промокод <strong style={{ color: "var(--atext)" }}>{confirmDelete.code}</strong>? Это действие необратимо.
              </p>
            </div>
            <div className="admin2-modal-ft">
              <button className="admin2-btn" onClick={() => setConfirmDelete(null)}>Отмена</button>
              <button className="admin2-btn danger" onClick={() => remove(confirmDelete.code)}>Удалить</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
