"use client";

const Icon = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><path d="M12 6v12"/><path d="M9 9h5a2 2 0 0 1 0 4H9"/>
  </svg>
);

export default function Admincosts() {
  return (
    <div className="admin2-page">
      <h2 className="admin2-page-title">Стоимость и токены</h2>
      <div className="admin2-card-placeholder">
        <div className="admin2-placeholder-icon"><Icon /></div>
        <p className="admin2-placeholder-title">Раздел «Стоимость и токены»</p>
        <p className="admin2-placeholder-desc">
          В разработке. Здесь появится интерфейс управления — таблицы, фильтры, формы и аналитика.
        </p>
      </div>
    </div>
  );
}
