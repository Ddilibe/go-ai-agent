# src/go/agents/base_agent.py
from abc import ABCMeta, abstractmethod
from typing import List, Optional, Tuple

import numpy as np


class BaseAgent():
    def __init__(self, color: int, board_size: int):
        self.color = color
        self.board_size = board_size

    # @abstractmethod
    def select_move(
        self, board: np.ndarray, legal_moves: List[Tuple[int, int]]
    ) -> Optional[Tuple[int, int]]:
        """Return (row, col) or None to pass."""
        raise NotImplementedError
