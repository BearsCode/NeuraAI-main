"use client";

const Icon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3"/><path d="M15 1v3"/><path d="M9 20v3"/><path d="M15 20v3"/><path d="M20 9h3"/><path d="M20 14h3"/><path d="M1 9h3"/><path d="M1 14h3"/>
  </svg>
);

export default function AdminmodelRouter() {
  return (
    <div className="admin2-page">
      <h2 className="admin2-page-title">Model Router</h2>
      <div className="admin2-card-placeholder">
        <div className="admin2-placeholder-icon"><Icon /></div>
        <p className="admin2-placeholder-title">Раздел «Model Router»</p>
        <p className="admin2-placeholder-desc">
          В разработке. Здесь появится интерфейс управления — таблицы, фильтры, формы и аналитика.
        </p>
      </div>
    </div>
  );
}
