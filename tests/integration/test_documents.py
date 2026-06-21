import io
import uuid

from fpdf import FPDF
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk


def unique_email() -> str:
    return f"docs_{uuid.uuid4().hex[:8]}@example.com"


def _make_pdf() -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="This is a test document for the upload integration test.")
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


async def _register_and_token(client: AsyncClient) -> tuple[str, uuid.UUID]:
    reg = await client.post(
        "/auth/register", json={"email": unique_email(), "password": "pass1234"}
    )
    token = reg.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = uuid.UUID(me.json()["id"])
    return token, user_id


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


async def test_upload_pdf_returns_201_with_ready_status(client: AsyncClient) -> None:
    token, _ = await _register_and_token(client)

    response = await client.post(
        "/documents/upload",
        files={"file": ("notes.pdf", _make_pdf(), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["filename"] == "notes.pdf"
    assert "id" in body
    assert "created_at" in body


async def test_upload_pdf_persists_chunks_with_correct_user_id(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token, user_id = await _register_and_token(client)

    response = await client.post(
        "/documents/upload",
        files={"file": ("notes.pdf", _make_pdf(), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    doc_id = uuid.UUID(response.json()["id"])

    result = await db_session.execute(select(Chunk).where(Chunk.document_id == doc_id))
    chunks = result.scalars().all()

    assert len(chunks) > 0
    assert all(c.user_id == user_id for c in chunks)


# ---------------------------------------------------------------------------
# Validation — extension and magic bytes
# ---------------------------------------------------------------------------


async def test_upload_unsupported_extension_returns_415(client: AsyncClient) -> None:
    token, _ = await _register_and_token(client)

    response = await client.post(
        "/documents/upload",
        files={"file": ("malware.exe", b"MZ fake exe", "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 415


async def test_upload_wrong_magic_bytes_returns_415(client: AsyncClient) -> None:
    token, _ = await _register_and_token(client)

    # JPEG bytes disguised as a PDF
    response = await client.post(
        "/documents/upload",
        files={"file": ("sneaky.pdf", b"\xff\xd8\xff fake jpeg", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 415


# ---------------------------------------------------------------------------
# Validation — file size
# ---------------------------------------------------------------------------


async def test_upload_oversized_file_returns_413(client: AsyncClient) -> None:
    token, _ = await _register_and_token(client)

    # Valid PDF magic bytes followed by enough zeros to exceed 50 MB
    big_content = b"%PDF" + b"\x00" * (50 * 1024 * 1024)

    response = await client.post(
        "/documents/upload",
        files={"file": ("huge.pdf", big_content, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 413


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def test_upload_without_auth_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/documents/upload",
        files={"file": ("notes.pdf", b"%PDF fake", "application/pdf")},
    )

    assert response.status_code == 401
