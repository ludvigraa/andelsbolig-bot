"""Orchestrator: hent alle kilder -> find nye opslag -> notificér -> gem state.

Koeres af GitHub Actions hvert par minutter (eller lokalt).

  python -m scraper.main             # normal koersel
  python -m scraper.main --dry-run   # hent og print, send/gem intet
"""
from __future__ import annotations

import os
import sys

try:  # gør lokal .env nem; valgfrit i cloud hvor secrets er env vars
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from .sources.base import Listing, Source
from .sources.andelsboliger_dk import AndelsboligerDk
from .sources.boligdeal import Boligdeal
from . import notify
from .state import is_first_run, load_seen, save_seen


def build_sources() -> list[Source]:
    pages = int(os.environ.get("POLL_PAGES", "1"))
    return [AndelsboligerDk(pages=pages), Boligdeal(pages=pages)]


def collect_listings(sources: list[Source]) -> list[Listing]:
    """Hent fra alle kilder; isolér fejl saa én doed portal ikke vaelter resten."""
    all_listings: list[Listing] = []
    for source in sources:
        try:
            found = source.fetch()
            print(f"  {source.name}: {len(found)} opslag")
            all_listings.extend(found)
        except Exception as exc:  # noqa: BLE001
            print(f"  {source.name}: FEJL — {exc}", file=sys.stderr)
    return all_listings


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    dry_run = "--dry-run" in argv

    print("Henter opslag…")
    listings = collect_listings(build_sources())

    # Behold kun ét opslag pr. dedup-noegle.
    unique: dict[str, Listing] = {l.key: l for l in listings}
    print(f"I alt {len(unique)} unikke opslag.")

    if dry_run:
        for listing in unique.values():
            print(f"  - [{listing.source}] {listing.title} | {listing.price} | {listing.url}")
        return 0

    first_run = is_first_run()
    seen = load_seen()

    new_keys = [k for k in unique if k not in seen]

    if first_run:
        # Foerste koersel: marker alt som set, spam ikke alle eksisterende opslag.
        save_seen(set(unique))
        try:
            notify.send_message(
                "👋 <b>Andelsbolig-bot er live.</b> "
                f"Overvaager {len(unique)} eksisterende opslag — "
                "du faar besked naar nye dukker op."
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Kunne ikke sende opstartsbesked: {exc}", file=sys.stderr)
        print(f"Foerste koersel: {len(unique)} opslag markeret som set.")
        return 0

    print(f"{len(new_keys)} nye opslag.")
    sent = 0
    for key in new_keys:
        listing = unique[key]
        try:
            notify.notify_listing(listing)
            sent += 1
        except Exception as exc:  # noqa: BLE001
            print(f"Kunne ikke notificere {key}: {exc}", file=sys.stderr)

    # Gem state — inkl. alt vi saa, saa fjernede opslag ikke dukker op igen.
    save_seen(seen | set(unique))
    print(f"Sendte {sent} notifikationer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
