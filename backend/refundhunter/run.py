"""One background run, end to end, plus answering a decision later.

    run_daily():  mail -> Receipt Reader -> Hunter (files claims, may pause on interrupts)
                  -> follow-ups on quiet claims -> report
    decide():     answer one pending interrupt -> the Hunter resumes exactly where it stopped
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .agents import reader
from .agents.hunter import build_hunter
from .config import settings
from .mail import get_mail_source, send_mail
from .models import ClaimStatus, Decision, RunReport, State
from .policies import find_policy
from .store import get_store


def _session_id(state: State, run_id: str) -> str:
    return f"{state.user_id}-{run_id}"


async def run_daily(user_id: str = "local", trigger: str = "manual") -> RunReport:
    store = get_store()
    state = store.load(user_id)
    report = RunReport(trigger=trigger)
    log = report.log

    # 1. mail -> purchases
    emails = get_mail_source().fetch(settings.imap_lookback_days)
    new = [e for e in emails if e.id not in state.seen_email_ids]
    report.emails_seen = len(new)
    if new:
        extraction = await reader.extract(new, datetime.now(UTC).date())
        report.purchases_added = reader.apply(state, extraction, log)
        state.seen_email_ids.extend(e.id for e in new)
        log.append(f"reader: {len(new)} new emails, {report.purchases_added} purchases added")
    else:
        log.append("reader: no new emails")
    store.save(state)

    # 2. the Hunter
    agent = build_hunter(_session_id(state, report.id))
    invocation_state = {"state": state, "log": log}
    result = await agent.invoke_async(
        "Run today's check over every open purchase.", invocation_state=invocation_state
    )
    _absorb(state, report, result, _session_id(state, report.id))

    # 3. follow-ups on claims that went quiet
    report.followups_sent = _followups(state, log)

    # 4. wrap up
    report.claims_filed = sum(1 for c in state.claims if c.filed_at and c.filed_at >= report.started_at)
    report.claims_proposed = report.claims_filed + report.decisions_waiting
    report.finished_at = datetime.now(UTC)
    if not report.summary:
        report.summary = "Nothing new to claim today."
    state.runs.insert(0, report)
    state.runs = state.runs[:30]
    state.updated_at = datetime.now(UTC)
    state.running_since = None
    store.save(state)
    return report


def _absorb(state: State, report: RunReport, result, session_id: str) -> None:
    """Record the agent's outcome: pending interrupts become Decisions; text becomes the summary."""
    if result.stop_reason == "interrupt":
        for it in result.interrupts or []:
            reason = it.reason or {}
            claim = reason.get("claim", {})
            if any(d.interrupt_id == it.id for d in state.decisions):
                continue
            state.decisions.append(
                Decision(
                    interrupt_id=it.id,
                    session_id=session_id,
                    claim_id=claim.get("id", ""),
                    question=reason.get("question", "Approve this claim?"),
                    options=reason.get("options", ["approve", "skip"]),
                )
            )
            # keep the proposed claim visible on the dashboard while it waits
            _stash_pending_claim(state, reason)
        report.decisions_waiting = len(state.pending_decisions())
        report.summary = (
            f"{report.decisions_waiting} claim(s) waiting for your yes."
            if report.decisions_waiting
            else ""
        )
        report.log.append(f"hunter paused: {report.decisions_waiting} decision(s) waiting")
    else:
        text = str(result).strip()
        report.summary = text[:600]
        report.log.append("hunter finished")


def _stash_pending_claim(state: State, reason: dict) -> None:
    from .models import Claim

    data = reason.get("claim")
    if not data:
        return
    if state.claim(data["id"]):
        return
    state.claims.append(Claim.model_validate(data))


async def decide(interrupt_id: str, answer: str, user_id: str = "local") -> RunReport:
    """Answer one pending decision and let the Hunter resume."""
    store = get_store()
    state = store.load(user_id)
    decision = next((d for d in state.decisions if d.interrupt_id == interrupt_id), None)
    if decision is None:
        raise KeyError(f"no such decision {interrupt_id}")
    if decision.answered:
        raise ValueError("already answered")
    decision.answered = answer
    decision.answered_at = datetime.now(UTC)
    # the provisional claim row is replaced by the one file_claim writes on resume
    state.claims = [c for c in state.claims if c.id != decision.claim_id]

    report = RunReport(trigger="decision")
    log = report.log
    # Every interrupt from the same paused session must be answered together; the ones the
    # person has not touched yet are answered "skip" only if they were explicitly skipped,
    # otherwise we re-raise them by answering them now with their own pending answers.
    # Strands needs a response for every interrupt that is currently open in this session:
    # the one just answered, plus the others still waiting, which are answered "pending" so
    # the tool raises them again (new id) and they keep waiting for their own answer.
    batch = [d for d in state.decisions if d.session_id == decision.session_id and d.answered is None]
    batch.append(decision)
    responses = [
        {"interruptResponse": {"interruptId": d.interrupt_id, "response": d.answered or "pending"}}
        for d in batch
    ]
    agent = build_hunter(decision.session_id)
    result = await agent.invoke_async(responses, invocation_state={"state": state, "log": log})
    _absorb_resume(state, report, result, decision.session_id, batch)
    report.claims_filed = sum(1 for c in state.claims if c.filed_at and c.filed_at >= report.started_at)
    report.finished_at = datetime.now(UTC)
    state.runs.insert(0, report)
    state.updated_at = datetime.now(UTC)
    store.save(state)
    return report


def _absorb_resume(state: State, report: RunReport, result, session_id: str, batch: list[Decision]) -> None:
    """After a resume, decisions answered 'pending' come back as fresh interrupts (new ids)."""
    if result.stop_reason == "interrupt":
        fresh = {it.id: it for it in (result.interrupts or [])}
        for d in batch:
            if d.answered == "pending":
                d.answered = None  # still waiting; may have a new interrupt id
        for it in fresh.values():
            reason = it.reason or {}
            claim = reason.get("claim", {})
            existing = next((d for d in state.decisions if d.claim_id == claim.get("id") and d.answered is None), None)
            if existing:
                existing.interrupt_id = it.id
                existing.session_id = session_id
            elif not any(d.interrupt_id == it.id for d in state.decisions):
                state.decisions.append(
                    Decision(
                        interrupt_id=it.id,
                        session_id=session_id,
                        claim_id=claim.get("id", ""),
                        question=reason.get("question", "Approve this claim?"),
                        options=reason.get("options", ["approve", "skip"]),
                    )
                )
                _stash_pending_claim(state, reason)
        report.decisions_waiting = len(state.pending_decisions())
        report.summary = f"Done. {report.decisions_waiting} decision(s) still waiting."
    else:
        report.summary = str(result).strip()[:600]
        report.decisions_waiting = 0
    report.log.append(report.summary)


def _followups(state: State, log: list[str]) -> int:
    """Claims filed N days ago with no outcome get one polite follow-up."""
    sent = 0
    cutoff = datetime.now(UTC) - timedelta(days=settings.followup_after_days)
    for c in state.claims:
        if c.status != ClaimStatus.filed or not c.filed_at or c.filed_at > cutoff:
            continue
        p = state.purchase(c.purchase_id)
        if not p:
            continue
        pol = find_policy(p.merchant)
        to = pol.claims_email if pol and pol.claims_email else f"support@{p.merchant.lower()}.example"
        body = (
            f"Hello {p.merchant} team,\n\nFollowing up on my request from "
            f"{c.filed_at.strftime('%B %d')} about order {p.order_id} ({p.item}): "
            f"a refund of ${c.amount:.2f}. I have not heard back yet. Could you let me know the status?\n\n"
            f"Thank you,\n{settings.owner_name}"
        )
        send_mail(state, to=to, subject=f"Re: {c.email_subject or 'Refund request'}", body=body, claim_id=c.id)
        c.status = ClaimStatus.followed_up
        c.followed_up_at = datetime.now(UTC)
        log.append(f"follow-up sent to {p.merchant} for claim {c.id}")
        sent += 1
    return sent

from .claims import resolve_claim  # noqa: E402,F401  (kept for the CLI/API import path)
