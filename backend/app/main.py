from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.toilets import router as toilet_router
from app.repositories.toilets import count_toilets, initialize_database
from app.services.importer import seed_database_if_empty
from app.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    seed_database_if_empty()
    yield


app = FastAPI(
    title="Public Toilet Map API",
    version="0.3.0",
    description="공중화장실 정보를 조회하고 JWT 인증을 제공하는 FastAPI 백엔드",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(toilet_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Public Toilet Map API",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, int | str]:
    return {
        "status": "ok",
        "database": str(settings.db_path),
        "toilet_count": count_toilets(),
    }
