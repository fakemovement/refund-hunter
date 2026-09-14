"""Settings a person enters in the dashboard (API key, Gmail, name). Saved to .data/settings.json,
which is git-ignored, and applied on top of the environment at startup and whenever saved.

Secrets never leave this machine: the API returns them masked, and an empty value in a save keeps
the existing secret.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel

from .config import settings

SECRET_FIELDS = ("anthropic_api_key", "imap_password", "smtp_password")


class UserSettings(BaseModel):
    # model
    model_provider: str = "bedrock"  # bedrock | anthropic
    anthropic_api_key: str = ""
    anthropic_model_id: str = "claude-sonnet-4-6"
    bedrock_model_id: str = "global.anthropic.claude-sonnet-4-6"
    aws_region: str = "us-east-1"
    # inbox
    mail_source: str = "fixtures"  # fixtures | imap
    imap_host: str = "imap.gmail.com"
    imap_user: str = ""
    imap_password: str = ""
    imap_lookback_days: int = 45
    # sending
    send_emails: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    safe_mode: bool = True  # send every claim to yourself instead of the store
    # you
    owner_name: str = "Sam Rivera"
    owner_email: str = "sam.rivera.demo@example.com"
    # behaviour
    followup_after_days: int = 5
    min_claim_amount: float = 3.0


def _path() -> Path:
    return Path(settings.data_dir) / "settings.json"


def load() -> UserSettings | None:
    p = _path()
    if not p.exists():
        return None
    try:
        return UserSettings.model_validate_json(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def save(new: dict) -> UserSettings:
    current = load() or from_env()
    data = current.model_dump()
    for k, v in new.items():
        if k not in data:
            continue
        if k in SECRET_FIELDS and (v is None or v == "" or str(v).startswith("•")):
            continue  # keep the existing secret
        data[k] = v
    us = UserSettings.model_validate(data)
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(us.model_dump_json(indent=2), encoding="utf-8")
    apply(us)
    return us


def from_env() -> UserSettings:
    """What the environment (.env) says, as a starting point for the form."""
    return UserSettings(
        model_provider=settings.model_provider,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        anthropic_model_id=settings.anthropic_model_id,
        bedrock_model_id=settings.bedrock_model_id,
        aws_region=settings.aws_region,
        mail_source=settings.mail_source,
        imap_host=settings.imap_host,
        imap_user=settings.imap_user or "",
        imap_password=settings.imap_password or "",
        imap_lookback_days=settings.imap_lookback_days,
        send_emails=settings.smtp_ready,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user or "",
        smtp_password=settings.smtp_password or "",
        safe_mode=bool(settings.claims_to_override),
        owner_name=settings.owner_name,
        owner_email=settings.owner_email,
        followup_after_days=settings.followup_after_days,
        min_claim_amount=settings.min_claim_amount,
    )


def apply(us: UserSettings) -> None:
    """Push the saved settings into the live config so the next run uses them."""
    settings.model_provider = us.model_provider
    settings.anthropic_model_id = us.anthropic_model_id
    settings.bedrock_model_id = us.bedrock_model_id
    settings.aws_region = us.aws_region
    if us.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = us.anthropic_api_key
    settings.mail_source = us.mail_source
    settings.imap_host = us.imap_host
    settings.imap_user = us.imap_user or None
    settings.imap_password = us.imap_password or None
    settings.imap_lookback_days = us.imap_lookback_days
    if us.send_emails:
        settings.smtp_host = us.smtp_host
        settings.smtp_port = us.smtp_port
        settings.smtp_user = us.smtp_user or us.imap_user or None
        settings.smtp_password = us.smtp_password or us.imap_password or None
    else:
        settings.smtp_user = None
        settings.smtp_password = None
    settings.claims_to_override = (us.owner_email or us.imap_user) if us.safe_mode else None
    settings.owner_name = us.owner_name
    settings.owner_email = us.owner_email or us.imap_user or settings.owner_email
    settings.followup_after_days = us.followup_after_days
    settings.min_claim_amount = us.min_claim_amount
    # the model factory caches per role; a new key or provider must rebuild it
    from .agents import llm

    llm.get_model.cache_clear()


def apply_saved() -> None:
    us = load()
    if us:
        apply(us)


def masked(us: UserSettings) -> dict:
    d = us.model_dump()
    for k in SECRET_FIELDS:
        v = d.get(k) or ""
        d[k] = ("•" * 8 + v[-4:]) if v else ""
    d["has_settings_file"] = _path().exists()
    return d


def test_connections(us: UserSettings) -> dict:
    """Try the inbox login and one tiny model call. Returns {inbox: ..., model: ...}."""
    out = {}
    if us.mail_source == "imap":
        import imaplib

        try:
            box = imaplib.IMAP4_SSL(us.imap_host)
            box.login(us.imap_user, us.imap_password)
            box.select("INBOX", readonly=True)
            _, data = box.search(None, "ALL")
            n = len(data[0].split())
            box.logout()
            out["inbox"] = f"ok, {n} emails visible"
        except Exception as e:  # noqa: BLE001
            out["inbox"] = f"failed: {type(e).__name__}: {str(e)[:120]}"
    else:
        out["inbox"] = "demo inbox (no login needed)"
    try:
        from strands import Agent

        from .agents.llm import get_model

        agent = Agent(model=get_model("ping"), callback_handler=None)
        r = agent("Reply with the single word OK.")
        out["model"] = "ok" if "OK" in str(r).upper() else f"answered: {str(r)[:40]}"
    except Exception as e:  # noqa: BLE001
        out["model"] = f"failed: {type(e).__name__}: {str(e)[:160]}"
    return out
