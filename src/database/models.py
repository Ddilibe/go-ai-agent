#!/usr/bin/env python3
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple


from sqlmodel import SQLModel, Field, Relationship, JSON


class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    board_size: int
    ai_level: str
    winner: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None

    moves: List["Move"] = Relationship(back_populates="game")


class Move(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="game.id")
    move_number: int
    player_color: int
    row: Optional[int] = None
    col: Optional[int] = None
    passed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    game: Optional[Game] = Relationship(back_populates="moves")


class TaskMemory(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True)
    session_id: str = Field(index=True)
    task_name: str
    params: Dict = Field(sa_column=JSON)
    missing: Optional[Dict] = Field(default=None, sa_column=JSON)
    status: str = Field(default="incomplete")
    context_type: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BoardModel(SQLModel, table=True):
    
    size: int
    gird: List[List[int]]
    ko: Optional[Tuple[int, int]]
    
    