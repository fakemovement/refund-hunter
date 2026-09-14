"""Refund Hunter on Amazon Bedrock AgentCore Runtime.

Actions (JSON payload):
  {"action": "run",    "user_id": "local", "trigger": "schedule"}        -> today's check
  {"action": "decide", "user_id": "local", "interrupt_id": "...", "answer": "approve"}
  {"action": "state",  "user_id": "local"}                               -> dashboard view

The EventBridge schedule calls "run" once a day. The dashboard calls "run" and "decide".
State lives in DynamoDB; the paused Hunter's session lives in S3 so a decision made hours
later resumes the exact same agent.
"""

from __future__ import annotations

import os
import traceback

os.environ.setdefault("RH_STORE", "dynamodb")
os.environ.setdefault("RH_SESSION_BACKEND", "s3")
os.environ.setdefault("RH_DATA_DIR", "/tmp/refundhunter")

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from refundhunter import __version__

app = BedrockAgentCoreApp()
log = app.logger


@app.entrypoint
async def invoke(payload, context):
    if not isinstance(payload, dict):
        payload = {"action": "run"}
    action = payload.get("action", "run")
    user_id = payload.get("user_id", "local")
    log.info("refundhunter action=%s user=%s", action, user_id)
    try:
        if action == "run":
            from refundhunter.run import run_daily

            report = await run_daily(user_id, trigger=payload.get("trigger", "runtime"))
            return {"ok": True, "version": __version__, **report.model_dump(mode="json")}
        if action == "decide":
            from refundhunter.run import decide

            report = await decide(payload["interrupt_id"], payload["answer"], user_id)
            return {"ok": True, "version": __version__, **report.model_dump(mode="json")}
        if action == "state":
            from refundhunter.api import _view
            from refundhunter.store import get_store

            return {"ok": True, **_view(get_store().load(user_id))}
        return {"ok": False, "error": f"unknown action {action!r}"}
    except Exception as e:  # noqa: BLE001
        log.error("refundhunter action %s failed: %s\n%s", action, e, traceback.format_exc())
        return {"ok": False, "action": action, "error": f"{type(e).__name__}: {e}"}


if __name__ == "__main__":
    app.run()
