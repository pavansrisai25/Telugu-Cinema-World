"""FastAPI entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registers the tables)
from app.config import settings
from app.database import Base, engine
from app.routers import analytics, extras, films


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if missing (Alembic migrations can come later).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Telugu Cinema to the World API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(films.router)
app.include_router(analytics.router)
app.include_router(extras.router)


@app.get("/api/health")
def health():
    """Used by the AWS load balancer to check the API is alive."""
    return {"status": "ok"}