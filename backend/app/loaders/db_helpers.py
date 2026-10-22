"""Small database helpers shared by the loaders."""
from datetime import date

from sqlalchemy import select

from app.models import Rating


def upsert_rating(db, film_id, source, score, vote_count):
    """Create or update one rating row per (film, source)."""
    rating = db.scalar(
        select(Rating).where(Rating.film_id == film_id, Rating.source == source)
    )
    if rating is None:
        rating = Rating(film_id=film_id, source=source)
        db.add(rating)
    rating.score = score
    rating.vote_count = vote_count
    rating.fetched_on = date.today()