import uuid

from httpx import AsyncClient


def unique_email() -> str:
    return f"frontend_{uuid.uuid4().hex[:8]}@example.com"


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------


async def test_static_css_is_served(client: AsyncClient) -> None:
    response = await client.get("/static/css/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


async def test_static_main_js_is_served(client: AsyncClient) -> None:
    response = await client.get("/static/js/main.js")
    assert response.status_code == 200


async def test_static_auth_js_is_served(client: AsyncClient) -> None:
    response = await client.get("/static/js/auth.js")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET / redirect logic
# ---------------------------------------------------------------------------


async def test_index_redirects_to_login_when_no_cookie(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/login"


async def test_index_redirects_to_dashboard_when_authenticated(client: AsyncClient) -> None:
    email = unique_email()
    await client.post("/auth/register", json={"email": email, "password": "password123"})
    await client.post("/auth/login", json={"email": email, "password": "password123"})

    response = await client.get("/")

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/dashboard"


# ---------------------------------------------------------------------------
# Login / register pages
# ---------------------------------------------------------------------------


async def test_login_page_returns_200_with_form(client: AsyncClient) -> None:
    response = await client.get("/login")
    assert response.status_code == 200
    assert 'id="login-form"' in response.text
    assert 'id="login-error"' in response.text


async def test_register_page_returns_200_with_form(client: AsyncClient) -> None:
    response = await client.get("/register")
    assert response.status_code == 200
    assert 'id="register-form"' in response.text
    assert 'id="register-error"' in response.text
