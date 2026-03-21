from contextlib import closing

from fastapi import FastAPI

from app.db.database import get_connection
from app.settings import DB_PATH


app = FastAPI(
    title="Weather Map API",
    version="0.1.0",
    description="중기예보 지도 앱용 FastAPI 백엔드 초기 스캐폴드",
)


@app.on_event("startup")
def startup() -> None:
    with closing(get_connection()) as connection:
        connection.execute("SELECT 1")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "database": str(DB_PATH),
    }
