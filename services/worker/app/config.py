from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database (sync for Celery)
    database_url_sync: str = "postgresql://planar:planar_dev_password@db:5432/planar"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_uploads: str = "uploads"
    minio_bucket_artifacts: str = "artifacts"
    minio_use_ssl: bool = False

    # AWS Bedrock
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_text_model_id: str = "us.anthropic.claude-opus-4-0-20250514"
    bedrock_embed_model_id: str = "amazon.titan-embed-text-v2:0"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
