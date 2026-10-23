"""Response shapes (Pydantic). These also drive the /docs page."""
from datetime import date
from typing import Optional

from pydantic import BaseModel


class Sourced(BaseModel):
    """A money figure with its provenance. label is 'Reported' or 'Not available'."""
    amount_cr: Optional[float] = None
    amount_max_cr: Optional[float] = None  # only when a range is reported
    label: str = "Not available"
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    fetched_on: Optional[date] = None
    note: Optional[str] = None


class FilmSummary(BaseModel):
    id: int
    title: str
    language: str
    release_date: Optional[date] = None
    status: str
    director: Optional[str] = None
    poster_url: Optional[str] = None


class SimilarFilm(FilmSummary):
    reason: str


class CollectionOut(BaseModel):
    market: str
    amount_cr: float
    label: str
    source_name: str
    source_url: str
    fetched_on: date
    conversion_note: Optional[str] = None


class CrewOut(BaseModel):
    person_id: int
    name: str
    photo_url: Optional[str] = None
    role: str
    character_name: Optional[str] = None


class RatingOut(BaseModel):
    source: str
    score: float
    vote_count: Optional[int] = None
    fetched_on: date


class LinkOut(BaseModel):
    site: str
    url: Optional[str] = None


class FilmDetail(FilmSummary):
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    runtime: Optional[int] = None
    overview: Optional[str] = None
    backdrop_url: Optional[str] = None
    trailer_url: Optional[str] = None
    budget: Sourced
    worldwide: Sourced
    roi: Optional[float] = None      # worldwide / budget_cr
    roi_min: Optional[float] = None  # worldwide / budget_cr_max (only if a range exists)
    collections: list[CollectionOut]
    ratings: list[RatingOut]
    crew: list[CrewOut]
    similar: list[SimilarFilm]
    links: list[LinkOut]


class CreditOut(BaseModel):
    film: FilmSummary
    role: str
    character_name: Optional[str] = None
    budget_cr: Optional[float] = None
    worldwide_cr: Optional[float] = None
    roi: Optional[float] = None


class PersonDetail(BaseModel):
    id: int
    name: str
    photo_url: Optional[str] = None
    known_for: Optional[str] = None
    stats: dict
    filmography: list[CreditOut]