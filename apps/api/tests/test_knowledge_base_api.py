import pytest

BASE_URL = "/api/v1"


async def register_and_login(client, email: str):
    await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
        },
    )

    response = await client.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_user_cannot_access_another_users_knowledge_base(client):
    token_a = await register_and_login(
        client,
        "alice@example.com",
    )

    token_b = await register_and_login(
        client,
        "bob@example.com",
    )

    headers_a = {
        "Authorization": f"Bearer {token_a}",
    }

    headers_b = {
        "Authorization": f"Bearer {token_b}",
    }

    # User A creates a knowledge base.
    create_response = await client.post(
        f"{BASE_URL}/knowledge-bases",
        headers=headers_a,
        json={
            "name": "Alice Private Documents",
            "description": "Private knowledge base",
        },
    )

    assert create_response.status_code == 201

    knowledge_base_id = create_response.json()["id"]

    # User A can access it.
    owner_response = await client.get(
        f"{BASE_URL}/knowledge-bases/{knowledge_base_id}",
        headers=headers_a,
    )

    assert owner_response.status_code == 200

    # User B sees no knowledge bases.
    list_response = await client.get(
        f"{BASE_URL}/knowledge-bases",
        headers=headers_b,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []

    # User B cannot access Alice's knowledge base.
    foreign_response = await client.get(
        f"{BASE_URL}/knowledge-bases/{knowledge_base_id}",
        headers=headers_b,
    )

    assert foreign_response.status_code == 404


@pytest.mark.asyncio
async def test_knowledge_base_requires_authentication(client):
    response = await client.get(
        f"{BASE_URL}/knowledge-bases",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_knowledge_base_uuid_returns_404(client):
    token = await register_and_login(
        client,
        "alice@example.com",
    )

    response = await client.get(
        f"{BASE_URL}/knowledge-bases/not-a-valid-uuid",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404