from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.language_models import BaseChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, get_llm
from app.models.user import User
from app.schemas.query import QueryRequest, QueryResponse, SourceResponse
from app.services import query_service

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm: BaseChatModel = Depends(get_llm),
) -> QueryResponse:
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )
    result = await query_service.run(
        question=request.question,
        use_web_search=request.use_web_search,
        user_id=current_user.id,
        db=db,
        llm=llm,
    )
    sources = [
        SourceResponse(
            document_id=s["document_id"],
            chunk_index=s["chunk_index"],
            text=s["content"],
        )
        for s in result["sources"]
    ]
    return QueryResponse(
        answer=result["answer"],
        sources=sources,
        used_web_search=result["used_web_search"],
    )
