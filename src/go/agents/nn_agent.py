# src/go/agents/nn_agent.py
from typing import List, Optional, Tuple

import torch
import numpy as np

from .base_agent import BaseAgent

class NNAgent(BaseAgent):
    """Neural network agent using PyTorch policy/value model."""

    def __init__(self, color, board_size, model_path="models/policy_net.pt"):
        super().__init__(color, board_size)
        self.model = torch.load(model_path, map_location="cpu")
        self.model.eval()

    def select_move(
        self, board: np.ndarray, legal_moves: List[Tuple[int, int]]
    ) -> Optional[Tuple[int, int]]:
        if not legal_moves:
            return None

        # Convert board to tensor
        x = torch.tensor(board, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

        with torch.no_grad():
            logits = self.model(x).flatten()

        # Mask illegal moves
        mask = np.zeros(self.board_size * self.board_size)
        for r, c in legal_moves:
            mask[r * self.board_size + c] = 1
        logits = logits * torch.tensor(mask)

        # Softmax to probabilities
        probs = torch.nn.functional.softmax(logits, dim=0).numpy()
        idx = np.random.choice(len(probs), p=probs / probs.sum())

        r, c = divmod(idx, self.board_size)
        return (r, c)
