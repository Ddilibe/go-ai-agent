# Monte Carlo Search Tree Agent Code

## Advanced
```python
# src/go/agents/mcts_agent.py
import math
import random
from typing import List, Optional, Tuple, Dict
import numpy as np

from ..board import Board
from .base_agent import BaseAgent


class MCTSNode:
    def __init__(
        self,
        board: Board,
        parent: Optional["MCTSNode"],
        move: Optional[Tuple[int, int]],
        to_move: int,
    ):
        """
        board: Board state at this node (must be a copy)
        parent: parent node
        move: the move that led to this node (None for root / pass)
        to_move: player to move at this node (1=black,2=white)
        """
        self.board = board
        self.parent = parent
        self.move = move
        self.to_move = to_move

        self.children: Dict[Optional[Tuple[int, int]], MCTSNode] = {}
        self.visits = 0
        self.wins = 0.0  # from perspective of the player who just moved (parent)

        # list of untried moves (legal moves at this node); includes None for pass if allowed
        self.untried_moves = board.legal_moves(to_move) + [None]

    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    def best_child(self, c_param: float = 1.4) -> "MCTSNode":
        """
        Choose best child according to UCT:
        UCT = (w_i / n_i) + c * sqrt( ln(N) / n_i )
        Note: wins are tracked relative to the player that made the move leading to the child.
        """
        choices = []
        for child in self.children.values():
            if child.visits == 0:
                uct_value = float("inf")
            else:
                # Parent total visits
                parent_visits = self.visits if self.visits > 0 else 1
                win_rate = child.wins / child.visits
                uct_value = win_rate + c_param * math.sqrt(
                    math.log(parent_visits) / child.visits
                )
            choices.append((uct_value, child))
        # return child with maximum UCT value
        return max(choices, key=lambda x: x[0])[1]

    def q(self) -> float:
        return self.wins

    def n(self) -> int:
        return self.visits


class MCTSAgent(BaseAgent):
    """
    Monte Carlo Tree Search agent using your Board rules.

    Parameters:
    - color: agent color (1 or 2)
    - board_size: size of board (passed to BaseAgent, not used here beyond consistency)
    - simulations: number of MCTS iterations per move
    - c_puct: exploration constant
    - rollout_limit: max moves during a random playout to avoid extremely long simulations
    """

    def __init__(
        self,
        color: int,
        board_size: int,
        simulations: int = 400,
        c_puct: float = 1.4,
        rollout_limit: int = 200,
    ):
        super().__init__(color=color, board_size=board_size)
        self.simulations = simulations
        self.c_puct = c_puct
        self.rollout_limit = rollout_limit
        random.seed()

    def select_move(
        self, board: np.ndarray, legal_moves: List[Tuple[int, int]]
    ) -> Optional[Tuple[int, int]]:
        """
        board_array: numpy array representing the current board (as used elsewhere)
        legal_moves: list of legal moves for this agent (computed by board.legal_moves(color))
        """
        # Create a Board object from the provided array by copying into Board
        root_board = Board(size=self.board_size)
        root_board.grid = np.copy(board)
        # Also reconstruct history and ko if needed: assume the passed board_array belongs to a Board instance
        # (best integration is to pass actual Board instance in future). For now, root_board.history is empty,
        # which means ko prevention via history won't work here unless callers pass the Board object instead.
        # We'll try to be safe by not relying on history in the MCTS simulation root. If your game passes
        # the Board object itself, replace this with root_board = board.copy()

        # If caller passed actual Board objects in legal_moves simulation, prefer that. But current glue uses arrays.
        # To integrate perfectly, call agent.select_move(self.board, legal_moves) in game loop instead of agent.select_move(self.board.grid,...)

        root = MCTSNode(board=root_board, parent=None, move=None, to_move=self.color)

        # If no legal moves, return pass
        if not legal_moves:
            return None

        for _ in range(self.simulations):
            node = root
            # 1) SELECTION
            # descend until we find a node that is not fully expanded or is terminal
            while node.is_fully_expanded() and node.children:
                node = node.best_child(self.c_puct)

            # 2) EXPANSION
            if node.untried_moves:
                m = node.untried_moves.pop(random.randrange(len(node.untried_moves)))
                # simulate applying m to node.board
                new_board = node.board.copy()
                # place_stone expects (color, move) where move is None for pass
                new_board.place_stone(node.to_move, m)
                child = MCTSNode(
                    board=new_board, parent=node, move=m, to_move=3 - node.to_move
                )
                node.children[m] = child
                node = child

            # 3) SIMULATION (rollout) from node
            winner = self._rollout(node.board, node.to_move)

            # 4) BACKPROPAGATION
            self._backpropagate(node, winner)

        # pick the most visited child of root
        if not root.children:
            # fallback: choose random legal move
            return random.choice(legal_moves)

        best = max(root.children.values(), key=lambda n: n.visits)
        return best.move

    def _rollout(self, board: Board, to_move: int) -> int:
        """
        Perform a random playout starting from the provided board and player to move.
        Returns winner color (1 or 2) or 0 if tie.
        """
        sim = board.copy()
        current_player = to_move
        passes = 0
        moves = 0

        while passes < 2 and moves < self.rollout_limit:
            legal = sim.legal_moves(current_player)
            if not legal:
                move = None
            else:
                move = random.choice(legal + [None])  # allow occasional pass
            made = sim.place_stone(current_player, move)
            # If place_stone refused (shouldn't happen if legal), treat as pass
            if not made:
                move = None
                passes += 1
            else:
                if move is None:
                    passes += 1
                else:
                    passes = 0
            current_player = 3 - current_player
            moves += 1

        # Scoring via area scoring from Board.score()
        black_score, white_score = sim.score()
        if black_score > white_score:
            return 1
        elif white_score > black_score:
            return 2
        else:
            return 0

    def _backpropagate(self, node: MCTSNode, winner: int):
        """
        Walk up from node to root, updating visits and wins.
        We record wins from the perspective of the player who made the move that led to the node.
        That is: if node.move was played by player P (parent.to_move), then node.wins counts
        how often P ended up winning.
        """
        while node is not None:
            node.visits += 1
            if node.parent is not None:
                # winner equals the player who made the move leading to this node?
                mover = 3 - node.to_move  # mover is the player who made node.move
                if winner == mover:
                    node.wins += 1.0
                elif winner == 0:
                    node.wins += 0.5
                # else no increment for loss
            if node.parent:
                node = node.parent
```

## Basic 
```python
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

```