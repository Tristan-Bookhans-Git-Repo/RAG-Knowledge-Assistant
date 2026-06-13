import asyncio
import uuid

from httpx import AsyncClient


def unique_email() -> str:
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


async def test_register_returns_201_with_tokens(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register", json={"email": unique_email(), "password": "password123"}
    )
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    email = unique_email()
    await client.post("/auth/register", json={"email": email, "password": "password123"})
    response = await client.post("/auth/register", json={"email": email, "password": "different"})
    assert response.status_code == 409


async def test_register_invalid_email_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register", json={"email": "not-an-email", "password": "password123"}
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def test_login_valid_credentials_returns_200_with_tokens(client: AsyncClient) -> None:
    email = unique_email()
    await client.post("/auth/register", json={"email": email, "password": "password123"})
    response = await client.post("/auth/login", json={"email": email, "password": "password123"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    email = unique_email()
    await client.post("/auth/register", json={"email": email, "password": "password123"})
    response = await client.post("/auth/login", json={"email": email, "password": "wrongpassword"})
    assert response.status_code == 401


async def test_login_unknown_email_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/login", json={"email": unique_email(), "password": "password123"}
    )
    assert response.status_code == 401


async def test_login_and_register_return_different_tokens(client: AsyncClient) -> None:
    email = unique_email()
    reg = await client.post("/auth/register", json={"email": email, "password": "password123"})
    await asyncio.sleep(1)
    login = await client.post("/auth/login", json={"email": email, "password": "password123"})
    assert reg.json()["access_token"] != login.json()["access_token"]


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


async def test_refresh_valid_token_returns_new_tokens(client: AsyncClient) -> None:
    reg = await client.post(
        "/auth/register", json={"email": unique_email(), "password": "password123"}
    )
    refresh_token = reg.json()["refresh_token"]
    response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_refresh_with_access_token_returns_401(client: AsyncClient) -> None:
    reg = await client.post(
        "/auth/register", json={"email": unique_email(), "password": "password123"}
    )
    access_token = reg.json()["access_token"]
    response = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


async def test_refresh_garbage_token_returns_401(client: AsyncClient) -> None:
    response = await client.post("/auth/refresh", json={"refresh_token": "not.a.valid.token"})
    assert response.status_code == 401


async def test_refresh_returns_different_tokens_than_original(client: AsyncClient) -> None:
    reg = await client.post(
        "/auth/register", json={"email": unique_email(), "password": "password123"}
    )
    original_access = reg.json()["access_token"]
    refresh_token = reg.json()["refresh_token"]
    await asyncio.sleep(1)
    refreshed = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.json()["access_token"] != original_access
    assert refreshed.json()["refresh_token"] != refresh_token


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


async def test_logout_returns_204(client: AsyncClient) -> None:
    response = await client.post("/auth/logout")
    assert response.status_code == 204


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


async def test_me_returns_user_info(client: AsyncClient) -> None:
    email = unique_email()
    reg = await client.post("/auth/register", json={"email": email, "password": "password123"})
    access_token = reg.json()["access_token"]
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == email
    assert "id" in body
    assert "created_at" in body
    assert "hashed_password" not in body


async def test_me_no_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_me_refresh_token_returns_401(client: AsyncClient) -> None:
    reg = await client.post(
        "/auth/register", json={"email": unique_email(), "password": "password123"}
    )
    refresh_token = reg.json()["refresh_token"]
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 401


async def test_me_tampered_token_returns_401(client: AsyncClient) -> None:
    reg = await client.post(
        "/auth/register", json={"email": unique_email(), "password": "password123"}
    )
    token = reg.json()["access_token"]
    tampered = token[:-4] + "xxxx"
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert response.status_code == 401


async def test_me_garbage_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert response.status_code == 401
