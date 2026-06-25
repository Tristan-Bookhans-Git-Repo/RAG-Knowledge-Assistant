import uuid
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk


class SimilarityResult(TypedDict):
    id: uuid.UUID
    content: str
    document_id: uuid.UUID
    chunk_index: int
    similarity: float


async def similarity_search(
    db: AsyncSession, query_embedding: list[float], user_id: uuid.UUID, top_k: int = 5
) -> list[SimilarityResult]:
    distance = Chunk.embedding.cosine_distance(query_embedding).label("distance")
    stmt = select(Chunk, distance).where(Chunk.user_id == user_id).order_by(distance).limit(top_k)
    rows = (await db.execute(stmt)).all()
    return [
        SimilarityResult(
            id=chunk.id,
            content=chunk.content,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            similarity=1 - dist,
        )
        for chunk, dist in rows
    ]


async def bulk_insert_chunks(db: AsyncSession, chunks: list[Chunk]) -> None:
    db.add_all(chunks)
    await db.commit()
