"""Afsendelse af Telegram-notifikationer via Bot API.

Token og chat-id laeses fra miljoevariablerne TELEGRAM_BOT_TOKEN og
TELEGRAM_CHAT_ID. Beskeder sendes som HTML, saa vi kan lave klikbare links.
"""
from __future__ import annotations

import os
import sys
from html import escape

import httpx

try:  # gør lokal .env nem; valgfrit i cloud hvor secrets er env vars
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from .sources.base import Listing

API = "https://api.telegram.org/bot{token}/sendMessage"


def _credentials() -> tuple[str, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN og TELEGRAM_CHAT_ID skal vaere sat "
            "(se .env.example / README)."
        )
    return token, chat_id


def send_message(text: str) -> None:
    """Send en raa HTML-besked til den konfigurerede chat."""
    token, chat_id = _credentials()
    resp = httpx.post(
        API.format(token=token),
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=20.0,
    )
    resp.raise_for_status()


def format_listing(listing: Listing) -> str:
    """Byg en paen besked for et enkelt opslag."""
    lines = [f"🏠 <b>Nyt andelsbolig-opslag</b>"]
    if listing.address:
        lines.append(f"📍 {escape(listing.address)}")
    if listing.price:
        lines.append(f"💰 {escape(listing.price)}")
    if listing.kind:
        lines.append(f"🏷️ {escape(listing.kind)}")
    lines.append(escape(listing.title))
    lines.append(f'<a href="{escape(listing.url, quote=True)}">Åbn opslag →</a>')
    lines.append(f"<i>via {escape(listing.source)}</i>")
    return "\n".join(lines)


def notify_listing(listing: Listing) -> None:
    send_message(format_listing(listing))


def _self_test() -> int:
    try:
        send_message(
            "✅ <b>Andelsbolig-bot</b>: testbesked. "
            "Hvis du kan se denne, virker notifikationer."
        )
    except Exception as exc:  # noqa: BLE001
        print(f"FEJL: {exc}", file=sys.stderr)
        return 1
    print("Testbesked sendt.")
    return 0


if __name__ == "__main__":
    if "--test" in sys.argv:
        raise SystemExit(_self_test())
    print("Brug: python -m scraper.notify --test")
