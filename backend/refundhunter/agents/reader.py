"""The Receipt Reader: turns raw emails into purchase facts (structured output).

One agent call per batch of emails. Anything that is not an order confirmation, shipping
notice, or delivery notice is ignored. Delivery notices update an existing purchase's
``delivered_on`` instead of creating a new purchase.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field
from strands import Agent

from ..models import Email, Purchase, State
from .llm import get_model

READER_SYSTEM = """You read a person's emails and extract only facts about online purchases.

For each ORDER CONFIRMATION email produce one purchase per line item (merchant, item name, unit
price, quantity, order id, order date as YYYY-MM-DD, item URL if present, shipping fee paid,
promised or guaranteed delivery date if stated).
For each SHIPPING notice: report the promised/estimated delivery date for the order if given.
For each DELIVERY notice: report the order id and the date it was actually delivered. For grocery
or restaurant deliveries with a scheduled window, also report the scheduled window end time and the
actual delivery time.
Ignore newsletters, marketing, personal messages, and anything that is not about a specific order.
Never invent an order id, price, or date: leave a field empty when the email does not state it.
Today's date is given in the prompt; resolve month-day dates against it (they are recent, never in
the future by more than a few days)."""


class ExtractedPurchase(BaseModel):
    merchant: str
    item: str
    price: float
    quantity: int = 1
    order_id: str = ""
    order_date: date
    url: str | None = None
    shipping_fee: float = 0.0
    promised_delivery: date | None = None
    source_email_id: str


class DeliveryUpdate(BaseModel):
    order_id: str
    merchant: str = ""
    delivered_on: date | None = None
    promised_delivery: date | None = None
    scheduled_window_end: str | None = Field(default=None, description="e.g. '6:00 PM'")
    delivered_at_time: str | None = Field(default=None, description="e.g. '7:48 PM'")
    source_email_id: str


class Extraction(BaseModel):
    purchases: list[ExtractedPurchase] = Field(default_factory=list)
    deliveries: list[DeliveryUpdate] = Field(default_factory=list)
    ignored_email_ids: list[str] = Field(default_factory=list)


def _render(emails: list[Email]) -> str:
    parts = []
    for e in emails:
        parts.append(
            f"<email id={e.id!r} date={e.date.date().isoformat()} from={e.from_addr!r}>\n"
            f"Subject: {e.subject}\n{e.body.strip()}\n</email>"
        )
    return "\n\n".join(parts)


async def extract(emails: list[Email], today: date) -> Extraction:
    if not emails:
        return Extraction()
    agent = Agent(model=get_model("reader"), system_prompt=READER_SYSTEM, callback_handler=None)
    prompt = f"Today is {today.isoformat()}.\n\nEmails:\n\n{_render(emails)}"
    return await agent.structured_output_async(Extraction, prompt)


def apply(state: State, extraction: Extraction, log: list[str]) -> int:
    """Merge extracted facts into the state. Returns the number of purchases added."""
    added = 0
    for ep in extraction.purchases:
        dup = next(
            (
                p
                for p in state.purchases
                if p.order_id and p.order_id == ep.order_id and p.item.lower() == ep.item.lower()
            ),
            None,
        )
        if dup:
            continue
        p = Purchase(
            merchant=ep.merchant,
            item=ep.item,
            price=ep.price,
            quantity=ep.quantity,
            order_id=ep.order_id,
            order_date=ep.order_date,
            url=ep.url,
            shipping_fee=ep.shipping_fee,
            promised_delivery=ep.promised_delivery,
            source_email_ids=[ep.source_email_id],
        )
        state.purchases.append(p)
        added += 1
        log.append(f"purchase: {p.merchant} / {p.item} ${p.price:.2f} ({p.order_date})")
    for d in extraction.deliveries:
        targets = [p for p in state.purchases if p.order_id and p.order_id == d.order_id]
        if not targets and d.merchant:
            targets = [p for p in state.purchases if p.merchant.lower() == d.merchant.lower()]
        for p in targets:
            if d.promised_delivery and not p.promised_delivery:
                p.promised_delivery = d.promised_delivery
            if d.delivered_on:
                p.delivered_on = d.delivered_on
            if d.scheduled_window_end or d.delivered_at_time:
                p.notes = (
                    f"scheduled window end {d.scheduled_window_end or '?'}; "
                    f"delivered at {d.delivered_at_time or '?'}"
                )
            if d.source_email_id not in p.source_email_ids:
                p.source_email_ids.append(d.source_email_id)
            log.append(f"delivery: {p.merchant} order {p.order_id} -> {p.delivered_on} {p.notes}")
    return added
