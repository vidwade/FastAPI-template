from __future__ import annotations

from email.message import EmailMessage
from typing import Iterable

import anyio
import smtplib

from app.core.config import settings


class EmailService:
    def send_mail(self, *, subject: str, recipients: Iterable[str], body: str, subtype: str = "plain") -> None:
        """Synchronously send an email via SMTP or Mailpit fallback."""
        message = EmailMessage()
        message["From"] = settings.mail_sender
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message.set_content(body, subtype=subtype)

        with smtplib.SMTP(settings.resolved_mail_host, settings.resolved_mail_port) as client:
            if settings.smtp_use_tls and settings.smtp_host:
                client.starttls()
            if settings.smtp_username and settings.smtp_password:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)

    async def send_mail_async(
        self, *, subject: str, recipients: Iterable[str], body: str, subtype: str = "plain"
    ) -> None:
        await anyio.to_thread.run_sync(
            self.send_mail,
            subject=subject,
            recipients=list(recipients),
            body=body,
            subtype=subtype,
        )


email_service = EmailService()
