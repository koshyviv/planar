import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user, get_db, get_user_project
from app.models.chat import Chat
from app.models.message import Message
from app.models.project import Project
from app.models.user import User
from app.schemas.chat import ChatResponse, MessageCreate, MessageResponse
from app.services.chat_service import generate_answer

router = APIRouter(prefix="/projects/{project_id}", tags=["chat"])


@router.post("/chats", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    project: Annotated[Project, Depends(get_user_project)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    chat = Chat(project_id=project.id, user_id=user.id)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return ChatResponse(id=str(chat.id), project_id=str(chat.project_id), created_at=chat.created_at)


@router.get("/chats", response_model=list[ChatResponse])
async def list_chats(
    project: Annotated[Project, Depends(get_user_project)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Chat).where(Chat.project_id == project.id, Chat.user_id == user.id).order_by(Chat.created_at.desc())
    )
    chats = result.scalars().all()
    return [ChatResponse(id=str(c.id), project_id=str(c.project_id), created_at=c.created_at) for c in chats]


@router.post("/chats/{chat_id}/messages", response_model=MessageResponse)
async def send_message(
    chat_id: uuid.UUID,
    body: MessageCreate,
    project: Annotated[Project, Depends(get_user_project)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Verify chat belongs to project and user
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.project_id == project.id, Chat.user_id == user.id)
    )
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    # Save user message
    user_msg = Message(chat_id=chat.id, role="user", content=body.content)
    db.add(user_msg)
    await db.flush()

    # Get chat history
    result = await db.execute(
        select(Message).where(Message.chat_id == chat.id).order_by(Message.created_at)
    )
    history = result.scalars().all()

    # Generate answer with RAG
    answer_text, citations = await generate_answer(
        project_id=project.id,
        messages=history,
        db=db,
    )

    # Save assistant message
    citations_json = [c.model_dump() for c in citations] if citations else None
    assistant_msg = Message(chat_id=chat.id, role="assistant", content=answer_text, citations=citations_json)
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return MessageResponse(
        id=str(assistant_msg.id), role=assistant_msg.role, content=assistant_msg.content,
        citations=citations, created_at=assistant_msg.created_at,
    )


@router.get("/chats/{chat_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    chat_id: uuid.UUID,
    project: Annotated[Project, Depends(get_user_project)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.project_id == project.id, Chat.user_id == user.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    result = await db.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [
        MessageResponse(id=str(m.id), role=m.role, content=m.content, citations=m.citations, created_at=m.created_at)
        for m in messages
    ]
