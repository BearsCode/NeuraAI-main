"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

/* ── Types ── */

type Overview = {
  users_total: number; active_users_total: number;
  tenants_total: number; projects_total: number;
  active_subscriptions: number; monthly_recurring_revenue: number;
  successful_payments_total: number;
};

type Analytics = {
  signups_today: number; signups_week: number; signups_month: number;
  projects_created_today: number; projects_created_week: number;
  ai_queries_today: number; ai_queries_week: number;
  active_users_today: number;
};

/* ── SVG Icons ── */

function IconUsers() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
}
function IconBuilding() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><line x1="8" y1="6" x2="10" y2="6"/><line x1="14" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="10" y2="10"/><line x1="14" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="10" y2="14"/><line x1="14" y1="14" x2="16" y2="14"/></svg>;
}
function IconRocket() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>;
}
function IconCreditCard() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>;
}
function IconChart() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>;
}
function IconBot() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>;
}
function IconActivity() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>;
}
function IconRefreshCw() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>;
}
function IconList() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>;
}
function IconAlertCircle() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>;
}

/* ── Chart ── */

function AdminChart() {
  return (
    <svg viewBox="0 0 500 140" width="100%" height="120" className="admin2-chart-svg">
      <defs>
        <linearGradient id="acg1" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#3B82F6" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="acg2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#24C26A" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#24C26A" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d="M0,130 Q30,120 60,105 T120,85 T180,70 T240,48 T300,55 T360,34 T420,40 T500,25 L500,140 L0,140Z" fill="url(#acg1)" />
      <polyline fill="none" stroke="#3B82F6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" points="0,130 60,105 120,85 180,70 240,48 300,55 360,34 420,40 500,25" />
      <path d="M0,138 Q30,130 60,118 T120,100 T180,90 T240,72 T300,78 T360,62 T420,68 T500,56 L500,140 L0,140Z" fill="url(#acg2)" />
      <polyline fill="none" stroke="#24C26A" strokeWidth="2" strokeOpacity="0.6" strokeLinecap="round" strokeLinejoin="round" points="0,138 60,118 120,100 180,90 240,72 300,78 360,62 420,68 500,56" />
    </svg>
  );
}

/* ── Metric Card ── */

function MC({ icon, label, value, sub, color }: { icon: React.ReactNode; label: string; value: string | number; sub?: string; color: string }) {
  return (
    <div className="admin2-card" style={{ "--c": color } as React.CSSProperties}>
      <div className="admin2-mc-icon">{icon}</div>
      <div className="admin2-mc-body">
        <div className="admin2-mc-label">{label}</div>
        <div className="admin2-mc-value">{value ?? "—"}</div>
        {sub && <div className="admin2-mc-sub">{sub}</div>}
      </div>
    </div>
  );
}

/* ── Dashboard ── */

export default function AdminDashboard() {
  const [ov, setOv] = useState<Overview | null>(null);
  const [an, setAn] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const [o, a] = await Promise.all([
      apiFetch<Overview>("/api/backend/admin/overview").catch(() => null),
      apiFetch<Analytics>("/api/backend/admin/analytics").catch(() => null),
    ]);
    setOv(o); setAn(a);
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  if (loading) {
    return <div className="admin2-loading"><div className="admin-spinner" /></div>;
  }

  return (
    <div className="admin2-page">
      {/* Row 1: Core SaaS */}
      <div className="admin2-grid">
        <MC icon={<IconUsers />} label="Активные пользователи" value={ov?.active_users_total ?? "—"} sub={`всего: ${ov?.users_total ?? 0}`} color="#3B82F6" />
        <MC icon={<IconBuilding />} label="Активные компании" value={ov?.tenants_total ?? "—"} color="#8B5CF6" />
        <MC icon={<IconRocket />} label="Проектов" value={ov?.projects_total ?? "—"} color="#24C26A" />
        <MC icon={<IconCreditCard />} label="Активные подписки" value={ov?.active_subscriptions ?? 0} color="#F59E0B" />
      </div>

      {/* Row 2: Financial */}
      <div className="admin2-grid">
        <MC icon={<IconChart />} label="MRR" value={ov?.monthly_recurring_revenue ? `${ov.monthly_recurring_revenue.toLocaleString()} ₽` : "—"} sub={`всего: ${ov?.successful_payments_total?.toLocaleString() ?? 0} ₽`} color="#24C26A" />
        <MC icon={<IconActivity />} label="Регистраций сегодня" value={an?.signups_today ?? 0} sub={`${an?.signups_week ?? 0} за нед. / ${an?.signups_month ?? 0} за мес.`} color="#3B82F6" />
        <MC icon={<IconBot />} label="AI запросов сегодня" value={an?.ai_queries_today ?? 0} sub={`${an?.ai_queries_week ?? 0} за неделю`} color="#8B5CF6" />
        <MC icon={<IconUsers />} label="Активных сегодня" value={an?.active_users_today ?? 0} color="#F59E0B" />
      </div>

      {/* Charts section */}
      <div className="admin2-section">
        <h3 className="admin2-section-title">Аналитика AI</h3>
        <div className="admin2-grid2">
          <div className="admin2-chart-placeholder">
            <div className="admin2-chart-label">Динамика запросов</div>
            <AdminChart />
          </div>
          <div className="admin2-chart-placeholder">
            <div className="admin2-chart-label">Активность пользователей</div>
            <AdminChart />
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="admin2-section">
        <h3 className="admin2-section-title">Быстрые действия</h3>
        <div className="admin2-actions">
          <button className="admin2-btn" onClick={load}><IconRefreshCw /> Обновить метрики</button>
          <button className="admin2-btn"><IconList /> Очередь задач</button>
          <button className="admin2-btn"><IconAlertCircle /> Последние ошибки</button>
        </div>
      </div>
    </div>
  );
}
