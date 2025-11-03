# src/go/board.py
from __future__ import annotations
from typing import List, Optional, Set, Tuple
import numpy as np
import copy

"""
Board representation for the game of Go.

Board convention:
  - 0 = empty
  - 1 = black
  - 2 = white
"""


class Board:
    def __init__(self, size: int = 9):
        self.size = size
        self.grid = np.zeros((size, size), dtype=np.int8)
        self.ko: Optional[Tuple[int, int]] = None  # position forbidden due to ko
        self.history: List[np.ndarray] = []  # used for ko/position repetition

    # -------------------------------------------------------------------------
    # Basic helpers
    # -------------------------------------------------------------------------
    def copy(self) -> "Board":
        """Return a deep copy of the board."""
        new_board = Board(self.size)
        new_board.grid = np.copy(self.grid)
        new_board.ko = self.ko
        new_board.history = [np.copy(h) for h in self.history]
        return new_board

    def is_on_board(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        n = []
        if row > 0:
            n.append((row - 1, col))
        if row < self.size - 1:
            n.append((row + 1, col))
        if col > 0:
            n.append((row, col - 1))
        if col < self.size - 1:
            n.append((row, col + 1))
        return n

    # -------------------------------------------------------------------------
    # Core gameplay logic
    # -------------------------------------------------------------------------
    def place_stone(self, color: int, move: Optional[Tuple[int, int]]) -> bool:
        """
        Place a stone of `color` at `move` if legal.
        Returns True if move was made, False otherwise.
        """
        if move is None:  # pass move
            self.ko = None
            self.history.append(np.copy(self.grid))
            return True

        r, c = move
        if not self.is_on_board(r, c) or self.grid[r, c] != 0:
            return False
        if self.ko == move:
            return False

        # Clone board for legality testing
        test_board = np.copy(self.grid)
        test_board[r, c] = color

        # Remove opponent groups with no liberties
        opp = 3 - color
        captured_any = False
        for nr, nc in self.neighbors(r, c):
            if test_board[nr, nc] == opp:
                group, liberties = self.get_group(test_board, nr, nc)
                if not liberties:
                    for gr, gc in group:
                        test_board[gr, gc] = 0
                    captured_any = True

        # Check if move is suicide
        _, liberties = self.get_group(test_board, r, c)
        if not liberties and not captured_any:
            return False

        # Ko rule — disallow repeating previous position
        if self.history and np.array_equal(test_board, self.history[-1]):
            return False

        # Apply final changes
        self.grid = test_board
        self.history.append(np.copy(self.grid))

        # Mark potential ko
        self.ko = None
        if captured_any:
            # If exactly one stone was captured, ko can occur
            captured_positions = [
                (nr, nc) for nr, nc in self.neighbors(r, c) if self.grid[nr, nc] == 0
            ]
            if len(captured_positions) == 1:
                self.ko = captured_positions[0]
        return True

    def get_group(
        self, grid: np.ndarray, row: int, col: int
    ) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        """
        Find all connected stones of same color and their liberties.
        """
        color = grid[row, col]
        group = set()
        liberties = set()

        def dfs(r: int, c: int):
            if (r, c) in group:
                return
            group.add((r, c))
            for nr, nc in self.neighbors(r, c):
                if grid[nr, nc] == 0:
                    liberties.add((nr, nc))
                elif grid[nr, nc] == color:
                    dfs(nr, nc)

        dfs(row, col)
        return group, liberties

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------
    def legal_moves(self, color: int) -> List[Tuple[int, int]]:
        """Return a list of legal (row, col) moves for color."""
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r, c] != 0:
                    continue
                if self.ko == (r, c):
                    continue

                # Simulate move
                test_board = np.copy(self.grid)
                test_board[r, c] = color
                opp = 3 - color

                # Remove captured opponent groups
                captured_any = False
                for nr, nc in self.neighbors(r, c):
                    if test_board[nr, nc] == opp:
                        group, liberties = self.get_group(test_board, nr, nc)
                        if not liberties:
                            for gr, gc in group:
                                test_board[gr, gc] = 0
                            captured_any = True

                # Check if suicide
                _, liberties = self.get_group(test_board, r, c)
                if not liberties and not captured_any:
                    continue

                # Ko prevention
                if self.history and np.array_equal(test_board, self.history[-1]):
                    continue

                moves.append((r, c))
        return moves

    def score(self) -> Tuple[int, int]:
        """
        Basic area scoring.
        Returns (black_score, white_score)
        """
        visited = set()
        black_score = 0
        white_score = 0

        for r in range(self.size):
            for c in range(self.size):
                if (r, c) in visited or self.grid[r, c] != 0:
                    continue

                territory, owner = self._explore_territory(r, c, visited)
                if owner == 1:
                    black_score += len(territory)
                elif owner == 2:
                    white_score += len(territory)

        # Add captured stones (area scoring counts all stones)
        black_score += np.sum(self.grid == 1)
        white_score += np.sum(self.grid == 2)
        return black_score, white_score

    def _explore_territory(
        self, r: int, c: int, visited: Set[Tuple[int, int]]
    ) -> Tuple[Set[Tuple[int, int]], Optional[int]]:
        """Find empty region and determine if it belongs to black, white, or neutral."""
        territory = set()
        bordering_colors = set()

        def dfs(x, y):
            if (x, y) in visited:
                return
            visited.add((x, y))
            territory.add((x, y))
            for nx, ny in self.neighbors(x, y):
                if self.grid[nx, ny] == 0:
                    dfs(nx, ny)
                else:
                    bordering_colors.add(self.grid[nx, ny])

        dfs(r, c)
        owner = None
        if len(bordering_colors) == 1:
            owner = bordering_colors.pop()
        return territory, owner

    # -------------------------------------------------------------------------
    # Pretty-print
    # -------------------------------------------------------------------------
    def __str__(self):
        symbols = {0: ".", 1: "●", 2: "○"}
        return "\n".join(
            " ".join(symbols[self.grid[r, c]] for c in range(self.size))
            for r in range(self.size)
        )

    @staticmethod
    def create_board(
        size: int,
        grid: List[List[int]],
        ko: Optional[Tuple[int, int]] = None,
        history: List[np.ndarray] = [],
    ) -> "Board":

        board = Board(size)
        board.grid = grid
        board.ko = ko
        board.history = history
        return board
