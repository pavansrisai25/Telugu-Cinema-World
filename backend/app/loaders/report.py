"""Coverage report. Run:  python -m app.loaders.report"""
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Film


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    yn = lambda ok: "yes" if ok else "-"
    print(f"{'Title':<32}{'TMDB':<6}{'IMDb':<6}{'Poster':<8}{'Crew':<6}{'Budget':<8}{'Collns':<7}Ratings")
    with SessionLocal() as db:
        for f in db.scalars(select(Film).order_by(Film.release_date)):
            ratings = ",".join(r.source for r in f.ratings) or "-"
            print(f"{f.title:<32}{yn(f.tmdb_id):<6}{yn(f.imdb_id):<6}{yn(f.poster_url):<8}"
                  f"{len(f.crew):<6}{yn(f.budget_cr):<8}{len(f.collections):<7}{ratings}")


if __name__ == "__main__":
    main()