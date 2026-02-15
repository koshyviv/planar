from datetime import datetime

from pydantic import BaseModel, Field


class PptRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    audience: str = Field(default="general", max_length=200)
    num_slides: int = Field(default=8, ge=3, le=30)
    style: str = Field(default="professional", max_length=100)


class ArtifactResponse(BaseModel):
    id: str
    artifact_type: str
    status: str
    metadata_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
