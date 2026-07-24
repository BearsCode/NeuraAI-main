"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, useTransition } from "react";

import { AppShellHeader } from "@/components/app-shell-header";
import { Skeleton } from "@/components/skeleton";
import { apiFetch } from "@/lib/client";
import type { ProfileResponse, UpdateProfilePayload } from "@/lib/types";

const roleLabels: Record<string, string> = {
  admin: "Администратор",
  client: "Клиент",
  partner: "Партнёр",
};

type ProfileFormState = {
  full_name: string;
  phone: string;
  company_name: string;
};

const emptyForm: ProfileFormState = {
  full_name: "",
  phone: "",
  company_name: "",
};

export function ProfileShell() {
  const router = useRouter();
  const [session, setSession] = useState<ProfileResponse | null>(null);
  const [form, setForm] = useState<ProfileFormState>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isSaving, startSaveTransition] = useTransition();
  const [isLoggingOut, startLogoutTransition] = useTransition();

  const loadProfile = useCallback(async (showSpinner = false) => {
    if (showSpinner) {
      setLoading(true);
    }

    setError(null);
    const response = await apiFetch<{ user: ProfileResponse }>("/api/auth/session");
    setSession(response.user);
    setForm({
      full_name: response.user.full_name,
      phone: response.user.phone ?? "",
      company_name: response.user.company_name ?? "",
    });
    setLoading(false);
  }, []);

  useEffect(() => {
    void loadProfile(true).catch((loadError: unknown) => {
      setError(
        loadError instanceof Error ? loadError.message : "Не удалось загрузить профиль.",
      );
      setLoading(false);
    });
  }, [loadProfile]);

  async function saveProfile() {
    setError(null);
    setNotice(null);

    const payload: UpdateProfilePayload = {
      full_name: form.full_name.trim(),
      phone: form.phone.trim() || null,
      company_name: form.company_name.trim() || null,
    };

    const response = await apiFetch<{ user: ProfileResponse }>("/api/auth/session", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });

    setSession(response.user);
    setForm({
      full_name: response.user.full_name,
      phone: response.user.phone ?? "",
      company_name: response.user.company_name ?? "",
    });
    setNotice("Профиль сохранён. Рабочее пространство уже использует новые данные.");
    router.refresh();
  }

  async function logout() {
    await apiFetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
    router.refresh();
  }

  const filledFields = [
    Boolean(form.full_name?.trim()),
    Boolean(session?.email),
    Boolean(form.phone?.trim()),
    Boolean(form.company_name?.trim()),
    Boolean(session?.referral_code),
  ].filter(Boolean).length;
  const completionPercent = Math.round((filledFields / 5) * 100);

  return (
    <main className="profile-shell">
      <AppShellHeader
        currentPath="/workspace/profile"
        session={session}
        actions={
          <>
            <button
              className="button-ghost button-sm"
              type="button"
              onClick={() => {
                void loadProfile(true).catch((loadError: unknown) => {
                  setError(
                    loadError instanceof Error
                      ? loadError.message
                      : "Не удалось обновить профиль.",
                  );
                  setLoading(false);
                });
              }}
            >
              Обновить
            </button>
            <button
              className="button-ghost button-danger button-sm"
              type="button"
              disabled={isLoggingOut}
              onClick={() => {
                startLogoutTransition(() => {
                  void logout().catch((logoutError: unknown) => {
                    setError(
                      logoutError instanceof Error
                        ? logoutError.message
                        : "Не удалось выйти из аккаунта.",
                    );
                  });
                });
              }}
            >
              {isLoggingOut ? "Выходим..." : "Выйти"}
            </button>
          </>
        }
      />

      {loading ? (
        <section className="detail-grid top-spacer">
          <article className="panel">
            <Skeleton className="skeleton-label" />
            <Skeleton className="skeleton-heading top-spacer" />
            <Skeleton className="skeleton-block" />
          </article>
          <article className="panel">
            <Skeleton className="skeleton-heading" />
            <Skeleton className="skeleton-block" />
          </article>
        </section>
      ) : null}

      {error ? (
        <div className="error-banner top-spacer">
          <span className="error-icon">!</span>
          <span>{error}</span>
          <button
            className="button-ghost button-sm"
            type="button"
            onClick={() => {
              void loadProfile(true).catch((loadError: unknown) => {
                setError(
                  loadError instanceof Error
                    ? loadError.message
                    : "Не удалось обновить профиль.",
                );
                setLoading(false);
              });
            }}
          >
            Повторить
          </button>
        </div>
      ) : null}

      {!loading && session ? (
        <>
          <section className="workspace-board top-spacer">
            <article className="panel workspace-stage">
              <div className="section-heading">
                <span className="eyebrow">Profile</span>
                <h1>Профиль, который задаёт тон всему workspace.</h1>
                <p className="lead">
                  Держи в порядке имя, контакты и бренд-контекст. Эти данные
                  сразу влияют на onboarding новых проектов и качество AI-ответов.
                </p>
              </div>

              <div className="workspace-meta">
                <span className="chip chip-email">{session.email}</span>
                <span className="chip">{roleLabels[session.role] ?? session.role}</span>
                <span className="chip">
                  Заполнено на {completionPercent}%
                </span>
              </div>

              <div className="signal-grid top-spacer">
                <article className="signal-card">
                  <span className="signal-value">{completionPercent}%</span>
                  <span className="signal-label">Профиль заполнен</span>
                </article>
                <article className="signal-card">
                  <span className="signal-value">
                    {session.referral_code ? "Есть" : "Пока нет"}
                  </span>
                  <span className="signal-label">Реферальный код</span>
                </article>
                <article className="signal-card">
                  <span className="signal-value">
                    {session.company_name ? "Готов" : "Нужно указать"}
                  </span>
                  <span className="signal-label">Брендовый контекст</span>
                </article>
              </div>
            </article>

            <aside className="panel workspace-brief">
              <div className="section-heading">
                <span className="eyebrow">Snapshot</span>
                <h2>Аккаунт под рукой</h2>
              </div>

              <div className="summary-list">
                <div className="summary-row">
                  <span>Email</span>
                  <strong>{session.email}</strong>
                </div>
                <div className="summary-row">
                  <span>Роль</span>
                  <strong>{roleLabels[session.role] ?? session.role}</strong>
                </div>
                <div className="summary-row">
                  <span>Компания</span>
                  <strong>{session.company_name ?? "Не указана"}</strong>
                </div>
                <div className="summary-row">
                  <span>Телефон</span>
                  <strong>{session.phone ?? "Не указан"}</strong>
                </div>
              </div>

              <div className="button-row top-spacer">
                <Link className="button-secondary" href="/workspace">
                  Вернуться к проектам
                </Link>
              </div>
            </aside>
          </section>

          <section className="detail-grid top-spacer">
            <div className="stack">
              <section className="panel">
                <div className="section-heading">
                  <span className="eyebrow">Edit</span>
                  <h2>Основные данные аккаунта</h2>
                  <p className="lead">
                    Здесь обновляются данные, которые видны в шапке рабочего
                    пространства и используются как базовый контекст команды.
                  </p>
                </div>

                <form
                  className="form-grid"
                  onSubmit={(event) => {
                    event.preventDefault();
                    startSaveTransition(() => {
                      void saveProfile().catch((saveError: unknown) => {
                        setError(
                          saveError instanceof Error
                            ? saveError.message
                            : "Не удалось сохранить профиль.",
                        );
                      });
                    });
                  }}
                >
                  <div className="field-grid">
                    <div className="field">
                      <label htmlFor="profile-full-name">Имя и фамилия</label>
                      <input
                        id="profile-full-name"
                        value={form.full_name}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            full_name: event.target.value,
                          }))}
                        placeholder="Алексей Петров"
                        required
                      />
                    </div>

                    <div className="field">
                      <label htmlFor="profile-company">Компания</label>
                      <input
                        id="profile-company"
                        value={form.company_name}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            company_name: event.target.value,
                          }))}
                        placeholder="NeuraAI Studio"
                      />
                    </div>
                  </div>

                  <div className="field-grid">
                    <div className="field">
                      <label htmlFor="profile-email">Email</label>
                      <input id="profile-email" value={session.email} disabled readOnly />
                    </div>

                    <div className="field">
                      <label htmlFor="profile-phone">Телефон</label>
                      <input
                        id="profile-phone"
                        value={form.phone}
                        onChange={(event) =>
                          setForm((current) => ({
                            ...current,
                            phone: event.target.value,
                          }))}
                        placeholder="+7 999 123 45 67"
                      />
                    </div>
                  </div>

                  {notice ? <p className="inline-note">{notice}</p> : null}
                  {error ? <p className="inline-error">{error}</p> : null}

                  <div className="button-row">
                    <button className="button-primary" type="submit" disabled={isSaving}>
                      {isSaving ? "Сохраняем..." : "Сохранить профиль"}
                    </button>
                  </div>
                </form>
              </section>
            </div>

            <div className="stack">
              <article className="insight-card">
                <div className="card-topline">
                  <div>
                    <h3>Доступ и безопасность</h3>
                    <p>Сессия идёт через серверные proxy-роуты и cookies.</p>
                  </div>
                </div>

                <div className="summary-list">
                  <div className="summary-row">
                    <span>Роль доступа</span>
                    <strong>{roleLabels[session.role] ?? session.role}</strong>
                  </div>
                  <div className="summary-row">
                    <span>Статус аккаунта</span>
                    <strong>{session.is_active ? "Активен" : "Отключён"}</strong>
                  </div>
                  <div className="summary-row">
                    <span>Токены</span>
                    <strong>Access + refresh</strong>
                  </div>
                </div>
              </article>

              <article className="insight-card">
                <div className="card-topline">
                  <div>
                    <h3>Что улучшает AI-результат</h3>
                    <p>Небольшие детали профиля сильно помогают качеству выдачи.</p>
                  </div>
                </div>

                <div className="step-list compact-list">
                  <div className={`step-item ${form.company_name ? "is-ready" : ""}`}>
                    <span className="step-badge">01</span>
                    <div>
                      <strong>Укажи актуальную компанию</strong>
                      <p>Так onboarding и шапка проектов будут консистентны.</p>
                    </div>
                  </div>
                  <div className={`step-item ${form.phone ? "is-ready" : ""}`}>
                    <span className="step-badge">02</span>
                    <div>
                      <strong>Добавь контакт для команды</strong>
                      <p>Это удобно для handoff между аккаунтами и продажей.</p>
                    </div>
                  </div>
                  <div className="step-item is-ready">
                    <span className="step-badge">03</span>
                    <div>
                      <strong>Держи email основным источником входа</strong>
                      <p>Он уже используется как ключ авторизации и восстановления.</p>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}
