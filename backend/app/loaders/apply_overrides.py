"""Manual corrections for hero / heroine / villain.

TMDB does not label these roles, so tmdb_loader only guesses. Put the fixes
in data/role_overrides.csv, then run:

    python -m app.loaders.apply_overrides
    python -m app.loaders.apply_overrides --cast "Eega"    (lists the TMDB cast)

Run it AFTER tmdb_loader, because that loader rebuilds the crew from scratch.
"""
import argparse
import csv
import requests
import sys
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.loaders.cleaning import clean_text, norm_key
from app.loaders.tmdb_loader import make_session, tmdb_get, upsert_person
from app.models import Film, FilmCrew

FILE = Path(__file__).resolve().parents[2] / "data" / "role_overrides.csv"
ROLES = {"hero", "heroine", "villain"}
GENDER = {1: "F", 2: "M"}


def find_film(db, title):
    films = {norm_key(f.title): f for f in db.scalars(select(Film))}
    return films.get(norm_key(title))


def show_cast(title):
    """Print the top 15 billed cast so you can copy exact names."""
    session = make_session()
    with SessionLocal() as db:
        film = find_film(db, title)
        if film is None or not film.tmdb_id:
            raise SystemExit(f"'{title}' not found, or it has no tmdb_id yet.")
        credits = tmdb_get(session, f"/movie/{film.tmdb_id}/credits")
        for c in sorted(credits["cast"], key=lambda c: c.get("order", 999))[:15]:
            print(f"{c.get('order', '-'):>3}  {c['name']:<28} "
                  f"{GENDER.get(c.get('gender'), '?')}  as {c.get('character') or '-'}")


def apply():
    if not FILE.exists():
        raise SystemExit(f"File not found: {FILE}")
    session = make_session()
    cache = {}  # film id -> TMDB credits (one request per film)

    with SessionLocal() as db, open(FILE, encoding="utf-8-sig", newline="") as f:
        for line, row in enumerate(csv.DictReader(f), start=2):
            title = clean_text(row.get("film_title"))
            name = clean_text(row.get("person_name"))
            role = (clean_text(row.get("role")) or "").lower()
            action = (clean_text(row.get("action")) or "").lower()

            film = find_film(db, title) if title else None
            if film is None:
                print(f"REJECTED line {line}: film '{title}' is not in the database")
                continue
            if not name or role not in ROLES or action not in {"add", "remove"}:
                print(f"REJECTED line {line}: need person_name, role in {sorted(ROLES)}, action add/remove")
                continue

            if action == "remove":
                rows = [fc for fc in film.crew
                        if fc.role == role and norm_key(fc.person.name) == norm_key(name)]
                for fc in rows:
                    film.crew.remove(fc)
                print(f"{'REMOVED' if rows else 'NOT FOUND'}  {film.title}: {name} as {role}")
                continue

            # action == "add": the person must be in this film's TMDB cast list
            if film.id not in cache:
                try:
                    cache[film.id] = tmdb_get(session, f"/movie/{film.tmdb_id}/credits")
                except (RuntimeError, requests.RequestException) as e:
                    print(f"REJECTED line {line}: TMDB unreachable for {film.title} ({type(e).__name__})")
                    continue
            match = next((c for c in cache[film.id].get("cast", [])
                          if norm_key(c["name"]) == norm_key(name)), None)
            if match is None:
                print(f"REJECTED line {line}: '{name}' not in TMDB cast of {film.title} "
                      f"(run --cast \"{film.title}\" to see exact names)")
                continue
            if any(fc.role == role and fc.person.tmdb_id == match["id"] for fc in film.crew):
                print(f"ALREADY   {film.title}: {name} as {role}")
                continue
            film.crew.append(FilmCrew(person=upsert_person(db, match), role=role,
                                      character_name=clean_text(match.get("character"))))
            print(f"ADDED     {film.title}: {name} as {role}")
        db.commit()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--cast", help="film title: list its top TMDB cast and exit")
    args = parser.parse_args()
    show_cast(args.cast) if args.cast else apply()


if __name__ == "__main__":
    main()