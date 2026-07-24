from __future__ import annotations

import asyncio
import html
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from backend.app.core.configs import settings

logger = logging.getLogger(__name__)


class EmailService:
    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
        cc: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        cfg = settings.email
        if cfg.provider == "disabled":
            logger.info("email_disabled_skipping", extra={"to": to, "subject": subject})
            return False

        if cfg.provider == "console":
            logger.info(
                "email_console_output",
                extra={
                    "to": to,
                    "subject": subject,
                    "html_length": len(html_body),
                },
            )
            return True

        return await self._send_smtp(to, subject, html_body, text_body, cc or [])

    async def send_verification_code(
        self,
        to: str,
        code: str,
        full_name: str,
    ) -> bool:
        subject = "Подтверждение email — NeuaraAI"
        safe_name = html.escape(full_name)
        safe_code = html.escape(code)
        html_body = (
            f"<h2>Добро пожаловать в NeuaraAI, {safe_name}!</h2>"
            f"<p>Ваш код подтверждения:</p>"
            f"<h1 style='letter-spacing:5px;font-size:32px;color:#6C5CE7;'>{safe_code}</h1>"
            f"<p>Код действителен в течение 10 минут.</p>"
            f"<hr><p style='color:#999;font-size:12px;'>"
            f"Если вы не регистрировались в NeuaraAI, проигнорируйте это письмо.</p>"
        )
        text_body = f"Ваш код подтверждения NeuaraAI: {safe_code}"
        return await self.send_email(to=to, subject=subject, html_body=html_body, text_body=text_body)

    async def send_password_changed_notification(self, to: str, full_name: str) -> bool:
        subject = "Пароль изменён — NeuaraAI"
        safe_name = html.escape(full_name)
        html_body = (
            f"<h2>Здравствуйте, {safe_name}!</h2>"
            f"<p>Пароль от вашего аккаунта NeuaraAI был успешно изменён.</p>"
            f"<p>Если это были не вы, немедленно свяжитесь с поддержкой.</p>"
        )
        return await self.send_email(to=to, subject=subject, html_body=html_body)

    async def send_weekly_report(
        self,
        to: str,
        full_name: str,
        report_data: dict[str, Any],
    ) -> bool:
        subject = "Еженедельный отчёт — NeuaraAI"
        safe_name = html.escape(full_name)
        html_parts = [f"<h2>Еженедельный отчёт, {safe_name}!</h2>"]
        for key, value in report_data.items():
            safe_key = html.escape(str(key))
            safe_value = html.escape(str(value))
            html_parts.append(f"<p><strong>{safe_key}:</strong> {safe_value}</p>")
        html_body = "".join(html_parts)
        return await self.send_email(to=to, subject=subject, html_body=html_body)

    async def _send_smtp(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: str | None,
        cc: list[str],
    ) -> bool:
        cfg = settings.email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{cfg.default_from_name} <{cfg.default_from}>"
        msg["To"] = to
        if cc:
            msg["Cc"] = ", ".join(cc)

        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        all_recipients = [to] + cc

        def _send() -> None:
            import smtplib

            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=15) as server:
                if cfg.smtp_use_tls:
                    server.starttls()
                if cfg.smtp_user and cfg.smtp_password:
                    server.login(cfg.smtp_user, cfg.smtp_password.get_secret_value())
                server.sendmail(cfg.default_from, all_recipients, msg.as_string())

        try:
            await asyncio.to_thread(_send)
            logger.info("email_sent_successfully", extra={"to": to, "subject": subject})
            return True
        except Exception as exc:
            logger.error("email_send_failed", extra={"to": to, "error": str(exc)})
            return False


email_service = EmailService()
