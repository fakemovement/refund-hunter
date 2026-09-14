"""Invoke the deployed AgentCore runtime (used by the web API in deployed mode)."""

from __future__ import annotations

import json
import uuid

import boto3

from .config import settings


def invoke_runtime(payload: dict, session_id: str | None = None) -> dict:
    client = boto3.client("bedrock-agentcore", region_name=settings.aws_region)
    resp = client.invoke_agent_runtime(
        agentRuntimeArn=settings.agent_runtime_arn,
        runtimeSessionId=session_id or uuid.uuid4().hex + uuid.uuid4().hex[:8],
        payload=json.dumps(payload).encode("utf-8"),
        contentType="application/json",
        accept="application/json",
    )
    body = resp["response"].read() if hasattr(resp["response"], "read") else resp["response"]
    if isinstance(body, bytes):
        body = body.decode("utf-8", "replace")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"ok": False, "raw": body[:2000]}
