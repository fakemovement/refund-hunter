"""Where emails come from: a synthetic fixture inbox (demo) or a real IMAP mailbox.

The fixture inbox stores dates as offsets from today (``days_ago``) so the demo always lands
inside the stores' price-adjustment windows no matter when it is run.
"""

from __future__ import annotations

import email
import imaplib
import json
import re
from datetime import UTC, datetime, timedelta
from email.header import decode_header
from pathlib import Path

from ..config import settings
from ..models import Email


class MailSource:
    def fetch(self, since_days: int) -> list[Email]:  # pragma: no cover - interface
        raise NotImplementedError


class FixtureMail(MailSource):
    def __init__(self, fixtures_dir: Path | None = None):
        self.path = Path(fixtures_dir or settings.fixtures_dir) / "inbox.json"

    def fetch(self, since_days: int = 45) -> list[Email]:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        today = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)
        out: list[Email] = []
        for m in raw["emails"]:
            when = today - timedelta(days=m["days_ago"])
            body = _fill_dates(m["body"], today)
            out.append(
                Email(
                    id=m["id"],
                    from_addr=m["from"],
                    subject=_fill_dates(m["subject"], today),
                    date=when,
                    body=body,
                )
            )
        return sorted(out, key=lambda e: e.date)


_DATE_TOKEN = re.compile(r"\{\{date([+-]\d+)\}\}")


def _fill_dates(text: str, today: datetime) -> str:
    """Replace {{date-9}} with the calendar date nine days before today (e.g. 'September 5')."""

    def sub(m: re.Match) -> str:
        d = today + timedelta(days=int(m.group(1)))
        return d.strftime("%B %-d") if not _is_windows() else d.strftime("%B %d").replace(" 0", " ")

    return _DATE_TOKEN.sub(sub, text)


def _is_windows() -> bool:
    import os

    return os.name == "nt"


class ImapMail(MailSource):
    """Read-only IMAP (Gmail with an app password works)."""

    def fetch(self, since_days: int | None = None) -> list[Email]:
        since_days = since_days or settings.imap_lookback_days
        if not (settings.imap_user and settings.imap_password):
            raise RuntimeError("RH_IMAP_USER / RH_IMAP_PASSWORD not set")
        since = (datetime.now(UTC) - timedelta(days=since_days)).strftime("%d-%b-%Y")
        box = imaplib.IMAP4_SSL(settings.imap_host)
        try:
            box.login(settings.imap_user, settings.imap_password)
            box.select(settings.imap_folder, readonly=True)
            _, data = box.search(None, f'(SINCE "{since}")')
            ids = data[0].split()
            out: list[Email] = []
            for uid in ids[-200:]:
                _, msg_data = box.fetch(uid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                out.append(
                    Email(
                        id=f"imap_{uid.decode()}",
                        from_addr=_decode(msg.get("From", "")),
                        subject=_decode(msg.get("Subject", "")),
                        date=_parse_date(msg.get("Date")),
                        body=_text_of(msg)[:6000],
                    )
                )
            return sorted(out, key=lambda e: e.date)
        finally:
            try:
                box.logout()
            except Exception:  # noqa: BLE001
                pass


def _decode(value: str) -> str:
    parts = decode_header(value)
    out = []
    for text, enc in parts:
        out.append(text.decode(enc or "utf-8", "replace") if isinstance(text, bytes) else text)
    return "".join(out)


def _parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        dt = email.utils.parsedate_to_datetime(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except Exception:  # noqa: BLE001
        return datetime.now(UTC)


def _text_of(msg) -> str:
    if msg.is_multipart():
        plain, html = "", ""
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain" and not plain:
                plain = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", "replace"
                )
            elif ctype == "text/html" and not html:
                html = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", "replace"
                )
        return plain or _strip_html(html)
    payload = msg.get_payload(decode=True) or b""
    text = payload.decode(msg.get_content_charset() or "utf-8", "replace")
    return text if msg.get_content_type() == "text/plain" else _strip_html(text)


def _strip_html(html: str) -> str:
    from bs4 import BeautifulSoup

    return BeautifulSoup(html, "html.parser").get_text("\n", strip=True)


def get_mail_source() -> MailSource:
    return ImapMail() if settings.mail_source == "imap" else FixtureMail()
