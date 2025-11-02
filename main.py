#!/usr/bin/env python3
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from decouple import config
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, status

from src.agents import GoAgent
from src.go.game import GoGame
from src.models import JSONRPCRequest, JSONRPCResponse

# from src.ai_session.main import run

agent: GoAgent


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:

    global agent

    agent = GoAgent(
        str(config("MINIO_ENDPOINT")),
        str(config("MINIO_ACCESS_KEY")),
        str(config("MINIO_SECRET_KEY")),
        str(config("MINIO_BUCKET")),
        "",
    )

    yield

    if agent:
        await agent.cleanup()


web = FastAPI(
    title="Go Agent A2A",
    description="A go playing agent with A2A protocol support",
    version="1.0.0",
    lifespan=lifespan,
)


@web.post("/rpc")
async def rpc_endpoint(req: Request):
    """RPC Endpoint for Go Agent"""

    body = await req.json()

    try:
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
            messages = [rpc_request.params.message]
            config = rpc_request.params.configuration
        elif rpc_request.method == "execute":
            messages = rpc_request.params.message
            context_id = rpc_request.params.contextId
            task_id = rpc_request.params.contextId

        result = await agent.process_messages(
            messages=messages, context_id=context_id, task_id=task_id, config=config
        )

        response = JSONRPCResponse(id=rpc_request.id, result=result)

        return response.model_dump()
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=dict(
                jsonrpc="2.0",
                id=body.get("id") if "body" in locals() else None,
                error=dict(
                    code=-32603, message="Internal error", data=dict(details=str(e))
                ),
            ),
        )


@web.get("/health")
async def health_check():
    """Health Check Endpoint"""
    return {"status": "healthy", "agent": "Go"}


def main():
    print("Hello from go-agent!")


if __name__ == "__main__":
    game = GoGame(board_size=19, black="intermediate", white="hard", output_dir="cache")
    game.play()
    # run()
