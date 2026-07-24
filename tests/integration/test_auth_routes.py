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


async def test_login_sets_httponly_cookies(client: AsyncClient) -> None:
    email = unique_email()
    await client.post("/auth/register", json={"email": email, "password": "password123"})
    response = await client.post("/auth/login", json={"email": email, "password": "password123"})

    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    set_cookie_headers = response.headers.get_list("set-cookie")
    access_cookie = next(h for h in set_cookie_headers if h.startswith("access_token="))
    refresh_cookie = next(h for h in set_cookie_headers if h.startswith("refresh_token="))

    assert "httponly" in access_cookie.lower()
    assert "samesite=lax" in access_cookie.lower()
    assert "httponly" in refresh_cookie.lower()
    assert "path=/auth/refresh" in refresh_cookie.lower()


async def test_login_does_not_set_cookies_on_failure(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/login", json={"email": unique_email(), "password": "password123"}
    )
    assert "access_token" not in response.cookies


async def test_register_does_not_set_cookies(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register", json={"email": unique_email(), "password": "password123"}
    )
    assert "access_token" not in response.cookies


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


async def test_refresh_sets_new_cookies(client: AsyncClient) -> None:
    reg = await client.post(
        "/auth/register", json={"email": unique_email(), "password": "password123"}
    )
    refresh_token = reg.json()["refresh_token"]

    response = await client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


async def test_refresh_falls_back_to_cookie_when_no_body_token(client: AsyncClient) -> None:
    email = unique_email()
    await client.post("/auth/register", json={"email": email, "password": "password123"})
    # login stores the refresh_token cookie on the client's cookie jar
    await client.post("/auth/login", json={"email": email, "password": "password123"})

    # no refresh_token in the body — only the cookie set by login is available
    response = await client.post("/auth/refresh", json={})

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_refresh_with_no_token_anywhere_returns_401(client: AsyncClient) -> None:
    response = await client.post("/auth/refresh", json={})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


async def test_logout_returns_204(client: AsyncClient) -> None:
    response = await client.post("/auth/logout")
    assert response.status_code == 204


async def test_logout_clears_auth_cookies(client: AsyncClient) -> None:
    email = unique_email()
    await client.post("/auth/register", json={"email": email, "password": "password123"})
    await client.post("/auth/login", json={"email": email, "password": "password123"})

    response = await client.post("/auth/logout")

    set_cookie_headers = response.headers.get_list("set-cookie")
    access_cookie = next(h for h in set_cookie_headers if h.startswith("access_token="))
    refresh_cookie = next(h for h in set_cookie_headers if h.startswith("refresh_token="))
    assert 'access_token=""' in access_cookie or "access_token=;" in access_cookie
    assert 'refresh_token=""' in refresh_cookie or "refresh_token=;" in refresh_cookie


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
