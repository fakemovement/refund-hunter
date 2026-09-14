"""Current price of an item: read the product page's schema.org data, else the demo price feed."""

from __future__ import annotations

import json
import re

import httpx
from bs4 import BeautifulSoup

from .config import settings

_UA = "Mozilla/5.0 (compatible; RefundHunter/0.1; +https://github.com/refund-hunter)"


async def current_price(url: str | None, merchant: str, item: str) -> tuple[float | None, str]:
    """Return (price, source). Source is 'page' or 'feed' or 'unknown'."""
    if url:
        feed = _feed_price(url)
        if feed is not None:
            return feed, "feed"
        page = await _page_price(url)
        if page is not None:
            return page, "page"
    return None, "unknown"


def _feed_price(url: str) -> float | None:
    path = settings.fixtures_dir / "prices.json"
    if not path.exists():
        return None
    try:
        prices = json.loads(path.read_text(encoding="utf-8"))["prices"]
    except Exception:  # noqa: BLE001
        return None
    value = prices.get(url)
    return float(value) if value is not None else None


async def _page_price(url: str) -> float | None:
    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=15, headers={"User-Agent": _UA}
        ) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return None
            html = r.text
    except Exception:  # noqa: BLE001
        return None
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except Exception:  # noqa: BLE001
            continue
        price = _price_in(data)
        if price is not None:
            return price
    meta = soup.find("meta", property="product:price:amount") or soup.find(
        "meta", attrs={"itemprop": "price"}
    )
    if meta and meta.get("content"):
        try:
            return float(re.sub(r"[^\d.]", "", meta["content"]))
        except ValueError:
            return None
    return None


def _price_in(data) -> float | None:
    if isinstance(data, list):
        for d in data:
            p = _price_in(d)
            if p is not None:
                return p
        return None
    if not isinstance(data, dict):
        return None
    if data.get("@type") in ("Product", "ProductGroup") or "offers" in data:
        offers = data.get("offers")
        if isinstance(offers, list):
            offers = offers[0] if offers else None
        if isinstance(offers, dict):
            for key in ("price", "lowPrice"):
                if offers.get(key) not in (None, ""):
                    try:
                        return float(str(offers[key]).replace(",", ""))
                    except ValueError:
                        pass
    for v in data.values():
        if isinstance(v, (dict, list)):
            p = _price_in(v)
            if p is not None:
                return p
    return None
