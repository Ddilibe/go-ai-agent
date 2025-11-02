#!/usr/bin/env python3
import asyncio
from io import BytesIO
from uuid import uuid4
from typing import List, Optional
from datetime import datetime, timezone

from google import genai
from google.genai import types
from minio import Minio

from src.go.game import GoGame
from src.models import (
    A2AMessage,
    TaskResult,
    TaskStatus,
    Artifact,
    MessagePart,
    MessageConfiguration,
)


class GoAgent:

    def __init__(
        self,
        minio_endpoint: str,
        minio_access_key: str,
        minio_secret_key: str,
        minio_bucket: str,
        google_gemini_api_key: str,
    ) -> None:

        self.game_state = {}

        self.minio_client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False,
        )

        # if not self.minio_client.bucket_exists(minio_bucket):
            # self.minio_client.make_bucket(minio_bucket)

    async def cleanup(self) -> None:
        del self.game_state

    async def process_messages(
        self,
        messages: List[A2AMessage] | A2AMessage,
        context_id: str,
        task_id: str,
        config: Optional[MessageConfiguration],
    ) -> TaskResult:
        return TaskResult(
            id=str(uuid4()),
            contextId=str(uuid4()),
            artifacts=[],
            history=[],
            kind="task",
            status=TaskStatus(state="working"),
        )
