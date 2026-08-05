from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseEmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, html: str, text: str) -> None: ...


class ConsoleEmailSender(BaseEmailSender):
    """Prints emails to the console — for development only."""

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        separator = "─" * 60
        logger.info(
            "\n%s\n📧  EMAIL (console mode)\n%s\n"
            "  To:      %s\n"
            "  Subject: %s\n%s\n%s\n%s\n",
            separator, separator, to, subject, separator, text, separator,
        )


class SMTPEmailSender(BaseEmailSender):
    """Sends real emails via SMTP (TLS)."""

    async def send(self, to: str, subject: str, html: str, text: str) -> None:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_ADDRESS}>"
        message["To"] = to
        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )


def get_email_sender() -> BaseEmailSender:
    if settings.EMAIL_BACKEND == "smtp":
        return SMTPEmailSender()
    return ConsoleEmailSender()


_sender = get_email_sender()


# ─── Email templates ──────────────────────────────────────────────────────────

async def send_verification_email(to: str, full_name: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "Verify your FormPilot AI email address"
    text = (
        f"Hi {full_name},\n\n"
        f"Please verify your email address by clicking the link below:\n{link}\n\n"
        f"This link expires in 24 hours.\n\n"
        f"— The FormPilot AI team"
    )
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:auto;padding:32px;">
      <h2 style="color:#7c3aed;">Verify your email</h2>
      <p>Hi {full_name},</p>
      <p>Click the button below to verify your FormPilot AI account.</p>
      <a href="{link}" style="display:inline-block;margin:24px 0;padding:12px 28px;
         background:#7c3aed;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">
        Verify Email
      </a>
      <p style="color:#666;font-size:13px;">Link expires in 24 hours. If you didn't register, ignore this email.</p>
    </div>
    """
    await _sender.send(to, subject, html, text)


async def send_password_reset_email(to: str, full_name: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    subject = "Reset your FormPilot AI password"
    text = (
        f"Hi {full_name},\n\n"
        f"Reset your password by clicking the link below:\n{link}\n\n"
        f"This link expires in 1 hour. If you didn't request this, ignore this email.\n\n"
        f"— The FormPilot AI team"
    )
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:auto;padding:32px;">
      <h2 style="color:#7c3aed;">Reset your password</h2>
      <p>Hi {full_name},</p>
      <p>Click the button below to reset your FormPilot AI password.</p>
      <a href="{link}" style="display:inline-block;margin:24px 0;padding:12px 28px;
         background:#7c3aed;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">
        Reset Password
      </a>
      <p style="color:#666;font-size:13px;">Link expires in 1 hour. If you didn't request this, ignore this email.</p>
    </div>
    """
    await _sender.send(to, subject, html, text)
