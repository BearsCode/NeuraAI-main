import Link from "next/link";

import { AuthForm } from "@/components/auth-form";
import { isValidRedirect } from "@/lib/redirect";

type LoginPageProps = {
  searchParams: Promise<{ next?: string }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const resolvedSearchParams = await searchParams;
  const nextPath =
    resolvedSearchParams.next && isValidRedirect(resolvedSearchParams.next)
      ? resolvedSearchParams.next
      : "/workspace";

  return (
    <main className="auth-shell">
      <div className="auth-intro">
        <span className="eyebrow">С возвращением</span>
        <h1>Войдите в NeuraAI</h1>
        <p className="lead">
          Просматривайте проекты, обновляйте AI-стратегию и управляйте контентом.
        </p>
        <Link className="button-ghost" href="/">
          На главную
        </Link>
      </div>
      <AuthForm mode="login" nextPath={nextPath} />
    </main>
  );
}
