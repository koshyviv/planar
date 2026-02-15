from datetime import datetime

from pydantic import BaseModel


class FileResponse(BaseModel):
    id: str
    original_name: str
    mime_type: str
    extension: str
    size_bytes: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
