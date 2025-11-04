#!/usr/bin/env python3
from typing import List, Optional, Tuple

import numpy as np

from .base_agent import BaseAgent


class HeuristicAgent(BaseAgent):
    """Simple rule-based agent using local heuristics."""

    def select_move(
        self, board: np.ndarray, legal_moves: List[Tuple[int, int]]
    ) -> Optional[Tuple[int, int]]:
        if not legal_moves:
            return None

        best_score = -float("inf")
        best_move = None

        for move in legal_moves:
            score = self.evaluate_move(board, move)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def evaluate_move(self, board: np.ndarray, move: Tuple[int, int]) -> float:
        """Return a heuristic score for a move."""
        # Clone the board for simulation (lightweight copy)
        sim_board = np.copy(board)
        color = self.color
        opp = 3 - color

        # Place temporarily
        sim_board[move] = color

        # Basic heuristics:
        score = 0.0

        # Count nearby opponent stones (potential captures)
        neighbors = self.get_neighbors(move)
        score += sum(1 for n in neighbors if board[n] == opp) * 2.0

        # Count liberties (the more, the safer)
        liberties = self.count_liberties(sim_board, move)
        score += liberties * 0.5

        # Penalize suicide/self-atari
        if liberties == 0:
            score -= 5.0

        return score

    def get_neighbors(self, move: Tuple[int, int]) -> List[Tuple[int, int]]:
        r, c = move
        neighbors = []
        if r > 0:
            neighbors.append((r - 1, c))
        if r < self.board_size - 1:
            neighbors.append((r + 1, c))
        if c > 0:
            neighbors.append((r, c - 1))
        if c < self.board_size - 1:
            neighbors.append((r, c + 1))
        return neighbors

    def count_liberties(self, board: np.ndarray, move: Tuple[int, int]) -> int:
        """Count liberties of the group connected to move."""
        color = board[move]
        visited = set()
        liberties = set()

        def dfs(r, c):
            if (r, c) in visited:
                return
            visited.add((r, c))
            for nr, nc in self.get_neighbors((r, c)):
                if board[nr, nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr, nc] == color:
                    dfs(nr, nc)

        dfs(*move)
        return len(liberties)
