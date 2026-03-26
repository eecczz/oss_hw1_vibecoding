import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.settings import DATA_DIR, settings


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def create_connection() -> sqlite3.Connection:
    ensure_data_dir()
    connection = sqlite3.connect(settings.db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = create_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
