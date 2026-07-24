import Link from "next/link";
import { notFound } from "next/navigation";

import { backendRequest, readJson } from "@/lib/backend";

interface Props {
  params: Promise<{ code: string }>;
}

interface ReferralInfo {
  referral_code: string | null;
  is_valid: boolean;
  partner_user_id?: string | null;
}

export default async function ReferralPage({ params }: Props) {
  const { code } = await params;

  let info: ReferralInfo;
  try {
    const response = await backendRequest(`/registration/referral?code=${encodeURIComponent(code)}`);
    info = await readJson<ReferralInfo>(response);
  } catch {
    notFound();
  }

  if (!info.is_valid) {
    notFound();
  }

  return (
    <div className="ref-page">
      <div className="ref-card">
        <div className="ref-logo">N</div>
        <h1>Вас пригласили в НЕЙРУ</h1>
        <p className="ref-subtitle">
          Присоединяйтесь к платформе AI-маркетинга и начните управлять контентом с помощью искусственного интеллекта
        </p>
        <div className="ref-benefits">
          <div className="ref-benefit">
            <span className="ref-benefit-icon">🤖</span>
            <span>AI-генерация контента</span>
          </div>
          <div className="ref-benefit">
            <span className="ref-benefit-icon">📊</span>
            <span>Умная аналитика</span>
          </div>
          <div className="ref-benefit">
            <span className="ref-benefit-icon">📅</span>
            <span>Автопостинг</span>
          </div>
          <div className="ref-benefit">
            <span className="ref-benefit-icon">🎯</span>
            <span>Стратегия под ключ</span>
          </div>
        </div>
        <Link href={`/register?ref=${encodeURIComponent(code)}`} className="ref-cta">
          Зарегистрироваться
        </Link>
        <p className="ref-login-hint">
          Уже есть аккаунт? <Link href="/login">Войти</Link>
        </p>
      </div>
    </div>
  );
}
