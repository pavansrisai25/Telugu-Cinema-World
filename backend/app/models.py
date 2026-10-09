"""Database tables (SQLAlchemy 2.0 style).

Money rule: every amount is stored in Rs crore (`*_cr`).
Missing values are NULL (None) and shown in the UI as "Not available".
"""
from datetime import date
from typing import Optional

from sqlalchemy import (
    CheckConstraint, Date, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Film(Base):
    __tablename__ = "films"
    # Same title + release date = same film (makes seeding repeatable).
    __table_args__ = (UniqueConstraint("title", "release_date", name="uq_film"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tmdb_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    language: Mapped[str] = mapped_column(String(30), index=True)
    release_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="released")  # released | upcoming
    director: Mapped[Optional[str]] = mapped_column(String(120))

    # Budget (reported). Provenance columns satisfy the "Reported" rule.
    budget_cr: Mapped[Optional[float]] = mapped_column(Float)
    budget_original_amount: Mapped[Optional[float]] = mapped_column(Float)
    budget_original_currency: Mapped[Optional[str]] = mapped_column(String(10))
    budget_note: Mapped[Optional[str]] = mapped_column(Text)  # conversion note
    budget_source_name: Mapped[Optional[str]] = mapped_column(String(100))
    budget_source_url: Mapped[Optional[str]] = mapped_column(Text)
    budget_fetched_on: Mapped[Optional[date]] = mapped_column(Date)

    runtime: Mapped[Optional[int]] = mapped_column(Integer)  # minutes
    overview: Mapped[Optional[str]] = mapped_column(Text)
    poster_url: Mapped[Optional[str]] = mapped_column(Text)
    backdrop_url: Mapped[Optional[str]] = mapped_column(Text)
    trailer_url: Mapped[Optional[str]] = mapped_column(Text)

    crew: Mapped[list["FilmCrew"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    collections: Mapped[list["Collection"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    ratings: Mapped[list["Rating"]] = relationship(back_populates="film", cascade="all, delete-orphan")
    links: Mapped[list["FilmLink"]] = relationship(back_populates="film", cascade="all, delete-orphan")


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True)
    tmdb_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    photo_url: Mapped[Optional[str]] = mapped_column(Text)
    known_for: Mapped[Optional[str]] = mapped_column(String(100))

    credits: Mapped[list["FilmCrew"]] = relationship(back_populates="person")


class FilmCrew(Base):
    """Links a person to a film with a role (the base for the network graph)."""
    __tablename__ = "film_crew"
    __table_args__ = (
        CheckConstraint(
            "role IN ('hero','heroine','villain','director','music',"
            "'cinematographer','producer')",
            name="ck_crew_role",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id"), index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), index=True)
    role: Mapped[str] = mapped_column(String(30))
    character_name: Mapped[Optional[str]] = mapped_column(String(150))

    film: Mapped[Film] = relationship(back_populates="crew")
    person: Mapped[Person] = relationship(back_populates="credits")


class Collection(Base):
    """One box-office figure for one market. Always labelled 'Reported'."""
    __tablename__ = "collections"
    __table_args__ = (
        CheckConstraint(
            "market IN ('india_net','hindi_belt','overseas','worldwide')",
            name="ck_collection_market",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id"), index=True)
    market: Mapped[str] = mapped_column(String(20))
    amount_cr: Mapped[float] = mapped_column(Float)
    original_amount: Mapped[Optional[float]] = mapped_column(Float)
    original_currency: Mapped[Optional[str]] = mapped_column(String(10))
    conversion_note: Mapped[Optional[str]] = mapped_column(Text)
    label: Mapped[str] = mapped_column(String(20), default="Reported")
    source_name: Mapped[str] = mapped_column(String(100))   # required
    source_url: Mapped[str] = mapped_column(Text)           # required
    fetched_on: Mapped[date] = mapped_column(Date)          # required

    film: Mapped[Film] = relationship(back_populates="collections")


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        CheckConstraint("source IN ('tmdb','imdb')", name="ck_rating_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id"), index=True)
    source: Mapped[str] = mapped_column(String(10))
    score: Mapped[float] = mapped_column(Float)
    vote_count: Mapped[Optional[int]] = mapped_column(Integer)
    fetched_on: Mapped[date] = mapped_column(Date)

    film: Mapped[Film] = relationship(back_populates="ratings")


class FilmLink(Base):
    """Optional link-out to BookMyShow / District. Link only, no scraping."""
    __tablename__ = "film_links"
    __table_args__ = (
        CheckConstraint("site IN ('bookmyshow','district')", name="ck_link_site"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    film_id: Mapped[int] = mapped_column(ForeignKey("films.id"), index=True)
    site: Mapped[str] = mapped_column(String(20))
    url: Mapped[Optional[str]] = mapped_column(Text)

    film: Mapped[Film] = relationship(back_populates="links")