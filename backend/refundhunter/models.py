"""Data model. Everything the agent knows lives in one State document per user."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from enum import Enum

from pydantic import BaseModel, Field


def now() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class Email(BaseModel):
    id: str
    from_addr: str
    subject: str
    date: datetime
    body: str


class PurchaseStatus(str, Enum):
    open = "open"  # still inside a window worth watching
    closed = "closed"  # nothing more can be claimed
    claimed = "claimed"  # a claim exists for it


class Purchase(BaseModel):
    id: str = Field(default_factory=lambda: new_id("pur"))
    merchant: str
    item: str
    price: float
    quantity: int = 1
    currency: str = "USD"
    order_id: str = ""
    order_date: date
    url: str | None = None
    shipping_fee: float = 0.0
    promised_delivery: date | None = None
    delivered_on: date | None = None
    source_email_ids: list[str] = Field(default_factory=list)
    status: PurchaseStatus = PurchaseStatus.open
    notes: str = ""


class ClaimKind(str, Enum):
    price_drop = "price_drop"
    late_delivery = "late_delivery"
    other = "other"


class ClaimStatus(str, Enum):
    pending_approval = "pending_approval"
    filed = "filed"
    followed_up = "followed_up"
    resolved = "resolved"
    skipped = "skipped"


class Claim(BaseModel):
    id: str = Field(default_factory=lambda: new_id("clm"))
    purchase_id: str
    kind: ClaimKind
    amount: float
    reason: str
    policy: str
    status: ClaimStatus = ClaimStatus.pending_approval
    created_at: datetime = Field(default_factory=now)
    filed_at: datetime | None = None
    followed_up_at: datetime | None = None
    resolved_at: datetime | None = None
    outcome: str = ""
    email_subject: str = ""
    email_body: str = ""


class Decision(BaseModel):
    """A Strands interrupt waiting for the human. Answered from the dashboard."""

    interrupt_id: str
    session_id: str
    claim_id: str
    question: str
    options: list[str] = Field(default_factory=lambda: ["approve", "skip"])
    created_at: datetime = Field(default_factory=now)
    answered: str | None = None
    answered_at: datetime | None = None


class OutboxMessage(BaseModel):
    id: str = Field(default_factory=lambda: new_id("msg"))
    to: str
    subject: str
    body: str
    sent_at: datetime = Field(default_factory=now)
    delivered: bool = False  # False = kept in the outbox (dry run)
    claim_id: str | None = None


class RunReport(BaseModel):
    id: str = Field(default_factory=lambda: new_id("run"))
    started_at: datetime = Field(default_factory=now)
    finished_at: datetime | None = None
    trigger: str = "manual"
    emails_seen: int = 0
    purchases_added: int = 0
    claims_proposed: int = 0
    claims_filed: int = 0
    followups_sent: int = 0
    decisions_waiting: int = 0
    summary: str = ""
    log: list[str] = Field(default_factory=list)


class State(BaseModel):
    user_id: str = "local"
    purchases: list[Purchase] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    outbox: list[OutboxMessage] = Field(default_factory=list)
    runs: list[RunReport] = Field(default_factory=list)
    seen_email_ids: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=now)
    # Set by the web tier when it starts a background run; cleared by run_daily when it ends.
    running_since: datetime | None = None

    def is_running(self) -> bool:
        if not self.running_since:
            return False
        return (now() - self.running_since).total_seconds() < 240

    # -- helpers ------------------------------------------------------------
    def purchase(self, purchase_id: str) -> Purchase | None:
        return next((p for p in self.purchases if p.id == purchase_id), None)

    def claim(self, claim_id: str) -> Claim | None:
        return next((c for c in self.claims if c.id == claim_id), None)

    def claims_for(self, purchase_id: str) -> list[Claim]:
        return [c for c in self.claims if c.purchase_id == purchase_id]

    def pending_decisions(self) -> list[Decision]:
        return [d for d in self.decisions if d.answered is None]

    def money_found(self) -> float:
        return round(sum(c.amount for c in self.claims if c.status != ClaimStatus.skipped), 2)

    def money_filed(self) -> float:
        return round(
            sum(
                c.amount
                for c in self.claims
                if c.status in (ClaimStatus.filed, ClaimStatus.followed_up, ClaimStatus.resolved)
            ),
            2,
        )
