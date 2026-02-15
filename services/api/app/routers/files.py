import hashlib
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db, get_user_project
from app.models.file import File
from app.models.project import Project
from app.schemas.file import FileResponse
from app.services.storage_client import upload_file

router = APIRouter(prefix="/projects/{project_id}/files", tags=["files"])

ALLOWED_MIMES = {
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".csv": "text/csv",
    ".txt": "text/plain",
}


@router.post("", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile,
    project: Annotated[Project, Depends(get_user_project)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Validate extension
    allowed = [e.strip() for e in settings.allowed_extensions.split(",")]
    ext = ""
    if file.filename:
        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type {ext} not allowed")

    # Read and validate size
    data = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    # Compute hash
    sha256 = hashlib.sha256(data).hexdigest()
    storage_path = f"{project.id}/{sha256}{ext}"
    mime = ALLOWED_MIMES.get(ext, "application/octet-stream")

    # Upload to MinIO
    await upload_file(settings.minio_bucket_uploads, storage_path, data, mime)

    # Create DB record
    db_file = File(
        project_id=project.id,
        original_name=file.filename or "unknown",
        storage_path=storage_path,
        mime_type=mime,
        extension=ext,
        sha256=sha256,
        size_bytes=len(data),
        status="pending",
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    # Enqueue ingestion task
    from app.services.file_service import enqueue_ingest
    await enqueue_ingest(str(db_file.id))

    return FileResponse(
        id=str(db_file.id), original_name=db_file.original_name, mime_type=db_file.mime_type,
        extension=db_file.extension, size_bytes=db_file.size_bytes, status=db_file.status,
        created_at=db_file.created_at,
    )


@router.get("", response_model=list[FileResponse])
async def list_files(
    project: Annotated[Project, Depends(get_user_project)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(File).where(File.project_id == project.id).order_by(File.created_at.desc())
    )
    files = result.scalars().all()
    return [
        FileResponse(
            id=str(f.id), original_name=f.original_name, mime_type=f.mime_type,
            extension=f.extension, size_bytes=f.size_bytes, status=f.status, created_at=f.created_at,
        )
        for f in files
    ]


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    project: Annotated[Project, Depends(get_user_project)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(File).where(File.id == file_id, File.project_id == project.id))
    f = result.scalar_one_or_none()
    if f is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    await db.delete(f)
    await db.commit()
