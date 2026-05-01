"""Tests for EmailService — SMTP notification implementation."""

from unittest.mock import AsyncMock, patch
import pytest

from app.domain.entities.comparative_report import ComparativeReport
from app.domain.value_objects.filter_config import FilterConfig
from app.infrastructure.services.email_service import EmailService


def _make_report() -> ComparativeReport:
    filter_config = FilterConfig(
        tipus_expedient=1,
        fase_vigent=0,
        sector_keywords=("construcció",),
    )
    return ComparativeReport(scored_tenders=[], filter_config=filter_config)


class TestEmailServiceSendReport:
    """Tests for EmailService.send_report()."""

    @pytest.mark.asyncio
    async def test_send_report_calls_smtp(self):
        """send_report() must open an SMTP connection and send a message."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="secret",
        )
        report = _make_report()

        with patch("app.infrastructure.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await service.send_report(report, recipient="dest@example.com")

        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_report_uses_recipient_address(self):
        """send_report() must address the email to the given recipient."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="secret",
        )
        report = _make_report()

        with patch("app.infrastructure.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await service.send_report(report, recipient="dest@example.com")

        call_kwargs = mock_send.call_args
        message = call_kwargs.args[0] if call_kwargs.args else None
        if message is None:
            message = call_kwargs.kwargs.get("message")
        assert message is not None
        assert "dest@example.com" in str(message["To"])


class TestEmailServiceSendError:
    """Tests for EmailService.send_error()."""

    @pytest.mark.asyncio
    async def test_send_error_calls_smtp(self):
        """send_error() must open an SMTP connection and send a message."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="secret",
        )

        with patch("app.infrastructure.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await service.send_error("Pipeline failed", recipient="dest@example.com")

        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_error_includes_reason_in_body(self):
        """send_error() must include the error reason in the message body."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="secret",
        )

        with patch("app.infrastructure.services.email_service.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await service.send_error("Timeout connecting to API", recipient="dest@example.com")

        call_kwargs = mock_send.call_args
        message = call_kwargs.args[0] if call_kwargs.args else None
        if message is None:
            message = call_kwargs.kwargs.get("message")
        assert message is not None
        body = message.get_payload(decode=True).decode("utf-8")
        assert "Timeout connecting to API" in body
