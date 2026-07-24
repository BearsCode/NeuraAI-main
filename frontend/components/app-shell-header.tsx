import Link from "next/link";
import type { ReactNode } from "react";

import type { ProfileResponse } from "@/lib/types";

type AppShellHeaderProps = {
  currentPath: string;
  session?: ProfileResponse | null;
  actions?: ReactNode;
};

const roleLabels: Record<string, string> = {
  admin: "Администратор",
  client: "Клиент",
  partner: "Партнёр",
};

const navItems = [
  { href: "/workspace", label: "Обзор", exact: true },
  { href: "/workspace#projects", label: "Проекты", prefix: "/workspace/projects" },
  { href: "/workspace/profile", label: "Профиль", prefix: "/workspace/profile" },
];

function isActivePath(
  currentPath: string,
  item: { href: string; exact?: boolean; prefix?: string },
): boolean {
  if (item.exact) {
    return currentPath === item.href;
  }

  return currentPath.startsWith(item.prefix ?? item.href.replace(/#.*$/, ""));
}

function getInitials(value: string | undefined): string {
  if (!value) {
    return "N";
  }

  const normalized = value.trim();
  if (!normalized) {
    return "N";
  }

  const parts = normalized.split(/\s+/).slice(0, 2);
  const initials = parts.map((part) => part[0]?.toUpperCase() ?? "").join("");
  return initials || normalized.slice(0, 2).toUpperCase();
}

export function AppShellHeader({
  currentPath,
  session = null,
  actions = null,
}: AppShellHeaderProps) {
  return (
    <header className="app-shell-header">
      <Link className="brand-lockup" href="/workspace">
        <span className="brand-mark">N</span>
        <span className="brand-text">
          <strong>NeuraAI</strong>
          <span>Панель управления</span>
        </span>
      </Link>

      <nav className="app-shell-nav" aria-label="Основная навигация">
        {navItems.map((item) => (
          <Link
            className={`app-shell-link ${isActivePath(currentPath, item) ? "is-active" : ""}`}
            href={item.href}
            key={item.label}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="app-shell-side">
        {session ? (
          <Link className="app-shell-account" href="/workspace/profile">
            <span className="account-avatar">{getInitials(session.full_name)}</span>
            <span className="account-copy">
              <strong>{session.full_name}</strong>
              <span>
                {roleLabels[session.role] ?? session.role}
                {session.company_name ? ` · ${session.company_name}` : ""}
              </span>
            </span>
          </Link>
        ) : null}

        {actions ? <div className="app-shell-actions">{actions}</div> : null}
      </div>
    </header>
  );
}
