import sqlite3

from fastapi import HTTPException, status

from app.db.database import get_connection
from app.schemas.auth import RegisterRequest
from app.security import hash_password, verify_password


def _row_to_user(row: sqlite3.Row) -> dict:
    payload = dict(row)
    payload["is_active"] = bool(payload["is_active"])
    return payload


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, email, name, is_active, created_at, updated_at, password_hash
            FROM users
            WHERE email = ?
            """,
            (email.lower(),),
        ).fetchone()
        return _row_to_user(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, email, name, is_active, created_at, updated_at, password_hash
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        return _row_to_user(row) if row else None


def create_user(payload: RegisterRequest) -> dict:
    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다.",
        )

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (email, password_hash, name)
            VALUES (?, ?, ?)
            """,
            (
                payload.email.lower(),
                hash_password(payload.password),
                payload.name,
            ),
        )
        user_id = int(cursor.lastrowid)

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=500, detail="사용자 생성에 실패했습니다.")
    user.pop("password_hash", None)
    return user


def authenticate_user(email: str, password: str) -> dict:
    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다.",
        )
    user.pop("password_hash", None)
    return user
