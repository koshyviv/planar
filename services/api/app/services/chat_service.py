import uuid

from pgvector.sqlalchemy import Vector as PgVector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.file import File
from app.models.message import Message
from app.models.vector import Vector
from app.schemas.chat import CitationItem
from app.services.bedrock_client import converse, embed


async def generate_answer(
    project_id: uuid.UUID,
    messages: list[Message],
    db: AsyncSession,
    top_k: int = 5,
) -> tuple[str, list[CitationItem]]:
    """RAG: embed query → retrieve chunks → call Claude → return answer + citations."""
    # Get the latest user message
    user_query = ""
    for msg in reversed(messages):
        if msg.role == "user":
            user_query = msg.content
            break

    if not user_query:
        return "I need a question to help you.", []

    # Embed the query
    query_embedding = await embed(user_query)

    # Vector search scoped to project
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    result = await db.execute(
        text("""
            SELECT v.id, v.chunk_id, v.embedding <=> CAST(:embedding AS vector) AS distance
            FROM vectors v
            WHERE v.project_id = :project_id
            ORDER BY v.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """),
        {"embedding": embedding_str, "project_id": str(project_id), "top_k": top_k},
    )
    rows = result.fetchall()

    if not rows:
        # No context available, still answer
        converse_messages = [{"role": m.role, "content": [{"text": m.content}]} for m in messages]
        system = "You are a helpful assistant for a project. No project documents have been uploaded yet. Let the user know."
        answer = await converse(converse_messages, system=system)
        return answer, []

    # Fetch chunks and file info
    chunk_ids = [row.chunk_id for row in rows]
    result = await db.execute(
        select(Chunk, File.original_name).join(File, Chunk.file_id == File.id).where(Chunk.id.in_(chunk_ids))
    )
    chunk_data = result.all()
    chunk_map = {str(chunk.id): (chunk, file_name) for chunk, file_name in chunk_data}

    # Build context
    context_parts = []
    citations = []
    for row in rows:
        if str(row.chunk_id) in chunk_map:
            chunk, file_name = chunk_map[str(row.chunk_id)]
            context_parts.append(f"[Source: {file_name}]\n{chunk.text}")
            citations.append(CitationItem(
                file_name=file_name,
                chunk_text=chunk.text[:300],
                metadata=chunk.metadata_json,
            ))

    context_text = "\n\n---\n\n".join(context_parts)

    system = f"""You are a helpful assistant for a project. Answer questions based on the provided context from project documents.
Always cite your sources by referring to the file names.
If the context doesn't contain enough information to answer, say so clearly.

Context from project documents:
{context_text}"""

    # Build conversation messages for Converse API
    converse_messages = [{"role": m.role, "content": [{"text": m.content}]} for m in messages]

    answer = await converse(converse_messages, system=system)
    return answer, citations
