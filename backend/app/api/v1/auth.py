from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.core.config import get_settings
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: DbSession) -> UserOut:
    try:
        user = await auth_service.register(db, email=payload.email, password=payload.password)
    except auth_service.EmailAlreadyRegisteredError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email is already registered") from error
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    try:
        user = await auth_service.authenticate(db, email=payload.email, password=payload.password)
    except auth_service.InvalidCredentialsError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password") from error
    token = auth_service.issue_token(user)
    return TokenResponse(
        access_token=token, expires_in_minutes=get_settings().jwt_access_ttl_minutes
    )
