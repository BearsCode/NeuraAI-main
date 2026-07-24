"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, useTransition } from "react";

import { ProjectOnboardingForm } from "@/components/project-onboarding-form";
import { apiFetch } from "@/lib/client";
import type { ProfileResponse, ProjectResponse, ProjectSummaryResponse } from "@/lib/types";

function toStatusClassName(status: string): string {
  return `status-pill ${status.replace(/\s+/g, "_")}`;
}

export function WorkspaceShell() {
  const router = useRouter();
  const [session, setSession] = useState<ProfileResponse | null>(null);
  const [projects, setProjects] = useState<ProjectSummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoggingOut, startLogoutTransition] = useTransition();

  const loadWorkspace = useCallback(async () => {
    setError(null);

    const [sessionResponse, projectsResponse] = await Promise.all([
      apiFetch<{ user: ProfileResponse }>("/api/auth/session"),
      apiFetch<{ projects: ProjectSummaryResponse[] }>("/api/projects"),
    ]);

    setSession(sessionResponse.user);
    setProjects(projectsResponse.projects);
    setLoading(false);
  }, []);

  useEffect(() => {
    void loadWorkspace().catch((loadError: unknown) => {
      setError(
        loadError instanceof Error ? loadError.message : "Не удалось загрузить рабочее пространство.",
      );
      setLoading(false);
    });
  }, [loadWorkspace]);

  const active = projects.filter((project) => project.strategy_status === "active").length;
  const draft = projects.filter((project) => project.strategy_status === "draft").length;
  const metrics = [
    { label: "Проекты", value: projects.length, note: "Активные клиентские пространства" },
    { label: "AI активен", value: active, note: "Проекты со сгенерированной стратегией" },
    { label: "Требуют настройки", value: draft, note: "Проекты готовы к первому запуску стратегии" },
    {
      label: "Оператор",
      value: session?.role ?? "client",
      note: session?.company_name ?? "Независимый пользователь",
    },
  ];

  async function logout() {
    await apiFetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
    router.refresh();
  }

  function prependProject(project: ProjectResponse) {
    setProjects((current) => [
      {
        project_id: project.project_id,
        company_name: project.company_name,
        industry: project.industry,
        city: project.city,
        strategy_status: project.strategy_status,
      },
      ...current,
    ]);
  }

  return (
    <main className="workspace-shell">
      <header className="workspace-header">
        <div className="workspace-hero">
          <span className="eyebrow">Рабочее пространство</span>
          <h1>Управляйте ростом клиентов с одной панели.</h1>
          <p className="lead">
            Создавайте проекты, отслеживайте статус и запускайте AI-планирование.
          </p>
          <div className="workspace-meta">
            {session ? <span className="chip">{session.full_name}</span> : null}
            {session?.email ? <span className="chip">{session.email}</span> : null}
            {session?.referral_code ? <span className="chip">ref {session.referral_code}</span> : null}
          </div>
        </div>

        <div className="button-row">
          <button
            className="button-ghost"
            type="button"
            onClick={() => {
              router.refresh();
              setLoading(true);
              void loadWorkspace().catch((loadError: unknown) => {
                setError(
                  loadError instanceof Error
                    ? loadError.message
                    : "Не удалось обновить рабочее пространство.",
                );
                setLoading(false);
              });
            }}
          >
            Обновить
          </button>
          <button
            className="button-danger button-ghost"
            type="button"
            disabled={isLoggingOut}
            onClick={() => {
              startLogoutTransition(() => {
                void logout().catch((logoutError: unknown) => {
                  setError(
                    logoutError instanceof Error
                      ? logoutError.message
                      : "Не удалось выйти.",
                  );
                });
              });
            }}
          >
            {isLoggingOut ? "Выход..." : "Выйти"}
          </button>
        </div>
      </header>

      {loading ? <div className="loader">Загрузка рабочего пространства...</div> : null}
      {error ? <div className="loader">{error}</div> : null}

      {!loading && !error ? (
        <>
          <section className="stat-grid">
            {metrics.map((metric) => (
              <article className="stat-card" key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
                <p>{metric.note}</p>
              </article>
            ))}
          </section>

          <section className="top-spacer">
            <ProjectOnboardingForm onCreated={prependProject} />
          </section>

          <section className="panel top-spacer">
            <div className="section-heading">
              <span className="eyebrow">Портфолио</span>
              <h2>Карта проектов</h2>
            </div>

            {projects.length ? (
              <div className="project-grid">
                {projects.map((project) => (
                  <article className="project-card" key={project.project_id}>
                    <div className="card-topline">
                      <div>
                        <h3>{project.company_name}</h3>
                        <p>
                          {project.industry}, {project.city}
                        </p>
                      </div>
                      <span className={toStatusClassName(project.strategy_status)}>
                        {project.strategy_status}
                      </span>
                    </div>
                    <Link
                      className="project-link"
                      href={`/workspace/projects/${project.project_id}`}
                    >
                      Открыть проект
                    </Link>
                  </article>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                Проектов пока нет. Создайте профиль клиента, чтобы запустить AI-планирование.
              </div>
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}
