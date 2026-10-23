"""Analytics endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import services
from app.database import get_db

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics/overview")
def overview(db: Session = Depends(get_db)):
    return services.overview(services.load_all_films(db))


@router.get("/analytics/language-share")
def language_share(db: Session = Depends(get_db)):
    return services.language_share(services.load_all_films(db))


@router.get("/analytics/pan-india")
def pan_india(language: str = Query("Telugu", max_length=30), db: Session = Depends(get_db)):
    return services.pan_india(services.load_all_films(db), language)


@router.get("/analytics/budget-vs-collection")
def budget_vs_collection(db: Session = Depends(get_db)):
    return services.budget_vs_collection(services.load_all_films(db))


@router.get("/compare")
def compare(a: int, b: int, db: Session = Depends(get_db)):
    """Duel mode: two films side by side."""
    if a == b:
        raise HTTPException(status_code=400, detail="Pick two different films")
    film_a, film_b = services.load_film(db, a), services.load_film(db, b)
    if film_a is None or film_b is None:
        raise HTTPException(status_code=404, detail="One or both films not found")
    return {"a": services.compare_card(film_a), "b": services.compare_card(film_b)}