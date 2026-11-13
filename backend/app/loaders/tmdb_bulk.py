"""Bulk-load films from TMDB: every film of one original language (default Telugu).

Run from the backend folder, with the hotspot or WARP on (TMDB is blocked on your Wi-Fi):

    python -m app.loaders.tmdb_bulk --dry-run          count only, writes nothing
    python -m app.loaders.tmdb_bulk                    add films + TMDB ratings
    python -m app.loaders.tmdb_bulk --details          cast, director, trailer, imdb_id (500 per run)
    python -m app.loaders.tmdb_bulk --ids 12345 67890  add specific films by TMDB id

Safe to re-run: films are matched by tmdb_id, so nothing is duplicated and your curated
films keep their budgets, collections and corrected roles. Budgets and collections are
NOT loaded here; they come only from sourced CSV files.
"""
import argparse
import sys
import time
from collections import Counter
from datetime import date, timedelta

import requests
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.loaders.cleaning import clean_text
from app.loaders.db_helpers import upsert_rating
from app.loaders.tmdb_loader import IMG, make_session, pick_trailer, rebuild_crew, tmdb_get
from app.models import Film

LANGUAGES = {"te": "Telugu", "hi": "Hindi", "kn": "Kannada", "ta": "Tamil", "ml": "Malayalam"}
FIRST_YEAR = 1931
NETWORK_ERRORS = (RuntimeError, requests.RequestException)


def parse_iso(text):
    """'2024-09-27' -> date. Empty or bad input -> None."""
    try:
        return date.fromisoformat(text) if text else None
    except ValueError:
        return None


def status_for(release: date, today: date) -> str:
    return "upcoming" if release > today else "released"


def discover(session, params, max_pages):
    """Yield every film for one search, page by page (TMDB allows at most 500 pages)."""
    page = 1
    while True:
        data = tmdb_get(session, "/discover/movie", language="en-US", include_adult="false",
                        sort_by="popularity.desc", page=page, **params)
        yield from data.get("results", [])
        if page >= min(data.get("total_pages", 1), max_pages, 500):
            return
        page += 1
        time.sleep(0.1)


def store_item(db, item, label, today, by_tmdb, seen, dry):
    """Save one TMDB film. Returns 'added', 'updated' or 'skipped'.
    by_tmdb: tmdb_id -> Film (None in a dry run). seen: {(title, release_date)}."""
    tid = item["id"]
    title = clean_text(item.get("title"))
    release = parse_iso(item.get("release_date"))
    if not title or release is None:
        return "skipped"                                 # no title or date: never guess
    title = title[:200]

    if tid in by_tmdb:                                   # already have it: refresh the rating only
        film = by_tmdb[tid]
        if film is not None and not dry and item.get("vote_count"):
            upsert_rating(db, film.id, "tmdb", item["vote_average"], item["vote_count"])
        return "updated"
    if (title, release) in seen:                         # same title and date, different TMDB id
        return "skipped"
    seen.add((title, release))
    if dry:
        by_tmdb[tid] = None
        return "added"

    poster, backdrop = item.get("poster_path"), item.get("backdrop_path")
    film = Film(
        tmdb_id=tid, title=title, language=label, release_date=release,
        status=status_for(release, today),
        overview=clean_text(item.get("overview")),
        poster_url=f"{IMG}/w500{poster}" if poster else None,
        backdrop_url=f"{IMG}/w1280{backdrop}" if backdrop else None,
    )
    db.add(film)
    db.flush()
    by_tmdb[tid] = film
    if item.get("vote_count"):                           # no votes = no rating row
        upsert_rating(db, film.id, "tmdb", item["vote_average"], item["vote_count"])
    return "added"


def existing_state(db):
    by_tmdb = {f.tmdb_id: f for f in db.scalars(select(Film).where(Film.tmdb_id.is_not(None)))}
    seen = {(f.title, f.release_date) for f in db.scalars(select(Film))}
    return by_tmdb, seen


def discover_all(session, db, args, label, today):
    by_tmdb, seen = existing_state(db)
    passes = [(str(y), {"primary_release_year": y, "vote_count.gte": args.min_votes}, 500)
              for y in range(args.from_year, args.to_year + 1)]
    # Upcoming films have no votes yet, so they get their own pass (most popular first).
    passes.append(("upcoming", {"primary_release_date.gte": (today + timedelta(days=1)).isoformat()},
                   args.upcoming_pages))

    total, failures = Counter(), 0
    for name, extra, max_pages in passes:
        params = {"with_original_language": args.language, **extra}
        try:
            items = list(discover(session, params, max_pages))
            failures = 0
        except NETWORK_ERRORS as e:
            failures += 1
            print(f"{name}: FAILED ({type(e).__name__}). Re-run later to fill it in.")
            if failures >= 3:
                print("Three failures in a row: stopping. Check the hotspot/WARP and retry.")
                break
            continue
        counts = Counter(store_item(db, it, label, today, by_tmdb, seen, args.dry_run) for it in items)
        if not args.dry_run:
            db.commit()
        total.update(counts)
        if items:
            print(f"{name:>8}: {len(items):>4} found | {counts['added']} new, "
                  f"{counts['updated']} already had, {counts['skipped']} skipped")

    verb = "would add" if args.dry_run else "added"
    print(f"\nDone. {verb} {total['added']} films; {total['updated']} were already in the database; "
          f"{total['skipped']} skipped.")


def add_by_ids(session, db, ids, today, dry):
    by_tmdb, seen = existing_state(db)
    for tid in ids:
        try:
            d = tmdb_get(session, f"/movie/{tid}", language="en-US")
        except NETWORK_ERRORS as e:
            print(f"FAILED id {tid}: {type(e).__name__}")
            continue
        label = LANGUAGES.get(d.get("original_language"))
        if label is None:
            print(f"SKIP {d.get('title')}: original language '{d.get('original_language')}' "
                  f"is not one of {sorted(LANGUAGES)}")
            continue
        result = store_item(db, d, label, today, by_tmdb, seen, dry)
        db.commit()
        print(f"{result.upper():<8} {d.get('title')} ({d.get('release_date')})")


def fill_details(session, db, limit, min_votes):
    """Cast, director, trailer and imdb_id for the most-voted films that have no crew yet.
    Films that already have crew (your curated 17) are left alone."""
    candidates = []
    for film in db.scalars(select(Film).where(Film.tmdb_id.is_not(None), ~Film.crew.any())):
        votes = max((r.vote_count or 0 for r in film.ratings if r.source == "tmdb"), default=0)
        if votes >= min_votes:
            candidates.append((votes, film.id))
    candidates.sort(reverse=True)
    todo = [fid for _, fid in candidates[:limit]]
    print(f"{len(candidates)} films still need details; doing {len(todo)} now.")

    done = fails_in_row = 0
    for fid in todo:
        film = db.get(Film, fid)
        title = film.title
        try:
            d = tmdb_get(session, f"/movie/{film.tmdb_id}", language="en-US",
                         append_to_response="credits,videos,external_ids",
                         include_video_language="en,te,hi,kn,null")
            imdb = clean_text(d.get("imdb_id")) or clean_text(d.get("external_ids", {}).get("imdb_id"))
            if imdb and db.scalar(select(Film.id).where(Film.imdb_id == imdb, Film.id != film.id)):
                imdb = None                              # imdb_id must be unique
            film.imdb_id = imdb
            film.runtime = d.get("runtime") or None
            film.trailer_url = pick_trailer(d.get("videos", {}))
            directors = [c["name"] for c in d["credits"].get("crew", []) if c.get("job") == "Director"]
            if directors:
                film.director = ", ".join(directors[:2])[:120]
            rebuild_crew(db, film, d["credits"])
            db.commit()
            done += 1
            fails_in_row = 0
            if done % 50 == 0:
                print(f"  {done} done...")
        except NETWORK_ERRORS as e:
            db.rollback()
            fails_in_row += 1
            print(f"FAILED {title}: {type(e).__name__}")
            if fails_in_row >= 5:
                print("Five failures in a row: stopping. Check the hotspot/WARP and run again.")
                break
        time.sleep(0.25)
    print(f"Details saved for {done} films. Run again for the next batch.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--language", default="te", choices=sorted(LANGUAGES), help="TMDB language code")
    p.add_argument("--from-year", type=int, default=FIRST_YEAR)
    p.add_argument("--to-year", type=int, default=date.today().year)
    p.add_argument("--min-votes", type=int, default=10, help="skip films with fewer TMDB votes")
    p.add_argument("--upcoming-pages", type=int, default=5, help="pages (20 films each) of upcoming films")
    p.add_argument("--dry-run", action="store_true", help="count only, write nothing")
    p.add_argument("--details", action="store_true", help="fill cast, director, trailer, imdb_id")
    p.add_argument("--details-limit", type=int, default=500)
    p.add_argument("--details-min-votes", type=int, default=50)
    p.add_argument("--ids", type=int, nargs="+", help="add specific films by TMDB id")
    args = p.parse_args()

    Base.metadata.create_all(bind=engine)
    session = make_session()
    try:
        tmdb_get(session, "/configuration")              # fail fast if TMDB is blocked or the token is wrong
    except NETWORK_ERRORS as e:
        raise SystemExit(f"Can't use TMDB ({type(e).__name__}: {e}). "
                         "Turn on the hotspot or WARP, check TMDB_API_KEY in .env, then retry.")

    today = date.today()
    with SessionLocal() as db:
        if args.ids:
            add_by_ids(session, db, args.ids, today, args.dry_run)
        elif args.details:
            if args.dry_run:
                print("--dry-run does not apply to --details; nothing done.")
            else:
                fill_details(session, db, args.details_limit, args.details_min_votes)
        else:
            discover_all(session, db, args, LANGUAGES[args.language], today)


if __name__ == "__main__":
    main()