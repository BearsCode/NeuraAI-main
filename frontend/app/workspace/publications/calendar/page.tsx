"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/client";
import type { PublishedPost } from "@/lib/types";

const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const MONTHS = [
  "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
];

const platformEmoji: Record<string, string> = {
  telegram: "✈️",
  instagram: "📸",
  vk: "💬",
  facebook: "📘",
  youtube: "▶️",
  tiktok: "🎵",
  twitter: "🐦",
  linkedin: "💼",
  website: "🌐",
};

function emojiFor(platform: string): string {
  return platformEmoji[platform.toLowerCase()] ?? "📄";
}

export default function CalendarPage() {
  const [posts, setPosts] = useState<PublishedPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const now = new Date();
  const [currentYear, setCurrentYear] = useState(now.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(now.getMonth());

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<PublishedPost[]>("/api/backend/publishing/history");
      setPosts(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  function prevMonth() {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear((y) => y - 1);
    } else {
      setCurrentMonth((m) => m - 1);
    }
  }

  function nextMonth() {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear((y) => y + 1);
    } else {
      setCurrentMonth((m) => m + 1);
    }
  }

  function today() {
    const n = new Date();
    setCurrentMonth(n.getMonth());
    setCurrentYear(n.getFullYear());
  }

  function postsForDay(year: number, month: number, day: number) {
    const prefix = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return posts.filter((p) => p.scheduled_at?.startsWith(prefix));
  }

  function isSameDay(day: number, month: number, year: number) {
    const n = new Date();
    return day === n.getDate() && month === n.getMonth() && year === n.getFullYear();
  }

  const firstWeekday = new Date(currentYear, currentMonth, 1).getDay();
  const offset = (firstWeekday + 6) % 7;
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const daysInPrev = new Date(currentYear, currentMonth, 0).getDate();

  type Cell = { day: number; month: number; year: number; other: boolean };
  const cells: Cell[] = [];

  for (let i = 0; i < offset; i++) {
    const d = daysInPrev - offset + 1 + i;
    const m = currentMonth === 0 ? 11 : currentMonth - 1;
    const y = currentMonth === 0 ? currentYear - 1 : currentYear;
    cells.push({ day: d, month: m, year: y, other: true });
  }

  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({ day: d, month: currentMonth, year: currentYear, other: false });
  }

  const rem = 7 - (cells.length % 7 === 0 ? 7 : cells.length % 7);
  if (rem > 0 && rem < 7) {
    for (let d = 1; d <= rem; d++) {
      const m = currentMonth === 11 ? 0 : currentMonth + 1;
      const y = currentMonth === 11 ? currentYear + 1 : currentYear;
      cells.push({ day: d, month: m, year: y, other: true });
    }
  }

  return (
    <div className="calendar-page">
      <header>
        <span className="eyebrow">Календарь публикаций</span>
        <h1
          style={{
            fontSize: "1.75rem",
            fontWeight: 700,
            letterSpacing: "-0.03em",
            marginTop: 4,
            marginBottom: 0,
          }}
        >
          {MONTHS[currentMonth]} {currentYear}
        </h1>
      </header>

      {loading ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 64,
          }}
        >
          <div className="loading-spinner" />
        </div>
      ) : error ? (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "var(--radius-sm)",
            background: "var(--error-soft)",
            color: "var(--error)",
            fontSize: "0.88rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>{error}</span>
          <button className="button-ghost button-sm" type="button" onClick={load}>
            Повторить
          </button>
        </div>
      ) : (
        <>
          <div className="calendar-nav">
            <button
              className="button-ghost"
              type="button"
              onClick={prevMonth}
              aria-label="Предыдущий месяц"
            >
              ◀
            </button>

            <div className="calendar-nav-center">
              <button
                className="button-ghost button-sm"
                type="button"
                onClick={prevMonth}
                aria-label="Предыдущий месяц"
              >
                ◀
              </button>
              <h2 className="calendar-title">
                {MONTHS[currentMonth]} {currentYear}
              </h2>
              <button
                className="button-ghost button-sm"
                type="button"
                onClick={nextMonth}
                aria-label="Следующий месяц"
              >
                ▶
              </button>
            </div>

            <button className="button-secondary" type="button" onClick={today}>
              Сегодня
            </button>
          </div>

          <div className="calendar-grid">
            {WEEKDAYS.map((d) => (
              <div key={d} className="calendar-weekday">
                {d}
              </div>
            ))}

            {cells.map((c) => {
              const dayPosts = postsForDay(c.year, c.month, c.day);
              const cellToday = isSameDay(c.day, c.month, c.year);

              return (
                <div
                  key={`${c.year}-${c.month}-${c.day}`}
                  className={[
                    "calendar-day",
                    cellToday && "today",
                    c.other && "other-month",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <span className="calendar-day-number">{c.day}</span>
                  {dayPosts.length > 0 && (
                    <div className="calendar-posts">
                      {dayPosts.map((p) => (
                        <div
                          key={p.publication_id}
                          className={`calendar-post ${p.status}`}
                        >
                          {emojiFor(p.platform)}
                          <span>{p.platform}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {posts.length === 0 && (
            <div className="empty-state">
              <p>Нет публикаций</p>
              <p style={{ marginTop: 4 }}>
                Публикации из истории будут отображаться в календаре.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
