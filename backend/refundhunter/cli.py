"""Command line: run the daily check, answer decisions, serve the dashboard."""

from __future__ import annotations

import asyncio
import json

import typer
import uvicorn

from .config import settings
from .store import get_store

app = typer.Typer(help="Refund Hunter", no_args_is_help=True)


@app.command()
def run(user: str = "local", trigger: str = "cli"):
    """Run today's check: read mail, hunt refunds, file approved claims, follow up."""
    from .run import run_daily

    report = asyncio.run(run_daily(user, trigger=trigger))
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))


@app.command()
def decisions(user: str = "local"):
    """List decisions waiting for you."""
    state = get_store().load(user)
    for d in state.pending_decisions():
        typer.echo(f"{d.interrupt_id}\n  {d.question}\n")


@app.command()
def decide(interrupt_id: str, answer: str, user: str = "local"):
    """Answer a decision: approve | skip."""
    from .run import decide as _decide

    report = asyncio.run(_decide(interrupt_id, answer, user))
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2))


@app.command()
def state(user: str = "local"):
    """Dump the current state."""
    typer.echo(get_store().load(user).model_dump_json(indent=2))


@app.command()
def reset(user: str = "local"):
    """Wipe the state (and local agent sessions) for a fresh demo."""
    get_store().reset(user)
    sessions = settings.data_dir / "sessions"
    if sessions.exists():
        import shutil

        shutil.rmtree(sessions, ignore_errors=True)
    typer.echo("reset")


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Serve the dashboard + API."""
    uvicorn.run("refundhunter.api:app", host=host, port=port, reload=reload)


@app.command("create-table")
def create_table():
    """Create the DynamoDB table (deployed mode)."""
    from .store import DynamoStore

    typer.echo(DynamoStore.ensure_table())


if __name__ == "__main__":
    app()
