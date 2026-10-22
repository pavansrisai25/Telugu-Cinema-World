"""Load IMDb ratings from the official non-commercial dataset.

    python -m app.loaders.imdb_loader            (downloads the file once)
    python -m app.loaders.imdb_loader --refresh  (download a fresh copy)
Run tmdb_loader first: it provides each film's imdb_id.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import requests
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.loaders.db_helpers import upsert_rating
from app.models import Film

URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"
FILE = Path(__file__).resolve().parents[2] / "data" / "imdb" / "title.ratings.tsv.gz"


def download():
    FILE.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(FILE, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="download a fresh copy")
    args = parser.parse_args()

    if args.refresh or not FILE.exists():
        print("Downloading IMDb ratings dataset (a few MB)...")
        download()

    # IMDb writes missing values as \N
    ratings = pd.read_csv(FILE, sep="\t", na_values="\\N", dtype={"tconst": str}).set_index("tconst")

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        films = db.scalars(select(Film).order_by(Film.release_date)).all()
        for film in films:
            if not film.imdb_id:
                print(f"SKIP {film.title:<32} no imdb_id (run tmdb_loader first, or not on TMDB)")
            elif film.imdb_id in ratings.index:
                row = ratings.loc[film.imdb_id]
                upsert_rating(db, film.id, "imdb", float(row["averageRating"]), int(row["numVotes"]))
                print(f"OK   {film.title:<32} {film.imdb_id}  {row['averageRating']} ({int(row['numVotes'])} votes)")
            else:
                print(f"SKIP {film.title:<32} {film.imdb_id} not in dataset")
        db.commit()


if __name__ == "__main__":
    main()