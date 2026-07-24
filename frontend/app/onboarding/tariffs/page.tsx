"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const monthlyPlans = [
  {
    code: "starter",
    name: "Стартовый",
    price: "0 ₽",
    period: "на 14 дней",
    description: "Попробуйте AI-маркетинг бесплатно",
    features: [
      "1 проект",
      "Базовый AI-ассистент",
      "План контента до 30 дней",
      "Подключение 2 соцсетей",
      "Базовая аналитика",
    ],
    cta: "Начать бесплатно",
    highlight: false,
  },
  {
    code: "basic",
    name: "Базовый",
    price: "2 990 ₽",
    period: "в месяц",
    description: "Для активного роста",
    features: [
      "До 3 проектов",
      "Продвинутый AI-ассистент",
      "План контента до 90 дней",
      "Подключение всех соцсетей",
      "Полная аналитика",
      "Автопостинг",
    ],
    cta: "Выбрать тариф",
    highlight: true,
  },
  {
    code: "pro",
    name: "Профессиональный",
    price: "7 990 ₽",
    period: "в месяц",
    description: "Максимум возможностей",
    features: [
      "Безлимит проектов",
      "Экспертный AI-ассистент",
      "Неограниченный контент-план",
      "Все соцсети + блог",
      "AI-аватар",
      "Приоритетная поддержка",
      "API-доступ",
    ],
    cta: "Выбрать тариф",
    highlight: false,
  },
];

type Plan = (typeof monthlyPlans)[number] & { originalPrice?: string };

const yearlyPlans: Plan[] = [
  { ...monthlyPlans[0], price: "0 ₽", period: "на 14 дней" },
  { ...monthlyPlans[1], price: "2 390 ₽", period: "в месяц при годовой подписке", originalPrice: "2 990 ₽" },
  { ...monthlyPlans[2], price: "6 390 ₽", period: "в месяц при годовой подписке", originalPrice: "7 990 ₽" },
];

const comparisonFeatures = [
  { name: "Проекты", starter: "1", basic: "До 3", pro: "Безлимит" },
  { name: "AI-ассистент", starter: "Базовый", basic: "Продвинутый", pro: "Экспертный" },
  { name: "План контента", starter: "До 30 дней", basic: "До 90 дней", pro: "Неограниченный" },
  { name: "Соцсети", starter: "2 сети", basic: "Все сети", pro: "Все + блог" },
  { name: "Аналитика", starter: "Базовая", basic: "Полная", pro: "Полная" },
  { name: "Автопостинг", starter: "—", basic: "✓", pro: "✓" },
  { name: "AI-аватар", starter: "—", basic: "—", pro: "✓" },
  { name: "Приоритетная поддержка", starter: "—", basic: "—", pro: "✓" },
  { name: "API-доступ", starter: "—", basic: "—", pro: "✓" },
];

const faqs = [
  {
    q: "Можно ли перейти на другой тариф позже?",
    a: "Да, вы можете сменить тариф в любое время в настройках аккаунта. Разница в стоимости будет пересчитана пропорционально.",
  },
  {
    q: "Что произойдёт после окончания пробного периода?",
    a: "Через 14 дней доступ к базовым функциям ограничится. Чтобы продолжить работу, достаточно выбрать подходящий платный тариф — все данные сохранятся.",
  },
  {
    q: "Предоставляете ли вы скидки при оплате за год?",
    a: "Да! При выборе годовой подписки вы получаете скидку 20% на тарифы «Базовый» и «Профессиональный».",
  },
  {
    q: "Можно ли отменить подписку в любой момент?",
    a: "Конечно. Вы можете отменить подписку в один клик без штрафов и комиссий. Доступ к оплаченному периоду сохранится до его окончания.",
  },
];

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

export default function TariffsPage() {
  const router = useRouter();
  const [selected, setSelected] = useState("starter");
  const [yearly, setYearly] = useState(false);

  const plans: Plan[] = yearly ? yearlyPlans : monthlyPlans;

  function handleContinue() {
    const planCode = selected;
    const billing = yearly && selected !== "starter" ? "yearly" : "monthly";
    localStorage.setItem("selected_plan", planCode);
    localStorage.setItem("billing_period", billing);
    router.push("/onboarding/company");
  }

  return (
    <main className="auth-shell">
      <style>{`
        .toggle-wrap {
          display: inline-flex;
          align-items: center;
          gap: 12px;
          background: var(--surface-muted);
          border: 1px solid var(--border);
          border-radius: var(--radius-pill);
          padding: 4px;
        }
        .toggle-btn {
          position: relative;
          padding: 8px 20px;
          border: none;
          border-radius: var(--radius-pill);
          font-size: 0.85rem;
          font-weight: 600;
          cursor: pointer;
          transition: all var(--transition);
          font-family: inherit;
        }
        .toggle-btn:first-child {
          background: transparent;
          color: var(--ink-soft);
        }
        .toggle-btn:last-child {
          background: transparent;
          color: var(--ink-soft);
        }
        .toggle-btn.active {
          background: var(--surface);
          color: var(--ink);
          box-shadow: var(--shadow-sm);
        }
        .toggle-save {
          font-size: 0.72rem;
          color: var(--accent);
          font-weight: 600;
          white-space: nowrap;
        }
        .comparison-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.88rem;
        }
        .comparison-table th {
          text-align: left;
          padding: 12px 16px;
          font-weight: 700;
          color: var(--ink);
          border-bottom: 2px solid var(--border);
        }
        .comparison-table th:first-child { color: var(--ink-soft); font-weight: 600; }
        .comparison-table td {
          padding: 12px 16px;
          border-bottom: 1px solid var(--border);
          color: var(--ink);
        }
        .comparison-table td:first-child {
          color: var(--ink-soft);
          font-weight: 500;
        }
        .comparison-table tr:last-child td {
          border-bottom: none;
        }
        .comparison-table tr:hover td {
          background: var(--surface-muted);
        }
        .faq-item {
          border-bottom: 1px solid var(--border);
          padding: 20px 0;
        }
        .faq-item:first-child { padding-top: 0; }
        .faq-item:last-child { border-bottom: none; padding-bottom: 0; }
        .faq-question {
          font-weight: 600;
          font-size: 0.95rem;
          color: var(--ink);
          margin-bottom: 8px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        .faq-answer {
          font-size: 0.88rem;
          color: var(--ink-soft);
          line-height: 1.7;
        }
        .tariff-original {
          text-decoration: line-through;
          color: var(--ink-faint);
          font-size: 0.82rem;
          font-weight: 400;
        }
        @media (max-width: 900px) {
          .auth-shell {
            grid-template-columns: 1fr;
            gap: 32px;
          }
          .auth-intro { order: 0; }
          .tariff-grid { max-width: 100%; }
        }
      `}</style>

      <div className="auth-intro">
        <span className="eyebrow">Шаг 1 из 2</span>
        <h1>Выберите тариф</h1>
        <p className="lead">
          Начните с 14-дневного пробного периода — никаких платежей до окончания.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
        {/* Toggle */}
        <div style={{ display: "flex", justifyContent: "center" }}>
          <div className="toggle-wrap">
            <button
              type="button"
              className={`toggle-btn ${!yearly ? "active" : ""}`}
              onClick={() => setYearly(false)}
            >
              Ежемесячно
            </button>
            <button
              type="button"
              className={`toggle-btn ${yearly ? "active" : ""}`}
              onClick={() => setYearly(true)}
            >
              Ежегодно
            </button>
            <span className="toggle-save">–20%</span>
          </div>
        </div>

        {/* Pricing Cards */}
        <section className="tariff-grid stagger-grid">
          {plans.map((plan, i) => (
            <button
              key={plan.code}
              type="button"
              onClick={() => setSelected(plan.code)}
              className={`tariff-card ${selected === plan.code ? "selected" : ""} ${plan.highlight ? "highlight" : ""}`}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "16px",
                padding: "32px 24px",
                textAlign: "center",
                alignItems: "center",
                animationDelay: `${i * 0.1}s`,
              }}
            >
              {plan.highlight && <span className="tariff-badge">Популярное</span>}
              <h3 className="tariff-name" style={{ fontSize: "1.15rem" }}>{plan.name}</h3>
              <p className="tariff-desc" style={{ fontSize: "0.85rem", minHeight: "2.6em" }}>{plan.description}</p>
              <div className="tariff-price" style={{ justifyContent: "center" }}>
                <span className="tariff-amount" style={{ fontSize: "2.2rem" }}>{plan.price}</span>
                <span className="tariff-period">{plan.period}</span>
              </div>
              {plan.originalPrice && (
                <span className="tariff-original">{plan.originalPrice} / мес</span>
              )}
              <ul className="tariff-features" style={{ textAlign: "left", width: "100%", marginTop: "4px" }}>
                {plan.features.map((f) => (
                  <li key={f}>
                    <CheckIcon />
                    {f}
                  </li>
                ))}
              </ul>
              <span
                className={`button-${plan.code === "starter" ? "secondary" : "primary"}`}
                style={{
                  width: "100%",
                  marginTop: "auto",
                  fontSize: "0.92rem",
                  padding: "0 20px",
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelected(plan.code);
                }}
              >
                {plan.cta}
              </span>
            </button>
          ))}
        </section>

        {/* Feature Comparison */}
        <section className="feature-panel" style={{ marginTop: 0 }}>
          <div className="section-heading" style={{ marginBottom: "20px" }}>
            <h2>Сравнение тарифов</h2>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Функция</th>
                  <th>Стартовый</th>
                  <th>Базовый</th>
                  <th>Профессиональный</th>
                </tr>
              </thead>
              <tbody>
                {comparisonFeatures.map((feat) => (
                  <tr key={feat.name}>
                    <td>{feat.name}</td>
                    <td>{feat.starter}</td>
                    <td>{feat.basic}</td>
                    <td>{feat.pro}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* FAQ */}
        <section className="feature-panel" style={{ marginTop: 0 }}>
          <div className="section-heading" style={{ marginBottom: "12px" }}>
            <h2>Часто задаваемые вопросы</h2>
          </div>
          <div>
            {faqs.map((faq) => (
              <div key={faq.q} className="faq-item">
                <div className="faq-question">{faq.q}</div>
                <div className="faq-answer">{faq.a}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Continue */}
        <div className="button-row" style={{ justifyContent: "center" }}>
          <button className="button-primary" onClick={handleContinue} style={{ minWidth: 300 }}>
            Продолжить
          </button>
        </div>
        <p className="auth-hint" style={{ textAlign: "center" }}>
          Отмена в любой момент. Без комиссий.
        </p>
      </div>
    </main>
  );
}
