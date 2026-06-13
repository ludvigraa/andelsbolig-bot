"""Faelles byggesten for alle portal-kilder.

Hver portal implementeres som en klasse der arver fra `Source` og returnerer
en liste af `Listing`. Orchestratoren (`scraper.main`) kender kun til disse to
ting, saa nye portaler kan tilfoejes uden at roere resten af koden.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

# Realistisk browser-header saa portaler ikke afviser os som bot.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "da-DK,da;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


@dataclass(frozen=True)
class Listing:
    """Et normaliseret boligopslag paa tvaers af portaler."""

    source: str
    id: str
    title: str
    url: str
    price: str | None = None
    address: str | None = None
    kind: str | None = None  # fx "Andelsbolig" eller "Byttebolig"
    seen_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def key(self) -> str:
        """Stabil dedup-noegle paa tvaers af koersler."""
        return f"{self.source}:{self.id}"


class Source:
    """Basisklasse for en portal-kilde."""

    name: str = "base"

    def fetch(self) -> list[Listing]:  # pragma: no cover - override i subklasser
        raise NotImplementedError


def get_html(url: str, *, timeout: float = 20.0) -> str:
    """Hent en side som tekst med fornuftige headers og fejl ved HTTP-fejl."""
    resp = httpx.get(
        url, headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True
    )
    resp.raise_for_status()
    return resp.text
