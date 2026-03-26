from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user
from app.repositories.users import authenticate_user, create_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security import create_access_token


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> TokenResponse:
    user = create_user(payload)
    token = create_access_token(str(user["id"]))
    return TokenResponse(access_token=token, user=UserResponse(**user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    user = authenticate_user(payload.email, payload.password)
    token = create_access_token(str(user["id"]))
    return TokenResponse(access_token=token, user=UserResponse(**user))


@router.get("/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(**current_user)
