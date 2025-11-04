#!/usr/bin/env python3
import yaml
import asyncio
import logging
from io import BytesIO
from uuid import uuid4
from typing import Dict, List, Optional
from datetime import datetime, timezone

from minio import Minio
from google import genai
from google.genai import types
from google.genai.chats import Content, AsyncChats

from .tools import ALL_TOOLS
from src.engine.game import GoGame
from src.models import (
    A2AMessage,
    TaskResult,
    TaskStatus,
    Artifact,
    MessagePart,
    MessageConfiguration,
)

logger = logging.getLogger('go_agent')


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
        self.chat_state: Dict[str, AsyncChats] = {}

        self.minio_client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False,
        )

        self.model_client = genai.Client(
            api_key=google_gemini_api_key,
        )

        # if not self.minio_client.bucket_exists(minio_bucket):
        # self.minio_client.make_bucket(minio_bucket)

    async def cleanup(self) -> None:
        del self.game_state

    async def process_messages(
        self,
        user_id: str,
        messages: List[A2AMessage] | A2AMessage,
        context_id: str,
        task_id: str,
        config: Optional[MessageConfiguration],
    ) -> TaskResult:

        system_prompt: str
        tools = types.Tool(function_declarations=[*ALL_TOOLS.values()])
        aconfig = types.GenerateContentConfig(tools=[tools])

        with open("agent.yaml", "r") as file:
            system_prompt = yaml.load(file, yaml.FullLoader)

        a2a_message = messages[-1] if isinstance(messages, list) else messages
        message = (
            a2a_message.parts[-1]
            if isinstance(a2a_message.parts, list)
            else a2a_message.parts
        )

        user_prompt = f"The gameid is {user_id if user_id in self.game_state.keys() else None} {message.text}"

        content = [
            types.Content(
                role="system",
                parts=[types.Part(text=system_prompt)],
            ),
            types.Content(role="user", parts=[types.Part(text=user_prompt)]),
        ]

        response = self.model_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content,
            config=aconfig,
        )
        
        
        tool_call = response.candidates[0].content.parts[].function_call
        
        tool = ALL_TOOLS.get(tool_call)

        return TaskResult(
            id=str(user_id),
            contextId=str(context_id),
            artifacts=[],
            history=[messages] if isinstance(messages, A2AMessage) else messages,
            kind="task",
            status=TaskStatus(state="working"),
        )
