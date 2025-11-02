#!/usr/bin/env python3
from go.game import GoGame


if __name__ == "__main__":
    # Black = Intermediate AI (Heuristic)
    # White = Beginner AI (Random)
    game = GoGame(
        board_size=9, black="intermediate", white="beginner", output_dir="cache"
    )
    game.play()
