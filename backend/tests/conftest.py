"""Shared test setup: a small in-memory database with known numbers."""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Collection, Film, FilmCrew, Person, Rating


def add_collection(film, market, amount_cr, fetched, source="Test Source"):
    film.collections.append(Collection(
        market=market, amount_cr=amount_cr, source_name=source,
        source_url="https://example.com/" + source.replace(" ", "-"), fetched_on=fetched))


def seed(db):
    alpha = Film(title="Alpha", language="Telugu", release_date=date(2015, 7, 10), status="released",
                 director="Dir One", budget_cr=100, budget_source_name="Budget Src",
                 budget_source_url="https://example.com/b", budget_fetched_on=date(2026, 10, 1))
    beta = Film(title="Beta", language="Telugu", release_date=date(2017, 4, 28), status="released",
                budget_cr=200, budget_cr_max=250, budget_source_name="Budget Src",
                budget_source_url="https://example.com/b", budget_fetched_on=date(2026, 10, 1))
    gamma = Film(title="Gamma: The Film", language="Hindi", release_date=date(2023, 1, 25),
                 status="released", budget_cr=300, budget_source_name="Budget Src",
                 budget_source_url="https://example.com/b", budget_fetched_on=date(2026, 10, 1))
    delta = Film(title="Delta", language="Telugu", release_date=date(2022, 3, 25), status="released")
    varanasi = Film(title="Varanasi", language="Telugu", release_date=date(2027, 4, 7),
                    status="upcoming", budget_cr=1000, budget_cr_max=1400,
                    budget_source_name="Budget Src", budget_source_url="https://example.com/b",
                    budget_fetched_on=date(2026, 10, 1))
    db.add_all([alpha, beta, gamma, delta, varanasi])

    add_collection(alpha, "worldwide", 600, date(2026, 10, 1))
    add_collection(alpha, "india_net", 400, date(2026, 10, 1))
    add_collection(alpha, "hindi_belt", 100, date(2026, 10, 1))
    add_collection(alpha, "overseas", 120, date(2026, 10, 1))
    # Two sources for Beta: the newer fetch (1800) must win.
    add_collection(beta, "worldwide", 1500, date(2026, 10, 1), source="Old Source")
    add_collection(beta, "worldwide", 1800, date(2026, 10, 20), source="New Source")
    add_collection(gamma, "worldwide", 1000, date(2026, 10, 1))

    alpha.ratings.append(Rating(source="tmdb", score=8.0, vote_count=100, fetched_on=date(2026, 10, 1)))
    alpha.ratings.append(Rating(source="imdb", score=8.1, vote_count=200, fetched_on=date(2026, 10, 1)))

    dir1, hero1 = Person(name="Dir One", tmdb_id=1), Person(name="Hero One", tmdb_id=2)
    music1, hero2 = Person(name="Music One", tmdb_id=3), Person(name="Hero Two", tmdb_id=4)
    db.add_all([dir1, hero1, music1, hero2])

    for film, person, role in [
        (alpha, dir1, "director"), (alpha, hero1, "hero"), (alpha, music1, "music"),
        (beta, dir1, "director"), (beta, hero1, "hero"),
        (delta, dir1, "director"), (gamma, hero2, "hero"),
    ]:
        film.crew.append(FilmCrew(person=person, role=role))
    db.commit()


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with sessionmaker(bind=engine, autoflush=False)() as session:
        seed(session)
        yield session
    engine.dispose()


@pytest.fixture()
def ids(db_session):
    return {f.title: f.id for f in db_session.scalars(select(Film))}


@pytest.fixture()
def person_ids(db_session):
    return {p.name: p.id for p in db_session.scalars(select(Person))}


@pytest.fixture()
def client(db_session):
    def override():
        yield db_session
    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()