import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_password_hashing():
    password = "MyStrongPassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword123!", hashed)


def test_refresh_token_generation():
    token = generate_refresh_token()

    assert len(token) > 32
    assert token != generate_refresh_token()


def test_refresh_token_hashing():
    token = generate_refresh_token()

    hashed = hash_refresh_token(token)

    assert len(hashed) == 64
    assert hashed == hash_refresh_token(token)
    assert hashed != token


def test_access_token_creation():
    import uuid

    user_id = uuid.uuid4()

    token = create_access_token(user_id)

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
    )

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"