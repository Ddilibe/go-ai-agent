#!/usr/bin/env python3
import math, random
from typing import List, Optional, Tuple

import numpy as np

from .base_agent import BaseAgent

class MCTSNode:
    def __init__(self, board, move=None, parent=None, color=1):
        self.board = board
        self.move = move
        self.parent = parent
        self.color = color
        self.children = []
        self.visits = 0
        self.wins = 0.0

    def uct_score(self, total_visits, c=1.4):
        if self.visits == 0:
            return float("inf")
        return self.wins / self.visits + c * math.sqrt(math.log(total_visits) / self.visits)

class MCTSAgent(BaseAgent):
    """Monte Carlo Tree Search agent (simplified)."""

    def __init__(self, color, board_size, simulations=100):
        super().__init__(color, board_size)
        self.simulations = simulations

    def select_move(
        self, board: np.ndarray, legal_moves: List[Tuple[int, int]]
    ) -> Optional[Tuple[int, int]]:
        if not legal_moves:
            return None

        root = MCTSNode(np.copy(board), color=self.color)

        for _ in range(self.simulations):
            node = self.select(root)
            winner = self.simulate(node.board, node.color)
            self.backpropagate(node, winner)

        # Pick best child by visit count
        if not root.children:
            return random.choice(legal_moves)

        best_child = max(root.children, key=lambda n: n.visits)
        return best_child.move

    def select(self, node):
        while node.children:
            total_visits = sum(c.visits for c in node.children)
            node = max(node.children, key=lambda n: n.uct_score(total_visits))
        return node

    def simulate(self, board, color):
        """Random playout simulation (placeholder)."""
        return random.choice([1, 2])

    def backpropagate(self, node, winner):
        while node:
            node.visits += 1
            if node.color == winner:
                node.wins += 1
            node = node.parent
