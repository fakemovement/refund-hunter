"""Claim bookkeeping that needs no agent (used by the web tier without importing Strands)."""

from __future__ import annotations

from datetime import UTC, datetime

from .models import ClaimStatus
from .store import get_store


def resolve_claim(claim_id: str, outcome: str, user_id: str = "local") -> None:
    """The person tells us a store answered (refund received / refused)."""
    store = get_store()
    state = store.load(user_id)
    c = state.claim(claim_id)
    if not c:
        raise KeyError(claim_id)
    c.status = ClaimStatus.resolved
    c.resolved_at = datetime.now(UTC)
    c.outcome = outcome
    store.save(state)
