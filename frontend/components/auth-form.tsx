"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiFetch } from "@/lib/client";
import { isValidRedirect } from "@/lib/redirect";
import type {
  LoginPayload,
  RegisterPayload,
  RegistrationAcceptedResponse,
} from "@/lib/types";

type AuthFormProps = {
  mode: "login" | "register";
  nextPath?: string;
};

type AuthFormState = {
  full_name: string;
  email: string;
  password: string;
  phone: string;
  company_name: string;
  referral_code: string;
};

const initialState: AuthFormState = {
  full_name: "",
  email: "",
  password: "",
  phone: "",
  company_name: "",
  referral_code: "",
};

export function AuthForm({ mode, nextPath = "/workspace" }: AuthFormProps) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState<AuthFormState>(initialState);
  const [error, setError] = useState<string | null>(null);

  const [registration, setRegistration] =
    useState<RegistrationAcceptedResponse | null>(null);
  const [otpCode, setOtpCode] = useState("");

  const safeNextPath = isValidRedirect(nextPath) ? nextPath : "/workspace";

  function updateField(key: keyof AuthFormState, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function redirectToOAuth(provider: string, authorizeUrl: string) {
    const redirectUri = `${window.location.origin}/api/auth/oauth/${provider}/callback`;
    const params = new URLSearchParams({
      client_id: process.env[`NEXT_PUBLIC_${provider.toUpperCase()}_CLIENT_ID`] || "",
      redirect_uri: redirectUri,
      response_type: "code",
      state: crypto.randomUUID(),
    });
    window.location.href = `${authorizeUrl}?${params}`;
  }

  function redirectToVK() {
    if (!process.env.NEXT_PUBLIC_VK_CLIENT_ID) {
      setError("VK OAuth не настроен");
      return;
    }
    redirectToOAuth("vk", "https://id.vk.com/authorize");
  }

  function redirectToYandex() {
    if (!process.env.NEXT_PUBLIC_YANDEX_CLIENT_ID) {
      setError("Яндекс OAuth не настроен");
      return;
    }
    redirectToOAuth("yandex", "https://oauth.yandex.ru/authorize");
  }

  function redirectToMailru() {
    if (!process.env.NEXT_PUBLIC_MAILRU_CLIENT_ID) {
      setError("Mail.ru OAuth не настроен");
      return;
    }
    redirectToOAuth("mailru", "https://oauth.mail.ru/login");
  }

  async function handleLogin() {
    setError(null);
    setSubmitting(true);
    try {
      const payload: LoginPayload = {
        email: form.email,
        password: form.password,
      };
      await apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      router.push(safeNextPath);
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось выполнить вход.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRegister() {
    setError(null);
    setSubmitting(true);
    try {
      const payload: RegisterPayload = {
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        phone: form.phone || null,
        referral_code: form.referral_code || null,
      };
      const result = await apiFetch<RegistrationAcceptedResponse>(
        "/api/auth/register",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
      setRegistration(result);
      if (result.debug_code) {
        setOtpCode(result.debug_code);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Не удалось завершить регистрацию.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function submitVerification() {
    setError(null);
    setSubmitting(true);
    try {
      await apiFetch("/api/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({
          email: registration!.email,
          code: otpCode,
        }),
      });
      localStorage.setItem("just_registered", "true");
      router.push("/onboarding/tariffs");
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Ошибка подтверждения",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (registration) {
    return (
      <section className="auth-card">
        <div className="section-heading">
          <span className="eyebrow">Подтверждение email</span>
          <h2>Проверьте почту</h2>
        </div>
        <p className="lead">
          Мы отправили код подтверждения на <strong>{registration.email}</strong>
        </p>

        {registration.debug_code ? (
          <div className="field">
            <label htmlFor="otp">Код подтверждения (dev mode)</label>
            <input
              id="otp"
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value)}
              placeholder="000000"
              autoFocus
            />
            <p style={{ fontSize: "0.75rem", opacity: 0.6, marginTop: 4 }}>
              Dev mode: код заполнен автоматически
            </p>
          </div>
        ) : (
          <div className="field">
            <label htmlFor="otp">Код подтверждения</label>
            <input
              id="otp"
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value)}
              placeholder="000000"
              autoFocus
            />
          </div>
        )}

        {error ? <p className="inline-error">{error}</p> : null}

        <div className="button-row">
          <button
            className="button-primary"
            type="button"
            disabled={submitting || otpCode.length < 6}
            onClick={() => void submitVerification()}
          >
            {submitting ? "Проверяем..." : "Подтвердить email"}
          </button>
          <Link className="button-ghost" href="/login">
            Уже есть аккаунт
          </Link>
        </div>
      </section>
    );
  }

  const isLogin = mode === "login";

  return (
    <section className="auth-card">
      <div className="section-heading">
        <span className="eyebrow">{isLogin ? "Вход" : "Регистрация"}</span>
        <h2>{isLogin ? "Войти в рабочий кабинет" : "Создать аккаунт"}</h2>
      </div>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (submitting) return;
          if (isLogin) {
            void handleLogin();
          } else {
            void handleRegister();
          }
        }}
      >
        {!isLogin ? (
    <div className="field">
      <label htmlFor="full_name">Имя и фамилия</label>
      <input
        id="full_name"
        name="full_name"
        value={form.full_name}
        onChange={(event) => updateField("full_name", event.target.value)}
        placeholder="Иван Иванов"
        required
      />
    </div>
  ) : null}

  {!isLogin ? (
    <div className="field">
      <label htmlFor="phone">Телефон</label>
      <input
        id="phone"
        name="phone"
        type="tel"
        value={form.phone}
        onChange={(event) => {
          const raw = event.target.value.replace(/[^\d]/g, "");
          if (!raw) { updateField("phone", ""); return; }
          const parts = [];
          parts.push(raw.slice(0, 1));
          if (raw.length > 1) parts.push(raw.slice(1, 4));
          if (raw.length > 4) parts.push(raw.slice(4, 7));
          if (raw.length > 7) parts.push(raw.slice(7, 9));
          if (raw.length > 9) parts.push(raw.slice(9, 11));
          updateField("phone", "+" + parts.join(" "));
        }}
        placeholder="+7 999 999 99 99"
      />
    </div>
  ) : null}

  <div className="field">
    <label htmlFor="email">Email</label>
    <input
      id="email"
      name="email"
      type="email"
      value={form.email}
      onChange={(event) => updateField("email", event.target.value)}
      placeholder="team@neura.ai"
      required
    />
  </div>

  <div className="field">
    <label htmlFor="password">Пароль</label>
    <input
      id="password"
      name="password"
      type="password"
      value={form.password}
      onChange={(event) => updateField("password", event.target.value)}
      placeholder="Минимум 8 символов"
      minLength={8}
      required
    />
  </div>

  {!isLogin ? (
    <div className="field">
      <label htmlFor="referral_code">Реферальный код</label>
      <input
        id="referral_code"
        name="referral_code"
        value={form.referral_code}
        onChange={(event) => updateField("referral_code", event.target.value)}
        placeholder="Необязательно"
      />
      </div>
    ) : null}

    <div className="social-divider">
      <span>{isLogin ? "или войти через" : "или зарегистрироваться через"}</span>
    </div>
    <div className="social-buttons">
              <button
                className="button-social button-vk"
                type="button"
                disabled={submitting}
                onClick={() => void redirectToVK()}
              >
                <svg viewBox="0 0 24 24" width="20" height="20" fill="#0077FF">
                  <path d="M13.162 18.994c.609 0 .858-.406.851-.915-.031-1.917.714-2.949 2.059-1.604 1.488 1.488 1.796 2.519 3.603 2.519h3.2c.808 0 1.126-.26 1.126-.668 0-.863-1.421-2.386-2.625-3.504-1.216-1.128-1.352-1.218-.328-2.558 1.41-1.843 2.42-3.771 2.059-4.194-.332-.389-1.185-.299-2.336-.299h-2.854c-.663 0-.865.228-.865.663 0 1.398-1.919 4.15-2.399 4.15-.245 0-.369-.245-.369-.855V9.195c0-.678-.175-.996-.687-.996H9.839c-.518 0-.829.372-.829.721 0 .758 1.078 1.067 1.078 3.125v2.189c0 .833-.175.99-.554.99-1.011 0-3.463-3.95-4.778-8.117-.282-.891-.658-.908-1.774-.908H.978c-.749 0-.978.373-.978.696 0 .775 1.762 7.642 5.256 11.46C7.479 18.146 9.898 19 12.012 19"/>
                </svg>
                VK ID
              </button>
              <button
                className="button-social button-yandex"
                type="button"
                disabled={submitting}
                onClick={() => void redirectToYandex()}
              >
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <circle cx="12" cy="12" r="12" fill="#FC3F1D"/>
                  <path fill="#fff" d="M13.1 5.3h-2.2c-2.2 0-3.6 1.3-3.6 3.3 0 1.6.8 2.6 2.5 3.5l1 .5-3.1 5.4H9.7l2.8-5.1h.6v5.1h2.2V5.3h-2.2v4.1h-.6l-.6-4.1z"/>
                </svg>
                Яндекс
              </button>
              <button
                className="button-social button-mailru"
                type="button"
                disabled={submitting}
                onClick={() => void redirectToMailru()}
              >
                <svg viewBox="0 0 24 24" width="20" height="20" fill="#005FF9">
                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.6 0 12 0zm.5 15.5c-.5.5-1.1.7-1.8.7-2.3 0-3.9-1.9-3.9-4.3 0-2.3 1.6-4.2 3.9-4.2.7 0 1.3.2 1.8.7v7.1zm3.1-4.3c0 4-2.2 6.3-5.1 6.3-2.8 0-5-2.3-5-6.2 0-4 2.2-6.3 5-6.3 2.9 0 5.1 2.3 5.1 6.2z"/>
                </svg>
                Mail.ru
              </button>
              <button
                className="button-social button-telegram"
                type="button"
                disabled={submitting}
                onClick={() => {
                  if (!process.env.NEXT_PUBLIC_TELEGRAM_BOT_NAME) {
                    setError("Telegram бот не настроен");
                    return;
                  }
                  window.location.href = "/telegram-login";
                }}
              >
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.127.087.775.047 1.19-.094 1.028-.572 4.473-.805 5.954-.095.583-.29.758-.462.777-.35.04-.617-.23-.957-.455-.558-.368-1.144-.575-1.791-.922-.426-.237-.143-.394.026-.576.1-.107.674-.612 1.153-1.052.137-.13.249-.259.114-.492-.072-.134-.36-.214-.568-.314-.268-.128-.536-.257-.802-.38-.256-.13-.523-.263-.409-.512.06-.13.39-.266.674-.385.365-.155 2.124-.88 2.403-1.002.586-.256.798-.216.575-.38a.506.506 0 0 0-.164-.085c-.095-.03-.24-.04-.384-.03-.193.012-.686.134-1.943.62-.476.186-.882.274-1.211.265-.367-.01-.675-.056-.993-.112-.43-.075-.769-.166-1.144-.284-.145-.046-.258-.066-.341-.064-.535.008-1.003.297-1.252.766.08.012.167.034.255.06.366.11.727.223 1.084.347.572.2 1.145.413 1.697.686.316.156.617.374.818.612.21.244.208.47.204.624-.007.21-.237.277-.428.272-.247-.006-.54-.086-.837-.182-.56-.18-1.28-.46-1.779-.586-.344-.089-.702-.136-1.008-.114-.286.02-.56.088-.82.214-.287.137-.542.319-.774.507.223.122.471.224.726.322.27.104.545.2.822.268.548.137 1.035.225 1.395.354.447.16.703.27.818.526.091.2.071.576-.14.876-.218.293-.6.417-.906.478-.722.14-1.432-.001-2.089-.149-1.58-.355-2.58-.885-3.145-1.364-.544-.465-.686-.796-.723-.972-.048-.22.024-.49.088-.65.08-.2.252-.367.422-.497.212-.163.456-.278.716-.386.518-.214 1.066-.367 1.634-.53 1.21-.343 2.442-.682 3.088-.903.768-.255.871-.296.962-.34z"/>
                </svg>
                Telegram
              </button>
            </div>

    {error ? <p className="inline-error">{error}</p> : null}

        <div className="button-row">
          <button className="button-primary" type="submit" disabled={submitting}>
            {submitting
              ? "Подождите..."
              : isLogin
                ? "Войти"
                : "Создать аккаунт"}
          </button>
          <Link
            className="button-ghost"
            href={isLogin ? "/register" : "/login"}
          >
            {isLogin ? "Создать аккаунт" : "Уже есть аккаунт"}
          </Link>
        </div>
      </form>
    </section>
  );
}
