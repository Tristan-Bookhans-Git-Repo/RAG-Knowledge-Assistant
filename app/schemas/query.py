import uuid

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    use_web_search: bool = False


class SourceResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    chunk_index: int
    text: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    used_web_search: bool
