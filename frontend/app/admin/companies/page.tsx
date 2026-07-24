"use client";

import { useState } from "react";

const companies = [
  { id: "1", name: "ООО Технологии", email: "info@tech.ru", users: 12, tariff: "Business", status: "active", created: "12.03.2025" },
  { id: "2", name: "ИП Марков", email: "markov@mail.ru", users: 3, tariff: "Startup", status: "active", created: "05.01.2025" },
  { id: "3", name: "АО МедиаГрупп", email: "media@group.ru", users: 25, tariff: "Enterprise", status: "active", created: "20.11.2024" },
  { id: "4", name: "ООО Креатив", email: "hello@creativ.ru", users: 7, tariff: "Business", status: "trial", created: "01.06.2025" },
  { id: "5", name: "ИП Соколова", email: "sokolova@ya.ru", users: 1, tariff: "Free", status: "disabled", created: "15.02.2025" },
];

const statusClass = (s: string) => s === "active" ? "on" : s === "trial" ? "trial" : "off";
const statusLabel = (s: string) => s === "active" ? "Активна" : s === "trial" ? "Триал" : "Отключена";

export default function AdminCompanies() {
  const [search, setSearch] = useState("");
  const filtered = companies.filter((c) => c.name.toLowerCase().includes(search.toLowerCase()) || c.email.includes(search));
  return (
    <div className="admin2-page">
      <h2 className="admin2-page-title">Компании</h2>
      <p style={{ color: "var(--atext-soft)", fontSize: "0.87rem", marginTop: "-16px", marginBottom: "20px" }}>
        Управление компаниями и организациями платформы
      </p>
      <div className="admin2-card" style={{ flexDirection: "column", alignItems: "stretch", padding: 0 }}>
        <div className="admin2-toolbar">
          <div className="admin2-search">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input placeholder="Поиск компании..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <span className="admin2-count">{filtered.length} компаний</span>
        </div>
        <div className="admin2-table">
          <div className="admin2-tr admin2-tr-hd">
            <span>Компания</span><span>Email</span><span>Пользователей</span><span>Тариф</span><span>Статус</span><span>Создана</span>
          </div>
          {filtered.map((c) => (
            <div key={c.id} className="admin2-tr">
              <span className="admin2-td-name"><span className="admin2-av">{c.name[0]}</span>{c.name}</span>
              <span className="admin2-td-email">{c.email}</span>
              <span>{c.users}</span>
              <span><span className="admin2-badge" style={{ background: "#3B82F6" }}>{c.tariff}</span></span>
              <span><span className={"admin2-status " + statusClass(c.status)}>{statusLabel(c.status)}</span></span>
              <span className="admin2-date">{c.created}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
