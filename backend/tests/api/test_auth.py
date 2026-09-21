import pytest
from app.models.user import User
from httpx import AsyncClient

_VALID_PASSWORD = "a-reasonably-long-password"  # noqa: S105 - test fixture, not a real credential


@pytest.mark.asyncio
async def test_register_then_login_round_trips(client: AsyncClient) -> None:
    register = await client.post(
        "/api/v1/auth/register", json={"email": "new@example.com", "password": _VALID_PASSWORD}
    )
    assert register.status_code == 201
    assert register.json()["email"] == "new@example.com"
    assert "password" not in register.json()
    assert "password_hash" not in register.json()

    login = await client.post(
        "/api/v1/auth/login", json={"email": "new@example.com", "password": _VALID_PASSWORD}
    )
    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer"  # noqa: S105 - asserting the OAuth2 token type, not a credential
    assert len(body["access_token"]) > 20


@pytest.mark.asyncio
async def test_duplicate_registration_is_rejected(client: AsyncClient) -> None:
    payload = {"email": "dupe@example.com", "password": _VALID_PASSWORD}
    first = await client.post("/api/v1/auth/register", json=payload)
    second = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_login_with_wrong_password_is_rejected(
    client: AsyncClient, existing_user: User
) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": existing_user.email, "password": "totally wrong"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_unknown_email_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": _VALID_PASSWORD}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_short_password_is_rejected_by_validation(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={"email": "short@example.com", "password": "short"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_protected_endpoint_without_token_is_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/analyses")
    assert response.status_code in (401, 403)  # HTTPBearer returns 403 when the header is absent


@pytest.mark.asyncio
async def test_protected_endpoint_with_garbage_token_is_401(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/analyses", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401
