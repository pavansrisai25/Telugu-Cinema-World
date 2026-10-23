"""Search, film page and person page."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.schemas import FilmDetail, FilmSummary, PersonDetail

router = APIRouter(prefix="/api", tags=["films"])


@router.get("/search", response_model=list[FilmSummary])
def search(q: str = Query(..., min_length=1, max_length=100),
           limit: int = Query(10, ge=1, le=25),
           db: Session = Depends(get_db)):
    """Autocomplete for the search box."""
    return services.search_films(db, q, limit)


@router.get("/films/{film_id}", response_model=FilmDetail)
def get_film(film_id: int, db: Session = Depends(get_db)):
    film = services.load_film(db, film_id)
    if film is None:
        raise HTTPException(status_code=404, detail="Film not found")
    return services.film_detail(db, film)


@router.get("/people/{person_id}", response_model=PersonDetail)
def get_person(person_id: int, db: Session = Depends(get_db)):
    person = services.person_detail(db, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return person