"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";

export default function AdminLoginPage() {
  const router = useRouter();
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [adminPath, setAdminPath] = useState("/admin");

  useEffect(() => {
    apiFetch<{ today_path: string }>("/api/admin-path")
      .then((data) => {
        if (data.today_path) setAdminPath(data.today_path);
      })
      .catch(() => {});
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiFetch("/api/auth/admin-login", {
        method: "POST",
        body: JSON.stringify({ login, password }),
      });
      router.push(adminPath);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-shell">
      <div className="auth-intro">
        <span className="eyebrow">Администратор</span>
        <h1>Вход в панель управления</h1>
        <p className="lead">
          Только для сотрудников платформы. Регистрация недоступна.
        </p>
      </div>
      <section className="auth-card">
        <div className="section-heading">
          <span className="eyebrow">Авторизация</span>
          <h2>Войти в панель администратора</h2>
        </div>

        {error && <p className="inline-error">{error}</p>}

        <form onSubmit={handleSubmit}>
          <label className="field">
            <span>Логин</span>
            <input
              type="text"
              autoComplete="username"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              required
            />
          </label>
          <label className="field">
            <span>Пароль</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <div className="button-row">
            <button className="button-primary" type="submit" disabled={submitting}>
              {submitting ? "Вход..." : "Войти"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
