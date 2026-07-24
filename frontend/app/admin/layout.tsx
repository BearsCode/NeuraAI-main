"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";
import { AdminContext } from "@/lib/admin-context";
import type { AdminCtx, AdminUser } from "@/lib/admin-context";

/* ── SVG Icons ── */

function IconDashboard() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>;
}
function IconUsers() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
}
function IconBuilding() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><line x1="8" y1="6" x2="10" y2="6"/><line x1="14" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="10" y2="10"/><line x1="14" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="10" y2="14"/><line x1="14" y1="14" x2="16" y2="14"/></svg>;
}
function IconCreditCard() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>;
}
function IconCoin() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v12"/><path d="M9 9h5a2 2 0 0 1 0 4H9"/></svg>;
}
function IconBell() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>;
}
function IconChart() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>;
}
function IconBrain() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z"/><path d="M9 9h.01"/><path d="M15 9h.01"/><path d="M9 13a3 3 0 0 0 3 3 3 3 0 0 0 3-3"/></svg>;
}
function IconBot() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>;
}
function IconPuzzle() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/><path d="M12 9V3"/><path d="M12 21v-6"/><path d="M3 12h6"/><path d="M15 12h6"/></svg>;
}
function IconFileText() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>;
}
function IconRefreshCw() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>;
}
function IconTool() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>;
}
function IconCpu() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3"/><path d="M15 1v3"/><path d="M9 20v3"/><path d="M15 20v3"/><path d="M20 9h3"/><path d="M20 14h3"/><path d="M1 9h3"/><path d="M1 14h3"/></svg>;
}
function IconList() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>;
}
function IconHistory() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>;
}
function IconActivity() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>;
}
function IconTerminal() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>;
}
function IconFlask() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M9 3h6v5l4 11H5l4-11V3z"/><line x1="9" y1="3" x2="15" y2="3"/></svg>;
}
function IconRocket() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>;
}
function IconShield() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>;
}
function IconGear() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>;
}
function IconSubscription() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M21 4H3a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z"/><path d="M1 10h22"/></svg>;
}
function IconPayments() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>;
}
function IconPromo() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>;
}
function IconArrowLeft() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>;
}
function IconChevronLeft() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"/></svg>;
}
function IconChevronRight() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>;
}
function IconExternalLink() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>;
}

/* ── Section config ── */

const NAV_ICONS: Record<string, React.FC> = {
  "": IconDashboard,
  users: IconUsers,
  companies: IconBuilding,
  tariffs: IconCreditCard,
  subscriptions: IconSubscription,
  payments: IconPayments,
  promocodes: IconPromo,
  costs: IconCoin,
  notifications: IconBell,
  analytics: IconChart,
  "business-memory": IconBrain,
  agents: IconBot,
  capabilities: IconPuzzle,
  prompts: IconFileText,
  workflows: IconRefreshCw,
  tools: IconTool,
  "model-router": IconCpu,
  queue: IconList,
  "workflow-history": IconHistory,
  "ai-monitoring": IconActivity,
  logs: IconTerminal,
  testing: IconFlask,
  deployments: IconRocket,
  access: IconShield,
  settings: IconGear,
};

const SECTIONS: { id: string; label: string; group: string }[] = [
  /* УПРАВЛЕНИЕ ПЛАТФОРМОЙ */
  { id: "",                  label: "Dashboard",          group: "ops" },
  { id: "users",             label: "Пользователи",       group: "ops" },
  { id: "companies",         label: "Компании",           group: "ops" },
  { id: "tariffs",           label: "Тарифы",             group: "ops" },
  { id: "subscriptions",     label: "Подписки",           group: "ops" },
  { id: "payments",          label: "Платежи",            group: "ops" },
  { id: "promocodes",        label: "Промокоды",          group: "ops" },
  { id: "costs",             label: "Стоимость и токены", group: "ops" },
  { id: "notifications",     label: "Уведомления",        group: "ops" },
  { id: "analytics",         label: "Аналитика",          group: "ops" },
  { id: "queue",             label: "Очередь задач",      group: "ops" },
  { id: "workflow-history",  label: "История Workflow",   group: "ops" },
  { id: "ai-monitoring",     label: "AI Monitoring",      group: "ops" },
  /* AI-ПЛАТФОРМА */
  { id: "business-memory",   label: "Business Memory",    group: "ai" },
  { id: "agents",            label: "Агенты",             group: "ai" },
  { id: "capabilities",      label: "Capability Registry",group: "ai" },
  { id: "prompts",           label: "Prompt Registry",    group: "ai" },
  { id: "workflows",         label: "Workflow Manager",   group: "ai" },
  { id: "tools",             label: "Tool Registry",      group: "ai" },
  { id: "model-router",      label: "Model Router",       group: "ai" },
  /* СИСТЕМА */
  { id: "logs",              label: "Логи",               group: "sys" },
  { id: "testing",           label: "Центр тестирования", group: "sys" },
  { id: "deployments",       label: "Версии и деплой",    group: "sys" },
  { id: "access",            label: "Права доступа",      group: "sys" },
  { id: "settings",          label: "Настройки",          group: "sys" },
];

const GROUP_LABELS: Record<string, string> = {
  ops: "УПРАВЛЕНИЕ ПЛАТФОРМОЙ",
  ai: "AI-ПЛАТФОРМА",
  sys: "СИСТЕМА",
};

/* ── Layout ── */

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [adminCtx, setAdminCtx] = useState<AdminCtx>({ user: null, role: "viewer", loading: true });

  // Detect current section from browser URL (hashed or direct)
  const current = pathname.includes("/admin/")
    ? pathname.replace("/admin/", "")
    : pathname.includes("-admin/")
    ? pathname.split("-admin/")[1] || ""
    : pathname.endsWith("-admin")
    ? ""
    : "";

  const currentSection = SECTIONS.find((s) => s.id === current);

  useEffect(() => {
    apiFetch<AdminUser>("/api/auth/session")
      .then((u) => setAdminCtx({ user: u, role: u.admin_role || u.role, loading: false }))
      .catch(() => { router.push("/admin-login"); });
  }, [router]);

  // Derive admin base from current browser URL (always available after middleware rewrite)
  const adminBase = (() => {
    const m = pathname.match(/^\/([a-f0-9]{12}-admin)/);
    return m ? m[1] : null;
  })();

  const toAdmin = (section: string) => {
    if (adminBase) return `/${adminBase}${section ? `/${section}` : ""}`;
    return `/admin${section ? `/${section}` : ""}`;
  };

  useEffect(() => {
    Promise.all([
      apiFetch<AdminUser>("/api/auth/session"),
      apiFetch<{ today_path: string }>("/api/admin-path").catch(() => null),
    ]).then(([u, p]) => {
      setAdminCtx({ user: u, role: u.admin_role || u.role, loading: false });
    }).catch(() => { router.push("/admin-login"); });
  }, [router]);

  if (adminCtx.loading) {
    return (
      <div className="admin-shell">
        <div className="admin-loading"><div className="admin-spinner" /><span>Загрузка...</span></div>
      </div>
    );
  }

  const NavIcon = currentSection ? NAV_ICONS[currentSection.id] : null;

  return (
    <AdminContext.Provider value={adminCtx}>
      <div className={`admin2-shell${collapsed ? " collapsed" : ""}`}>
        {/* Sidebar */}
        <aside className="admin2-aside">
          <div className="admin2-aside-hd">
            <Link href={toAdmin("")} className="admin2-logo">
              <span className="admin2-logo-m">N</span>
              {!collapsed && <span className="admin2-logo-t">НЕЙРА Admin</span>}
            </Link>
            <button className="admin2-collapse" onClick={() => setCollapsed((c) => !c)}>
              {collapsed ? <IconChevronRight /> : <IconChevronLeft />}
            </button>
          </div>

          <nav className="admin2-nav">
            {Object.entries(
              Object.groupBy(SECTIONS, (s) => s.group)
            ).map(([group, items]) => (
              <div key={group} className="admin2-nav-group">
                {!collapsed && <div className="admin2-nav-glabel">{GROUP_LABELS[group]}</div>}
                {items!.map((s) => {
                  const active = current === s.id || (s.id === "" && current === "");
                  const ItemIcon = NAV_ICONS[s.id];
                  return (
                    <Link
                      key={s.id}
                      href={toAdmin(s.id)}
                      className={`admin2-nav-item${active ? " active" : ""}`}
                      title={collapsed ? s.label : undefined}
                    >
                      <span className="admin2-nav-icon">{ItemIcon ? <ItemIcon /> : null}</span>
                      {!collapsed && <span className="admin2-nav-label">{s.label}</span>}
                      {active && !collapsed && <span className="admin2-nav-indicator" />}
                    </Link>
                  );
                })}
              </div>
            ))}
          </nav>

          <div className="admin2-aside-ft">
            <Link href="/workspace" className="admin2-back">
              <IconArrowLeft /> {!collapsed && "На сайт"}
            </Link>
          </div>
        </aside>

        {/* Main */}
        <div className="admin2-main">
          <header className="admin2-topbar">
            <div className="admin2-topbar-left">
              {NavIcon && <span className="admin2-topbar-icon"><NavIcon /></span>}
              <span className="admin2-breadcrumb">
                {currentSection?.label || "Dashboard"}
              </span>
            </div>
            <div className="admin2-topbar-right">
              <span className="admin2-role-badge">{adminCtx.role === "super_owner" ? "OWNER" : adminCtx.role}</span>
              <span className="admin2-topbar-email">{adminCtx.user?.email}</span>
            </div>
          </header>
          <div className="admin2-content">{children}</div>
        </div>
      </div>
    </AdminContext.Provider>
  );
}
