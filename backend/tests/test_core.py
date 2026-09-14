"""Tests that need no model: policies, fixtures, pricing feed, state store, claim email text."""

from __future__ import annotations

import asyncio
from datetime import date

from refundhunter.agents.hunter import _claim_email
from refundhunter.mail.source import FixtureMail
from refundhunter.models import Claim, ClaimKind, Purchase, State
from refundhunter.policies import find_policy
from refundhunter.pricing import current_price
from refundhunter.store import LocalStore


def test_policies_known_stores():
    assert find_policy("Target").price_adjust_days == 14
    assert find_policy("costco.com").price_adjust_days == 30
    assert find_policy("Amazon").price_adjust_days is None
    assert find_policy("Amazon").late_delivery_refund == "shipping_fee"
    assert find_policy("Instacart").late_delivery_fixed_amount == 5.0
    assert find_policy("Some Corner Shop") is None


def test_fixture_inbox_dates_are_relative():
    emails = FixtureMail().fetch()
    assert len(emails) == 12
    ids = {e.id for e in emails}
    assert "em_target_order" in ids and "em_newsletter" in ids
    target = next(e for e in emails if e.id == "em_target_order")
    assert "{{" not in target.body  # date tokens resolved
    assert (date.today() - target.date.date()).days == 9


def test_price_feed():
    price, source = asyncio.run(
        current_price("https://www.target.com/p/ninja-foodi-dz201-air-fryer/-/A-79463150", "Target", "x")
    )
    assert (price, source) == (107.99, "feed")
    assert asyncio.run(current_price(None, "Target", "x")) == (None, "unknown")


def test_state_roundtrip(tmp_path):
    store = LocalStore(tmp_path)
    state = State()
    p = Purchase(merchant="Target", item="Air fryer", price=129.99, order_date=date(2026, 9, 5), order_id="1")
    state.purchases.append(p)
    state.claims.append(Claim(purchase_id=p.id, kind=ClaimKind.price_drop, amount=22, reason="r", policy="p"))
    store.save(state)
    back = store.load()
    assert back.purchase(p.id).item == "Air fryer"
    assert back.money_found() == 22


def test_claim_email_mentions_the_facts():
    p = Purchase(merchant="Target", item="Air fryer", price=129.99, order_date=date(2026, 9, 5), order_id="102-1")
    c = Claim(purchase_id=p.id, kind=ClaimKind.price_drop, amount=22.0, reason="r", policy="14-day window")
    subject, body = _claim_email(p, c)
    assert "102-1" in subject and "$22.00" in body and "14-day window" in body
