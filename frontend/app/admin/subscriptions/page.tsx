"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

type Subscription = {
  subscription_id: string;
  tenant_id: string;
  tenant_name: string | null;
  plan_id: string;
  plan_code: string | null;
  plan_name: string | null;
  status: string;
  seats: number;
  starts_at: string;
  ends_at: string | null;
  next_charge_at: string | null;
  trial_ends_at: string | null;
  created_at: string;
};

function IconRefreshCw() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>;
}
function IconChevronLeft() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"/></svg>;
}
function IconChevronRight() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>;
}
function IconList() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>;
}

const STATUS_COLORS: Record<string, string> = {
  active: "#24C26A",
  trial: "#3B82F6",
  past_due: "#F59E0B",
  cancelled: "#EF4444",
  expired: "#6B7280",
  paused: "#8B5CF6",
};

const STATUS_LABELS: Record<string, string> = {
  active: "Активна",
  trial: "Триал",
  past_due: "Просрочена",
  cancelled: "Отменена",
  expired: "Истекла",
  paused: "Приостановлена",
};

const PAGE_SIZE = 20;

function fmtDate(s: string | null) {
  if (!s) return "—";
  return new Date(s).toLocaleDateString("ru-RU");
}

export default function AdminSubscriptions() {
  const [items, setItems] = useState<Subscription[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), size: String(PAGE_SIZE) });
    if (statusFilter) params.set("status", statusFilter);
    const data = await apiFetch<{ items: Subscription[]; total: number }>(`/api/backend/admin/subscriptions?${params}`).catch(() => ({ items: [], total: 0 }));
    setItems(data.items);
    setTotal(data.total);
    setLoading(false);
  }, [page, statusFilter]);

  useEffect(() => { void load(); }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="admin2-page">
      <div className="admin2-page-hd">
        <h2 className="admin2-page-title">Подписки</h2>
        <button className="admin2-btn" onClick={load} title="Обновить"><IconRefreshCw /></button>
      </div>

      <div className="admin2-card" style={{ padding: 0 }}>
        <div className="admin2-toolbar">
          <select className="admin2-sel" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="">Все статусы</option>
            <option value="active">Активна</option>
            <option value="trial">Триал</option>
            <option value="past_due">Просрочена</option>
            <option value="cancelled">Отменена</option>
            <option value="expired">Истекла</option>
            <option value="paused">Приостановлена</option>
          </select>
          <span className="admin2-count">{total} подписок</span>
        </div>

        {loading ? (
          <div className="admin2-empty"><div className="admin-spinner" /></div>
        ) : items.length === 0 ? (
          <div className="admin2-empty"><IconList /> Подписки не найдены</div>
        ) : (
          <div className="admin2-table">
            <div className="admin2-tr admin2-tr-hd">
              <span>Клиент</span>
              <span>Тариф</span>
              <span>Статус</span>
              <span>Мест</span>
              <span>Начало / Конец</span>
            </div>
            {items.map((s) => (
              <div key={s.subscription_id} className="admin2-tr">
                <span className="admin2-td-name">
                  <span className="admin2-av">{(s.tenant_name || "?")[0]}</span>
                  {s.tenant_name || "—"}
                </span>
                <span>{s.plan_name || s.plan_code || "—"}</span>
                <span>
                  <span className="admin2-badge" style={{ background: STATUS_COLORS[s.status] || "#6B7280" }}>
                    {STATUS_LABELS[s.status] || s.status}
                  </span>
                </span>
                <span>{s.seats}</span>
                <span className="admin2-date">
                  {fmtDate(s.starts_at)}
                  {(s.ends_at || s.next_charge_at) && <><br />{fmtDate(s.ends_at || s.next_charge_at)}</>}
                </span>
              </div>
            ))}
          </div>
        )}

        {totalPages > 1 && (
          <div className="admin2-pagination">
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}><IconChevronLeft /></button>
            <span className="admin2-pagination-info">{page} / {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}><IconChevronRight /></button>
          </div>
        )}
      </div>
    </div>
  );
}
