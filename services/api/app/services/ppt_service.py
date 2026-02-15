import asyncio

from celery import Celery

from app.config import settings

_celery = Celery(broker=settings.redis_url)


async def enqueue_ppt(artifact_id: str, params: dict):
    await asyncio.to_thread(_celery.send_task, "app.tasks.ppt_generate.generate_ppt", args=[artifact_id, params])
