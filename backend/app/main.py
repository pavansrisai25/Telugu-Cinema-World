"""FastAPI entry point. More endpoints are added in Phase 3."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401  (registers the tables)

# Create tables if they don't exist yet (Alembic migrations can come later).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Telugu Cinema to the World API", version="0.1.0")

# Allow the React dev server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Used by the AWS load balancer to check the API is alive."""
    return {"status": "ok"}