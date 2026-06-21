import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.user import User
from app.schemas.documents import DocumentResponse
from app.services.chunker import chunk
from app.services.embeddings import get_embeddings
from app.services.parsers import SUPPORTED_TYPES, UnsupportedFileTypeError, parse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

_MAX_BYTES = 50 * 1024 * 1024  # 50 MB

_MAGIC_BYTES: dict[str, bytes] = {
    "pdf": b"%PDF",
    "docx": b"PK\x03\x04",
}


def _magic_ok(content: bytes, ext: str) -> bool:
    expected = _MAGIC_BYTES.get(ext)
    if expected is None:
        return True
    return content[: len(expected)] == expected


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in SUPPORTED_TYPES:
        supported = ", ".join(sorted(SUPPORTED_TYPES))
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '.{ext}'. Supported: {supported}",
        )

    content = await file.read()

    if len(content) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File exceeds the 50 MB limit.",
        )

    if not _magic_ok(content, ext):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File content does not match the declared extension.",
        )

    document = Document(user_id=current_user.id, filename=filename, status="processing")
    db.add(document)
    await db.commit()
    await db.refresh(document)

    try:
        text = parse(content, ext)
        chunk_texts = chunk(text)
        if chunk_texts:
            model = get_embeddings()
            vectors = model.embed_documents(chunk_texts)
            db.add_all(
                [
                    Chunk(
                        document_id=document.id,
                        user_id=current_user.id,
                        chunk_index=i,
                        content=chunk_texts[i],
                        embedding=vectors[i],
                    )
                    for i in range(len(chunk_texts))
                ]
            )
        document.status = "ready"
        await db.commit()
        await db.refresh(document)
        return document
    except UnsupportedFileTypeError:
        await db.rollback()
        doc = await db.get(Document, document.id)
        if doc is not None:
            doc.status = "failed"
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File type is not supported.",
        )
    except Exception:
        logger.exception("Failed to process document %s", document.id)
        await db.rollback()
        doc = await db.get(Document, document.id)
        if doc is not None:
            doc.status = "failed"
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document processing failed.",
        )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    doc = await db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    await db.execute(delete(Document).where(Document.id == doc_id))
    await db.commit()
