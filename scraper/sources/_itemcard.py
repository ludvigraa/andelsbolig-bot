"""Faelles HTML-parser for portaler der bruger samme "item-card"-markup.

Baade andelsboliger.dk og boligdeal.dk renderer hvert opslag som:

    <div class="item-card">
        <a class="block-overlay" href="/.../<id>" title="..."></a>
        <h4>...</h4>
        <div class="text-label">Andelsbolig|Byttebolig</div>
        <ul><li><label>Pris: </label><span>Ca. 2.790.000 kr.</span></li>...</ul>
    </div>

Det sidste segment i href er et stabilt numerisk id. Standard-sorteringen paa
begge sites er nyeste foerst (faldende id), saa side 1 indeholder de nyeste opslag.
"""
from __future__ import annotations

from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from .base import Listing


def parse_item_cards(html: str, *, source: str, base_url: str) -> list[Listing]:
    tree = HTMLParser(html)
    listings: list[Listing] = []

    for card in tree.css("div.item-card"):
        anchor = card.css_first("a.block-overlay")
        if anchor is None:
            continue
        href = (anchor.attributes.get("href") or "").strip()
        if not href:
            continue

        listing_id = href.rstrip("/").rsplit("/", 1)[-1]
        if not listing_id.isdigit():
            # Spring over kort der ikke peger paa et konkret opslag.
            continue

        title = (anchor.attributes.get("title") or "").strip()
        url = urljoin(base_url, href)

        # Adresse/omraade staar typisk efter " paa " i titlen.
        address = None
        if " på " in title:
            address = title.split(" på ", 1)[1].strip()

        # Pris ligger i et <li> hvis <label> indeholder "Pris".
        price = None
        for li in card.css("li"):
            label = li.css_first("label")
            if label and "pris" in label.text().lower():
                span = li.css_first("span")
                if span:
                    price = span.text(strip=True)
                break

        kind_node = card.css_first("div.text-label")
        kind = kind_node.text(strip=True) if kind_node else None

        listings.append(
            Listing(
                source=source,
                id=listing_id,
                title=title or f"Opslag {listing_id}",
                url=url,
                price=price,
                address=address,
                kind=kind,
            )
        )

    return listings
