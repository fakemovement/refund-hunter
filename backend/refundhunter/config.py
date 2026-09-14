"""Runtime configuration (env vars / .env). Prefix: RH_."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


def _load_ssm_secrets() -> None:
    """On AWS the secrets live in one SSM SecureString (KEY=VALUE lines or JSON)."""
    name = os.getenv("RH_SSM_PARAM")
    if not name:
        return
    try:
        import boto3

        val = boto3.client("ssm").get_parameter(Name=name, WithDecryption=True)["Parameter"][
            "Value"
        ]
    except Exception as e:  # noqa: BLE001
        print(f"[refundhunter] could not load SSM secrets {name}: {e}")
        return
    try:
        pairs = json.loads(val).items()
    except json.JSONDecodeError:
        pairs = (
            line.split("=", 1)
            for line in val.splitlines()
            if "=" in line and not line.startswith("#")
        )
    for k, v in pairs:
        os.environ.setdefault(k.strip(), str(v).strip())


_load_ssm_secrets()

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RH_", env_file=".env", extra="ignore")

    # --- model ---------------------------------------------------------------
    model_provider: str = "bedrock"  # bedrock | anthropic
    bedrock_model_id: str = "global.anthropic.claude-sonnet-4-6"
    aws_region: str = "us-east-1"
    anthropic_model_id: str = "claude-sonnet-4-6"
    model_max_tokens: int = 4000

    # --- storage -------------------------------------------------------------
    store: str = "local"  # local | dynamodb
    ddb_table: str = "refundhunter"
    data_dir: Path = Field(default=_BACKEND_ROOT / ".data")
    # Agent sessions (needed to resume an interrupted agent later): file | s3
    session_backend: str = "file"
    session_bucket: str | None = None
    # When set, the web API delegates runs/decisions to the deployed AgentCore runtime.
    agent_runtime_arn: str | None = None

    # --- mail ----------------------------------------------------------------
    mail_source: str = "fixtures"  # fixtures | imap
    fixtures_dir: Path = Field(default=_BACKEND_ROOT / "fixtures")
    imap_host: str = "imap.gmail.com"
    imap_user: str | None = None
    imap_password: str | None = None
    imap_folder: str = "INBOX"
    imap_lookback_days: int = 45
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    # Where claim emails really go. Leave empty to keep every outbound email in the outbox
    # (dry run) so a demo never emails a real store.
    claims_to_override: str | None = None
    owner_name: str = "Sam Rivera"
    owner_email: str = "sam.rivera.demo@example.com"

    # --- behaviour -------------------------------------------------------------
    followup_after_days: int = 5
    min_claim_amount: float = 3.0

    @property
    def smtp_ready(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)


settings = Settings()
