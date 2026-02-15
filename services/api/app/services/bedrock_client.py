import asyncio
import json
from functools import lru_cache

import boto3
import numpy as np

from app.config import settings


@lru_cache(maxsize=1)
def _get_bedrock_client():
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    return boto3.client("bedrock-runtime", **kwargs)


async def converse(messages: list[dict], system: str | None = None, max_tokens: int = 4096) -> str:
    """Call Claude via Bedrock Converse API."""
    client = _get_bedrock_client()

    kwargs = {
        "modelId": settings.bedrock_text_model_id,
        "messages": messages,
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.3},
    }
    if system:
        kwargs["system"] = [{"text": system}]

    def _call():
        response = client.converse(**kwargs)
        return response["output"]["message"]["content"][0]["text"]

    return await asyncio.to_thread(_call)


async def embed(text: str) -> list[float]:
    """Embed text via Bedrock Titan Embed V2."""
    client = _get_bedrock_client()

    def _call():
        body = json.dumps({"inputText": text, "dimensions": 1024, "normalize": True})
        response = client.invoke_model(modelId=settings.bedrock_embed_model_id, body=body, contentType="application/json")
        result = json.loads(response["body"].read())
        return result["embedding"]

    return await asyncio.to_thread(_call)
