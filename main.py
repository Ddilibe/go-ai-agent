#!/usr/bin/env python3
import os
import asyncio
from typing import AsyncGenerator, Any
from contextlib import asynccontextmanager

import cloudinary
from decouple import config
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware

from src.ai import GoAgent
from src.engine.game import GoGame
from src.logger import setup_logger
from src.manager import ToolsManager
from src.models import JSONRPCRequest, JSONRPCResponse, A2AMessage, MessagePart

# from src.ai_session.main import run

agent: GoAgent
# manager: ToolsManager
logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:

    global agent

    agent = GoAgent(
        str(config("MINIO_ENDPOINT")),
        str(config("MINIO_ACCESS_KEY")),
        str(config("MINIO_SECRET_KEY")),
        str(config("MINIO_BUCKET")),
        str(config("GOOGLE_API_KEY")),
    )

    cloudinary.config(
        cloud_name=str(config("CLOUDINARY_CLOUD_NAME", "")),
        api_key=str(config("CLOUDINARY_API_KEY", "")),
        api_secret=str(config("CLOUDINARY_API_SECRET", "")),
        secure=True,
    )

    # manager = ToolsManager(
    #     """{"name":"go"}""", agent.minio_client, agent.minio_bucket, {}, ""
    # )

    yield

    if agent:
        await agent.cleanup()

    # if manager:
    #     await manager.cleanup()


web = FastAPI(
    title="Go Agent A2A",
    description="A go playing agent with A2A protocol support",
    version="1.0.0",
    lifespan=lifespan,
)


web.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@web.post("/tool")
@web.post("/rpc")
async def rpc_endpoint(req: Request):
    """RPC Endpoint for Go Agent"""

    try:
        body = await req.json()

        if body.get("jsonrpc") != "2.0" or "id" not in body:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: jsonrpc must be '2.0' and id is required",
                    },
                },
            )

        rpc_request = JSONRPCRequest(**body)

        messages, context_id, task_id, config = [], None, None, None

        if rpc_request.method == "message/send" and rpc_request.params:
            messages = [rpc_request.params.message]  # type: ignore
            config = rpc_request.params.configuration  # type: ignore
        elif rpc_request.method == "execute":
            messages = rpc_request.params.message  # type: ignore
            context_id = rpc_request.params.contextId  # type: ignore
            task_id = rpc_request.params.contextId  # type: ignore

        result = await agent.process_messages(
            user_id=rpc_request.id,
            messages=messages,
            context_id=context_id,
            task_id=task_id,
            config=config,  # type: ignore
        )

        response = JSONRPCResponse(id=rpc_request.id, result=result)

        return response.model_dump()

    except Exception as e:
        logger.error(f"Error from rpc endpoint: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=dict(
                jsonrpc="2.0",
                id=body.get("id") if "body" in locals() else None,  # type: ignore
                error=dict(
                    code=-32603, message="Internal error", data=dict(details=str(e))
                ),
            ),
        )


@web.get("/health")
async def health_check():
    """Health Check Endpoint"""
    return {"status": "healthy", "agent": "Go"}


async def main():
    """Initializes the GoAgent and enters the main input/process loop."""
    print("Hello from go-agent!")
    try:
        agent = GoAgent(
            str(config("MINIO_ENDPOINT")),
            str(config("MINIO_ACCESS_KEY")),
            str(config("MINIO_SECRET_KEY")),
            str(config("MINIO_BUCKET")),
            str(config("GOOGLE_API_KEY")),
        )
    except Exception as e:
        print(f"Error initializing GoAgent with configuration: {e}")
        return

    print("GoSifu Agent Initialized. Type 'exit' to quit.")

    value = input("What do you want to do? ")

    while value.lower() != "exit":

        if value.lower() == "exit":
            break

        message = A2AMessage(
            kind="message", role="user", parts=[MessagePart(kind="text", text=value)]
        )

        try:
            result = await agent.process_messages(
                "string", messages=message, context_id="", task_id="", config=None
            )
            print(f"Agent Response: {result}")

        except Exception as e:
            print(f"An error occurred during message processing: {e}")

        value = input("What do you want to do? ")


if __name__ == "__main__":
    asyncio.run(main())
