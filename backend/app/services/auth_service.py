"""Registration and login: password hashing/verification, issuing access tokens."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import users as users_repo


class EmailAlreadyRegisteredError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


async def register(db: AsyncSession, *, email: str, password: str) -> User:
    if await users_repo.get_by_email(db, email) is not None:
        raise EmailAlreadyRegisteredError(email)
    user = await users_repo.create(db, email=email, password_hash=hash_password(password))
    await db.commit()
    return user


async def authenticate(db: AsyncSession, *, email: str, password: str) -> User:
    user = await users_repo.get_by_email(db, email)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    return user


def issue_token(user: User) -> str:
    return create_access_token(user.id)
