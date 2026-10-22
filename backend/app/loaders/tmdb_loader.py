"""TMDB loader: details, images, trailer, cast/crew and the TMDB rating.

Run from the backend folder:   python -m app.loaders.tmdb_loader
Safe to re-run: existing rows are updated, not duplicated.
Budget is NOT loaded here (TMDB budgets are USD and unreliable); use csv_import.
"""
import sys
import time

import requests
from sqlalchemy import select

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.loaders.cleaning import clean_text, norm_key
from app.loaders.db_helpers import upsert_rating
from app.models import Film, FilmCrew, Person

API = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p"
LANG_CODE = {"Telugu": "te", "Hindi": "hi", "Kannada": "kn"}

# TMDB job name -> our role
CREW_JOBS = {
    "Director": "director",
    "Original Music Composer": "music",
    "Music": "music",
    "Director of Photography": "cinematographer",
    "Producer": "producer",
}
# Max people kept per role per film (keeps the network graph readable)
ROLE_LIMIT = {"director": 2, "music": 2, "cinematographer": 1,
              "producer": 3, "hero": 1, "heroine": 1}


def make_session():
    token = settings.tmdb_api_key
    if not token:
        raise SystemExit("TMDB_API_KEY is empty. Put your Read Access Token in backend/.env")
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "accept": "application/json"})
    return session


def tmdb_get(session, path, **params):
    """GET with one retry on rate limit. Error messages never contain the token."""
    for _ in range(2):
        r = session.get(f"{API}{path}", params=params, timeout=20)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", "2")))
            continue
        if r.status_code != 200:
            raise RuntimeError(f"TMDB returned status {r.status_code} for {path}")
        return r.json()
    raise RuntimeError(f"TMDB rate limit hit for {path}")


def search_queries(title):
    """Try the full title first, then the part before ':' or ' - '."""
    yield title
    for sep in (":", " - "):
        if sep in title:
            yield title.split(sep)[0].strip()


def find_match(session, film):
    """Best TMDB search hit. Needs a matching release date or language;
    otherwise returns None (we never guess)."""
    want_lang = LANG_CODE.get(film.language)
    want_date = str(film.release_date)

    def rank(m):
        points = 4 * (m.get("release_date") == want_date) + 2 * (m.get("original_language") == want_lang)
        return (points, m.get("popularity", 0))

    for query in search_queries(film.title):
        results = tmdb_get(session, "/search/movie", query=query,
                           year=film.release_date.year, include_adult="false").get("results", [])
        ranked = sorted(results, key=rank, reverse=True)
        if ranked and rank(ranked[0])[0] >= 2:
            return ranked[0]
    return None


def pick_trailer(videos):
    youtube = [v for v in videos.get("results", [])
               if v.get("site") == "YouTube" and v.get("type") == "Trailer"]
    if not youtube:
        return None
    best = ([v for v in youtube if v.get("official")] or youtube)[0]
    return f"https://www.youtube.com/watch?v={best['key']}"


def upsert_person(db, c):
    person = db.scalar(select(Person).where(Person.tmdb_id == c["id"]))
    if person is None:
        person = Person(tmdb_id=c["id"], name=c["name"])
        db.add(person)
    person.name = c["name"]
    person.photo_url = f"{IMG}/w185{c['profile_path']}" if c.get("profile_path") else None
    person.known_for = clean_text(c.get("known_for_department"))
    db.flush()  # autoflush is off, so flush to make the person findable
    return person


def rebuild_crew(db, film, credits):
    film.crew.clear()
    db.flush()
    seen, counts = set(), {}

    def add(c, role, character=None):
        if (c["id"], role) in seen or counts.get(role, 0) >= ROLE_LIMIT[role]:
            return
        seen.add((c["id"], role))
        counts[role] = counts.get(role, 0) + 1
        film.crew.append(FilmCrew(person=upsert_person(db, c), role=role,
                                  character_name=clean_text(character)))

    # Heuristic: first male / first female in the top-10 billing = hero / heroine.
    cast = sorted(credits.get("cast", []), key=lambda c: c.get("order", 999))[:10]
    for c in cast:
        if c.get("gender") == 2:
            add(c, "hero", c.get("character"))
        elif c.get("gender") == 1:
            add(c, "heroine", c.get("character"))
    for c in credits.get("crew", []):
        role = CREW_JOBS.get(c.get("job"))
        if role:
            add(c, role)
    return counts


def load_one(session, db, film, warnings):
    match = find_match(session, film)
    if match is None:
        warnings.append(f"{film.title}: not found on TMDB (left unchanged)")
        return None
    clash = db.scalar(select(Film).where(Film.tmdb_id == match["id"], Film.id != film.id))
    if clash:
        warnings.append(f"{film.title}: TMDB id {match['id']} is already used by '{clash.title}'")
        return None

    d = tmdb_get(session, f"/movie/{match['id']}", language="en-US",
                 append_to_response="credits,videos,external_ids",
                 include_video_language="en,te,hi,kn,null")

    # Verify the Phase 1 seed against TMDB (warn only, never overwrite)
    if d.get("release_date") and d["release_date"] != str(film.release_date):
        warnings.append(f"{film.title}: TMDB release date {d['release_date']} vs seed {film.release_date}")
    if d.get("original_language") != LANG_CODE.get(film.language):
        warnings.append(f"{film.title}: TMDB language '{d.get('original_language')}' vs seed '{film.language}'")
    directors = [c["name"] for c in d["credits"].get("crew", []) if c.get("job") == "Director"]
    if film.director and directors and norm_key(film.director) not in [norm_key(x) for x in directors]:
        warnings.append(f"{film.title}: seed director '{film.director}' vs TMDB {directors}")

    film.tmdb_id = d["id"]
    film.imdb_id = clean_text(d.get("imdb_id")) or clean_text(d.get("external_ids", {}).get("imdb_id"))
    film.runtime = d.get("runtime") or None
    film.overview = clean_text(d.get("overview"))
    film.poster_url = f"{IMG}/w500{d['poster_path']}" if d.get("poster_path") else None
    film.backdrop_url = f"{IMG}/w1280{d['backdrop_path']}" if d.get("backdrop_path") else None
    film.trailer_url = pick_trailer(d.get("videos", {}))

    if d.get("vote_count"):  # skip films with zero votes (e.g. unreleased)
        upsert_rating(db, film.id, "tmdb", d["vote_average"], d["vote_count"])

    return rebuild_crew(db, film, d["credits"]), d


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # safe printing of names on Windows
    Base.metadata.create_all(bind=engine)
    session = make_session()
    warnings = []

    with SessionLocal() as db:
        for film in db.scalars(select(Film).order_by(Film.release_date)).all():
            title = film.title
            try:
                result = load_one(session, db, film, warnings)
                db.commit()
            except (RuntimeError, requests.RequestException) as e:
                db.rollback()
                warnings.append(f"{title}: {e}")
                result = None
            if result:
                counts, d = result
                picked = ", ".join(
                    f"{p.role}={p.person.name}" for p in film.crew if p.role in ("hero", "heroine")
                )
                print(f"OK   {title:<32} TMDB {d['id']}  | {picked}")
            else:
                print(f"SKIP {title}")
            time.sleep(0.3)  # be polite to the API

    if warnings:
        print("\nPLEASE REVIEW:")
        for w in warnings:
            print(" -", w)


if __name__ == "__main__":
    main()