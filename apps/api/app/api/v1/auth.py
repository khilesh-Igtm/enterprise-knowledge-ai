from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    create_token_pair,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def get_request_metadata(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent", "")[:512] or None

    # Do not trust arbitrary forwarded IP headers unless the
    # application is behind a correctly configured trusted proxy.
    ip_address = (
        request.client.host
        if request.client
        else None
    )

    return user_agent, ip_address


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await register_user(
        db=db,
        email=str(payload.email),
        password=payload.password,
    )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(
        db=db,
        email=str(payload.email),
        password=payload.password,
    )

    user_agent, ip_address = get_request_metadata(request)

    return await create_token_pair(
        db=db,
        user=user,
        user_agent=user_agent,
        ip_address=ip_address,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_agent, ip_address = get_request_metadata(request)

    return await rotate_refresh_token(
        db=db,
        raw_token=payload.refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
)
async def logout(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    await revoke_refresh_token(
        db=db,
        raw_token=payload.refresh_token,
    )

    return {"message": "Successfully logged out"}


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user