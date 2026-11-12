import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    get_refresh_token_expiry,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User:
    existing_user = await db.scalar(select(User).where(User.email == email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=email,
        hashed_password=hash_password(password),
    )

    db.add(user)

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        ) from e

    await db.refresh(user)

    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User:
    user = await db.scalar(select(User).where(User.email == email))

    if not user or not verify_password(
        password,
        user.hashed_password,
    ):
        raise _unauthorized()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive",
        )

    return user


async def create_token_pair(
    db: AsyncSession,
    user: User,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict:
    access_token = create_access_token(user.id)

    refresh_token = generate_refresh_token()

    token_record = RefreshToken(
        user_id=user.id,
        family_id=uuid.uuid4(),
        token_hash=hash_refresh_token(refresh_token),
        expires_at=get_refresh_token_expiry(),
        user_agent=user_agent,
        ip_address=ip_address,
    )

    db.add(token_record)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


async def rotate_refresh_token(
    db: AsyncSession,
    raw_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict:
    token_hash = hash_refresh_token(raw_token)

    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    stored_token = result.scalar_one_or_none()

    if stored_token is None:
        raise _unauthorized()

    now = datetime.now(UTC)

    # Detect reuse of a previously revoked token.
    if stored_token.revoked_at is not None:
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == stored_token.family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await db.commit()
        raise _unauthorized()

    expires_at = stored_token.expires_at

    # Handle timezone-naive values defensively.
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at <= now:
        stored_token.revoked_at = now
        await db.commit()
        raise _unauthorized()

    user = await db.get(User, stored_token.user_id)

    if user is None or not user.is_active:
        stored_token.revoked_at = now
        await db.commit()
        raise _unauthorized()

    new_refresh_token = generate_refresh_token()
    new_refresh_hash = hash_refresh_token(new_refresh_token)

    stored_token.revoked_at = now
    stored_token.replaced_by_token_hash = new_refresh_hash

    new_record = RefreshToken(
        user_id=user.id,
        family_id=stored_token.family_id,
        token_hash=new_refresh_hash,
        expires_at=get_refresh_token_expiry(),
        user_agent=user_agent,
        ip_address=ip_address,
    )

    db.add(new_record)

    access_token = create_access_token(user.id)

    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


async def revoke_refresh_token(
    db: AsyncSession,
    raw_token: str,
) -> None:
    token_hash = hash_refresh_token(raw_token)

    token = await db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    if token and token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)
        await db.commit()
