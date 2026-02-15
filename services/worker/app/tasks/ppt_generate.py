import json
import logging
import uuid

from sqlalchemy import text

from app.celery_app import celery
from app.config import settings
from app.database import get_session
from app.ppt_builder import build_pptx
from app.services.bedrock_client import converse, embed
from app.services.storage_client import upload_file

logger = logging.getLogger(__name__)


def _get_rag_context(session, project_id: str, topic: str, top_k: int = 10) -> str:
    """Retrieve relevant chunks for PPT context."""
    embedding = embed(topic)
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    result = session.execute(
        text("""
            SELECT c.text, f.original_name
            FROM vectors v
            JOIN chunks c ON v.chunk_id = c.id
            JOIN files f ON c.file_id = f.id
            WHERE v.project_id = :project_id
            ORDER BY v.embedding <=> :embedding::vector
            LIMIT :top_k
        """),
        {"project_id": project_id, "embedding": embedding_str, "top_k": top_k},
    )
    rows = result.fetchall()
    if not rows:
        return "No project documents available."

    parts = []
    for chunk_text, file_name in rows:
        parts.append(f"[Source: {file_name}]\n{chunk_text}")
    return "\n\n---\n\n".join(parts)


@celery.task(name="app.tasks.ppt_generate.generate_ppt", bind=True, max_retries=2)
def generate_ppt(self, artifact_id: str, params: dict):
    """Generate a PowerPoint presentation using RAG + Claude."""
    session = get_session()
    try:
        # Get artifact
        result = session.execute(
            text("SELECT id, project_id, status FROM artifacts WHERE id = :id"),
            {"id": artifact_id},
        )
        row = result.fetchone()
        if row is None:
            logger.error(f"Artifact {artifact_id} not found")
            return

        _, project_id, _ = row

        # Update status
        session.execute(text("UPDATE artifacts SET status = 'processing' WHERE id = :id"), {"id": artifact_id})
        session.commit()

        topic = params.get("topic", "Presentation")
        audience = params.get("audience", "general")
        num_slides = params.get("num_slides", 8)
        style = params.get("style", "professional")

        # Get RAG context
        context = _get_rag_context(session, str(project_id), topic)

        # Step 1: Generate outline
        outline_prompt = f"""Create a presentation outline with exactly {num_slides} slides.
Topic: {topic}
Audience: {audience}
Style: {style}

Use the following project context for content:
{context}

Return ONLY valid JSON in this format:
{{
  "title": "Presentation Title",
  "slides": [
    {{
      "title": "Slide Title",
      "bullet_points": ["Point 1", "Point 2", "Point 3"],
      "speaker_notes": "Notes for the presenter"
    }}
  ]
}}"""

        outline_response = converse(
            messages=[{"role": "user", "content": [{"text": outline_prompt}]}],
            system="You are a presentation designer. Return only valid JSON, no markdown formatting.",
            max_tokens=4096,
        )

        # Parse JSON from response
        try:
            # Strip any markdown code blocks
            json_text = outline_response.strip()
            if json_text.startswith("```"):
                json_text = json_text.split("\n", 1)[1]
            if json_text.endswith("```"):
                json_text = json_text.rsplit("```", 1)[0]
            outline = json.loads(json_text.strip())
        except json.JSONDecodeError:
            logger.error(f"Failed to parse outline JSON: {outline_response[:200]}")
            session.execute(text("UPDATE artifacts SET status = 'error' WHERE id = :id"), {"id": artifact_id})
            session.commit()
            return

        # Step 2: Build PPTX
        pptx_bytes = build_pptx(outline)

        # Step 3: Upload to MinIO
        storage_path = f"{project_id}/{artifact_id}.pptx"
        upload_file(
            settings.minio_bucket_artifacts,
            storage_path,
            pptx_bytes,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

        # Step 4: Update artifact
        session.execute(
            text("UPDATE artifacts SET status = 'ready', storage_path = :path WHERE id = :id"),
            {"path": storage_path, "id": artifact_id},
        )
        session.commit()
        logger.info(f"Generated PPT artifact {artifact_id}")

    except Exception as e:
        session.rollback()
        logger.exception(f"Error generating PPT {artifact_id}: {e}")
        session.execute(text("UPDATE artifacts SET status = 'error' WHERE id = :id"), {"id": artifact_id})
        session.commit()
        raise self.retry(exc=e, countdown=60)
    finally:
        session.close()
