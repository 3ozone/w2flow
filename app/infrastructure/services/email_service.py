"""Email notification service — implements NotificationPort via SMTP."""

from __future__ import annotations

import json
from email.mime.text import MIMEText

import aiosmtplib

from app.application.ports.notification_port import NotificationPort
from app.domain.entities.comparative_report import ComparativeReport


class EmailService(NotificationPort):
    """Sends email notifications via SMTP using aiosmtplib."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
    ) -> None:
        self._host = smtp_host
        self._port = smtp_port
        self._user = smtp_user
        self._password = smtp_password

    async def send_report(self, report: ComparativeReport, recipient: str) -> None:
        """Send a comparative report summary by email."""
        body = json.dumps(report.generate_json(), ensure_ascii=False, indent=2)
        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = "w2flow — Informe comparatiu de licitacions"
        message["From"] = self._user
        message["To"] = recipient

        await aiosmtplib.send(
            message,
            hostname=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
            start_tls=True,
        )

    async def send_error(self, reason: str, recipient: str) -> None:
        """Send an error notification by email."""
        message = MIMEText(reason, "plain", "utf-8")
        message["Subject"] = "w2flow — Error en el pipeline"
        message["From"] = self._user
        message["To"] = recipient

        await aiosmtplib.send(
            message,
            hostname=self._host,
            port=self._port,
            username=self._user,
            password=self._password,
            start_tls=True,
        )
