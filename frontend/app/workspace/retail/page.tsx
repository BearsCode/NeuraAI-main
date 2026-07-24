"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";

type RetailMetrics = {
  total_products: number;
  synced_products: number;
  last_sync: string | null;
  active_offers: number;
};

type SyncProduct = {
  id: string;
  name: string;
  sku: string;
  price: number;
  status: string;
};

function PackageIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.35 }}>
      <path d="M16.5 9.4 7.55 4.24"/>
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
      <polyline points="3.29 7 12 12 20.71 7"/>
      <line x1="12" y1="22" x2="12" y2="12"/>
    </svg>
  );
}

export default function RetailPage() {
  const [metrics, setMetrics] = useState<RetailMetrics | null>(null);
  const [products, setProducts] = useState<SyncProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [m, p] = await Promise.all([
        apiFetch<RetailMetrics>("/api/backend/retail/metrics").catch(() => null),
        apiFetch<SyncProduct[]>("/api/backend/retail/products").catch(() => [] as SyncProduct[]),
      ]);
      setMetrics(m);
      setProducts(Array.isArray(p) ? p : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function syncCatalog() {
    setSyncing(true); setError(null);
    try {
      await apiFetch<{ message: string }>("/api/backend/retail/sync", { method: "POST" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка синхронизации");
    }
    setSyncing(false);
  }

  return (
    <div className="dash-content">
      <header className="dash-header">
        <div className="dash-header-left">
          <h1 className="dash-greeting">Ритейл интеграция</h1>
          <p className="dash-subtitle">Синхронизация товарного каталога для создания контента о продуктах.</p>
        </div>
        <div className="dash-header-right">
          <button className="dash-btn dash-btn-primary" type="button" disabled={syncing} onClick={() => syncCatalog()}>
            {syncing ? "Синхронизация..." : "Синхронизировать каталог"}
          </button>
        </div>
      </header>

      {loading ? (
        <div className="dash-loading">
          <div className="dash-loading-spinner" />
          <span>Загрузка товарного каталога...</span>
        </div>
      ) : error ? (
        <div className="error-banner top-spacer">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={() => load()}>Повторить</button>
        </div>
      ) : (
        <>
          <div className="dash-kpi-row">
            {[
              { label: "Всего товаров", value: metrics?.total_products ?? 0 },
              { label: "Синхронизировано", value: metrics?.synced_products ?? 0 },
              { label: "Активных предложений", value: metrics?.active_offers ?? 0 },
            ].map((kpi) => (
              <article key={kpi.label} className="dash-card dash-kpi-card">
                <div className="dash-kpi-value" style={{ fontSize: 28 }}>{kpi.value}</div>
                <div className="dash-kpi-label">{kpi.label}</div>
              </article>
            ))}
            <article className="dash-card dash-kpi-card">
              <div className="dash-kpi-value" style={{ fontSize: 14, fontWeight: 600 }}>
                {metrics?.last_sync
                  ? new Date(metrics.last_sync).toLocaleDateString("ru", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })
                  : "—"}
              </div>
              <div className="dash-kpi-label">Последняя синхронизация</div>
            </article>
          </div>

          {products.length > 0 ? (
            <div className="dash-card" style={{ padding: 24 }}>
              <div className="dash-card-header" style={{ marginBottom: 16 }}>
                <h2 className="dash-section-title">Товары ({products.length})</h2>
              </div>
              <div className="summary-list">
                {products.map((p) => (
                  <div key={p.id} className="summary-row" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", borderRadius: 10, border: "1px solid var(--border)", gap: 12 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <span style={{ fontWeight: 600, color: "var(--ink)" }}>{p.name}</span>
                      {p.sku && <span style={{ color: "var(--ink-faint)", fontSize: 12, marginLeft: 8 }}>SKU: {p.sku}</span>}
                    </div>
                    <div style={{ display: "flex", gap: 12, alignItems: "center", flexShrink: 0 }}>
                      <strong>{Number(p.price).toLocaleString()} ₽</strong>
                      <span className={`status-pill ${p.status}`}>
                        {p.status === "active" ? "Активен" : "Неактивен"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="dash-card" style={{ padding: 40, textAlign: "center" }}>
              <PackageIcon />
              <p style={{ marginTop: 12, color: "var(--ink-faint)", fontSize: "0.92rem" }}>
                Каталог пуст. Подключите систему учёта и выполните синхронизацию.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
