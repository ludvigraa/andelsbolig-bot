"""Persistering af hvilke opslag vi allerede har set.

Gemmes som JSON i `state/seen.json`. Paa GitHub Actions committes filen tilbage
til repoet efter hver koersel, saa den overlever de flygtige runnere.
"""
from __future__ import annotations

import json
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent.parent / "state" / "seen.json"


def load_seen() -> set[str]:
    """Indlaes sete noegler. Tom set hvis filen mangler eller er korrupt."""
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()
    if isinstance(data, dict):  # tolerér {"seen": [...]} format
        data = data.get("seen", [])
    return set(data) if isinstance(data, list) else set()


def save_seen(keys: set[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(sorted(keys), ensure_ascii=False, indent=0),
        encoding="utf-8",
    )


def is_first_run() -> bool:
    """Sandt hvis vi aldrig har gemt state foer (saa vi ikke spammer alt)."""
    return not STATE_FILE.exists()
