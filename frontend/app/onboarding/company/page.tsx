"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/client";

export default function CompanyOnboardingPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    company_name: "",
    industry: "",
    city: "",
    phone: "",
    description: "",
    website: "",
    target_audience: "",
    competitors: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await apiFetch("/api/backend/business/profile", {
        method: "POST",
        body: JSON.stringify({
          company_name: form.company_name,
          description: form.description || `${form.company_name} — компания для AI-маркетинга`,
          city: form.city || "Не указан",
          industry: form.industry || "other",
          services: [],
          website: form.website || null,
          phone: form.phone || null,
          email: null,
          target_audience: form.target_audience || "Клиенты, заинтересованные в услугах компании",
          competitors: form.competitors ? form.competitors.split(",").map((s) => s.trim()).filter(Boolean) : [],
          features: [],
          social_links: [],
          offer_accepted: true,
          data_confirmed: true,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        }),
      });
      router.push("/workspace");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка сохранения");
    }
    setSubmitting(false);
  }

  return (
    <main className="auth-shell">
      <div className="auth-intro">
        <span className="eyebrow">Шаг 2 из 2</span>
        <h1>Информация о компании</h1>
        <p className="lead">
          Расскажите о вашем бизнесе, чтобы AI-маркетолог мог создавать
          релевантный контент.
        </p>
      </div>

      <section className="auth-card">
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="company_name">Название компании *</label>
            <input
              id="company_name"
              value={form.company_name}
              onChange={(e) => update("company_name", e.target.value)}
              placeholder="ООО «Маркетинг Про»"
              required
            />
          </div>

          <div className="field-grid">
            <div className="field">
              <label htmlFor="industry">Сфера деятельности</label>
              <select
                id="industry"
                value={form.industry}
                onChange={(e) => update("industry", e.target.value)}
              >
                <option value="other">Другое</option>
                <option value="tech">IT и технологии</option>
                <option value="finance">Финансы</option>
                <option value="retail">Ритейл</option>
                <option value="education">Образование</option>
                <option value="healthcare">Медицина</option>
                <option value="real_estate">Недвижимость</option>
                <option value="tourism">Туризм</option>
                <option value="entertainment">Развлечения</option>
                <option value="food">FMCG / Продукты</option>
                <option value="manufacturing">Производство</option>
              </select>
            </div>

            <div className="field">
              <label htmlFor="city">Город</label>
              <input
                id="city"
                value={form.city}
                onChange={(e) => update("city", e.target.value)}
                placeholder="Москва"
              />
            </div>
          </div>

          <div className="field">
            <label htmlFor="website">Сайт</label>
            <input
              id="website"
              type="url"
              value={form.website}
              onChange={(e) => update("website", e.target.value)}
              placeholder="https://example.com"
            />
          </div>

          <div className="field">
            <label htmlFor="description">Описание компании</label>
            <textarea
              id="description"
              rows={3}
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
              placeholder="Чем занимается ваша компания? Коротко о главном..."
            />
          </div>

          <div className="field">
            <label htmlFor="target_audience">Целевая аудитория</label>
            <textarea
              id="target_audience"
              rows={2}
              value={form.target_audience}
              onChange={(e) => update("target_audience", e.target.value)}
              placeholder="Кто ваши клиенты? Например: владельцы малого бизнеса от 25 до 45 лет"
            />
          </div>

          <div className="field">
            <label htmlFor="competitors">Конкуренты</label>
            <input
              id="competitors"
              value={form.competitors}
              onChange={(e) => update("competitors", e.target.value)}
              placeholder="Названия конкурентов через запятую"
            />
          </div>

          {error && <p className="inline-error">{error}</p>}

          <div className="button-row">
            <button className="button-primary" type="submit" disabled={submitting || !form.company_name}>
              {submitting ? "Сохраняем..." : "Перейти в рабочий пространство"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
