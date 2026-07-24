"use client";

const Icon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 3h6v5l4 11H5l4-11V3z"/><line x1="9" y1="3" x2="15" y2="3"/>
  </svg>
);

export default function Admintesting() {
  return (
    <div className="admin2-page">
      <h2 className="admin2-page-title">Центр тестирования</h2>
      <div className="admin2-card-placeholder">
        <div className="admin2-placeholder-icon"><Icon /></div>
        <p className="admin2-placeholder-title">Раздел «Центр тестирования»</p>
        <p className="admin2-placeholder-desc">
          В разработке. Здесь появится интерфейс управления — таблицы, фильтры, формы и аналитика.
        </p>
      </div>
    </div>
  );
}
