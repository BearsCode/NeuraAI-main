"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { apiFetch } from "@/lib/client";
import type { ProfileResponse, ProjectSummaryResponse } from "@/lib/types";

function IconHome() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>;
}
function IconChart() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>;
}
function IconTarget() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>;
}
function IconFile() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>;
}
function IconSend() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>;
}
function IconUsers() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
}
function IconSparkles() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5z"/><path d="M18 2l.5 1.5L20 4l-1.5.5L18 6l-.5-1.5L16 4l1.5-.5z"/><path d="M4 8l.5 1.5L6 10l-1.5.5L4 12l-.5-1.5L2 10l1.5-.5z"/></svg>;
}
function IconGear() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>;
}
function IconPuzzle() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/><path d="M12 9V3"/><path d="M12 21v-6"/><path d="M3 12h6"/><path d="M15 12h6"/></svg>;
}
function IconChevronDown() {
  return <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>;
}
function IconBot() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>;
}
function IconCpu() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3"/><path d="M15 1v3"/><path d="M9 20v3"/><path d="M15 20v3"/><path d="M20 9h3"/><path d="M20 14h3"/><path d="M1 9h3"/><path d="M1 14h3"/></svg>;
}
function IconLogOut() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>;
}
function IconPlus() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
}

const menuItems = [
  { label: "Главная", href: "/workspace", icon: IconHome, exact: true },
  { label: "Аналитика", href: "/workspace/analytics", icon: IconChart },
  { label: "Стратегия", href: "/workspace/strategy", icon: IconTarget },
  {
    label: "Контент", icon: IconFile, children: [
      { label: "План публикаций", href: "/workspace/content/plan" },
      { label: "Мои материалы", href: "/workspace/content/materials" },
      { label: "Генератор контента", href: "/workspace/content/generator" },
    ],
  },
  {
    label: "Публикации", icon: IconSend, children: [
      { label: "Календарь", href: "/workspace/publications/calendar" },
      { label: "Автопостинг", href: "/workspace/publications/autoposting" },
      { label: "Черновики", href: "/workspace/publications/drafts" },
      { label: "История", href: "/workspace/publications/history" },
    ],
  },
  { label: "Аудитория", href: "/workspace/audience", icon: IconUsers },
  { label: "AI-ассистент", href: "/workspace/ai-assistant", icon: IconSparkles },
  { label: "Партнёрская программа", href: "/workspace/partner", icon: IconReferral },
  { label: "Настройки", href: "/workspace/settings", icon: IconGear },
  { label: "Интеграции", href: "/workspace/integrations", icon: IconPuzzle },
  {
    label: "AI возможности", icon: IconBot, children: [
      { label: "AI-стажировка", href: "/workspace/internship" },
      { label: "AI-аватар", href: "/workspace/avatar" },
      { label: "Ритейл", href: "/workspace/retail" },
      { label: "AI Core", href: "/workspace/ai-core" },
    ],
  },
];

function IconReferral() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>;
}

export function Sidebar({ collapsed, onToggle }: { collapsed?: boolean; onToggle?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(new Set(["Контент", "Публикации"]));
  const [session, setSession] = useState<ProfileResponse | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);
  const [adminPath, setAdminPath] = useState<string | null>(null);
  const [companiesOpen, setCompaniesOpen] = useState(false);
  const [projects, setProjects] = useState<ProjectSummaryResponse[]>([]);
  const companiesRef = useRef<HTMLDivElement>(null);

  const loadSession = useCallback(async () => {
    try {
      const response = await apiFetch<{ user: ProfileResponse }>("/api/auth/session");
      setSession(response.user);
    } catch {
      // not logged in
    }
  }, []);

  const loadAdminPath = useCallback(async () => {
    try {
      const data = await apiFetch<{ today_path: string }>("/api/admin-path");
      setAdminPath(data.today_path);
    } catch {
      // not admin
    }
  }, []);

  useEffect(() => { void loadSession(); }, [loadSession]);
  useEffect(() => { void loadAdminPath(); }, [loadAdminPath]);

  const handleLogout = useCallback(async () => {
    setLoggingOut(true);
    try {
      await apiFetch("/api/auth/logout", { method: "POST" });
      router.replace("/login");
      router.refresh();
    } catch {
      setLoggingOut(false);
    }
  }, [router]);

  const displayName = session?.full_name || "Пользователь";
  const companyName = session?.company_name || "Бизнес аккаунт";
  const roleLabel = session?.role === "admin" ? "Администратор" : session?.role === "partner" ? "Партнёр" : "Владелец";
  const initials = displayName.split(/\s+/).map(s => s[0]).join("").toUpperCase().slice(0, 2) || "И";

  function isActive(href: string, exact?: boolean) {
    if (exact) return pathname === href;
    return pathname === href || pathname.startsWith(href + "/");
  }

  function toggleMenu(label: string) {
    setExpandedMenus((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  }

  async function toggleCompanies() {
    if (companiesOpen) {
      setCompaniesOpen(false);
      return;
    }
    try {
      const data = await apiFetch<{ projects: ProjectSummaryResponse[] }>("/api/projects");
      setProjects(data.projects);
    } catch {
      setProjects([]);
    }
    setCompaniesOpen(true);
  }

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (companiesRef.current && !companiesRef.current.contains(e.target as Node)) {
        setCompaniesOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function renderIcon(Icon: React.ComponentType) {
    return <span className="sidebar-menu-icon"><Icon /></span>;
  }

  return (
    <aside className={`sidebar${collapsed ? " collapsed" : ""}`}>
      <div className="sidebar-inner">
        <div className="sidebar-header">
          <Link href="/workspace" className="sidebar-logo">
            <span className="sidebar-logo-mark">N</span>
            <span className="sidebar-logo-text">НЕЙРА</span>
          </Link>
          <button className="sidebar-toggle" onClick={onToggle} type="button" title={collapsed ? "Развернуть" : "Свернуть"}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {collapsed ? (
                <><polyline points="9 18 15 12 9 6" /></>
              ) : (
                <><polyline points="15 18 9 12 15 6" /></>
              )}
            </svg>
          </button>
        </div>

        <div className="sidebar-companies-wrap" ref={companiesRef}>
          <button className="sidebar-account-card" onClick={toggleCompanies} type="button">
            <div className="sidebar-account-avatar" />
            <div className="sidebar-account-info">
              <strong>{companyName}</strong>
              <span>{roleLabel}</span>
            </div>
            <span className={`sidebar-account-arrow ${companiesOpen ? "open" : ""}`}><IconChevronDown /></span>
          </button>
          {companiesOpen && (
            <div className="sidebar-companies-dropdown">
              {projects.map((p) => (
                <Link
                  key={p.project_id}
                  href={`/workspace/projects/${p.project_id}`}
                  className="sidebar-company-item"
                  onClick={() => setCompaniesOpen(false)}
                >
                  <span className="sidebar-company-dot" />
                  <span>{p.company_name}</span>
                </Link>
              ))}
              <Link href="/onboarding/company" className="sidebar-company-create" onClick={() => setCompaniesOpen(false)}>
                <IconPlus />
                <span>Создать компанию</span>
              </Link>
            </div>
          )}
        </div>

        <nav className="sidebar-nav">
          {menuItems.map((item) => {
            if ("children" in item && item.children) {
              const isOpen = expandedMenus.has(item.label);
              return (
                <div key={item.label} className="sidebar-group">
                  <button className="sidebar-group-btn" onClick={() => toggleMenu(item.label)} type="button">
                    {renderIcon(item.icon)}
                    <span>{item.label}</span>
                    <span className={`sidebar-chevron ${isOpen ? "open" : ""}`}><IconChevronDown /></span>
                  </button>
                  {isOpen && (
                    <div className="sidebar-submenu">
                      {item.children.map((child) => (
                        <Link key={child.href} href={child.href}
                          className={`sidebar-link sub ${isActive(child.href) ? "active" : ""}`}>
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              );
            }
            return (
              <Link key={item.href} href={item.href!}
                className={`sidebar-link ${isActive(item.href!, (item as { exact?: boolean }).exact) ? "active" : ""}`}>
                {renderIcon(item.icon)}
                <span>{item.label}</span>
              </Link>
            );
          })}
          {session?.admin_role && adminPath && (
            <Link href={adminPath}
              className={`sidebar-link ${isActive(adminPath) ? "active" : ""}`}>
              {renderIcon(IconCpu)}
              <span>Админ-панель</span>
            </Link>
          )}
        </nav>

        <div className="sidebar-spacer" />

        <div className="sidebar-tariff">
          <span className="sidebar-tariff-icon"><IconSparkles /></span>
          <div>
            <strong>Ваш тариф</strong>
            <span className="sidebar-tariff-name">Бизнес</span>
            <span className="sidebar-tariff-date">Действует до 29.07.2026</span>
          </div>
          <button className="sidebar-tariff-btn" type="button">Управление тарифом</button>
        </div>

        <div className="sidebar-profile">
          <Link href="/workspace/profile" className="sidebar-profile-link">
            <div className="sidebar-profile-avatar">{initials}</div>
            <div className="sidebar-profile-info">
              <strong>{displayName}</strong>
              <span>{roleLabel}</span>
            </div>
          </Link>
          <button
            className="sidebar-logout-btn"
            onClick={handleLogout}
            disabled={loggingOut}
            type="button"
            title="Выйти"
          >
            <IconLogOut />
          </button>
        </div>
      </div>
    </aside>
  );
}
