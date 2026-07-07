import io
import uuid

from fpdf import FPDF
from httpx import AsyncClient


def unique_email() -> str:
    return f"frontend_{uuid.uuid4().hex[:8]}@example.com"


def _make_pdf(content: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text=content)
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


async def _register_and_login(client: AsyncClient) -> str:
    email = unique_email()
    await client.post("/auth/register", json={"email": email, "password": "password123"})
    await client.post("/auth/login", json={"email": email, "password": "password123"})
    return email


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


# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------


async def test_dashboard_redirects_to_login_when_no_cookie(client: AsyncClient) -> None:
    response = await client.get("/dashboard")
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/login"


async def test_dashboard_returns_200_with_upload_form_when_authenticated(
    client: AsyncClient,
) -> None:
    await _register_and_login(client)

    response = await client.get("/dashboard")

    assert response.status_code == 200
    assert 'id="upload-form"' in response.text
    assert 'id="documents-table"' in response.text


async def test_dashboard_lists_uploaded_document(client: AsyncClient) -> None:
    await _register_and_login(client)
    await client.post(
        "/documents/upload",
        files={"file": ("notes.pdf", _make_pdf("dashboard test content"), "application/pdf")},
    )

    response = await client.get("/dashboard")

    assert response.status_code == 200
    assert "notes.pdf" in response.text


async def test_dashboard_shows_empty_state_with_no_documents(client: AsyncClient) -> None:
    await _register_and_login(client)

    response = await client.get("/dashboard")

    assert "No documents uploaded yet." in response.text


# ---------------------------------------------------------------------------
# Document API reachable via cookie only (no Authorization header) — this is
# the auth path the dashboard's own fetch() calls rely on, since JS cannot
# read the HttpOnly access_token cookie to set a Bearer header itself.
# ---------------------------------------------------------------------------


async def test_documents_list_accessible_via_cookie_only(client: AsyncClient) -> None:
    await _register_and_login(client)
    response = await client.get("/documents")
    assert response.status_code == 200


async def test_documents_upload_accessible_via_cookie_only(client: AsyncClient) -> None:
    await _register_and_login(client)

    response = await client.post(
        "/documents/upload",
        files={"file": ("cookie.pdf", _make_pdf("cookie auth content"), "application/pdf")},
    )

    assert response.status_code == 201


async def test_documents_delete_accessible_via_cookie_only(client: AsyncClient) -> None:
    await _register_and_login(client)
    upload = await client.post(
        "/documents/upload",
        files={"file": ("cookie.pdf", _make_pdf("cookie auth content"), "application/pdf")},
    )
    doc_id = upload.json()["id"]

    response = await client.delete(f"/documents/{doc_id}")

    assert response.status_code == 204
