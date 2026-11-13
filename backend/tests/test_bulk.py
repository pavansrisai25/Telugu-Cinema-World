"""Tests for the bulk loader's save logic (no network)."""
from datetime import date

from sqlalchemy import func, select

from app.loaders.tmdb_bulk import status_for, store_item
from app.models import Film

TODAY = date(2026, 11, 13)


def item(tid, title="New Film", release="2024-09-27", votes=100):
    return {"id": tid, "title": title, "release_date": release, "overview": "Plot",
            "poster_path": "/p.jpg", "backdrop_path": None,
            "vote_average": 7.5, "vote_count": votes}


def count(db):
    return db.scalar(select(func.count(Film.id)))


def state(db):
    return {}, {(f.title, f.release_date) for f in db.scalars(select(Film))}


def test_adds_then_updates(db_session):
    by_tmdb, seen = state(db_session)
    assert store_item(db_session, item(1), "Telugu", TODAY, by_tmdb, seen, False) == "added"
    db_session.commit()
    film = db_session.scalar(select(Film).where(Film.tmdb_id == 1))
    assert (film.status, film.language) == ("released", "Telugu")
    assert film.poster_url.endswith("/w500/p.jpg") and film.backdrop_url is None
    assert [r.source for r in film.ratings] == ["tmdb"]
    before = count(db_session)
    assert store_item(db_session, item(1), "Telugu", TODAY, by_tmdb, seen, False) == "updated"
    assert count(db_session) == before


def test_skips_same_title_and_date(db_session):
    by_tmdb, seen = state(db_session)
    clash = item(2, title="Alpha", release="2015-07-10")   # Alpha exists in the test data
    assert store_item(db_session, clash, "Telugu", TODAY, by_tmdb, seen, False) == "skipped"


def test_upcoming_status(db_session):
    assert status_for(date(2026, 11, 14), TODAY) == "upcoming"
    assert status_for(TODAY, TODAY) == "released"
    by_tmdb, seen = state(db_session)
    store_item(db_session, item(3, release="2027-04-07"), "Telugu", TODAY, by_tmdb, seen, False)
    assert db_session.scalar(select(Film).where(Film.tmdb_id == 3)).status == "upcoming"


def test_skips_missing_or_bad_dates(db_session):
    by_tmdb, seen = state(db_session)
    for rd in (None, "", "not-a-date"):
        assert store_item(db_session, item(4, release=rd), "Telugu", TODAY, by_tmdb, seen, False) == "skipped"


def test_no_rating_without_votes(db_session):
    by_tmdb, seen = state(db_session)
    store_item(db_session, item(5, votes=0), "Telugu", TODAY, by_tmdb, seen, False)
    db_session.commit()
    assert db_session.scalar(select(Film).where(Film.tmdb_id == 5)).ratings == []


def test_dry_run_writes_nothing(db_session):
    before = count(db_session)
    by_tmdb, seen = state(db_session)
    assert store_item(db_session, item(6), "Telugu", TODAY, by_tmdb, seen, True) == "added"
    assert count(db_session) == before
    assert store_item(db_session, item(6), "Telugu", TODAY, by_tmdb, seen, True) == "updated"