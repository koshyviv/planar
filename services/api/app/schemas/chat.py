from datetime import datetime

from pydantic import BaseModel, Field


class ChatCreate(BaseModel):
    pass


class ChatResponse(BaseModel):
    id: str
    project_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class CitationItem(BaseModel):
    file_name: str
    chunk_text: str
    metadata: dict | None = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: list[CitationItem] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
