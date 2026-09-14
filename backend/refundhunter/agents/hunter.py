"""The Hunter: walks every open purchase, checks store policy, current price, and delivery
timing, and files a claim when money is owed. Filing pauses on a Strands interrupt until the
human approves from the dashboard, then resumes and sends the claim email.

Tools are plain functions over the State object carried in ``invocation_state`` so the
agent never sees or edits raw JSON.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

from strands import Agent, tool
from strands.session.file_session_manager import FileSessionManager
from strands.types.tools import ToolContext

from ..config import settings
from ..mail import send_mail
from ..models import Claim, ClaimKind, ClaimStatus, Purchase, PurchaseStatus, State
from ..policies import find_policy
from ..pricing import current_price
from .llm import get_model

HUNTER_SYSTEM = """You are Refund Hunter, an agent that works in the background for one person.
Your job: find money this person is owed on recent purchases and file the claim, without
bothering them unless a real decision is needed.

Procedure for a run:
1. Call list_open_purchases once.
2. For every open purchase, call lookup_policy for its merchant. Then:
   - If the policy has a price-adjustment window and the purchase is still inside it, call
     check_price. If the current price is lower than what was paid, the refund is
     (paid - current) x quantity.
   - If the purchase has a promised delivery date and a delivered date after it (or a delivery
     time after the scheduled window end), and the policy gives something for late delivery,
     the refund is the shipping fee paid (late_delivery_refund = shipping_fee) or the fixed
     amount (late_delivery_refund = fixed). If the shipping fee was $0 and the refund type is
     shipping_fee, there is nothing to claim.
   Call several tools in one turn when they do not depend on each other. Gather ALL the facts
   (policies, prices, delivery dates) for every purchase before filing anything.
3. Then, in ONE turn, call file_claim once for every refund worth at least the minimum amount
   (several file_claim calls in the same turn). file_claim asks the person for approval and then
   sends the claim, so you do not write emails yourself. Never file two claims for the same
   purchase and kind. Filing everything in one turn matters: the person sees all questions at
   once instead of one at a time.
4. Call close_purchase, with a one-line reason, only for purchases where nothing can ever be
   claimed any more: outside the store's price-adjustment window (or the store has none) AND
   delivered on time or with no delivery promise to check. A purchase still inside a window whose
   price simply has not dropped yet stays open; you will check it again tomorrow.
5. After the person has answered, make sure every refund you found has a claim (filed or skipped);
   if any is still missing, file it now. Finish with a plain two-sentence summary of what you
   found. Be precise with dollar amounts.

Rules: never invent prices or policies; only use what the tools return. Do not claim when the
policy says there is no price adjustment. Use the person's own words in the summary sparingly;
it is read by them once a day."""


def _today() -> date:
    return datetime.now(UTC).date()


def _state(ctx: ToolContext) -> State:
    return ctx.invocation_state["state"]


def _log(ctx: ToolContext, line: str) -> None:
    ctx.invocation_state.setdefault("log", []).append(line)


@tool(context=True)
def list_open_purchases(tool_context: ToolContext) -> str:
    """List the purchases that are still open (inside a window worth checking). Call once."""
    state = _state(tool_context)
    rows = []
    for p in state.purchases:
        if p.status != PurchaseStatus.open:
            continue
        rows.append(
            {
                "purchase_id": p.id,
                "merchant": p.merchant,
                "item": p.item,
                "paid_each": p.price,
                "quantity": p.quantity,
                "order_date": p.order_date.isoformat(),
                "days_since_order": (_today() - p.order_date).days,
                "has_url": bool(p.url),
                "shipping_fee_paid": p.shipping_fee,
                "promised_delivery": p.promised_delivery.isoformat() if p.promised_delivery else None,
                "delivered_on": p.delivered_on.isoformat() if p.delivered_on else None,
                "delivery_notes": p.notes,
                "existing_claims": [f"{c.kind.value}:{c.status.value}" for c in state.claims_for(p.id)],
            }
        )
    return json.dumps({"today": _today().isoformat(), "purchases": rows})


@tool
def lookup_policy(merchant: str) -> str:
    """Look up a store's price-adjustment window and late-delivery rules.

    Args:
        merchant: Store name as it appears on the receipt (e.g. "Target", "Amazon").
    """
    p = find_policy(merchant)
    if not p:
        return json.dumps({"merchant": merchant, "known": False, "note": "No policy on file; nothing to claim."})
    return json.dumps({"known": True, **p.model_dump()})


@tool(context=True)
async def check_price(tool_context: ToolContext, purchase_id: str) -> str:
    """Check the store's current price for a purchase (reads the product page, or the price feed).

    Args:
        purchase_id: The purchase to check.
    """
    state = _state(tool_context)
    p = state.purchase(purchase_id)
    if not p:
        return json.dumps({"error": "unknown purchase"})
    price, source = await current_price(p.url, p.merchant, p.item)
    _log(tool_context, f"price check {p.merchant} / {p.item}: paid {p.price} now {price} ({source})")
    return json.dumps(
        {
            "purchase_id": p.id,
            "paid_each": p.price,
            "current_price": price,
            "source": source,
            "drop_each": round(p.price - price, 2) if price is not None else None,
        }
    )


@tool(context=True)
def close_purchase(tool_context: ToolContext, purchase_id: str, reason: str) -> str:
    """Mark a purchase as closed: nothing can be claimed on it any more.

    Args:
        purchase_id: The purchase to close.
        reason: One line explaining why (e.g. "outside Best Buy's 15-day window").
    """
    state = _state(tool_context)
    p = state.purchase(purchase_id)
    if not p:
        return "unknown purchase"
    p.status = PurchaseStatus.closed
    p.notes = (p.notes + " | " if p.notes else "") + f"closed: {reason}"
    _log(tool_context, f"closed {p.merchant} / {p.item}: {reason}")
    return "closed"


@tool(context=True)
def file_claim(
    tool_context: ToolContext,
    purchase_id: str,
    kind: str,
    amount: float,
    reason: str,
    policy: str,
) -> str:
    """File a refund claim for a purchase. Pauses for the person's approval, then emails the store.

    Args:
        purchase_id: The purchase the claim is about.
        kind: "price_drop" or "late_delivery".
        amount: Refund amount in dollars.
        reason: One or two sentences with the facts (paid, current price / dates, window).
        policy: The store rule this relies on, in one sentence.
    """
    state = _state(tool_context)
    p = state.purchase(purchase_id)
    if not p:
        return json.dumps({"error": "unknown purchase"})
    if amount < settings.min_claim_amount:
        return json.dumps({"filed": False, "note": f"below minimum ${settings.min_claim_amount:.2f}"})
    kind_enum = ClaimKind(kind) if kind in ClaimKind.__members__ else ClaimKind.other
    # A claim that is still waiting for approval is not a duplicate: the tool re-runs from the
    # top when the agent resumes, and must reach the interrupt again to collect the answer.
    existing = next(
        (
            c
            for c in state.claims_for(p.id)
            if c.kind == kind_enum
            and c.status not in (ClaimStatus.skipped, ClaimStatus.pending_approval)
        ),
        None,
    )
    if existing:
        return json.dumps({"filed": False, "note": "a claim of this kind already exists", "claim_id": existing.id})

    # Deterministic id: the tool re-runs from the top when the agent resumes after the
    # interrupt, and the dashboard must recognise the same claim both times.
    claim = Claim(
        id=f"clm_{p.id.removeprefix('pur_')}_{kind_enum.value}",
        purchase_id=p.id, kind=kind_enum, amount=round(amount, 2), reason=reason, policy=policy,
    )
    question = (
        f"{p.merchant}: {reason} Claim ${claim.amount:.2f} ({kind_enum.value.replace('_', ' ')})?"
    )
    payload = {
        "claim": claim.model_dump(mode="json"),
        "purchase": p.model_dump(mode="json"),
        "question": question,
        "options": ["approve", "skip"],
    }
    # --- the human decision: a Strands interrupt ---------------------------------------
    # The agent stops here and the dashboard shows the question. When several claims are
    # waiting and the person answers only one, the others come back as "pending" and are
    # raised again under a new name so they keep waiting for their own answer.
    base = f"approve_claim_{p.id}_{kind_enum.value}"
    decision = tool_context.interrupt(base, reason=payload)
    attempt = 0
    while str(decision).lower() == "pending" and attempt < 20:
        attempt += 1
        decision = tool_context.interrupt(f"{base}#{attempt}", reason=payload)
    # --- resumed with the answer ------------------------------------------------------
    state.claims = [c for c in state.claims if c.id != claim.id]
    state.claims.append(claim)
    if str(decision).lower().startswith("approve"):
        subject, body = _claim_email(p, claim)
        pol = find_policy(p.merchant)
        to = (pol.claims_email if pol and pol.claims_email else f"support@{p.merchant.lower().replace(' ', '')}.example")
        msg = send_mail(state, to=to, subject=subject, body=body, claim_id=claim.id)
        claim.status = ClaimStatus.filed
        claim.filed_at = datetime.now(UTC)
        claim.email_subject, claim.email_body = subject, body
        p.status = PurchaseStatus.claimed
        _log(tool_context, f"filed {claim.kind.value} ${claim.amount:.2f} with {p.merchant} -> {msg.to} (delivered={msg.delivered})")
        return json.dumps({"filed": True, "claim_id": claim.id, "sent_to": msg.to, "delivered": msg.delivered})
    claim.status = ClaimStatus.skipped
    claim.outcome = "skipped by owner"
    _log(tool_context, f"skipped {claim.kind.value} ${claim.amount:.2f} with {p.merchant}")
    return json.dumps({"filed": False, "claim_id": claim.id, "note": "owner chose to skip"})


def _claim_email(p: Purchase, c: Claim) -> tuple[str, str]:
    owner = settings.owner_name
    if c.kind == ClaimKind.price_drop:
        subject = f"Price adjustment request, order {p.order_id}"
        body = (
            f"Hello {p.merchant} team,\n\n"
            f"I ordered the {p.item} on {p.order_date.strftime('%B %d, %Y')} (order {p.order_id}) and paid "
            f"${p.price:.2f}. The same item is now listed at a lower price on your site, and my order is "
            f"still inside your price-adjustment window.\n\n{c.policy}\n\n"
            f"Could you please refund the difference of ${c.amount:.2f} to my original payment method?\n\n"
            f"Thank you,\n{owner}\n{settings.owner_email}"
        )
    else:
        subject = f"Late delivery refund request, order {p.order_id}"
        if p.notes and "scheduled window" in p.notes and "closed:" not in p.notes:
            timing = (
                f"was scheduled for a delivery window on "
                f"{p.delivered_on.strftime('%B %d, %Y') if p.delivered_on else 'the promised day'} "
                f"({p.notes.split('|')[0].strip()})"
            )
        else:
            timing = (
                f"had a promised delivery date of "
                f"{p.promised_delivery.strftime('%B %d, %Y') if p.promised_delivery else 'the scheduled window'} "
                f"and arrived on {p.delivered_on.strftime('%B %d, %Y') if p.delivered_on else 'a later date'}"
            )
        body = (
            f"Hello {p.merchant} team,\n\n"
            f"My order {p.order_id} ({p.item}) {timing}.\n\n{c.policy}\n\n"
            f"Could you please refund ${c.amount:.2f} to my original payment method?\n\n"
            f"Thank you,\n{owner}\n{settings.owner_email}"
        )
    return subject, body


HUNTER_TOOLS = [list_open_purchases, lookup_policy, check_price, close_purchase, file_claim]


def build_hunter(session_id: str) -> Agent:
    session_manager = _session_manager(session_id)
    return Agent(
        model=get_model("hunter"),
        system_prompt=HUNTER_SYSTEM,
        tools=HUNTER_TOOLS,
        session_manager=session_manager,
        callback_handler=None,
    )


def _session_manager(session_id: str):
    if settings.session_backend == "s3" and settings.session_bucket:
        from strands.session.s3_session_manager import S3SessionManager

        return S3SessionManager(
            session_id=session_id, bucket=settings.session_bucket, prefix="sessions/",
            region_name=settings.aws_region,
        )
    sessions_dir = settings.data_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return FileSessionManager(session_id=session_id, storage_dir=str(sessions_dir))
