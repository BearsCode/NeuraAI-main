"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/client";

/* ── SVG Icons ── */

function IconSearch() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>;
}
function IconRefreshCw() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>;
}
function IconUser() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>;
}
function IconCheckCircle() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>;
}
function IconXCircle() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>;
}

/* ── Types ── */

type User = {
  id: string; email: string; full_name: string; role: string;
  admin_role: string | null; is_active: boolean; is_verified: boolean;
  created_at: string;
};

function Badge({ text, color }: { text: string; color: string }) {
  return <span className="admin2-badge" style={{ background: color }}>{text}</span>;
}

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const data = await apiFetch<User[]>("/api/backend/admin/users").catch(() => []);
    setUsers(data);
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const filtered = useMemo(() => {
    let list = users;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((u) => u.full_name?.toLowerCase().includes(q) || u.email?.includes(q));
    }
    if (filter !== "all") list = list.filter((u) => (u.admin_role || u.role) === filter);
    return list;
  }, [users, search, filter]);

  const ROLE_COLORS: Record<string, string> = {
    client: "#3B82F6", admin: "#24C26A", super_owner: "#8B5CF6",
    manager: "#F59E0B", viewer: "#6B7280",
  };

  return (
    <div className="admin2-page">
      <div className="admin2-page-hd">
        <h2 className="admin2-page-title">Пользователи</h2>
        <button className="admin2-btn" onClick={load} title="Обновить"><IconRefreshCw /></button>
      </div>

      <div className="admin2-card">
        <div className="admin2-toolbar">
          <div className="admin2-search">
            <IconSearch />
            <input placeholder="Поиск по имени или email..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <select className="admin2-sel" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">Все роли</option>
            <option value="client">Клиент</option>
            <option value="admin">Admin</option>
            <option value="manager">Менеджер</option>
            <option value="super_owner">Super Owner</option>
          </select>
          <span className="admin2-count">{filtered.length} из {users.length}</span>
        </div>

        {loading ? (
          <div className="admin2-empty"><div className="admin-spinner" /></div>
        ) : filtered.length === 0 ? (
          <div className="admin2-empty"><IconUser /> Пользователи не найдены</div>
        ) : (
          <div className="admin2-table">
            <div className="admin2-tr admin2-tr-hd">
              <span>Пользователь</span>
              <span>Email</span>
              <span>Роль</span>
              <span>Статус</span>
              <span>Зарегистрирован</span>
            </div>
            {filtered.map((u) => (
              <div key={u.id} className="admin2-tr">
                <span className="admin2-td-name">
                  <span className="admin2-av">{u.full_name?.charAt(0) || "?"}</span>
                  {u.full_name || "—"}
                </span>
                <span className="admin2-td-email">{u.email}</span>
                <span><Badge text={u.admin_role || u.role} color={ROLE_COLORS[u.admin_role || u.role] || "#6B7280"} /></span>
                <span>{u.is_active ? <span className="admin2-status on"><IconCheckCircle /> Активен</span> : <span className="admin2-status off"><IconXCircle /> Неактивен</span>}</span>
                <span className="admin2-date">{new Date(u.created_at).toLocaleDateString("ru-RU")}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
