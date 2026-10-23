"""Collaboration network and Varanasi Watch."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import services
from app.database import get_db

router = APIRouter(prefix="/api", tags=["extras"])

ALLOWED_ROLES = {"director", "hero", "heroine", "villain", "music", "cinematographer", "producer"}


@router.get("/network")
def network(roles: str = Query("director,hero,music"),
            min_weight: int = Query(1, ge=1, le=10),
            db: Session = Depends(get_db)):
    chosen = [r.strip() for r in roles.split(",") if r.strip()]
    if not chosen or not set(chosen) <= ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"roles must be from {sorted(ALLOWED_ROLES)}")
    return services.build_network(db, chosen, min_weight)


@router.get("/varanasi")
def varanasi(share_pct: float = Query(100.0, ge=1, le=100), db: Session = Depends(get_db)):
    """share_pct = the break-even slider (assumed producer share of gross)."""
    data = services.varanasi_watch(db, share_pct=share_pct)
    if data is None:
        raise HTTPException(status_code=404, detail="Varanasi is not in the database")
    return data