import asyncio

from celery import Celery

from app.config import settings

_celery = Celery(broker=settings.redis_url)


async def enqueue_ingest(file_id: str):
    await asyncio.to_thread(_celery.send_task, "app.tasks.ingest.ingest_file", args=[file_id])
