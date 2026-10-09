"""Load data/seed_films.csv into the films table.

Run from the backend folder:  python -m app.seed
Safe to run repeatedly: existing films are updated, not duplicated.
"""
import csv
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Film

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "seed_films.csv"


def seed_films() -> None:
    Base.metadata.create_all(bind=engine)
    added = updated = 0

    with SessionLocal() as db, open(SEED_FILE, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            release = date.fromisoformat(row["release_date"])

            # Look for an existing film with the same title + release date.
            film = db.scalar(
                select(Film).where(Film.title == row["title"], Film.release_date == release)
            )
            if film is None:
                film = Film(title=row["title"], release_date=release)
                db.add(film)
                added += 1
            else:
                updated += 1

            film.language = row["language"]
            film.status = row["status"]
            film.director = row["director"]

        db.commit()

        print(f"Seed done: {added} added, {updated} updated.\n")
        print(f"{'ID':<4}{'Title':<34}{'Lang':<9}{'Release':<12}Status")
        for f_ in db.scalars(select(Film).order_by(Film.release_date)):
            print(f"{f_.id:<4}{f_.title:<34}{f_.language:<9}{str(f_.release_date):<12}{f_.status}")


if __name__ == "__main__":
    seed_films()