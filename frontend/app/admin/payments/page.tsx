"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

type Payment = {
  payment_id: string;
  tenant_id: string;
  tenant_name: string | null;
  subscription_id: string;
  plan_code: string | null;
  amount: number;
  currency: string;
  status: string;
  provider: string;
  external_payment_id: string | null;
  paid_at: string | null;
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
  succeeded: "#24C26A",
  pending: "#F59E0B",
  failed: "#EF4444",
  refunded: "#8B5CF6",
  cancelled: "#6B7280",
};

const STATUS_LABELS: Record<string, string> = {
  succeeded: "Оплачен",
  pending: "Ожидает",
  failed: "Ошибка",
  refunded: "Возврат",
  cancelled: "Отменён",
};

const PAGE_SIZE = 20;

function fmtDate(s: string | null) {
  if (!s) return "—";
  return new Date(s).toLocaleDateString("ru-RU");
}

function fmtAmount(n: number, c: string) {
  return `${n.toLocaleString("ru-RU")} ${c}`;
}

export default function AdminPayments() {
  const [items, setItems] = useState<Payment[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [providerFilter, setProviderFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), size: String(PAGE_SIZE) });
    if (statusFilter) params.set("status", statusFilter);
    if (providerFilter) params.set("provider", providerFilter);
    const data = await apiFetch<{ items: Payment[]; total: number }>(`/api/backend/admin/payments?${params}`).catch(() => ({ items: [], total: 0 }));
    setItems(data.items);
    setTotal(data.total);
    setLoading(false);
  }, [page, statusFilter, providerFilter]);

  useEffect(() => { void load(); }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="admin2-page">
      <div className="admin2-page-hd">
        <h2 className="admin2-page-title">Платежи</h2>
        <button className="admin2-btn" onClick={load} title="Обновить"><IconRefreshCw /></button>
      </div>

      <div className="admin2-card" style={{ padding: 0 }}>
        <div className="admin2-toolbar">
          <select className="admin2-sel" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="">Все статусы</option>
            <option value="succeeded">Оплачен</option>
            <option value="pending">Ожидает</option>
            <option value="failed">Ошибка</option>
            <option value="refunded">Возврат</option>
            <option value="cancelled">Отменён</option>
          </select>
          <input className="admin2-sel" style={{ width: 140 }} placeholder="Провайдер" value={providerFilter} onChange={(e) => { setProviderFilter(e.target.value); setPage(1); }} />
          <span className="admin2-count">{total} платежей</span>
        </div>

        {loading ? (
          <div className="admin2-empty"><div className="admin-spinner" /></div>
        ) : items.length === 0 ? (
          <div className="admin2-empty"><IconList /> Платежи не найдены</div>
        ) : (
          <div className="admin2-table">
            <div className="admin2-tr admin2-tr-hd">
              <span>Клиент</span>
              <span>Тариф</span>
              <span>Сумма</span>
              <span>Статус</span>
              <span>Провайдер</span>
              <span>Дата</span>
            </div>
            {items.map((p) => (
              <div key={p.payment_id} className="admin2-tr" style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr" }}>
                <span className="admin2-td-name">
                  <span className="admin2-av">{(p.tenant_name || "?")[0]}</span>
                  {p.tenant_name || "—"}
                </span>
                <span>{p.plan_code || "—"}</span>
                <span style={{ fontWeight: 600 }}>{fmtAmount(p.amount, p.currency)}</span>
                <span>
                  <span className="admin2-badge" style={{ background: STATUS_COLORS[p.status] || "#6B7280" }}>
                    {STATUS_LABELS[p.status] || p.status}
                  </span>
                </span>
                <span>{p.provider}</span>
                <span className="admin2-date">{fmtDate(p.paid_at || p.created_at)}</span>
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
