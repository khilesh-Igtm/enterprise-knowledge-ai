import pytest

BASE_URL = "/api/v1"


@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_duplicate_registration(client):
    payload = {
        "email": "alice@example.com",
        "password": "StrongPassword123!",
    }

    first = await client.post(
        f"{BASE_URL}/auth/register",
        json=payload,
    )

    second = await client.post(
        f"{BASE_URL}/auth/register",
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    response = await client.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    response = await client.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "alice@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_current_user(client):
    await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    login = await client.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    access_token = login.json()["access_token"]

    response = await client.get(
        f"{BASE_URL}/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_current_user_without_token(client):
    response = await client.get(
        f"{BASE_URL}/auth/me",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_current_user_with_invalid_token(client):
    response = await client.get(
        f"{BASE_URL}/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_token_cannot_be_used_as_refresh_token(client):
    await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    login = await client.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    access_token = login.json()["access_token"]

    response = await client.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_rotation(client):
    await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    login = await client.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    old_token = login.json()["refresh_token"]

    refresh = await client.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": old_token},
    )

    assert refresh.status_code == 200

    new_token = refresh.json()["refresh_token"]

    assert new_token != old_token

    # Reusing the old token should trigger family revocation.
    reuse = await client.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": old_token},
    )

    assert reuse.status_code == 401

    # The newly issued token from that compromised family
    # must also be rejected.
    second_attempt = await client.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": new_token},
    )

    assert second_attempt.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_families_are_isolated(client):
    await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    login_one = await client.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    login_two = await client.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    token_one = login_one.json()["refresh_token"]
    token_two = login_two.json()["refresh_token"]

    # Rotate the first session.
    rotated = await client.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": token_one},
    )

    assert rotated.status_code == 200

    # Reuse the old first-session token.
    reused = await client.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": token_one},
    )

    assert reused.status_code == 401

    # The second device/session should remain valid.
    second_session = await client.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": token_two},
    )

    assert second_session.status_code == 200


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client):
    await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    login = await client.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword123!",
        },
    )

    refresh_token = login.json()["refresh_token"]

    logout = await client.post(
        f"{BASE_URL}/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert logout.status_code == 200

    refresh = await client.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh.status_code == 401