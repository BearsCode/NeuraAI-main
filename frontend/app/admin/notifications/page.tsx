"use client";

const Icon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
  </svg>
);

export default function Adminnotifications() {
  return (
    <div className="admin2-page">
      <h2 className="admin2-page-title">Уведомления</h2>
      <div className="admin2-card-placeholder">
        <div className="admin2-placeholder-icon"><Icon /></div>
        <p className="admin2-placeholder-title">Раздел «Уведомления»</p>
        <p className="admin2-placeholder-desc">
          В разработке. Здесь появится интерфейс управления — таблицы, фильтры, формы и аналитика.
        </p>
      </div>
    </div>
  );
}
