import io
from functools import lru_cache

from minio import Minio

from app.config import settings


@lru_cache(maxsize=1)
def _get_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl,
    )


def ensure_buckets():
    client = _get_client()
    for bucket in [settings.minio_bucket_uploads, settings.minio_bucket_artifacts]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)


def download_file(bucket: str, object_name: str) -> bytes:
    client = _get_client()
    response = client.get_object(bucket, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def upload_file(bucket: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    client = _get_client()
    client.put_object(bucket, object_name, io.BytesIO(data), len(data), content_type=content_type)
    return f"{bucket}/{object_name}"
