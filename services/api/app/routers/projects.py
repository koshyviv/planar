import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, get_user_project
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [ProjectResponse(id=str(p.id), name=p.name, description=p.description, created_at=p.created_at) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = Project(name=body.name, description=body.description, user_id=user.id)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(id=str(project.id), name=project.name, description=project.description, created_at=project.created_at)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project: Annotated[Project, Depends(get_user_project)]):
    return ProjectResponse(id=str(project.id), name=project.name, description=project.description, created_at=project.created_at)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    body: ProjectUpdate,
    project: Annotated[Project, Depends(get_user_project)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(id=str(project.id), name=project.name, description=project.description, created_at=project.created_at)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project: Annotated[Project, Depends(get_user_project)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.delete(project)
    await db.commit()
