"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, useTransition } from "react";

import { apiFetch } from "@/lib/client";
import type { ContentPlanResponse, ProjectOverviewResponse } from "@/lib/types";

type ProjectDetailShellProps = {
  projectId: string;
};

function toStatusClassName(status: string): string {
  return `status-pill ${status.replace(/\s+/g, "_")}`;
}

function formatDate(dateValue: string): string {
  return new Intl.DateTimeFormat("ru", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(dateValue));
}

function formatDateTime(dateValue: string): string {
  return new Intl.DateTimeFormat("ru", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(dateValue));
}

export function ProjectDetailShell({ projectId }: ProjectDetailShellProps) {
  const [overview, setOverview] = useState<ProjectOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGeneratingStrategy, startStrategyTransition] = useTransition();
  const [isGeneratingPlan, startPlanTransition] = useTransition();

  const loadOverview = useCallback(async (showSpinner = false) => {
    if (showSpinner) {
      setLoading(true);
    }

    setError(null);
    const response = await apiFetch<{ overview: ProjectOverviewResponse }>(
      `/api/projects/${projectId}/overview`,
    );
    setOverview(response.overview);
    setLoading(false);
  }, [projectId]);

  useEffect(() => {
    void loadOverview(true).catch((loadError: unknown) => {
      setError(loadError instanceof Error ? loadError.message : "Не удалось загрузить проект.");
      setLoading(false);
    });
  }, [loadOverview]);

  async function generateStrategy() {
    setError(null);
    await apiFetch(`/api/projects/${projectId}/strategy`, {
      method: "POST",
    });
    await loadOverview(false);
  }

  async function generateContentPlan() {
    setError(null);
    await apiFetch<{ contentPlan: ContentPlanResponse }>(
      `/api/projects/${projectId}/content-plan`,
      {
        method: "POST",
        body: JSON.stringify({ period_days: 30, source_mode: "mixed" }),
      },
    );
    await loadOverview(false);
  }

  return (
    <main className="project-shell">
      <header className="project-header">
        <div className="project-overview">
          <span className="eyebrow">Проект</span>
          <h1>{overview?.project.company_name ?? "Загрузка проекта"}</h1>
          <p className="lead">
            {overview?.project.business_description ??
              "Просмотр стратегии, анализа и предстоящих публикаций."}
          </p>
          <div className="project-meta">
            <Link className="button-ghost" href="/workspace">
              Назад
            </Link>
            {overview ? (
              <>
                <span className="chip">{overview.project.industry}</span>
                <span className="chip">{overview.project.city}</span>
                <span className={toStatusClassName(overview.project.strategy_status)}>
                  {overview.project.strategy_status}
                </span>
              </>
            ) : null}
          </div>
        </div>

        <div className="button-row">
          <button
            className="button-primary"
            type="button"
            disabled={isGeneratingStrategy || loading}
            onClick={() => {
              startStrategyTransition(() => {
                void generateStrategy().catch((strategyError: unknown) => {
                  setError(
                    strategyError instanceof Error
                      ? strategyError.message
                      : "Не удалось сгенерировать стратегию.",
                  );
                });
              });
            }}
          >
            {isGeneratingStrategy ? "Генерация..." : "Создать AI-стратегию"}
          </button>

          <button
            className="button-secondary"
            type="button"
            disabled={isGeneratingPlan || loading}
            onClick={() => {
              startPlanTransition(() => {
                void generateContentPlan().catch((planError: unknown) => {
                  setError(
                    planError instanceof Error
                      ? planError.message
                      : "Не удалось создать контент-план.",
                  );
                });
              });
            }}
          >
            {isGeneratingPlan ? "Создание..." : "Создать контент-план на 30 дней"}
          </button>
        </div>
      </header>

      {loading ? <div className="loader">Загрузка проекта...</div> : null}
      {error ? <div className="loader">{error}</div> : null}

      {!loading && overview ? (
        <>
          <section className="stat-grid">
            {overview.dashboard.metrics.map((metric) => (
              <article className="stat-card" key={metric.label}>
                <span>{metric.label.replaceAll("_", " ")}</span>
                <strong>{metric.value}</strong>
                <p>{metric.delta ?? "Данные с бэкенда"}</p>
              </article>
            ))}
          </section>

          <section className="detail-grid top-spacer">
            <div className="stack">
              <article className="insight-card">
                <div className="card-topline">
                  <div>
                    <h3>Бизнес</h3>
                    <p>Основные данные для планирования.</p>
                  </div>
                </div>
                <div className="chip-row">
                  {overview.project.services.map((service) => (
                    <span className="chip" key={service}>
                      {service}
                    </span>
                  ))}
                </div>
                <div className="list-block top-spacer">
                  <p>
                    <strong>Целевая аудитория:</strong> {overview.project.target_audience}
                  </p>
                  <p>
                    <strong>Сайт:</strong> {overview.project.website ?? "Не указан"}
                  </p>
                  <p>
                    <strong>Особенности:</strong>{" "}
                    {overview.project.business_features.length
                      ? overview.project.business_features.join(", ")
                      : "Не указаны"}
                  </p>
                </div>
              </article>

              <article className="insight-card">
                <div className="card-topline">
                  <div>
                    <h3>Стратегия</h3>
                    <p>
                      {overview.strategy
                        ? "Текущее позиционирование и план публикаций."
                        : "Запустите генерацию стратегии, чтобы заполнить этот раздел."}
                    </p>
                  </div>
                </div>

                {overview.strategy ? (
                  <div className="stack">
                    <p>{overview.strategy.positioning}</p>
                    <div className="chip-row">
                      {overview.strategy.channels.map((channel) => (
                        <span className="chip" key={channel}>
                          {channel}
                        </span>
                      ))}
                    </div>
                    <p>
                      <strong>Частота:</strong> {overview.strategy.publishing_frequency}
                    </p>
                    <div className="list-block">
                      <strong>Контент-столпы</strong>
                      <ul>
                        {overview.strategy.content_pillars.map((pillar) => (
                          <li key={pillar}>{pillar}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <div className="empty-state">
                    Стратегия ещё не создана. Используйте кнопку выше.
                  </div>
                )}
              </article>

              <article className="insight-card">
                <div className="card-topline">
                  <div>
                    <h3>Анализ</h3>
                    <p>Рынок, бизнес и конкуренты от AI.</p>
                  </div>
                </div>

                {overview.analysis ? (
                  <div className="insight-grid">
                    <div className="empty-card">
                      <h3>Бизнес</h3>
                      <ul>
                        {overview.analysis.business_analysis.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="empty-card">
                      <h3>Рынок</h3>
                      <ul>
                        {overview.analysis.market_analysis.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="empty-card">
                      <h3>Конкуренты</h3>
                      <ul>
                        {overview.analysis.competitor_analysis.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="empty-card">
                      <h3>Рекомендации</h3>
                      <ul>
                        {(overview.recommendations?.recommendations ??
                          overview.dashboard.ai_recommendations
                        ).map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <div className="empty-state">
                    Анализ появится после первого запуска стратегии.
                  </div>
                )}
              </article>
            </div>

            <div className="stack">
              <article className="insight-card">
                <div className="card-topline">
                  <div>
                    <h3>Контент-план</h3>
                    <p>
                      {overview.contentPlan.items.length
                        ? `Последний план: ${overview.contentPlan.period_days} дней`
                        : "План ещё не создан."}
                    </p>
                  </div>
                </div>

                {overview.contentPlan.items.length ? (
                  <div className="timeline">
                    {overview.contentPlan.items.slice(0, 8).map((item) => (
                      <article className="timeline-item" key={item.content_item_id}>
                        <header>
                          <strong>{formatDate(item.date)}</strong>
                          <span className={toStatusClassName(item.status)}>{item.status}</span>
                        </header>
                        <div className="split-line">
                          <span>
                            {item.platform} / {item.content_type}
                          </span>
                          <span>{item.time}</span>
                        </div>
                        <p>{item.text}</p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    Создайте контент-план, чтобы заполнить ленту публикаций.
                  </div>
                )}
              </article>

              <article className="insight-card">
                <div className="card-topline">
                  <div>
                    <h3>Календарь</h3>
                    <p>Предстоящие публикации из контент-плана.</p>
                  </div>
                </div>
                {overview.dashboard.content_calendar.length ? (
                  <div className="timeline">
                    {overview.dashboard.content_calendar.map((item) => (
                      <article className="timeline-item" key={item.publication_id}>
                        <header>
                          <strong>{item.platform}</strong>
                          <span className={toStatusClassName(item.status)}>{item.status}</span>
                        </header>
                        <p>{formatDateTime(item.scheduled_at)}</p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    Запланированных публикаций пока нет.
                  </div>
                )}
              </article>
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}
