"""Kilde: andelsboliger.dk — Danmarks stoerste andelsbolig-portal."""
from __future__ import annotations

from .base import Source, Listing, get_html
from ._itemcard import parse_item_cards

BASE_URL = "https://www.andelsboliger.dk"


class AndelsboligerDk(Source):
    name = "andelsboliger.dk"

    def __init__(self, pages: int = 1) -> None:
        self.pages = max(1, pages)

    def _page_url(self, page: int) -> str:
        path = "/andelsboliger/koebenhavn"
        return f"{BASE_URL}{path}" if page == 1 else f"{BASE_URL}{path}/side{page}"

    def fetch(self) -> list[Listing]:
        out: list[Listing] = []
        for page in range(1, self.pages + 1):
            html = get_html(self._page_url(page))
            out.extend(
                parse_item_cards(html, source=self.name, base_url=BASE_URL)
            )
        return out
