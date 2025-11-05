#!/usr/bin/env python3
import json
from io import BytesIO
from uuid import uuid4
from json import JSONDecodeError
from typing import List, Any, Dict, Optional, Tuple

from minio import Minio
import cloudinary.uploader

from src.engine.game import GoGame
from src.models import (
    A2AMessage,
    Artifact,
    MessageConfiguration,
    MessagePart,
    TaskResult,
    TaskStatus,
)
from src.tools import make_move, get_game_status, start_game


class ToolsManager:

    def __init__(
        self,
        response: str,
        Minio_Client: Minio,
        minio_bucket: str,
        game_dict: Dict[Any, GoGame],
        id: str,
        *args,
        **kwargs,
    ) -> None:
        if "```json" in response:
            self.response: Dict[str, str | Dict[str, str | int]] = (
                self.extract_json_from_markdown(response)
            )
        else:
            self.response: Dict[str, str | Dict[str, str | int]] = json.loads(response)
        self.kwargs = kwargs
        self.minio_client = Minio_Client
        self.minio_bucket = minio_bucket
        self.game = game_dict
        self.id = id

    async def __call__(
        self, *args: List[Any], **kwds: Dict[Any, Any]
    ) -> Tuple[A2AMessage, List[Artifact]]:

        a2amessage = A2AMessage(role="agent", parts=[], taskId=str(uuid4()))
        arts = []

        tool_args = self.response.get("args")
        match self.response.get("tool_name"):
            case "make_move":
                arguments = [
                    tool_args.get(i)
                    for i in [
                        "move",
                    ]
                ]
                value = make_move(
                    arguments[0],
                    self.id,
                    self.game,
                )

                self.kwargs[self.id] = value
                a2amessage.parts.append(
                    MessagePart(kind="text", text=f"Placed a {tool_args}")
                )

            case "get_game_status":
                value = get_game_status(game=self.game[self.id])
                
                image_response = await self._upload_board_image(value[0])
                url = image_response["url"] if image_response.get("url") else ""

                a2amessage.parts.append(
                    MessagePart(kind="text", text=f"Displayed game {self.id}")
                )

                arts.append(
                    Artifact(
                        name="display", parts=[MessagePart(kind="file", file_url=url)]
                    )
                )

            case "start_game":
                arguments = [tool_args.get(i) for i in ["boardsize", "black", "white"]]
                value = start_game(
                    arguments[0], arguments[1], arguments[2], self.id, self.game
                )
                self.kwargs[self.id] = value
                a2amessage.parts.append(
                    MessagePart(kind="text", text="Initiated new game")
                )

            case _:
                pass

        return (a2amessage, arts)

    def extract_json_from_markdown(self, response: str) -> dict:
        """
        Extracts a JSON object enclosed in a ```json ... ``` markdown block.
        """
        try:
            start_marker, end_marker = "```json", "```"

            start_index = response.find(start_marker)
            if start_index == -1:
                raise ValueError("JSON start marker '```json' not found.")

            json_start = start_index + len(start_marker)

            end_index = response.find(end_marker, json_start)
            if end_index == -1:
                raise ValueError("JSON end marker '```' not found.")

            raw_json_string = response[json_start:end_index].strip()

            json_data = json.loads(raw_json_string)

            return json_data

        except ValueError as e:
            print(f"Error extracting JSON: {e}")
            return {}
        except JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return {}

    async def process_messages(
        self,
        messages: List[A2AMessage],
        context_id: Optional[str] = None,
        task_id: Optional[str] = None,
        config: Optional[MessageConfiguration] = None,
    ) -> TaskResult:
        """Process incoming messages and generate chess moves"""

        context_id = context_id or str(uuid4())
        task_id = task_id or str(uuid4())

        board = self.game.get(context_id, GoGame())

        user_message = messages[-1] if messages else None
        if not user_message:
            raise ValueError("No message provided")

        move_text = ""
        for part in user_message.parts:
            if part.kind == "text":
                move_text = part.text.strip()
                break

        try:
            move = board.play_step(move_text)
        except Exception as e:
            raise ValueError(f"Invalid move: {move_text}")

        self.game[context_id] = board
        ai_move = board.play_step()

        board_svg, _ = get_game_status(board)
        image_response = await self._upload_board_image(board_svg)
        board_url = image_response["url"] if image_response.get("url") else ""

        response_text = f"I played {ai_move['message']}"

        response_message = A2AMessage(
            role="agent",
            parts=[MessagePart(kind="text", text=response_text)],
            taskId=task_id,
        )

        artifacts = [
            Artifact(
                name="move", parts=[MessagePart(kind="text", text=ai_move["message"])]
            ),
            Artifact(
                name="board", parts=[MessagePart(kind="file", file_url=board_url)]
            ),
        ]

        # Build history
        history = messages + [response_message]

        # Determine state
        state = (
            "input-required"
            if not len(board.board.legal_moves(board.turn)) > 0
            else "completed"
        )

        return TaskResult(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(state=state, message=response_message),
            role="agent",
            artifacts=artifacts,
            history=history,
        )

    async def _upload_board_image(
        self,
        file_path: str,
        folder: str = "go_game_boards",
        public_id: Optional[str] = None,
        overwrite: bool = True,
    ) -> Dict:
        """
        Uploads an image file to Cloudinary.

        Args:
            file_path (str): Local path to the image file.
            folder (str): Cloudinary folder to store the image in.
            public_id (Optional[str]): Custom name for the uploaded file (without extension).
            overwrite (bool): Whether to overwrite if file exists.

        Returns:
            Dict: Upload result containing 'url', 'public_id', 'secure_url', etc.
        """
        try:
            result = cloudinary.uploader.upload(
                file_path,
                folder=folder,
                public_id=public_id,
                overwrite=overwrite,
                resource_type="image",
                use_filename=True,
                unique_filename=True,
            )
            return {
                "url": result.get("secure_url"),
                "public_id": result.get("public_id"),
                "width": result.get("width"),
                "height": result.get("height"),
                "format": result.get("format"),
            }
        except Exception as e:
            raise RuntimeError(f"Cloudinary upload failed: {e}")

    async def cleanup(self):
        """Cleanup resources"""
        self.game.clear()
