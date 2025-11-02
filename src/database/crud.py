#!/usr/bin/env python3
from sqlmodel import Session, select
from .models import Game, Move


def create_game(session: Session, board_size: int, ai_level: str) -> Game:
    game = Game(board_size=board_size, ai_level=ai_level)
    session.add(game)
    session.commit()
    session.refresh(game)
    return game


def save_move(
    session: Session, game_id: int, move_number: int, player_color: int, move=None
):
    move_obj = Move(
        game_id=game_id,
        move_number=move_number,
        player_color=player_color,
        passed=(move is None),
        row=move[0] if move else None,
        col=move[1] if move else None,
    )
    session.add(move_obj)
    session.commit()


def update_game_winner(session: Session, game_id: int, winner: str):
    game = session.get(Game, game_id)
    if game:
        game.winner = winner
        session.commit()
