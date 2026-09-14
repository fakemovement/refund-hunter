"""Outbound mail. Real SMTP when configured, otherwise the message stays in the outbox.

Every message is recorded in the state's outbox either way, so the dashboard can show what the
agent sent (or would have sent). A demo with no SMTP settings never emails a real store.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from ..config import settings
from ..models import OutboxMessage, State


def send_mail(state: State, to: str, subject: str, body: str, claim_id: str | None = None) -> OutboxMessage:
    msg = OutboxMessage(to=to, subject=subject, body=body, claim_id=claim_id)
    if settings.smtp_ready:
        real_to = settings.claims_to_override or to
        try:
            em = EmailMessage()
            em["From"] = settings.smtp_user
            em["To"] = real_to
            em["Subject"] = subject
            em.set_content(body)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as s:
                s.starttls()
                s.login(settings.smtp_user, settings.smtp_password)
                s.send_message(em)
            msg.delivered = True
            msg.to = real_to
        except Exception as e:  # noqa: BLE001 - a failed send is recorded, not fatal
            msg.body += f"\n\n[send failed: {type(e).__name__}: {e}]"
    state.outbox.append(msg)
    return msg
