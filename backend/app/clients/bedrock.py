from __future__ import annotations

import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.core.config import AWS_REGION, BEDROCK_MODEL_ID


def _extract_text(response: dict[str, Any]) -> str:
    message = response.get("output", {}).get("message", {})
    for block in message.get("content", []):
        if "text" in block:
            return block["text"]
    return ""


def converse_text(prompt: str, max_tokens: int = 1024) -> str:
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    last_error: Exception | None = None

    for attempt in range(4):
        try:
            response = client.converse(
                modelId=BEDROCK_MODEL_ID,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": max_tokens},
            )
            return _extract_text(response)
        except ClientError as error:
            last_error = error
            code = error.response.get("Error", {}).get("Code", "")
            throttled = code == "ThrottlingException" or "Too many tokens" in str(error)
            if throttled and attempt < 3:
                time.sleep(0.5 * (2 ** (attempt + 1)))
                continue
            raise

    raise RuntimeError("Bedrock converse failed") from last_error
