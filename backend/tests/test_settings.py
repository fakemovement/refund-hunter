"""Dashboard settings: saved to a private file, secrets masked, empty secret keeps the old one."""

from __future__ import annotations

from refundhunter import user_settings
from refundhunter.config import settings


def test_settings_roundtrip_and_masking(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    assert user_settings.load() is None
    us = user_settings.save({"model_provider": "openai", "openai_api_key": "sk-openai-abcdef1234",
                             "anthropic_api_key": "sk-ant-abcdef1234",
                             "mail_source": "imap", "imap_user": "me@gmail.com", "imap_password": "pppp",
                             "safe_mode": True, "owner_email": "me@gmail.com", "unknown_field": "ignored"})
    assert us.anthropic_api_key == "sk-ant-abcdef1234"
    assert (tmp_path / "settings.json").exists()
    m = user_settings.masked(us)
    assert m["openai_api_key"].endswith("1234") and m["openai_api_key"].startswith("•")
    assert m["imap_password"].startswith("•")
    # an empty or masked secret in a later save keeps the stored value
    us2 = user_settings.save({"openai_api_key": "", "imap_password": m["imap_password"], "owner_name": "Alex"})
    assert us2.openai_api_key == "sk-openai-abcdef1234" and us2.imap_password == "pppp"
    assert us2.owner_name == "Alex"
    # applied to the live config
    assert settings.model_provider == "openai" and settings.mail_source == "imap"
    assert settings.claims_to_override == "me@gmail.com"


def test_notify_uses_inbox_creds_and_gates(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    # notify on, sending off: SMTP creds come from the Gmail inbox, claims still do not send
    user_settings.save({"model_provider": "anthropic", "mail_source": "imap",
                        "imap_user": "me@gmail.com", "imap_password": "apppw",
                        "send_emails": False, "notify_by_email": True,
                        "dashboard_url": "http://localhost:8000"})
    assert settings.notify_by_email is True
    assert settings.send_claims is False           # claims stay in the outbox
    assert settings.smtp_ready is True             # but notifications can send
    assert settings.smtp_user == "me@gmail.com" and settings.smtp_password == "apppw"
