#!/usr/bin/env python3
from src.manager import ToolsManager
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

logger = logging.getLogger("go_agent")


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

        self.minio_bucket = minio_bucket

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

        if user_id not in self.game_state:
            self.game_state[user_id] = GoGame()

        system_prompt: str
        tools = types.Tool(
            # function_declarations=[*ALL_TOOLS.values()]
        )
        aconfig = types.GenerateContentConfig(tools=[tools])

        with open("src/config/agents.yaml", "r") as file:
            system_prompt = yaml.load(file, yaml.Loader)  # type: ignore

        a2a_message = messages[-1] if isinstance(messages, list) else messages
        message = (
            a2a_message.parts[-1]
            if isinstance(a2a_message.parts, list)
            else a2a_message.parts
        )

        user_prompt = f"{system_prompt}\n\nThe gameid is {user_id if user_id in self.game_state.keys() else None} {message.text}"

        content = [
            # types.Content(
            #     role="system",
            #     parts=[types.Part(text=system_prompt)],
            # ),
            types.Content(role="user", parts=[types.Part(text=user_prompt)]),
        ]

        print("calling the model")

        response = self.model_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content,
            config=aconfig,
        )

        # print(response)

        tool_call = response.text

        manager = ToolsManager(
            tool_call,
            self.minio_client,
            self.minio_bucket,
            self.game_state,
            user_id,
            {"taskId": task_id, "id": user_id},
        )
        a2amessage, arts = await manager()

        history = messages + [a2amessage]

        # state = "input-required" if not self.game_state[id].board.is_game_over() else "completed"

        # tool = ALL_TOOLS.get(tool_call)

        return TaskResult(
            id=str(user_id),
            contextId=str(context_id),
            artifacts=arts,
            history=history,
            kind="message",
            role="agent",
            status=TaskStatus(state="working"),
        )
