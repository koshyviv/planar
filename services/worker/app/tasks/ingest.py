import json
import logging
import uuid

from sqlalchemy import text

from app.celery_app import celery
from app.chunker import chunk_text
from app.config import settings
from app.database import get_session
from app.parsers.csv_parser import parse_csv
from app.parsers.docx_parser import parse_docx
from app.parsers.pdf_parser import parse_pdf
from app.parsers.pptx_parser import parse_pptx
from app.parsers.xlsx_parser import parse_xlsx
from app.services.bedrock_client import embed
from app.services.storage_client import download_file

logger = logging.getLogger(__name__)

PARSERS = {
    ".pdf": parse_pdf,
    ".pptx": parse_pptx,
    ".xlsx": parse_xlsx,
    ".docx": parse_docx,
    ".csv": parse_csv,
    ".txt": lambda data: [{"text": data.decode("utf-8", errors="replace"), "metadata": {"type": "text"}}],
}


@celery.task(name="app.tasks.ingest.ingest_file", bind=True, max_retries=3)
def ingest_file(self, file_id: str):
    """Download file from MinIO, parse, chunk, embed, store vectors."""
    session = get_session()
    try:
        # Get file record
        result = session.execute(
            text("SELECT id, project_id, storage_path, extension, status FROM files WHERE id = :id"),
            {"id": file_id},
        )
        row = result.fetchone()
        if row is None:
            logger.error(f"File {file_id} not found")
            return

        file_id_val, project_id, storage_path, extension, status = row

        # Update status to processing
        session.execute(text("UPDATE files SET status = 'processing' WHERE id = :id"), {"id": file_id})
        session.commit()

        # Download from MinIO
        data = download_file(settings.minio_bucket_uploads, storage_path)

        # Parse
        parser = PARSERS.get(extension)
        if parser is None:
            logger.error(f"No parser for {extension}")
            session.execute(text("UPDATE files SET status = 'error' WHERE id = :id"), {"id": file_id})
            session.commit()
            return

        sections = parser(data)

        # Chunk and embed
        chunk_ordinal = 0
        for section in sections:
            text_content = section.get("text", "")
            metadata = section.get("metadata", {})
            chunks = chunk_text(text_content)

            for chunk_text_val in chunks:
                if not chunk_text_val.strip():
                    continue

                chunk_id = str(uuid.uuid4())

                # Insert chunk
                session.execute(
                    text("""
                        INSERT INTO chunks (id, file_id, ordinal, text, metadata_json)
                        VALUES (:id, :file_id, :ordinal, :text, :metadata::jsonb)
                    """),
                    {
                        "id": chunk_id,
                        "file_id": file_id,
                        "ordinal": chunk_ordinal,
                        "text": chunk_text_val,
                        "metadata": json.dumps(metadata),
                    },
                )

                # Embed
                embedding = embed(chunk_text_val)
                embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

                # Insert vector
                session.execute(
                    text("""
                        INSERT INTO vectors (id, chunk_id, project_id, embedding)
                        VALUES (:id, :chunk_id, :project_id, :embedding::vector)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "chunk_id": chunk_id,
                        "project_id": str(project_id),
                        "embedding": embedding_str,
                    },
                )

                chunk_ordinal += 1

        # Update file status
        session.execute(text("UPDATE files SET status = 'ready' WHERE id = :id"), {"id": file_id})
        session.commit()
        logger.info(f"Ingested file {file_id}: {chunk_ordinal} chunks")

    except Exception as e:
        session.rollback()
        logger.exception(f"Error ingesting file {file_id}: {e}")
        session.execute(text("UPDATE files SET status = 'error' WHERE id = :id"), {"id": file_id})
        session.commit()
        raise self.retry(exc=e, countdown=30)
    finally:
        session.close()
