"""Web API + the one-page dashboard.

Local mode runs the agent in-process. Deployed mode (RH_AGENT_RUNTIME_ARN set) forwards runs
and decisions to the AgentCore runtime and reads state from DynamoDB.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from . import __version__
from .config import settings
from .models import State
from .store import get_store

from . import user_settings

app = FastAPI(title="Refund Hunter", version=__version__, docs_url="/api/docs", redoc_url=None)
_STATIC = Path(__file__).with_name("dashboard.html")
_lock = asyncio.Lock()
user_settings.apply_saved()  # settings entered in the dashboard win over .env


def _view(state: State) -> dict:
    purchases = {p.id: p for p in state.purchases}
    claims = []
    for c in sorted(state.claims, key=lambda c: c.created_at, reverse=True):
        p = purchases.get(c.purchase_id)
        claims.append(
            {
                **c.model_dump(mode="json"),
                "merchant": p.merchant if p else "?",
                "item": p.item if p else "?",
                "order_id": p.order_id if p else "",
            }
        )
    decisions = []
    for d in state.pending_decisions():
        c = state.claim(d.claim_id)
        p = purchases.get(c.purchase_id) if c else None
        decisions.append(
            {
                **d.model_dump(mode="json"),
                "amount": c.amount if c else None,
                "kind": c.kind.value if c else "",
                "reason": c.reason if c else "",
                "policy": c.policy if c else "",
                "merchant": p.merchant if p else "",
                "item": p.item if p else "",
            }
        )
    return {
        "owner": settings.owner_name,
        "mode": "agentcore" if settings.agent_runtime_arn else "local",
        "mail_source": settings.mail_source,
        "smtp": settings.smtp_ready,
        "safe_mode": bool(settings.claims_to_override),
        "model_provider": settings.model_provider,
        "configured": user_settings.load() is not None,
        "running": state.is_running(),
        "purchases": [p.model_dump(mode="json") for p in sorted(state.purchases, key=lambda p: p.order_date, reverse=True)],
        "claims": claims,
        "decisions": decisions,
        "outbox": [m.model_dump(mode="json") for m in sorted(state.outbox, key=lambda m: m.sent_at, reverse=True)],
        "runs": [r.model_dump(mode="json") for r in state.runs[:10]],
        "totals": {
            "found": state.money_found(),
            "filed": state.money_filed(),
            "waiting": len(state.pending_decisions()),
            "open_purchases": sum(1 for p in state.purchases if p.status.value == "open"),
        },
    }


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return _STATIC.read_text(encoding="utf-8")


@app.get("/api/state")
async def api_state(user_id: str = "local"):
    return _view(get_store().load(user_id))


@app.post("/api/run")
async def api_run(user_id: str = "local"):
    async with _lock:
        if settings.agent_runtime_arn:
            # Hosted mode: a run takes ~45 s, longer than API Gateway allows, so start it in the
            # background (a self-invocation of this Lambda) and let the page poll /api/state.
            store = get_store()
            state = store.load(user_id)
            if state.is_running():
                return {"started": False, "already_running": True}
            from .models import now

            state.running_since = now()
            store.save(state)
            _start_background_run(user_id)
            return {"started": True}
        from .run import run_daily

        report = await run_daily(user_id, trigger="dashboard")
        return report.model_dump(mode="json")


def _start_background_run(user_id: str) -> None:
    import json
    import os
    import threading

    payload = {"action": "run", "user_id": user_id, "trigger": "dashboard"}
    fn = os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    if fn:
        import boto3

        boto3.client("lambda", region_name=settings.aws_region).invoke(
            FunctionName=fn, InvocationType="Event", Payload=json.dumps(payload).encode()
        )
        return
    from .agentcore_client import invoke_runtime

    threading.Thread(target=invoke_runtime, args=(payload,), daemon=True).start()


def run_via_runtime(payload: dict) -> dict:
    """Entry for the background self-invocation (see infra/deploy_web.py)."""
    from .agentcore_client import invoke_runtime

    return invoke_runtime(payload)


class DecideBody(BaseModel):
    interrupt_id: str
    answer: str
    user_id: str = "local"


@app.post("/api/decide")
async def api_decide(body: DecideBody):
    async with _lock:
        try:
            if settings.agent_runtime_arn:
                from .agentcore_client import invoke_runtime

                out = await asyncio.to_thread(
                    invoke_runtime,
                    {"action": "decide", "user_id": body.user_id, "interrupt_id": body.interrupt_id, "answer": body.answer},
                )
                return JSONResponse(out)
            from .run import decide

            report = await decide(body.interrupt_id, body.answer, body.user_id)
            return report.model_dump(mode="json")
        except (KeyError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


class ResolveBody(BaseModel):
    claim_id: str
    outcome: str
    user_id: str = "local"


@app.post("/api/resolve")
async def api_resolve(body: ResolveBody):
    from .claims import resolve_claim

    try:
        resolve_claim(body.claim_id, body.outcome, body.user_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"ok": True}


@app.post("/api/reset")
async def api_reset(user_id: str = "local"):
    async with _lock:
        get_store().reset(user_id)
        sessions = settings.data_dir / "sessions"
        if sessions.exists():
            import shutil

            shutil.rmtree(sessions, ignore_errors=True)
    return {"ok": True}


# ---- settings (local mode only: the hosted demo has nothing to configure) -------------------


def _local_only():
    if settings.agent_runtime_arn:
        raise HTTPException(status_code=400, detail="Settings are only available when you run Refund Hunter yourself.")


@app.get("/api/settings")
async def api_settings_get():
    _local_only()
    return user_settings.masked(user_settings.load() or user_settings.from_env())


@app.post("/api/settings")
async def api_settings_save(body: dict):
    _local_only()
    async with _lock:
        us = user_settings.save(body)
    return user_settings.masked(us)


@app.post("/api/settings/test")
async def api_settings_test(body: dict):
    _local_only()
    async with _lock:
        us = user_settings.save(body)  # save first so the test uses exactly what is on screen
        result = await asyncio.to_thread(user_settings.test_connections, us)
    return result


@app.get("/healthz")
async def healthz():
    return {"ok": True, "version": __version__}
