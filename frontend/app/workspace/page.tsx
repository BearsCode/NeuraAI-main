"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";
import type { DashboardData } from "@/lib/types";

/* ── SVG Icons ── */
const IconUsers = () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
const IconGrid = () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>;
const IconFileText = () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>;
const IconGlobe = () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>;
const IconBell = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>;
const IconSparkle = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5z"/></svg>;
const IconGift = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M7.5 8a2.5 2.5 0 0 1 0-5 4.5 4.5 0 0 1 4.5 4.5"/><path d="M16.5 8a2.5 2.5 0 0 0 0-5 4.5 4.5 0 0 0-4.5 4.5"/></svg>;
const IconCheck = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>;
const IconArrowUp = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>;
const IconPlus = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
const IconCheckCircle = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>;
const IconArrowRight = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>;
const IconLightbulb = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>;
const IconMessageSquare = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>;

/* ── Platform-specific icons & colors ── */
const platformMeta: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  instagram: {
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="5"/><circle cx="17.5" cy="6.5" r="1.5"/></svg>,
    color: "#E4405F",
    label: "Instagram",
  },
  telegram: {
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.127.087.775.047 1.19-.094 1.028-.572 4.473-.805 5.954-.095.583-.29.758-.462.777-.35.04-.617-.23-.957-.455-.558-.368-1.144-.575-1.791-.922-.426-.237-.143-.394.026-.576.1-.107.674-.612 1.153-1.052.137-.13.249-.259.114-.492-.072-.134-.36-.214-.568-.314-.268-.128-.536-.257-.802-.38-.256-.13-.523-.263-.409-.512.06-.13.39-.266.674-.385.365-.155 2.124-.88 2.403-1.002.586-.256.798-.216.575-.38a.506.506 0 0 0-.164-.085c-.095-.03-.24-.04-.384-.03-.193.012-.686.134-1.943.62-.476.186-.882.274-1.211.265-.367-.01-.675-.056-.993-.112-.43-.075-.769-.166-1.144-.284-.145-.046-.258-.066-.341-.064-.535.008-1.003.297-1.252.766.08.012.167.034.255.06.366.11.727.223 1.084.347.572.2 1.145.413 1.697.686.316.156.617.374.818.612.21.244.208.47.204.624-.007.21-.237.277-.428.272-.247-.006-.54-.086-.837-.182-.56-.18-1.28-.46-1.779-.586-.344-.089-.702-.136-1.008-.114-.286.02-.56.088-.82.214-.287.137-.542.319-.774.507.223.122.471.224.726.322.27.104.545.2.822.268.548.137 1.035.225 1.395.354.447.16.703.27.818.526.091.2.071.576-.14.876-.218.293-.6.417-.906.478-.722.14-1.432-.001-2.089-.149-1.58-.355-2.58-.885-3.145-1.364-.544-.465-.686-.796-.723-.972-.048-.22.024-.49.088-.65.08-.2.252-.367.422-.497.212-.163.456-.278.716-.386.518-.214 1.066-.367 1.634-.53 1.21-.343 2.442-.682 3.088-.903.768-.255.871-.296.962-.34z"/></svg>,
    color: "#0088CC",
    label: "Telegram",
  },
  vk: {
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M13.162 18.994c.609 0 .858-.406.851-.915-.031-1.917.714-2.949 2.059-1.604 1.488 1.488 1.796 2.519 3.603 2.519h3.2c.808 0 1.126-.26 1.126-.668 0-.863-1.421-2.386-2.625-3.504-1.216-1.128-1.352-1.218-.328-2.558 1.41-1.843 2.42-3.771 2.059-4.194-.332-.389-1.185-.299-2.336-.299h-2.854c-.663 0-.865.228-.865.663 0 1.398-1.919 4.15-2.399 4.15-.245 0-.369-.245-.369-.855V9.195c0-.678-.175-.996-.687-.996H9.839c-.518 0-.829.372-.829.721 0 .758 1.078 1.067 1.078 3.125v2.189c0 .833-.175.99-.554.99-1.011 0-3.463-3.95-4.778-8.117-.282-.891-.658-.908-1.774-.908H.978c-.749 0-.978.373-.978.696 0 .775 1.762 7.642 5.256 11.46C7.479 18.146 9.898 19 12.012 19"/></svg>,
    color: "#0077FF",
    label: "VK",
  },
  youtube: {
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>,
    color: "#FF0000",
    label: "YouTube",
  },
  tiktok: {
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg>,
    color: "#000000",
    label: "TikTok",
  },
  threads: {
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm2.986 13.648c-.537.536-1.36.854-2.366.854-1.398 0-2.466-.507-3.2-1.334-.692-.78-1.063-1.842-1.063-2.918 0-.392.048-.761.14-1.102.728-2.256 2.86-4.097 5.443-4.097 1.408 0 2.606.43 3.46 1.15-.338.444-.753.822-1.217 1.108-.443-.343-.999-.562-1.638-.562-.826 0-1.56.334-2.108.864a2.87 2.87 0 0 0-.695 1.135c-.06.182-.1.374-.118.574.16-.052.33-.088.511-.088 1.166 0 2.07.49 2.654 1.144a2.576 2.576 0 0 1 .71 1.712c0 .645-.239 1.241-.668 1.67zm-1.09-2.206c-.331-.352-.846-.584-1.523-.584-.149 0-.297.013-.44.038a3.984 3.984 0 0 0 .012.455c.072.54.34.997.742 1.303.306.233.68.37 1.088.37.34 0 .618-.1.805-.277.173-.163.27-.379.27-.669 0-.358-.15-.666-.454-.945z"/></svg>,
    color: "#8A8A8A",
    label: "Threads",
  },
};

/* ── Helpers ── */
function getFirstName(name: string | null | undefined): string {
  if (!name) return "пользователь";
  return name.split(/\s+/)[0] ?? name;
}

const kpiColors = ["#3B82F6", "#8B5CF6", "#24C26A", "#F59E0B"];
const kpiIcons = [<IconUsers key={0} />, <IconGrid key={1} />, <IconFileText key={2} />, <IconGlobe key={3} />];

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 6) return "Доброй ночи";
  if (h < 12) return "Доброе утро";
  if (h < 18) return "Добрый день";
  return "Добрый вечер";
}

/* ── Platform quick-connect card ── */
function PlatformConnectCard({
  platform,
  connected,
  onConnect,
}: {
  platform: string;
  connected: boolean;
  onConnect: () => void;
}) {
  const meta = platformMeta[platform] ?? { icon: null, color: "#666", label: platform };
  return (
    <div className={`soc-card ${connected ? "connected" : ""}`} style={{ "--soc-color": meta.color } as React.CSSProperties}>
      <div className="soc-card-icon" style={{ background: `${meta.color}15`, color: meta.color }}>
        {meta.icon}
      </div>
      <div className="soc-card-info">
        <strong>{meta.label}</strong>
        <span>{connected ? "Подключено" : "Не подключено"}</span>
      </div>
      {connected ? (
        <span className="soc-card-badge">
          <IconCheckCircle /> Активен
        </span>
      ) : (
        <button className="soc-card-btn" type="button" onClick={onConnect}>
          <IconPlus /> Подключить
        </button>
      )}
    </div>
  );
}

/* ── Chart ── */
function Chart() {
  return (
    <svg viewBox="0 0 500 160" width="100%" height="140" className="dash-chart-svg">
      <defs>
        <linearGradient id="chartGrad1" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6C4CF6" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#6C4CF6" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="chartGrad2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#24C26A" stopOpacity="0.1" />
          <stop offset="100%" stopColor="#24C26A" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d="M0,145 Q30,135 60,120 T120,95 T180,80 T240,55 T300,62 T360,38 T420,45 T500,28 L500,160 L0,160Z" fill="url(#chartGrad1)" />
      <polyline fill="none" stroke="#6C4CF6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" points="0,145 60,120 120,95 180,80 240,55 300,62 360,38 420,45 500,28" />
      <path d="M0,155 Q30,148 60,138 T120,120 T180,110 T240,92 T300,98 T360,80 T420,85 T500,72 L500,160 L0,160Z" fill="url(#chartGrad2)" />
      <polyline fill="none" stroke="#24C26A" strokeWidth="2" strokeOpacity="0.6" strokeLinecap="round" strokeLinejoin="round" points="0,155 60,138 120,120 180,110 240,92 300,98 360,80 420,85 500,72" />
    </svg>
  );
}

/* ── Main Dashboard Component ── */
export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const result = await apiFetch<DashboardData>("/api/dashboard");
      setData(result);
    } catch {
      setData(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    if (!data) return;
    if (data.user?.admin_role) {
      apiFetch<{ today_path: string }>("/api/admin-path").then((p) => {
        if (p.today_path) router.replace(`/${p.today_path}`);
      }).catch(() => {});
      return;
    }
    if (data.projects.length === 0) {
      router.replace("/onboarding/tariffs");
    } else if (!data.projects[0]?.company_name || data.projects[0]?.company_name === "My Business") {
      router.replace("/onboarding/company");
    }
  }, [data, router]);

  if (loading) {
    return (
      <div className="dash-loading">
        <div className="dash-loading-spinner" />
        <span>Загружаем ваш дашборд...</span>
      </div>
    );
  }

  if (!data?.user) {
    return (
      <div className="dash-loading">
        <div className="dash-empty-icon">👋</div>
        <p>Сессия недоступна.</p>
        <Link href="/login" className="dash-btn dash-btn-primary">Войти</Link>
      </div>
    );
  }

  const name = getFirstName(data.user.full_name);
  const analytics = data.analytics;
  const socials = data.socials;
  const plan = data.contentPlan;
  const publications = data.publications;
  const strategy = data.strategy;
  const recommendations = data.recommendations;
  const connectedPlatforms = new Set(socials.map((s) => s.platform.toLowerCase()));

  const hasStrategy = strategy && strategy.status !== "draft" && strategy.market_analysis?.length > 0;

  const connectedCount = socials.filter(s => s.status === "active").length;
  const publishedCount = publications.filter(p => p.status === "published" || p.status === "completed").length;
  const projectCount = data.projects?.length ?? 0;

  const kpis = [
    { label: "Подключено площадок", value: String(connectedCount) },
    { label: "Опубликовано", value: String(publishedCount) },
    { label: "Проекты", value: String(projectCount) },
    { label: "Стратегия", value: hasStrategy ? "Готова" : "Не создана" },
  ];

  const weekDayNames = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
  const today = new Date();
  const monday = new Date(today);
  monday.setDate(today.getDate() - ((today.getDay() + 6) % 7));
  const weekDays = weekDayNames.map((day, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return { day, date: d };
  });

  function localDateStr(date: Date): string {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  }

  function getPlanForDate(date: Date) {
    const dateStr = localDateStr(date);
    if (!plan?.items) return [];
    return plan.items.filter((item) => item.publish_at.startsWith(dateStr));
  }

  function handleConnect(platform: string) {
    window.location.href = `/workspace/integrations?connect=${platform}`;
  }

  const allPlatforms = ["instagram", "telegram", "vk", "youtube", "tiktok", "threads"];

  return (
    <div className="dash-content">
      {/* ══ HEADER ══ */}
      <header className="dash-header">
        <div>
          <div className="dash-greeting-line">
            <span className="dash-greeting-emoji">👋</span>
            <h1 className="dash-greeting">{getGreeting()}, {name}!</h1>
          </div>
          <p className="dash-subtitle">Нейра — ваш AI-маркетолог. Всё нужное в одном окне.</p>
        </div>
        <div className="dash-header-right">
          <button className="dash-btn dash-btn-ghost" type="button"><IconGift /> Что нового?</button>
          <button className="dash-btn dash-btn-icon" type="button" aria-label="Уведомления">
            <IconBell />
            <span className="dash-badge">3</span>
          </button>
          <Link href="/workspace/content/plan" className="dash-btn dash-btn-primary"><IconSparkle /> Создать контент</Link>
        </div>
      </header>

      {/* ══ KPI ══ */}
      <section className="dash-kpi-row">
        {kpis.map((kpi, i) => {
          const color = kpiColors[i] ?? kpiColors[0];
          const icon = kpiIcons[i] ?? kpiIcons[0];
          return (
            <article key={kpi.label} className="dash-card dash-kpi-card" style={{ "--kpi-accent": color } as React.CSSProperties}>
              <div className="dash-kpi-top">
                <span className="dash-kpi-icon-wrap" style={{ background: `${color}12`, color }}>
                  {icon}
                </span>
              </div>
              <div className="dash-kpi-value">{kpi.value}</div>
              <div className="dash-kpi-label">{kpi.label}</div>
            </article>
          );
        })}
      </section>

      {/* ══ SOCIAL QUICK CONNECT ══ */}
      <section className="dash-section-label">
        <h2>📱 Подключенные площадки</h2>
        <Link href="/workspace/integrations" className="dash-link">Все интеграции →</Link>
      </section>
      <div className="soc-grid">
        {allPlatforms.map((p) => (
          <PlatformConnectCard
            key={p}
            platform={p}
            connected={connectedPlatforms.has(p)}
            onConnect={() => handleConnect(p)}
          />
        ))}
      </div>

      {/* ══ CONTENT PLAN ══ */}
      <section className="dash-section-label">
        <h2>📅 Контент-план на неделю</h2>
        {!plan && <Link href="/workspace/content/plan" className="dash-link">Создать план →</Link>}
      </section>
      <section className="dash-card dash-plan-card">
        <div className="dash-plan-grid">
          {weekDays.map((wd) => {
            const items = getPlanForDate(wd.date);
            const isToday = localDateStr(wd.date) === localDateStr(today);
            return (
              <div key={wd.day} className={`dash-plan-col ${isToday ? "today" : ""}`}>
                <div className="dash-plan-col-header">
                  <strong>{wd.day}</strong>
                  <span className="dash-plan-date">{wd.date.toLocaleDateString("ru", { day: "numeric", month: "short" })}</span>
                  <span className="dash-plan-count">{items.length}</span>
                </div>
                <div className="dash-plan-thumbs">
                  {items.slice(0, 4).map((item) => {
                    const meta = platformMeta[item.platform.toLowerCase()];
                    return (
                      <div key={item.content_item_id} className="dash-plan-thumb" style={meta ? { color: meta.color, borderColor: `${meta.color}30` } : {}}>
                        {meta?.icon ?? <span>◎</span>}
                      </div>
                    );
                  })}
                </div>
                <Link href="/workspace/content/plan" className="dash-plan-add"><IconPlus /></Link>
              </div>
            );
          })}
        </div>
      </section>

      {/* ══ BOTTOM ROW ══ */}
      <div className="dash-cols-2-1">

        {/* Strategy + Chart */}
        <div className="dash-strategy-col">

          {/* Strategy */}
          <article className="dash-card dash-strategy-card">
            <div className="dash-strategy-inner">
              <div className="dash-strategy-left">
                <span className="dash-card-badge">AI-стратегия</span>
                <h2 className="dash-section-title">Маркетинговая стратегия</h2>
                <p className="dash-strategy-meta">
                  {hasStrategy ? `Статус: ${strategy!.status}` : "ещё не создана"}
                </p>
                <p className="dash-strategy-desc">
                  {hasStrategy
                    ? (strategy!.market_analysis[0] ?? "AI проанализировал ваш бизнес и построил стратегию продвижения.")
                    : "Запустите анализ бизнеса — AI изучит вашу нишу, конкурентов и аудиторию."}
                </p>
                <Link href="/workspace/strategy" className="dash-strategy-link">
                  {hasStrategy ? "Смотреть стратегию" : "Запустить анализ"} <IconArrowRight />
                </Link>
              </div>
              <div className="dash-strategy-right">
                <div className="dash-progress-ring">
                  <svg viewBox="0 0 100 100" width="120" height="120">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#ECECF2" strokeWidth="8" />
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#6C4CF6" strokeWidth="8"
                      strokeDasharray={`${2 * Math.PI * 42}`}
                      strokeDashoffset={`${2 * Math.PI * 42 * (1 - (hasStrategy ? 0.85 : 0.05))}`}
                      strokeLinecap="round" transform="rotate(-90 50 50)" />
                  </svg>
                  <span className="dash-progress-text">{hasStrategy ? "85%" : "0%"}</span>
                </div>
                <span className="dash-progress-label">{hasStrategy ? "Выполнение стратегии" : "Ожидание запуска"}</span>
                <div className="dash-checklist">
                  {["Анализ бизнеса", "Анализ конкурентов", "Анализ аудитории", "Контент-стратегия", "Контент-план"].map((step, i) => (
                    <div key={step} className={`dash-checklist-item ${hasStrategy && i < 4 ? "done" : ""}`}>
                      {hasStrategy && i < 4 ? <IconCheck /> : <span className="dash-checkbox-empty" />}
                      <span>{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </article>

          {/* Chart */}
          <article className="dash-card dash-stat-card">
            <div className="dash-card-header">
              <h2 className="dash-section-title">📈 Динамика показателей</h2>
              <select className="dash-select" defaultValue="7">
                <option value="7">7 дней</option>
                <option value="30">30 дней</option>
                <option value="90">90 дней</option>
              </select>
            </div>
            <div className="dash-chart">
              <Chart />
            </div>
          </article>
        </div>

        {/* Right Column */}
        <div className="dash-right-stack">

          {/* Posts */}
          <article className="dash-card dash-posts-card">
            <div className="dash-card-header">
              <h2 className="dash-section-title">📬 Недавние публикации</h2>
              <Link href="/workspace/publications/history" className="dash-link">Все →</Link>
            </div>
            <div className="dash-posts-list">
              {publications.length === 0 ? (
                <div className="dash-empty-state-sm">
                  <div className="dash-empty-icon-sm">📝</div>
                  <p>Публикаций пока нет. Создайте контент-план!</p>
                </div>
              ) : publications.slice(0, 5).map((pub) => {
                const meta = platformMeta[pub.platform.toLowerCase()];
                return (
                  <div key={pub.publication_id} className="dash-post-row">
                    <div className="dash-post-thumb" style={meta ? { color: meta.color, background: `${meta.color}10` } : {}}>
                      {meta?.icon ?? <span>◎</span>}
                    </div>
                    <div className="dash-post-info">
                      <strong>{meta?.label ?? pub.platform}</strong>
                      <div className="dash-post-meta">
                        <span>{new Date(pub.scheduled_at).toLocaleDateString("ru")}</span>
                      </div>
                    </div>
                    <span className={`dash-status-published ${pub.status === "published" || pub.status === "completed" ? "done" : ""}`}>
                      {pub.status === "published" || pub.status === "completed" ? "Опубликовано" : pub.status}
                    </span>
                  </div>
                );
              })}
            </div>
          </article>

          {/* AI Tips */}
          <article className="dash-card dash-tips-card">
            <div className="dash-card-header">
              <h2 className="dash-section-title">💡 AI рекомендации</h2>
              <span className="dash-tag new">Новое</span>
            </div>
            <div className="dash-tips-list">
              {recommendations.length === 0 ? (
                <div className="dash-empty-state-sm">
                  <div className="dash-empty-icon-sm">🤖</div>
                  <p>Подключите аналитику и площадки, чтобы получать рекомендации.</p>
                </div>
              ) : recommendations.slice(0, 3).map((rec, i) => {
                const tipText = typeof rec === "string" ? rec : ((rec as Record<string, unknown>).summary as string) || JSON.stringify(rec);
                return (
                  <div key={i} className="dash-tip-item">
                    <span className="dash-tip-icon"><IconLightbulb /></span>
                    <div>
                      <strong>Рекомендация {i + 1}</strong>
                      <p>{tipText}</p>
                    </div>
                  </div>
                );
              })}
            </div>
            {recommendations.length > 0 && (
              <Link href="/workspace/ai-assistant" className="dash-link">Все рекомендации →</Link>
            )}
          </article>

          {/* Manager */}
          <article className="dash-card dash-manager-card">
            <div className="dash-card-header">
              <h2 className="dash-section-title">🎯 Ваш менеджер</h2>
            </div>
            <div className="dash-manager-body">
              <div className="dash-manager-avatar"><IconMessageSquare /></div>
              <div className="dash-manager-info">
                <strong>Анастасия</strong>
                <span>Персональный менеджер</span>
                <p>Поможет с настройкой, ответит на вопросы и предложит новые форматы.</p>
              </div>
              <button className="dash-btn dash-btn-primary full" type="button">Написать в чат</button>
            </div>
          </article>
        </div>
      </div>
    </div>
  );
}
