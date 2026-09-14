"""Store policies: how long you have to ask for a price adjustment, and what a late delivery earns.

Kept as data (policies.yaml next to this file) so anyone can correct or extend a store without
touching code. The values shipped here are illustrative for the demo; check a store's current
policy page before relying on a number.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

_FILE = Path(__file__).with_name("policies.yaml")


class Policy(BaseModel):
    merchant: str
    aliases: list[str] = []
    price_adjust_days: int | None = None  # None = no price adjustment policy
    price_adjust_how: str = ""
    late_delivery: str = ""  # what you can claim when a promised date is missed
    late_delivery_refund: str = "none"  # none | shipping_fee | fixed
    late_delivery_fixed_amount: float = 0.0
    claims_email: str = ""
    source: str = ""
    notes: str = ""


@lru_cache(maxsize=1)
def all_policies() -> list[Policy]:
    raw = yaml.safe_load(_FILE.read_text(encoding="utf-8"))
    return [Policy(**p) for p in raw["policies"]]


def find_policy(merchant: str) -> Policy | None:
    key = merchant.strip().lower()
    for p in all_policies():
        names = [p.merchant.lower(), *[a.lower() for a in p.aliases]]
        if key in names or any(n in key for n in names):
            return p
    return None
