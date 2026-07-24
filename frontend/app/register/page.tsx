import Link from "next/link";

import { AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return (
    <main className="auth-shell">
      <div className="auth-intro">
        <span className="eyebrow">Регистрация</span>
        <h1>Создайте аккаунт в NeuraAI</h1>
        <p className="lead">
          Заполните базовую информацию. После подтверждения email вы сможете
          настроить профиль компании.
        </p>
        <Link className="button-ghost" href="/">
          На главную
        </Link>
      </div>
      <AuthForm mode="register" />
    </main>
  );
}
