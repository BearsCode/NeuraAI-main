"use client";

const Icon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
  </svg>
);

export default function AdminaiMonitoring() {
  return (
    <div className="admin2-page">
      <h2 className="admin2-page-title">AI Monitoring</h2>
      <div className="admin2-card-placeholder">
        <div className="admin2-placeholder-icon"><Icon /></div>
        <p className="admin2-placeholder-title">Раздел «AI Monitoring»</p>
        <p className="admin2-placeholder-desc">
          В разработке. Здесь появится интерфейс управления — таблицы, фильтры, формы и аналитика.
        </p>
      </div>
    </div>
  );
}
