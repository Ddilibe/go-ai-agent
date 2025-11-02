# src/go/agents/random_agent.py
import random
from typing import List, Optional, Tuple

import numpy as np

from .base_agent import BaseAgent


class RandomAgent(BaseAgent):
    """Chooses a random legal move (uniformly)."""

    def select_move(
        self, board: np.ndarray, legal_moves: List[Tuple[int, int]]
    ) -> Optional[Tuple[int, int]]:
        if not legal_moves:
            return None  # pass
        return random.choice(legal_moves)
