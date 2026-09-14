"""Dashboard settings: saved to a private file, secrets masked, empty secret keeps the old one."""

from __future__ import annotations

from refundhunter import user_settings
from refundhunter.config import settings


def test_settings_roundtrip_and_masking(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    assert user_settings.load() is None
    us = user_settings.save({"model_provider": "anthropic", "anthropic_api_key": "sk-ant-abcdef1234",
                             "mail_source": "imap", "imap_user": "me@gmail.com", "imap_password": "pppp",
                             "safe_mode": True, "owner_email": "me@gmail.com", "unknown_field": "ignored"})
    assert us.anthropic_api_key == "sk-ant-abcdef1234"
    assert (tmp_path / "settings.json").exists()
    m = user_settings.masked(us)
    assert m["anthropic_api_key"].endswith("1234") and m["anthropic_api_key"].startswith("•")
    assert m["imap_password"].startswith("•")
    # an empty or masked secret in a later save keeps the stored value
    us2 = user_settings.save({"anthropic_api_key": "", "imap_password": m["imap_password"], "owner_name": "Alex"})
    assert us2.anthropic_api_key == "sk-ant-abcdef1234" and us2.imap_password == "pppp"
    assert us2.owner_name == "Alex"
    # applied to the live config
    assert settings.model_provider == "anthropic" and settings.mail_source == "imap"
    assert settings.claims_to_override == "me@gmail.com"
