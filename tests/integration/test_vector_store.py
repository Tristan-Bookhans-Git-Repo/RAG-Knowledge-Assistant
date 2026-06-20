import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.user import User
from app.services.vector_store import bulk_insert_chunks, similarity_search


def unit_vector(index: int, dim: int = settings.EMBEDDING_DIM, sign: float = 1.0) -> list[float]:
    vec = [0.0] * dim
    vec[index] = sign
    return vec


async def _make_user_and_document(db: AsyncSession) -> tuple[User, Document]:
    user = User(email=f"vs_{uuid.uuid4().hex[:8]}@example.com", hashed_password="hashed")
    db.add(user)
    await db.flush()
    document = Document(user_id=user.id, filename="notes.txt")
    db.add(document)
    await db.flush()
    return user, document


# ---------------------------------------------------------------------------
# bulk_insert_chunks
# ---------------------------------------------------------------------------


async def test_bulk_insert_chunks_persists_all_chunks(db_session: AsyncSession) -> None:
    user, document = await _make_user_and_document(db_session)
    chunks = [
        Chunk(
            document_id=document.id,
            user_id=user.id,
            chunk_index=i,
            content=f"chunk {i}",
            embedding=unit_vector(0),
        )
        for i in range(3)
    ]

    await bulk_insert_chunks(db_session, chunks)

    results = await similarity_search(db_session, unit_vector(0), user.id, top_k=10)
    assert len(results) == 3


async def test_bulk_insert_chunks_empty_list_is_a_no_op(db_session: AsyncSession) -> None:
    await bulk_insert_chunks(db_session, [])


# ---------------------------------------------------------------------------
# similarity_search
# ---------------------------------------------------------------------------


async def test_similarity_search_orders_by_closest_first(db_session: AsyncSession) -> None:
    user, document = await _make_user_and_document(db_session)
    identical = Chunk(
        document_id=document.id,
        user_id=user.id,
        chunk_index=0,
        content="identical",
        embedding=unit_vector(0),
    )
    orthogonal = Chunk(
        document_id=document.id,
        user_id=user.id,
        chunk_index=1,
        content="orthogonal",
        embedding=unit_vector(1),
    )
    opposite = Chunk(
        document_id=document.id,
        user_id=user.id,
        chunk_index=2,
        content="opposite",
        embedding=unit_vector(0, sign=-1.0),
    )
    await bulk_insert_chunks(db_session, [orthogonal, opposite, identical])

    results = await similarity_search(db_session, unit_vector(0), user.id, top_k=3)

    assert [r["content"] for r in results] == ["identical", "orthogonal", "opposite"]
    assert results[0]["similarity"] == 1.0
    assert results[1]["similarity"] == 0.0
    assert results[2]["similarity"] == -1.0


async def test_similarity_search_respects_top_k(db_session: AsyncSession) -> None:
    user, document = await _make_user_and_document(db_session)
    chunks = [
        Chunk(
            document_id=document.id,
            user_id=user.id,
            chunk_index=i,
            content=f"chunk {i}",
            embedding=unit_vector(0),
        )
        for i in range(5)
    ]
    await bulk_insert_chunks(db_session, chunks)

    results = await similarity_search(db_session, unit_vector(0), user.id, top_k=2)
    assert len(results) == 2


async def test_similarity_search_returns_expected_shape(db_session: AsyncSession) -> None:
    user, document = await _make_user_and_document(db_session)
    chunk = Chunk(
        document_id=document.id,
        user_id=user.id,
        chunk_index=7,
        content="hello world",
        embedding=unit_vector(0),
    )
    await bulk_insert_chunks(db_session, [chunk])

    results = await similarity_search(db_session, unit_vector(0), user.id, top_k=1)

    assert results[0] == {
        "id": chunk.id,
        "content": "hello world",
        "document_id": document.id,
        "chunk_index": 7,
        "similarity": 1.0,
    }


async def test_similarity_search_is_scoped_to_user(db_session: AsyncSession) -> None:
    user_a, document_a = await _make_user_and_document(db_session)
    user_b, document_b = await _make_user_and_document(db_session)
    await bulk_insert_chunks(
        db_session,
        [
            Chunk(
                document_id=document_a.id,
                user_id=user_a.id,
                chunk_index=0,
                content="user a's secret",
                embedding=unit_vector(0),
            )
        ],
    )

    results = await similarity_search(db_session, unit_vector(0), user_b.id, top_k=10)

    assert results == []
