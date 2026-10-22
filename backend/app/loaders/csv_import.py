"""Import collections / budgets from CSV with strict validation.

    python -m app.loaders.csv_import collections
    python -m app.loaders.csv_import budgets
Every row MUST have source_name, source_url (http...) and fetched_on (YYYY-MM-DD).
Non-INR rows MUST have original_amount and conversion_note.
"""
import argparse
import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.loaders.cleaning import (ALLOWED_MARKETS, clean_text, norm_key,
                                  parse_date, parse_number)
from app.models import Collection, Film

DATA = Path(__file__).resolve().parents[2] / "data"


def read_source(row):
    name = clean_text(row.get("source_name"))
    url = clean_text(row.get("source_url"))
    fetched = parse_date(row.get("fetched_on"))
    if not name:
        raise ValueError("source_name is missing")
    if not url or not url.lower().startswith("http"):
        raise ValueError("source_url must start with http")
    if fetched is None:
        raise ValueError("fetched_on is missing (use YYYY-MM-DD)")
    if fetched > date.today():
        raise ValueError("fetched_on is in the future")
    return name, url, fetched


def read_money(row, field):
    """Returns (amount_in_crore, currency, original_amount, conversion_note)."""
    amount = parse_number(row.get(field))
    if amount is None or amount <= 0:
        raise ValueError(f"{field} must be a number greater than 0")
    currency = (clean_text(row.get("original_currency")) or "INR").upper()
    original = parse_number(row.get("original_amount"))
    note = clean_text(row.get("conversion_note"))
    if currency == "INR":
        original = original if original is not None else amount
        note = note or "Published in Rs crore"
    elif original is None or not note:
        raise ValueError(f"{currency} rows need original_amount and conversion_note")
    return amount, currency, original, note


def find_film(films, row):
    title = clean_text(row.get("film_title"))
    film = films.get(norm_key(title))
    if film is None:
        raise ValueError(f"film '{title}' is not in the database (use the title from seed_films.csv)")
    return film


def open_rows(path):
    if not path.exists():
        raise SystemExit(f"File not found: {path}\nCopy the *_template.csv next to it and fill it in.")
    with open(path, encoding="utf-8-sig", newline="") as f:  # utf-8-sig handles Excel files
        yield from enumerate(csv.DictReader(f), start=2)  # line 1 is the header


def import_collections(db, films, path):
    ok, errors = 0, []
    seen = defaultdict(dict)  # (film title, source) -> {market: amount}
    for line, row in open_rows(path):
        try:
            film = find_film(films, row)
            market = (clean_text(row.get("market")) or "").lower()
            if market not in ALLOWED_MARKETS:
                raise ValueError(f"market must be one of {sorted(ALLOWED_MARKETS)}")
            amount, cur, orig, note = read_money(row, "amount_cr")
            src_name, src_url, fetched = read_source(row)
        except ValueError as e:
            errors.append((line, str(e)))
            continue

        c = db.scalar(select(Collection).where(
            Collection.film_id == film.id, Collection.market == market,
            Collection.source_name == src_name))
        if c is None:
            c = Collection(film_id=film.id, market=market)
            db.add(c)
        c.amount_cr, c.original_currency, c.original_amount = amount, cur, orig
        c.conversion_note, c.label = note, "Reported"
        c.source_name, c.source_url, c.fetched_on = src_name, src_url, fetched
        seen[(film.title, src_name)][market] = amount
        ok += 1

    # Sanity checks inside one source: worldwide >= india_net >= hindi_belt
    warnings = []
    for (title, src), m in seen.items():
        if "india_net" in m and "worldwide" in m and m["india_net"] > m["worldwide"]:
            warnings.append(f"{title} [{src}]: india_net is larger than worldwide")
        if "hindi_belt" in m and "india_net" in m and m["hindi_belt"] > m["india_net"]:
            warnings.append(f"{title} [{src}]: hindi_belt is larger than india_net")
    return ok, errors, warnings


def import_budgets(db, films, path):
    ok, errors = 0, []
    for line, row in open_rows(path):
        try:
            film = find_film(films, row)
            low, cur, orig, note = read_money(row, "budget_cr")
            high = parse_number(row.get("budget_cr_max"))
            if high is not None and high < low:
                raise ValueError("budget_cr_max must be >= budget_cr")
            src_name, src_url, fetched = read_source(row)
        except ValueError as e:
            errors.append((line, str(e)))
            continue
        film.budget_cr, film.budget_cr_max = low, high
        film.budget_original_currency, film.budget_original_amount = cur, orig
        film.budget_note = note
        film.budget_source_name, film.budget_source_url, film.budget_fetched_on = src_name, src_url, fetched
        ok += 1
    return ok, errors, []


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["collections", "budgets"])
    parser.add_argument("--file", help="CSV path (default: data/<kind>.csv)")
    args = parser.parse_args()
    path = Path(args.file) if args.file else DATA / f"{args.kind}.csv"

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        films = {norm_key(f.title): f for f in db.scalars(select(Film))}
        run = import_collections if args.kind == "collections" else import_budgets
        ok, errors, warnings = run(db, films, path)
        db.commit()

    print(f"Imported {ok} row(s). Rejected {len(errors)}.")
    for line, msg in errors:
        print(f"  REJECTED line {line}: {msg}")
    for w in warnings:
        print(f"  CHECK: {w}")


if __name__ == "__main__":
    main()