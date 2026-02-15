import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db, get_user_project
from app.models.artifact import Artifact
from app.models.project import Project
from app.models.user import User
from app.schemas.ppt import ArtifactResponse, PptRequest
from app.services.ppt_service import enqueue_ppt

router = APIRouter(tags=["ppt"])


@router.post("/projects/{project_id}/ppt", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def request_ppt(
    body: PptRequest,
    project: Annotated[Project, Depends(get_user_project)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    artifact = Artifact(
        project_id=project.id,
        artifact_type="pptx",
        storage_path="",  # filled by worker
        status="pending",
        metadata_json={"topic": body.topic, "audience": body.audience, "num_slides": body.num_slides, "style": body.style},
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    await enqueue_ppt(str(artifact.id), body.model_dump())
    return ArtifactResponse(
        id=str(artifact.id), artifact_type=artifact.artifact_type, status=artifact.status,
        metadata_json=artifact.metadata_json, created_at=artifact.created_at,
    )


@router.get("/projects/{project_id}/artifacts", response_model=list[ArtifactResponse])
async def list_artifacts(
    project: Annotated[Project, Depends(get_user_project)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Artifact).where(Artifact.project_id == project.id).order_by(Artifact.created_at.desc())
    )
    artifacts = result.scalars().all()
    return [
        ArtifactResponse(
            id=str(a.id), artifact_type=a.artifact_type, status=a.status,
            metadata_json=a.metadata_json, created_at=a.created_at,
        )
        for a in artifacts
    ]


@router.get("/artifacts/{artifact_id}/download")
async def download_artifact(
    artifact_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    # Verify ownership
    result = await db.execute(
        select(Project).where(Project.id == artifact.project_id, Project.user_id == user.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    if artifact.status != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Artifact is {artifact.status}")

    from app.services.storage_client import presigned_url
    url = await presigned_url(settings.minio_bucket_artifacts, artifact.storage_path)
    return RedirectResponse(url=url)
