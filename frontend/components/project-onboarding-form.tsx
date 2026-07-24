"use client";

import { useState, useTransition } from "react";

import { apiFetch } from "@/lib/client";
import type { BusinessOnboardingPayload, ProjectResponse } from "@/lib/types";

type ProjectOnboardingFormProps = {
  onCreated: (project: ProjectResponse) => void;
};

type FormState = {
  company_name: string;
  business_description: string;
  city: string;
  industry: string;
  services: string;
  website: string;
  phone: string;
  email: string;
  social_links: string;
  target_audience: string;
  competitors: string;
  business_features: string;
};

const initialState: FormState = {
  company_name: "",
  business_description: "",
  city: "",
  industry: "",
  services: "",
  website: "",
  phone: "",
  email: "",
  social_links: "",
  target_audience: "",
  competitors: "",
  business_features: "",
};

function splitToList(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function ProjectOnboardingForm({ onCreated }: ProjectOnboardingFormProps) {
  const [isPending, startTransition] = useTransition();
  const [form, setForm] = useState<FormState>(initialState);
  const [error, setError] = useState<string | null>(null);

  function updateField(key: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submitForm() {
    setError(null);

    const payload: BusinessOnboardingPayload = {
      company_name: form.company_name,
      business_description: form.business_description,
      city: form.city,
      industry: form.industry,
      services: splitToList(form.services),
      website: form.website || null,
      phone: form.phone || null,
      email: form.email || null,
      social_links: splitToList(form.social_links),
      target_audience: form.target_audience,
      competitors: splitToList(form.competitors),
      business_features: splitToList(form.business_features),
    };

    const response = await apiFetch<{ project: ProjectResponse }>("/api/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    setForm(initialState);
    onCreated(response.project);
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <span className="eyebrow">Онбординг</span>
        <h2>Создать новый проект</h2>
      </div>

      <form
        className="form-grid"
        onSubmit={(event) => {
          event.preventDefault();
          startTransition(() => {
            void submitForm().catch((submitError: unknown) => {
              setError(
                submitError instanceof Error
                  ? submitError.message
                  : "Не удалось создать проект.",
              );
            });
          });
        }}
      >
        <div className="field-grid">
          <div className="field">
            <label htmlFor="company_name">Название компании</label>
            <input
              id="company_name"
              value={form.company_name}
              onChange={(event) => updateField("company_name", event.target.value)}
              placeholder="ООО «Маркетинг Про»"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="industry">Сфера деятельности</label>
            <input
              id="industry"
              value={form.industry}
              onChange={(event) => updateField("industry", event.target.value)}
              placeholder="Маркетинг"
              required
            />
          </div>
        </div>

        <div className="field-grid">
          <div className="field">
            <label htmlFor="city">Город</label>
            <input
              id="city"
              value={form.city}
              onChange={(event) => updateField("city", event.target.value)}
              placeholder="Москва"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="services">Услуги</label>
            <input
              id="services"
              value={form.services}
              onChange={(event) => updateField("services", event.target.value)}
              placeholder="реклама, SMM, контент"
            />
          </div>
        </div>

        <div className="field">
          <label htmlFor="business_description">Описание бизнеса</label>
          <textarea
            id="business_description"
            value={form.business_description}
            onChange={(event) => updateField("business_description", event.target.value)}
            placeholder="Опишите бизнес, позиционирование и цели роста."
            required
          />
        </div>

        <div className="field">
          <label htmlFor="target_audience">Целевая аудитория</label>
          <textarea
            id="target_audience"
            value={form.target_audience}
            onChange={(event) => updateField("target_audience", event.target.value)}
            placeholder="Владельцы малого бизнеса, локальные предприниматели..."
            required
          />
        </div>

        <div className="field-grid">
          <div className="field">
            <label htmlFor="website">Сайт</label>
            <input
              id="website"
              value={form.website}
              onChange={(event) => updateField("website", event.target.value)}
              placeholder="https://example.com"
            />
          </div>

          <div className="field">
            <label htmlFor="email">Публичный email</label>
            <input
              id="email"
              type="email"
              value={form.email}
              onChange={(event) => updateField("email", event.target.value)}
              placeholder="hello@example.com"
            />
          </div>
        </div>

        <div className="field-grid">
          <div className="field">
            <label htmlFor="phone">Телефон</label>
            <input
              id="phone"
              value={form.phone}
              onChange={(event) => updateField("phone", event.target.value)}
              placeholder="+7 999 999 99 99"
            />
          </div>

          <div className="field">
            <label htmlFor="social_links">Социальные сети</label>
            <input
              id="social_links"
              value={form.social_links}
              onChange={(event) => updateField("social_links", event.target.value)}
              placeholder="https://t.me/company, https://vk.com/company"
            />
          </div>
        </div>

        <div className="field-grid">
          <div className="field">
            <label htmlFor="competitors">Конкуренты</label>
            <textarea
              id="competitors"
              value={form.competitors}
              onChange={(event) => updateField("competitors", event.target.value)}
              placeholder="Конкурент А, Конкурент Б"
            />
          </div>

          <div className="field">
            <label htmlFor="business_features">Особенности бизнеса</label>
            <textarea
              id="business_features"
              value={form.business_features}
              onChange={(event) => updateField("business_features", event.target.value)}
              placeholder="Круглосуточная поддержка, индивидуальный подход"
            />
          </div>
        </div>

        {error ? <p className="inline-error">{error}</p> : null}

        <div className="button-row">
          <button className="button-primary" type="submit" disabled={isPending}>
            {isPending ? "Создание..." : "Создать проект"}
          </button>
        </div>
      </form>
    </section>
  );
}
