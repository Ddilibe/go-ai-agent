#!/usr/bin/env python3
import os
import time
from uuid import uuid4
from typing import Optional, Tuple

# from ..database.crud import create_game, update_game_winner
# from ..database.session import get_session, init_db

from .board import Board
from src.agents.mcts_agent import MCTSAgent
from src.agents.random_agent import RandomAgent
from src.agents.heuristic_agent import HeuristicAgent
from .render import AudioMode, render_board, render_video


AGENT_LEVELS = {
    "beginner": RandomAgent,
    "intermediate": HeuristicAgent,
    "hard": MCTSAgent,
}


class GoGame:
    def __init__(
        self,
        board_size: int = 9,
        black: str = "human",
        white: str = "beginner",
        output_dir: str = "cache",
    ):
        self.board = Board(board_size)
        self.board_size = board_size
        self.output_dir = f"{output_dir}/{uuid4()}/"
        self.turn = 1  # 1 = black, 2 = white
        self.passes = 0

        # Initialize agents (if not human)
        self.black_agent = self._init_agent(black, color=1)
        self.white_agent = self._init_agent(white, color=2)
        # init_db()
        # self.session = next(get_session())
        # # self.db_game = create_game(
        #     self.session,
        #     board_size,
        #     f"{black}:{self.black_agent} - {white}{self.white_agent}",
        # )

    def _init_agent(self, name: str, color: int):
        if name.lower() == "human":
            return None
        name = name.lower()
        if name not in AGENT_LEVELS:
            raise ValueError(f"Unknown AI level: {name}")
        return AGENT_LEVELS[name](color=color, board_size=self.board_size)

    # ---------------------------------------------------------------------
    # Main game loop
    # ---------------------------------------------------------------------
    def play(self, max_moves: int = 500):
        step = 1
        while self.passes < 2 and step <= max_moves:
            player_color = self.turn
            agent = self.black_agent if player_color == 1 else self.white_agent

            print(f"\nMove {step} | {'Black' if player_color == 1 else 'White'}'s turn")

            legal_moves = self.board.legal_moves(player_color)

            if not legal_moves:
                print("No legal moves available. Passing.")
                move = None
            elif agent is None:
                # Human move
                move = self.prompt_human(legal_moves)
            else:
                # AI move
                move = agent.select_move(self.board.grid, legal_moves)
                print(f"AI ({agent.__class__.__name__}) chose: {move}")

            # Apply move
            valid = self.board.place_stone(player_color, move)
            if not valid:
                print("Illegal move, skipping.")
                move = None

            # Render current board
            render_board(self.board, step, move, self.output_dir)

            # Handle pass detection
            if move is None:
                self.passes += 1
            else:
                self.passes = 0

            # Next turn
            self.turn = 3 - self.turn
            step += 1
            # save_move(self.session, self.db_game.id, move_num, current_color, move)

        # Game finished
        black_score, white_score = self.board.score()
        print("\nGame Over!")
        print(self.board)
        print(f"Final Score -> Black: {black_score}, White: {white_score}")
        winner = (
            "Black"
            if black_score > white_score
            else "White" if white_score > black_score else "Draw"
        )
        print(f"Winner: {winner}")
        # update_game_winner(self.session, self.db_game.id, winner)  # type: ignore
        render_video(
            self.output_dir,
            "media/Teresa Teng - 月亮代表我的心.mp3",
            audio_mode=AudioMode.LOOP,
        )
        return winner

    # ---------------------------------------------------------------------
    # CLI input for human player
    # ---------------------------------------------------------------------
    def prompt_human(self, legal_moves):
        print("Enter move as row,col or 'pass':")
        while True:
            user_input = input("> ").strip().lower()
            if user_input == "pass":
                return None
            try:
                r, c = map(int, user_input.split(","))
                if (r, c) in legal_moves:
                    return (r, c)
                print("Illegal move.")
                raise Exception
            except Exception:
                print("Invalid input. Format: row,col or 'pass'.")

    # ----------------------------------------------------------------------
    # Step by Step Play
    # ----------------------------------------------------------------------
    def play_step(self, move=None):
        player_color = self.turn
        agent = self.black_agent if player_color == 1 else self.white_agent

        legal_moves = self.board.legal_moves(player_color)
        if not legal_moves:
            self.passes += 1
            self.turn = 3 - self.turn
            return {"status": "pass", "message": "No legal moves"}

        if agent is None:
            if move not in legal_moves:
                return {"status": "error", "message": "Illegal move"}
        else:
            # AI selects move
            move = agent.select_move(self.board.grid, legal_moves)

        valid, step = self.board.place_stone(player_color, move), int(time.time())
        render_board(self.board, step, move, self.output_dir)
        self.turn = 3 - self.turn

        return {
            "status": "ok",
            "move": move,
            "board": os.path.join(self.output_dir, f"step_{step:04d}.png"),
        }
