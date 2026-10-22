"""Helpers that turn messy input into clean, validated values."""
from datetime import date

ALLOWED_MARKETS = {"india_net", "hindi_belt", "overseas", "worldwide"}


def clean_text(value):
    """Trim and collapse spaces. Empty or None becomes None."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def norm_key(text):
    """'S. S. Rajamouli' and 'S.S. Rajamouli' both become 'ssrajamouli'.
    Used to compare names/titles without caring about spaces or punctuation."""
    return "".join(ch for ch in (text or "").lower() if ch.isalnum())


def parse_number(value):
    """'1,234.5' -> 1234.5 ; '' -> None ; 'abc' -> ValueError."""
    text = clean_text(value)
    if text is None:
        return None
    return float(text.replace(",", ""))


def parse_date(value):
    """'2026-10-09' -> date ; '' -> None ; bad format -> ValueError."""
    text = clean_text(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"bad date '{text}', use YYYY-MM-DD")