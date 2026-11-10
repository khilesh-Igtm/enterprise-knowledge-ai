import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: AsyncSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={
                "require": ["exp", "iat", "sub", "iss", "type"],
            },
        )

        if payload.get("type") != "access":
            raise unauthorized

        user_id = uuid.UUID(payload["sub"])

    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise unauthorized

    user = await db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None or not user.is_active:
        raise unauthorized

    return user